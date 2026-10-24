"""The single per-host sync worker: spool -> events/<host>.jsonl in the ledger repo -> commit -> push.

Spool lines are acknowledged (removed) only after the push succeeds; on any failure the local ledger is
reset to the remote and the spool kept, so retries can duplicate (deduped by event_id) but never lose.
"""
from __future__ import annotations

import fcntl
import json
import os
import socket
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from . import events, gitutil

STATE_FILE = "sync-state.json"
LOCK_FILE = "sync.lock"


@dataclass
class SyncState:
    last_pull_ok: bool = False
    last_push_ok: bool = False
    pending: int = 0
    error: str = ""
    at: str | None = None
    busy: bool = False


def default_state_dir() -> Path:
    return Path(os.environ.get("WORKBOARD_STATE", "~/.local/state/workboard")).expanduser()


def host_id_for(cfg) -> str:
    short = socket.gethostname().split(".")[0]
    for s in cfg.servers:
        if s.host_alias and (s.host_alias == short or short.startswith(s.host_alias)):
            return s.id
    return short


def load_state(state_dir: Path) -> SyncState:
    try:
        return SyncState(**json.loads((Path(state_dir) / STATE_FILE).read_text()))
    except (OSError, ValueError, TypeError):
        return SyncState()


def _save_state(state_dir: Path, st: SyncState) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".state-")
    with os.fdopen(fd, "w") as fh:
        json.dump(asdict(st), fh)
    os.replace(tmp, state_dir / STATE_FILE)


def _spool_lines(state_dir: Path) -> list[bytes]:
    path = state_dir / events.SPOOL_NAME
    try:
        with open(path, "rb") as fh:
            fcntl.flock(fh, fcntl.LOCK_SH)
            data = fh.read()
    except FileNotFoundError:
        return []
    return [l for l in data.split(b"\n") if l.strip()] if data.endswith(b"\n") else \
        [l for l in data.split(b"\n")[:-1] if l.strip()]          # ignore an unterminated tail


def _ack_spool(state_dir: Path, n: int) -> None:
    """Drop the first n complete lines, keeping anything appended meanwhile. Holds the spool lock."""
    path = state_dir / events.SPOOL_NAME
    fd = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with os.fdopen(os.dup(fd), "rb") as fh:
            data = fh.read()
        lines = data.split(b"\n")
        rest = b"\n".join(lines[n:])
        fd2, tmp = tempfile.mkstemp(dir=state_dir, prefix=".spool-")
        with os.fdopen(fd2, "wb") as out:
            out.write(rest)
        os.replace(tmp, path)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _last_seq(path: Path) -> int:
    evs, _ = events.read_events([path])
    return max((e["seq"] for e in evs), default=0)


def _ensure_clone(cfg, timeout: float) -> tuple[Path, str]:
    led = Path(cfg.ledger.path).expanduser()
    if not (led / ".git").exists():
        led.parent.mkdir(parents=True, exist_ok=True)
        p = gitutil.run(led.parent, "clone", "-q", "-b", cfg.ledger.branch, cfg.ledger.remote, str(led), timeout=timeout)
        if p.returncode != 0:
            return led, f"clone failed: {gitutil.err(p)}"
        gitutil.run(led, "config", "user.email", "workboard@localhost")
        gitutil.run(led, "config", "user.name", "workboard")
    return led, ""


def _pull(led: Path, branch: str, timeout: float) -> str:
    p = gitutil.run(led, "fetch", "-q", "origin", branch, timeout=timeout)
    if p.returncode != 0:
        return f"pull failed: {gitutil.err(p)}"
    p = gitutil.run(led, "reset", "-q", "--hard", f"origin/{branch}")
    return "" if p.returncode == 0 else f"reset failed: {gitutil.err(p)}"


def _push(led: Path, branch: str, timeout: float):
    return gitutil.run(led, "push", "-q", "origin", f"HEAD:{branch}", timeout=timeout)


def sync(cfg, *, host_id: str | None = None, state_dir: Path | None = None, timeout_seconds: float = 30,
         retries: int = 3) -> SyncState:
    state_dir = Path(state_dir or default_state_dir())
    state_dir.mkdir(parents=True, exist_ok=True)
    host_id = host_id or host_id_for(cfg)
    lock = open(state_dir / LOCK_FILE, "w")
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            st = load_state(state_dir)
            st.busy = True
            return st
        st = _sync_locked(cfg, host_id, state_dir, timeout_seconds, retries)
        _save_state(state_dir, st)
        return st
    finally:
        lock.close()


def _sync_locked(cfg, host_id, state_dir, timeout, retries) -> SyncState:
    st = SyncState(at=events.utcnow())
    if not cfg.ledger.remote:
        st.error = "no ledger.remote configured"
        st.pending = len(_spool_lines(state_dir))
        return st
    led, err = _ensure_clone(cfg, timeout)
    if err:
        st.error, st.pending = err, len(_spool_lines(state_dir))
        return st
    branch = cfg.ledger.branch
    err = _pull(led, branch, timeout)
    st.last_pull_ok = not err
    lines = _spool_lines(state_dir)
    st.pending = len(lines)
    if err:
        st.error = err
        return st
    if not lines:
        st.last_push_ok = True
        return st
    rel = Path("events") / f"{host_id}.jsonl"
    for attempt in range(retries):
        path = led / rel
        path.parent.mkdir(exist_ok=True)
        seq = _last_seq(path)
        out = []
        for raw in lines:
            try:
                ev = json.loads(raw)
            except ValueError:
                continue                          # unparseable spool line: dropped (cannot be repaired)
            seq += 1
            out.append(json.dumps(events.stamp(ev, host_id, seq), separators=(",", ":"), ensure_ascii=False))
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("".join(l + "\n" for l in out))
        gitutil.run(led, "add", str(rel))
        c = gitutil.run(led, "commit", "-q", "-m", f"events: {host_id} +{len(out)}")
        if c.returncode != 0:
            st.error = f"commit failed: {gitutil.err(c)}"
            _pull(led, branch, timeout)
            return st
        p = _push(led, branch, timeout)
        if p.returncode == 0:
            _ack_spool(state_dir, len(lines))
            st.last_push_ok, st.pending, st.error = True, len(_spool_lines(state_dir)), ""
            return st
        st.error = f"push failed: {gitutil.err(p)}"
        if _pull(led, branch, timeout):            # drop our local commit; spool still holds the lines
            break
    return st

"""The single per-host sync worker: spool -> events/<host>.jsonl in the ledger repo -> commit -> push.

Spool lines are acknowledged (removed) only after the push succeeds; on any failure the local ledger is
reset to the remote and the spool kept, so retries can duplicate (deduped by event_id) but never lose.
The whole run shares one deadline (default 20 s); every git call gets only the remaining budget.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import events, gitutil

STATE_FILE = "sync-state.json"
LOCK_FILE = "sync.lock"
_SAFE_HOST = re.compile(r"[^A-Za-z0-9_.-]")


@dataclass
class SyncState:
    last_pull_ok: bool = False
    last_push_ok: bool = False
    pending: int = 0
    error: str = ""
    at: str | None = None
    busy: bool = False
    notes: list = None


class Deadline:
    def __init__(self, seconds: float):
        self.end = time.monotonic() + seconds

    def left(self) -> float:
        return max(0.0, self.end - time.monotonic())

    def expired(self) -> bool:
        return self.left() <= 0.5


def default_state_dir() -> Path:
    return Path(os.environ.get("WORKBOARD_STATE", "~/.cache/workboard")).expanduser()


def host_id_for(cfg) -> str:
    short = socket.gethostname().split(".")[0]
    for s in cfg.servers:
        if s.host_alias and (s.host_alias == short or short.startswith(s.host_alias)):
            return s.id
    return short


def safe_host(host_id: str) -> str:
    cleaned = _SAFE_HOST.sub("_", host_id).strip(".") or "host"
    return cleaned[:64]


def load_state(state_dir: Path) -> SyncState:
    try:
        data = json.loads((Path(state_dir) / STATE_FILE).read_text())
        return SyncState(**{k: v for k, v in data.items() if k in SyncState.__dataclass_fields__})
    except (OSError, ValueError, TypeError):
        return SyncState()


def _save_state(state_dir: Path, st: SyncState) -> None:
    fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".state-")
    with os.fdopen(fd, "w") as fh:
        json.dump(asdict(st), fh)
    os.replace(tmp, state_dir / STATE_FILE)


def _read_spool_locked(state_dir: Path) -> bytes:
    try:
        return (state_dir / events.SPOOL_NAME).read_bytes()
    except FileNotFoundError:
        return b""


def _complete_lines(data: bytes) -> list[bytes]:
    parts = data.split(b"\n")
    if not data.endswith(b"\n"):
        parts = parts[:-1]               # an unterminated tail is not a record yet
    return [l for l in parts if l.strip()]


def _spool_lines(state_dir: Path) -> list[bytes]:
    with events.spool_lock(state_dir):
        return _complete_lines(_read_spool_locked(state_dir))


def _ack_spool(state_dir: Path, n: int) -> None:
    """Drop the first n complete records, keeping anything appended meanwhile. Holds the spool lock."""
    with events.spool_lock(state_dir):
        data = _read_spool_locked(state_dir)
        kept, seen = [], 0
        for line in data.split(b"\n"):
            if line.strip() and seen < n:
                seen += 1
                continue
            kept.append(line)
        fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".spool-")
        with os.fdopen(fd, "wb") as out:
            out.write(b"\n".join(kept).lstrip(b"\n"))
        os.replace(tmp, state_dir / events.SPOOL_NAME)


def _last_seq(path: Path) -> int:
    return events.max_physical_seq(path)


def _ensure_clone(cfg, dl: Deadline) -> tuple[Path, str]:
    led = Path(cfg.ledger.path).expanduser()
    if not (led / ".git").exists():
        led.parent.mkdir(parents=True, exist_ok=True)
        p = gitutil.run(led.parent, "clone", "-q", "-b", cfg.ledger.branch, cfg.ledger.remote, str(led), timeout=dl.left())
        if p.returncode != 0:
            return led, f"clone failed: {gitutil.err(p)}"
        gitutil.run(led, "config", "user.email", "workboard@localhost", timeout=dl.left())
        gitutil.run(led, "config", "user.name", "workboard", timeout=dl.left())
    # always follow the configured remote, so a config change never keeps writing an old ledger
    p = gitutil.run(led, "remote", "set-url", "origin", cfg.ledger.remote, timeout=dl.left())
    if p.returncode != 0:
        return led, f"remote set-url failed: {gitutil.err(p)}"
    return led, ""


def _pull(led: Path, branch: str, dl: Deadline) -> str:
    p = gitutil.run(led, "fetch", "-q", "origin", branch, timeout=dl.left())
    if p.returncode != 0:
        return f"pull failed: {gitutil.err(p)}"
    p = gitutil.run(led, "reset", "-q", "--hard", f"origin/{branch}", timeout=dl.left())
    return "" if p.returncode == 0 else f"reset failed: {gitutil.err(p)}"


def _push(led: Path, branch: str, timeout: float):
    return gitutil.run(led, "push", "-q", "origin", f"HEAD:{branch}", timeout=timeout)


def sync(cfg, *, host_id: str | None = None, state_dir: Path | None = None, timeout_seconds: float = 20,
         retries: int = 3) -> SyncState:
    state_dir = Path(state_dir or default_state_dir())
    state_dir.mkdir(parents=True, exist_ok=True)
    host_id = safe_host(host_id or host_id_for(cfg))
    lock = open(state_dir / LOCK_FILE, "w")
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            st = load_state(state_dir)
            st.busy = True
            return st
        try:
            st = _sync_locked(cfg, host_id, state_dir, Deadline(timeout_seconds), retries)
        except Exception as exc:
            # Cron must always leave a durable explanation.  In particular, optional
            # inventory/snapshot sources must never turn a sync attempt into a silent
            # traceback with an old heartbeat.
            st = SyncState(at=events.utcnow(), error=f"sync exception: {exc.__class__.__name__}: {exc}"[:300])
            try:
                st.pending = len(_spool_lines(state_dir))
            except Exception:
                st.pending = 0
        # Usage is an isolated derived cache: a parser/schema failure must not
        # prevent ledger delivery, and tests with an explicit state directory
        # never touch the live cache.
        try:
            from . import usage
            configured_cache = os.environ.get("WORKBOARD_CACHE")
            usage_cache = Path(configured_cache).expanduser() if configured_cache else state_dir
            isolated = str(getattr(cfg, "path", "")) == "/nonexistent"
            roots = ({"claude_root": state_dir / "usage-fixtures" / "claude",
                      "codex_root": state_dir / "usage-fixtures" / "codex",
                      "muse_db": state_dir / "usage-fixtures" / "muse.db"} if isolated else {})
            usage.collect(cfg, [], host_id, cache_dir=usage_cache, byte_budget=32 * 1024 * 1024,
                          time_budget_s=5.0, **roots)
        except Exception:
            pass
        _save_state(state_dir, st)
        return st
    finally:
        lock.close()


AUTO_CLAIM = [True]


def _touched(lines: list[bytes]) -> list[tuple[str, dict]]:
    seen, out = set(), []
    for raw in lines:
        try:
            ev = json.loads(raw)
        except ValueError:
            continue
        if isinstance(ev, dict) and ev.get("type") == "touch" and isinstance(ev.get("entity"), dict):
            key = (ev["entity"].get("id"), ev.get("actor", {}).get("session_id"))
            if key not in seen and key[0] and key[1] and ev["actor"].get("kind") != "human" and \
                    not (ev.get("payload") or {}).get("weak"):       # name-in-command evidence never auto-claims
                seen.add(key)
                out.append((key[0], ev["actor"]))
    return out


def _stamp_lines(lines: list[bytes], host_id: str, seq: int) -> list[str]:
    out = []
    for raw in lines:
        try:
            ev = json.loads(raw)
        except ValueError:
            ev = None
        if not isinstance(ev, dict):
            # keep a trace instead of silently dropping an unreadable record
            ev = events.new_event("warning", None, {"bad_spool_line": raw[:200].decode("utf-8", "replace")},
                                  actor={"session_id": "workboard", "alias": "workboard", "kind": "human"},
                                  commit=None, source="sync")
        seq += 1
        out.append(json.dumps(events.stamp(ev, host_id, seq), separators=(",", ":"), ensure_ascii=False))
    return out


def _sync_locked(cfg, host_id, state_dir, dl: Deadline, retries) -> SyncState:
    st = SyncState(at=events.utcnow())
    st.pending = len(_spool_lines(state_dir))
    if not cfg.ledger.remote:
        st.error = "no ledger.remote configured"
        return st
    led, err = _ensure_clone(cfg, dl)
    if err:
        st.error = err
        return st
    branch = cfg.ledger.branch
    err = _pull(led, branch, dl)
    st.last_pull_ok = not err
    if err:
        st.error = err
        return st
    lines = _spool_lines(state_dir)
    st.pending = len(lines)
    rel = Path("events") / f"{host_id}.jsonl"
    host_rel = Path("hosts") / f"{host_id}.json"
    backoff = 0.5
    for attempt in range(retries):
        if dl.expired():
            st.error = st.error or "sync deadline reached"
            break
        path = led / rel
        path.parent.mkdir(exist_ok=True)
        if lines:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("".join(l + "\n" for l in _stamp_lines(lines, host_id, _last_seq(path))))
        from . import host_snapshots
        host_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        queued_after_batch = max(0, len(_spool_lines(state_dir)) - len(lines))
        snapshot_error = ""
        try:
            host_snapshots.publish(led, state_dir, host_id, at=host_at, spool_pending=queued_after_batch,
                                   sync_error="", sync_at=st.at)
            add_paths = [str(host_rel)] + ([str(rel)] if lines else [])
        except Exception as exc:
            snapshot_error = f"host snapshot skipped: {exc.__class__.__name__}: {exc}"[:300]
            add_paths = [str(rel)] if lines else []
        if not add_paths:
            st.error = snapshot_error
            st.pending = len(_spool_lines(state_dir))
            return st
        a = gitutil.run(led, "add", *add_paths, timeout=dl.left())
        if a.returncode != 0:
            st.error = f"git add failed: {gitutil.err(a)}"
            _pull(led, branch, dl)
            return st
        subject = f"events: {host_id} +{len(lines)}" if lines else f"host: {host_id} snapshot"
        c = gitutil.run(led, "commit", "-q", "-m", subject, timeout=dl.left())
        if c.returncode != 0:
            st.error = f"commit failed: {gitutil.err(c)}"
            _pull(led, branch, dl)
            return st
        p = _push(led, branch, dl.left())
        if p.returncode == 0:
            touched = _touched(lines)
            _ack_spool(state_dir, len(lines))
            if touched and getattr(cfg.claims, "mode", "atomic") == "atomic" and AUTO_CLAIM[0]:
                try:
                    from .coord import auto_claims
                    st.notes = auto_claims(cfg, state_dir, touched)
                except Exception as exc:          # claims must never break event delivery
                    st.error = f"auto-claim: {exc}"
            st.last_push_ok = True
            st.error = st.error if st.error.startswith("auto-claim") else snapshot_error
            st.pending = len(_spool_lines(state_dir))
            return st
        st.error = f"push failed: {gitutil.err(p)}"
        if _pull(led, branch, dl):          # drop our local commit; the spool still holds the lines
            break
        time.sleep(min(backoff, dl.left()))
        backoff *= 2
    st.pending = len(_spool_lines(state_dir))
    return st

"""Claude Code hooks: name sessions, record task activity, block edits to a task another live session owns.

Contract (DESIGN §6): fast, no network, no git, no stdout; any internal error -> exit 0 (never break a
session). The only non-zero outcome is the deliberate block (exit 2 + a message on stderr), and only when a
fresh claim cache (refreshed by `workboard sync`) names a different live session.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import shlex
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import events

CLAIMS_CACHE = "claims-cache.json"
HOOK_STATE = "hook-state.json"
TOUCH_WINDOW_S = 600
ALIAS_RECHECK_S = 600
TITLE_TAIL = 262144
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
BUDGET_S = 0.08                                   # hook work budget (process startup comes on top)
BUILD_TOOLS = {"codex", "muse"}
BUILD_DIR_FLAGS = {"-C", "--cd", "--workspace", "--cwd"}
OUR_COMMAND = re.compile(r"(^|[/\s])(board|workboard) hook (session-start|pre-tool|post-tool)$")


@dataclass
class HookResult:
    code: int = 0
    stderr: str = ""


# ---------------------------------------------------------------------------------------------- state
def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _atomic_write(path: Path, text: str, mode: int = 0o600) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fchmod(fh.fileno(), mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _locked_update(state_dir: Path, fn, deadline: float):
    """Read-modify-write hook-state.json under a lock acquired within the deadline; fn(state) -> result."""
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = os.open(state_dir / (HOOK_STATE + ".lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        events.flock_bounded(lock, max(0.0, deadline - time.monotonic()))
        state = _load(state_dir / HOOK_STATE)
        result = fn(state)
        _atomic_write(state_dir / HOOK_STATE, json.dumps(state))
        return result
    finally:
        try:
            fcntl.flock(lock, fcntl.LOCK_UN)
        finally:
            os.close(lock)


def save_claims_cache(state_dir: Path, data: dict) -> None:
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(state_dir / CLAIMS_CACHE, json.dumps(data))


# ---------------------------------------------------------------------------------------------- inputs
def title_from(transcript_path: str) -> str:
    try:
        path = Path(transcript_path)
        size = path.stat().st_size
        with open(path, "rb") as fh:
            if size > TITLE_TAIL:
                fh.seek(size - TITLE_TAIL)
            data = fh.read()
    except (OSError, TypeError, ValueError):
        return ""
    custom = ai = ""
    for raw in data.split(b"\n"):
        if b"Title" not in raw:
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if isinstance(row, dict):
            if isinstance(row.get("customTitle"), str) and row["customTitle"].strip():
                custom = row["customTitle"].strip()
            if isinstance(row.get("aiTitle"), str) and row["aiTitle"].strip():
                ai = row["aiTitle"].strip()
    return (custom or ai)[:80]


def _build_target(cmd: str) -> tuple[str | None, str | None]:
    """(model, working dir) for `codex exec -C <dir>` / `muse exec --workspace <dir>`; (None, None) otherwise."""
    try:
        toks = shlex.split(cmd, posix=True)
    except ValueError:
        return None, None
    for i, tok in enumerate(toks):
        name = os.path.basename(tok)
        if name in BUILD_TOOLS and i + 1 < len(toks) and toks[i + 1] == "exec":
            for j in range(i + 2, len(toks)):
                t = toks[j]
                if t in BUILD_DIR_FLAGS and j + 1 < len(toks):
                    return name, toks[j + 1]
                for flag in BUILD_DIR_FLAGS:
                    if t.startswith(flag + "="):
                        return name, t.split("=", 1)[1]
            return name, None
    return None, None


def _candidates(data: dict) -> list[Path]:
    """Paths the tool call acts on, most specific first; cwd is only a fallback."""
    ti = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    cwd = Path(data["cwd"]) if isinstance(data.get("cwd"), str) else None
    out = []
    for key in ("file_path", "notebook_path", "path"):
        if isinstance(ti.get(key), str):
            out.append(Path(ti[key]))
    if data.get("tool_name") == "Bash":
        cmd = ti.get("command") if isinstance(ti.get("command"), str) else ""
        _, target = _build_target(cmd)
        if target:
            out.append(Path(os.path.expanduser(target)) / "_")
        try:
            toks = shlex.split(cmd)[:200]
        except ValueError:
            toks = re.findall(r"[\w./~-]+", cmd)[:200]
        for tok in toks:
            if "/" in tok or tok.startswith("~"):
                out.append(Path(os.path.expanduser(tok)))
        if cwd:
            out.append(cwd / "_")
    resolved = []
    for p in out:
        if not p.is_absolute() and cwd:
            p = cwd / p
        resolved.append(p)
    return resolved


def task_of(data: dict, cfg) -> str | None:
    for p in _candidates(data):
        for repo in cfg.repositories:
            root = Path(repo.path).expanduser()
            try:
                rel = Path(os.path.normpath(p)).relative_to(os.path.normpath(root))
            except ValueError:
                continue
            parts = rel.parts
            if len(parts) >= 2 and not parts[0].startswith(".") and (root / parts[0]).is_dir():
                return parts[0]
    return None


# ---------------------------------------------------------------------------------------------- handlers
def _actor(data: dict, host_id: str, state: dict) -> dict:
    sid = data.get("session_id") if isinstance(data.get("session_id"), str) else ""
    alias = state.get("aliases", {}).get(sid, {}).get("alias") or f"{host_id}·session {sid[:8]}"
    return {"session_id": sid, "alias": alias, "kind": "claude", "host": host_id}


def _refresh_alias(data, host_id, state, now, force=False) -> dict | None:
    sid = data.get("session_id")
    if not isinstance(sid, str) or not sid:
        return None
    rec = state.setdefault("aliases", {}).get(sid, {})
    if not force and now - rec.get("checked", 0) < ALIAS_RECHECK_S:
        return None
    title = title_from(data.get("transcript_path", ""))
    alias = f"{host_id}·{title}" if title else rec.get("alias") or f"{host_id}·session {sid[:8]}"
    changed = alias != rec.get("alias")
    state["aliases"][sid] = {"alias": alias, "checked": now}
    return {"session_id": sid, "alias": alias, "kind": "claude", "host": host_id} if changed else None


def _post_tool(data, cfg, state_dir, host_id, deadline) -> HookResult:
    now = time.time()
    task = task_of(data, cfg)
    ti = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    cmd = ti.get("command") if data.get("tool_name") == "Bash" and isinstance(ti.get("command"), str) else ""
    build_model = _build_target(cmd)[0] if cmd else None

    def update(state):
        out = []
        new_alias = _refresh_alias(data, host_id, state, now)
        actor = _actor(data, host_id, state)
        if new_alias:
            out.append(("alias", None, {"alias": new_alias["alias"]}, actor))
        if task and actor["session_id"]:
            key = f"{task}|{actor['session_id']}"
            if now - state.setdefault("touch", {}).get(key, 0) >= TOUCH_WINDOW_S:
                state["touch"][key] = now
                out.append(("touch", task, {"tool": data.get("tool_name")}, actor))
            if build_model:
                out.append(("build_action", task, {"model": build_model}, actor))
        return out

    for type_, ent, payload, actor in _locked_update(state_dir, update, deadline):
        events.spool_append(state_dir, events.new_event(type_, ent, payload, actor=actor, commit=None, source="hook"),
                            wait_seconds=max(0.0, deadline - time.monotonic()))
    return HookResult(0)


def _session_start(data, cfg, state_dir, host_id, deadline) -> HookResult:
    now = time.time()
    new_alias = _locked_update(state_dir, lambda state: _refresh_alias(data, host_id, state, now, force=True), deadline)
    if new_alias:
        events.spool_append(state_dir, events.new_event("alias", None, {"alias": new_alias["alias"]},
                                                        actor=new_alias, commit=None, source="hook"),
                            wait_seconds=max(0.0, deadline - time.monotonic()))
    return HookResult(0)


def _pre_tool(data, cfg, state_dir, host_id, deadline) -> HookResult:
    if data.get("tool_name") not in EDIT_TOOLS:
        return HookResult(0)
    task = task_of(data, cfg)
    sid = data.get("session_id")
    if not task or not isinstance(sid, str):
        return HookResult(0)
    cache = _load(Path(state_dir) / CLAIMS_CACHE)
    try:
        fetched = datetime.fromisoformat(cache["fetched_at"])
        claim = cache["claims"].get(task)
    except (KeyError, TypeError, ValueError, AttributeError):
        return HookResult(0)
    now = datetime.now(timezone.utc)
    if not claim or fetched.tzinfo is None or (now - fetched).total_seconds() > cfg.claims.healthy_ttl_seconds:
        return HookResult(0)                       # no claim, or cache not fresh: advisory only, never block
    try:
        renewed = datetime.fromisoformat(claim["renewed_at"])
    except (KeyError, TypeError, ValueError):
        return HookResult(0)
    if renewed.tzinfo is None or now - renewed > timedelta(hours=cfg.claims.expire_after_hours):
        return HookResult(0)
    if claim.get("session_id") == sid:
        return HookResult(0)
    return HookResult(2, f"owned by {claim.get('alias', 'another session')} — run: workboard show {task}")


HANDLERS = {"post-tool": _post_tool, "session-start": _session_start, "pre-tool": _pre_tool}


def handle(kind, data, *, cfg, state_dir, host_id, budget: float = BUDGET_S) -> HookResult:
    deadline = time.monotonic() + budget
    try:
        if not isinstance(data, dict):
            return HookResult(0)
        return HANDLERS[kind](data, cfg, Path(state_dir), host_id, deadline)
    except events.LockBusy:
        return HookResult(0)                       # out of budget: skip quietly, never make Claude wait
    except Exception as exc:                       # fail open, and leave a trace if we still can
        try:
            sid = data.get("session_id") if isinstance(data, dict) and isinstance(data.get("session_id"), str) else "unknown"
            events.spool_append(Path(state_dir), events.new_event(
                "warning", None, {"source": "hook", "kind": kind, "error": f"{exc.__class__.__name__}: {exc}"[:300]},
                actor={"session_id": sid or "unknown", "alias": f"{host_id}·hook", "kind": "claude"},
                commit=None, source="hook"), wait_seconds=0.01)
        except Exception:
            pass
        return HookResult(0)


# ---------------------------------------------------------------------------------------------- install
def _ours(entry) -> bool:
    hooks = entry.get("hooks", []) if isinstance(entry, dict) else []
    return any(isinstance(h, dict) and OUR_COMMAND.search(str(h.get("command", "")).replace("'", "")) for h in hooks)


def _plan(board: str) -> dict:
    exe = shlex.quote(board)
    return {
        "SessionStart": [{"hooks": [{"type": "command", "command": f"{exe} hook session-start", "timeout": 5}]}],
        "PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit",
                        "hooks": [{"type": "command", "command": f"{exe} hook pre-tool", "timeout": 5}]}],
        "PostToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
                         "hooks": [{"type": "command", "command": f"{exe} hook post-tool", "timeout": 5}]}],
    }


def _backup(settings: Path) -> None:
    if settings.exists():
        dest = settings.with_name(f"{settings.name}.workboard-backup-{time.time_ns()}-{uuid.uuid4().hex[:6]}")
        shutil.copy2(settings, dest)
        os.chmod(dest, settings.stat().st_mode & 0o777)


def _write_settings(settings: Path, data: dict) -> None:
    mode = (settings.stat().st_mode & 0o777) if settings.exists() else 0o600
    _atomic_write(settings, json.dumps(data, indent=2) + "\n", mode)


def install(settings: Path, board: str, *, dry_run: bool = False) -> str:
    settings = Path(settings)
    data = json.loads(settings.read_text()) if settings.exists() else {}
    hooks_cfg = data.setdefault("hooks", {})
    for event, entries in _plan(board).items():
        kept = [e for e in hooks_cfg.get(event, []) if not _ours(e)]
        hooks_cfg[event] = kept + entries
    text = json.dumps(data, indent=2)
    if dry_run:
        return text
    settings.parent.mkdir(parents=True, exist_ok=True)
    _backup(settings)
    _write_settings(settings, data)
    return text


def uninstall(settings: Path) -> None:
    settings = Path(settings)
    data = json.loads(settings.read_text())
    for event in list(data.get("hooks", {})):
        data["hooks"][event] = [e for e in data["hooks"][event] if not _ours(e)]
        if not data["hooks"][event]:
            del data["hooks"][event]
    _backup(settings)
    _write_settings(settings, data)

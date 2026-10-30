"""Who is acting: the Claude Code session (named by its tab title) or a human shell."""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path

PROJECTS = Path(os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser()
MAX_SCAN = 4 * 1024 * 1024   # only read the tail of very long transcripts


def transcript_for(session_id: str) -> Path | None:
    if not session_id or "/" in session_id:
        return None
    hits = list(PROJECTS.glob(f"*/{session_id}.jsonl")) if PROJECTS.is_dir() else []
    return hits[0] if hits else None


def tab_title(session_id: str) -> str:
    """Latest customTitle (set by /rename) else latest aiTitle from the session transcript; '' if unknown."""
    path = transcript_for(session_id)
    if not path:
        return ""
    try:
        size = path.stat().st_size
        with open(path, "rb") as fh:
            if size > MAX_SCAN:
                fh.seek(size - MAX_SCAN)
            data = fh.read()
    except OSError:
        return ""
    custom = ai = ""
    for raw in data.split(b"\n"):
        if b"Title" not in raw:
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("customTitle"), str) and row["customTitle"].strip():
            custom = row["customTitle"].strip()
        if isinstance(row.get("aiTitle"), str) and row["aiTitle"].strip():
            ai = row["aiTitle"].strip()
    return (custom or ai)[:80]


def current_actor(host_id: str, env=None, person: str = "") -> dict:
    """The acting session. `person` is the configured user id, stored in claims so that person can later
    release claims their own agent sessions hold."""
    env = os.environ if env is None else env
    sid = env.get("CLAUDE_CODE_SESSION_ID", "")
    child = _codex_ancestor(stop_at_claude=True) if sid and env is os.environ else None
    if child:                                         # a codex/muse job launched by a Claude session: its own actor,
        pid, start, cwd = child                       # so it can never release or renew the parent's claims
        return {"session_id": f"codex:{host_id}:{pid}:{start}", "alias": f"{host_id}·Codex {Path(cwd).name or pid}·{str(pid)[-4:]}",
                "kind": "codex", "host": host_id, "person": person, "parent_session": sid}
    if sid:
        title = tab_title(sid) or f"session {sid[:8]}"
        return {"session_id": sid, "alias": f"{host_id}·{title}", "kind": "claude", "host": host_id, "person": person}
    user = env.get("USER") or getpass.getuser()
    codex = _codex_ancestor() if env is os.environ else None
    if codex:                                         # a Codex session not started from Claude: its own identity
        pid, start, cwd = codex
        return {"session_id": f"codex:{host_id}:{pid}:{start}", "alias": f"{host_id}·Codex {Path(cwd).name or pid}·{str(pid)[-4:]}",
                "kind": "codex", "host": host_id, "person": person}
    tty = _tty()
    sid = f"human:{user}@{host_id}" + (f":{tty}" if tty else "")   # separate terminals are separate actors
    return {"session_id": sid, "alias": f"{host_id}·{user} (shell{' ' + tty if tty else ''})", "kind": "human",
            "host": host_id, "person": person}


def _codex_ancestor(max_depth: int = 12, stop_at_claude: bool = False):
    """(pid, start_ticks, cwd) of the nearest `codex`/`muse` ancestor process, if any (Linux /proc only). With
    stop_at_claude, only one that is nearer than the first Claude Code process (i.e. launched by it)."""
    pid = os.getppid()
    for _ in range(max_depth):
        if pid <= 1:
            return None
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            return None
        exe = os.path.basename(cmd[0].decode(errors="replace")) if cmd and cmd[0] else ""
        if stop_at_claude and (exe == "claude" or "/claude_code/" in cmd[0].decode(errors="replace")):
            return None
        if exe in ("codex", "muse") or (exe.startswith("codex") and len(cmd) > 1):
            try:
                cwd = os.readlink(f"/proc/{pid}/cwd")
            except OSError:
                cwd = ""
            return pid, stat.rsplit(")", 1)[1].split()[19], cwd
        try:
            pid = int(stat.rsplit(")", 1)[1].split()[1])
        except (IndexError, ValueError):
            return None
    return None


def _tty() -> str:
    for fd in (0, 1, 2):
        try:
            return os.ttyname(fd).replace("/dev/", "")
        except OSError:
            continue
    return ""

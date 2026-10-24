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


def current_actor(host_id: str, env=None) -> dict:
    env = os.environ if env is None else env
    sid = env.get("CLAUDE_CODE_SESSION_ID", "")
    if sid:
        title = tab_title(sid) or f"session {sid[:8]}"
        return {"session_id": sid, "alias": f"{host_id}·{title}", "kind": "claude", "host": host_id}
    user = env.get("USER") or getpass.getuser()
    return {"session_id": f"human:{user}@{host_id}", "alias": f"{host_id}·{user} (shell)", "kind": "human", "host": host_id}

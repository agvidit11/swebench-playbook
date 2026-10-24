"""Presence: which sessions on this host are actively working on which task, even without a claim.

Run by `board sync` (cron). It looks at recently modified Claude Code transcripts and Codex session logs and
finds tasks whose *paths* they touched (`<repo>/<task>/...` or `<task>/...` in tool inputs / working dirs).
Plain mentions of a task name (e.g. in board output) do not count. One `presence` event per (task, session)
per 10 minutes; the projection shows tasks with fresh presence as ACTIVE (👀), not free.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

WINDOW_S = 6 * 3600          # transcripts modified within this window are scanned
TAIL = 512 * 1024
REEMIT_S = 600
CLAUDE = Path(os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser()
CODEX = Path(os.environ.get("CODEX_SESSIONS_DIR", "~/.codex/sessions")).expanduser()


def _tail(path: Path) -> bytes:
    try:
        size = path.stat().st_size
        with open(path, "rb") as fh:
            if size > TAIL:
                fh.seek(size - TAIL)
            return fh.read()
    except OSError:
        return b""


def _title(data: bytes) -> str:
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


def _path_hits(text: str, tasks: set[str]) -> set[str]:
    """Tasks referenced as a path component: '/<task>/' or '<task>/' at a token start, `-C <task>`, or a path
    component that contains the full task name (scratch dirs like /tmp/rev-<task>, /tmp/<task>-build)."""
    hits = set()
    for comp in set(re.findall(r"/([A-Za-z0-9._-]{8,140})(?=/|\s|$|['\"])", text)):
        for t in tasks:
            if len(t) >= 12 and t in comp:
                hits.add(t)
    for m in re.finditer(r"(?:^|[\s/'\"=])([a-z0-9][a-z0-9._-]{6,90})(?:/|['\"\s]*$)", text, re.M):
        if m.group(1) in tasks:
            hits.add(m.group(1))
    for m in re.finditer(r"(?:-C|--cd|--workspace)[ =]['\"]?([^\s'\"]+)", text):
        last = m.group(1).rstrip("/").rsplit("/", 1)[-1]
        if last in tasks:
            hits.add(last)
    return hits


def _tool_inputs(data: bytes) -> str:
    """Only the tool-use inputs and cwd fields of transcript lines (not assistant prose or tool output)."""
    out = []
    for raw in data.split(b"\n")[-4000:]:
        if b'"tool_use"' not in raw and b'"cwd"' not in raw:
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("cwd"), str):
            out.append(row["cwd"] + "/")
        msg = row.get("message") if isinstance(row.get("message"), dict) else {}
        for part in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
            if isinstance(part, dict) and part.get("type") == "tool_use" and isinstance(part.get("input"), dict):
                for v in part["input"].values():
                    if isinstance(v, str):
                        out.append(v[:4000])
    return "\n".join(out)


def scan(tasks: set[str], *, now: float | None = None, window_s: int = WINDOW_S) -> list[dict]:
    """[{task, session_id, alias_title, kind, last_seen}] for recently active sessions on this host."""
    now = now or time.time()
    found = []
    if CLAUDE.is_dir():
        for path in CLAUDE.glob("*/*.jsonl"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if now - mtime > window_s:
                continue
            data = _tail(path)
            for task in _path_hits(_tool_inputs(data), tasks):
                found.append({"task": task, "session_id": path.stem, "title": _title(data), "kind": "claude",
                              "last_seen": mtime})
    if CODEX.is_dir():
        for path in CODEX.glob("*/*/*/*.jsonl"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if now - mtime > window_s:
                continue
            head = b""
            try:
                with open(path, "rb") as fh:
                    head = fh.read(65536)
            except OSError:
                continue
            m = re.search(rb'"cwd"\s*:\s*"([^"]+)"', head)
            if not m:
                continue
            for task in _path_hits(m.group(1).decode("utf-8", "replace") + "/", tasks):
                found.append({"task": task, "session_id": "codex:" + path.stem[-12:], "title": "Codex run",
                              "kind": "codex", "last_seen": mtime})
    return found


def emit(cfg, state_dir: Path, host_id: str, tasks: set[str], *, now: float | None = None) -> int:
    """Append presence events for fresh findings (rate-limited per task/session). Returns events queued."""
    from . import events
    now = now or time.time()
    state_path = Path(state_dir) / "presence-state.json"
    try:
        seen = json.loads(state_path.read_text())
    except (OSError, ValueError):
        seen = {}
    n = 0
    for f in scan(tasks, now=now):
        key = f"{f['task']}|{f['session_id']}"
        if now - seen.get(key, 0) < REEMIT_S:
            continue
        alias = f"{host_id}·{f['title']}" if f["title"] else f"{host_id}·{f['kind']} {f['session_id'][-6:]}"
        ev = events.new_event("presence", f["task"], {"last_seen": f["last_seen"]},
                              actor={"session_id": f["session_id"], "alias": alias, "kind": f["kind"]},
                              commit=None, source="presence")
        if events.spool_append(Path(state_dir), ev):
            seen[key] = now
            n += 1
    seen = {k: v for k, v in seen.items() if now - v < WINDOW_S}
    try:
        state_path.write_text(json.dumps(seen))
    except OSError:
        pass
    return n

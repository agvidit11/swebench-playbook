"""Event schema v1, the local spool, and the event-file reader.

Producers (hooks, CLI) only append to a local spool; the sync worker (sync.py) moves spool lines into this
host's event file in the ledger repo, assigning host_id + seq. Readers never trust a line they can't parse.
"""
from __future__ import annotations

import fcntl
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .model import Finding

SCHEMA_VERSION = 1
SPOOL_NAME = "spool.jsonl"
MAX_LINE = 16384
MAX_QUEUE = 10000
EVENT_TYPES = {
    "alias", "touch", "claim", "renew", "steal", "release", "assign", "check", "review",
    "build_action", "warning", "note",
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_event(type: str, entity_id: str | None, payload: dict, *, actor: dict, commit: str | None,
              source: str, entity_kind: str = "task") -> dict:
    if type not in EVENT_TYPES:
        raise ValueError(f"unknown event type {type!r}")
    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "occurred_at": utcnow(),
        "actor": dict(actor),
        "entity": {"kind": entity_kind, "id": entity_id} if entity_id else None,
        "type": type,
        "commit": commit,
        "source": source,
        "payload": payload,
    }


def spool_append(spool_dir: Path, event: dict, *, max_line: int = MAX_LINE, max_queue: int = MAX_QUEUE) -> bool:
    """Append one event line under flock. Never raises: returns False if the event was not recorded."""
    try:
        line = json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n"
        data = line.encode("utf-8")
        if len(data) > max_line:
            return False
        spool_dir.mkdir(parents=True, exist_ok=True)
        path = spool_dir / SPOOL_NAME
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            if max_queue and os.fstat(fd).st_size > max_queue * max_line:
                return False
            os.write(fd, data)
            return True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
    except Exception:
        return False


def _valid(ev) -> bool:
    return (
        isinstance(ev, dict)
        and ev.get("schema_version") == SCHEMA_VERSION
        and isinstance(ev.get("event_id"), str)
        and ev.get("type") in EVENT_TYPES
        and isinstance(ev.get("actor"), dict)
    )


def read_events(paths: list[Path]) -> tuple[list[dict], list[Finding]]:
    """Read event files: dedupe by event_id, order by (host_id, seq), quarantine bad lines as one finding."""
    seen: dict[str, dict] = {}
    bad: list[str] = []
    for path in paths:
        try:
            raw = Path(path).read_bytes()
        except FileNotFoundError:
            continue
        for lineno, line in enumerate(raw.split(b"\n"), 1):
            if not line.strip():
                continue
            if len(line) > MAX_LINE:
                bad.append(f"{Path(path).name}:{lineno} oversize")
                continue
            try:
                ev = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                bad.append(f"{Path(path).name}:{lineno} unparseable")
                continue
            if not _valid(ev):
                bad.append(f"{Path(path).name}:{lineno} invalid schema")
                continue
            seen.setdefault(ev["event_id"], ev)
    evs = sorted(seen.values(), key=lambda e: (str(e.get("host_id", "")), int(e.get("seq") or 0), e["occurred_at"]))
    findings = []
    if bad:
        findings.append(Finding("MALFORMED_EVENTS", "warn",
                                f"{len(bad)} ledger line(s) skipped: " + ", ".join(bad[:3]) + ("…" if len(bad) > 3 else ""),
                                "workboard status"))
    return evs, findings


def latest_aliases(evs: list[dict]) -> dict[str, str]:
    """session_id -> latest alias. History stays in the log; only rendering uses the latest."""
    out: dict[str, str] = {}
    for ev in evs:
        sid = ev["actor"].get("session_id")
        if sid and ev["type"] == "alias":
            out[sid] = ev["payload"].get("alias") or out.get(sid, "")
        elif sid and sid not in out and ev["actor"].get("alias"):
            out[sid] = ev["actor"]["alias"]
    return out

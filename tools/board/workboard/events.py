"""Event schema v1, the local spool, and the event-file reader.

Producers (hooks, CLI) only append to a local spool; the sync worker (sync.py) moves spool lines into this
host's event file in the ledger repo, assigning host_id + seq. Readers never trust a line they can't parse.
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .model import Finding

SCHEMA_VERSION = 1
SPOOL_NAME = "spool.jsonl"
SPOOL_LOCK = "spool.lock"     # never replaced; every spool reader/writer takes it before opening the spool
MAX_LINE = 16384
MAX_QUEUE = 10000
ACTOR_KINDS = {"claude", "codex", "muse", "human"}
EVENT_TYPES = {
    "alias", "touch", "claim", "renew", "steal", "release", "assign", "check", "review",
    "build_action", "warning", "note", "presence", "msg", "ack", "heartbeat", "checkin",
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


def stamp(event: dict, host_id: str, seq: int) -> dict:
    """Fields the sync worker adds when moving a spool line into the host's ledger file."""
    out = dict(event)
    out.update(host_id=host_id, seq=seq, recorded_at=utcnow())
    return out


def _write_all(fd: int, data: bytes, write=os.write) -> None:
    view = memoryview(data)
    while view:
        try:
            n = write(fd, view)
        except InterruptedError:
            continue
        if n <= 0:
            raise OSError(errno.EIO, "short write")
        view = view[n:]


def _queued_records(fd: int) -> int:
    count, tail = 0, False
    os.lseek(fd, 0, os.SEEK_SET)
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        count += chunk.count(b"\n")
        tail = not chunk.endswith(b"\n")
    return count + (1 if tail else 0)


class LockBusy(Exception):
    pass


def flock_bounded(fd: int, wait_seconds: float | None) -> None:
    """Exclusive flock; with wait_seconds, poll non-blocking and raise LockBusy when the budget runs out."""
    if wait_seconds is None:
        fcntl.flock(fd, fcntl.LOCK_EX)
        return
    import time
    end = time.monotonic() + max(0.0, wait_seconds)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            if time.monotonic() >= end:
                raise LockBusy()
            time.sleep(0.002)


class spool_lock:
    """Exclusive lock on the spool's dedicated lock file (stable across the spool's atomic replacement)."""

    def __init__(self, spool_dir: Path, wait_seconds: float | None = None):
        self.path = Path(spool_dir) / SPOOL_LOCK
        self.wait = wait_seconds

    def __enter__(self):
        self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            flock_bounded(self.fd, self.wait)
        except BaseException:
            os.close(self.fd)
            raise
        return self

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)


def spool_append(spool_dir: Path, event: dict, *, max_line: int = MAX_LINE, max_queue: int = MAX_QUEUE,
                 _write=os.write, wait_seconds: float | None = None) -> bool:
    """Append one complete event line. Never raises; False means the event was not recorded."""
    try:
        data = (json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        if len(data) > max_line:
            return False
        spool_dir = Path(spool_dir)
        spool_dir.mkdir(parents=True, exist_ok=True)
        with spool_lock(spool_dir, wait_seconds):
            fd = os.open(spool_dir / SPOOL_NAME, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600)
            try:
                if max_queue and _queued_records(fd) >= max_queue:
                    return False
                start = os.fstat(fd).st_size
                if start and os.pread(fd, 1, start - 1) != b"\n":
                    _write_all(fd, b"\n", _write)          # crash-truncated tail: close it so it stays one bad line
                    start = os.fstat(fd).st_size
                try:
                    _write_all(fd, data, _write)
                except Exception:
                    try:
                        os.ftruncate(fd, start)   # never leave a partial line behind
                    except OSError:
                        pass
                    return False
                return True
            finally:
                os.close(fd)
    except Exception:
        return False


_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def _aware(ts) -> bool:
    if not isinstance(ts, str):
        return False
    try:
        return datetime.fromisoformat(ts).tzinfo is not None
    except ValueError:
        return False


def validate_committed(ev) -> str | None:
    """None if ev is a well-formed committed ledger event, else the reason it is not."""
    if not isinstance(ev, dict):
        return "not an object"
    if ev.get("schema_version") != SCHEMA_VERSION:
        return "schema_version"
    if not (isinstance(ev.get("event_id"), str) and _UUID.match(ev["event_id"])):
        return "event_id"
    if not (isinstance(ev.get("host_id"), str) and ev["host_id"]):
        return "host_id"
    seq = ev.get("seq")
    if not (isinstance(seq, int) and not isinstance(seq, bool) and seq >= 0):
        return "seq"
    if not (_aware(ev.get("occurred_at")) and _aware(ev.get("recorded_at"))):
        return "timestamps"
    if ev.get("type") not in EVENT_TYPES:
        return "type"
    actor = ev.get("actor")
    if not (isinstance(actor, dict) and isinstance(actor.get("session_id"), str) and actor["session_id"]
            and isinstance(actor.get("alias"), str) and actor.get("kind") in ACTOR_KINDS):
        return "actor"
    ent = ev.get("entity")
    if ent is not None and not (isinstance(ent, dict) and isinstance(ent.get("kind"), str) and isinstance(ent.get("id"), str)):
        return "entity"
    if ev.get("commit") is not None and not (isinstance(ev["commit"], str) and _SHA.match(ev["commit"])):
        return "commit"
    if not (isinstance(ev.get("source"), str) and ev["source"]):
        return "source"
    if not isinstance(ev.get("payload"), dict):
        return "payload"
    return None


def _bounded_lines(path: Path, limit: int):
    """Yield (lineno, bytes|None). None marks an oversize record, drained without holding it in memory."""
    with open(path, "rb") as fh:
        lineno = 0
        while True:
            line = fh.readline(limit + 1)
            if not line:
                return
            lineno += 1
            if not line.endswith(b"\n") and len(line) <= limit:
                yield lineno, b"\x00unterminated"          # a final line without newline is a torn write
                return
            if len(line) > limit:
                if not line.endswith(b"\n"):
                    while True:   # drain the rest of the oversize record
                        more = fh.readline(65536)
                        if not more or more.endswith(b"\n"):
                            break
                yield lineno, None
                continue
            yield lineno, line.rstrip(b"\n")


def read_events(paths: list[Path]) -> tuple[list[dict], list[Finding]]:
    """Read ledger files: validate, dedupe by event_id, order by (host_id, seq); bad lines -> one finding."""
    seen: dict[str, dict] = {}
    bad: list[str] = []
    for path in paths:
        path = Path(path)
        try:
            for lineno, line in _bounded_lines(path, MAX_LINE):
                if line is None:
                    bad.append(f"{path.name}:{lineno} oversize")
                    continue
                if line == b"\x00unterminated":
                    bad.append(f"{path.name}:{lineno} unterminated (torn write)")
                    continue
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    bad.append(f"{path.name}:{lineno} unparseable")
                    continue
                why = validate_committed(ev)
                if why == "type":
                    continue                              # written by a newer workboard: skip quietly
                if why:
                    bad.append(f"{path.name}:{lineno} bad {why}")
                    continue
                seen.setdefault(ev["event_id"], ev)
        except FileNotFoundError:
            continue
    evs = sorted(seen.values(), key=lambda e: (e["host_id"], e["seq"]))
    findings = []
    if bad:
        findings.append(Finding("MALFORMED_EVENTS", "warn",
                                f"{len(bad)} ledger line(s) skipped: " + ", ".join(bad[:3]) + ("…" if len(bad) > 3 else ""),
                                "workboard status"))
    return evs, findings


def max_physical_seq(path: Path) -> int:
    """Highest seq over every valid physical record (before event_id dedupe): the allocation watermark."""
    top = 0
    try:
        for _, line in _bounded_lines(Path(path), MAX_LINE):
            if not line:
                continue
            try:
                ev = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if validate_committed(ev) is None:
                top = max(top, ev["seq"])
    except FileNotFoundError:
        pass
    return top


def latest_aliases(evs: list[dict]) -> dict[str, str]:
    """session_id -> latest alias. History stays in the log; only rendering uses the latest."""
    out: dict[str, str] = {}
    for ev in evs:
        sid = ev["actor"].get("session_id")
        alias = ev["payload"].get("alias") if ev["type"] == "alias" else None
        if sid and isinstance(alias, str) and alias:
            out[sid] = alias
        elif sid and sid not in out and isinstance(ev["actor"].get("alias"), str) and ev["actor"]["alias"]:
            out[sid] = ev["actor"]["alias"]
    return out

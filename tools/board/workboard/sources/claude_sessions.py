"""Read Claude's local session registry without opening its messaging sockets.

The registry is native evidence, but a JSON file or socket pathname alone does not prove
liveness.  Records are scoped to the current uid + pidDomain and, when the PID is visible,
the process start tick must match to rule out PID reuse.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REGISTRY = Path(os.environ.get("CLAUDE_SESSIONS_DIR", "~/.claude/sessions")).expanduser()
_RUNTIME_UID = re.compile(r"/run/user/(\d+)(?:/|$)")


def session_key(kind: str, host_id: str, uid: int | str, pid_domain: str, native_id: str) -> str:
    """Stable identity; PID and display name deliberately are not part of it."""
    return f"{kind}:{host_id}:{uid}:{pid_domain}:{native_id}"


def _epoch(value) -> float | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return float(value) / 1000 if value > 10_000_000_000 else float(value)


def _iso(value) -> str | None:
    value = _epoch(value)
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def _socket_uid(value) -> int | None:
    m = _RUNTIME_UID.search(value if isinstance(value, str) else "")
    return int(m.group(1)) if m else None


def proc_identity(pid: int, proc_root: Path = Path("/proc")) -> tuple[int, str] | None:
    """Return (uid, Linux start ticks), or None when the PID is outside this namespace."""
    try:
        base = Path(proc_root) / str(pid)
        uid = base.stat().st_uid
        raw = (base / "stat").read_text()
        end = raw.rfind(")")
        fields = raw[end + 2:].split()
        return uid, fields[19]  # field 22 overall; state is fields[0] after the comm field
    except (OSError, IndexError, ValueError):
        return None


def _expected_domain(records: list[tuple[Path, dict]], uid: int, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    domains = [d.get("pidDomain") for _, d in records
               if _socket_uid(d.get("messagingSocketPath")) == uid and isinstance(d.get("pidDomain"), str)]
    return Counter(domains).most_common(1)[0][0] if domains else None


def discover(host_id: str, *, root: Path | None = None, uid: int | None = None,
             pid_domain: str | None = None, proc_root: Path = Path("/proc"), now: float | None = None,
             hooks_installed_at: float | None = None) -> tuple[list[dict], list[dict]]:
    """Return (local session rows, sanitized diagnostics).

    Diagnostics contain only classification/reason and a filename, never names, cwd, socket
    paths, registry secrets, prompts, responses, or command lines.
    """
    root = Path(root or REGISTRY).expanduser()
    uid = os.getuid() if uid is None else uid
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    parsed: list[tuple[Path, dict]] = []
    diagnostics: list[dict] = []
    try:
        paths = sorted(root.glob("*.json"))
    except OSError:
        paths = []
    for path in paths:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError, UnicodeDecodeError):
            diagnostics.append({"file": path.name, "classification": "invalid", "reason": "malformed JSON"})
            continue
        if not isinstance(data, dict):
            diagnostics.append({"file": path.name, "classification": "invalid", "reason": "not an object"})
            continue
        parsed.append((path, data))

    expected = _expected_domain(parsed, uid, pid_domain)
    sessions = []
    required = ("sessionId", "pid", "pidDomain", "procStart", "startedAt")
    for path, data in parsed:
        if any(not data.get(k) and data.get(k) != 0 for k in required) or not isinstance(data.get("pid"), int):
            diagnostics.append({"file": path.name, "classification": "invalid", "reason": "missing required field"})
            continue
        socket_uid = _socket_uid(data.get("messagingSocketPath"))
        try:
            file_uid = path.stat().st_uid
        except OSError:
            file_uid = None
        if socket_uid != uid or file_uid not in (None, uid):
            diagnostics.append({"file": path.name, "classification": "foreign-uid", "reason": "uid namespace differs"})
            continue
        domain = data["pidDomain"]
        if expected is not None and domain != expected:
            diagnostics.append({"file": path.name, "classification": "foreign-domain", "reason": "pidDomain differs"})
            continue

        ident = proc_identity(data["pid"], proc_root)
        if ident is None:
            classification, live, reason = "local-stale", False, "PID is not visible"
        elif ident[0] != uid:
            classification, live, reason = "foreign-uid", False, "process uid differs"
        elif str(ident[1]) != str(data["procStart"]):
            classification, live, reason = "pid-reused", False, "process start does not match"
        else:
            classification, live, reason = "local-live", True, "process identity matches"

        native_id = str(data["sessionId"])
        started = _epoch(data.get("startedAt"))
        native_status = data.get("status") if isinstance(data.get("status"), str) else None
        status = native_status or ("unknown" if live else "stale")
        row = {
            "session_key": session_key("claude", host_id, uid, domain, native_id),
            "native_id": native_id,
            "kind": "claude",
            "kind_icon": "🟣",
            "host": host_id,
            "uid": uid,
            "pid_domain": domain,
            "pid": data["pid"],
            "name": (data.get("name") if isinstance(data.get("name"), str) else "")[:80]
                    or f"Claude {native_id[:8]}",
            "started_at": _iso(data.get("startedAt")),
            "age_s": int(max(0, now - started)) if started is not None else None,
            "status": status,
            "status_since": _iso(data.get("statusUpdatedAt") or data.get("nameSince") or data.get("startedAt")),
            "live": live,
            "classification": classification,
            "liveness_reason": reason,
            "cwd": data.get("cwd") if isinstance(data.get("cwd"), str) else None,
            "transport": {"available": live, "kind": "courier" if live else "unavailable",
                          "reason": "deliver through the courier session" if live else reason},
            # Hook readiness is evidence-based and filled by session_inventory, which has
            # access to the ledger.  Registry age alone cannot prove which hooks a process
            # loaded (settings may have been re-written without changing their behaviour).
            "restart": {"state": "unknown", "needed": False,
                        "reason": "no hook evidence evaluated yet", "command": None},
            "child_runs": [],
        }
        if classification == "local-live":
            sessions.append(row)
        else:
            diagnostics.append({"file": path.name, "classification": classification, "reason": reason})
    sessions.sort(key=lambda x: (not x["live"], -(x.get("age_s") or 0), x["session_key"]))
    return sessions, diagnostics

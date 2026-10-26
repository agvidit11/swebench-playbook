"""Small replaceable per-host summaries shared through the private ledger."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
CACHE_NAME = "host-sessions.json"
SESSION_FIELDS = {
    "session_key", "native_id", "kind", "kind_icon", "host", "name", "started_at", "age_s",
    "last_activity_at", "status", "status_since", "live", "classification", "liveness_reason",
    "transport", "restart", "focus", "tasks", "tokens", "advice", "child_runs", "last_report",
    "last_request", "is_summary", "recent_run_count", "older_run_count", "older_child_run_count",
}
CHILD_FIELDS = {
    "session_key", "native_id", "kind", "kind_icon", "host", "name", "started_at", "age_s",
    "last_activity_at", "status", "status_since", "live", "cwd_task", "model", "effort", "provider",
    "transport", "parent_session_key", "parent_confidence", "tokens",
}


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _summary(session: dict) -> dict:
    out = {key: session[key] for key in SESSION_FIELDS if key in session}
    out["child_runs"] = [
        {key: child[key] for key in CHILD_FIELDS if key in child}
        for child in session.get("child_runs", []) if isinstance(child, dict)
    ]
    return out


def cache_local(state_dir: Path, host_id: str, sessions: list[dict], diagnostics: list[dict], *, at: str) -> None:
    """Cache a redacted inventory for the next ledger sync; never cache paths or registry internals."""
    safe_diagnostics = [
        {key: row[key] for key in ("host", "classification", "reason") if key in row}
        for row in diagnostics if isinstance(row, dict)
    ]
    _atomic_json(Path(state_dir) / CACHE_NAME, {
        "schema_version": SCHEMA_VERSION, "host": host_id, "observed_at": at,
        "sessions": [_summary(row) for row in sessions if isinstance(row, dict)],
        "diagnostics": safe_diagnostics,
    })


def _cached(state_dir: Path, host_id: str) -> dict:
    try:
        value = json.loads((Path(state_dir) / CACHE_NAME).read_text())
    except (OSError, ValueError, TypeError):
        value = {}
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION or value.get("host") != host_id:
        return {"observed_at": None, "sessions": [], "diagnostics": []}
    return value


def publish(ledger: Path, state_dir: Path, host_id: str, *, at: str, spool_pending: int,
            sync_error: str = "", sync_at: str | None = None) -> Path:
    """Write the host-owned ordinary file after a pull and before the sync commit."""
    cached = _cached(state_dir, host_id)
    path = Path(ledger) / "hosts" / f"{host_id}.json"
    _atomic_json(path, {
        "schema_version": SCHEMA_VERSION,
        "host": host_id,
        "heartbeat_at": at,
        "sessions_observed_at": cached.get("observed_at"),
        "queues": {"spool_pending": int(spool_pending)},
        "sync": {"at": sync_at or at, "error": str(sync_error or "")[:300]},
        "sessions": cached.get("sessions") if isinstance(cached.get("sessions"), list) else [],
        "diagnostics": cached.get("diagnostics") if isinstance(cached.get("diagnostics"), list) else [],
    })
    return path


def load_peers(ledger: Path, local_host: str, *, now: float, stale_after: float = 180) -> tuple[list[dict], list[dict]]:
    sessions, diagnostics = [], []
    root = Path(ledger) / "hosts"
    for path in sorted(root.glob("*.json")) if root.exists() else []:
        try:
            value = json.loads(path.read_text())
        except (OSError, ValueError, TypeError):
            diagnostics.append({"host": path.stem, "classification": "invalid", "reason": "malformed host snapshot"})
            continue
        host = value.get("host") if isinstance(value, dict) else None
        if not host or host == local_host or value.get("schema_version") != SCHEMA_VERSION:
            continue
        try:
            heartbeat = datetime.fromisoformat(value["heartbeat_at"]).timestamp()
        except (KeyError, TypeError, ValueError):
            heartbeat = 0
        stale = not heartbeat or now - heartbeat > stale_after
        queue = (value.get("queues") or {}).get("spool_pending")
        sync = value.get("sync") if isinstance(value.get("sync"), dict) else {}
        diagnostics.append({"host": host, "classification": "host-state", "reason": "peer host state",
                            "heartbeat_at": value.get("heartbeat_at"),
                            "queue": int(queue) if isinstance(queue, int) else 0,
                            "sync_error": str(sync.get("error") or "")[:300], "sync_at": sync.get("at")})
        excluded = 0
        for raw in value.get("sessions", []):
            if not isinstance(raw, dict) or raw.get("host") != host or not raw.get("session_key"):
                continue
            classification = raw.get("classification")
            interactive = classification == "local-live" or (classification is None and raw.get("kind") == "claude"
                                                                and raw.get("live") is True)
            if not raw.get("is_summary") and not interactive:
                excluded += 1
                continue
            row = _summary(raw)
            row["remote"] = True
            row["snapshot_age_s"] = int(max(0, now - heartbeat)) if heartbeat else None
            if stale:
                row["live"] = False
                row["status"] = "unknown"
                row["liveness_reason"] = "peer host snapshot is stale"
                row["transport"] = {"available": False, "kind": "unavailable", "reason": "peer host snapshot is stale"}
            sessions.append(row)
        if excluded:
            diagnostics.append({"host": host, "classification": "historical-runs",
                                "reason": f"{excluded} historical/noninteractive row(s) counted, not shown"})
        for raw in value.get("diagnostics", []):
            if isinstance(raw, dict):
                diagnostics.append({"host": host, "classification": raw.get("classification", "unknown"),
                                    "reason": raw.get("reason", "peer diagnostic")})
        if stale:
            diagnostics.append({"host": host, "classification": "peer-stale", "reason": "host snapshot is stale"})
    return sessions, diagnostics

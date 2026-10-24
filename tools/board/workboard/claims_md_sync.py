"""Continuous CLAIMS.md -> ledger sync, run by `board sync` on every host.

Reads the newest CLAIMS.md from the playbook's remote (so both servers' rows count), and for every known task
whose latest row changed since last time, queues a `note` event: {legacy_owner, status, updated, live, expires_at}.
The projection shows LEGACY owners for live rows and clears them when the latest row is finished.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import events, gitutil, legacy


def read_latest(cfg) -> str | None:
    path = Path(cfg.legacy.claims_md).expanduser() if cfg.legacy.claims_md else None
    if not path:
        return None
    top = gitutil.run(path.parent, "rev-parse", "--show-toplevel", timeout=10)
    if top.returncode == 0:
        root = top.stdout.strip()
        rel = str(path.resolve().relative_to(Path(root).resolve()))
        gitutil.run(root, "fetch", "-q", "origin", timeout=30)
        for ref in ("origin/HEAD", "origin/master", "origin/main"):
            shown = gitutil.run(root, "show", f"{ref}:{rel}", timeout=20)
            if shown.returncode == 0:
                return shown.stdout
    try:
        return path.read_text()
    except OSError:
        return None


def sync(cfg, state_dir: Path, host_id: str, known: set[str], *, now: datetime | None = None,
         text: str | None = None, days: int = 7) -> int:
    now = now or datetime.now(timezone.utc)
    text = text if text is not None else read_latest(cfg)
    if not text:
        return 0
    state_path = Path(state_dir) / "claims-md-state.json"
    try:
        seen = json.loads(state_path.read_text())
    except (OSError, ValueError):
        seen = {}
    actor = {"session_id": f"claims-md@{host_id}", "alias": f"{host_id}·CLAIMS.md", "kind": "human"}
    n = 0
    for task, row in legacy.latest_rows(legacy.parse_claims_md(text), known).items():
        live = legacy.is_live(row, now, days)
        h = legacy.row_hash(row) + ("L" if live else "D")
        if seen.get(task) == h:
            continue
        try:
            expires = (datetime.fromisoformat(row["updated"]).replace(tzinfo=timezone.utc) + timedelta(days=days)).isoformat()
        except ValueError:
            continue
        ev = events.new_event("note", task, {"legacy_owner": row["machine"], "status": row["status"],
                                             "updated": row["updated"], "live": live, "expires_at": expires,
                                             "text": row["note"]}, actor=actor, commit=None, source="claims-md")
        if events.spool_append(Path(state_dir), ev):
            seen[task] = h
            n += 1
    try:
        state_path.write_text(json.dumps(seen))
    except OSError:
        pass
    return n

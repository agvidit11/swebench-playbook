"""One-time import of live rows from a free-text claims ledger (CLAIMS.md) as advisory "legacy" owners."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

LIVE = {"ACTIVE", "CLAIMED", "BUILDING", "OWNED", "HELD", "PROBING", "PUSHED", "BUILT", "READY", "READY-LOCAL",
        "PASSING", "BLOCKED", "TAKING", "ACTIVE-PIVOT-2STEP"}


def parse_claims_md(text: str) -> list[dict]:
    """Rows of the markdown table: machine | task | repo | seam | lane | status | updated | note."""
    rows = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---") or "task-or-card" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        status = cells[5].split()[0].rstrip(":").upper() if cells[5] else ""
        rows.append({"machine": cells[0], "task": cells[1], "status": status, "updated": cells[6],
                     "note": cells[7][:160] if len(cells) > 7 else ""})
    return rows


def live_rows(rows, known_tasks: set[str], now: datetime, days: int = 7) -> list[dict]:
    """Latest row per known task, kept only if its status is live and it was updated within `days`."""
    latest = {}
    for r in rows:
        if r["task"] in known_tasks:
            latest[r["task"]] = r                 # later rows win (file is append-ordered)
    out = []
    for task, r in latest.items():
        try:
            upd = datetime.fromisoformat(r["updated"][:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if r["status"] in LIVE and now - upd <= timedelta(days=days):
            out.append(r)
    return out

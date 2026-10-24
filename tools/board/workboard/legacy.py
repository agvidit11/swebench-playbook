"""Owners from a free-text claims ledger (CLAIMS.md), kept in sync continuously by `board sync`.

The ledger is written by many sessions, so parsing is tolerant: the date column is located by its shape (notes may
contain `|`), task names are normalised (`foo (MT3)`, `foo-review-audit` -> `foo` when `foo` is a known task), and a
row means "someone is on it" unless its status is in an explicit finished vocabulary.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

DEAD = {"RELEASED", "PARKED", "PARKED-TOO-EASY", "EXHAUSTED", "KILLED", "RETIRED", "ARCHIVED", "DONE", "ACCEPTED",
        "SUBMITTED", "HANDED-OFF", "HANDED", "DROPPED", "FAILED", "NOT", "ABANDONED", "CLOSED", "STOOD-DOWN"}
ACTIVE = {"OWNED", "CLAIMED", "ACTIVE", "ACTIVE-REVISION", "ACTIVE-PIVOT-2STEP", "TAKING", "FIXING", "BUILDING",
          "PROBING", "WORKING", "IN-PROGRESS", "REWORKING"}      # someone is on it now
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _status_word(cell: str) -> str:
    w = cell.strip().split()[0] if cell.strip() else ""
    return re.sub(r"[^A-Z0-9-]", "", w.upper())


def parse_claims_md(text: str) -> list[dict]:
    """Rows: machine | task | ... | status | updated(date) | note. Finds the date cell by shape."""
    rows = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---") or "task-or-card" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        di = next((i for i, c in enumerate(cells[2:], 2) if DATE.match(c)), None)
        if di is None or di < 3:
            continue
        rows.append({"machine": cells[0], "task": cells[1], "status": _status_word(cells[di - 1]),
                     "updated": cells[di][:10], "note": " | ".join(cells[di + 1:])[:160]})
    return rows


def normalise_task(raw: str, known: set[str]) -> str | None:
    """Map a ledger task-or-card cell onto a known task name (longest known name that the cell starts with)."""
    name = re.sub(r"\s*\(.*$", "", raw.strip())                 # drop "(MT3, slug tentative)" etc.
    name = name.split()[0] if name.split() else ""
    if name in known:
        return name
    best = max((k for k in known if name.startswith(k + "-") or name.startswith(k + "_")), key=len, default=None)
    return best


def latest_rows(rows, known: set[str]) -> dict[str, dict]:
    latest = {}
    for r in rows:
        task = normalise_task(r["task"], known)
        if task:
            latest[task] = dict(r, task=task)                    # later rows win (file is append-ordered)
    return latest


def is_live(row: dict, now: datetime, days: int = 7) -> bool:
    try:
        upd = datetime.fromisoformat(row["updated"]).replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return row["status"] in ACTIVE and timedelta(0) <= now - upd <= timedelta(days=days)


def live_rows(rows, known_tasks: set[str], now: datetime, days: int = 7) -> list[dict]:
    return [r for r in latest_rows(rows, known_tasks).values() if is_live(r, now, days)]


def row_hash(row: dict) -> str:
    return hashlib.sha256(f"{row['machine']}|{row['status']}|{row['updated']}".encode()).hexdigest()[:12]

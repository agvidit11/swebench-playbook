"""Stats. Definitions are printed with every section; nothing estimated is shown as exact.

Accepted = status accepted or used_in_training (or archived after either), dated by reviewedAt, in the user's
timezone weeks (Monday start). Submitted = entered the review pool (enteredPoolAt). Worked on = created.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

from .projection import ts

ACCEPTED = {"accepted", "used_in_training"}
DEFINITIONS = ("accepted = status accepted/used_in_training, dated by reviewedAt; submitted = enteredPoolAt; "
               "worked on = createdAt; weeks Monday-start in {tz}")


def week_start(dt: datetime, tz: ZoneInfo) -> datetime:
    local = dt.astimezone(tz)
    return (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _rows(observations):
    return [o for o in observations if o.source == "codimango"]


def is_accepted(f) -> bool:
    return f.get("codimango.status") in ACCEPTED or f.get("codimango.status_before_archive") in ACCEPTED


def is_mt(f) -> bool:
    return "multi" in (f.get("codimango.track") or "")


def accepted_times(observations) -> list[tuple[datetime, str]]:
    out = []
    for o in _rows(observations):
        if is_accepted(o.fields):
            at = ts(o.fields.get("codimango.reviewed_at"))
            if at:
                out.append((at, o.fields.get("codimango.track") or ""))
    return out


def weekly(observations, cfg, now: datetime, weeks: int = 8) -> list[dict]:
    tz = ZoneInfo(cfg.user.timezone)
    this_mon = week_start(now, tz)
    starts = [this_mon - timedelta(days=7 * k) for k in range(weeks - 1, -1, -1)]
    table = [{"week": s, "accepted": 0, "accepted_mt": 0, "accepted_st": 0, "submitted": 0, "worked_on": 0} for s in starts]

    def slot(t):
        if t is None:
            return None
        ws = week_start(t, tz)
        for row in table:
            if row["week"] == ws:
                return row
        return None

    for o in _rows(observations):
        f = o.fields
        if is_accepted(f):
            row = slot(ts(f.get("codimango.reviewed_at")))
            if row:
                row["accepted"] += 1
                row["accepted_mt" if is_mt(f) else "accepted_st"] += 1
        if f.get("codimango.status") != "draft":
            row = slot(ts(f.get("codimango.entered_pool_at")))
            if row:
                row["submitted"] += 1
        row = slot(ts(f.get("codimango.created_at")))
        if row:
            row["worked_on"] += 1
    return table


def week_numbers(observations, cfg, now: datetime) -> dict:
    tz = ZoneInfo(cfg.user.timezone)
    times = [t for t, _ in accepted_times(observations)]
    this_mon = week_start(now, tz)
    elapsed = now.astimezone(tz) - this_mon
    last_mon = this_mon - timedelta(days=7)
    full = [sum(1 for t in times if this_mon - timedelta(days=7 * k) <= t < this_mon - timedelta(days=7 * (k - 1)))
            for k in range(1, 5)]
    return {"week": this_mon.isocalendar()[1], "this_week": sum(1 for t in times if t >= this_mon),
            "same_point_last_week": sum(1 for t in times if last_mon <= t < last_mon + elapsed),
            "median_4wk": median(full), "total": len(times)}


def week_header(observations, cfg, now: datetime) -> str:
    n = week_numbers(observations, cfg, now)
    return (f"W{n['week']}: {n['this_week']} accepted  ·  last week at this point {n['same_point_last_week']}  ·  "
            f"4-week median {n['median_4wk']:g}  (accepted incl. used_in_training, by acceptance date)")


def funnel(observations) -> dict:
    """Exact sources only: built = task dirs in git; status counts from codimango (archived included)."""
    git_tasks = {o.entity_id for o in observations if o.source == "git" and not o.entity_id.startswith("__repo__:")}
    cm = _rows(observations)
    status = {}
    for o in cm:
        status[o.fields.get("codimango.status")] = status.get(o.fields.get("codimango.status"), 0) + 1
    submitted = sum(1 for o in cm if o.fields.get("codimango.entered_pool_at"))
    return {"built": len(git_tasks), "imported": len(cm), "submitted": submitted,
            "accepted": sum(1 for o in cm if is_accepted(o.fields)),
            "archived": status.get("archived", 0),
            "archived_after_accept": sum(1 for o in cm if o.fields.get("codimango.status") == "archived"
                                         and o.fields.get("codimango.status_before_archive") in ACCEPTED),
            "open": sum(v for k, v in status.items() if k not in ACCEPTED | {"archived"}),
            "by_status": status}


def pipeline_age(views, now) -> dict[str, dict]:
    out = {}
    for v in views:
        st, age = v.fields.get("state"), v.fields.get("state_age_s")
        if st in ("ACCEPTED", "ARCHIVED") or age is None:
            continue
        out.setdefault(st, []).append(age)
    return {k: {"count": len(a), "median_h": round(median(a) / 3600, 1), "max_h": round(max(a) / 3600, 1)}
            for k, a in sorted(out.items())}


# ---------------------------------------------------------------------------------------------- quality
REVIEWS_CACHE = "reviews-cache.json"


def _reviews_cache(cache_dir: Path) -> dict:
    try:
        return json.loads((cache_dir / REVIEWS_CACHE).read_text())
    except (OSError, ValueError):
        return {}


def _save_reviews_cache(cache_dir: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=cache_dir, prefix=".rev-")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, cache_dir / REVIEWS_CACHE)


def revision_rounds(cfg, observations, cache_dir: Path, *, fetch=True, runner=subprocess.run, limit: int = 400) -> dict:
    """task -> number of human 'revision' decisions, from `codimango task reviews --full` (cached by updatedAt).
    Returns {"rounds": {...}, "covered": n, "eligible": m}."""
    cache = _reviews_cache(cache_dir)
    eligible = [o for o in _rows(observations) if o.fields.get("codimango.entered_pool_at")]
    rounds = {}
    for o in eligible[:limit]:
        key = f"{o.entity_id}|{o.fields.get('codimango.updated_at')}"
        if key in cache:
            rounds[o.entity_id] = cache[key]
            continue
        if not fetch:
            continue
        try:
            p = runner([cfg.codimango.command, "task", "reviews", o.entity_id, "--full"], capture_output=True,
                       text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if p.returncode != 0:
            continue
        n = len(re.findall(r"^\s*REVISION by", p.stdout, re.M))
        cache[key] = rounds[o.entity_id] = n
    try:
        _save_reviews_cache(cache_dir, cache)
    except OSError:
        pass
    return {"rounds": rounds, "covered": len(rounds), "eligible": len(eligible)}


def first_pass_by_cohort(observations, rounds: dict, cfg) -> list[dict]:
    """Per submission week: decided tasks, accepted with zero revision rounds, rate."""
    tz = ZoneInfo(cfg.user.timezone)
    cohorts = {}
    for o in _rows(observations):
        f = o.fields
        pool = ts(f.get("codimango.entered_pool_at"))
        if not pool or o.entity_id not in rounds:
            continue
        decided = is_accepted(f) or f.get("codimango.status") in ("needs_revision", "archived")
        if not decided:
            continue
        c = cohorts.setdefault(week_start(pool, tz), {"decided": 0, "first_pass": 0})
        c["decided"] += 1
        if is_accepted(f) and rounds[o.entity_id] == 0:
            c["first_pass"] += 1
    return [{"week": w, **c, "rate": round(100 * c["first_pass"] / c["decided"]) if c["decided"] else None}
            for w, c in sorted(cohorts.items())]


# ---------------------------------------------------------------------------------------------- charts
def bar(value: float, top: float, width: int, unicode: bool) -> str:
    if top <= 0:
        return ""
    cells = value / top * width
    if not unicode:
        return "#" * int(round(cells))
    full = int(cells)
    rest = cells - full
    blocks = " ▏▎▍▌▋▊▉"
    return "█" * full + (blocks[int(rest * 8)] if rest and full < width else "")


def spark(values, unicode: bool) -> str:
    if not values:
        return ""
    chars = "▁▂▃▄▅▆▇█" if unicode else "_.-=#"
    top = max(values) or 1
    return "".join(chars[min(len(chars) - 1, int(v / top * (len(chars) - 1)))] for v in values)

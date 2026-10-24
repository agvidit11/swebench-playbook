"""Counting helpers. Accepted = accepted or used_in_training, dated by reviewedAt, in the user's timezone weeks."""
from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median
from zoneinfo import ZoneInfo

from .projection import ts

ACCEPTED = {"accepted", "used_in_training"}


def week_start(dt: datetime, tz: ZoneInfo) -> datetime:
    local = dt.astimezone(tz)
    return (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def accepted_times(observations) -> list[tuple[datetime, str]]:
    out = []
    for o in observations:
        f = o.fields
        if f.get("codimango.status") in ACCEPTED or f.get("codimango.status_before_archive") in ACCEPTED:
            at = ts(f.get("codimango.reviewed_at"))
            if at:
                out.append((at, f.get("codimango.track") or ""))
    return out


def week_header(observations, cfg, now: datetime) -> str:
    tz = ZoneInfo(cfg.user.timezone)
    times = [t for t, _ in accepted_times(observations)]
    this_mon = week_start(now, tz)
    elapsed = now.astimezone(tz) - this_mon
    this_week = sum(1 for t in times if t >= this_mon)
    last_mon = this_mon - timedelta(days=7)
    same_point = sum(1 for t in times if last_mon <= t < last_mon + elapsed)
    full = [sum(1 for t in times if this_mon - timedelta(days=7 * k) <= t < this_mon - timedelta(days=7 * (k - 1)))
            for k in range(1, 5)]
    iso = this_mon.isocalendar()
    return (f"W{iso[1]}: {this_week} accepted  ·  last week at this point {same_point}  ·  "
            f"4-week median {median(full):g}  (accepted incl. used_in_training, by acceptance date)")

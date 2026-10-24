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
DEFINITIONS = ("accepted = current status accepted or used_in_training, dated by reviewedAt; "
               "submitted = has enteredPoolAt (dated by it); worked on = createdAt; MT = multi-turn track, "
               "ST = single-turn; imported = known to codimango; first-submission cycle time = unavailable (codimango keeps only the latest pool entry); latest-round cycle = latest submission -> acceptance; "
               "reviewer wait = submission -> latest human decision (codimango keeps only the latest); "
               "weeks Monday-start in {tz}; timestamps after now are ignored")


def week_start(dt: datetime, tz: ZoneInfo) -> datetime:
    local = dt.astimezone(tz)
    return (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def _rows(observations):
    return [o for o in observations if o.source == "codimango"]


def is_accepted(f) -> bool:
    """Current codimango status only (archived-after-acceptance is reported separately)."""
    return f.get("codimango.status") in ACCEPTED


def is_mt(f) -> bool:
    return "multi" in (f.get("codimango.track") or "")


def _past(t, now):
    return t if (t is not None and (now is None or t <= now)) else None


def accepted_times(observations, now=None) -> list[tuple[datetime, str]]:
    out = []
    for o in _rows(observations):
        if is_accepted(o.fields):
            at = _past(ts(o.fields.get("codimango.reviewed_at")), now)
            if at:
                out.append((at, o.fields.get("codimango.track") or ""))
    return out


def weekly(observations, cfg, now: datetime, weeks: int = 8, start: datetime | None = None,
           end: datetime | None = None) -> list[dict]:
    """Per-week counts. With start/end, weeks covering [start, end) are listed and only events inside count."""
    tz = ZoneInfo(cfg.user.timezone)
    end = min(end, now) if end else now
    if start:
        first, starts = week_start(start, tz), []
        w = first
        while w < end:
            starts.append(w)
            w += timedelta(days=7)
    else:
        this_mon = week_start(end, tz)
        starts = [this_mon - timedelta(days=7 * k) for k in range(weeks - 1, -1, -1)]
    table = [{"week": s, "accepted": 0, "accepted_mt": 0, "accepted_st": 0, "submitted": 0, "worked_on": 0} for s in starts]

    def slot(t):
        if t is None or t >= end or (start and t < start):
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
        row = slot(ts(f.get("codimango.entered_pool_at")))
        if row:
            row["submitted"] += 1
        row = slot(ts(f.get("codimango.created_at")))
        if row:
            row["worked_on"] += 1
    return table


def week_numbers(observations, cfg, now: datetime) -> dict:
    tz = ZoneInfo(cfg.user.timezone)
    times = [t for t, _ in accepted_times(observations, now)]
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
    submitted = sum(1 for o in cm if ts(o.fields.get("codimango.entered_pool_at")))
    return {"built": len(git_tasks), "imported": len(cm), "submitted": submitted,
            "accepted": sum(1 for o in cm if is_accepted(o.fields)),
            "archived": status.get("archived", 0),
            "archived_after_accept": sum(1 for o in cm if o.fields.get("codimango.status") == "archived"
                                         and o.fields.get("codimango.status_before_archive") in ACCEPTED),
            "open": sum(v for k, v in status.items() if k not in ACCEPTED | {"archived"}),
            "by_status": status}


def _pct(values, q):
    if not values:
        return None
    v = sorted(values)
    k = (len(v) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return round((v[lo] + (v[hi] - v[lo]) * (k - lo)) / 3600, 1)


def _in(t, start, end):
    return t is not None and (start is None or t >= start) and (end is None or t < end)


def range_totals(observations, now, start=None, end=None) -> dict:
    end = min(end, now) if end else now
    acc = sub = work = 0
    for o in _rows(observations):
        f = o.fields
        if is_accepted(f) and _in(ts(f.get("codimango.reviewed_at")), start, end):
            acc += 1
        if _in(ts(f.get("codimango.entered_pool_at")), start, end):
            sub += 1
        if _in(ts(f.get("codimango.created_at")), start, end):
            work += 1
    return {"accepted": acc, "submitted": sub, "worked_on": work}


def cycle_and_wait(observations, now, start=None, end=None) -> dict:
    """Cycle time (latest submission -> acceptance) for accepted tasks and reviewer wait (latest submission ->
    latest human decision) for decided tasks, for decisions inside [start, end). codimango keeps only the latest
    pool entry and decision, so these are latest-round measures; coverage is reported."""
    cycle, wait, accepted, decided = [], [], 0, 0
    end = min(end, now) if end else now
    for o in _rows(observations):
        f = o.fields
        pool, rev = ts(f.get("codimango.entered_pool_at")), _past(ts(f.get("codimango.reviewed_at")), now)
        if not _in(rev, start, end):
            continue
        if is_accepted(f):
            accepted += 1
            if pool and rev and rev >= pool:
                cycle.append((rev - pool).total_seconds())
        if f.get("codimango.status") in ACCEPTED | {"needs_revision"}:
            decided += 1
            if pool and rev and rev >= pool:
                wait.append((rev - pool).total_seconds())
    return {"first_submission_cycle": {"available": False, "reason": "codimango keeps only the latest pool entry",
                                       "coverage": f"0/{accepted}"},
            "latest_round_cycle_p50_h": _pct(cycle, .5), "latest_round_cycle_p75_h": _pct(cycle, .75),
            "latest_round_cycle_coverage": f"{len(cycle)}/{accepted}",
            "wait_p50_h": _pct(wait, .5), "wait_p75_h": _pct(wait, .75), "wait_coverage": f"{len(wait)}/{decided}"}


def tasks_per_repo(cfg, task_names, *, runner=None) -> dict:
    """Upstream repo per task from <task>/tests/config.json (or steps/*/tests/config.json) at the fetched ref.
    Always returns {"by_repo", "coverage", "available", "reason"}."""
    from . import gitutil
    counts, covered = {}, 0
    if not cfg.repositories:
        return {"by_repo": {}, "coverage": f"0/{len(task_names)}", "available": False, "reason": "no repositories configured"}
    for repo in cfg.repositories:
        path = Path(repo.path).expanduser()
        ref = f"refs/workboard/{repo.branch}"
        if gitutil.run(path, "rev-parse", "-q", "--verify", ref).returncode != 0:
            ref = f"origin/{repo.branch}"
        listing = gitutil.run(path, "ls-tree", "-r", "--name-only", ref, timeout=60)
        if listing.returncode != 0:
            continue
        files = {}
        for name in listing.stdout.splitlines():
            if name.endswith("tests/config.json"):
                files.setdefault(name.split("/", 1)[0], name)
        for task in task_names:
            fname = files.get(task)
            if not fname:
                continue
            shown = gitutil.run(path, "show", f"{ref}:{fname}", timeout=20)
            try:
                up = json.loads(shown.stdout).get("repo") if shown.returncode == 0 else None
            except (ValueError, AttributeError):
                up = None
            if isinstance(up, str) and up:
                counts[up] = counts.get(up, 0) + 1
                covered += 1
    return {"by_repo": dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))), "coverage": f"{covered}/{len(task_names)}",
            "available": covered > 0, "reason": "" if covered else "no readable tests/config.json with a repo key"}


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


def first_pass_by_cohort(observations, rounds: dict, cfg, start=None, end=None) -> list[dict]:
    """Per submission week: decided tasks, accepted with zero revision rounds, rate."""
    tz = ZoneInfo(cfg.user.timezone)
    cohorts = {}
    for o in _rows(observations):
        f = o.fields
        pool = ts(f.get("codimango.entered_pool_at"))
        if not pool or o.entity_id not in rounds or not _in(pool, start, end):
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

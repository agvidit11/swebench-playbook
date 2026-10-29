"""Stats v2: one compact, exact-where-possible fact table per task; the page aggregates it for any range, grain
and filter (so filters are instant and need no server round trip).

Per task: dimensions (ST/MT, repo, category, current status), lifecycle events (created, every submission from
Codimango system events, every human decision from structured reviews, archived), and activity episodes per local
day: [day, phase, agent kind, model, evidence count, confidence]. Semantics follow /tmp/wb-review/stats/04-design.md:
- worked on = any qualifying activity (commit, strong touch, presubmit, agent review, build launch) that day;
- submitted = "Task was submitted for review (vN)" events; falls back to the current enteredPoolAt (flagged);
- accepted = timestamped accept decisions (survive archival); auto/ATR accepts are a separate series;
- phase/agent attribution carries confidence and an explicit unclassified bucket; models only from native runs.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .projection import ts

PHASES = ("sourcing", "drafting", "calibration", "presubmit", "independent_review", "revision", "draft_fixing",
          "validation_babysit", "submit", "unclassified")
CALIBRATE = re.compile(r"calibrat|tighten|loosen|too (easy|hard)|pass@|band|re-?band|saturat|discriminat|avocado|"
                       r"\b\d/\d\b|step[- ]?\d gate", re.I)
FIX = re.compile(r"\bfix|repair|unblock|address|resolve|correct", re.I)
SOURCING = {"CARD", "PROBING", "SOURCING", "SCOUTING", "IDEA", "CANDIDATE"}
WINDOW = timedelta(minutes=45)


def _day(dt: datetime, tz: ZoneInfo) -> str:
    return dt.astimezone(tz).date().isoformat()


def _git_commits(cfg, cache_dir: Path) -> dict[str, list[dict]]:
    """task -> [{sha, at, subject, paths}] (newest last), cached by repo HEAD."""
    out: dict[str, list[dict]] = {}
    for repo in cfg.repositories:
        path = Path(repo.path).expanduser()
        ref = f"refs/workboard/{repo.branch}"
        head = subprocess.run(["git", "-C", str(path), "rev-parse", "-q", "--verify", ref], capture_output=True,
                              text=True)
        if head.returncode != 0:
            ref = f"origin/{repo.branch}"
            head = subprocess.run(["git", "-C", str(path), "rev-parse", ref], capture_output=True, text=True)
        key = head.stdout.strip()
        cache = Path(cache_dir) / f"stats-git-{repo.id}.json"
        try:
            data = json.loads(cache.read_text())
            if data.get("head") == key:
                for t, rows in data["tasks"].items():
                    out.setdefault(t, []).extend(rows)
                continue
        except (OSError, ValueError):
            pass
        log = subprocess.run(["git", "-C", str(path), "log", ref, "--reverse", "--format=@%H\t%cI\t%s", "--name-only"],
                             capture_output=True, text=True, timeout=120)
        tasks: dict[str, list[dict]] = {}
        cur = None
        for line in log.stdout.splitlines():
            if line.startswith("@"):
                sha, at, subj = (line[1:].split("\t", 2) + ["", ""])[:3]
                cur = {"sha": sha[:10], "at": at, "subject": subj[:140], "by_task": {}}
            elif line and "/" in line and cur:
                task, rest = line.split("/", 1)
                if task.startswith("."):
                    continue
                if task not in cur["by_task"]:
                    cur["by_task"][task] = []
                    tasks.setdefault(task, []).append({"sha": cur["sha"], "at": cur["at"], "subject": cur["subject"],
                                                       "paths": cur["by_task"][task]})
                cur["by_task"][task].append(rest)
        try:
            cache.write_text(json.dumps({"head": key, "tasks": tasks}))
        except OSError:
            pass
        for t, rows in tasks.items():
            out.setdefault(t, []).extend(rows)
    return out


def _groups(paths: list[str]) -> set[str]:
    g = set()
    for p in paths:
        if p.startswith("instruction") or "/instruction" in p or p.startswith("steps/"):
            g.add("spec")
        if p.startswith("tests/") or "/tests/" in p:
            g.add("tests")
        if p.startswith("solution/") or "/solution/" in p:
            g.add("solution")
        if p.startswith("environment/"):
            g.add("env")
        if p in ("task.toml",) or p.endswith("config.json"):
            g.add("config")
        if p.lower().startswith("readme"):
            g.add("readme")
    return g


def _windows(decisions, submits):
    """Ordered lifecycle boundaries: [(at, 'submit'|'revision'|'accept'...)]."""
    marks = [(ts(s["at"]), "submit") for s in submits if ts(s["at"])]
    marks += [(ts(d["at"]), d["decision"]) for d in decisions if ts(d["at"])]
    return sorted(marks)


def _failing_at(vals: list[tuple[datetime, bool]], at: datetime) -> bool:
    """Validation state just before `at` from ordered (time, failing) observations."""
    state = False
    for when, failing in vals:
        if when > at:
            break
        state = failing
    return state


def _phase_for_commit(c, at, marks, vals: list[tuple[datetime, bool]]) -> tuple[str, str]:
    """(phase, confidence) for a commit by timeline position, then content."""
    state = "draft"
    for when, kind in marks:
        if when > at:
            break
        state = {"submit": "submitted", "revision": "revision", "reject": "revision", "accept": "accepted",
                 "atr_accept": "accepted"}.get(kind, state)
    groups = _groups(c["paths"])
    if state == "revision":
        return "revision", "high"
    if groups == {"readme"}:
        return "drafting" if state == "draft" else "unclassified", "low"
    if CALIBRATE.search(c["subject"]) and groups & {"tests", "spec", "config", "solution"}:
        return "calibration", "medium"
    if state == "draft" and _failing_at(vals, at) and FIX.search(c["subject"]):
        return "draft_fixing", "medium"
    if state == "draft":
        return "drafting", "medium"
    return "unclassified", "low"


def _agent_near(at: datetime, task_events: list[dict], runs: list[dict]) -> tuple[str, str | None, str]:
    """(kind, model, confidence) of the session that touched the task closest to `at`."""
    best = None
    for e in task_events:
        if e["type"] not in ("touch", "build_action", "check", "review", "claim", "renew") or \
                (e.get("payload") or {}).get("weak"):
            continue
        when = ts(e.get("occurred_at"))
        if when and abs(when - at) <= WINDOW and (best is None or abs(when - at) < abs(best[0] - at)):
            best = (when, e)
    kind = ((best[1].get("actor") or {}).get("kind") if best else None) or "unknown"
    if best and best[1]["type"] == "build_action":
        kind = (best[1].get("payload") or {}).get("model") or kind      # codex/muse launched on the task
    model, cands = None, []
    for r in runs:
        st, la = ts(r.get("started_at")), ts(r.get("last_activity_at")) or ts(r.get("started_at"))
        if st and la and st - WINDOW <= at <= la + WINDOW and kind in ("unknown", r.get("kind")):
            gap = timedelta(0) if st <= at <= la else min(abs(at - st), abs(at - la))
            cands.append((gap, r))
    if cands:
        cands.sort(key=lambda x: x[0])
        if len(cands) == 1 or cands[0][0] < cands[1][0]:   # a tie between runs stays ambiguous: kind only
            kind, model = cands[0][1].get("kind") or kind, _model_name(cands[0][1].get("model"))
    conf = "high" if model else "medium" if best else "unknown"
    return kind if kind in ("claude", "codex", "muse", "human") else "unknown", model, conf


def build(snap, cfg, cache_dir: Path, *, facts_rows: list[dict] | None = None) -> dict:
    from . import facts as facts_mod
    tz = ZoneInfo(getattr(cfg.user, "timezone", "") or "America/Los_Angeles")
    store = facts_mod.Store(cache_dir)
    rows = facts_rows if facts_rows is not None else store.read()
    by_task: dict[str, list[dict]] = {}
    for f in rows:
        by_task.setdefault(f["task"], []).append(f)
    obs: dict[str, dict] = {}
    for ob in snap.observations:
        obs.setdefault(ob.entity_id, {}).update(ob.fields)
    ev_by_task: dict[str, list[dict]] = {}
    for e in snap.events:
        ent = e.get("entity") or {}
        if ent.get("id"):
            ev_by_task.setdefault(ent["id"], []).append(e)
    runs_by_task: dict[str, list[dict]] = {}
    for sv_sessions in [getattr(snap, "sessions", []) or []]:
        for s in sv_sessions:
            for r in (s.get("child_runs") or []) + ([s] if s.get("kind") in ("codex", "muse") else []):
                t = r.get("cwd_task") or r.get("task")
                if t:
                    runs_by_task.setdefault(t, []).append(r)
    commits = _git_commits(cfg, cache_dir)
    names = sorted({n for n, f in obs.items() if any(k.startswith("codimango.") for k in f)} |
                   {t for t in commits if t in obs} | set(by_task))           # historical-only tasks stay visible
    cm_rows = [{"name": n, "updated_at": f.get("codimango.updated_at"), "entered_pool_at": f.get("codimango.entered_pool_at"),
                "reviewed_at": f.get("codimango.reviewed_at"), "status": f.get("codimango.status")}
               for n, f in obs.items() if any(k.startswith("codimango.") for k in f)]
    cov = facts_mod.coverage(store, cm_rows)
    out_tasks, repo_cache = [], {}
    sub_cov = eligible = 0
    for name in names:
        cm = obs.get(name, {})
        fs = by_task.get(name, [])
        subs = [{"at": f["occurred_at"], "v": f["value"].get("version"), "ev": f["value"]["event"]}
                for f in facts_mod.latest(fs, "submission") if f["occurred_at"]]
        submits = [x for x in subs if x["ev"] in ("first_submit", "resubmit")]
        claimed = [x["at"] for x in subs if x["ev"] == "review_claimed"]
        decisions = [{"at": f["occurred_at"], "decision": f["value"]["decision"], "reason": f["value"].get("reason")}
                     for f in facts_mod.latest(fs, "review_decision") if f["occurred_at"]]
        pool = cm.get("codimango.entered_pool_at")
        status = cm.get("codimango.status") or ("archived" if cm.get("codimango.archived_at") else None)
        last_status = max((f for f in fs if f["kind"] == "status"), key=lambda f: f["observed_at"], default=None)
        if not status and last_status:
            status = last_status["value"].get("status")
        tc = cov["tasks"].get(name, {})
        rc = bool(tc.get("current") and tc.get("complete") and not tc.get("error"))
        fallback_submit = not submits and bool(pool)
        if name in cov["tasks"]:
            eligible += 1
            sub_cov += bool(submits)
        if fallback_submit:
            submits = [{"at": pool, "v": None, "ev": "first_submit"}]
        reviewed = cm.get("codimango.reviewed_at")
        if not any(d["decision"] in ("accept", "atr_accept") for d in decisions) and \
                status in ("accepted", "used_in_training") and reviewed:
            decisions.append({"at": reviewed, "decision": "accept_fb", "reason": None})   # not a human decision
            decisions.sort(key=lambda d: d["at"])
        marks = _windows([d for d in decisions if d["decision"] != "accept_fb"], submits)
        vals = sorted(((ts(f["occurred_at"]) or ts((f.get("interval") or {}).get("at_or_before")) or ts(f["observed_at"]),
                        str(f["value"].get("validation")).lower() in ("failing", "failed", "fail")) for f in fs
                       if f["kind"] == "validation"), key=lambda x: x[0])
        tev = ev_by_task.get(name, [])
        runs = runs_by_task.get(name, [])
        episodes: dict[tuple, list] = {}

        def add(at, phase, kind, model, pconf, aconf, src):
            key = (_day(at, tz), phase, kind, model or "")
            cur = episodes.setdefault(key, [0, pconf, set(), at, aconf])
            cur[0] += 1
            cur[2].add(src)
            cur[3] = min(cur[3], at)
            rank = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
            if rank[pconf] > rank[cur[1]]:
                cur[1] = pconf
            if rank[aconf] > rank[cur[4]]:
                cur[4] = aconf

        for c in commits.get(name, []):
            at = ts(c["at"])
            if not at:
                continue
            phase, pconf = _phase_for_commit(c, at, marks, vals)
            kind, model, aconf = _agent_near(at, tev, runs)
            add(at, phase, kind, model, pconf, aconf, "commit")
        for e in tev:
            at = ts(e.get("occurred_at"))
            if not at:
                continue
            actor = e.get("actor") or {}
            kind = actor.get("kind") if actor.get("kind") in ("claude", "codex", "muse", "human") else "unknown"
            pl = e.get("payload") or {}
            if e["type"] in ("check", "review"):
                from .roles import role_of
                role = role_of(e, tev)
                add(at, "independent_review" if role == "independent" else "presubmit", kind, None, "high", "high", e["type"])
            elif e["type"] == "build_action":
                add(at, "unclassified", pl.get("model") or kind, None, "unknown", "medium", "build")
            elif e["type"] == "touch" and not pl.get("weak"):
                add(at, "unclassified", kind, None, "unknown", "high", "touch")
            elif e["type"] == "note" and str(pl.get("status") or "").upper() in SOURCING:
                add(at, "sourcing", "unknown", None, "medium", "unknown", "claims_md")
        for x in submits:
            at = ts(x["at"])
            if at:
                add(at, "submit", "unknown", None, "high" if not fallback_submit else "low", "unknown", "submission")
        act = [[d, ph, k, m or None, v[0], v[1], sorted(v[2]), v[3].isoformat(timespec="seconds"), v[4]]
               for (d, ph, k, m), v in sorted(episodes.items())]
        # when the task entered its current state (exact when a boundary event exists, else a labelled proxy)
        se, se_exact = None, False
        if status == "being_reviewed" and claimed and (not submits or claimed[-1] >= submits[-1]["at"]):
            se, se_exact = claimed[-1], True
        elif status in ("needs_reviewers_assigned", "being_reviewed") and submits:
            se, se_exact = submits[-1]["at"], not fallback_submit
        elif status == "needs_revision":
            rev = [d["at"] for d in decisions if d["decision"] == "revision"]
            se, se_exact = (rev[-1], True) if rev else (reviewed, False)
        elif last_status and last_status["value"].get("status") == status:
            se = last_status["occurred_at"] or (last_status.get("interval") or {}).get("at_or_before")
            se_exact = bool(last_status["occurred_at"])
        if not se:
            se = cm.get("codimango.created_at")
        vt = []                                    # validation failed / cleared transitions (interval-censored)
        prev_fail = None
        for when, failing in vals:
            if prev_fail is not None and failing != prev_fail:
                vt.append([when.isoformat(timespec="seconds"), "VF" if failing else "VP"])
            prev_fail = failing
        repo = repo_cache.get(name)
        if repo is None:
            repo = _repo_of(cfg, name)
            repo_cache[name] = repo
        fmt = str(cm.get("codimango.format") or cm.get("codimango.track") or "")
        out_tasks.append({
            "t": name, "k": "mt" if "multi" in fmt else "st" if fmt else "unknown", "r": repo or "unknown",
            "c": cm.get("codimango.category") or "unknown", "s": status or "not_imported",
            "cr": cm.get("codimango.created_at") or (commits.get(name, [{}])[0].get("at")),
            "ar": cm.get("codimango.archived_at"), "rc": rc, "se": se, "sex": se_exact, "vt": vt,
            "sub": [[x["at"], x["v"]] for x in submits], "subfb": fallback_submit, "cl": claimed,
            "dec": [[d["at"], d["decision"], (d.get("reason") or "")[:120]] for d in decisions],
            "act": act,
        })
    usage = getattr(snap, "usage", {}) or {}
    acc = usage.get("accounting", {}) or {}
    models: dict[tuple, int] = {}
    for s in getattr(snap, "sessions", []) or []:
        for r in [s] + (s.get("child_runs") or []):
            tok = (r.get("tokens") or {}).get("counters") or {}
            if tok.get("total"):
                key = (r.get("kind") or "unknown", _model_name((r.get("tokens") or {}).get("model") or r.get("model")))
                models[key] = models.get(key, 0) + int(tok["total"])
    snap_at = snap.health.get("codimango").observed_at.isoformat() if snap.health.get("codimango") and \
        snap.health["codimango"].observed_at else None
    phase_rows = sum(a[4] for t in out_tasks for a in t["act"] if a[1] != "submit")
    classified = sum(a[4] for t in out_tasks for a in t["act"] if a[1] not in ("unclassified", "submit"))
    model_rows = sum(a[4] for t in out_tasks for a in t["act"] if a[3])
    ledger_start = min((e.get("occurred_at") for e in snap.events if e.get("occurred_at")), default=None)
    return {
        "schema_version": 2, "generated_at": snap.now.isoformat(), "timezone": str(tz), "phases": list(PHASES),
        "ledger_start": ledger_start, "tasks": out_tasks,
        "tokens": {"daily": usage.get("daily", []), "accounting": acc,
                   "models": [[k, m, v] for (k, m), v in sorted(models.items(), key=lambda x: -x[1])]},
        "quality": [
            {"id": "snapshot", "label": "Snapshot", "covered": len(out_tasks), "eligible": len(out_tasks),
             "fresh_at": snap_at, "status": "exact"},
            {"id": "submissions", "label": "Submissions", "covered": sub_cov, "eligible": eligible,
             "status": "exact" if sub_cov == eligible else "partial",
             "reason": f"{eligible - sub_cov} tasks still use the latest enteredPoolAt" if sub_cov < eligible else ""},
            {"id": "reviews", "label": "Reviews", "covered": cov["covered"], "eligible": cov["eligible"],
             "status": "exact" if cov["covered"] == cov["eligible"] else "partial",
             "reason": ", ".join(x for x in (f"{cov['pending']} waiting for refresh" if cov["pending"] else "",
                                             f"{cov['errors']} last refresh failed" if cov["errors"] else "") if x)},
            {"id": "phases", "label": "Phases", "covered": classified, "eligible": phase_rows, "status": "estimated",
             "reason": f"{phase_rows - classified} of {phase_rows} activity records unclassified; exact model on {model_rows}"},
            {"id": "tokens", "label": "Tokens", "covered": acc.get("attributed", 0), "eligible": acc.get("total", 0),
             "status": "partial", "reason": f"{acc.get('coverage_pct', 0)}% of reported tokens linked to tasks"},
            _peers(cache_dir)],
        "peers": _peer_rows(cache_dir),
    }


def _model_name(m) -> str:
    """Muse sometimes reports its model as a stringified dict; keep just the model id."""
    m = str(m or "unknown")
    hit = re.search(r"model_id['\"]?\s*[:=]\s*['\"]([^'\"]+)", m)
    return hit.group(1) if hit else m


def _repo_of(cfg, task: str) -> str | None:
    for repo in cfg.repositories:
        p = Path(repo.path).expanduser() / task / "tests" / "config.json"
        try:
            data = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        for key in ("repo", "repository", "repo_name"):
            if isinstance(data.get(key), str):
                return data[key]
    return None


def _peer_rows(cache_dir: Path) -> list[dict]:
    try:
        return json.loads((Path(cache_dir) / "rank-cache.json").read_text()).get("rows", [])
    except (OSError, ValueError):
        return []


def _peers(cache_dir: Path) -> dict:
    rows = _peer_rows(cache_dir)
    return {"id": "peers", "label": "Peers", "covered": len(rows), "eligible": len(rows) or 1,
            "status": "exact" if rows else "unavailable",
            "reason": "" if rows else "not connected: board rank import <file>, or set [rank] daiquery_id"}

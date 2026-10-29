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


def _phase_for_commit(c, at, marks, validation_fail_before: datetime | None) -> tuple[str, str]:
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
    if state == "draft" and validation_fail_before and at >= validation_fail_before and FIX.search(c["subject"]):
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
    model = None
    for r in runs:
        st, la = ts(r.get("started_at")), ts(r.get("last_activity_at")) or ts(r.get("started_at"))
        if st and la and st - WINDOW <= at <= la + WINDOW and (kind in ("unknown", r.get("kind"))):
            kind, model = r.get("kind") or kind, r.get("model")
            break
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
                   {t for t in commits if t in obs})
    out_tasks, repo_cache = [], {}
    sub_cov = dec_cov = eligible = 0
    hyd = facts_mod.coverage(store).get("hydrated", {})
    for name in names:
        cm = obs.get(name, {})
        fs = by_task.get(name, [])
        subs = sorted(({"at": f["occurred_at"], "v": f["value"].get("version"), "ev": f["value"]["event"]}
                       for f in fs if f["kind"] == "submission" and f["occurred_at"]), key=lambda x: x["at"])
        submits = [s for s in subs if s["ev"] in ("first_submit", "resubmit")]
        claimed = [s["at"] for s in subs if s["ev"] == "review_claimed"]
        decisions = sorted(({"at": f["occurred_at"], "decision": f["value"]["decision"],
                             "reason": f["value"].get("reason")} for f in fs if f["kind"] == "review_decision"),
                           key=lambda x: x["at"])
        pool = cm.get("codimango.entered_pool_at")
        status = cm.get("codimango.status") or ("archived" if cm.get("codimango.archived_at") else None)
        fallback_submit = not submits and bool(pool)
        if pool or decisions:
            eligible += 1
            sub_cov += bool(submits)
            dec_cov += bool(hyd.get(name, {}).get("complete"))
        if fallback_submit:
            submits = [{"at": pool, "v": None, "ev": "first_submit"}]
        reviewed = cm.get("codimango.reviewed_at")
        if not decisions and status in ("accepted", "used_in_training") and reviewed:
            decisions = [{"at": reviewed, "decision": "accept", "reason": None, "fallback": True}]
        marks = _windows(decisions, submits)
        vfail = [ts(f["observed_at"]) for f in fs if f["kind"] == "validation" and
                 str(f["value"].get("validation")).lower() in ("failing", "failed", "fail")]
        tev = ev_by_task.get(name, [])
        runs = runs_by_task.get(name, [])
        episodes: dict[tuple, list] = {}

        def add(at, phase, kind, model, conf, src):
            key = (_day(at, tz), phase, kind, model or "")
            cur = episodes.setdefault(key, [0, conf, set()])
            cur[0] += 1
            cur[2].add(src)
            if conf == "high" or (conf == "medium" and cur[1] in ("low", "unknown")):
                cur[1] = conf

        for c in commits.get(name, []):
            at = ts(c["at"])
            if not at:
                continue
            phase, conf = _phase_for_commit(c, at, marks, min(vfail) if vfail else None)
            kind, model, aconf = _agent_near(at, tev, runs)
            add(at, phase, kind, model, conf if aconf != "unknown" else ("low" if conf != "high" else "medium"), "commit")
        for e in tev:
            at = ts(e.get("occurred_at"))
            if not at:
                continue
            actor = e.get("actor") or {}
            kind = actor.get("kind") if actor.get("kind") in ("claude", "codex", "muse", "human") else "unknown"
            p = e.get("payload") or {}
            if e["type"] in ("check", "review"):
                from .roles import role_of
                role = role_of(e, tev)
                add(at, "independent_review" if role == "independent" else "presubmit", kind, None, "high", e["type"])
            elif e["type"] == "build_action":
                add(at, "unclassified", p.get("model") or kind, None, "medium", "build")
            elif e["type"] == "touch" and not p.get("weak"):
                add(at, "unclassified", kind, None, "low", "touch")
            elif e["type"] == "note" and str(p.get("status") or "").upper() in SOURCING:
                add(at, "sourcing", "unknown", None, "medium", "claims_md")
        for s in submits:
            at = ts(s["at"])
            if at:
                add(at, "submit", "human", None, "high" if not fallback_submit else "low", "submission")
        act = [[d, ph, k, m or None, v[0], v[1], sorted(v[2])] for (d, ph, k, m), v in sorted(episodes.items())]
        repo = repo_cache.get(name)
        if repo is None:
            repo = _repo_of(cfg, name)
            repo_cache[name] = repo
        fmt = str(cm.get("codimango.format") or cm.get("codimango.track") or "")
        out_tasks.append({
            "t": name, "k": "mt" if "multi" in fmt else "st" if fmt else "unknown", "r": repo or "unknown",
            "c": cm.get("codimango.category") or "unknown", "s": status or "not_imported",
            "cr": cm.get("codimango.created_at") or (commits.get(name, [{}])[0].get("at")),
            "ar": cm.get("codimango.archived_at"),
            "sub": [[s["at"], s["v"]] for s in submits], "subfb": fallback_submit, "cl": claimed,
            "dec": [[d["at"], d["decision"], (d.get("reason") or "")[:120], bool(d.get("fallback"))] for d in decisions],
            "act": act,
            "val": [cm.get("codimango.oracle_pass"), cm.get("codimango.oracle_total"), cm.get("codimango.avocado_pass"),
                    cm.get("codimango.avocado_total"), cm.get("codimango.codex_pass"), cm.get("codimango.codex_total")],
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
    phase_rows = sum(len(t["act"]) for t in out_tasks)
    classified = sum(1 for t in out_tasks for a in t["act"] if a[1] != "unclassified")
    model_rows = sum(1 for t in out_tasks for a in t["act"] if a[3])
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
            {"id": "reviews", "label": "Reviews", "covered": dec_cov, "eligible": eligible,
             "status": "exact" if dec_cov == eligible else "partial",
             "reason": f"{eligible - dec_cov} review histories pending" if dec_cov < eligible else ""},
            {"id": "phases", "label": "Phases", "covered": classified, "eligible": phase_rows, "status": "estimated",
             "reason": f"{phase_rows - classified} activity rows unclassified; exact model on {model_rows}"},
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

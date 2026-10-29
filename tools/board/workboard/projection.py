"""Projection: observations (codimango, git) + ledger events -> one TaskView per task.

Authority (DESIGN §2): codimango owns lifecycle/validation/server commit, git owns task-dir heads, the
ledger owns claims/reviews/checks. Disagreements become findings; no source overwrites another.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from . import events as ev_mod
from .model import Finding, TaskView

REPO_ENTITY_PREFIX = "__repo__:"
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

STATE = {
    "draft": "DRAFT", "needs_reviewers_assigned": "QUEUE", "being_reviewed": "REVIEW",
    "needs_revision": "NEEDS_REV", "accepted": "ACCEPTED", "used_in_training": "ACCEPTED", "archived": "ARCHIVED",
}
THRESHOLD_KEY = {"QUEUE": "review", "REVIEW": "review", "NEEDS_REV": "needs_revision"}
VALID = {"passing": "PASS", "passed": "PASS", "pending": "RUN", "running": "RUN", "failed": "FAIL", "failing": "FAIL"}
GROUP_ORDER = {"ATTENTION": 0, "READY": 1, "VALIDATING": 2, "REVIEWING": 3, "DONE": 4}
TAG = {"draft": "Draft", "needs_revision": "Needs revision", "needs_reviewers_assigned": "Needs reviewers",
       "being_reviewed": "In review", "accepted": "Accepted", "used_in_training": "In training", "archived": "Archived"}
IMPORT_GRACE_S = 15 * 60          # a push newer than the server by less than this is "importing", not drift
GIT_ONLY_MAX_AGE_S = 14 * 86400   # git-only folders older than this are not tasks (templates, samples)
SEV_ORDER = {"block": 0, "warn": 1, "info": 2}


def fmt_ago(seconds: float) -> str:
    s = int(max(0, seconds))
    return f"{s // 60}m" if s < 3600 else f"{s // 3600}h" if s < 86400 else f"{s // 86400}d"


def ts(value) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return out if out.tzinfo else None


DOC_NAMES = ("readme", "changelog", "notes", "license")


def _is_doc(path: str) -> bool:
    low = path.lower()
    name = low.rsplit("/", 1)[-1]
    if "/audit/" in f"/{low}" and name.endswith(".md"):
        return True                                       # audit notes / review ledgers are documentation
    return name.endswith(".md") and any(name.startswith(d) for d in DOC_NAMES + ("review-ledger",)) or \
        name in ("readme", "readme.txt")


AUTH_RANK = {"derived": 0, "advisory": 1, "authoritative": 2}


def _merge(observations):
    """Deterministic: per field, higher authority wins, then the newer observation."""
    by_task, repos = {}, {}
    def rank(o):
        top = max((AUTH_RANK.get(a, 0) for a in o.authority.values()), default=0)
        return (top, o.observed_at)
    for o in sorted(observations, key=rank):
        if o.entity_id.startswith(REPO_ENTITY_PREFIX):
            repos[o.entity_id[len(REPO_ENTITY_PREFIX):]] = dict(o.fields)
            continue
        by_task.setdefault(o.entity_id, {}).update(o.fields)
    return by_task, repos


def _claims(task_events, cfg, now, aliases):
    """Live claims from claim/renew/steal/release audit events only (DESIGN §5: ordinary activity is
    not a heartbeat). Returns (owner_alias, claim_health, live_claimants)."""
    live: dict[str, dict] = {}
    skew = timedelta(seconds=cfg.claims.clock_skew_warn_seconds)
    for e in task_events:
        sid = e["actor"]["session_id"]
        at = ts(e["occurred_at"])
        if at is None or at - now > skew:
            continue                       # future-dated: reported as CLOCK_SKEW, never trusted for liveness
        if e["type"] in ("claim", "renew", "steal"):
            target = e["payload"].get("to_session") or sid
            if e["type"] == "steal":
                live.clear()
            prev = live.get(target, {})
            since = prev.get("since") if (e["type"] == "renew" and prev) else at
            live[target] = {"alias": e["payload"].get("to_alias") or aliases.get(target) or e["actor"].get("alias", ""),
                            "host": e["host_id"], "session": target, "at": max(at, prev.get("at") or at),
                            "since": since or at}
        elif e["type"] == "release":
            live.pop(sid, None)
            released = e["payload"].get("released_owner")
            if isinstance(released, dict) and isinstance(released.get("session_id"), str):
                live.pop(released["session_id"], None)
    expire = timedelta(hours=cfg.claims.expire_after_hours)
    fresh = {s: c for s, c in live.items() if now - c["at"] <= expire}
    if not live:
        return "", "FREE", []
    if not fresh:
        newest = max(live.values(), key=lambda c: c["at"])
        return newest["alias"], "EXPIRED", []
    if len(fresh) > 1:
        return " / ".join(c["alias"] for c in fresh.values()), "CONFLICT", list(fresh.values())
    (c,) = fresh.values()
    return c["alias"], "OWNED", [c]


def _reviews(task_events, current, g=None):
    """R-label from the shared author/independent reducer: R2 = both roles ready on the current commit."""
    from .roles import gates
    g = g or gates(task_events, current)
    cur = set(current) if isinstance(current, (set, list, tuple)) else ({current} if current else set())
    reviews = [e for e in task_events if e["type"] == "review"]
    latest = {}
    for r in reviews:
        latest[(r["actor"]["session_id"], r.get("commit"))] = r
    at_current = [r for r in latest.values() if r.get("commit") in cur]
    dissent = len({r["actor"]["session_id"] for r in at_current if r["payload"].get("verdict") == "changes"})
    ok = [r for r in ("author", "independent") if g[r]["review"]["state"] == "ok"]
    label = "R2" if len(ok) == 2 else "R1" if ok else "R~" if reviews and not at_current else "R0"
    pool = at_current or reviews
    conf = next((r["payload"].get("confidence") for r in reversed(pool) if r["payload"].get("confidence")), None)
    return label, conf, bool(conf) and not at_current, dissent


def _check(task_events, current):
    checks = [e for e in task_events if e["type"] == "check"]
    if not checks:
        return "NONE", False, None
    last = checks[-1]
    p = last["payload"]
    text = f"P{p.get('pass', 0)} W{p.get('warn', 0)} F{p.get('fail', 0)}"
    current = set(current) if isinstance(current, (set, list, tuple)) else ({current} if current else set())
    return text, bool(current and last.get("commit") not in current), p


def _age_level(state, age_s, cfg):
    key = THRESHOLD_KEY.get(state, state.lower())
    warn = cfg.thresholds.warn_hours.get(key, cfg.thresholds.warn_hours.get("default", 48))
    block = cfg.thresholds.block_hours.get(key, cfg.thresholds.block_hours.get("default", 120))
    if age_s is None:
        return "ok"
    if age_s >= block * 3600:
        return "block"
    if age_s >= warn * 3600:
        return "warn"
    return "ok"


def _state_since(state, cm):
    """(timestamp, label): when this state began if knowable, else an honestly-labelled proxy."""
    if state in ("ACCEPTED", "NEEDS_REV"):
        return ts(cm.get("codimango.reviewed_at")), "decided"
    if state == "QUEUE":
        return ts(cm.get("codimango.entered_pool_at")), "submitted"
    if state == "REVIEW":
        return ts(cm.get("codimango.updated_at")) or ts(cm.get("codimango.entered_pool_at")), "in review since (approx.)"
    if state == "ARCHIVED":
        return ts(cm.get("codimango.archived_at")), "archived"
    if state == "DRAFT" and cm.get("codimango.entered_pool_at"):
        return ts(cm.get("codimango.updated_at")), "back in draft since (approx.)"
    return ts(cm.get("codimango.created_at")), "created"


PARKED = {"PARKED", "PARKED-TOO-EASY", "EXHAUSTED", "KILLED", "RETIRED", "ARCHIVED", "DROPPED", "ABANDONED",
          "HOLD", "ON-HOLD", "ONHOLD"}
PARK_REASON = re.compile(r"^\s*(parked|park|hold|on hold|retired|killed|abandoned)\b", re.I)


def _parked(legacy_rows, tev, state, claim_health, head_time, now=None, window_s=7200):
    """A draft parked by its latest CLAIMS.md row (PARKED, HOLD, KILLED, ...) or by a release whose reason says so,
    with no work since: off the to-do list (group DONE), not free. A later push, presubmit or build revives it for
    good; a check-in or path touch only while it is fresh; a live claim always (machine beats CLAIMS.md)."""
    if state not in ("DRAFT", "NOT_IMPORTED") or claim_health == "OWNED":
        return None
    marks = []
    if legacy_rows and legacy_rows[-1]["payload"].get("status") in PARKED:
        last = legacy_rows[-1]["payload"]
        dates = [d for d in (ts((last.get("updated") or "")[:10] + "T23:59:59+00:00"),
                             ts(legacy_rows[-1].get("occurred_at"))) if d]   # the row date, or when the board read it
        if dates:
            marks.append((max(dates), {"status": last["status"], "updated": last.get("updated"),
                                       "machine": last.get("legacy_owner"), "source": "CLAIMS.md"}))
    rel = [e for e in tev if e["type"] == "release" and PARK_REASON.match(str((e.get("payload") or {}).get("reason") or ""))]
    if rel and ts(rel[-1].get("occurred_at")):
        r = rel[-1]
        marks.append((ts(r["occurred_at"]), {"status": "PARKED", "updated": r["occurred_at"][:10],
                                             "machine": (r.get("actor") or {}).get("alias"), "source": "release",
                                             "reason": str(r["payload"].get("reason"))[:160]}))
    if not marks:
        return None
    since, info = max(marks, key=lambda m: m[0])
    now = now or datetime.now(since.tzinfo)
    for e in tev:
        at = ts(e.get("occurred_at"))
        if not at or at <= since:
            continue
        if e["type"] in ("check", "build_action"):   # worked on since (releases and claims alone are not work)
            return None
        if e["type"] in ("presence", "touch") and (now - at).total_seconds() <= window_s:
            return None
    if head_time and head_time > since:
        return None
    return info


def _next(f, findings):
    codes = {x.code for x in findings}
    state, valid = f["state"], f["valid"]
    if state in ("ACCEPTED", "ARCHIVED"):
        return "DONE", "—"
    if f.get("parked"):
        return "DONE", "PARKED"
    if "CONFLICT" in codes:
        return "ATTENTION", "RESOLVE CONFLICT"
    if codes & {"HEAD≠SERVER", "STALE_VALID"}:            # results are for an older commit: refresh them first
        return "ATTENTION", "RERUN server"
    if f.get("sync") == "IMPORTING":
        return "VALIDATING", "WAIT import"
    if valid == "FAIL":
        return "ATTENTION", ("RERUN validation" if f.get("infra_only") else "FIX validation")
    if "NONOWNER_EDIT" in codes:
        return "ATTENTION", "RESOLVE ownership"
    if "CLOCK_SKEW" in codes:
        return "ATTENTION", "CHECK clock"
    if "VALID≠SERVER" in codes:
        return ("VALIDATING", "WAIT validation") if valid == "RUN" else ("ATTENTION", "RERUN server")
    if valid == "RUN":
        return "VALIDATING", "WAIT validation"
    if state in ("QUEUE", "REVIEW"):
        return "REVIEWING", "WAIT reviewer"
    if state == "NEEDS_REV" and not f.get("pushes_since_decision"):
        return "READY", "ADDRESS review"                  # nothing pushed since it was sent back
    if state == "NOT_IMPORTED":
        return "READY", "IMPORT task"
    if f.get("dissent") and state in ("DRAFT", "NEEDS_REV"):
        return "ATTENTION", "ADDRESS agent review"
    # DRAFT ladder: both presubmits (building session + independent agent) clean on this commit
    if f["check_fail"]:
        return "ATTENTION", "FIX check"
    if f.get("check_need", f["check"] == "NONE" or f["check_stale"]):
        return "READY", "RUN check"
    if f["review"] in ("R0", "R~"):
        return "READY", "GET R1"
    if f["review"] == "R1":
        return "READY", "GET R2"
    return "READY", "RESUBMIT" if state == "NEEDS_REV" else "SUBMIT"


def _ref_claim(g_claims: dict, cfg, now):
    """Owner from the authoritative claim ref fields (claims.*)."""
    renewed = ts(g_claims.get("claims.renewed_at"))
    alias = g_claims.get("claims.alias", "")
    acquired = ts(g_claims.get("claims.acquired_at")) or renewed
    if renewed is None:
        return alias, "EXPIRED", g_claims.get("claims.session_id"), None
    if now - renewed > timedelta(hours=cfg.claims.expire_after_hours):
        return alias, "EXPIRED", g_claims.get("claims.session_id"), acquired
    return alias, "OWNED", g_claims.get("claims.session_id"), acquired


def project(observations, evs, cfg, now, *, claims_healthy: bool = False) -> list[TaskView]:
    by_task, repos = _merge(observations)
    observed = {}
    for ob in observations:
        if not ob.entity_id.startswith(REPO_ENTITY_PREFIX):
            observed.setdefault(ob.entity_id, {})[ob.source] = max(
                ob.observed_at, observed.get(ob.entity_id, {}).get(ob.source, ob.observed_at))
    aliases = ev_mod.latest_aliases(evs)
    per_task_events: dict[str, list] = {}
    for e in evs:
        ent = e.get("entity")
        if ent and ent.get("kind") == "task":
            per_task_events.setdefault(ent["id"], []).append(e)
    for lst in per_task_events.values():
        lst.sort(key=lambda e: (ts(e["occurred_at"]) or now, e["host_id"], e["seq"]))

    for tid, tev_list in per_task_events.items():          # claimed before codimango/git know it (new slug)
        if tid not in by_task and any(e["type"] in ("claim", "presence") for e in tev_list) and \
                any((now - (ts(e["occurred_at"]) or now)).total_seconds() < GIT_ONLY_MAX_AGE_S for e in tev_list):
            by_task[tid] = {"workboard.claim_only": True}
    views = []
    for task, fields in by_task.items():
        cm = {k: v for k, v in fields.items() if k.startswith("codimango.")}
        g = {k: v for k, v in fields.items() if k.startswith("git.")}
        tev = per_task_events.get(task, [])
        findings: list[Finding] = []
        state = STATE.get(cm.get("codimango.status"), "NOT_IMPORTED" if not cm else str(cm.get("codimango.status")).upper())
        repo_cfg = next((r for r in cfg.repositories if r.id == (g.get("git.repo") or "tasks")), None)
        links = {}
        if cfg.codimango.web_task_url and ("{id}" not in cfg.codimango.web_task_url or cm.get("codimango.id")):
            links["codimango"] = cfg.codimango.web_task_url.replace("{task}", task).replace("{id}", str(cm.get("codimango.id") or ""))
        if cm.get("codimango.github_url"):
            links["github"] = cm["codimango.github_url"]
        if repo_cfg and repo_cfg.remote_url and "github.com" in repo_cfg.remote_url:
            slug = repo_cfg.remote_url.split("github.com", 1)[1].lstrip(":/").replace("22/", "", 1).removesuffix(".git")
            links["latest"] = f"https://github.com/{slug}/tree/{repo_cfg.branch}/{task}"
        raw = cm.get("codimango.status")
        if not cm and not fields.get("workboard.claim_only"):
            ht = ts(g.get("git.task_head_time"))
            if not ht or (now - ht).total_seconds() > GIT_ONLY_MAX_AGE_S:
                continue                                   # old git-only folder: template/sample, not a task
        f = {"links": links, "state": state, "track": cm.get("codimango.track") or "",
             "status_raw": raw or "", "tag": TAG.get(raw, "Not imported" if not cm else str(raw)),
             "done_kind": ("in_training" if raw == "used_in_training" else "accepted" if raw == "accepted"
                           else "archived" if raw == "archived" else None),
             "category": {k: cm.get(f"codimango.{k}") for k in ("category", "subdomain", "usecase", "difficulty",
                                                                 "languages", "domain")},
             "valid": VALID.get(cm.get("codimango.validation_status"), "UNK" if cm else "—")}
        since, f["age_label"] = _state_since(state, cm)
        f["state_age_s"] = int((now - since).total_seconds()) if since else None
        f["tbr_status"] = cm.get("codimango.tbr_status")
        vitems = cm.get("codimango.validation") or []
        bad = [x for x in vitems if x.get("status") in ("failed", "error")]
        from .insights import INFRA, DEPENDENT
        roots = [x for x in bad if not DEPENDENT.search(x.get("detail") or "")]
        f["infra_only"] = bool(roots) and all(INFRA.search(x.get("detail") or "") for x in roots)
        f["age_level"] = _age_level(state, f["state_age_s"], cfg)

        # sync: has the server seen this task's latest commit, and validated it?
        server_sha = cm.get("codimango.commit_sha")            # version the server validated
        server_head = cm.get("codimango.head_commit_sha")      # newest commit the server has seen
        head, head_time = g.get("git.task_head"), ts(g.get("git.task_head_time"))
        repo_times = repos.get(g.get("git.repo"), {}).get("git.commit_time_by_sha", {})
        seen_time = ts(repo_times.get(server_head)) if server_head else None
        if seen_time is None and server_sha:
            seen_time = ts(repo_times.get(server_sha))
        open_task = state not in ("ACCEPTED", "ARCHIVED")
        f["sync"] = "—" if not (g and cm) else "UNCHECKED"
        if head and server_head and head == server_head:
            # the server has seen exactly this head; only the validated version can lag
            if head == server_sha:
                f["sync"] = "OK"
            elif "git.changed_since_validated" in g:
                changed = g["git.changed_since_validated"]
                if open_task and changed and not all(_is_doc(x) for x in changed):
                    f["sync"] = "STALE_VALID"
                    findings.append(Finding("STALE_VALID", "warn",
                                            f"server validated an older commit; {len(changed)} non-doc file(s) changed since",
                                            "codimango task rerun <task>, then wait for validation"))
                else:
                    f["sync"] = "OK·doc" if changed else "OK"
        elif head_time and seen_time:
            if open_task and head_time > seen_time:
                lag = (now - head_time).total_seconds()
                if lag < IMPORT_GRACE_S:
                    f["sync"] = "IMPORTING"
                else:
                    f["sync"] = "HEAD≠SERVER"
                    findings.append(Finding(
                        "HEAD≠SERVER", "warn",
                        f"your commit {head[:8]} ({fmt_ago(lag)} ago) is not on the server; it last imported "
                        f"{(server_head or server_sha or '')[:8]} from {fmt_ago((now - seen_time).total_seconds())} ago",
                        "auto-import normally catches up within minutes; if not: codimango task rerun <task>"))
            else:
                f["sync"] = "OK"
        f["imported"] = None if f["sync"] in ("UNCHECKED", "—") else f["sync"] not in ("HEAD≠SERVER", "IMPORTING")
        f["validated"] = None if f["imported"] is None else (f["sync"] in ("OK", "OK·doc") and f["valid"] != "RUN")
        vsha = cm.get("codimango.validation_commit_sha")
        if server_sha and vsha and vsha != server_sha:
            running = f["valid"] == "RUN"
            findings.append(Finding("VALID≠SERVER", "info" if running else "warn",
                                    "validation results are for an older server commit" + (" (re-validation running)" if running else ""),
                                    "wait for validation" if running else "codimango task rerun <task>"))

        current = {c for c in (head or server_sha,) if c}
        if f["sync"] == "OK·doc" and server_sha:
            current.add(server_sha)                     # doc-only commits since the server commit keep reviews current
        f["equiv_commits"] = sorted(current)
        from .roles import gates as _gates
        gts = _gates(tev, current, generation=cm.get("codimango.validation_generation"))
        f["gates"] = gts
        f["review"], f["confidence"], f["confidence_stale"], f["dissent"] = _reviews(tev, current, gts)
        f["check"], f["check_stale"], check_payload = _check(tev, current)
        f["check_fail"] = any(gts[r]["check"]["state"] == "bad" for r in gts)
        f["check_need"] = not all(gts[r]["check"]["state"] == "ok" for r in gts)

        refc = {k: v for k, v in fields.items() if k.startswith("claims.")}
        if claims_healthy:
            if refc:
                owner, claim_health, owner_sid, since = _ref_claim(refc, cfg, now)
                claimants = [{"session": owner_sid, "at": since or now, "alias": owner}]
            else:
                owner, claim_health, claimants = "", "FREE", []
            f["claim_source"] = "claim" if refc else "none"
        else:
            owner, claim_health, claimants = _claims(tev, cfg, now, aliases)
            f["claim_source"] = "ledger claim (advisory)"
        if claim_health == "FREE":
            legacy = [e for e in tev if e["type"] == "note" and isinstance(e["payload"].get("legacy_owner"), str)]
            if legacy and legacy[-1]["payload"].get("live") is not False:    # latest row finished -> no owner
                last = legacy[-1]["payload"]
                expires = ts(last.get("expires_at"))
                if expires is None:                         # notes from before expires_at: 7 days from the row date
                    upd = ts((last.get("updated") or "")[:10] + "T00:00:00+00:00")
                    expires = upd + timedelta(days=7) if upd else None
                if expires and now <= expires and (last.get("status") in __import__("workboard.legacy", fromlist=["x"]).ACTIVE):
                    machine = last["legacy_owner"]
                    short = next((sv.id for sv in cfg.servers if sv.host_alias and sv.host_alias == machine), machine)
                    owner, claim_health = f"{short} (CLAIMS.md)", "LEGACY"
        legacy_rows = [e for e in tev if e["type"] == "note" and isinstance(e["payload"].get("legacy_owner"), str)]
        f["parked"] = _parked(legacy_rows, tev, state, claim_health, head_time, now,
                              cfg.claims.active_window_minutes * 60)
        if f["parked"]:
            f["tag"] = "Parked"
        if claim_health in ("OWNED", "EXPIRED") and legacy_rows:      # CLAIMS.md says another machine has it
            last = legacy_rows[-1]["payload"]
            machine = last.get("legacy_owner") or ""
            short = next((sv.id for sv in cfg.servers if sv.host_alias and sv.host_alias == machine), machine)
            active = last.get("status") in __import__("workboard.legacy", fromlist=["x"]).ACTIVE
            if active and short and not str(owner).startswith(f"{short}·") and last.get("live") is not False:
                findings.append(Finding("CLAIMS_DRIFT", "info",        # the machine (claim + activity) wins
                                        f"CLAIMS.md says {machine} has it ({last.get('status')}, {last.get('updated')}) "
                                        f"but the board claim is {owner}",
                                        "the board claim is authoritative; update the CLAIMS.md row if it is stale"))
        pres = {}
        for e in tev:
            if e["type"] == "presence":
                seen_at = e["payload"].get("last_seen")
                if isinstance(seen_at, (int, float)):
                    sid = e["actor"]["session_id"]
                    old = pres.get(sid, {"at": 0})
                    if seen_at >= old["at"]:
                        pres[sid] = {"at": seen_at, "alias": e["actor"].get("alias", ""),
                                     "checkin": bool(e["payload"].get("checkin"))}
        window = cfg.claims.active_window_minutes * 60
        active = sorted(((now.timestamp() - x["at"], sid, x) for sid, x in pres.items()
                         if 0 <= now.timestamp() - x["at"] <= window))
        f["active"] = [{"alias": x["alias"], "ago_s": int(ago), "session_key": sid,
                        "evidence": "explicit here" if x["checkin"] else "transcript path"}
                       for ago, sid, x in active]

        assignment_state = {"OWNED": "claimed", "LEGACY": "legacy", "CONFLICT": "conflict",
                            "EXPIRED": "expired"}.get(claim_health, "unassigned")
        assignment = {"state": assignment_state, "owner": owner or None,
                      "session_key": claimants[0]["session"] if assignment_state == "claimed" and claimants else None,
                      "source": f.get("claim_source"),
                      "reason": {"claimed": "atomic claim is live", "legacy": "advisory CLAIMS.md row is live",
                                 "conflict": "multiple live claims", "expired": "the last claim expired",
                                 "unassigned": "no live assignment"}[assignment_state]}
        activity = {"state": "active" if active else "inactive",
                    "last_at": datetime.fromtimestamp(now.timestamp() - active[0][0], now.tzinfo).isoformat() if active else None,
                    "session_keys": [sid for _, sid, _ in active],
                    "aliases": [x["alias"] for _, _, x in active],
                    "confidence": "high" if any(x["checkin"] for _, _, x in active) else "medium" if active else "unknown",
                    "evidence": sorted({"explicit here" if x["checkin"] else "transcript path" for _, _, x in active}),
                    "reason": ("explicit check-in" if any(x["checkin"] for _, _, x in active)
                               else "recent task-path activity" if active else "no recent task activity")}
        recent_build = [e for e in tev if e["type"] == "build_action" and
                        0 <= (now - (ts(e["occurred_at"]) or now)).total_seconds() <= window]
        if f["sync"] in ("IMPORTING", "HEAD≠SERVER"):
            pipeline = {"state": "importing", "since": head_time.isoformat() if head_time else None,
                        "reason": "latest remote change is awaiting server import", "source": "git+codimango"}
        elif f["valid"] == "RUN":
            pipeline = {"state": "validating", "since": cm.get("codimango.updated_at"),
                        "reason": "server validation is running", "source": "codimango"}
        elif state in ("QUEUE", "REVIEW"):
            pipeline = {"state": "review", "since": cm.get("codimango.entered_pool_at"),
                        "reason": "submitted and waiting for human review", "source": "codimango"}
        elif recent_build:
            pipeline = {"state": "building", "since": recent_build[-1]["occurred_at"],
                        "reason": "a recent build run is recorded", "source": "ledger"}
        else:
            pipeline = {"state": "none", "since": None, "reason": "no active pipeline transition", "source": None}
        work_events = [e for e in tev if e.get("type") in
                       ("touch", "presence", "claim", "renew", "steal", "build_action", "check", "review")
                       and ts(e.get("occurred_at"))]
        last_worker = max(work_events, key=lambda e: ts(e["occurred_at"])) if work_events else None
        last_change = {"commit": head, "at": head_time.isoformat() if head_time else None,
                       "time_kind": "commit",
                       "session_key": (last_worker.get("actor") or {}).get("session_id") if last_worker else None,
                       "session_alias": (last_worker.get("actor") or {}).get("alias") if last_worker else None,
                       "confidence": "inferred" if last_worker else "ambiguous",
                       "reason": "remote commit date; exact push time is unavailable" if head_time else "no remote change observed"}
        source_times = observed.get(task, {})
        source_at = source_times.get("codimango") if cm else source_times.get("git")
        max_stale = cfg.codimango.max_stale_seconds if cm else max(900, cfg.codimango.cache_ttl_seconds * 3)
        sources_fresh = bool(source_at and 0 <= (now - source_at).total_seconds() <= max_stale)
        from .ownership import reduce_ownership
        axes = reduce_ownership(assignment, activity, pipeline, last_change,
                                done=state in ("ACCEPTED", "ARCHIVED") or bool(f["parked"]),
                                actionable=state not in ("QUEUE", "REVIEW", "ACCEPTED", "ARCHIVED"),
                                sources_fresh=sources_fresh, now=now.timestamp(),
                                activity_window_s=window)
        f.update(axes)
        display_state = axes["availability"]["state"]
        if display_state == "done":
            owner, compat = "", "DONE"
        elif display_state == "conflict":
            compat = "CONFLICT"
        elif display_state == "actively_working":
            owner = active[0][2]["alias"] if active and assignment_state not in ("claimed", "conflict") else owner
            compat = "OWNED" if assignment_state == "claimed" else "ACTIVE"
        elif display_state == "assigned_idle":
            compat = {"claimed": "OWNED", "legacy": "LEGACY"}.get(assignment_state, claim_health)
        elif display_state == "in_pipeline":
            compat = "PIPELINE"
        elif display_state == "worked_recently":
            compat = "RECENT"
        elif display_state == "never_seen":
            compat = "UNSEEN"
        else:
            compat = "EXPIRED" if assignment_state == "expired" else "FREE"
        if display_state in ("available", "never_seen") and owner:
            f["expired_owner"], owner = owner, ""     # free: an old claimant must not group or sort it as theirs
        f["claim_source"] = {"ACTIVE": "recent activity", "LEGACY": "CLAIMS.md (advisory)", "OWNED": "claim",
                             "FREE": "none", "EXPIRED": "expired claim", "CONFLICT": "conflicting claims",
                             "PIPELINE": "pipeline", "RECENT": "recent remote change", "UNSEEN": "insufficient evidence"}.get(compat, f.get("claim_source"))
        f["owner"], f["claim_health"] = owner, compat
        f["ownership_state"], f["ownership_reason"] = display_state, axes["availability"]["reason"]
        if compat == "CONFLICT":
            findings.append(Finding("CONFLICT", "block", f"claimed by more than one live session: {owner}",
                                    "workboard release <task> on one of them"))
        skew = timedelta(seconds=cfg.claims.clock_skew_warn_seconds)
        future = [e for e in tev if (ts(e["occurred_at"]) or now) - now > skew]
        if future:
            hosts = sorted({e["host_id"] for e in future})
            findings.append(Finding("CLOCK_SKEW", "warn", f"{len(future)} event(s) dated in the future from {', '.join(hosts)}",
                                    "check the clock on that host (timedatectl)"))
        f["owner_session"] = claimants[0]["session"] if assignment_state == "claimed" and claimants else None
        if assignment_state == "claimed" and claimants:
            owner_sid = claimants[0]["session"]
            since = claimants[0].get("since") or claimants[0]["at"]
            foreign = [e for e in tev if e["type"] == "touch" and e["payload"].get("tool") in EDIT_TOOLS
                       and e["actor"]["session_id"] != owner_sid and (ts(e["occurred_at"]) or now) >= since]
            if foreign:
                who = foreign[-1]["actor"].get("alias") or foreign[-1]["actor"]["session_id"]
                findings.append(Finding("NONOWNER_EDIT", "warn", f"{who} edited this task while {owner} owns it",
                                        "agree who owns it; release or reassign"))

        pool = ts(cm.get("codimango.entered_pool_at"))
        times = [t for t in (ts(x) for x in g.get("git.commit_times", [])) if t]
        f["pushes_before_submit"] = sum(1 for t in times if not pool or t < pool)
        f["pushes_after_submit"] = sum(1 for t in times if pool and t >= pool)
        f["pushes"] = f"{f['pushes_before_submit']}+{f['pushes_after_submit']}"
        decided = ts(cm.get("codimango.reviewed_at"))
        f["pushes_since_decision"] = sum(1 for t in times if decided and t > decided)
        f["round"] = None
        f["group"], f["next"] = _next(f, findings)
        views.append(TaskView(task, f, findings))

    views.sort(key=lambda v: (GROUP_ORDER[v.fields["group"]],
                              min((SEV_ORDER[x.severity] for x in v.findings), default=3),
                              -(v.fields["state_age_s"] or 0), v.entity_id))
    return views

"""Projection: observations (codimango, git) + ledger events -> one TaskView per task.

Authority (DESIGN §2): codimango owns lifecycle/validation/server commit, git owns task-dir heads, the
ledger owns claims/reviews/checks. Disagreements become findings; no source overwrites another.
"""
from __future__ import annotations

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
GROUP_ORDER = {"ATTENTION": 0, "READY": 1, "WAITING": 2, "DONE": 3}
SEV_ORDER = {"block": 0, "warn": 1, "info": 2}


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
    name = path.rsplit("/", 1)[-1].lower()
    return name.endswith(".md") and any(name.startswith(d) for d in DOC_NAMES) or name in ("readme", "readme.txt")


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


def _reviews(task_events, current):
    reviews = [e for e in task_events if e["type"] == "review"]
    at_current = [r for r in reviews if current and r["commit"] == current]
    ready = {r["actor"]["session_id"] for r in at_current if r["payload"].get("verdict") == "ready"}
    dissent = len({r["actor"]["session_id"] for r in at_current if r["payload"].get("verdict") == "changes"})
    if len(ready) >= 2:
        label = "R2"
    elif len(ready) == 1:
        label = "R1"
    elif reviews and not at_current:
        label = "R~"
    else:
        label = "R0"
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
    return text, bool(current and last["commit"] != current), p


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
    if state in ("ACCEPTED", "NEEDS_REV"):
        return ts(cm.get("codimango.reviewed_at"))
    if state in ("QUEUE", "REVIEW"):
        return ts(cm.get("codimango.entered_pool_at"))
    if state == "ARCHIVED":
        return ts(cm.get("codimango.archived_at"))
    return ts(cm.get("codimango.created_at"))


def _next(f, findings):
    codes = {x.code for x in findings}
    state, valid = f["state"], f["valid"]
    if state in ("ACCEPTED", "ARCHIVED"):
        return "DONE", "—"
    if "CONFLICT" in codes:
        return "ATTENTION", "RESOLVE CONFLICT"
    if valid == "FAIL":
        return "ATTENTION", "FIX validation"
    if codes & {"HEAD≠SERVER", "STALE_VALID"}:
        return "ATTENTION", "RERUN server"
    if "NONOWNER_EDIT" in codes:
        return "ATTENTION", "RESOLVE ownership"
    if "CLOCK_SKEW" in codes:
        return "ATTENTION", "CHECK clock"
    if "VALID≠SERVER" in codes:
        return ("WAITING", "WAIT validation") if valid == "RUN" else ("ATTENTION", "RERUN server")
    if valid == "RUN":
        return "WAITING", "WAIT validation"
    if state in ("QUEUE", "REVIEW"):
        return "WAITING", "WAIT reviewer"
    if state == "NEEDS_REV":
        return "READY", "ADDRESS review"
    if state == "NOT_IMPORTED":
        return "READY", "IMPORT task"
    # DRAFT ladder
    if f["check"] == "NONE" or f["check_stale"]:
        return "READY", "RUN check"
    if f["check_fail"]:
        return "ATTENTION", "FIX check"
    if f["review"] in ("R0", "R~"):
        return "READY", "GET R1"
    if f["review"] == "R1":
        return "READY", "GET R2"
    return "READY", "SUBMIT"


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
    aliases = ev_mod.latest_aliases(evs)
    per_task_events: dict[str, list] = {}
    for e in evs:
        ent = e.get("entity")
        if ent and ent.get("kind") == "task":
            per_task_events.setdefault(ent["id"], []).append(e)
    for lst in per_task_events.values():
        lst.sort(key=lambda e: (ts(e["occurred_at"]) or now, e["host_id"], e["seq"]))

    views = []
    for task, fields in by_task.items():
        cm = {k: v for k, v in fields.items() if k.startswith("codimango.")}
        g = {k: v for k, v in fields.items() if k.startswith("git.")}
        tev = per_task_events.get(task, [])
        findings: list[Finding] = []
        state = STATE.get(cm.get("codimango.status"), "NOT_IMPORTED" if not cm else str(cm.get("codimango.status")).upper())
        repo_cfg = next((r for r in cfg.repositories if r.id == (g.get("git.repo") or "tasks")), None)
        links = {}
        if cfg.codimango.web_task_url:
            links["codimango"] = cfg.codimango.web_task_url.replace("{task}", task)
        if cm.get("codimango.github_url"):
            links["github"] = cm["codimango.github_url"]
        if repo_cfg and repo_cfg.remote_url and "github.com" in repo_cfg.remote_url:
            slug = repo_cfg.remote_url.split("github.com", 1)[1].lstrip(":/").replace("22/", "", 1).removesuffix(".git")
            links["latest"] = f"https://github.com/{slug}/tree/{repo_cfg.branch}/{task}"
        f = {"links": links, "state": state, "track": cm.get("codimango.track") or "",
             "valid": VALID.get(cm.get("codimango.validation_status"), "UNK" if cm else "—")}
        since = _state_since(state, cm)
        f["state_age_s"] = int((now - since).total_seconds()) if since else None
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
                f["sync"] = "HEAD≠SERVER"
                findings.append(Finding("HEAD≠SERVER", "warn", "a newer commit to this task is not on the server yet",
                                        "codimango task rerun <task> (free), then wait for validation"))
            else:
                f["sync"] = "OK"
        vsha = cm.get("codimango.validation_commit_sha")
        if server_sha and vsha and vsha != server_sha:
            running = f["valid"] == "RUN"
            findings.append(Finding("VALID≠SERVER", "info" if running else "warn",
                                    "validation results are for an older server commit" + (" (re-validation running)" if running else ""),
                                    "wait for validation" if running else "codimango task rerun <task>"))

        current = head or server_sha
        f["review"], f["confidence"], f["confidence_stale"], f["dissent"] = _reviews(tev, current)
        f["check"], f["check_stale"], check_payload = _check(tev, current)
        f["check_fail"] = bool(check_payload and check_payload.get("fail"))

        refc = {k: v for k, v in fields.items() if k.startswith("claims.")}
        if claims_healthy:
            if refc:
                owner, claim_health, owner_sid, since = _ref_claim(refc, cfg, now)
                claimants = [{"session": owner_sid, "at": since or now, "alias": owner}]
            else:
                owner, claim_health, claimants = "", "FREE", []
            f["claim_source"] = "ref"
        else:
            owner, claim_health, claimants = _claims(tev, cfg, now, aliases)
            f["claim_source"] = "ledger (advisory)"
        if claim_health == "FREE":
            legacy = [e for e in tev if e["type"] == "note" and isinstance(e["payload"].get("legacy_owner"), str)]
            if legacy and legacy[-1]["payload"].get("live") is not False:    # latest row finished -> no owner
                last = legacy[-1]["payload"]
                expires = ts(last.get("expires_at"))
                if expires is None:                         # notes from before expires_at: 7 days from the row date
                    upd = ts((last.get("updated") or "")[:10] + "T00:00:00+00:00")
                    expires = upd + timedelta(days=7) if upd else None
                if expires and now <= expires:
                    machine = last["legacy_owner"]
                    short = next((sv.id for sv in cfg.servers if sv.host_alias and sv.host_alias == machine), machine)
                    owner, claim_health = f"{short} (CLAIMS.md)", "LEGACY"
        pres = {}
        for e in tev:
            if e["type"] == "presence":
                seen_at = e["payload"].get("last_seen")
                if isinstance(seen_at, (int, float)):
                    sid = e["actor"]["session_id"]
                    pres[sid] = max(pres.get(sid, (0, ""))[0], seen_at), e["actor"].get("alias", "")
        window = cfg.claims.active_window_minutes * 60
        active = sorted(((now.timestamp() - t, a) for t, a in pres.values() if 0 <= now.timestamp() - t <= window))
        f["active"] = [{"alias": a, "ago_s": int(ago)} for ago, a in active]
        if active and claim_health in ("FREE", "LEGACY", "EXPIRED"):
            owner, claim_health = active[0][1], "ACTIVE"
        if state in ("ACCEPTED", "ARCHIVED"):
            owner, claim_health = "", "DONE"
        f["owner"], f["claim_health"] = owner, claim_health
        if claim_health == "CONFLICT":
            findings.append(Finding("CONFLICT", "block", f"claimed by more than one live session: {owner}",
                                    "workboard release <task> on one of them"))
        skew = timedelta(seconds=cfg.claims.clock_skew_warn_seconds)
        future = [e for e in tev if (ts(e["occurred_at"]) or now) - now > skew]
        if future:
            hosts = sorted({e["host_id"] for e in future})
            findings.append(Finding("CLOCK_SKEW", "warn", f"{len(future)} event(s) dated in the future from {', '.join(hosts)}",
                                    "check the clock on that host (timedatectl)"))
        if claim_health == "OWNED" and claimants:
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
        f["round"] = None
        f["group"], f["next"] = _next(f, findings)
        views.append(TaskView(task, f, findings))

    views.sort(key=lambda v: (GROUP_ORDER[v.fields["group"]],
                              min((SEV_ORDER[x.severity] for x in v.findings), default=3),
                              -(v.fields["state_age_s"] or 0), v.entity_id))
    return views

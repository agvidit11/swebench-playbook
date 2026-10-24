"""HTML dashboard: `board html` writes one self-contained page; `board serve` serves it live on localhost.

Same data as the terminal views (TaskViews + stats). No external assets, no CDN: CSS, JS and data are inline.
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _task_extra(v, obs_by_task, ev_by_task, decisions) -> dict:
    """Detail for hover cards and the task card: validation checks, timestamps, commits, reviews, rounds."""
    from .reviews import versions
    o = obs_by_task.get(v.entity_id, {})
    tev = ev_by_task.get(v.entity_id, [])
    head = o.get("git.task_head")
    agent_reviews = [{"who": e["actor"].get("alias", ""), "verdict": e["payload"].get("verdict"),
                      "confidence": e["payload"].get("confidence"), "note": (e["payload"].get("note") or "")[:120],
                      "current": bool(head and e.get("commit") == head), "at": e["occurred_at"]}
                     for e in tev if e["type"] == "review"]
    checks = [e for e in tev if e["type"] == "check"]
    last_check = None
    if checks:
        c = checks[-1]
        last_check = dict(c["payload"], at=c["occurred_at"], current=bool(head and c.get("commit") == head))
    legacy = [e["payload"] for e in tev if e["type"] == "note" and e["payload"].get("legacy_owner")]
    dec = decisions.get(v.entity_id, {}).get("decisions", [])
    return {
        "validation": [{"name": x.get("name", ""), "status": x.get("status", ""), "detail": x.get("detail", "")}
                       for x in (o.get("codimango.validation") or [])],
        "oracle": [o.get("codimango.oracle_pass"), o.get("codimango.oracle_total")],
        "avocado": [o.get("codimango.avocado_pass"), o.get("codimango.avocado_total")],
        "created_at": o.get("codimango.created_at"), "entered_pool_at": o.get("codimango.entered_pool_at"),
        "reviewed_at": o.get("codimango.reviewed_at"), "status_raw": o.get("codimango.status"),
        "server_commit": (o.get("codimango.commit_sha") or "")[:8], "server_head": (o.get("codimango.head_commit_sha") or "")[:8],
        "validated_commit": (o.get("codimango.validation_commit_sha") or "")[:8], "task_head": (head or "")[:8],
        "changed": (o.get("git.changed_since_validated") or [])[:8],
        "agent_reviews": agent_reviews, "last_check": last_check,
        "legacy": legacy[-1] if legacy else None,
        "decisions": dec,
        "versions": versions(o.get("git.commit_times") or [], dec) if (dec or o.get("git.commit_times")) else [],
    }


def payload(snap, cfg) -> dict:
    from . import insights, reviews, stats as st
    from .app import cache_dir
    obs_by_task = {}
    for ob in snap.observations:
        obs_by_task.setdefault(ob.entity_id, {}).update(ob.fields)
    ev_by_task = {}
    for e in snap.events:
        ent = e.get("entity")
        if ent:
            ev_by_task.setdefault(ent.get("id"), []).append(e)
    decisions = reviews.load(cache_dir())
    flow = st.cycle_and_wait(snap.observations, snap.now)
    load = {}
    for v in snap.views:
        if v.fields.get("claim_health") in ("OWNED", "ACTIVE") and "·" in (v.fields.get("owner") or ""):
            host = v.fields["owner"].split("·", 1)[0]
            load[host] = load.get(host, 0) + 1
    for sv in cfg.servers:
        load.setdefault(sv.id, 0)
    views = []
    for v in snap.views:
        f = dict(v.fields)
        t = {"task": v.entity_id, **{k: f.get(k) for k in (
            "group", "next", "state", "state_age_s", "age_level", "owner", "claim_health", "valid", "review",
            "confidence", "confidence_stale", "sync", "check", "check_stale", "check_fail", "pushes_before_submit",
            "pushes_after_submit", "track", "active", "dissent", "links", "tag", "status_raw", "done_kind",
            "category", "imported", "validated")},
            "findings": [{"code": x.code, "severity": x.severity, "summary": x.summary, "next": x.next_action}
                         for x in v.findings],
            **_task_extra(v, obs_by_task, ev_by_task, decisions)}
        t["vsum"] = insights.validation_summary(t["validation"])
        t["rsum"] = insights.review_summary(t)
        t["steps"] = insights.next_steps(t, flow)
        t["assignee"] = insights.assignee(t, load)
        views.append(t)
    weekly = st.weekly(snap.observations, cfg, snap.now, 10)
    cm_at = snap.health.get("codimango").observed_at.isoformat() if snap.health.get("codimango") and \
        snap.health["codimango"].observed_at else None
    return {
        "generated_at": snap.now.isoformat(), "codimango_at": cm_at,
        "health": {k: {"ok": h.ok, "detail": h.detail} for k, h in snap.health.items()},
        "ledger_ok": bool(snap.sync_state and snap.sync_state.last_pull_ok
                          and (snap.sync_state.last_push_ok or not snap.sync_state.pending)) if snap.sync_state else None,
        "week": st.week_numbers(snap.observations, cfg, snap.now),
        "weekly": [dict(r, week=r["week"].strftime("%b %d")) for r in weekly],
        "funnel": st.funnel(snap.observations), "flow": flow,
        "ages": st.pipeline_age(snap.views, snap.now), "load": load,
        "tasks": views,
    }


from .html_page import PAGE  # noqa: E402  (template lives in its own module)


def page(data: dict, live: bool = False) -> str:
    blob = json.dumps(data, default=str).replace("</", "<\\/")
    return PAGE.replace("__DATA__", blob).replace("__LIVE__", "true" if live else "false")


def write(snap, cfg, path: Path) -> Path:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page(payload(snap, cfg)))
    return path


def serve(gather_fn, cfg, *, port: int = 8765, interval: int = 60, host: str = "127.0.0.1"):
    """Serve the dashboard; data refreshes in the background every `interval` seconds."""
    state = {"data": payload(gather_fn(), cfg), "at": time.time()}
    lock = threading.Lock()

    def refresher():
        while True:
            time.sleep(interval)
            try:
                d = payload(gather_fn(), cfg)
                with lock:
                    state["data"], state["at"] = d, time.time()
            except Exception:
                pass

    threading.Thread(target=refresher, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            with lock:
                data = state["data"]
            if self.path.startswith("/data.json"):
                body, ctype = json.dumps(data, default=str).encode(), "application/json"
            elif self.path in ("/", "/index.html"):
                body, ctype = page(data, live=True).encode(), "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    srv = ThreadingHTTPServer((host, port), Handler)
    return srv

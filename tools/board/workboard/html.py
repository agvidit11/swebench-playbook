"""HTML dashboard: `board html` writes one self-contained page; `board serve` serves it live on localhost.

Same data as the terminal views (TaskViews + stats). No external assets, no CDN: CSS, JS and data are inline.
"""
from __future__ import annotations

import json
import re
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
    equiv = set(v.fields.get("equiv_commits") or ([head] if head else []))
    agent_reviews = [{"who": e["actor"].get("alias", ""), "verdict": e["payload"].get("verdict"),
                      "confidence": e["payload"].get("confidence"), "note": (e["payload"].get("note") or "")[:120],
                      "current": e.get("commit") in equiv, "at": e["occurred_at"]}
                     for e in tev if e["type"] == "review"]
    checks = [e for e in tev if e["type"] == "check"]
    last_check = None
    if checks:
        c = checks[-1]
        last_check = dict(c["payload"], at=c["occurred_at"], current=c.get("commit") in equiv)
    legacy = [e["payload"] for e in tev if e["type"] == "note" and e["payload"].get("legacy_owner")]
    rec = decisions.get(v.entity_id, {})
    upd = o.get("codimango.updated_at")
    history_stale = bool(rec) and bool(upd) and rec.get("key") != f"{upd}"
    dec = [] if history_stale else rec.get("decisions", [])
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
        "decisions": dec, "review_history_stale": history_stale,
        "versions": versions(o.get("git.commit_times") or [], dec) if (dec or o.get("git.commit_times")) else [],
    }


def payload(snap, cfg) -> dict:
    from . import comms, insights, reviews, stats as st
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
    servers = comms.servers(snap.events, snap.views, cfg)
    live_hosts = {sv["id"] for sv in servers if sv["last_sync_ago_s"] is not None and sv["last_sync_ago_s"] < 900
                  and sv["sessions"]}
    views = []
    for v in snap.views:
        f = dict(v.fields)
        t = {"task": v.entity_id, **{k: f.get(k) for k in (
            "group", "next", "state", "state_age_s", "age_level", "owner", "claim_health", "valid", "review",
            "confidence", "confidence_stale", "sync", "check", "check_stale", "check_fail", "pushes_before_submit",
            "pushes_after_submit", "track", "active", "dissent", "links", "tag", "status_raw", "done_kind",
            "category", "imported", "validated", "age_label", "claim_source", "tbr_status", "infra_only")},
            "findings": [{"code": x.code, "severity": x.severity, "summary": x.summary, "next": x.next_action}
                         for x in v.findings],
            **_task_extra(v, obs_by_task, ev_by_task, decisions)}
        t["vsum"] = insights.validation_summary(t["validation"], t.get("tbr_status"))
        t["older_results"] = t.get("sync") in ("STALE_VALID", "HEAD≠SERVER")
        t["rsum"] = insights.review_summary(t)
        t["steps"] = insights.next_steps(t, flow)
        t["assignee"] = insights.assignee(t, load, live_hosts)
        views.append(t)
    weekly = st.weekly(snap.observations, cfg, snap.now, 10)
    cm_at = snap.health.get("codimango").observed_at.isoformat() if snap.health.get("codimango") and \
        snap.health["codimango"].observed_at else None
    return {
        "generated_at": snap.now.isoformat(), "codimango_at": cm_at,
        "health": {k: {"ok": h.ok, "detail": h.detail} for k, h in snap.health.items()},
        "ledger_ok": bool(snap.sync_state and snap.sync_state.last_pull_ok
                          and (snap.sync_state.last_push_ok or not snap.sync_state.pending)) if snap.sync_state else None,
        "ledger_at": snap.sync_state.at if snap.sync_state else None,
        "week": st.week_numbers(snap.observations, cfg, snap.now),
        "weekly": [dict(r, week=r["week"].strftime("%b %d")) for r in weekly],
        "funnel": st.funnel(snap.observations), "flow": flow,
        "ages": st.pipeline_age(snap.views, snap.now), "load": load,
        "tasks": views,
        "servers": servers,
        "codimango_detail": snap.health["codimango"].detail if snap.health.get("codimango") else "",
        "feed": comms.feed(snap.events, since_s=24 * 3600, limit=150),
        "messages": comms.messages(snap.events)[-80:],
        "sessions": sorted({a for a in __import__("workboard.events", fromlist=["x"]).latest_aliases(snap.events).values()}),
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


def serve(gather_fn, cfg, *, port: int = 8765, interval: int = 60, host: str = "127.0.0.1", send_fn=None):
    """Serve the dashboard; data refreshes in the background every `interval` seconds."""
    state = {"data": payload(gather_fn(), cfg), "at": time.time(), "error": None}
    lock = threading.Lock()

    def refresher():
        while True:
            time.sleep(interval)
            try:
                d = payload(gather_fn(), cfg)
                with lock:
                    state["data"], state["at"], state["error"] = d, time.time(), None
            except Exception as exc:              # keep the last data, but tell the page
                with lock:
                    state["error"] = f"{exc.__class__.__name__}: {exc}"[:200]

    threading.Thread(target=refresher, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            origin = self.headers.get("Origin", "")
            host_hdr = self.headers.get("Host", "")
            local = host_hdr.split(":")[0] in ("localhost", "127.0.0.1")
            if not local or (origin and not re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", origin)):
                self.send_error(403, "local only")
                return
            if self.path != "/api/msg" or send_fn is None:
                self.send_error(404)
                return
            try:
                n = min(int(self.headers.get("Content-Length", "0")), 8192)
                body = json.loads(self.rfile.read(n) or b"{}")
                result = send_fn(str(body.get("to", "")), str(body.get("text", "")), body.get("task") or None)
                code, out = 200, {"ok": True, **result}
            except ValueError as exc:
                code, out = 400, {"ok": False, "error": str(exc)}
            except Exception as exc:          # never crash the server
                code, out = 500, {"ok": False, "error": exc.__class__.__name__}
            data = json.dumps(out).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            with lock:
                data = dict(state["data"], refresh_error=state["error"], refreshed_ago_s=int(time.time() - state["at"]))
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

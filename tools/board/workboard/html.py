"""HTML dashboard: `board html` writes one self-contained page; `board serve` serves it live on localhost.

Same data as the terminal views (TaskViews + stats). No external assets, no CDN: CSS, JS and data are inline.
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _workers(tev: list[dict], window_s: int = 48 * 3600) -> list[str]:
    """Agents seen working on the task recently: the sessions themselves (Claude / Codex) plus what they launched."""
    now = time.time()
    out = set()
    for e in tev:
        if e["type"] not in ("presence", "touch", "build_action", "claim", "check", "review"):
            continue
        try:
            at = datetime.fromisoformat(e["occurred_at"]).timestamp()
        except (ValueError, KeyError):
            continue
        if now - at > window_s:
            continue
        kind = (e.get("actor") or {}).get("kind")
        if kind in ("claude", "codex"):
            out.add(kind)
        out |= set((e.get("payload") or {}).get("agents") or [])
        if e["type"] == "build_action" and (e.get("payload") or {}).get("model"):
            m = str(e["payload"]["model"]).lower()
            out.add("codex" if "gpt" in m or "codex" in m else "muse" if "avocado" in m or "muse" in m else "claude")
    return sorted(out)


RETIRE = re.compile(r"\b(retire|archive it|park(ed)?|abandon|drop the task|kill the task|not salvageable)\b", re.I)


def task_tags(t: dict) -> list[dict]:
    """Short labels at the end of a row: who works on it, type, how close it is, agent advice. [{k, label, why}]"""
    tags = []
    names = {"claude": "Claude", "codex": "Codex", "muse": "Muse"}
    for w in t.get("workers") or []:
        tags.append({"k": "who", "label": names.get(w, w), "why": f"{names.get(w, w)} worked on it in the last 48h"})
    kind = t.get("kind") or ""
    if kind in ("multi-turn", "single-turn"):
        tags.append({"k": "type", "label": "MT" if kind == "multi-turn" else "ST", "why": kind})
    steps = [s_ for s_ in t.get("steps") or [] if not s_.get("routine")]
    ladder = all(("building session" in s_["do"] or "independent agent" in s_["do"]) for s_ in steps)
    if re.match(r"(RE)?SUBMIT", t.get("next") or ""):
        tags.append({"k": "stage", "label": "ready", "why": "both presubmits and approvals are in — submit"})
    elif t.get("group") in ("ATTENTION", "READY") and steps and ladder and t.get("valid") == "PASS":
        tags.append({"k": "stage", "label": "near submit", "why": "validation passes; only presubmits / approvals left"})
    notes = [g.get("review", {}).get("note") or "" for g in (t.get("gates") or {}).values()] + \
            [g.get("check", {}).get("summary") or "" for g in (t.get("gates") or {}).values()]
    hit = next((n for n in notes if RETIRE.search(n)), None)
    if hit:
        tags.append({"k": "warn", "label": "retire?", "why": "an agent suggested retiring/parking it: " + hit[:140]})
    rounds = int((t.get("vp") or "0.0").split(".")[0])
    if rounds >= 2:
        tags.append({"k": "warn", "label": f"{rounds} rounds", "why": f"revision requested {rounds} times"})
    if t.get("infra_only"):
        tags.append({"k": "info", "label": "infra", "why": "validation failed only on infrastructure — a rerun should fix it"})
    idle = t.get("owner_last_at")
    if t.get("claim_health") == "OWNED" and idle:
        try:
            if time.time() - datetime.fromisoformat(idle).timestamp() > 24 * 3600:
                tags.append({"k": "info", "label": "idle 1d+", "why": "claimed, but no activity for over a day"})
        except ValueError:
            pass
    return tags


def _vp(o: dict, decisions: list[dict]) -> str:
    """'V.P': times a revision was requested . commits since the last request (or in total if never)."""
    from .projection import ts
    revs = [ts(d["at"]) for d in decisions if d.get("kind") == "revision" and ts(d.get("at"))]
    n = len(revs) or (1 if o.get("codimango.status") == "needs_revision" else 0)
    last = max(revs) if revs else (ts(o.get("codimango.reviewed_at")) if n else None)
    times = [t for t in (ts(x) for x in o.get("git.commit_times") or []) if t]
    return f"{n}.{sum(1 for t in times if not last or t > last)}"


def _task_extra(v, obs_by_task, ev_by_task, decisions) -> dict:
    """Detail for hover cards and the task card: validation checks, timestamps, commits, reviews, rounds."""
    from .reviews import versions
    o = obs_by_task.get(v.entity_id, {})
    tev = ev_by_task.get(v.entity_id, [])
    head = o.get("git.task_head")
    equiv = set(v.fields.get("equiv_commits") or ([head] if head else []))
    from .roles import role_of
    tev = sorted(tev, key=lambda e: (e.get("occurred_at") or "", e.get("host_id") or "", e.get("seq") or 0))
    owner_sid = v.fields.get("owner_session")
    agent_reviews = [{"who": e["actor"].get("alias", ""), "verdict": e["payload"].get("verdict"),
                      "confidence": e["payload"].get("confidence"), "note": (e["payload"].get("note") or "")[:300],
                      "current": e.get("commit") in equiv, "at": e["occurred_at"], "role": role_of(e, tev)}
                     for e in tev if e["type"] == "review"]
    g = v.fields.get("gates") or {}
    checks_by_role = {r: g[r]["check"] for r in g if g[r]["check"].get("state") != "none"}
    last_check = max(checks_by_role.values(), key=lambda c: c.get("at") or "") if checks_by_role else None
    def _when(e):                                       # presence: when the session was last seen, not when it was logged
        ls = (e.get("payload") or {}).get("last_seen")
        if e["type"] == "presence" and isinstance(ls, (int, float)):
            return datetime.fromtimestamp(ls, timezone.utc).isoformat()
        return e["occurred_at"]
    mine = [_when(e) for e in tev if owner_sid and (e.get("actor") or {}).get("session_id") == owner_sid
            and e["type"] in ("touch", "presence", "claim", "renew", "build_action", "check", "review")]
    owner_last = max(mine) if mine else None
    legacy = [e["payload"] for e in tev if e["type"] == "note" and e["payload"].get("legacy_owner")]
    rec = decisions.get(v.entity_id, {})
    upd = o.get("codimango.updated_at")
    history_stale = bool(rec) and bool(upd) and rec.get("key") != f"{upd}"
    dec = [] if history_stale else rec.get("decisions", [])
    online_kinds = {"oracle": o.get("codimango.oracle_total"), "avocado": o.get("codimango.avocado_total"),
                    "codex": o.get("codimango.codex_total")}
    known_online = {key: int(value) for key, value in online_kinds.items()
                    if isinstance(value, (int, float)) and not isinstance(value, bool)}
    return {
        "validation": [{"name": x.get("name", ""), "status": x.get("status", ""), "detail": x.get("detail", "")}
                       for x in (o.get("codimango.validation") or [])],
        "oracle": [o.get("codimango.oracle_pass"), o.get("codimango.oracle_total")],
        "avocado": [o.get("codimango.avocado_pass"), o.get("codimango.avocado_total")],
        "codex": [o.get("codimango.codex_pass"), o.get("codimango.codex_total")],
        "online_usage": {"source": "codimango task list", "run_count": None,
                         "trial_count": sum(known_online.values()) if known_online else None,
                         "trials_by_kind": known_online,
                         "cost": {"available": False, "label": "cost unavailable",
                                  "reason": "open the drawer to fetch bounded job counts"}},
        "created_at": o.get("codimango.created_at"), "entered_pool_at": o.get("codimango.entered_pool_at"),
        "reviewed_at": o.get("codimango.reviewed_at"), "status_raw": o.get("codimango.status"),
        "server_commit": (o.get("codimango.commit_sha") or "")[:8], "server_head": (o.get("codimango.head_commit_sha") or "")[:8],
        "validated_commit": (o.get("codimango.validation_commit_sha") or "")[:8], "task_head": (head or "")[:8],
        "changed": (o.get("git.changed_since_validated") or [])[:8],
        "agent_reviews": agent_reviews, "last_check": last_check, "checks": checks_by_role,
        "owner_last_at": owner_last,
        "kind": {"swe_bench_multi_turn": "multi-turn", "swe_bench_single_turn": "single-turn"}.get(
            o.get("codimango.format") or "", "multi-turn" if "multi" in (o.get("codimango.track") or "") else
            "single-turn" if o.get("codimango.track") else "not imported"),
        "legacy": legacy[-1] if legacy else None,
        "decisions": dec, "review_history_stale": history_stale,
        "vp": _vp(o, dec),
        "workers": _workers(tev),
        "versions": versions(o.get("git.commit_times") or [], dec) if (dec or o.get("git.commit_times")) else [],
    }


def short_names(servers) -> dict[str, str]:
    """native session id -> 'host·registry-name' (the name ListAgents / the Team tab use)."""
    out = {}
    for sv in servers or []:
        for row in sv.get("sessions") or []:
            if row.get("native_id") and row.get("name") and not row.get("is_summary"):
                out[str(row["native_id"])] = f"{sv['id']}·{row['name']}"
    return out


def _team_payload(snap, cfg, servers=None) -> dict:
    """Build only Team data; safe to call on the cheap native-session refresh path."""
    from . import comms
    from . import sync as sync_mod
    if servers is None:
        local_host = sync_mod.safe_host(sync_mod.host_id_for(cfg))
        servers = comms.servers(snap.events, snap.views, cfg, getattr(snap, "sessions", []),
                                getattr(snap, "session_diagnostics", []), sync_state=snap.sync_state,
                                local_host=local_host)
    task_targets = {}
    for view in snap.views:
        try:
            target = comms.target_for_task(view.entity_id, snap.views, getattr(snap, "sessions", []))
            recipient = target["resolved_recipients"][0]
            task_targets[view.entity_id] = {"state": "resolved", "to": target["to"],
                                            "label": target["to_label"], "host": recipient.get("host"),
                                            "session_key": recipient.get("session_key")}
        except ValueError as exc:
            task_targets[view.entity_id] = {"state": "nobody", "reason": str(exc)}
    session_targets = []
    for server in servers:
        for session in server["sessions"]:
            if session.get("is_summary") or session.get("is_actor"):
                continue
            session_targets.append({"session_key": session.get("session_key") or session.get("native_id"),
                                    "native_id": session.get("native_id"),
                                    "name": session.get("name") or session.get("alias"),
                                    "host": server["id"], "kind": session.get("kind"),
                                    "kind_icon": session.get("kind_icon"), "tasks": session.get("tasks") or [],
                                    "transport": session.get("transport")})
            for run in session.get("child_runs") or []:     # live Codex/Muse jobs: reachable through their parent
                if run.get("status") != "busy":             # only jobs running right now; finished ones are history
                    continue
                session_targets.append({"session_key": session.get("session_key") or session.get("native_id"),
                                        "native_id": session.get("native_id"),
                                        "name": f"{run.get('name') or run.get('kind')} (via {session.get('name')})",
                                        "host": server["id"], "kind": run.get("kind"),
                                        "kind_icon": run.get("kind_icon") or {"codex": "🟢", "muse": "🟠"}.get(run.get("kind"), "❔"),
                                        "tasks": [run["cwd_task"]] if run.get("cwd_task") else (session.get("tasks") or []),
                                        "via": session.get("name"), "transport": session.get("transport")})
    names = short_names(servers)
    msgs = comms.messages(snap.events)[-80:]
    for m in msgs:                                    # one name per session everywhere: the registry name
        if m.get("from_session") in names:
            m["from"] = names[m["from_session"]]
        for r in (m.get("delivery") or {}).get("recipients") or []:
            if str(r.get("native_id")) in names:
                r["name"] = names[str(r["native_id"])]
    return {"servers": servers, "messages": msgs,
            "session_targets": session_targets, "task_targets": task_targets}


def fast_regions(snap, cfg, names=("team", "activity")) -> dict[str, dict]:
    """Regions which can be refreshed without running task sources/projectors."""
    from . import comms
    names = set(names)
    out = {}
    if "team" in names:
        out["team"] = _team_payload(snap, cfg)
    if "activity" in names:
        who = short_names(out.get("team", {}).get("servers") if isinstance(out.get("team"), dict) else None) or \
            short_names(_team_payload(snap, cfg)["servers"])
        out["activity"] = {"items": [dict(f, who=who.get(f.get("session") or "", f.get("who")))
                                     for f in comms.feed(snap.events, since_s=24 * 3600, limit=150)]}
    return out


def payload(snap, cfg) -> dict:
    from . import comms, insights, reviews, stats as st
    from .app import cache_dir
    from . import sync as sync_mod
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
    local_host = sync_mod.safe_host(sync_mod.host_id_for(cfg))
    servers = comms.servers(snap.events, snap.views, cfg, getattr(snap, "sessions", []),
                            getattr(snap, "session_diagnostics", []), sync_state=snap.sync_state,
                            local_host=local_host)
    live_hosts = {sv["id"] for sv in servers if sv["last_sync_ago_s"] is not None and sv["last_sync_ago_s"] < 900
                  and sv["sessions"]}
    names = {}                                      # native session id -> short registry name (e.g. agvidit-0b)
    for sv in servers:
        for row in sv.get("sessions") or []:
            if row.get("native_id") and row.get("name") and not row.get("is_summary"):
                names[str(row["native_id"])] = row["name"]
    views = []
    for v in snap.views:
        f = dict(v.fields)
        sid = f.get("owner_session") or str((f.get("assignment") or {}).get("session_key") or "").rsplit(":", 1)[-1]
        if sid in names and names[sid] not in (f.get("owner") or ""):
            host = (f.get("owner") or "").split("·", 1)[0]
            title = (f.get("owner") or "").split("·", 1)[-1]
            f["owner"] = f"{host}·{names[sid]}" + (f" · {title}" if title and title != names[sid] else "")
        t = {"task": v.entity_id, **{k: f.get(k) for k in (
            "group", "next", "state", "state_age_s", "age_level", "owner", "claim_health", "valid", "review",
            "confidence", "confidence_stale", "sync", "check", "check_stale", "check_fail", "pushes_before_submit",
            "pushes_after_submit", "track", "active", "dissent", "links", "tag", "status_raw", "done_kind",
            "category", "imported", "validated", "age_label", "claim_source", "tbr_status", "infra_only", "gates", "check_need", "pushes_since_decision",
            "assignment", "activity", "pipeline", "last_push", "availability", "ownership_state",
            "ownership_reason", "owner_session", "local_usage", "local_spend")},
            "findings": [{"code": x.code, "severity": x.severity, "summary": x.summary, "next": x.next_action}
                         for x in v.findings],
            **_task_extra(v, obs_by_task, ev_by_task, decisions)}
        t["vsum"] = insights.validation_summary(t["validation"], t.get("tbr_status"))
        t["older_results"] = t.get("sync") in ("STALE_VALID", "HEAD≠SERVER")
        t["rsum"] = insights.review_summary(t)
        t["steps"] = insights.next_steps(t, flow)
        t["assignee"] = insights.assignee(t, load, live_hosts)
        t["tags"] = task_tags(t)
        t["primary"] = insights.primary_action(t)
        views.append(t)
    team = _team_payload(snap, cfg, servers)
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
        "s2": _stats2(snap, cfg),
        "token_daily": (getattr(snap, "usage", {}) or {}).get("daily", []),
        "token_accounting": (getattr(snap, "usage", {}) or {}).get("accounting", {}),
        "usage_collector": (getattr(snap, "usage", {}) or {}).get("collector", {}),
        **team,
        "codimango_detail": snap.health["codimango"].detail if snap.health.get("codimango") else "",
        "feed": [dict(f, who=short_names(servers).get(f.get("session") or "", f.get("who")))
                 for f in comms.feed(snap.events, since_s=24 * 3600, limit=150)],
    }


def _stats2(snap, cfg):
    """Stats v2 fact table; never let it break the rest of the dashboard."""
    try:
        from . import stats2
        from .app import cache_dir
        return stats2.build(snap, cfg, cache_dir())
    except Exception as exc:
        return {"error": f"{exc.__class__.__name__}: {exc}"[:200]}


from .html_page import PAGE  # noqa: E402  (template lives in its own module)


def page(data: dict, live: bool = False) -> str:
    blob = json.dumps(data, default=str).replace("</", "<\\/")
    return PAGE.replace("__DATA__", blob).replace("__LIVE__", "true" if live else "false")


def write(snap, cfg, path: Path) -> Path:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page(payload(snap, cfg)))
    return path


def _etag_matches(header: str | None, etag: str) -> bool:
    if not header:
        return False
    tags = [part.strip() for part in header.split(",")]
    return "*" in tags or etag in (tag[2:] if tag.startswith("W/") else tag for tag in tags)


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        self.stop_event = threading.Event()
        super().__init__(*args, **kwargs)

    def server_close(self):
        self.stop_event.set()
        super().server_close()


def serve(gather_fn, cfg, *, port: int = 8765, interval: int = 30, team_interval: int = 12,
          host: str = "127.0.0.1", send_fn=None):
    """Serve coherent, canonical regions plus the historical compatibility view."""
    from . import regions
    from .app import cache_dir, refresh_sessions

    initial = gather_fn()
    generations = regions.source_generations(cfg)
    cache = regions.RegionCache(payload(initial, cfg), now=initial.now, generations=generations)
    state = {"snap": initial, "at": initial.now.isoformat(), "error": None, "generations": generations}
    state_lock = threading.RLock()

    def set_error(exc):
        error = f"{exc.__class__.__name__}: {exc}"[:200]
        with state_lock:
            state["error"] = error
            gens = dict(state["generations"], presence="error:" + error)
        summary = dict(cache.region("summary").data, refresh_error=error)
        cache.replace_selected({"summary": summary}, generations=gens, force=True)

    def core_rebuild():
        try:
            snap = gather_fn()
            gens = regions.source_generations(cfg)
            full = payload(snap, cfg)
            full["refresh_error"] = None
            cache.replace(full, now=snap.now, generations=gens)
            with state_lock:
                state.update(snap=snap, at=snap.now.isoformat(), error=None, generations=gens)
        except Exception as exc:              # keep last-good documents and expose the failure in summary
            set_error(exc)

    def team_rebuild():
        try:
            gens = regions.source_generations(cfg)
            dirty = [name for name in ("team", "activity") if
                     cache.region(name).basis != tuple((key, gens.get(key))
                                                       for key in regions.REGION_INPUTS[name])]
            if not dirty:
                return
            with state_lock:
                base = state["snap"]
            snap = refresh_sessions(cfg, base)
            # refresh_sessions may advance telemetry cursors; publish the Team
            # document against that new usage generation in the same cycle.
            gens = regions.source_generations(cfg)
            cache.replace_selected(fast_regions(snap, cfg, dirty), generations=gens)
            with state_lock:
                state.update(snap=snap, at=snap.now.isoformat(), generations=gens)
        except Exception as exc:
            set_error(exc)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _send(self, code, body=b"", ctype=None, etag=None, cache_control="no-store"):
            self.send_response(code)
            if ctype:
                self.send_header("Content-Type", ctype)
            if etag:
                self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache_control)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body and self.command != "HEAD":
                self.wfile.write(body)

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
            self._send(code, regions.canonical_bytes(out), "application/json")

        def do_GET(self):
            from urllib.parse import unquote, urlsplit
            path = urlsplit(self.path).path
            if path.startswith("/api/regions/"):
                name = unquote(path[len("/api/regions/"):])
                doc = cache.region(name) if name in regions.NAMES else None
                if doc is None:
                    self.send_error(404)
                elif _etag_matches(self.headers.get("If-None-Match"), doc.etag):
                    self._send(304, etag=doc.etag, cache_control="no-cache")
                else:
                    self._send(200, doc.body, "application/json", doc.etag, "no-cache")
                return
            if path.startswith("/api/task/"):
                task = unquote(path[len("/api/task/"):])
                doc = cache.detail(task)
                if doc is None:
                    self.send_error(404)
                elif _etag_matches(self.headers.get("If-None-Match"), doc.etag):
                    self._send(304, etag=doc.etag, cache_control="no-cache")
                else:
                    self._send(200, doc.body, "application/json", doc.etag, "no-cache")
                return
            if path.startswith("/api/spend/"):
                task = unquote(path[len("/api/spend/"):])
                doc = cache.detail(task)
                if doc is None:
                    self.send_error(404)
                    return
                detail = doc.data
                baseline = {"oracle": (detail.get("oracle") or [None, None])[1],
                            "avocado": (detail.get("avocado") or [None, None])[1],
                            "codex": (detail.get("codex") or [None, None])[1]}
                try:
                    from . import costs
                    value = costs.online_usage(task, cfg, cache_dir(), baseline=baseline)
                    self._send(200, regions.canonical_bytes(value), "application/json", cache_control="no-cache")
                except Exception as exc:
                    self._send(200, regions.canonical_bytes({"source": "codimango read-only CLI",
                               "run_count": None, "trial_count": sum(x or 0 for x in baseline.values()),
                               "trials_by_kind": baseline,
                               "cost": {"available": False, "label": "cost unavailable"},
                               "error": f"{exc.__class__.__name__}: {exc}"[:160]}),
                               "application/json", cache_control="no-cache")
                return
            with state_lock:
                built_at, error = state["at"], state["error"]
            if path == "/api/health":
                self._send(200, regions.canonical_bytes({"ok": True, "service": "workboard", "built_at": built_at}),
                           "application/json", cache_control="no-cache")
            elif path == "/data.json":
                data = dict(cache.compatibility(), generated_at=built_at, refresh_error=error)
                self._send(200, regions.canonical_bytes(data), "application/json")
            elif path in ("/", "/index.html"):
                data = dict(cache.bootstrap(), generated_at=built_at, refresh_error=error)
                self._send(200, page(data, live=True).encode(), "text/html; charset=utf-8")
            else:
                self.send_error(404)

    srv = _Server((host, port), Handler)
    srv.region_cache = cache

    def scheduler():
        next_core = time.monotonic() + max(1, interval)
        next_team = time.monotonic() + max(1, team_interval)
        while not srv.stop_event.is_set():
            now = time.monotonic()
            if now >= next_core:
                core_rebuild()
                next_core = time.monotonic() + max(1, interval)
                next_team = min(next_team, time.monotonic() + max(1, team_interval))
            elif now >= next_team:
                team_rebuild()
                next_team = time.monotonic() + max(1, team_interval)
            wait = max(0.05, min(next_core, next_team) - time.monotonic())
            srv.stop_event.wait(wait)

    threading.Thread(target=scheduler, daemon=True, name="workboard-regions").start()
    return srv

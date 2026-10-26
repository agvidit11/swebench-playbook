"""Server/session communication on top of the shared ledger.

* messages: `msg` events addressed to all / a server / a session; `ack` events mark them handled.
* inbox: what is addressed to *this* session/server and not yet acked by it.
* delivery: `board sync` writes inbox-cache.json; the Claude Code hook injects unread messages into the session as
  additional context (once per message per session), so sessions receive messages without anyone relaying them.
* feed + servers: a cross-server activity timeline and per-server health for the dashboard / `board feed`.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from . import events

INBOX_CACHE = "inbox-cache.json"
DELIVERED = "inbox-delivered.json"
FEED_TYPES = {"msg", "claim", "release", "steal", "assign", "check", "review", "presence", "note", "checkin"}   # not heartbeat/receipt
RECEIPT_RANK = {"queued": 0, "published": 1, "failed": 1, "delivered": 2, "acked": 3}


def target_for_task(task: str, views, sessions: list[dict] | None = None) -> dict:
    """Resolve a task to its current owner and pin that recipient at send time."""
    view = next((v for v in views if getattr(v, "entity_id", None) == task), None)
    if view is None:
        raise ValueError(f"no task matches {task!r}")
    f = view.fields
    native = f.get("owner_session")
    if not native:
        active = (f.get("activity") or {}).get("session_keys") or []
        native = active[0] if len(active) == 1 else None
    if not native:
        raise ValueError(f"{task} has no resolved owner — choose a server or everyone")
    sessions = sessions or []
    session = next((s for s in sessions if native in (s.get("native_id"), s.get("session_key"))), None)
    target_id = session.get("session_key") if session else native
    label = session.get("name") if session else f.get("owner") or native
    host = session.get("host") if session else (label.split("·", 1)[0] if "·" in label else None)
    recipient = {"session_key": target_id, "native_id": session.get("native_id") if session else native,
                 "host": host, "name": label}
    return {"to": f"session:{target_id}", "to_label": label, "selector": {"kind": "task_owner", "task": task},
            "resolved_recipients": [recipient], "task": task}


def target_for(spec: str, aliases: dict[str, str], servers: list[str], *, views=(), sessions=()) -> dict:
    """'all' | server id | tab-title fragment -> {to, to_label}. Raises ValueError if ambiguous/unknown."""
    spec = spec.strip()
    if spec.lower() in ("all", "everyone", "*"):
        return {"to": "all", "to_label": "everyone"}
    if spec in servers:
        return {"to": f"host:{spec}", "to_label": f"server {spec}"}
    task = spec[5:] if spec.startswith("task:") else spec
    if any(getattr(v, "entity_id", None) == task for v in views):
        return target_for_task(task, views, list(sessions))
    labels = dict(aliases)
    for session in sessions:
        labels[session.get("session_key") or session.get("native_id")] = session.get("name") or "unnamed session"
    hits = {sid: a for sid, a in labels.items() if spec.lower() in a.lower() or spec == sid}
    if len(hits) == 1:
        sid, alias = next(iter(hits.items()))
        session = next((s for s in sessions if sid in (s.get("session_key"), s.get("native_id"))), None)
        recipient = ({"session_key": session.get("session_key"), "native_id": session.get("native_id"),
                      "host": session.get("host"), "name": alias} if session else
                     {"session_key": sid, "native_id": sid, "host": None, "name": alias})
        return {"to": f"session:{sid}", "to_label": alias, "selector": {"kind": "session"},
                "resolved_recipients": [recipient]}
    if not hits:
        raise ValueError(f"no server or session matches {spec!r} (servers: {', '.join(servers) or 'none'})")
    raise ValueError(f"{spec!r} matches several sessions: " + ", ".join(sorted(hits.values())[:5]))


def new_message(text: str, target: dict, actor: dict, task: str | None = None, reply_to: str | None = None) -> dict:
    payload = {"to": target["to"], "to_label": target["to_label"], "text": text.strip()[:8000]}
    if target.get("selector"):
        payload["selector"] = target["selector"]
    if target.get("resolved_recipients"):
        payload["resolved_recipients"] = target["resolved_recipients"]
    if reply_to:
        payload["reply_to"] = reply_to
    return events.new_event("msg", task or target.get("task"), payload, actor=actor, commit=None, source="comms")


def receipt_event(msg_id: str, recipient: str, state: str, actor: dict, *, reason: str = "",
                  transport: str = "courier") -> dict:
    if state not in ("delivered", "failed"):
        raise ValueError("receipt state must be delivered or failed")
    payload = {"msg_id": msg_id, "recipient": recipient, "state": state, "transport": transport}
    if reason:
        payload["reason"] = reason[:300]
    return events.new_event("receipt", None, payload, actor=actor, commit=None, source="comms")


def _receipt_states(evs: list[dict]) -> dict[tuple[str, str], dict]:
    out = {}
    ordered = sorted((e for e in evs if e.get("type") == "receipt"),
                     key=lambda e: (e.get("occurred_at") or "", e.get("host_id") or "", e.get("seq") or 0))
    for e in ordered:
        p = e.get("payload") or {}
        key, state = (p.get("msg_id"), p.get("recipient")), p.get("state")
        if not all(isinstance(x, str) and x for x in key) or state not in RECEIPT_RANK:
            continue
        old = out.get(key)
        if old and RECEIPT_RANK[old["state"]] > RECEIPT_RANK[state]:
            continue
        if old and old["state"] == state:                 # retry event is idempotent in the visible reducer
            continue
        out[key] = {"state": state, "at": e.get("occurred_at"), "reason": p.get("reason", ""),
                    "transport": p.get("transport", "")}
    return out


def messages(evs: list[dict]) -> list[dict]:
    acks = {}
    for e in evs:
        if e["type"] == "ack" and isinstance(e["payload"].get("msg_id"), str):
            acks.setdefault(e["payload"]["msg_id"], []).append(e["actor"].get("session_id"))
    receipts = _receipt_states(evs)
    out = []
    for e in evs:
        if e["type"] != "msg":
            continue
        p = e["payload"]
        recipients = [dict(x) for x in p.get("resolved_recipients", []) if isinstance(x, dict)]
        if not recipients and str(p.get("to", "")).startswith("session:"):
            key = p["to"].split(":", 1)[1]
            recipients = [{"session_key": key, "native_id": key, "host": None, "name": p.get("to_label", key)}]
        states = []
        for recipient in recipients:
            key = recipient.get("session_key") or recipient.get("native_id")
            rec = receipts.get((e["event_id"], key), {"state": "queued" if e.get("_pending_local") else "published",
                                                       "at": e.get("recorded_at") or e.get("occurred_at"),
                                                       "reason": "", "transport": ""})
            native = recipient.get("native_id") or key
            if native in acks.get(e["event_id"], []) or key in acks.get(e["event_id"], []):
                rec = {"state": "acked", "at": rec.get("at"), "reason": "", "transport": rec.get("transport", "")}
            states.append({**recipient, **rec})
        aggregate = ("acked" if states and all(x["state"] == "acked" for x in states) else
                     "delivered" if states and all(x["state"] in ("delivered", "acked") for x in states) else
                     "failed" if states and all(x["state"] == "failed" for x in states) else
                     "queued" if e.get("_pending_local") else "published")
        out.append({"id": e["event_id"], "at": e["occurred_at"], "from": e["actor"].get("alias", ""),
                    "from_session": e["actor"].get("session_id"), "from_host": e.get("host_id"),
                    "to": p.get("to", "all"), "to_label": p.get("to_label", ""), "text": p.get("text", ""),
                    "task": (e.get("entity") or {}).get("id"), "reply_to": p.get("reply_to"),
                    "acked_by": acks.get(e["event_id"], []), "delivery": {"state": aggregate, "recipients": states}})
    return sorted(out, key=lambda m: m["at"])


def addressed_to(m: dict, session_id: str, host_id: str) -> bool:
    pinned = (m.get("delivery") or {}).get("recipients") or []
    return (m["to"] == "all" or m["to"] == f"host:{host_id}" or m["to"] == f"session:{session_id}" or
            any(session_id in (x.get("session_key"), x.get("native_id")) for x in pinned))


def inbox(evs: list[dict], session_id: str, host_id: str, include_acked: bool = False) -> list[dict]:
    return [m for m in messages(evs) if addressed_to(m, session_id, host_id) and m["from_session"] != session_id
            and (include_acked or session_id not in m["acked_by"])]


def ack_event(msg_id: str, actor: dict) -> dict:
    return events.new_event("ack", None, {"msg_id": msg_id}, actor=actor, commit=None, source="comms")


def _broadcast_target(session: dict, sent_at: str | None) -> bool:
    if session.get("session_kind") not in (None, "interactive") or str(session.get("name") or "").startswith("mcdaemon"):
        return False
    try:
        return not session.get("started_at") or not sent_at or \
            datetime.fromisoformat(session["started_at"]) <= datetime.fromisoformat(sent_at)
    except (TypeError, ValueError):
        return True


def courier_jobs(evs: list[dict], sessions: list[dict], host_id: str) -> list[dict]:
    """Undelivered local Claude recipients. Message bodies remain sourced from the private ledger."""
    local = [s for s in sessions if s.get("host") == host_id and s.get("kind") == "claude"]
    receipts = _receipt_states(evs)              # broadcasts have no pinned list: receipts must be checked directly
    out, seen = [], set()
    for m in messages(evs):
        pinned = (m.get("delivery") or {}).get("recipients") or []
        if pinned:
            candidates = [s for s in local if any(s.get("session_key") == r.get("session_key") or
                                                  s.get("native_id") == r.get("native_id") for r in pinned)]
        elif m["to"] == "all" or m["to"] == f"host:{host_id}":
            # Broadcasts reach interactive sessions that existed when it was sent: daemons and sessions started later
            # (e.g. short-lived mcdaemon-NN workers) never receive old broadcasts.
            candidates = [s for s in local if _broadcast_target(s, m.get("at"))]
        elif m["to"].startswith("session:"):
            key = m["to"].split(":", 1)[1]
            candidates = [s for s in local if key in (s.get("session_key"), s.get("native_id"))]
        else:
            candidates = []
        state_by_key = {r.get("session_key") or r.get("native_id"): r for r in pinned}
        for session in candidates:
            recipient = session.get("session_key") or session.get("native_id")
            state = state_by_key.get(recipient, {}).get("state", "published")
            for k in (recipient, session.get("native_id")):
                rec = receipts.get((m["id"], k))
                if rec and RECEIPT_RANK.get(rec["state"], 0) > RECEIPT_RANK.get(state, 0):
                    state = rec["state"]
            if session.get("native_id") in m.get("acked_by", []):
                state = "acked"
            key = (m["id"], recipient)
            if key in seen or state in ("delivered", "acked", "failed") or m["from_session"] == session.get("native_id"):
                continue
            seen.add(key)
            out.append({"message_id": m["id"], "recipient": recipient, "native_id": session.get("native_id"),
                        "name": session.get("name"), "host": host_id, "task": m.get("task"),
                        "from": m.get("from"), "body": m.get("text"), "state": state})
    return out


# ------------------------------------------------------------------------------------------- hook delivery
def write_inbox_cache(state_dir: Path, evs: list[dict]) -> None:
    """All messages (with ack lists), compact, for the hook to filter by session quickly."""
    data = {"at": datetime.now(timezone.utc).isoformat(), "messages": messages(evs)[-300:]}
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".inbox-")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    os.chmod(tmp, 0o600)
    os.replace(tmp, state_dir / INBOX_CACHE)


def pending_for_hook(state_dir: Path, session_id: str, host_id: str, max_items: int = 5) -> list[dict]:
    """Unread, undelivered messages for this session; marks them delivered (once per session)."""
    state_dir = Path(state_dir)
    try:
        cache = json.loads((state_dir / INBOX_CACHE).read_text())
    except (OSError, ValueError):
        return []
    import fcntl
    lock = os.open(state_dir / (DELIVERED + ".lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            delivered = json.loads((state_dir / DELIVERED).read_text())
        except (OSError, ValueError):
            delivered = {}
        mine = delivered.get(session_id, [])            # [[msg_id, at], ...] newest last
        mine_ids = {x[0] for x in mine if isinstance(x, list)}
        out = [m for m in cache.get("messages", []) if addressed_to(m, session_id, host_id)
               and m.get("from_session") != session_id and session_id not in m.get("acked_by", [])
               and m["id"] not in mine_ids][:max_items]
        if out:
            merged = [x for x in mine if isinstance(x, list)] + [[m["id"], m["at"]] for m in out]
            delivered[session_id] = sorted(merged, key=lambda x: x[1])[-500:]
            fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".delivered-")
            with os.fdopen(fd, "w") as fh:
                json.dump(delivered, fh)
            os.replace(tmp, state_dir / DELIVERED)
        return out
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)


def hook_context(msgs: list[dict]) -> str:
    lines = ["📬 workboard: you have messages from other sessions/servers (shared ledger):"]
    for m in msgs:
        about = f" [task {m['task']}]" if m.get("task") else ""
        lines.append(f"- from {m['from']} to {m['to_label']}{about}: {m['text']}  (ack: board ack {m['id'][:8]})")
    lines.append("Act on them if relevant, reply with `board msg <to> \"...\"`, then `board ack <id>`.")
    return "\n".join(lines)


# ------------------------------------------------------------------------------------------- feed + servers
def feed(evs: list[dict], since_s: float = 24 * 3600, now: float | None = None, limit: int = 200) -> list[dict]:
    """Cross-server activity, newest first. Presence is collapsed to the first sighting per (task, session)."""
    now = now or time.time()
    out, seen_presence = [], set()
    for e in evs:
        if e["type"] not in FEED_TYPES:
            continue
        try:
            at = datetime.fromisoformat(e["occurred_at"]).timestamp()
        except ValueError:
            continue
        if now - at > since_s:
            continue
        task = (e.get("entity") or {}).get("id")
        if e["type"] == "presence":
            key = (task, e["actor"].get("session_id"))
            if key in seen_presence:
                continue
            seen_presence.add(key)
        p = e["payload"]
        what = {"msg": f"💬 → {p.get('to_label', '')}: {p.get('text', '')}",
                "claim": "👤 claimed" + (" (auto)" if p.get("auto") else ""), "release": f"🔓 released — {p.get('reason', '')}",
                "steal": "🤺 took over an expired claim", "assign": f"→ assigned to {p.get('to_alias', '')}",
                "check": f"🧪 presubmit P{p.get('pass', 0)} W{p.get('warn', 0)} F{p.get('fail', 0)}",
                "review": f"👀 review: {p.get('verdict', '')}" + (f" C{p['confidence']}" if p.get("confidence") else ""),
                "presence": "✍ started working", "note": f"📜 CLAIMS.md: {p.get('legacy_owner', '')} {p.get('status', '')}",
                "checkin": ("💤 checked in: idle" if p.get("status") == "idle" else
                            "📋 checked in: " + (", ".join(p.get("tasks") or []) or "working"))}[e["type"]]
        if e["type"] == "note" and not p.get("legacy_owner"):
            continue
        out.append({"id": e.get("event_id") or f"{e.get('host_id', '')}:{e.get('seq', '')}",
                    "at": e["occurred_at"], "ts": at, "host": e.get("host_id", ""), "who": e["actor"].get("alias", ""),
                    "type": e["type"], "task": task, "what": what})
    out.sort(key=lambda x: -x["ts"])
    return out[:limit]


def _checkin_view(e: dict | None, now: float) -> dict:
    if not e:
        return {"status": None}
    try:
        ago = int(now - datetime.fromisoformat(e["occurred_at"]).timestamp())
    except ValueError:
        return {"status": None}
    return {"status": e["payload"].get("status"), "tasks": e["payload"].get("tasks") or [],
            "checkin_at": e.get("occurred_at"), "checkin_ago_s": ago}


def _ago(s: float) -> str:
    return f"{int(s // 86400)}d" if s >= 86400 else f"{int(s // 3600)}h" if s >= 3600 else f"{int(s // 60)}m"


def _fold_quiet_runs(rows: list[dict], host: str) -> list[dict]:
    """Codex/Muse processes with no task focus and nothing recent fold into one row each (a host can have dozens of
    leftover processes; listing them one by one buries the real sessions)."""
    keep, quiet = [], {}
    for r in rows:
        f = (r.get("focus") or {}).get("tasks") or []
        idle_s = r.get("status_ago_s") or 0
        if r.get("kind") in ("codex", "muse") and not r.get("is_summary") and not f and idle_s > 2 * 3600:
            quiet.setdefault(r["kind"], []).append(r)
        else:
            keep.append(r)
    for kind, rs in quiet.items():
        if len(rs) < 3:
            keep.extend(rs)
            continue
        ages = sorted(r.get("status_ago_s") or 0 for r in rs)
        keep.append({"session_key": f"quiet-{kind}:{host}", "native_id": f"quiet-{kind}:{host}", "kind": kind,
                     "kind_icon": rs[0].get("kind_icon"), "name": f"{len(rs)} {kind.capitalize()} processes, no task",
                     "is_summary": True, "status": f"idle {_ago(ages[0])}–{_ago(ages[-1])}", "status_group": "unknown",
                     "focus": {"tasks": []}, "tasks": [], "child_runs": [],
                     "advice": {"state": "watch", "reason": f"{len(rs)} live {kind} processes on {host} idle for "
                                f"{_ago(ages[0])}–{_ago(ages[-1])} with no task — probably hung/leftover; check "
                                f"`ps -u $USER -o pid,etime,args | grep {kind}` there and kill what is not needed"},
                     "transport": {"available": False, "kind": "unavailable", "reason": "not an interactive session"},
                     "restart": {"needed": False, "state": "not-applicable", "command": None}})
    return keep


def servers(evs: list[dict], views, cfg, native_sessions: list[dict] | None = None,
            diagnostics: list[dict] | None = None, now: float | None = None,
            sync_state=None, local_host: str | None = None) -> list[dict]:
    """Per server: sync health plus native live sessions and recent ledger-only actors."""
    now = now or time.time()
    native_sessions, diagnostics = native_sessions or [], diagnostics or []
    ids = [s.id for s in cfg.servers] or sorted({e.get("host_id") for e in evs if e.get("host_id")} |
                                                {s.get("host") for s in native_sessions if s.get("host")})
    out = []
    for h in ids:
        mine = [e for e in evs if e.get("host_id") == h]
        host_state = next((d for d in diagnostics if d.get("host") == h and d.get("classification") == "host-state"), {})
        beats = [e for e in mine if e["type"] == "heartbeat"]          # heartbeat = a successful sync from that host
        last = max((datetime.fromisoformat(e["recorded_at"]).timestamp() for e in beats if e.get("recorded_at")),
                   default=None)
        try:
            snapshot_last = datetime.fromisoformat(host_state.get("heartbeat_at")).timestamp()
            last = max(x for x in (last, snapshot_last) if x is not None)
        except (TypeError, ValueError):
            pass
        if h == local_host and sync_state is not None and getattr(sync_state, "last_pull_ok", False) and \
                (getattr(sync_state, "last_push_ok", False) or not getattr(sync_state, "pending", 0)):
            try:
                local_last = datetime.fromisoformat(sync_state.at).timestamp()
                last = max(x for x in (last, local_last) if x is not None)
            except (TypeError, ValueError):
                pass
        last_act = max((datetime.fromisoformat(e["recorded_at"]).timestamp() for e in mine if e.get("recorded_at")),
                       default=None)
        checkins = {}
        for e in mine:
            if e["type"] == "checkin":
                checkins[e["actor"].get("session_id", "")] = e
        ledger_sessions = {}
        for e in mine:
            try:
                at = datetime.fromisoformat(e["occurred_at"]).timestamp()
            except ValueError:
                continue
            sid = e["actor"].get("session_id", "")
            kind = e["actor"].get("kind")
            if now - at <= 2 * 3600 and kind in ("claude", "codex", "muse", "human") and sid:
                previous = ledger_sessions.get(sid, (0, "", kind))
                ledger_sessions[sid] = max(previous[0], at), e["actor"].get("alias", ""), kind
        owned = [v.entity_id for v in views if (v.fields.get("owner") or "").startswith(f"{h}·")
                 and (v.fields.get("assignment") or {}).get("state") in ("claimed", "legacy")]
        native = []
        for s in native_sessions:
            if s.get("host") != h:
                continue
            sid = s.get("native_id")
            tasks = sorted(set(s.get("tasks") or []) |
                           {v.entity_id for v in views if v.fields.get("owner_session") == sid})
            status_since = None
            try:
                status_since = int(now - datetime.fromisoformat(s["status_since"]).timestamp()) if s.get("status_since") else None
            except ValueError:
                pass
            child_runs = [{k: r.get(k) for k in ("session_key", "native_id", "kind", "kind_icon", "name", "status",
                                                  "started_at", "age_s", "last_activity_at", "cwd_task", "model",
                                                  "effort", "parent_confidence", "transport", "tokens")}
                          for r in s.get("child_runs") or []]
            native.append({k: v for k, v in {
                "session_key": s.get("session_key"), "native_id": sid, "alias": f"{h}·{s.get('name')}",
                "name": s.get("name"), "kind": s.get("kind"), "kind_icon": s.get("kind_icon"),
                "started_at": s.get("started_at"), "age_s": s.get("age_s"),
                "last_activity_at": s.get("last_activity_at"),
                "ago_s": 0 if s.get("live") else s.get("age_s"),
                "status": s.get("status"), "status_since": s.get("status_since"),
                "status_ago_s": status_since, "live": s.get("live"),
                "classification": s.get("classification"), "liveness_reason": s.get("liveness_reason"),
                "focus": s.get("focus"), "tasks": tasks, "child_runs": child_runs, "transport": s.get("transport"),
                "restart": s.get("restart"), "tokens": s.get("tokens"), "advice": s.get("advice"),
                "last_report": s.get("last_report"), "last_request": s.get("last_request"),
                "is_summary": s.get("is_summary"), "recent_run_count": s.get("recent_run_count"),
                "older_run_count": s.get("older_run_count"),
                "older_child_run_count": s.get("older_child_run_count")}.items() if v is not None})
        native_ids = {s.get("native_id") for s in native}
        fallback = [dict({"session_key": sid, "native_id": sid, "alias": a, "name": a.split("·", 1)[-1],
                          "kind": kind, "kind_icon": {"claude": "🟣", "codex": "🟢", "muse": "🟠",
                                                        "human": "👤"}.get(kind, "❔"),
                          "started_at": None, "last_activity_at": datetime.fromtimestamp(t, timezone.utc).isoformat(),
                          "age_s": None, "ago_s": int(now - t),
                          "status": None, "live": None,
                          "classification": "human-shell" if kind == "human" else "ledger-only",
                          "is_actor": kind == "human", "tasks": [],
                          "child_runs": [], "transport": {"available": False, "kind": "hook",
                                                            "reason": "human shell actor" if kind == "human" else
                                                                      "native registry entry unavailable"},
                          "restart": {"state": "not-applicable" if kind == "human" else "unknown",
                                      "needed": False, "reason": "human shell actor" if kind == "human" else
                                                                  "native registry entry unavailable", "command": None},
                          "tokens": {"total": None, "reason": "—"},
                          "advice": {"state": "keep" if kind == "human" else "watch",
                                     "reason": "human shell check-in" if kind == "human" else
                                               "registry entry unavailable"}},
                         **_checkin_view(checkins.get(sid), now))
                    for sid, (t, a, kind) in sorted(ledger_sessions.items(), key=lambda kv: -kv[1][0])
                    if sid not in native_ids and (kind == "human" or not native)][:12]   # registry is authoritative where present
        rows = native + fallback
        for row in rows:
            raw = str(row.get("status") or "unknown").lower()
            if raw in ("busy", "shell", "working", "running") and (row.get("status_ago_s") or 0) > 6 * 3600 and \
                    not row.get("is_actor"):
                row["status"] = raw = f"stale ({raw} {_ago(row['status_ago_s'])} ago)"   # registry not updated since
            row["status_group"] = ("waiting" if raw.startswith("waiting") else
                                   "busy" if raw in ("busy", "shell", "working", "active", "running") else
                                   "idle" if raw == "idle" else "unknown")
        rows = _fold_quiet_runs(rows, h)
        interactive = [s for s in rows if not s.get("is_summary") and not s.get("is_actor")]
        counts = {key: sum(s.get("status_group") == key for s in interactive)
                  for key in ("busy", "waiting", "idle", "unknown")}
        local_state = sync_state if h == local_host else None
        sync_error = getattr(local_state, "error", "") if local_state is not None else host_state.get("sync_error", "")
        queue = getattr(local_state, "pending", 0) if local_state is not None else host_state.get("queue", 0)
        out.append({"id": h,
                    "last_sync_at": datetime.fromtimestamp(last, timezone.utc).isoformat() if last else None,
                    "last_sync_ago_s": int(now - last) if last else None,
                    "last_activity_at": datetime.fromtimestamp(last_act, timezone.utc).isoformat() if last_act else None,
                    "last_activity_ago_s": int(now - last_act) if last_act else None,
                    "sessions": rows, "session_count": len(interactive), "human_actor_count": sum(bool(s.get("is_actor")) for s in rows),
                    "status_counts": counts, "queue": int(queue or 0), "sync_error": str(sync_error or "")[:300],
                    "owned": owned,
                    "session_diagnostics": [d for d in diagnostics if d.get("host") == h and
                                             d.get("classification") != "host-state"]})
    return out

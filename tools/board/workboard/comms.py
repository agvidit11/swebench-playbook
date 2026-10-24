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
FEED_TYPES = {"msg", "claim", "release", "steal", "assign", "check", "review", "presence", "note"}   # not heartbeat


def target_for(spec: str, aliases: dict[str, str], servers: list[str]) -> dict:
    """'all' | server id | tab-title fragment -> {to, to_label}. Raises ValueError if ambiguous/unknown."""
    spec = spec.strip()
    if spec.lower() in ("all", "everyone", "*"):
        return {"to": "all", "to_label": "everyone"}
    if spec in servers:
        return {"to": f"host:{spec}", "to_label": f"server {spec}"}
    hits = {sid: a for sid, a in aliases.items() if spec.lower() in a.lower()}
    if len(hits) == 1:
        sid, alias = next(iter(hits.items()))
        return {"to": f"session:{sid}", "to_label": alias}
    if not hits:
        raise ValueError(f"no server or session matches {spec!r} (servers: {', '.join(servers) or 'none'})")
    raise ValueError(f"{spec!r} matches several sessions: " + ", ".join(sorted(hits.values())[:5]))


def new_message(text: str, target: dict, actor: dict, task: str | None = None, reply_to: str | None = None) -> dict:
    payload = {"to": target["to"], "to_label": target["to_label"], "text": text.strip()[:1000]}
    if reply_to:
        payload["reply_to"] = reply_to
    return events.new_event("msg", task, payload, actor=actor, commit=None, source="comms")


def messages(evs: list[dict]) -> list[dict]:
    acks = {}
    for e in evs:
        if e["type"] == "ack" and isinstance(e["payload"].get("msg_id"), str):
            acks.setdefault(e["payload"]["msg_id"], []).append(e["actor"].get("session_id"))
    out = []
    for e in evs:
        if e["type"] != "msg":
            continue
        p = e["payload"]
        out.append({"id": e["event_id"], "at": e["occurred_at"], "from": e["actor"].get("alias", ""),
                    "from_session": e["actor"].get("session_id"), "from_host": e.get("host_id"),
                    "to": p.get("to", "all"), "to_label": p.get("to_label", ""), "text": p.get("text", ""),
                    "task": (e.get("entity") or {}).get("id"), "reply_to": p.get("reply_to"),
                    "acked_by": acks.get(e["event_id"], [])})
    return sorted(out, key=lambda m: m["at"])


def addressed_to(m: dict, session_id: str, host_id: str) -> bool:
    return m["to"] == "all" or m["to"] == f"host:{host_id}" or m["to"] == f"session:{session_id}"


def inbox(evs: list[dict], session_id: str, host_id: str, include_acked: bool = False) -> list[dict]:
    return [m for m in messages(evs) if addressed_to(m, session_id, host_id) and m["from_session"] != session_id
            and (include_acked or session_id not in m["acked_by"])]


def ack_event(msg_id: str, actor: dict) -> dict:
    return events.new_event("ack", None, {"msg_id": msg_id}, actor=actor, commit=None, source="comms")


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
                "steal": "🤺 took over an expired claim", "assign": f"➡️ assigned to {p.get('to_alias', '')}",
                "check": f"🧪 presubmit P{p.get('pass', 0)} W{p.get('warn', 0)} F{p.get('fail', 0)}",
                "review": f"👀 review: {p.get('verdict', '')}" + (f" C{p['confidence']}" if p.get("confidence") else ""),
                "presence": "✍️ started working", "note": f"📜 CLAIMS.md: {p.get('legacy_owner', '')} {p.get('status', '')}"
                }[e["type"]]
        if e["type"] == "note" and not p.get("legacy_owner"):
            continue
        out.append({"at": e["occurred_at"], "ts": at, "host": e.get("host_id", ""), "who": e["actor"].get("alias", ""),
                    "type": e["type"], "task": task, "what": what})
    out.sort(key=lambda x: -x["ts"])
    return out[:limit]


def servers(evs: list[dict], views, cfg, now: float | None = None) -> list[dict]:
    """Per server: last ledger activity, sessions seen in the last 2h (tab titles), tasks owned/active."""
    now = now or time.time()
    ids = [s.id for s in cfg.servers] or sorted({e.get("host_id") for e in evs if e.get("host_id")})
    out = []
    for h in ids:
        mine = [e for e in evs if e.get("host_id") == h]
        beats = [e for e in mine if e["type"] == "heartbeat"]          # heartbeat = a successful sync from that host
        last = max((datetime.fromisoformat(e["recorded_at"]).timestamp() for e in beats if e.get("recorded_at")),
                   default=None)
        last_act = max((datetime.fromisoformat(e["recorded_at"]).timestamp() for e in mine if e.get("recorded_at")),
                       default=None)
        sessions = {}
        for e in mine:
            try:
                at = datetime.fromisoformat(e["occurred_at"]).timestamp()
            except ValueError:
                continue
            sid = e["actor"].get("session_id", "")
            if now - at <= 2 * 3600 and e["actor"].get("kind") in ("claude", "codex") and sid:
                sessions[sid] = max(sessions.get(sid, (0, ""))[0], at), e["actor"].get("alias", "")
        owned = [v.entity_id for v in views if (v.fields.get("owner") or "").startswith(f"{h}·")
                 and v.fields.get("claim_health") in ("OWNED", "ACTIVE")]
        out.append({"id": h, "last_sync_ago_s": int(now - last) if last else None,
                    "last_activity_ago_s": int(now - last_act) if last_act else None,
                    "sessions": [{"alias": a, "ago_s": int(now - t)} for t, a in sorted(sessions.values(), reverse=True)][:12],
                    "owned": owned})
    return out

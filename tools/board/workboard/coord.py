"""Coordination commands shared by the CLI and the sync worker: claim, release, assign, auto-claim, renew."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import claims, events, sync as sync_mod
from .identity import current_actor

LOCAL_CLAIMS = "claims-local.json"


def _now():
    return datetime.now(timezone.utc)


def host_id(cfg) -> str:
    return sync_mod.safe_host(sync_mod.host_id_for(cfg))


def _local(state_dir) -> dict:
    try:
        return json.loads((Path(state_dir) / LOCAL_CLAIMS).read_text())
    except (OSError, ValueError):
        return {}


def _save_local(state_dir, data) -> None:
    import os, tempfile
    fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".claims-")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, Path(state_dir) / LOCAL_CLAIMS)


def record(state_dir, type_, task, actor, payload, commit=None) -> bool:
    return events.spool_append(Path(state_dir), events.new_event(type_, task, payload, actor=actor, commit=commit,
                                                                 source="workboard"))


def ledger_fresh(cfg, state_dir, timeout=15) -> tuple[bool, str]:
    """Coordination writes fail closed unless the ledger syncs now."""
    st = sync_mod.sync(cfg, state_dir=state_dir, timeout_seconds=timeout)
    if st.busy:
        st = sync_mod.load_state(state_dir)
    ok = st.last_pull_ok
    return ok, st.error


def claim(cfg, task, *, state_dir, actor=None, to_actor=None, steal=False, clock_healthy=True) -> claims.ClaimResult:
    actor = actor or current_actor(host_id(cfg))
    owner = to_actor or actor
    pr = claims.ensure_probe(cfg, state_dir)
    if not pr.ok:
        return claims.ClaimResult("REFUSED", None, f"claims disabled: probe failed ({pr.detail})")
    if steal:
        res = claims.steal(cfg, task, owner, state_dir=state_dir, source_healthy=True, clock_healthy=clock_healthy)
    else:
        res = claims.acquire(cfg, task, owner, state_dir=state_dir)
    if res.status == "ACQUIRED":
        local = _local(state_dir)
        local[task] = {"oid": res.oid, "session_id": owner["session_id"], "renewed": _now().isoformat()}
        _save_local(state_dir, local)
        record(state_dir, "steal" if steal else "claim", task, owner, {"oid": res.oid, "by": actor["alias"]})
        if to_actor:
            record(state_dir, "assign", task, actor, {"to_session": owner["session_id"], "to_alias": owner["alias"]})
    return res


def release(cfg, task, reason, *, state_dir, actor=None) -> claims.ClaimResult:
    actor = actor or current_actor(host_id(cfg))
    cur = claims.read(cfg, task, state_dir=state_dir)
    if cur.status != "HELD":
        return claims.ClaimResult("RELEASED" if cur.status == "FREE" else cur.status, None, cur.detail or "not claimed")
    if cur.owner.get("session_id") != actor["session_id"] and actor["kind"] != "human":
        return claims.ClaimResult("REFUSED", cur.oid, f"owned by {cur.owner.get('alias')}", cur.owner)
    if actor["kind"] == "human" and cur.owner.get("session_id") != actor["session_id"]:
        actor = dict(actor, session_id=cur.owner["session_id"])   # the person can release their own agents' claims
    res = claims.release(cfg, task, actor, expected_oid=cur.oid, state_dir=state_dir)
    if res.status == "RELEASED":
        local = _local(state_dir)
        local.pop(task, None)
        _save_local(state_dir, local)
        record(state_dir, "release", task, actor, {"reason": reason, "was": cur.owner.get("alias", "")})
    return res


def auto_claims(cfg, state_dir, touched: list[tuple[str, dict]]) -> list[str]:
    """Called by sync for spooled touch events: claim free tasks, renew own claims older than the interval."""
    notes = []
    if not claims.ensure_probe(cfg, state_dir).ok:
        return ["claims disabled: probe failed"]
    local = _local(state_dir)
    interval = timedelta(minutes=cfg.claims.heartbeat_interval_minutes)
    for task, actor in touched:
        mine = local.get(task)
        if mine and mine.get("session_id") == actor.get("session_id"):
            renewed = datetime.fromisoformat(mine["renewed"])
            if _now() - renewed >= interval:
                res = claims.heartbeat(cfg, task, actor, expected_oid=mine["oid"], state_dir=state_dir)
                if res.status == "ACQUIRED":
                    mine.update(oid=res.oid, renewed=_now().isoformat())
                    record(state_dir, "renew", task, actor, {"oid": res.oid})
                else:
                    local.pop(task, None)
                    notes.append(f"{task}: lost claim ({res.status} {res.detail})")
            continue
        cur = claims.read(cfg, task, state_dir=state_dir)
        if cur.status == "FREE":
            res = claims.acquire(cfg, task, actor, state_dir=state_dir)
            if res.status == "ACQUIRED":
                local[task] = {"oid": res.oid, "session_id": actor["session_id"], "renewed": _now().isoformat()}
                record(state_dir, "claim", task, actor, {"oid": res.oid, "auto": True})
                notes.append(f"{task}: auto-claimed by {actor.get('alias')}")
    _save_local(state_dir, local)
    return notes

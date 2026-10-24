"""Coordination shared by the CLI and the sync worker: claim, release, assign, auto-claim, renew."""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import claims, events, sync as sync_mod
from .identity import current_actor

LOCAL_CLAIMS = "claims-local.json"


def _now():
    return datetime.now(timezone.utc)


def host_id(cfg) -> str:
    return sync_mod.safe_host(sync_mod.host_id_for(cfg))


def actor_for(cfg) -> dict:
    return current_actor(host_id(cfg), person=cfg.user.id)


@contextlib.contextmanager
def local_claims(state_dir):
    """One flock'd read-modify-write transaction on the local renewal registry."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = os.open(state_dir / (LOCAL_CLAIMS + ".lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = json.loads((state_dir / LOCAL_CLAIMS).read_text())
            data = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            data = {}
        yield data
        fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".claims-")
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh)
        os.replace(tmp, state_dir / LOCAL_CLAIMS)
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)


def record(state_dir, type_, task, actor, payload, commit=None) -> bool:
    return events.spool_append(Path(state_dir), events.new_event(type_, task, payload, actor=actor, commit=commit,
                                                                 source="workboard"))


def ledger_fresh(cfg, state_dir, timeout=15) -> tuple[bool, str]:
    """Coordination writes fail closed unless this run pulled AND pushed with no error."""
    st = sync_mod.sync(cfg, state_dir=state_dir, timeout_seconds=timeout)
    if st.busy:
        return False, "another sync is running; try again in a moment"
    if not (st.last_pull_ok and st.last_push_ok) or (st.error and not st.error.startswith("auto-claim")):
        return False, st.error or "ledger push did not complete"
    return True, ""


def claim(cfg, task, *, state_dir, actor=None, to_actor=None, steal=False, source_healthy=None,
          clock_healthy=None) -> claims.ClaimResult:
    actor = actor or actor_for(cfg)
    owner = to_actor or actor
    pr = claims.ensure_probe(cfg, state_dir)
    if not pr.ok:
        return claims.ClaimResult("REFUSED", None, f"claims disabled: probe failed ({pr.detail})")
    if steal:
        if source_healthy is None or clock_healthy is None:
            return claims.ClaimResult("REFUSED", None, "steal needs claim-source and clock health evidence")
        res = claims.steal(cfg, task, owner, state_dir=state_dir, source_healthy=source_healthy,
                           clock_healthy=clock_healthy)
    else:
        res = claims.acquire(cfg, task, owner, state_dir=state_dir)
    if res.status == "ACQUIRED":
        with local_claims(state_dir) as local:
            local[task] = {"oid": res.oid, "session_id": owner["session_id"], "renewed": _now().isoformat()}
        audited = record(state_dir, "steal" if steal else "claim", task, owner, {"oid": res.oid, "by": actor["alias"]})
        if to_actor:
            audited &= record(state_dir, "assign", task, actor, {"to_session": owner["session_id"],
                                                                 "to_alias": owner["alias"]})
        if not audited:
            res.detail += " (warning: audit event could not be queued)"
    return res


def release(cfg, task, reason, *, state_dir, actor=None) -> claims.ClaimResult:
    """Owner release. A human shell releasing their own agent's claim goes through release_own_agent."""
    actor = actor or actor_for(cfg)
    cur = claims.read(cfg, task, state_dir=state_dir)
    if cur.status != "HELD":
        return claims.ClaimResult("RELEASED" if cur.status == "FREE" else cur.status, None, cur.detail or "not claimed")
    owner_sid = cur.owner.get("session_id") if isinstance(cur.owner, dict) else None
    if actor["kind"] == "human" and owner_sid != actor["session_id"]:
        return release_own_agent(cfg, task, reason, state_dir=state_dir, actor=actor, current=cur)
    res = claims.release(cfg, task, actor, expected_oid=cur.oid, state_dir=state_dir)
    if res.status == "RELEASED":
        with local_claims(state_dir) as local:
            local.pop(task, None)
        record(state_dir, "release", task, actor, {"reason": reason, "was": cur.owner.get("alias", "")})
    return res


def release_own_agent(cfg, task, reason, *, state_dir, actor, current=None) -> claims.ClaimResult:
    """A person releases a claim held by one of their own agent sessions (claim payload person == cfg.user.id).
    The audit event records the human as actor and the released owner separately."""
    if not cfg.user.id:
        return claims.ClaimResult("REFUSED", None, "set [user] id in config to release your agents' claims")
    if actor.get("person") != cfg.user.id:
        return claims.ClaimResult("REFUSED", None, "caller is not the configured person")
    cur = current or claims.read(cfg, task, state_dir=state_dir)
    if cur.status != "HELD":
        return claims.ClaimResult(cur.status, None, cur.detail)
    res = claims.release(cfg, task, actor, expected_oid=cur.oid, state_dir=state_dir, override_person=cfg.user.id)
    if res.status == "RELEASED":
        with local_claims(state_dir) as local:
            local.pop(task, None)
        record(state_dir, "release", task, actor, {"reason": reason, "override": True,
                                                  "released_owner": {"session_id": cur.owner.get("session_id"),
                                                                     "alias": cur.owner.get("alias", "")}})
    return res


def auto_claims(cfg, state_dir, touched: list[tuple[str, dict]]) -> list[str]:
    """For spooled touch events: claim free tasks; adopt and renew claims the touching session owns."""
    notes = []
    if not claims.ensure_probe(cfg, state_dir).ok:
        return ["claims disabled: probe failed"]
    interval = timedelta(minutes=cfg.claims.heartbeat_interval_minutes)
    for task, actor in touched:
        actor = dict(actor, person=actor.get("person") or cfg.user.id)
        with local_claims(state_dir) as local:
            mine = local.get(task)
        if not (mine and mine.get("session_id") == actor.get("session_id")):
            cur = claims.read(cfg, task, state_dir=state_dir)
            if cur.status == "FREE":
                res = claims.acquire(cfg, task, actor, state_dir=state_dir)
                if res.status == "ACQUIRED":
                    with local_claims(state_dir) as local:
                        local[task] = {"oid": res.oid, "session_id": actor["session_id"], "renewed": _now().isoformat()}
                    record(state_dir, "claim", task, actor, {"oid": res.oid, "auto": True})
                    notes.append(f"{task}: auto-claimed by {actor.get('alias')}")
                else:
                    notes.append(f"{task}: auto-claim {res.status} {res.detail}")
                continue
            if cur.status == "HELD" and cur.owner.get("session_id") == actor["session_id"]:
                renewed = claims._aware(cur.owner.get("renewed_at")) or _now()
                mine = {"oid": cur.oid, "session_id": actor["session_id"], "renewed": renewed.isoformat()}
                with local_claims(state_dir) as local:
                    local[task] = mine            # adopt an assigned / other-host claim we own
            else:
                continue
        renewed = datetime.fromisoformat(mine["renewed"])
        if _now() - renewed >= interval:
            res = claims.heartbeat(cfg, task, actor, expected_oid=mine["oid"], state_dir=state_dir)
            with local_claims(state_dir) as local:
                if res.status == "ACQUIRED":
                    local[task] = {"oid": res.oid, "session_id": actor["session_id"], "renewed": _now().isoformat()}
                else:
                    local.pop(task, None)
            if res.status == "ACQUIRED":
                record(state_dir, "renew", task, actor, {"oid": res.oid})
            else:
                notes.append(f"{task}: lost claim ({res.status} {res.detail})")
    return notes

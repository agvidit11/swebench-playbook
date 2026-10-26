"""Gathering: run sources (cache-first), a time-bounded ledger sync, read events, project."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

from . import events, sync as sync_mod
from .model import SourceHealth
from .projection import project
from .sources.codimango import CodimangoSource
from .model import Observation
from .sources.claimrefs import ClaimRefSource
from .sources.gitsrc import GitSource, changed_files

GIT_STAMP = "git-last-fetch"


def _usage_roots(cfg, cdir: Path) -> dict:
    """Keep default/no-config test snapshots isolated from real native logs."""
    if str(getattr(cfg, "path", "")) != "/nonexistent":
        return {}
    root = Path(cdir) / "usage-fixtures"
    return {"claude_root": root / "claude", "codex_root": root / "codex", "muse_db": root / "muse.db"}


@dataclass
class Snapshot:
    views: list
    observations: list
    events: list
    health: dict
    findings: list = field(default_factory=list)
    sync_state: object = None
    now: datetime = None
    sessions: list = field(default_factory=list)
    session_diagnostics: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)


def cache_dir() -> Path:
    d = Path(os.environ.get("WORKBOARD_CACHE", "~/.cache/workboard")).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


def ledger_event_files(cfg) -> list[Path]:
    d = Path(cfg.ledger.path).expanduser() / "events"
    return sorted(d.glob("*.jsonl")) if d.is_dir() else []


def pending_spool_events(state_dir: Path, host_id: str) -> list[dict]:
    """Unsynced local events, stamped provisionally so the board shows them before they are pushed."""
    out = []
    for i, raw in enumerate(sync_mod._spool_lines(state_dir), 1):
        try:
            ev = json.loads(raw)
        except ValueError:
            continue
        if isinstance(ev, dict):
            stamped = events.stamp(ev, host_id, 10**9 + i)
            if events.validate_committed(stamped) is None:
                stamped["_pending_local"] = True
                out.append(stamped)
    return out


def _enrich_changed(cfg, cm_obs, git_obs, now) -> list:
    """For tasks whose head differs from the validated commit, which files changed (one git diff each)."""
    validated = {o.entity_id: o.fields.get("codimango.commit_sha") for o in cm_obs}
    open_ = {o.entity_id for o in cm_obs if o.fields.get("codimango.status") not in ("accepted", "used_in_training", "archived")}
    out = []
    for o in git_obs:
        task, head = o.entity_id, o.fields.get("git.task_head")
        old = validated.get(task)
        if task in open_ and head and old and head != old:
            files = changed_files(cfg, o.fields.get("git.repo"), task, old, head)
            if files is not None:
                out.append(Observation("git", task, now, {"git.changed_since_validated": files},
                                       {"git.changed_since_validated": "derived"}))
    return out


def refresh_claims_cache(cfg, state_dir, cres=None) -> None:
    """Write the claim cache the pre-tool hook reads (only from a healthy claim-ref fetch)."""
    from .hooks import save_claims_cache
    if not (cfg.ledger.remote and cfg.claims.mode == "atomic"):
        return
    cres = cres or ClaimRefSource(cfg, state_dir=state_dir).fetch()
    if not cres.health.ok:
        return
    save_claims_cache(state_dir, {
        "fetched_at": cres.health.observed_at.isoformat(),
        "claims": {o.entity_id: {"session_id": o.fields.get("claims.session_id"), "alias": o.fields.get("claims.alias"),
                                 "renewed_at": o.fields.get("claims.renewed_at")} for o in cres.observations}})


class _SkipUsage(Exception):
    pass


def gather(cfg, *, refresh: bool = False, do_sync: bool = True, sync_timeout: float = 8, light: bool = False) -> Snapshot:
    """light=True (CLI reads and check-ins): skip token accounting and run linkage, which only the dashboard needs."""
    now = datetime.now(timezone.utc)
    cdir = cache_dir()
    health, findings, obs = {}, [], []

    cm = CodimangoSource(cfg, cache_dir=cdir).fetch(max_age_seconds=0 if refresh else cfg.codimango.cache_ttl_seconds)
    health["codimango"], findings = cm.health, list(cm.findings)
    obs += cm.observations

    if cfg.repositories:
        stamp = cdir / GIT_STAMP
        fresh = stamp.exists() and time.time() - stamp.stat().st_mtime < cfg.codimango.cache_ttl_seconds
        gres = GitSource(cfg, fetch_remote=refresh or not fresh).fetch()
        if gres.health.ok and (refresh or not fresh):
            stamp.touch()
        health["git"] = gres.health
        findings += gres.findings
        obs += gres.observations + _enrich_changed(cfg, cm.observations, gres.observations, now)

    state_dir = sync_mod.default_state_dir()
    sync_state = None
    if cfg.ledger.remote:
        sync_state = sync_mod.sync(cfg, state_dir=state_dir, timeout_seconds=sync_timeout) if do_sync \
            else sync_mod.load_state(state_dir)
    claims_healthy = False
    if cfg.ledger.remote and cfg.claims.mode == "atomic":
        cres = ClaimRefSource(cfg, state_dir=state_dir).fetch()
        health["claims"] = cres.health
        findings += cres.findings
        claim_obs = list(cres.observations)                # includes slugs claimed before they exist anywhere else
        obs += claim_obs
        claims_healthy = cres.health.ok
        refresh_claims_cache(cfg, state_dir, cres)
    evs, ev_findings = events.read_events(ledger_event_files(cfg))
    known = {e["event_id"] for e in evs}
    evs += [e for e in pending_spool_events(state_dir, sync_mod.safe_host(sync_mod.host_id_for(cfg)))
            if e["event_id"] not in known]
    findings += ev_findings
    views = project(obs, evs, cfg, now, claims_healthy=claims_healthy)
    native_sessions, session_diagnostics, usage_summary = [], [], {}
    try:
        from . import session_inventory
        host_id = sync_mod.safe_host(sync_mod.host_id_for(cfg))
        native_sessions, session_diagnostics = session_inventory.discover(
            cfg, evs, host_id, now=now.timestamp(), link_runs=not light)
        try:
            if light:
                raise _SkipUsage()
            from . import usage
            usage_summary = usage.collect(cfg, evs, host_id, sessions=native_sessions, cache_dir=cdir,
                                          now=now.timestamp(), byte_budget=16 * 1024 * 1024,
                                          time_budget_s=min(1.5, max(0.2, sync_timeout / 4)),
                                          **_usage_roots(cfg, cdir))
            usage.decorate_sessions(native_sessions, usage_summary)
            usage.apply_task_usage(views, usage_summary, cfg)
            usage.apply_advice(native_sessions, views, now=now.timestamp())
            cycle = usage_summary.get("collector") or {}
            health["usage"] = SourceHealth("usage", not bool(cycle.get("errors")), now, 120,
                                           f"{cycle.get('bytes_read', 0)} bytes; "
                                           f"{len(usage_summary.get('sessions', {}))} indexed session(s)" +
                                           (f"; {', '.join(cycle['errors'])}" if cycle.get("errors") else ""))
        except _SkipUsage:
            pass                                       # light read: no token accounting
        except Exception as exc:
            session_diagnostics.append({"host": host_id, "classification": "source-error",
                                        "reason": f"usage collector: {exc.__class__.__name__}"})
            health["usage"] = SourceHealth("usage", False, now, 120,
                                           f"usage collector: {exc.__class__.__name__}")
        from . import host_snapshots
        host_snapshots.cache_local(state_dir, host_id, [s for s in native_sessions if not s.get("remote")],
                                   [d for d in session_diagnostics if d.get("host") == host_id], at=now.isoformat())
        local_count = sum(not s.get("remote") and not s.get("is_summary") for s in native_sessions)
        peer_count = sum(bool(s.get("remote")) and not s.get("is_summary") for s in native_sessions)
        health["sessions"] = SourceHealth("sessions", True, now, 30,
                                          f"{local_count} local, {peer_count} peer; "
                                          f"{len(session_diagnostics)} diagnostic")
    except Exception as exc:
        health["sessions"] = SourceHealth("sessions", False, now, 30,
                                          f"session discovery: {exc.__class__.__name__}")
    return Snapshot(views, obs, evs, health, findings, sync_state, now,
                    native_sessions, session_diagnostics, usage_summary)


def refresh_sessions(cfg, snap: Snapshot) -> Snapshot:
    """Cheap Team refresh: ledger/spool + native session inputs, no Codimango or Git work."""
    now = datetime.now(timezone.utc)
    state_dir = sync_mod.default_state_dir()
    evs, ev_findings = events.read_events(ledger_event_files(cfg))
    known = {e["event_id"] for e in evs}
    evs += [e for e in pending_spool_events(state_dir, sync_mod.safe_host(sync_mod.host_id_for(cfg)))
            if e["event_id"] not in known]
    sessions, diagnostics, usage_summary = [], [], getattr(snap, "usage", {})
    try:
        from . import session_inventory
        sessions, diagnostics = session_inventory.discover(
            cfg, evs, sync_mod.safe_host(sync_mod.host_id_for(cfg)), now=now.timestamp())
        try:
            from . import usage
            usage_summary = usage.collect(cfg, evs, sync_mod.safe_host(sync_mod.host_id_for(cfg)),
                                          sessions=sessions, cache_dir=cache_dir(), now=now.timestamp(),
                                          byte_budget=8 * 1024 * 1024, time_budget_s=0.75,
                                          **_usage_roots(cfg, cache_dir()))
            usage.decorate_sessions(sessions, usage_summary)
            usage.apply_advice(sessions, snap.views, now=now.timestamp())
        except Exception as exc:
            diagnostics.append({"host": sync_mod.safe_host(sync_mod.host_id_for(cfg)),
                                "classification": "source-error",
                                "reason": f"usage collector: {exc.__class__.__name__}"})
    except Exception as exc:
        diagnostics = [{"host": sync_mod.safe_host(sync_mod.host_id_for(cfg)),
                        "classification": "source-error",
                        "reason": f"session discovery: {exc.__class__.__name__}"}]
    return replace(snap, events=evs, sessions=sessions, session_diagnostics=diagnostics,
                   findings=list(snap.findings) + ev_findings, now=now, usage=usage_summary)

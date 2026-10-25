"""Compose native sessions, child runs, focus, and bounded command-center summaries."""
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from pathlib import Path

from .ownership import reduce_focus
from .sources import agent_runs, claude_sessions


def _seconds(value) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = float(value)
        return value / 1000 if value > 10_000_000_000 else value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _hooks_installed(settings: Path) -> bool:
    try:
        data = json.loads(settings.read_text())
    except (OSError, ValueError, TypeError):
        return False
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return False
    commands = []
    for entries in hooks.values():
        for entry in entries if isinstance(entries, list) else []:
            for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    commands.append(hook["command"])
    return any("board" in command and "hook" in command for command in commands)


def _restart_state(session: dict, evs: list[dict], *, now: float, hooks_installed: bool) -> dict:
    native = session.get("native_id")
    evidence = []
    for e in evs:
        if e.get("source") != "hook" or (e.get("actor") or {}).get("session_id") != native:
            continue
        at = _seconds(e.get("occurred_at"))
        if at is not None and 0 <= now - at <= 7 * 86400:
            evidence.append(at)
    if evidence:
        return {"state": "loaded", "needed": False, "reason": "hook event observed in the last 7 days",
                "evidence_at": datetime.fromtimestamp(max(evidence), timezone.utc).isoformat(), "command": None}
    status = str(session.get("status") or "unknown").lower()
    status_at = _seconds(session.get("status_since"))
    recent = status_at is not None and 0 <= now - status_at <= 2 * 3600
    active = status in ("busy", "waiting", "waiting-for-permission", "shell", "active", "working")
    if hooks_installed and (active or (recent and status not in ("idle", "unknown"))):
        return {"state": "probably-missing", "needed": True,
                "reason": "probably missing hooks — resume to load them",
                "command": f"claude --resume {native}"}
    return {"state": "unknown", "needed": False,
            "reason": "hook state unknown (idle or no recent hook evidence)", "command": None}


def _task_from_cwd(cwd: str | None, cfg) -> str | None:
    if not cwd:
        return None
    p = Path(cwd)
    for repo in cfg.repositories:
        try:
            rel = p.relative_to(Path(repo.path).expanduser())
        except ValueError:
            continue
        return rel.parts[0] if rel.parts else None
    return None


def discover(cfg, evs: list[dict], host_id: str, *, now: float | None = None,
             claude_root: Path | None = None, codex_root: Path | None = None,
             muse_db: Path | None = None, proc_root: Path = Path("/proc"), pid_domain: str | None = None,
             claude_projects_root: Path | None = None) -> tuple[list[dict], list[dict]]:
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    settings = Path(os.environ.get("CLAUDE_SETTINGS", "~/.claude/settings.json")).expanduser()
    diagnostics = []
    try:
        parents, found = claude_sessions.discover(
            host_id, root=claude_root, proc_root=proc_root, pid_domain=pid_domain, now=now)
        diagnostics.extend(found)
    except Exception as exc:
        parents = []
        diagnostics.append({"classification": "source-error", "reason": f"Claude registry: {exc.__class__.__name__}"})
    for item in diagnostics:
        item["host"] = host_id
    installed = _hooks_installed(settings)
    for session in parents:
        session["restart"] = _restart_state(session, evs, now=now, hooks_installed=installed)
        session["cwd_task"] = _task_from_cwd(session.get("cwd"), cfg)
        session["focus"] = reduce_focus(session, evs, now=now)
        session["tasks"] = session["focus"]["tasks"]
        session["tokens"] = {"total": None, "last_hour": None, "reason": "token indexing arrives in increment 3"}
        if session["classification"] != "local-live":
            advice = ("watch", session["liveness_reason"])
        elif session["focus"]["tasks"]:
            advice = ("keep", "live session has current task focus")
        elif session["restart"]["needed"]:
            advice = ("watch", session["restart"]["reason"])
        else:
            advice = ("keep", "live and reachable through the courier")
        session["advice"] = {"state": advice[0], "reason": advice[1]}

    try:
        codex = agent_runs.discover_codex(cfg, host_id, root=codex_root, now=now) if codex_root is not False else []
    except Exception as exc:
        codex = []
        diagnostics.append({"host": host_id, "classification": "source-error",
                            "reason": f"Codex runs: {exc.__class__.__name__}"})
    try:
        muse = agent_runs.discover_muse(cfg, host_id, db_path=muse_db, now=now) if muse_db is not False else []
    except Exception as exc:
        muse = []
        diagnostics.append({"host": host_id, "classification": "source-error",
                            "reason": f"Muse runs: {exc.__class__.__name__}"})
    try:
        live_codex = agent_runs.live_codex_ids(proc_root)
    except Exception as exc:
        live_codex = set()
        diagnostics.append({"host": host_id, "classification": "source-error",
                            "reason": f"Codex liveness: {exc.__class__.__name__}"})
    # A live process proves liveness, but ``source=exec`` is still a child job,
    # never a TUI.  Only interactive Codex sessions may be top-level rows.
    interactive = [run for run in codex if run.get("native_id") in live_codex and run.get("source") != "exec"]
    codex = [run for run in codex if run not in interactive]
    for session in interactive:
        session.update(live=True, classification="local-live", liveness_reason="same-uid process carries this Codex id")
        session["status"] = "busy" if session.get("status") == "historical" else session.get("status")
        session["transport"] = {"available": False, "kind": "unavailable",
                                "reason": "direct Codex TUI messaging is unavailable"}
        session["restart"] = {"state": "not-applicable", "needed": False,
                              "reason": "Codex process is live", "command": None}
        session["focus"] = reduce_focus(session, evs, now=now)
        session["tasks"] = session["focus"]["tasks"]
        session["tokens"] = {"total": None, "last_hour": None, "reason": "token indexing arrives in increment 3"}
        session["advice"] = {"state": "keep", "reason": "live Codex interactive session"}
        session["child_runs"] = []
        parents.append(session)
    runs = codex + muse
    try:
        launches = agent_runs.transcript_launches(parents, root=claude_projects_root, now=now)
    except Exception as exc:
        launches = []
        diagnostics.append({"host": host_id, "classification": "source-error",
                            "reason": f"launch evidence: {exc.__class__.__name__}"})
    try:
        agent_runs.link_parents(runs, parents, evs, now=now, launches=launches)
    except Exception as exc:
        diagnostics.append({"host": host_id, "classification": "source-error",
                            "reason": f"parent linkage: {exc.__class__.__name__}"})

    for session in parents:
        children = session.get("child_runs") or []
        recent = [r for r in children if 0 <= now - (_seconds(r.get("started_at")) or 0) <= 24 * 3600]
        session["older_child_run_count"] = len(children) - len(recent)
        session["child_runs"] = recent
    unmatched = [run for run in runs if not run.get("parent_session_key")]
    recent_unmatched = [r for r in unmatched if 0 <= now - (_seconds(r.get("started_at")) or 0) <= 24 * 3600]
    older_unmatched = len(unmatched) - len(recent_unmatched)
    if recent_unmatched or older_unmatched:
        tasks = sorted({r.get("cwd_task") for r in recent_unmatched if r.get("cwd_task")})
        parents.append({
            "session_key": f"unlinked:{host_id}", "native_id": f"unlinked:{host_id}",
            "kind": "unlinked", "kind_icon": "❔", "host": host_id, "name": f"unlinked runs ({len(recent_unmatched)})",
            "status": "unknown", "status_since": None, "live": False, "classification": "summary",
            "liveness_reason": "runs without a proven live interactive parent", "is_summary": True,
            "recent_run_count": len(recent_unmatched), "older_run_count": older_unmatched,
            "focus": {"state": "ambiguous" if len(tasks) > 1 else "single" if tasks else "none",
                      "primary": tasks[0] if len(tasks) == 1 else None, "tasks": tasks,
                      "confidence": "unknown", "evidence": ["unlinked run cwd"] if tasks else []},
            "tasks": tasks, "tokens": {"total": None, "last_hour": None, "reason": "—"},
            "transport": {"available": False, "kind": "unavailable", "reason": "no parent route"},
            "restart": {"state": "not-applicable", "needed": False, "reason": "not an interactive session", "command": None},
            "advice": {"state": "watch", "reason": "inspect only if a recent run needs attribution"},
            "child_runs": recent_unmatched,
        })

    for session in parents:
        native = session["native_id"]
        identities = {native, session.get("session_key")}
        if session.get("kind") == "codex" and isinstance(native, str):
            identities.add("codex:" + native[-12:])
        reports = [e for e in evs if (e.get("actor") or {}).get("session_id") in identities
                   and e.get("type") in ("checkin", "presence", "check", "review")]
        requests = [e for e in evs if e.get("type") == "msg" and
                    ((e.get("payload") or {}).get("to") in (f"session:{native}", f"session:{session['session_key']}"))]
        report = max(reports, key=lambda e: _seconds(e.get("occurred_at")) or 0) if reports else None
        request = max(requests, key=lambda e: _seconds(e.get("occurred_at")) or 0) if requests else None
        session["last_report"] = ({"at": report["occurred_at"], "kind": report["type"],
                                   "task": (report.get("entity") or {}).get("id")}
                                  if report else None)
        session["last_request"] = ({"at": request["occurred_at"],
                                    "message_id": request["event_id"],
                                    "task": (request.get("entity") or {}).get("id")}
                                   if request else None)
    try:
        from . import host_snapshots
        peers, peer_diagnostics = host_snapshots.load_peers(
            Path(cfg.ledger.path).expanduser(), host_id, now=now)
        parents.extend(peers)
        diagnostics.extend(peer_diagnostics)
    except Exception as exc:
        diagnostics.append({"host": host_id, "classification": "source-error",
                            "reason": f"peer snapshots: {exc.__class__.__name__}"})
    return parents, diagnostics

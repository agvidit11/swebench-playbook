"""Pure reducers for focus and the three independent ownership axes."""
from __future__ import annotations

from datetime import datetime, timezone


def _ts(value) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def reduce_focus(session: dict, evs: list[dict], *, now: float | None = None) -> dict:
    """Reduce real-shaped ledger activity into a session's current/recent task focus.

    Explicit ``board here`` evidence wins, followed by task actions, cwd, then
    transcript path hits.  A workday window is intentional: an idle session should
    still say what it worked on today instead of becoming an unexplained ``none``.
    """
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    native = session.get("native_id")
    identities = {native, session.get("session_key")}
    if session.get("kind") == "codex" and isinstance(native, str):
        identities.add("codex:" + native[-12:])       # presence scanner's bounded id
    identities.discard(None)
    candidates: dict[str, list[tuple[int, float, str]]] = {}
    latest_checkin = None
    for e in evs:
        if (e.get("actor") or {}).get("session_id") in identities and e.get("type") == "checkin":
            at = _ts(e.get("occurred_at"))
            if at is not None and (latest_checkin is None or at > latest_checkin[0]):
                latest_checkin = (at, e)
    idle_since = latest_checkin[0] if latest_checkin and \
        (latest_checkin[1].get("payload") or {}).get("status") == "idle" else None
    for e in evs:
        if (e.get("actor") or {}).get("session_id") not in identities:
            continue
        at = _ts(e.get("occurred_at"))
        if at is None or not 0 <= now - at <= 24 * 3600:
            continue
        if idle_since is not None and at <= idle_since:
            continue                                      # `board here --idle` clears earlier focus
        task = (e.get("entity") or {}).get("id")
        if e.get("type") == "checkin" and latest_checkin and e is latest_checkin[1] and \
                (e.get("payload") or {}).get("status") != "idle":
            for t in (e.get("payload") or {}).get("tasks") or []:
                candidates.setdefault(t, []).append((4, at, "explicit here"))
        elif e.get("type") == "presence" and (e.get("payload") or {}).get("checkin") and task:
            candidates.setdefault(task, []).append((4, at, "explicit here"))
        elif e.get("type") in ("touch", "claim", "renew", "steal", "assign", "check", "review", "build_action") and task:
            candidates.setdefault(task, []).append((3, at, "ledger activity"))
        elif e.get("type") == "presence" and task:
            seen = _ts((e.get("payload") or {}).get("last_seen")) or at
            if 0 <= now - seen <= 24 * 3600:
                candidates.setdefault(task, []).append((1, seen, "transcript path"))
    if session.get("cwd_task"):
        candidates.setdefault(session["cwd_task"], []).append((2, now, "cwd"))
    if not candidates:
        return {"state": "none", "primary": None, "tasks": [], "confidence": "unknown", "evidence": []}
    best = max(rank for values in candidates.values() for rank, _, _ in values)
    # At the winning evidence rank, keep the latest task(s).  This prevents an
    # unrelated morning claim from competing with a tool-path hit from minutes ago.
    newest = max(at for values in candidates.values() for rank, at, _ in values if rank == best)
    tasks = sorted(t for t, values in candidates.items()
                   if any(rank == best and newest - at <= 5 for rank, at, _ in values))
    evidence = sorted({kind for t in tasks for rank, _, kind in candidates[t] if rank == best})
    confidence = "high" if best >= 3 else "medium" if best == 2 else "low"
    return {"state": "single" if len(tasks) == 1 else "ambiguous", "primary": tasks[0] if len(tasks) == 1 else None,
            "tasks": tasks, "confidence": confidence, "evidence": evidence}


def reduce_ownership(assignment: dict, activity: dict, pipeline: dict, last_push: dict, *, done: bool,
                     actionable: bool, sources_fresh: bool, now: float | None = None,
                     activity_window_s: int = 2 * 3600, push_window_s: int = 72 * 3600) -> dict:
    """Reduce independent axes to exactly one scan-friendly state.

    Crucial invariant: available/free is emitted only after every blocking axis and
    the recent-remote-change window are clear.
    """
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    last_activity = _ts(activity.get("last_at"))
    active = activity.get("state") == "active" and last_activity is not None and 0 <= now - last_activity <= activity_window_s
    claimed = assignment.get("state") in ("claimed", "legacy", "conflict")
    piped = pipeline.get("state") not in (None, "none", "idle", "done")
    push_at = _ts(last_push.get("at"))
    recent_push = push_at is not None and 0 <= now - push_at <= push_window_s
    if done:
        state, reason = "done", "task lifecycle is complete"
    elif assignment.get("state") == "conflict":
        state, reason = "conflict", "more than one assignment is live"
    elif active:
        state, reason = "actively_working", activity.get("reason") or "current task activity"
    elif piped:
        state, reason = "in_pipeline", pipeline.get("reason") or pipeline.get("state")
    elif claimed:
        state, reason = "assigned_idle", assignment.get("reason") or "assigned with no recent activity"
    elif recent_push:
        state, reason = "worked_recently", last_push.get("reason") or "remote change within 72 hours"
    elif actionable and sources_fresh:
        state, reason = "available", "no assignment, recent activity, pipeline, or recent remote change"
    else:
        state, reason = "never_seen", "insufficient fresh evidence to call this task free"
    return {"assignment": assignment, "activity": activity, "pipeline": pipeline, "last_push": last_push,
            "availability": {"state": state, "reason": reason, "free": state == "available"}}

"""Who recorded a presubmit or agent review: the session that builds the task ("author") or a fresh agent without
the build context ("independent"). A task needs one of each — a clean presubmit and a "ready" review from both —
on its current commit before it is submitted.

Role evidence, in order:
1. explicit `role` in the payload (`--role author|independent` on `board check record|run|import` / `board review add`);
2. independent-review markers in the text ("§5d", "independent");
3. the recording session owns or claimed the task (claim, renew, steal, build_action events) -> author;
4. otherwise independent.

`gates()` is the one reducer used by the projection (Next / R-label), the dashboard ticks, the card and Next steps,
so they cannot disagree.
"""
from __future__ import annotations

import re

INDEPENDENT_MARK = re.compile(r"^\s*(§5d\b|\[independent\]|independent:)", re.I)

ROLES = ("author", "independent")
AUTHOR_EVENTS = {"claim", "renew", "steal", "build_action"}


def role_of(event: dict, task_events: list[dict], owner_session: str | None = None) -> str:
    p = event.get("payload") or {}
    if p.get("role") in ROLES:
        return p["role"]
    if INDEPENDENT_MARK.match(p.get("summary") or "") or INDEPENDENT_MARK.match(p.get("note") or ""):
        return "independent"
    sid = (event.get("actor") or {}).get("session_id")
    if sid and owner_session and sid == owner_session:
        return "author"
    at = event.get("occurred_at") or ""
    if sid and any(e["type"] in AUTHOR_EVENTS and (e.get("actor") or {}).get("session_id") == sid
                   and (e.get("occurred_at") or "") <= at for e in task_events):   # ownership at the time, not later
        return "author"
    return "independent"


def _older_run(payload: dict, generation: str | None) -> bool:
    """Recorded against an earlier server validation run of the same commit (codimango revalidated since)."""
    rec = payload.get("validation_generation")
    return bool(generation and rec and str(rec) != str(generation))


def _provisional(payload: dict) -> bool:
    return str(payload.get("validation_status") or "").lower() in ("pending", "running", "in_progress", "queued")


def _chrono(task_events: list[dict]) -> list[dict]:
    return sorted(task_events, key=lambda e: (e.get("occurred_at") or "", e.get("host_id") or "", e.get("seq") or 0))


def _as_set(current) -> set:
    if isinstance(current, (set, list, tuple)):
        return {c for c in current if c}
    return {current} if current else set()


def gates(task_events: list[dict], current, owner_session: str | None = None,
          generation: str | None = None) -> dict:
    """{author|independent: {check: {...state}, review: {...state}}}; state is ok | bad | old | none.

    check: the role's latest presubmit (chronological across servers). ok = clean on a current commit, bad = failures
    on a current commit, old = latest result is for an earlier commit.
    review: latest verdict per (session, commit); a role is ok when a session in it said ready on a current commit and
    no session in it asked for changes there; bad when one asked for changes. The independent slot never counts the
    session that already fills the author slot.
    """
    cur = _as_set(current)
    evs = _chrono(task_events)
    out = {r: {"check": {"state": "none"}, "review": {"state": "none"}} for r in ROLES}
    checks = [(e, role_of(e, evs, owner_session)) for e in evs if e["type"] == "check"]
    author_sessions = {(e.get("actor") or {}).get("session_id") for e, r in checks if r == "author"}
    for e, role in checks:
        if role == "independent" and (e.get("actor") or {}).get("session_id") in author_sessions:
            continue                                   # the building session cannot also be the independent check
        p = e.get("payload") or {}
        here = e.get("commit") in cur and not _older_run(p, generation)
        out[role]["check"] = dict(p, at=e.get("occurred_at"), current=here, commit=(e.get("commit") or "")[:8],
                                  who=(e.get("actor") or {}).get("alias", ""),
                                  session=(e.get("actor") or {}).get("session_id"),
                                  state="old" if not here else "bad" if p.get("fail") else "ok",
                                  older_run=e.get("commit") in cur and _older_run(p, generation),
                                  provisional=here and _provisional(p))
    latest = {}
    for e in evs:
        if e["type"] == "review":
            latest[((e.get("actor") or {}).get("session_id"), e.get("commit"))] = e
    by_role = {r: [] for r in ROLES}
    for e in latest.values():
        by_role[role_of(e, evs, owner_session)].append(e)
    author_ready = {(e.get("actor") or {}).get("session_id") for e in by_role["author"]
                    if e.get("commit") in cur and (e.get("payload") or {}).get("verdict") == "ready"}
    for role in ROLES:
        rs = sorted(by_role[role], key=lambda e: e.get("occurred_at") or "")
        here = [e for e in rs if e.get("commit") in cur and not _older_run(e.get("payload") or {}, generation)]
        ready = [e for e in here if (e.get("payload") or {}).get("verdict") == "ready"
                 and not (role == "independent" and (e.get("actor") or {}).get("session_id") in author_ready)]
        changes = [e for e in here if (e.get("payload") or {}).get("verdict") == "changes"]
        pick = (changes or ready or here or rs or [None])[-1]
        if pick is None:
            continue
        state = "bad" if changes else "ok" if ready else "old" if not here else "none"
        p = pick.get("payload") or {}
        out[role]["review"] = {"state": state, "verdict": p.get("verdict"), "note": p.get("note", ""),
                               "confidence": p.get("confidence"),
                               "at": pick.get("occurred_at"), "current": pick.get("commit") in cur,
                               "who": (pick.get("actor") or {}).get("alias", ""),
                               "session": (pick.get("actor") or {}).get("session_id")}
    return out

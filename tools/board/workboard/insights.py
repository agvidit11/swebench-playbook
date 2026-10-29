"""Short, decision-ready summaries shared by the web page and the terminal: validation issues, review status,
sync status, next steps with rough ETAs, and who should take a task. Deterministic rules, no model calls."""
from __future__ import annotations

import re
from datetime import datetime, timezone

CHECK_NAMES = [  # (keyword in codimango label, short name, default fix)
    ("reward_hack", "reward-hack detector", "make sure tests can't be passed without the real fix"),
    ("test_patch", "test-patch", "fix the test patch so it applies and runs (see harbor output)"),
    ("deep", "deep review", "address the deep-review findings"),
    ("structur", "structure", "fix the task layout codimango flags"),
    ("oracle", "oracle", "fix the reference solution so it passes 3/3"),
    ("balance", "calibration", "rebalance difficulty (see detail)"),
    ("solvab", "calibration", "rebalance difficulty (see detail)"),
    ("calibrat", "calibration", "rebalance difficulty (see detail)"),
    ("agentic", "agentic review", "address the agentic reviewer's findings"),
    ("provenance", "provenance", "have Codex re-author the flagged files"),
    ("contamin", "contamination", "re-source or prove novelty"),
    ("tbr", "TBR", "re-run TBR at this commit"),
    ("build", "build", "fix the Docker build"),
    ("evalgt", "eval GT", "fix the eval ground truth"),
    ("ai ", "AI check", "see codimango"),
]
INFRA = re.compile(r"infrastructure error|not a task defect|PROCESSED_FAILED|job did not succeed|\d+ errored|"
                   r"without a usable result|click Revalidate", re.I)
DEPENDENT = re.compile(r"not run because|skipped[:\s].*(gate|failed)|because .* (failed|errored)", re.I)
ACTION = re.compile(r"ACTION REQUIRED|SUSPECT|review recommended|manual review", re.I)
CLEAN = re.compile(r"\bCLEAN\b|not third-party|\bpass(ed)?\b(?!.*fail)", re.I)


def short_check(label: str) -> tuple[str, str]:
    low = (label or "").lower()
    for key, name, fix in CHECK_NAMES:
        if key in low:
            return name, fix
    return (label or "check").split("::")[-1].split(" (")[0][:28].lower(), "see codimango"


def short_detail(detail: str) -> tuple[str, str | None]:
    """(few-word reason, specific fix or None)."""
    d = (detail or "").strip()
    if INFRA.search(d):
        return "infra error on codimango's side (not your task)", "codimango task rerun {task} (free); retry if it repeats"
    m = re.search(r'"(\d+)_[^"]*"\s+too\s+(hard|easy)', d)
    if m:
        step, how = m.group(1), m.group(2)
        if how == "hard":
            return f"step {step} too hard", f"loosen step {step} or state the hidden rule"
        return f"step {step} too easy", f"make step {step} harder (more unstated work, less spec)"
    if re.search(r"\bBAD_GRADING_(WRONG|WEAK)\b", d):
        kind = re.search(r"BAD_GRADING_(WRONG|WEAK)", d).group(1).lower()
        return f"grading {kind} (agentic verdict)", None
    if re.search(r"suspect", d, re.I) and "provenance" in d.lower():
        return "provenance SUSPECT — review recommended", "check the flagged files; re-author with Codex if needed"
    if re.search(r"third-party", d, re.I) and not re.search(r"not third-party|CLEAN", d, re.I):
        return "3rd-party authorship flagged", None
    if re.search(r"pending|waiting|still running", d, re.I):
        return "still running", None
    first = re.split(r"[;(—]| - ", d)[0].strip()
    return (first[:60] + ("…" if len(first) > 60 else "")) if first else "failed", None


def validation_summary(items: list[dict], tbr_status: str | None = None) -> dict:
    """Problems only. Dependent checks (skipped because another failed) are folded into their root cause; passed
    checks stay hidden unless their detail asks for reviewer action; canonical passes are never warnings."""
    issues, skipped, info = [], [], []
    for it in items or []:
        st, detail = it.get("status", ""), it.get("detail", "") or ""
        name, fix = short_check(it.get("name", ""))
        if DEPENDENT.search(detail):
            skipped.append(name)
            continue
        if st in ("passed", "pass", "ok"):
            if ACTION.search(detail):
                why = "provenance SUSPECT — review recommended" if "suspect" in detail.lower() else "reviewer action required"
                issues.append({"check": name, "why": why, "fix": "verify before submit (see codimango)", "severity": "warn"})
            elif re.search(r"(never ran|errored|did not run|has not run|stopped waiting|unavailable|without a usable result)", detail, re.I):
                info.append({"check": name, "why": short_detail(detail)[0]})
            continue
        if st == "warn" and CLEAN.search(detail) and not ACTION.search(detail):
            continue                                      # e.g. "Canonical TBR review pass", "Provenance CLEAN"
        why, specific = short_detail(detail)
        if why.startswith("still running") and st in ("pending", "running", ""):
            sev = "pending"
        else:
            sev = "fail" if st in ("failed", "error") else "warn" if st == "warn" else "pending"
        if why.startswith("infra error"):
            sev = "warn"                                   # rerun, not a task fix
        if name != "calibration" and re.match(r"step \d+ too (hard|easy)$", why):
            why, specific = short_detail(re.sub(r'"\d+_[^"]*"\s+too\s+(hard|easy)', "", detail))
            specific = None
        issues.append({"check": name, "why": why, "fix": specific or fix, "severity": sev})
    if tbr_status == "fail" and not any(i["check"] == "TBR" for i in issues):
        issues.append({"check": "TBR", "why": "TBR failed", "fix": "re-run TBR at this commit", "severity": "warn"})
    order = {"fail": 0, "warn": 1, "pending": 2}
    issues.sort(key=lambda i: order[i["severity"]])
    total = len(items or [])
    return {"issues": issues, "passed": total - len(issues) - len(skipped), "total": total,
            "skipped": skipped, "info": info}


def _h(hours):
    if hours is None:
        return None
    if hours < 1:
        return f"~{max(5, int(hours * 60) // 5 * 5)}m"
    if hours < 48:
        return f"~{round(hours)}h"
    return f"~{hours / 24:.1f}d"


def next_steps(t: dict, flow: dict) -> list[dict]:
    """Ordered steps [{do, eta}] for a task dict (projection fields + extra). Exactly one branch per Next action;
    unresolved validation warnings come before any submit/resubmit ladder."""
    n = t.get("next") or ""
    steps = []
    vs = t.get("vsum") or {"issues": []}
    fails = [i for i in vs["issues"] if i["severity"] == "fail"]
    infra = [i for i in vs["issues"] if i["why"].startswith("infra error")]
    warns = [i for i in vs["issues"] if i["severity"] == "warn" and i not in infra]
    age_h = (t.get("state_age_s") or 0) / 3600
    wait_p50 = flow.get("wait_p50_h")
    task = t.get("task", "<task>")
    raw = t.get("status_raw")
    submit = "resubmit for human review" if raw == "needs_revision" or t.get("entered_pool_at") else "submit for human review"

    def warn_steps():
        for i in warns:
            fix = i["fix"].replace("{task}", task)
            steps.append({"do": f"{i['check']}: {i['why']} — {fix}", "eta": "~15m"})
        for i in infra:
            steps.append({"do": f"{i['check']}: infra error — codimango task rerun {task} (free)", "eta": "~1m"})

    g = gates(t)

    def findings():
        """What the presubmits / agent reviews on this commit asked for. A review note is skipped when the same session
        already reported it as a failing presubmit (the §5d agents record both)."""
        seen = set()
        for role in ("author", "independent"):
            ck = g[role]["check"]
            if ck["state"] == "bad" or (ck["state"] == "ok" and ck.get("warn") and ck.get("summary")):
                text = ck.get("summary") or f"{ck.get('fail')} failure(s) — see the run"
                key = " ".join(text.lower().split())
                if key not in seen:
                    seen.add(key)
                    kind = "presubmit" if ck["state"] == "bad" else "presubmit warnings"
                    steps.append({"do": f"{kind} ({ROLE_LABEL[role]}): {text}", "eta": "effort varies"})
        for role in ("author", "independent"):
            ck, rv = g[role]["check"], g[role]["review"]
            if rv["state"] != "bad" or not rv.get("note"):
                continue
            if ck["state"] == "bad" and ck.get("session") and ck.get("session") == rv.get("session"):
                continue
            key = " ".join(rv["note"].lower().split())
            if key not in seen:
                seen.add(key)
                steps.append({"do": f"review ({ROLE_LABEL[role]}): {rv['note'][:200]}", "eta": "effort varies"})

    def ladder(need_check=True):
        a, i = g["author"], g["independent"]
        if need_check and a["check"]["state"] != "ok":
            steps.append({"do": f"building session: run presubmit (`board check run {task}`)", "eta": "~10m"})
        if a["review"]["state"] != "ok":
            steps.append({"do": f"building session: approve (`board review add {task} --verdict ready --role author`)",
                          "eta": "~5m"})
        if i["check"]["state"] != "ok" or i["review"]["state"] != "ok":
            steps.append({"do": "independent agent (fresh, no build context): full presubmit + review, recorded with "
                                "`--role independent`", "eta": "~30m"})
        steps.append({"do": submit, "eta": "~2m"})

    if n.startswith("RESOLVE"):
        steps.append({"do": "agree who owns it; release the other claim", "eta": "~5m"})
    elif n.startswith("FIX validation") or n.startswith("RERUN validation"):
        findings()
        for i in fails:
            if i not in infra:
                steps.append({"do": f"{i['check']}: {i['fix']}".replace("{task}", task), "eta": "effort varies"})
        if infra:
            steps.append({"do": f"{infra[0]['check']}: infra error — codimango task rerun {task} (free)", "eta": "~1m"})
        if vs.get("skipped"):
            steps.append({"do": f"then {', '.join(sorted(set(vs['skipped'])))} will run (skipped until then)", "eta": "—"})
        steps.append({"do": "push, then wait for validation" if [i for i in fails if i not in infra]
                      else "wait for the rerun to validate", "eta": "typically ~45m"})
        if raw == "needs_revision":
            steps.append({"do": "once green: resubmit for human review", "eta": "~2m"})
    elif n.startswith("RERUN"):
        findings()
        steps.append({"do": f"codimango task rerun {task} (free) — results are for an older commit", "eta": "~1m"})
        steps.append({"do": "wait for validation", "eta": "~45m"})
    elif n.startswith("WAIT import"):
        steps.append({"do": "wait: codimango is importing your latest push", "eta": "~10m"})
        findings()
    elif n.startswith("WAIT validation"):
        steps.append({"do": "wait for validation to finish", "eta": "typically ~30m"})
        findings()
        if infra:
            steps.append({"do": f"{infra[0]['check']} hit an infra error — if it isn't retried: codimango task rerun "
                                f"{task}", "eta": "~1m"})
    elif n.startswith("ADDRESS agent"):
        before = len(steps)
        findings()
        if len(steps) == before:
            steps.append({"do": "address the session reviewer's 'changes' note (see card)", "eta": "effort varies"})
        warn_steps()
        ladder()
    elif n.startswith("ADDRESS"):
        last = next((d for d in reversed(t.get("decisions") or []) if d.get("kind") == "revision" and d.get("reason")), None)
        steps.append({"do": "address the human reviewer: " + (f"“{last['reason'][:220]}”" if last else "see the last review in codimango"),
                      "eta": "~3h"})
        findings()
        warn_steps()
        ladder()
    elif n.startswith("FIX check"):
        before = len(steps)
        findings()
        if len(steps) == before:
            steps.append({"do": "fix the presubmit failures, re-run `board check run`", "eta": "~1h"})
        warn_steps()
        ladder(need_check=False)
    elif n.startswith(("RUN check", "GET R1", "GET R2", "SUBMIT", "RESUBMIT")):
        if raw == "needs_revision":
            last = next((d for d in reversed(t.get("decisions") or []) if d.get("kind") == "revision" and d.get("reason")), None)
            steps.append({"do": f"confirm every point of the human review is covered ({t.get('pushes_since_decision', 0)} "
                                f"push(es) since it was sent back)" + (f": “{last['reason'][:160]}”" if last else ""),
                          "eta": "~15m"})
        findings()
        warn_steps()
        ladder()
    elif n.startswith("WAIT reviewer"):
        left = max(0.0, (wait_p50 or 40) - age_h)
        what = "review in progress — waiting for a decision" if raw == "being_reviewed" else "waiting for a reviewer to be assigned"
        steps.append({"do": what + (" (past the typical wait)" if left == 0 else ""),
                      "eta": _h(left) if left else "any time now"})
    elif n.startswith("IMPORT"):
        findings()
        steps.append({"do": "import the task into codimango", "eta": "~10m"})
    return rank_steps(steps)


ROUTINE = re.compile(r"^(submit|resubmit|once green|wait|then |push, then wait|waiting for|review in progress)", re.I)


def rank_steps(steps: list[dict]) -> list[dict]:
    """Real work first; obvious routine steps (submit, resubmit, waits) after it and marked 'routine' so the page greys
    them. Order within each class is kept — it is the plan."""
    for st in steps:
        st["routine"] = bool(ROUTINE.match(st["do"]))
    if all(st["routine"] for st in steps):
        return steps                                     # a pure wait: nothing to demote
    return [st for st in steps if not st["routine"]] + [st for st in steps if st["routine"]]


ROLE_LABEL = {"author": "building session", "independent": "independent agent"}


def gates(t: dict) -> dict:
    """The shared author/independent reducer result (computed once in the projection, see roles.gates)."""
    empty = {"check": {"state": "none"}, "review": {"state": "none"}}
    g = t.get("gates") or {}
    return {r: g.get(r) or empty for r in ("author", "independent")}


def review_summary(t: dict) -> dict:
    """{agent: '✓✓'|'✓'|'', human: text, bullets: [(kind, text)]}. Two agent approvals = the building session + one
    independent agent, both on the current commit."""
    g = gates(t)
    rounds = sum(1 for d in t.get("decisions") or [] if d["kind"] == "revision")
    bullets = []
    for role in ("author", "independent"):
        rv, ck = g[role]["review"], g[role]["check"]
        word = {"ok": "approved", "bad": "asked for changes", "old": "reviewed an older commit", "none": "no review yet"}[rv["state"]]
        bullets.append(({"ok": "ok", "bad": "bad", "old": "dim", "none": "pend"}[rv["state"]],
                        f"{ROLE_LABEL[role]}: {word}" + (f" (confidence {rv['confidence']}/5)" if rv.get("confidence") else "") + (f" — {rv['note'][:160]}" if rv["state"] in ("bad", "old") and rv.get("note") else "")))
        cword = {"ok": "presubmit clean", "bad": f"presubmit {ck.get('fail')} failure(s)", "old": "presubmit on an older commit",
                 "none": "presubmit not recorded"}[ck["state"]]
        bullets.append(({"ok": "ok", "bad": "bad", "old": "dim", "none": "pend"}[ck["state"]], f"{ROLE_LABEL[role]}: {cword}"))
    raw = t.get("status_raw")
    human = {"needs_reviewers_assigned": "waiting for a reviewer", "being_reviewed": "being reviewed",
             "needs_revision": f"needs revision ({rounds}×)", "accepted": "accepted", "used_in_training": "accepted · in training",
             "draft": "not submitted"}.get(raw, raw or "—")
    bullets.append(("ok" if raw in ("accepted", "used_in_training") else "bad" if raw == "needs_revision" else "info",
                    f"human: {human}"))
    order = {"bad": 0, "pend": 1, "info": 2, "ok": 3, "dim": 4}       # problems first
    bullets.sort(key=lambda b: order.get(b[0], 5))
    ok = [r for r in g if g[r]["review"]["state"] == "ok"]
    return {"agent": "✓✓" if len(ok) == 2 else "✓" if ok else "", "agent_current": bool(ok), "agent_green": len(ok) == 2,
            "human": human, "bullets": bullets, "gates": g}


def assignee(t: dict, load: dict[str, int], live_hosts: set[str] | None = None) -> str:
    """Turn the ownership availability state into one non-contradictory recommendation."""
    state = t.get("ownership_state") or (t.get("availability") or {}).get("state")
    if state in ("done", "in_pipeline") or (not state and t.get("group") in ("REVIEWING", "DONE", "VALIDATING")):
        return "nobody needed right now"
    if state == "worked_recently":
        last = t.get("last_push") or {}
        who = last.get("session_alias") or t.get("owner") or "the last session"
        at = last.get("at")
        try:
            age_s = max(0, datetime.now(timezone.utc).timestamp() - datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp())
            pushed = (f"{int(age_s // 60)}m" if age_s < 3600 else
                      f"{int(age_s // 3600)}h" if age_s < 86400 else f"{int(age_s // 86400)}d")
        except (AttributeError, TypeError, ValueError):
            pushed = None
        return f"check with {who} first ({'pushed ' + pushed + ' ago' if pushed else 'pushed recently'})"
    if state == "assigned_idle":
        owner = t.get("owner") or "assigned owner"
        at = t.get("owner_last_at")
        try:
            age_s = max(0, datetime.now(timezone.utc).timestamp() - datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp())
            idle = f"{int(age_s // 60)}m" if age_s < 3600 else f"{int(age_s // 3600)}h" if age_s < 86400 else f"{int(age_s // 86400)}d"
        except (AttributeError, TypeError, ValueError):
            idle = "unknown"
        return f"{owner} (idle {idle}) — message or take over"
    if state == "actively_working" and t.get("owner"):
        return f"keep with {t['owner']}"
    if state not in ("available", "never_seen"):                  # never worked = free too
        return "ownership unclear — inspect the three axes before assigning"
    live = {h: n for h, n in load.items() if live_hosts is None or h in live_hosts}
    if not live:
        return f"any free session (`board claim {t['task']}`)"
    host = min(live, key=lambda h: live[h])
    return f"a free session on {host} ({live[host]} tasks in progress there) · `board claim {t['task']}` from it"


# ------------------------------------------------------------------------------ primary action ("what now")
CHECK_ACTIONS = [  # (short check name from short_check, emoji, self-explaining label)
    ("oracle", "🔧", "Fix oracle · gold solution fails"),
    ("structure", "🔧", "Fix task structure"),
    ("test-patch", "🔧", "Fix test patch · does not apply/run"),
    ("build", "🐳", "Fix Docker build"),
    ("calibration", "🎚", "Calibrate difficulty"),
    ("reward-hack detector", "🛡", "Harden grader · reward hack possible"),
    ("agentic review", "🔍", "Fix agentic-review findings"),
    ("deep review", "🔍", "Fix deep-review findings"),
    ("provenance", "✍️", "Re-author flagged files · provenance"),
    ("contamination", "🧬", "Prove novelty · contamination flagged"),
    ("TBR", "🔁", "Rerun TBR on this commit"),
    ("eval GT", "🔧", "Fix eval ground truth"),
    ("AI check", "🔍", "Fix AI-assessment findings"),
]


def _check_action(issue: dict) -> tuple[str, str]:
    for name, emoji, label in CHECK_ACTIONS:
        if issue.get("check") == name:
            if name == "calibration" and re.search(r"step \d+ too (hard|easy)", issue.get("why", "")):
                return emoji, f"Calibrate · {re.search(r'step \d+ too (hard|easy)', issue['why']).group(0)}"
            return emoji, label
    return "🔧", f"Fix {issue.get('check', 'validation')}"


def done_when(t: dict) -> list[list[str]]:
    """The gates a task passes on its way to acceptance: [state, label]; state ok | bad | wait | todo."""
    g, raw, vs = gates(t), t.get("status_raw"), t.get("vsum") or {"issues": []}
    fails = [i for i in vs["issues"] if i["severity"] == "fail" and not i["why"].startswith("infra error")]
    sync_ok = t.get("sync") in ("OK", "OK·doc") and not t.get("older_results")
    st = lambda s: {"ok": "ok", "bad": "bad", "old": "todo", "none": "todo"}.get(s, "todo")
    submitted = raw in ("needs_reviewers_assigned", "being_reviewed", "accepted", "used_in_training")
    return [
        ["ok" if sync_ok and t.get("valid") != "RUN" else "wait" if t.get("valid") == "RUN" or t.get("sync") == "IMPORTING"
         else "todo", "server has the latest push and validated it"],
        ["ok" if t.get("valid") == "PASS" and not fails else "bad" if fails else "wait" if t.get("valid") == "RUN"
         else "todo", "server validation green"],
        [st(g["author"]["check"]["state"]), "presubmit · owner (building session) clean on this commit"],
        [st(g["independent"]["check"]["state"]), "presubmit · 3P (fresh independent agent) clean on this commit"],
        [st(g["author"]["review"]["state"]), "agent approval · owner"],
        [st(g["independent"]["review"]["state"]), "agent review · 3P approves"],
        ["ok" if submitted else "todo", "submitted for human review"],
        ["ok" if raw in ("accepted", "used_in_training") else "bad" if raw == "needs_revision"
         else "wait" if submitted else "todo", "human review accepted"],
    ]


def primary_action(t: dict) -> dict:
    """The one thing to do now, named so it explains itself: {emoji, label, tone, why, done_when}.
    tone: block (broken) | act (your move) | ship | wait | done."""
    n, raw, g = t.get("next") or "", t.get("status_raw"), gates(t)
    vs = t.get("vsum") or {"issues": []}
    fails = [i for i in vs["issues"] if i["severity"] == "fail" and not i["why"].startswith("infra error")]
    warns = [i for i in vs["issues"] if i["severity"] == "warn" and not i["why"].startswith("infra error")]
    role = lambda kind: next((r for r in ("author", "independent") if g[r][kind]["state"] == "bad"), "author")
    who = {"author": "owner", "independent": "3P"}
    def pa(emoji, label, tone, why):
        return {"emoji": emoji, "label": label, "tone": tone, "why": why, "done_when": done_when(t)}
    if n == "PARKED":
        pk = t.get("parked") or {}
        return pa("🅿️", f"Parked · {str(pk.get('status', 'parked')).lower()} in CLAIMS.md", "done",
                  f"CLAIMS.md parked it on {pk.get('updated', '?')} and nothing has touched it since; "
                  "claim it to pick it back up")
    if t.get("group") == "DONE" or n == "—":
        return pa("🏁", {"used_in_training": "Done · in training", "archived": "Done · archived"}.get(raw, "Done · accepted"),
                  "done", "nothing left to do")
    if n.startswith("RESOLVE") or n.startswith("CHECK clock"):
        return pa("🤺", "Resolve ownership" if n.startswith("RESOLVE") else "Fix host clock", "block",
                  "two sessions/claims disagree about who owns this task" if n.startswith("RESOLVE") else "event times are in the future")
    if n == "RERUN server":
        return pa("🔁", "Revalidate on server · latest push not validated", "block",
                  "server results are for an older commit; run `codimango task rerun` (free)")
    if n == "WAIT import":
        return pa("📥", "Server importing latest push", "wait", "auto-import normally finishes within minutes")
    if n == "RERUN validation":
        return pa("🔁", "Revalidate on server · infra error", "block", "a check errored on infrastructure, not the task")
    if n == "FIX validation":
        first = fails[0] if fails else (vs["issues"][0] if vs["issues"] else {"check": "validation", "why": ""})
        emoji, label = _check_action(first)
        more = f" (+{len(fails) - 1} more)" if len(fails) > 1 else ""
        return pa(emoji, label + more, "block", first.get("why", ""))
    if n == "WAIT validation":
        return pa("⏳", "Server validating", "wait", "codimango is running checks on the latest push")
    if n.startswith("WAIT reviewer"):
        return pa("👀" if raw == "being_reviewed" else "⌛",
                  "Human review · in progress" if raw == "being_reviewed" else "Human review · waiting for a reviewer",
                  "wait", "submitted; nothing to do until the reviewer decides")
    if n == "ADDRESS review":
        return pa("📝", "Revise · address human review", "act", "reviewer asked for a revision; nothing pushed since")
    if n.startswith("IMPORT"):
        return pa("📦", "Import task into codimango", "act", "the task exists only locally")
    if n.startswith("ADDRESS agent"):
        r = role("review")
        return pa("📝", f"Fix agent-review findings · {who[r]}", "block", (g[r]["review"].get("note") or "")[:160])
    if n.startswith("FIX check"):
        r = role("check")
        return pa("🧪", f"Fix presubmit findings · {who[r]}", "block", (g[r]["check"].get("summary") or "")[:160])
    known = ("RUN check", "GET R", "SUBMIT", "RESUBMIT", "FIX check", "ADDRESS")
    if n and not n.startswith(known):                    # a state this board does not model yet: say so plainly
        return pa("❔", f"Check task state · {n.lower()}", "act", "unrecognised state — open the task in codimango")
    if warns and any("verify" in (w.get("fix") or "") or "reviewer action" in w.get("why", "") for w in warns):
        w = next(w for w in warns if "verify" in (w.get("fix") or "") or "reviewer action" in w.get("why", ""))
        return pa("▲", f"Verify flagged check · {w['check']}", "act", w.get("why", ""))
    if g["author"]["check"]["state"] != "ok":
        return pa("🧪", "Presubmit · owner (building session)", "act", "run `board check run <task> --role author`")
    if g["independent"]["check"]["state"] != "ok":
        return pa("🧪", "Presubmit · 3P (fresh independent agent)", "act",
                  "a fresh agent with no build context runs the full presubmit and records it with --role independent")
    if g["author"]["review"]["state"] != "ok":
        return pa("👍", "Agent approval · owner", "act", "`board review add <task> --verdict ready --role author`")
    if g["independent"]["review"]["state"] != "ok":
        return pa("👀", "Agent review · 3P (fresh independent agent)", "act", "independent reviewer records --role independent")
    if n.startswith("RESUBMIT") or raw == "needs_revision":
        return pa("🚀", "Resubmit for human review", "ship", "every gate above is green on this commit")
    return pa("🚀", "Submit for human review", "ship", "every gate above is green on this commit")

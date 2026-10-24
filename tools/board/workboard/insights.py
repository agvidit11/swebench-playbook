"""Short, decision-ready summaries shared by the web page and the terminal: validation issues, review status,
sync status, next steps with rough ETAs, and who should take a task. Deterministic rules, no model calls."""
from __future__ import annotations

import re

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
            elif re.search(r"(never ran|errored|did not run)", detail, re.I):
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
    """Ordered steps [{do, eta}] for a task dict (projection fields + extra)."""
    n = t.get("next") or ""
    steps = []
    vs = t.get("vsum") or {"issues": []}
    fails = [i for i in vs["issues"] if i["severity"] == "fail"]
    age_h = (t.get("state_age_s") or 0) / 3600
    wait_p50 = flow.get("wait_p50_h")
    if n.startswith("RESOLVE"):
        steps.append({"do": "agree who owns it; release the other claim", "eta": "~5m"})
    infra = [i for i in vs["issues"] if i["why"].startswith("infra error")]
    task = t.get("task", "<task>")
    if n.startswith("FIX validation") or n.startswith("RERUN validation"):
        for i in fails:
            steps.append({"do": f"{i['check']}: {i['fix']}".replace("{task}", task), "eta": "effort varies"})
        if infra:
            steps.append({"do": f"{infra[0]['check']}: infra error — codimango task rerun {task} (free)", "eta": "~1m"})
        if vs.get("skipped"):
            steps.append({"do": f"then {', '.join(sorted(set(vs['skipped'])))} will run (skipped until then)", "eta": "—"})
        steps.append({"do": "push, then wait for validation" if fails else "wait for the rerun to validate",
                      "eta": "typically ~45m"})
        if t.get("status_raw") == "needs_revision":
            steps.append({"do": "once green: resubmit for human review", "eta": "~2m"})
    if n.startswith("ADDRESS agent"):
        steps.append({"do": "address the session reviewer's 'changes' note (see card)", "eta": "effort varies"})
    if n.startswith("FIX check"):
        steps.append({"do": "fix the presubmit failures, re-run `board check run`", "eta": "~1h"})
    if n.startswith("RERUN"):
        steps.append({"do": f"codimango task rerun {t.get('task', '<task>')} (free)", "eta": "~1m"})
        steps.append({"do": "wait for validation", "eta": "~45m"})
    if n.startswith("WAIT import"):
        steps.append({"do": "wait: codimango is importing your latest push", "eta": "~10m"})
    if n.startswith("WAIT validation"):
        steps.append({"do": "wait for validation to finish", "eta": "typically ~30m"})
        if infra:
            steps.append({"do": f"{infra[0]['check']} hit an infra error — if it isn't retried: codimango task rerun "
                                f"{t.get('task', '<task>')}", "eta": "~1m"})
    if n.startswith("ADDRESS"):
        steps.append({"do": "address the reviewer's points (see last review)", "eta": "~3h"})
        steps.append({"do": "presubmit + 2 agent reviews, then resubmit", "eta": "~1h"})
    if n.startswith("RUN check"):
        steps.append({"do": "`board check run` (presubmit)", "eta": "~10m"})
    if n.startswith("RUN check") or n.startswith("GET R1") or n.startswith("GET R2"):
        need = 2 if (t.get("review") in ("R0", "R~", None) or n.startswith("RUN")) else 1 if t.get("review") == "R1" else 0
        if need:
            steps.append({"do": f"{need} agent-session review{'s' if need > 1 else ''} (`board review add`)",
                          "eta": "~15m" if need == 1 else "~30m"})
        steps.append({"do": "submit for human review", "eta": "~2m"})
    if n.startswith("SUBMIT"):
        steps.append({"do": "submit for human review", "eta": "~2m"})
    if n.startswith("WAIT reviewer"):
        left = max(0.0, (wait_p50 or 40) - age_h)
        steps.append({"do": "waiting for a human reviewer" + (" (past the typical wait)" if left == 0 else ""),
                      "eta": _h(left) if left else "any time now"})
    if n.startswith("IMPORT"):
        steps.append({"do": "import the task into codimango", "eta": "~10m"})
    return steps


def review_summary(t: dict) -> dict:
    """{agent: '✓✓'|'✓'|'', agent_on_current: bool, human: tag-ish text, bullets: [(kind, text)]}"""
    latest = {}
    for r in t.get("agent_reviews") or []:              # latest verdict per session wins
        latest[(r.get("who"), r.get("current"))] = r
    cur = [r for r in latest.values() if r.get("current")]
    ready = {r["who"] for r in cur if r.get("verdict") == "ready"}
    changes = [r for r in cur if r.get("verdict") == "changes"]
    older_ready = {r["who"] for r in t.get("agent_reviews") or [] if r.get("verdict") == "ready" and not r.get("current")}
    rounds = sum(1 for d in t.get("decisions") or [] if d["kind"] == "revision")
    bullets = []
    bullets.append(("ok" if len(ready) >= 2 else "pend", f"agent approvals {min(len(ready), 2)}/2 on this commit"))
    if changes:
        bullets.append(("bad", f"{len(changes)} session asked for changes"))
    if older_ready and len(ready) < 2:
        bullets.append(("dim", f"{len(older_ready)} approval(s) on an older commit"))
    c = t.get("last_check")
    if not c:
        bullets.append(("pend", "presubmit not run"))
    elif c.get("fail"):
        bullets.append(("bad", f"presubmit {c['fail']} failure(s)"))
    else:
        bullets.append(("ok" if c.get("current") else "dim", "presubmit clean" + ("" if c.get("current") else " (older commit)")))
    raw = t.get("status_raw")
    human = {"needs_reviewers_assigned": "waiting for a reviewer", "being_reviewed": "being reviewed",
             "needs_revision": f"sent back ({rounds}×)", "accepted": "accepted", "used_in_training": "accepted · in training",
             "draft": "not submitted"}.get(raw, raw or "—")
    bullets.append(("ok" if raw in ("accepted", "used_in_training") else "bad" if raw == "needs_revision" else "info",
                    f"human: {human}"))
    return {"agent": "✓✓" if len(ready) >= 2 else "✓" if ready else ("✓" if older_ready else ""),
            "agent_current": bool(ready), "agent_green": len(ready) >= 2, "human": human, "bullets": bullets}


def assignee(t: dict, load: dict[str, int], live_hosts: set[str] | None = None) -> str:
    """Nobody while it waits on the server/reviewers; keep with a live owner; else the less-loaded *live* server."""
    if t.get("group") in ("REVIEWING", "DONE", "VALIDATING"):
        return "nobody needed right now"
    if t.get("claim_health") in ("OWNED", "ACTIVE", "LEGACY") and t.get("owner"):
        return f"keep with {t['owner']}"
    live = {h: n for h, n in load.items() if live_hosts is None or h in live_hosts}
    if not live:
        return f"any free session (`board claim {t['task']}`)"
    host = min(live, key=lambda h: live[h])
    return f"a free session on {host} ({live[host]} tasks in progress there) · `board claim {t['task']}` from it"

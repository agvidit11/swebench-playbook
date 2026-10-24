"""Short, decision-ready summaries shared by the web page and the terminal: validation issues, review status,
sync status, next steps with rough ETAs, and who should take a task. Deterministic rules, no model calls."""
from __future__ import annotations

import re

CHECK_NAMES = [  # (keyword in codimango label, short name, default fix)
    ("structur", "structure", "fix the task layout codimango flags"),
    ("oracle", "oracle", "fix the reference solution so it passes 3/3"),
    ("balance", "calibration", "rebalance difficulty (see detail)"),
    ("calibrat", "calibration", "rebalance difficulty (see detail)"),
    ("agentic", "agentic review", "address the agentic reviewer's findings"),
    ("provenance", "provenance", "have Codex re-author the flagged files"),
    ("contamin", "contamination", "re-source or prove novelty"),
    ("ai ", "AI check", "see codimango"),
    ("tbr", "TBR", "re-run TBR at this commit"),
    ("build", "build", "fix the Docker build"),
    ("evalgt", "eval GT", "fix the eval ground truth"),
]


def short_check(label: str) -> tuple[str, str]:
    low = (label or "").lower()
    for key, name, fix in CHECK_NAMES:
        if key in low:
            return name, fix
    return (label or "check").split(" (")[0][:28].lower(), "see codimango"


def short_detail(detail: str) -> tuple[str, str | None]:
    """(few-word reason, specific fix or None)."""
    d = (detail or "").strip()
    if re.search(r"infrastructure error|not a task defect|PROCESSED_FAILED|job did not succeed|\d+ errored", d, re.I):
        return "infra error on codimango's side (not your task)", "codimango task rerun (free); retry later if it repeats"
    m = re.search(r'"(\d+)_[^"]*"\s+too\s+(hard|easy)', d)
    if m:
        step, how = m.group(1), m.group(2)
        if how == "hard":
            return f"step {step} too hard", f"loosen step {step} or state the hidden rule"
        return f"step {step} too easy", f"make step {step} harder (more unstated work, less spec)"
    m = re.search(r"(\d+)\s*/\s*(\d+)\s+(?:checks\s+)?(?:failed|passed)", d)
    if "flagged" in d.lower() or "third-party" in d.lower():
        return "3rd-party authorship flagged", None
    if "pending" in d.lower() or "waiting" in d.lower() or "not run" in d.lower():
        return "still running", None
    first = re.split(r"[;(—]| - ", d)[0].strip()
    return (first[:60] + ("…" if len(first) > 60 else "")) if first else "failed", None


def validation_summary(items: list[dict]) -> dict:
    issues = []
    for it in items or []:
        st = it.get("status", "")
        if st in ("passed", "pass", "ok"):
            continue
        name, fix = short_check(it.get("name", ""))
        why, specific = short_detail(it.get("detail", ""))
        if name != "calibration" and re.match(r"step \d+ too (hard|easy)$", why):
            why, specific = short_detail(re.sub(r'"\d+_[^"]*"\s+too\s+(hard|easy)', "", it.get("detail", "")))
            specific = None
        sev = "fail" if st in ("failed", "error") else "warn" if st == "warn" else "pending"
        if why.startswith("infra error"):
            sev = "warn"                                   # rerun, not a task fix
        issues.append({"check": name, "why": why, "fix": specific or fix, "severity": sev})
    order = {"fail": 0, "warn": 1, "pending": 2}
    issues.sort(key=lambda i: order[i["severity"]])
    total = len(items or [])
    return {"issues": issues, "passed": total - len(issues), "total": total}


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
    if n.startswith("FIX validation"):
        for i in fails[:2]:
            steps.append({"do": f"{i['check']}: {i['fix']}", "eta": "~2h"})
        steps.append({"do": "push, then wait for validation", "eta": "~45m"})
    if n.startswith("FIX check"):
        steps.append({"do": "fix the presubmit failures, re-run `board check run`", "eta": "~1h"})
    if n.startswith("RERUN"):
        steps.append({"do": "codimango task rerun (free)", "eta": "~1m"})
        steps.append({"do": "wait for validation", "eta": "~45m"})
    if n.startswith("WAIT import"):
        steps.append({"do": "wait: codimango is importing your latest push", "eta": "~10m"})
    if n.startswith("WAIT validation"):
        steps.append({"do": "wait for validation to finish", "eta": "~30m"})
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
    cur = [r for r in t.get("agent_reviews") or [] if r.get("current")]
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


def assignee(t: dict, load: dict[str, int]) -> str:
    """Keep with the current owner; otherwise suggest the less-loaded server."""
    if t.get("claim_health") in ("OWNED", "ACTIVE", "LEGACY") and t.get("owner"):
        return f"keep with {t['owner']}"
    if t.get("group") in ("REVIEWING", "DONE", "VALIDATING"):
        return "nobody needed right now"
    if not load:
        return "any free session (`board claim`)"
    host = min(load, key=lambda h: load[h])
    return f"{host} (lighter load: {load[host]} active) · `board claim {t['task']} --to <{host} session>`"

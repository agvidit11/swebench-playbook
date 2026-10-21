#!/usr/bin/env python3
"""readme-server-check.py — fail a task whose README does not describe its server-validated commit.

Usage:
  readme-server-check.py <repo-root> <task> [<task> ...]          # fetches server state via codimango
  readme-server-check.py <repo-root> --snapshot server.jsonl        # uses a pre-fetched snapshot

Checks (any FAIL blocks submit):
  R1  README.md exists with Description / Completion Rates / Model Analysis / Anti-Cheating sections
  R2  Completion Rates names the server-validated commit (short SHA, 7 chars)
  R3  every Avocado per-step rate on the server appears in Completion Rates (as k/5 or a 0.x/1.0 score)
  R4  no placeholder / "pending" / "will be replaced" language in Completion Rates or Model Analysis
  R5  no internal links or local paths (internalfb, fburl, manifold, /tmp/, /home/, /data/, scratch)
  R6  Model Analysis is non-trivial (>= 200 chars)
Validation must be passing for R2/R3 to be meaningful; a pending/failed task reports SKIP for them.
"""
import json, re, subprocess, sys
from pathlib import Path

SECTIONS = ["Description", "Completion Rates", "Model Analysis", "Anti-Cheating"]
PLACEHOLDER = re.compile(r"(will (replace|be replaced|be added|come from)|not (yet )?available|pending|TBD|TODO|to be (measured|filled)|once (its|the) validation)", re.I)
INTERNAL = re.compile(r"(internalfb|fburl|manifold|fb\.workplace|/tmp/|/home/|/data/|scratch/)", re.I)


def server_state(task):
    show = subprocess.run(["codimango", "task", "show", task], capture_output=True, text=True).stdout
    errs = subprocess.run(["codimango", "task", "errors", task], capture_output=True, text=True).stdout
    sha = re.search(r"Commit SHA:\s+(\w+)", show)
    val = re.search(r"^Validation:\s+(\w+)", show, re.M)
    bal = next((l.strip() for l in errs.splitlines() if "pass/fail balance" in l), "")
    return {"task": task, "commit": sha.group(1) if sha else "", "validation": val.group(1) if val else "", "balance": bal}


def avocado_rates(balance):
    m = re.search(r"avocado \[[^\]]*\]:? ?([0-9./|]+)", balance)
    if not m:
        return []
    raw = m.group(1).strip("|")
    if "/" in raw:  # single-turn "2/5"
        return [raw]
    out = []
    for x in raw.split("|"):
        try:
            out.append(f"{round(float(x) * 5)}/5")
        except ValueError:
            pass
    return out


def section(text, name):
    m = re.search(rf"^#+\s*{re.escape(name)}[^\n]*\n(.*?)(?=^#+\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else None


def check(repo, st):
    t = st["task"]
    res = []
    p = Path(repo) / t / "README.md"
    if not p.exists():
        return [("R1", "FAIL", "README.md missing")]
    text = p.read_text()
    missing = [s for s in SECTIONS if section(text, s) is None]
    res.append(("R1", "FAIL" if missing else "PASS", f"missing {missing}" if missing else "sections ok"))
    cr = section(text, "Completion Rates") or ""
    ma = section(text, "Model Analysis") or ""
    if st["validation"] != "passing":
        res.append(("R2", "SKIP", f"validation {st['validation']}"))
        res.append(("R3", "SKIP", f"validation {st['validation']}"))
    else:
        short = st["commit"][:7]
        res.append(("R2", "PASS" if short and short in cr else "FAIL", f"server commit {short} {'named' if short in cr else 'NOT named'} in Completion Rates"))
        rates = avocado_rates(st["balance"])
        def present(r):
            k = int(r.split("/")[0]); dec = {0: ["0", "0.0"], 5: ["1", "1.0"]}.get(k, [f"{k/5:.1f}"])
            return r in cr or r.replace("/", " / ") in cr or any(re.search(rf"(?<![\d.]){re.escape(d)}(?![\d/])", cr) for d in dec)
        miss = [r for r in rates if not present(r)]
        res.append(("R3", "FAIL" if miss or not rates else "PASS", f"server avocado {rates}; missing in README: {miss}" if (miss or not rates) else f"rates {rates} present"))
    ph = PLACEHOLDER.search(cr + "\n" + ma)
    res.append(("R4", "FAIL" if ph else "PASS", f"placeholder text: '{ph.group(0)}'" if ph else "no placeholder"))
    il = INTERNAL.search(text)
    res.append(("R5", "FAIL" if il else "PASS", f"internal reference: '{il.group(0)}'" if il else "no internal refs"))
    res.append(("R6", "FAIL" if len(ma.strip()) < 200 else "PASS", f"model analysis {len(ma.strip())} chars"))
    return res


def main():
    repo = sys.argv[1]
    if len(sys.argv) > 3 and sys.argv[2] == "--snapshot":
        states = [json.loads(l) for l in open(sys.argv[3]) if l.strip()]
    else:
        states = [server_state(t) for t in sys.argv[2:]]
    bad = 0
    for st in sorted(states, key=lambda s: s["task"]):
        r = check(repo, st)
        fails = [x for x in r if x[1] == "FAIL"]
        bad += bool(fails)
        print(f"{'FAIL' if fails else 'PASS'}  {st['task']}  (server {st['commit'][:7]} {st['validation']})")
        for code, verdict, msg in r:
            if verdict != "PASS":
                print(f"      {verdict}  {code}  {msg}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

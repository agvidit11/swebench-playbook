#!/usr/bin/env python3
"""Compute the provenance L3 score LOCALLY, before pushing.

Mechanism (verified 2026-09-30 to 15 decimal places on dropshot-websocket):

    matchScore = sum(len(b) for b in blocks if b.text in file) / len(file)

The server re-diffs the CURRENT tree against the logged Claude tool-call on every
scoring — it is NOT a frozen carry-forward record. So a re-author does clear it,
and the score is predictable before you push.

    dropshot-websocket step-1 parser.py:  149 / 2358 = 0.063189143341815
    server reported:                                   0.063189143341815

CLEAR threshold is ~0.03 (measured: 0.0298 CLEAN with a block still present;
0.036 and 0.0631 both CONTAMINATED).

NOTE THE DENOMINATOR. Score is matched/len(file), so DELETING unrelated content
raises the score. Shrinking a file to "clean it up" can push it over the line.

Usage:
    prov-score.py                 # every task with a provenance record
    prov-score.py <task> [...]    # named tasks
    prov-score.py --json          # machine-readable
"""
import json
import os
import subprocess
import sys

CLEAR = 0.03          # below this has been observed CLEAN
SERVER_MIN_BLOCK = 24  # smallest block the server has ever reported is 29


def fetch(task):
    p = subprocess.run(["codimango", "task", "show", task, "--json"],
                       capture_output=True, text=True, timeout=180)
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return None


def live_tasks():
    p = subprocess.run(["codimango", "task", "list"],
                       capture_output=True, text=True, timeout=300)
    out = []
    for line in p.stdout.splitlines():
        parts = line.split()
        if parts and parts[0].replace("-", "").isalnum() and "=" not in parts[0]:
            out.append(parts[0])
    return out


def analyse(task, doc, root):
    """Return per-file rows: (path, matched, total, survived, n_blocks, score)."""
    prov = ((doc.get("qualitativeResult") or {}).get("provenanceCheck") or {})
    aw = prov.get("agentWrites") or {}
    rows = []
    for ev in aw.get("evidence") or []:
        fn = ev.get("fileName") or ""
        blocks = [b for x in (ev.get("v2Data") or {}).get("evidences") or []
                  for b in x.get("blocks", [])]
        if not blocks:
            continue
        path = os.path.join(root, fn)
        if not os.path.exists(path):
            rows.append((fn, None, sum(b["length"] for b in blocks),
                         None, len(blocks), None, ev.get("matchScore")))
            continue
        try:
            cur = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        alive = [b for b in blocks if b["text"] in cur]
        matched = sum(b["length"] for b in alive)
        score = matched / len(cur) if cur else 0.0
        rows.append((fn, matched, sum(b["length"] for b in blocks),
                     len(alive), len(blocks), score, ev.get("matchScore")))
    return prov.get("verdict"), aw.get("maxMatchScore"), rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    root = os.path.expanduser("~/swe-bench-pro-agvidit")
    tasks = args or live_tasks()

    results = []
    for t in tasks:
        doc = fetch(t)
        if not doc:
            continue
        verdict, server_max, rows = analyse(t, doc, root)
        if not rows:
            continue
        pred = max((r[5] for r in rows if r[5] is not None), default=None)
        results.append({"task": t, "verdict": verdict, "server": server_max,
                        "predicted": pred, "files": rows})

    if as_json:
        print(json.dumps(results, indent=1))
        return

    if not results:
        print("no tasks carry a provenance agent-write record")
        return

    print(f"{'task':<50}{'server':>9}{'predicted':>11}  {'blocks':>8}  next")
    print("-" * 104)
    for r in sorted(results, key=lambda r: -(r["predicted"] or 0)):
        pred = r["predicted"]
        surv = sum(f[3] or 0 for f in r["files"])
        tot = sum(f[4] for f in r["files"])
        if pred is None:
            verdict = "file missing"
        elif pred == 0:
            verdict = "clean — expect CLEAN on next scoring"
        elif pred < CLEAR:
            verdict = f"under {CLEAR} — expect CLEAN"
        else:
            need = pred / CLEAR
            verdict = f"needs ~{need:.1f}x reduction"
        s = f"{r['server']:.4f}" if r["server"] is not None else "-"
        p = f"{pred:.4f}" if pred is not None else "-"
        print(f"{r['task'][:49]:<50}{s:>9}{p:>11}  {str(surv) + '/' + str(tot):>8}  {verdict}")

    print()
    print("per-file detail (only files with surviving matches):")
    for r in results:
        for fn, matched, total, surv, nb, score, srv in r["files"]:
            if not matched:
                continue
            print(f"  {r['task'][:40]:<42} {fn.split('/', 1)[-1][:46]:<48} "
                  f"{matched:>5}ch {surv}/{nb} blk  score {score:.4f}")
    print(f"\nscore = surviving matched chars / len(file). CLEAR below ~{CLEAR}.")
    print("Deleting unrelated lines RAISES the score — the file length is the denominator.")


if __name__ == "__main__":
    main()

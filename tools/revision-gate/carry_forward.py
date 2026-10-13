#!/usr/bin/env python3
"""Step carry-forward check for a multi-turn task.

Reviewers bounce tasks when a later step no longer re-runs an earlier step's graded tests
("a step-3 agent could break rename and still pass"). For every step N >= 2, each test in
step N-1's fail_to_pass must appear in step N's fail_to_pass or pass_to_pass, either by the
same test ID or by the same test name (renamed copies such as test_s2_prior_s1.py count).

Usage: carry_forward.py <task-dir> [--json]
Exit: 0 = every step re-runs its predecessor's graded tests (or single-turn), 1 = gap, 2 = usage error.
Read-only.
"""
import json
import os
import re
import sys


def ids(cfg, key):
    return list(cfg.get(key) or cfg.get(key.upper()) or [])


def leaf(test_id):
    # pytest a/b.py::Cls::test_x[p] -> test_x[p]; go pkg::TestX -> TestX; junit Cls#m -> m
    t = re.split(r"::|#", test_id)[-1]
    t = t.split()[-1] if t.split() else t
    if "::" not in test_id and "#" not in test_id and "/" not in test_id:
        # unittest dotted id: app.tests.mod.Class.test_x -> test_x (keep any [param] intact)
        name, bracket, param = t.partition("[")
        t = name.rsplit(".", 1)[-1] + bracket + param
    return t


def step_dirs(task):
    sd = os.path.join(task, "steps")
    if not os.path.isdir(sd):
        return []
    def num(d):
        m = re.match(r"(\d+)_", d)
        return int(m.group(1)) if m else 10**9
    return [os.path.join(sd, d) for d in sorted(os.listdir(sd), key=num)
            if os.path.isfile(os.path.join(sd, d, "tests", "config.json"))]


def check(task):
    steps = step_dirs(task)
    if len(steps) < 2:
        return {"task": task, "applicable": False, "pairs": [], "ok": True}
    cfgs = [json.load(open(os.path.join(s, "tests", "config.json"))) for s in steps]
    pairs = []
    for i in range(1, len(steps)):
        prev = ids(cfgs[i - 1], "fail_to_pass")
        cur = ids(cfgs[i], "fail_to_pass") + ids(cfgs[i], "pass_to_pass")
        cur_ids, cur_leaves = set(cur), {leaf(t) for t in cur}
        missing = [t for t in prev if t not in cur_ids and leaf(t) not in cur_leaves]
        pairs.append({
            "from": os.path.basename(steps[i - 1]), "to": os.path.basename(steps[i]),
            "graded": len(prev), "missing": len(missing), "missing_sample": missing[:5],
        })
    return {"task": task, "applicable": True, "pairs": pairs,
            "ok": all(p["missing"] == 0 for p in pairs)}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1 or not os.path.isdir(args[0]):
        print(__doc__.strip().splitlines()[-3], file=sys.stderr)
        sys.exit(2)
    r = check(os.path.abspath(args[0]))
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))
    elif not r["applicable"]:
        print("SKIP  single-turn or one step: no carry-forward to check")
    else:
        for p in r["pairs"]:
            tag = "PASS" if p["missing"] == 0 else "FAIL"
            print(f"{tag}  {p['from']} -> {p['to']}: {p['graded'] - p['missing']}/{p['graded']} graded tests re-run")
            for t in p["missing_sample"]:
                print(f"        not re-run: {t}")
        if not r["ok"]:
            print("FIX   add every earlier step's graded tests (and their test files) to the later step's "
                  "test_patch and pass_to_pass. Reviewers flag this on every MT task that skips it.")
    sys.exit(0 if r["ok"] else 1)


main()

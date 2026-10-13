#!/usr/bin/env python3
"""grader-lint.py <task-dir> — grading-correctness detectors (R08 / BAD_GRADING).

Exit 1 on a blocking finding. Derived from the 2026-09-18 agentic-review
diagnosis over 8 tasks; each detector caught a real failure with 0 false
positives on the 4 GOOD tasks.
"""
import json, glob, os, re, sys

PRIVATE = [r'unsafe\.Pointer', r'UnsafeAddr', r'NumField\(\)', r'IsExported\(\)',
           r'reflect\.ValueOf\([^)]*\)\.Elem\(\)', r'instance_variable_get',
           r'\.send\(:', r'__dict__', r"getattr\([^,]+,\s*['\"]_"]

def configs(t):
    out = sorted(glob.glob(os.path.join(t, "steps", "*", "tests", "config.json")))
    top = os.path.join(t, "tests", "config.json")
    if os.path.exists(top): out.append(top)
    return out

def label(c, t):
    parts = c.split(os.sep)
    return parts[-3] if "steps" in parts else "top-level"

def main():
    t = sys.argv[1].rstrip("/")
    bad = False
    for c in configs(t):
        try: tp = json.load(open(c)).get("test_patch", "") or ""
        except Exception: continue

        hits = [p for p in PRIVATE if re.search(p, tp)]
        if hits:
            print(f"  \033[31mFAIL\033[0m  grader reaches PRIVATE STATE ({label(c,t)}): {len(hits)} pattern(s)")
            print( "        the grader may only touch what the instruction names -> R08 => BAD_GRADING_WRONG")
            print( "        circl named its whole public boundary and still failed on exactly this;")
            print( "        all nine non-oracle attempts died on that one test.")
            bad = True

        if re.search(r'reflect\.DeepEqual\([^,]+,\s*nil\s*\)', tp):
            print(f"  \033[36mADV \033[0m  nil-vs-empty pin ({label(c,t)}): DeepEqual against nil")
            print( "        representation is not contract unless stated. Assert len(got)==0.")

        # helper whose expected-value param is a collection, called with bare nil.
        # This is the form that actually bit us: awaitPendingFlushes(t, fn, nil)
        # compared with DeepEqual inside the helper, so an empty non-nil slice
        # fails with the unreadable 'got = [], want []'.
        # NB: params may themselves contain '(' — e.g. `pending func() []T` —
        # so match greedily to the last ')' before the opening brace.
        for m in re.finditer(r'^\+\s*func\s+(\w+)\((.*)\)\s*\{?\s*$', tp, re.M):
            name, params = m.group(1), m.group(2)
            if not re.search(r'(\[\]\w|map\[)', params):
                continue
            if re.search(r'\b' + re.escape(name) + r'\([^\n]*,\s*nil\s*\)', tp):
                print(f"  \033[36mADV \033[0m  nil-for-collection ({label(c,t)}): {name}(..., nil)")
                print( "        a collection-typed expectation passed as bare nil pins nil-vs-empty;")
                print( "        an empty non-nil result fails with 'got = [], want []'. Assert length.")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())

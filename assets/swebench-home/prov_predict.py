#!/usr/bin/env python3
"""Predict the provenance verdict LOCALLY, before spending a push.

Server evidence lives at qualitativeResult.provenanceCheck.agentWrites.evidence.
Per flagged file, `v2Data.evidences[].blocks` lists the exact text spans of the
SUBMITTED file that match logged third-party (claude_code) writes. Note
`scoredContent` is the submitted file itself, not the logged content, so it is
useless for prediction; and `presentInCurrent` is unreliable (see memory).

Prediction: a block that still occurs verbatim in the current working-tree file
is still evidence. Report, per file, how many logged blocks survive and what
fraction of the logged-block characters survive.

Usage: prov_predict.py <task> [<task>...] [--show]
"""
import os
import sys
from urllib.parse import quote

import glob  # noqa: E402
for _sp in sorted(glob.glob(os.path.expanduser("~/.local/share/uv/tools/codimango/lib/python3*/site-packages"))):
    sys.path.insert(0, _sp)
from cli.api_client import CodimangoClient  # noqa: E402

REPO = "https://github.com/codimango/swe-bench-pro-agvidit"
ROOT = os.path.expanduser("~/swe-bench-pro-agvidit")
MIN_LEN = 12          # ignore trivially short blocks (e.g. a lone brace)
SHOW = "--show" in sys.argv
client = CodimangoClient()

for name in [a for a in sys.argv[1:] if not a.startswith("--")]:
    d = client._request("GET", f"/api/v1/aai/tasks/{quote(name, safe='')}",
                        params={"sourceRepo": REPO}, cacheable=False)
    t = d.get("task", d)
    pc = (t.get("qualitativeResult") or {}).get("provenanceCheck") or {}
    ev = (pc.get("agentWrites") or {}).get("evidence") or []
    print("=" * 96)
    print(f"{name}  server={pc.get('verdict')}  evaluated-head={str(t.get('validationCommitSha') or t.get('commitSha'))[:8]}")
    print(f"  {'file':<40}{'server':>8}{'blocks':>8}{'surviving':>11}{'chars%':>8}  prediction")
    any_fail = False
    for e in ev:
        rel = e.get("fileName", "")
        blocks = []
        for x in (e.get("v2Data") or {}).get("evidences", []):
            blocks += [b.get("text", "") for b in x.get("blocks", []) if len(b.get("text", "")) >= MIN_LEN]
        path = os.path.join(ROOT, rel)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                cur = fh.read()
        except FileNotFoundError:
            cur = None
        if cur is None:
            surv, frac = 0, 0.0
            pred = "deleted"
        else:
            alive = [b for b in blocks if b in cur]
            surv = len(alive)
            tot = sum(len(b) for b in blocks) or 1
            frac = 100.0 * sum(len(b) for b in alive) / tot
            pred = "FAIL (blocks survive)" if alive else "clear"
            if SHOW and alive:
                for b in alive[:4]:
                    print(f"        surviving: {b[:90]!r}")
        any_fail |= pred.startswith("FAIL")
        short = rel.split("/", 1)[-1]
        print(f"  {short:<40}{e.get('matchScore', 0):>8.3f}{len(blocks):>8}{surv:>11}{frac:>7.0f}%  {pred}")
    if ev:
        print(f"  => {'PREDICTED CONTAMINATED — re-author the FAIL files' if any_fail else 'PREDICTED CLEAR on every flagged file'}")

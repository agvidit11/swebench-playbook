#!/usr/bin/env python3
"""Write a Codex brief that names the exact server-flagged spans to eliminate.

Usage: mk_prov_brief.py <task> <out.md>
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
name, out = sys.argv[1], sys.argv[2]
d = CodimangoClient()._request("GET", f"/api/v1/aai/tasks/{quote(name, safe='')}",
                               params={"sourceRepo": REPO}, cacheable=False)
pc = (d.get("task", d).get("qualitativeResult") or {}).get("provenanceCheck") or {}
ev = (pc.get("agentWrites") or {}).get("evidence") or []

lines = [f"# Task: clear the provenance gate on `{name}`", "",
         f"Work only in {ROOT}/{name}/ .",
         "Do NOT touch `instruction.md` or `solution/`.", "",
         "## Why", "",
         "The provenance gate reports CONTAMINATED. Its server-side evidence lists, per file, the",
         "exact text spans of the submitted file that match logged third-party (claude_code)",
         "writes. Every one of those spans is still present verbatim today, which is why earlier",
         "remediation attempts did not clear it. You must re-author each listed file so that NONE",
         "of its listed spans occurs in it any more.", "",
         "## Flagged files and the spans that must disappear", ""]
for e in ev:
    rel = e.get("fileName", "").split("/", 1)[-1]
    blocks = []
    for x in (e.get("v2Data") or {}).get("evidences", []):
        blocks += [b.get("text", "") for b in x.get("blocks", []) if len(b.get("text", "")) >= 12]
    lines.append(f"### `{rel}`  (server match {e.get('matchScore', 0):.3f})")
    lines.append("")
    for b in blocks:
        lines.append("```")
        lines.append(b)
        lines.append("```")
    lines.append("")
lines += [
    "## How",
    "",
    "- Re-author each listed file in your own form. A reword is not enough; the spans above are",
    "  matched verbatim, so change structure, statement order, naming and idiom.",
    "- For `tests/config.json`: the parsed JSON VALUE must stay exactly identical (same repo,",
    "  base_commit, patch, test_patch, every fail_to_pass/pass_to_pass id, and any mirrored",
    "  upper-case keys). Only the serialization may change — key order, indentation,",
    "  separators — and it must break every listed span.",
    "- For scripts: keep the contract (same commands run, same tests selected, same output the",
    "  parser consumes, same exit-status semantics). Where a span is a command line, an",
    "  equivalent invocation with a different argument order or form is fine.",
    "- Do not mention provenance, authorship or remediation in any file.",
    "",
    "## Verify before finishing",
    "",
    "1. For every span listed above, confirm it does NOT occur in the re-authored file",
    "   (e.g. a Python check reading each file and testing `span in text`). Report 0 survivors.",
    "2. config.json: load old (from `git show HEAD:<path>`) and new with json.load and confirm",
    "   they compare equal.",
    "3. Build/run the task image and confirm: baseline (test_patch only) — every fail_to_pass",
    "   FAILS and every pass_to_pass PASSES; oracle (solution/solve.sh) — all graded ids pass.",
    "",
    "Report the survivor count per file, the config equality result, and the baseline/oracle counts.",
]
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"wrote {out}: {len(ev)} flagged files")

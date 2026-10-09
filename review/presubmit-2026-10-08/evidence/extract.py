#!/usr/bin/env python3
"""Pull every human review block out of the dumped `task reviews --full` files.

Writes:
  decisions.tsv  one row per review: task, date, decision, confidence, reason (one line)
  nonaccept.md   full text of every Request-changes / Reject review, for root-cause reading
"""
import glob
import json
import re

tasks = json.load(open("tasks.json"))
tasks = tasks if isinstance(tasks, list) else tasks.get("tasks", [])
meta = {t["name"]: t for t in tasks}

rows, blocks = [], []
for f in sorted(glob.glob("rv-*.txt")):
    name = f[3:-4]
    text = open(f, encoding="utf-8", errors="replace").read()
    parts = re.split(r"\n\s*REVIEW by [^\n]*@ ", text)
    for p in parts[1:]:
        date = p[:16]
        dec = re.search(r"\*\*Decision:\*\*\s*([^\n]+)", p)
        if not dec:
            continue  # system rows like "Task was updated", "Revalidation started"
        dec = dec.group(1).strip()
        conf = re.search(r"Confidence \(1-5\):\*\*\s*(\d)", p)
        reason = re.search(r"\*\*Reason:\*\*\s*(.+?)(?:\n\s*- \*\*|\n\s*###|\Z)", p, re.S)
        reason = " ".join(reason.group(1).split()) if reason else ""
        t = meta.get(name, {})
        fmt = "MT" if "multi" in str(t.get("format")) else "ST"
        rows.append((name, fmt, t.get("reviewStatus", "?"), date, dec, conf.group(1) if conf else "", reason))
        if not dec.lower().startswith("accept"):
            body = re.sub(r"\n\s*\n+", "\n", p.split("### Reviewer Confidence")[0])
            blocks.append(f"\n\n######## {name} [{fmt}] now={t.get('reviewStatus')} review@{date} decision={dec}\n{body[:6000]}")

with open("decisions.tsv", "w") as fh:
    fh.write("task\tfmt\tnow\tdate\tdecision\tconf\treason\n")
    for r in rows:
        fh.write("\t".join(str(x) for x in r) + "\n")
open("nonaccept.md", "w").write("".join(blocks))

from collections import Counter
print("reviews with a decision:", len(rows))
print(Counter(r[4].split()[0] for r in rows))
print("tasks with >=1 non-accept:", len({r[0] for r in rows if not r[4].lower().startswith('accept')}))
acc_first = [n for n in meta if meta[n].get("reviewStatus") == "accepted"
             and not any(r[0] == n and not r[4].lower().startswith("accept") for r in rows)]
print("accepted on FIRST review (no prior request-changes):", len(acc_first))
print("nonaccept.md bytes:", len("".join(blocks)))

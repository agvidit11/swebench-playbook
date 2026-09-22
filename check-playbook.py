#!/usr/bin/env python3
"""Conformance checker for the playbook itself.

Neither source pipeline had one, and both rotted the same way: dangling pointers,
rules restated in two files, and owner boundaries that drifted between documents.
Run this before any commit that touches a playbook file.

Exit 1 on any FAIL. WARN never sets the exit code.
"""
import os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
ACT_DIRS = ("A-source", "B-build", "C-drive")
fails, warns = [], []


def md_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # .e2e/ and .review/ hold RUN ARTIFACTS, not playbook files. They are
        # produced by agents executing the playbook and must never be linted as
        # part of it — doing so once turned 0 fail into 27.
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", ".e2e", ".review", "node_modules")]
        for fn in sorted(filenames):
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def rel(p):
    return os.path.relpath(p, ROOT)


def is_act(p):
    return os.path.basename(os.path.dirname(p)) in ACT_DIRS


ALL = {rel(p): open(p, encoding="utf-8").read() for p in md_files()}
ACTS = {k: v for k, v in ALL.items() if is_act(os.path.join(ROOT, k))}

# ---------------------------------------------------------------- 1. act headers
# Every act-file must declare owner / input / output / exit in its first 40 lines.
for name, body in sorted(ACTS.items()):
    head = "\n".join(body.splitlines()[:40]).lower()
    for field in ("owner", "input", "output", "exit"):
        if not re.search(rf"\b{field}\b\**\s*[:|]", head):
            fails.append(f"{name}: header missing '{field}' in first 40 lines")

# ------------------------------------------------- 2. checklist + handoff blocks
for name, body in sorted(ACTS.items()):
    if not re.search(r"(?i)^#{1,4}.*checklist", body, re.M):
        fails.append(f"{name}: no CHECKLIST section (router §8)")
    if "HANDOFF" not in body:
        fails.append(f"{name}: no HANDOFF block (router §8)")
    else:
        for field in ("EXIT:", "CHECKLIST:", "ARTIFACTS:", "FACTS:", "OPEN:", "NEXT:"):
            if field not in body:
                warns.append(f"{name}: HANDOFF missing '{field}'")

# ------------------------------------------------------------ 3. dangling links
# The exact bug that broke SKILL.md: 8 router rows pointed at deleted files.
LINK = re.compile(r"`([A-Za-z0-9][\w./-]*\.(?:md|sh|py))`|\]\(([^)#]+\.md)\)")
known = set(ALL) | {
    rel(os.path.join(dp, fn))
    for dp, dn, fns in os.walk(ROOT)
    if ".git" not in dp
    for fn in fns
}
basenames = defaultdict(set)
for k in known:
    basenames[os.path.basename(k)].add(k)

# Source-set citations and external tooling are provenance, not navigation.
SOURCE_CITATION = re.compile(
    r"^(0[1-9]-[a-z-]+\.md|runbooks/[0-9]-[a-z]+\.md|0[0-9]-[a-z-]+\.md"
    r"|SKILL\.md|RUNBOOK\.md|[0-9]-(brainstorm|build|harness)\.md"
    r"|AGENT-BRIEF.*\.md|MT-[A-Z0-9-]+\.md|.*-CODEX-BRIEF.*\.md)$")
EXTERNAL_TOOL = ("harbor/", "sync_config.py", "multi_step.py")

EXTERNAL_OK = ("preflight.sh", "grader-lint.py", "instruction-lint.py",
               "push-task.sh", "mc.sh", "codex_repair.py", "verify_task.sh",
               "rubric-audit.py", "check-symbol-reachability.py",
               "check-playbook.py", "solve.sh", "test.sh", "run_script.sh",
               "parser.py", "config.json", "task.toml", "instruction.md",
               "README.md", "CLAUDE.md", "AGENTS.md", "TEST_RATIONALE.md",
               "MEMORY.md", "INDEX.md", "eval.sh", "Dockerfile",
               "gate0-override.md", "TEST_RATIONALE.md", "CHECKPOINT.md",
               "RELAY-STATE.md", "friction.md")

for name, body in sorted(ALL.items()):
    if name.startswith("ledger/RUNS"):
        continue  # archive of past runs; its paths are historical, not navigation
    for m in LINK.finditer(body):
        target = (m.group(1) or m.group(2)).strip()
        base = os.path.basename(target)
        if base in EXTERNAL_OK or target.startswith(("http", "/", "~", "codimango")):
            continue
        if SOURCE_CITATION.match(target) or any(t in target for t in EXTERNAL_TOOL):
            continue
        # resolve relative to the citing file's dir, then to root, then by basename
        cand = os.path.normpath(os.path.join(os.path.dirname(name), target))
        if cand in known or target in known or base in basenames:
            continue
        fails.append(f"{name}: dangling link -> {target}")

# ------------------------------------------------- 4. the iron-clad ownership rule
# No file may tell Claude or Codex to write instruction.md.
BAD_OWNER = re.compile(
    r"(?i)(claude|codex)[^.\n]{0,80}\b(write|author|edit|update|modif\w+|draft)s?\b"
    r"[^.\n]{0,60}instruction", re.M)
# The rule is stated many times; only an UNnegated instruction to write is a violation.
NEGATED = re.compile(r"(?i)\b(never|not|cannot|can't|no|nobody|neither|forbid\w*|"
                     r"prohibit\w*|must not|may not|out of scope|violation|ban\w*)\b")
for name, body in sorted(ALL.items()):
    for m in BAD_OWNER.finditer(body):
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_end = body.find("\n", m.end())
        ctx = body[line_start: line_end if line_end > 0 else len(body)]
        if NEGATED.search(ctx):
            continue
        line = body[: m.start()].count("\n") + 1
        fails.append(f"{name}:{line}: IRON-CLAD VIOLATION -> {ctx.strip()[:110]!r}")

# router must carry the rule verbatim
if "IRON-CLAD" not in ALL.get("00-ROUTER.md", ""):
    fails.append("00-ROUTER.md: the iron-clad rule is missing")

# ------------------------------------------------------- 5. duplicated rule text
# A distinctive sentence appearing in two files means a rule was restated.
def sentences(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    for s in re.split(r"(?<=[.!?])\s+|\n\|", t):
        s = " ".join(s.split())
        if 70 <= len(s) <= 400 and s.count("|") < 3:
            yield s

seen = defaultdict(list)
for name, body in ALL.items():
    if name.startswith("ledger/RUNS"):
        continue
    for s in sentences(body):
        seen[s].append(name)
for s, files in seen.items():
    if len(set(files)) > 1:
        warns.append(f"duplicated sentence in {sorted(set(files))}: {s[:100]!r}")

# ------------------------------------------------------------ 6. status markers
for name, body in sorted(ALL.items()):
    if name.startswith(("ledger/", "README")) or not is_act(os.path.join(ROOT, name)):
        continue
    if not re.search(r"STATUS:\s*(LIVE|SCOPED-TO|UNVALIDATED-PRIOR|QUARANTINED)", body):
        warns.append(f"{name}: no STATUS marker anywhere")

# ------------------------------------------------------ 7. router coverage of acts
router = ALL.get("00-ROUTER.md", "")
for name in sorted(ACTS):
    if os.path.basename(name) not in router:
        fails.append(f"{name}: not referenced from 00-ROUTER.md")

# -------------------------------------------------------------------- 8. report
conflicts = sum(len(re.findall(r"CONFLICT\s*[—-]\s*UNRESOLVED", b)) for b in ALL.values())

print(f"scanned {len(ALL)} md files ({sum(b.count(chr(10)) for b in ALL.values())} lines), "
      f"{len(ACTS)} act-files")
print(f"open CONFLICT — UNRESOLVED markers: {conflicts}\n")

for f in fails:
    print(f"FAIL  {f}")
for w in warns:
    print(f"WARN  {w}")

print(f"\n{len(fails)} fail, {len(warns)} warn")
sys.exit(1 if fails else 0)

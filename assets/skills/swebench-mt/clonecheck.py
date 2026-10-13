#!/usr/bin/env python3
"""Oracle-clone contamination check for a split table.

A generated implementation that reproduces the oracle is NOT independent
evidence of solvability -- the oracle was itself model-authored, so the same
model family regenerates it. Counting such a run as a "pass" manufactures a
fake gradient out of a step that is genuinely too hard.

Two cheap signals, no execution required:

  ratio     difflib similarity of the ADDED lines vs the oracle's added lines.
  novel     how many string literals that the ORACLE INTRODUCED (absent from the
            repo at base) the implementation reproduces verbatim. This is the
            sharp one: two independent authors essentially never coin the same
            error message.

Usage: clonecheck.py <oracle.patch> <base-repo-dir> <impl.patch> [impl.patch ...]
"""
import difflib
import pathlib
import re
import sys


def added(patch_text):
    return [l[1:].strip() for l in patch_text.splitlines()
            if l.startswith("+") and not l.startswith("+++")]


def literals(lines):
    out = set()
    for l in lines:
        for m in re.findall(r'"((?:[^"\\]|\\.){8,})"', l):
            out.add(m)
    return out


oracle_patch = pathlib.Path(sys.argv[1]).read_text()
base_dir = pathlib.Path(sys.argv[2])
oracle_added = added(oracle_patch)
oracle_text = "\n".join(oracle_added)

# Literals the oracle INTRODUCES: present in the oracle patch, absent from the
# repo at base. Those are the fingerprints.
base_blob = ""
for p in base_dir.rglob("*.rs"):
    try:
        base_blob += p.read_text(errors="replace")
    except Exception:
        pass
novel = {s for s in literals(oracle_added) if s not in base_blob}

print(f"oracle introduces {len(novel)} novel string literal(s)")
print()
print(f"{'impl':<12} {'ratio':>6}  {'novel/'+str(len(novel)):>8}  verdict")
for f in sys.argv[3:]:
    impl_added = added(pathlib.Path(f).read_text())
    ratio = difflib.SequenceMatcher(None, oracle_text,
                                    "\n".join(impl_added)).ratio()
    hits = sum(1 for s in novel if any(s in l for l in impl_added))
    clone = ratio >= 0.90 or (len(novel) and hits >= max(2, len(novel) // 2))
    name = pathlib.Path(f).parent.name
    print(f"{name:<12} {ratio:6.3f}  {hits:>8}  "
          f"{'ORACLE-CLONE (discount)' if clone else 'independent'}")

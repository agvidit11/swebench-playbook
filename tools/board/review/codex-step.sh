#!/usr/bin/env bash
# usage: review/codex-step.sh <task-number> "<files/paths reviewed>" ["extra context"]
# Codex reviews one build task as a pair programmer and writes review/step-<n>.md. Read-only on code.
set -u
n="$1"; paths="$2"; extra="${3:-}"
cd "$(dirname "$0")/.."
brief="You are the pair-programming reviewer for task $n of plans/2026-10-23-workboard-v1.md (spec: DESIGN.md).
Experts you embody: terminal UI/UX, software design, engineering manager readability, open-source architect.
Review ONLY these paths: $paths. Run: python3 -m unittest discover -s tests -v (paste the summary).
Check: correctness vs plan task $n + spec; failure modes and edge cases the tests miss; stdlib-only; no private
values in code; naming/readability; API shapes later tasks rely on (plan Interfaces). $extra
Output review/step-$n.md: 1) VERDICT: APPROVE or CHANGES; 2) numbered required changes (file:line, exact fix);
3) optional suggestions (max 5). Do NOT edit any file except review/step-$n.md."
timeout 1700 codex exec -s workspace-write -c model_reasoning_effort=high -C "$PWD" "$brief" < /dev/null > "review/step-$n.log" 2>&1
echo "exit=$?"; cat "review/step-$n.md" 2>/dev/null || tail -20 "review/step-$n.log"

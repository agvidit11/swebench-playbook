#!/usr/bin/env bash
# task-budget.sh — where every task sits against the accepted commit distribution.
#
#   ./task-budget.sh            # whole portfolio, worst first
#   ./task-budget.sh <task>     # one task
#
# Measured over our own corpus: accepted tasks median 6.5 commits, MAX 10. Failures run to 22.
# Nothing has ever been accepted past 10, so that is where the runbook forces a retire
# question (C8). This reports; it never decides.
set -uo pipefail
REPO="${SWEBENCH_REPO:-$HOME/swe-bench-pro-agvidit}"
[ -d "$REPO/.git" ] || { echo "task-budget: no repo at $REPO" >&2; exit 2; }
ONE="${1:-}"
{ for d in "$REPO"/*/; do
  t=$(basename "$d"); [ -f "$d/task.toml" ] || continue
  [ -n "$ONE" ] && [ "$t" != "$ONE" ] && continue
  n=$(git -C "$REPO" rev-list --count HEAD -- "$t" 2>/dev/null || echo 0)
  [ "$n" -eq 0 ] && continue
  if   [ "$n" -le 6 ];  then b="normal"
  elif [ "$n" -le 10 ]; then b="TAIL — name what is different"
  else                       b="OVER — outside the accepted distribution (C8)"; fi
  printf "%-56s %7s  %s\n" "${t:0:56}" "$n" "$b"
done ; } | sort -k2,2nr | { printf "%-56s %7s  %s\n" "TASK" "COMMITS" "BAND"; cat; }

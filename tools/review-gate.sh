#!/usr/bin/env bash
# review-gate.sh — run the SERVER'S OWN reviewers locally, before the push.
#
#   ./review-gate.sh <task-dir> plan      # resolve reviewers, print the dispatch plan
#   ./review-gate.sh <task-dir> check     # validate collected verdicts; exit 1 if not all clean
#
# Why this exists: `codimango job review` CANNOT review an unpushed tree — it resolves a
# server-side commit. So every rubric failure is discovered a cohort late unless you run the
# reviewers yourself first. We had four of these skills installed and were self-scoring the
# axes from memory instead of invoking them.
#
# This script does only the mechanical half: path resolution and verdict validation. The
# reviewing itself is one subagent per reviewer -- see B-build/B6-review-gate.md.

set -uo pipefail

TASK="${1:?usage: review-gate.sh <task-dir> plan|check}"
MODE="${2:?usage: review-gate.sh <task-dir> plan|check}"
TASK="${TASK%/}"
[ -d "$TASK" ] || { echo "review-gate: no such task dir: $TASK" >&2; exit 2; }

LLMS="$HOME/.llms/skills/claude-templates"
BUNDLE_ROOT="$HOME/.config/opencode/bundles/cache/claude-templates/team-aai"
# newest bundle wins; sort -V so 1.55.0 beats 1.9.0
BUNDLE="$(ls -1d "$BUNDLE_ROOT"/*/skills 2>/dev/null | sort -V | tail -1)"

REVIEWERS=(
  review-task-swebench-v2
  review-task-swebench-multiturn
  aai-code-review
  review-quality-swebench-skills
  check-contamination-v2
  verify-task-provenance
)
# Known-unavailable. Named explicitly so its absence is a recorded gap, not a silent omission.
MISSING_EXPECTED=(test-quality-verifier)

OUT="$TASK/audit/review-gate"

resolve() {  # $1=skill name -> prints path, or nothing
  local s="$1" p
  for p in "$LLMS/$s/SKILL.md" "${BUNDLE:-/nonexistent}/$s/SKILL.md"; do
    [ -f "$p" ] && { printf '%s' "$p"; return 0; }
  done
  return 1
}

if [ "$MODE" = plan ]; then
  mkdir -p "$OUT"
  echo "task:     $TASK"
  echo "verdicts: $OUT/<reviewer>.json   (one per reviewer, written by its subagent)"
  echo
  echo "DISPATCH ONE SUBAGENT PER LINE. Each reads ONLY its own SKILL.md and reviews $TASK."
  echo
  local_missing=0
  # Format-aware. Dispatching the multi-turn reviewer at a single-turn task produced 82
  # NO-SIGNAL checks on one run -- noise that buries the signal and burns a reviewer slot.
  IS_MT=no; [ -d "$TASK/steps" ] && IS_MT=yes
  for s in "${REVIEWERS[@]}"; do
    if [ "$s" = review-task-swebench-multiturn ] && [ "$IS_MT" = no ]; then
      printf '  %-34s SKIPPED — single-turn task, reviewer is not applicable\n' "$s"; continue
    fi
    if p="$(resolve "$s")"; then
      printf '  %-34s %s\n' "$s" "$p"
    else
      printf '  %-34s *** UNRESOLVED -- record as a gap, do not skip silently\n' "$s"
      local_missing=$((local_missing+1))
    fi
  done
  for s in "${MISSING_EXPECTED[@]}"; do
    resolve "$s" >/dev/null 2>&1 \
      && printf '  %-34s %s  (was missing, now available -- add to REVIEWERS)\n' "$s" "$(resolve "$s")" \
      || printf '  %-34s NOT INSTALLED (known gap; note it in the ledger)\n' "$s"
  done
  echo
  BH=$("$(dirname "${BASH_SOURCE[0]}")/bundle-hash.sh" "$TASK" 2>/dev/null | sed 's/.*bundle_sha256=//;s/ .*//')
  echo "bundle:   ${BH:-<unavailable>}"
  echo "  Every verdict MUST record this hash. A verdict against a different bundle is void:"
  echo "  measured 2026-09-30, five sibling verdicts had reviewed a file edited 53 minutes"
  echo "  later, and one quoted a sentence that no longer existed."
  echo
  echo "Each subagent must write $OUT/<reviewer>.json:"
  echo '  {"reviewer":"<name>","verdict":"Accept|Revise|Reject","critical":0,"high":0,'
  echo '   "medium":0,"low":0,"findings":[{"id":"","severity":"","summary":"","evidence":""}]}'
  echo
  echo "Then: review-gate.sh $TASK check"
  [ "$local_missing" -gt 0 ] && echo "NOTE: $local_missing reviewer(s) unresolved." >&2
  exit 0
fi

if [ "$MODE" != check ]; then
  echo "review-gate: mode must be 'plan' or 'check'" >&2; exit 2
fi

# ---- check ---------------------------------------------------------------
[ -d "$OUT" ] || { echo "review-gate: no verdicts at $OUT -- run 'plan' first" >&2; exit 1; }

FAIL=0
declare -a EVIDENCE=()

IS_MT=no; [ -d "$TASK/steps" ] && IS_MT=yes
for s in "${REVIEWERS[@]}"; do
  if [ "$s" = review-task-swebench-multiturn ] && [ "$IS_MT" = no ]; then
    printf '  SKIP  %-34s not applicable to a single-turn task\n' "$s"; continue
  fi
  f="$OUT/$s.json"
  if ! resolve "$s" >/dev/null 2>&1; then
    printf '  SKIP  %-34s reviewer not installed (recorded gap)\n' "$s"
    continue
  fi
  if [ ! -s "$f" ]; then
    printf '  FAIL  %-34s no verdict file\n' "$s"; FAIL=1; continue
  fi
  read -r verdict crit high < <(python3 - "$f" <<'PY'
import json,sys
try: d=json.load(open(sys.argv[1]))
except Exception: print("UNPARSEABLE 9 9"); raise SystemExit
print(d.get("verdict","MISSING"), int(d.get("critical",0) or 0), int(d.get("high",0) or 0))
PY
  )
  # Collect evidence strings for the boilerplate check
  while IFS= read -r e; do [ -n "$e" ] && EVIDENCE+=("$e"); done < <(
    python3 - "$f" <<'PY'
import json,sys
try: d=json.load(open(sys.argv[1]))
except Exception: raise SystemExit
for x in d.get("findings") or []:
    ev=(x.get("evidence") or "").strip()
    if ev: print(ev)
PY
  )
  vb=$(python3 -c 'import json,sys;print((json.load(open(sys.argv[1])).get("bundle") or "")[:16])' "$f" 2>/dev/null)
  cb=$("$(dirname "${BASH_SOURCE[0]}")/bundle-hash.sh" "$TASK" 2>/dev/null | sed 's/.*bundle_sha256=//;s/ .*//' | cut -c1-16)
  if [ -n "$cb" ] && [ "$vb" != "$cb" ]; then
    printf '  FAIL  %-34s STALE — reviewed bundle %s, current %s\n' "$s" "${vb:-<none>}" "$cb"; FAIL=1; continue
  fi
  if [ "$verdict" != "Accept" ] || [ "$crit" -gt 0 ] || [ "$high" -gt 0 ]; then
    printf '  FAIL  %-34s verdict=%s critical=%s high=%s\n' "$s" "$verdict" "$crit" "$high"; FAIL=1
  else
    printf '  PASS  %-34s Accept (C0 H0)\n' "$s"
  fi
done

# Their anti-boilerplate rule: identical evidence across >3 checks blocks completion.
if [ "${#EVIDENCE[@]}" -gt 0 ]; then
  DUP=$(printf '%s\n' "${EVIDENCE[@]}" | sort | uniq -c | sort -rn | awk '$1>3{print; exit}')
  if [ -n "$DUP" ]; then
    echo "  FAIL  boilerplate evidence reused >3 times: ${DUP}"
    FAIL=1
  fi
fi

echo
if [ "$FAIL" -eq 0 ]; then
  echo "REVIEW GATE: PASS — every installed reviewer returned Accept with zero Critical/High."
  echo "This is not a prediction of the server's verdict. It is the same check, run earlier."
else
  echo "REVIEW GATE: BLOCKED — do not push. Route each finding to the act that owns the artifact."
fi
exit "$FAIL"

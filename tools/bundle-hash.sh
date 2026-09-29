#!/usr/bin/env bash
# bundle-hash.sh — the semantic fingerprint of a task bundle.
#
#   ./bundle-hash.sh <task-dir>            # print the hash
#   ./bundle-hash.sh <task-dir> --list     # print the hash and every file that fed it
#
# Bind this to every calibration, oracle and review result. A hash mismatch invalidates
# the result REGARDLESS of timestamps or what you remember changing (B7 §4).
#
# Excluded, deliberately: README.md and audit/ — prose and evidence, not semantics. Editing
# a README must not invalidate a calibration campaign. Everything else counts: instruction,
# tests, solution, environment, task.toml, steps/.

set -uo pipefail
TASK="${1:?usage: bundle-hash.sh <task-dir> [--list]}"
TASK="${TASK%/}"
LIST="${2:-}"
[ -d "$TASK" ] || { echo "bundle-hash: no such task dir: $TASK" >&2; exit 2; }

# -print0/-z throughout: task paths can contain spaces, and a split path silently
# changes the hash, which is the one failure mode this tool must not have.
FILES=$(find "$TASK" -type f \
          ! -name 'README.md' \
          ! -path "$TASK/audit/*" \
          ! -path '*/.git/*' \
          -print0 | LC_ALL=C sort -z | tr '\0' '\n')

[ -n "$FILES" ] || { echo "bundle-hash: no files matched under $TASK" >&2; exit 2; }

# Hash CONTENT and PATH together, so a rename with identical bytes still moves the hash.
HASH=$(
  while IFS= read -r f; do
    printf '%s\0' "${f#"$TASK"/}"
    sha256sum "$f" | cut -d' ' -f1
  done <<< "$FILES" | sha256sum | cut -d' ' -f1
)

if [ "$LIST" = "--list" ]; then
  echo "bundle: $TASK"
  while IFS= read -r f; do
    printf '  %s  %s\n' "$(sha256sum "$f" | cut -c1-12)" "${f#"$TASK"/}"
  done <<< "$FILES"
  echo
fi

printf 'bundle_sha256=%s  files=%s\n' "$HASH" "$(wc -l <<< "$FILES")"

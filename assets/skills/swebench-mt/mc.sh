#!/usr/bin/env bash
# mc.sh — run the 1P prompt-authoring agent safely from a prompt FILE.
#
# Backend: `muse exec` (Muse Code). `metacode run` was retired 2026-09-29 and
# now shims to muse, so the old --format/--dir flags fail closed.
#
#   ./mc.sh <prompt-file> <repo-dir> [out-file]
#
# Solves three silent failures, all of which returned exit 0:
#
#  1. No TTY  -> metacode prints only a ~192-byte gateway banner and exits 0.
#               `script -qec ... /dev/null` supplies a pty.
#
#  2. Quoting -> embedding "$(cat prompt)" inside the script -qec string means
#               any apostrophe ("the crate's API") terminates the quoting.
#               Best case the apostrophes are silently DELETED and the model
#               gets a corrupted prompt; worst case the shell executes prompt
#               fragments. Passing the prompt as one argv element fixes it.
#
#  3. Backticks and $( ) -> measured on the pair-prism run, 2026-09-22: a
#               backticked identifier was shell-expanded OUT of the prompt and
#               metacode exited 0 on the mutilated text. The inner script is now
#               built with printf %q and a QUOTED heredoc, so nothing in this
#               file re-expands. See the CALLER WARNING below, because the more
#               common corruption happens before mc.sh is ever invoked.
#
# CALLER WARNING — the usual cause of a mangled prompt is how you WROTE the file.
#   BAD :  cat > p.md <<EOF     ... `Foo#bar` is executed by YOUR shell
#   GOOD:  cat > p.md <<'EOF'   ... quoted delimiter, nothing expands
#   BEST:  write the file with an editor/Write tool, not a heredoc.
# mc.sh checks the file for surviving shell metacharacters and reports a digest
# so you can prove what was sent.

set -uo pipefail
P="${1:?usage: mc.sh <prompt-file> <repo-dir> [out-file]}"
D="${2:?usage: mc.sh <prompt-file> <repo-dir> [out-file]}"
OUT="${3:-}"
[ -s "$P" ] || { echo "mc.sh: prompt file empty or missing: $P" >&2; exit 2; }

# --- integrity report: prove what is about to be sent -----------------------
BYTES=$(wc -c < "$P")
SHA=$(sha256sum "$P" | cut -c1-12)
echo "mc.sh: sending $BYTES bytes sha=$SHA from $P" >&2

# A prompt that reaches here having ALREADY lost its backticks is undetectable,
# so warn on the asymmetry instead: backticks should come in pairs.
TICKS=$(tr -cd '`' < "$P" | wc -c)
if [ $((TICKS % 2)) -ne 0 ]; then
  echo "mc.sh: WARNING odd number of backticks ($TICKS) — the prompt may have been" >&2
  echo "mc.sh:          mangled at write time by an UNQUOTED heredoc. Use <<'EOF'." >&2
fi
if grep -qE '\$\(|\$\{[A-Za-z_]' "$P"; then
  echo "mc.sh: WARNING prompt contains \$( or \${ — if you wrote it with an unquoted" >&2
  echo "mc.sh:          heredoc those already expanded. Verify before trusting the reply." >&2
fi

# --- inner script: quoted heredoc + printf %q, so nothing re-expands --------
TMP=$(mktemp -t mc-inner.XXXXXX.sh)
{
  printf '%s\n' '#!/usr/bin/env bash'
  printf '%s\n' 'set -uo pipefail'
  # 2026-09-29: `metacode run` is retired — it now shims to `muse exec`, which
  # rejects --format and exits before doing anything, leaving only a gateway
  # banner. Two dispatches died this way before the cause was visible.
  #
  # muse exec takes --prompt-file, so the prompt no longer round-trips through
  # a shell variable at all. That removes the quoting/backtick corruption this
  # script was written to defend against, at the source rather than by escaping.
  #   --dir  -> --workspace
  #   --yolo -> not needed; the workspace grant is enough to write files.
  printf 'exec muse exec --prompt-file %q --workspace %q\n' "$P" "$D"
} > "$TMP"
chmod +x "$TMP"

if [ -n "$OUT" ]; then
  timeout 1700 script -qec "$TMP" /dev/null > "$OUT" 2>&1
  rc=$?
  SZ=$(wc -c < "$OUT")
  echo "mc.sh: exit=$rc bytes=$SZ -> $OUT" >&2
  # Byte count does NOT separate success from the gateway banner. Measured
  # 2026-09-22: a successful one-line answer was 739 B, a total failure 723 B.
  # The old `-lt 600` gate passed three dead dispatches in a row. Detect the
  # banner by CONTENT, and require some prose that is not banner furniture.
  BODY=$(grep -avE 'Meta AI Gateway|Using AI Gateway|^[[:space:]]*$|^\[|Warning: Failed to mount' "$OUT" | wc -c)
  if grep -qaiE 'gateway|not authorized|quota|rate.?limit' "$OUT" && [ "$BODY" -lt 400 ]; then
    echo "mc.sh: ERROR looks like a gateway banner, not an answer (body=${BODY}B). NOT a usable reply." >&2
    rc=90
  elif [ "$BODY" -lt 200 ]; then
    echo "mc.sh: WARNING only ${BODY}B of non-banner content — verify before trusting this." >&2
  fi
else
  timeout 1700 script -qec "$TMP" /dev/null; rc=$?
fi
rm -f "$TMP"
exit $rc

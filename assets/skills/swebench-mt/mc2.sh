#!/usr/bin/env bash
# mc2.sh — run the 1P model (Muse Code, successor of MetaCode) headlessly from a prompt FILE.
#
#   ./mc2.sh <prompt-file> <workspace-dir> [out-file]
#
# MetaCode was retired 2026-09-29: `metacode run` now forwards to `muse exec`,
# which rejects `--format`, so mc.sh returns a ~250-byte banner and exit 0 with
# no work done. `muse exec` reads the prompt from a file natively, so none of
# mc.sh's pty/quoting workarounds are needed.
#
# --workspace roots the tools; containment beyond it must still be stated in
# the prompt. To let the model write a file outside the repo it reads, pass a
# common ancestor as the workspace and name the allowed path in the prompt.

set -uo pipefail
P="${1:?usage: mc2.sh <prompt-file> <workspace-dir> [out-file]}"
D="${2:?usage: mc2.sh <prompt-file> <workspace-dir> [out-file]}"
OUT="${3:-/dev/stdout}"
[ -s "$P" ] || { echo "mc2.sh: prompt file empty or missing: $P" >&2; exit 2; }
echo "mc2.sh: sending $(wc -c < "$P") bytes sha=$(sha256sum "$P" | cut -c1-12) from $P (workspace $D)" >&2
cd "$D" || exit 2
muse exec --workspace "$D" --prompt-file "$P" < /dev/null > "$OUT" 2>&1
rc=$?
if [ "$OUT" != /dev/stdout ]; then
  body=$(grep -v '^muse:' "$OUT" | wc -c)
  echo "mc2.sh: exit=$rc body=${body}B -> $OUT" >&2
  [ "$body" -lt 400 ] && echo "mc2.sh: WARNING short reply — check $OUT" >&2
fi
exit $rc

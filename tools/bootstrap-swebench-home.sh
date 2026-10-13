#!/usr/bin/env bash
# Create ~/swebench on a fresh host and seed it from assets/swebench-home/.
#
# Default is NO-CLOBBER: a file that already exists in ~/swebench is never touched.
# --update: also replace a local file when the asset differs AND the asset is newer
#           (mtime); the old local copy is kept as <file>.bak-<timestamp>.
# --dry-run: print what would happen.
#
# Usage: ~/swebench-playbook/tools/bootstrap-swebench-home.sh [--update] [--dry-run]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$HERE/assets/swebench-home"
DST="${SWEBENCH_HOME:-$HOME/swebench}"
UPDATE=0; DRY=0
for a in "$@"; do
  case "$a" in
    --update) UPDATE=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n 2,10p "$0"; exit 0 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done
[ -d "$SRC" ] || { echo "missing $SRC — is ~/swebench-playbook up to date? (git pull)" >&2; exit 1; }
run() { if [ "$DRY" = 1 ]; then echo "  (dry) $*"; else "$@"; fi; }

run mkdir -p "$DST" "$DST/skill-backups"
ts="$(date +%Y%m%d-%H%M)"
for f in "$SRC"/*; do
  [ -f "$f" ] || continue
  name="$(basename "$f")"; out="$DST/$name"
  if [ ! -e "$out" ]; then
    echo "add      $name"; run cp -p "$f" "$out"
  elif cmp -s "$f" "$out"; then
    echo "same     $name"
  elif [ "$UPDATE" = 1 ] && [ "$f" -nt "$out" ]; then
    echo "update   $name (local kept as $name.bak-$ts)"
    run cp -p "$out" "$out.bak-$ts"; run cp -p "$f" "$out"
  else
    echo "keep     $name (local differs; not overwritten — use --update to take a newer asset)"
  fi
done
for f in "$DST"/*.py; do [ -f "$f" ] && run chmod +x "$f"; done
echo "done: $DST"
echo "note: the provenance tools also need the codimango CLI (uv tool) and ~/swe-bench-pro-agvidit checked out."

#!/usr/bin/env bash
# Install the revision-gate pre-push hook into clones of the codimango task repo.
#
#   install-hook.sh                 # find every clone of codimango/swe-bench-pro-agvidit on this host
#   install-hook.sh <repo> [...]    # or name the clones
#   install-hook.sh --uninstall     # restore whatever hook was there before
#   install-hook.sh --list          # show discovered clones and their current pre-push hook
#
# Worktrees share their main clone's hooks, so one install covers them. An existing pre-push hook is
# kept as pre-push.local and still runs first. Re-running is safe.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARK="revision-gate pre-push hook"
UNINSTALL=""; [ "${1:-}" = "--uninstall" ] && { UNINSTALL=1; shift; }
LIST=""; [ "${1:-}" = "--list" ] && { LIST=1; shift; }

repos=("$@")
if [ ${#repos[@]} -eq 0 ]; then
    while IFS= read -r cfg; do
        grep -q 'codimango/swe-bench-pro-agvidit' "$cfg" 2>/dev/null && repos+=("$(dirname "$(dirname "$cfg")")")
    done < <(
        # top-level dirs only, skipping EdenFS checkouts (a recursive walk would traverse the whole mount)
        for d in "$HOME"/* "$HOME"/scratch/* /data/repos/*; do
            [ -d "$d" ] && [ ! -L "$d" ] && [ ! -e "$d/.eden" ] && [ ! -e "$d/.hg" ] || continue
            find "$d" -maxdepth 4 -path '*/.git/config' -type f 2>/dev/null
        done | sort -u)
fi
[ ${#repos[@]} -eq 0 ] && { echo "no clones of codimango/swe-bench-pro-agvidit found"; exit 1; }

for r in "${repos[@]}"; do
    common=$(git -C "$r" rev-parse --git-common-dir 2>/dev/null) || { echo "skip  $r (not a git repo)"; continue; }
    case "$common" in /*) ;; *) common="$r/$common" ;; esac
    hooks=$(git -C "$r" config core.hooksPath || echo "$common/hooks")
    case "$hooks" in /*) ;; *) hooks="$r/$hooks" ;; esac
    h="$hooks/pre-push"
    if [ -n "$LIST" ]; then
        echo "$(readlink -f "$r")  pre-push: $( [ -f "$h" ] && (grep -q "$MARK" "$h" && echo revision-gate || echo OTHER) || echo none)"
        continue
    fi
    mkdir -p "$hooks"
    if [ -n "$UNINSTALL" ]; then
        if grep -q "$MARK" "$h" 2>/dev/null; then
            rm -f "$h"; [ -f "$h.local" ] && mv "$h.local" "$h"; echo "removed  $r"
        fi
        continue
    fi
    if [ -f "$h" ] && ! grep -q "$MARK" "$h"; then
        mv "$h" "$h.local"; echo "kept existing hook as $h.local"
    fi
    cp "$HERE/pre-push" "$h"; chmod 755 "$h"
    echo "installed  $r  ($h)"
done

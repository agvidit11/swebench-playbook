#!/usr/bin/env bash
# Move Vidit's swebench-mt Claude skill between hosts via this repo.
#
#   sync-skill.sh install    # on another host: back up ~/.claude/skills/swebench-mt
#                            # to ~/swebench/skill-backups/, then install the snapshot
#   sync-skill.sh snapshot   # on the source host: refresh assets/skills/swebench-mt
#                            # from ~/.claude/skills/swebench-mt (then commit + push)
#   sync-skill.sh diff       # show what differs between snapshot and installed skill
#
# Backups never go inside ~/.claude/skills/ (Claude would load them as skills).
# *.bak* files and __pycache__ are never copied in either direction.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNAP="$HERE/assets/skills/swebench-mt"
LIVE="$HOME/.claude/skills/swebench-mt"
BK="$HOME/swebench/skill-backups"
EXCL=(--exclude='*.bak*' --exclude='__pycache__/')
command -v rsync >/dev/null || { echo "rsync required" >&2; exit 1; }

case "${1:-}" in
  install)
    [ -f "$SNAP/SKILL.md" ] || { echo "no snapshot at $SNAP (git pull?)" >&2; exit 1; }
    if [ -d "$LIVE" ]; then
      mkdir -p "$BK"; b="$BK/swebench-mt.bak-$(date +%Y%m%d-%H%M)"
      cp -r "$LIVE" "$b"; echo "backup: $b"
    fi
    mkdir -p "$LIVE"
    # rsync INTO the existing dir (keeps the dir inode: it may be bind-mounted elsewhere)
    rsync -a --delete "${EXCL[@]}" "$SNAP/" "$LIVE/"
    echo "installed: $LIVE"
    echo "next: ~/swebench-playbook/tools/bootstrap-swebench-home.sh   # if ~/swebench is missing"
    ;;
  snapshot)
    [ -f "$LIVE/SKILL.md" ] || { echo "no skill at $LIVE" >&2; exit 1; }
    mkdir -p "$SNAP"
    rsync -a --delete "${EXCL[@]}" "$LIVE/" "$SNAP/"
    echo "snapshot refreshed: $SNAP — review 'git diff' then commit + push"
    ;;
  diff)
    diff -ru -x '*.bak*' -x '__pycache__' "$SNAP" "$LIVE" || true
    ;;
  *) sed -n 2,12p "$0"; exit 2 ;;
esac

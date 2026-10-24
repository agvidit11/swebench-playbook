#!/usr/bin/env bash
# Ship tools/board from the shared checkout without touching other sessions' uncommitted files:
# copy tools/board into a clean worktree at origin/master, commit, push, then fast-forward the shared
# checkout only if `git reset --keep` can do it safely.
set -euo pipefail
msg="$1"
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
url="ssh://git@github.com:22/agvidit11/swebench-playbook.git"
wt="$(mktemp -d /tmp/wb-ship.XXXX)"
git -C "$repo" fetch -q origin
git -C "$repo" worktree add -q --detach "$wt" origin/master
rsync -a --delete --exclude '__pycache__' --exclude 'review/*.log' --exclude 'review/live-sample-*' \
      "$repo/tools/board/" "$wt/tools/board/"
cd "$wt"
git add -A tools/board
if git diff --cached --quiet; then echo "nothing to ship"; else
  git commit -q -m "$msg"
  git push -q "$url" HEAD:master
  echo "pushed $(git rev-parse --short HEAD)"
fi
cd "$repo"
git worktree remove --force "$wt"
git fetch -q origin
if git reset -q --keep origin/master 2>/dev/null; then echo "shared checkout now at $(git rev-parse --short HEAD)";
else echo "shared checkout left as is (other sessions' edits overlap upstream); tools/board files already match"; fi

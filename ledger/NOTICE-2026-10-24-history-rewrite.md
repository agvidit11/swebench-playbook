# NOTICE 2026-10-24: master history was rewritten (force-push)

Raw review logs under tools/board/review/*.log contained private data and were purged from all history.
The file tree is otherwise byte-identical (same 1250 commits, same tip tree).

**Before your next pull/push on any other clone (e.g. the second devserver):**

    git fetch origin
    git log --oneline origin/master@{1}..HEAD   # your unpushed commits, if any
    git reset --keep origin/master              # if you have NO unpushed commits
    # with unpushed commits instead:  git rebase --onto origin/master <old origin tip> HEAD

Do NOT `git pull` (merge) — that would merge the old history, logs included, back in.

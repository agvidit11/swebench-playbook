---
description: Show the workboard (who owns what, what to do next) or run a board subcommand
argument-hint: "[show <task> | available | changes | stats | claim <task> | status ...]"
allowed-tools: Bash(board:*), Bash(~/.local/bin/board:*)
---

Run `board $ARGUMENTS --plain` (if `board` is not on PATH use `~/.local/bin/board`) and show the output.
Then summarize in 3 bullets: what needs attention first, what is ready for me, and anything out of sync.
Do not edit any task files and do not run claim/release unless the arguments ask for it.

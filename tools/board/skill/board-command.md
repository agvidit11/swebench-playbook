---
description: Show the workboard (who owns what, what to do next) or run a board subcommand
argument-hint: "[checkin | show <task> | available | changes | stats | claim <task> | status ...]"
allowed-tools: Bash(board:*), Bash(~/.local/bin/board:*)
---

If the arguments are `checkin`: work out from THIS conversation which codimango tasks you are actively working on
(task folder names). Run `board here <task> [<task> ...]`, or `board here --idle` if none, then run `board here` and
confirm it lists exactly those tasks. Report the result in one line and stop.

Otherwise run `board $ARGUMENTS --plain` (if `board` is not on PATH use `~/.local/bin/board`) and show the output.
Then summarize in 3 bullets: what needs attention first, what is ready for me, and anything out of sync.
Do not edit any task files and do not run claim/release unless the arguments ask for it.

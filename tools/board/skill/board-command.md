---
description: Show the workboard (who owns what, what to do next) or run a board subcommand
argument-hint: "[checkin | courier | show <task> | available | msg <task|session> ... | status ...]"
allowed-tools: Bash(board:*), Bash(~/.local/bin/board:*), SendMessage
---

If the arguments are `checkin`: work out from THIS conversation which codimango tasks you are actively working on
(task folder names). Run `board here <task> [<task> ...]`, or `board here --idle` if none, then run `board here` and
confirm it lists exactly those tasks. Report the result in one line and stop.

If the arguments are `courier`, become the dedicated courier and keep looping until the user stops you:

1. Run `board courier-wait --json --timeout 3600`. Do not poll while it is blocked; the wait costs no model tokens.
2. For every returned item, use SendMessage to send a compact envelope containing its message id, sender, optional
   task, and body to `native_id`/the named session.
3. On a positive SendMessage result, run
   `board receipt <message_id> '<recipient>' delivered`. On rejection, run the same command with
   `failed --reason "<short error>"`.
4. Re-run step 1. Never infer “seen,” never write to sockets/transcripts, and never record delivery before success.

Otherwise run `board $ARGUMENTS --plain` (if `board` is not on PATH use `~/.local/bin/board`) and show the output.
Then summarize in 3 bullets: what needs attention first, what is ready for me, and anything out of sync.
Do not edit any task files and do not run claim/release unless the arguments ask for it.

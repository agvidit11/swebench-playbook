---
name: workboard
description: Shared task board across machines and agent sessions — who owns which codimango task, what to do next, server drift, reviews, stats and rank. Use before touching any task ("is anyone on X", "what should I work on", "claim/release a task", "review this task", "board", "workboard", "how is my week going", "my rank").
---

# workboard

Run `board` (alias for `~/swebench-playbook/tools/board/board`). Read-only commands are always safe.

**Before touching a task:** `board show <task>` — if OWNER is another live session, stop and coordinate.
Hooks already name your session, claim a task when you first edit it, and block edits to a task another
live session owns ("owned by … — run: workboard show <task>").

**After reviewing a task (the one manual step):**
`board review add <task> --verdict ready|changes|comment --confidence 1-5 --note "<one line>"`
R2 = two different sessions said ready on the same commit. A new push turns reviews into R~.

| Want | Command |
|---|---|
| What to do next / who owns what | `board` (`--wide`, `--all`, `--group owner`) |
| Free tasks | `board available` |
| One task in full / why NEXT says that | `board show <task>` / `board explain <task>` |
| Claim, hand to another session, give up | `board claim <task>` / `--to "<tab title words>"` / `board release <task> --reason ...` |
| Run presubmit and log it | `board check run <task>` |
| What changed | `board changes` |
| Progress, flow, funnel, rank | `board stats` (`--quality`, `--from/--to`), `board rank` |
| Health | `board status` |

Rules: never edit a task another live session owns; never fake a review; `--json` on any read for scripts.

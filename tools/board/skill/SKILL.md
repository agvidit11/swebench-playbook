---
name: workboard
description: Shared task board across machines and agent sessions — who owns which codimango task, what to do next, server drift, reviews, stats and rank. Use before touching any task ("is anyone on X", "what should I work on", "claim/release a task", "review this task", "board", "workboard", "how is my week going", "my rank").
---

# workboard

Run `board` (installed on PATH by `board setup`). Read-only commands are always safe.

**Before touching a task:** `board show <task>` — if OWNER is another live session, stop and coordinate.
Hooks name your session and record your activity on a task; the background sync (every 2 minutes) then
attempts the atomic claim, so there is a short window before ownership is real — claim explicitly with
`board claim <task>` when it matters. Edits to a task another live session owns are blocked
("owned by … — run: workboard show <task>").

**Shared routine for every session (this keeps both servers in sync and avoids overlap):**
1. Before picking work: `board available` and `board show <task>` (owner, next steps, last review).
2. Starting a NEW task: `board claim <slug>` *before* scaffolding, even if it isn't in codimango yet — the slug then
   shows as yours on every server, so no one builds the same idea. Also add your CLAIMS.md row as usual.
3. Presubmit: `board check run <task>`; if you ran the gate yourself, `board check record <task> --pass N --warn N
   --fail N --summary "..."`; for a batch, `board check import <dir>` (one `<task>.txt` per task).
4. Done or handing over: `board release <task> --reason "..."` and tell the next owner with `board msg`.
5. Messages to you appear inside your session automatically (📬 workboard: …). Act, reply with `board msg`,
   then `board ack <id>`.

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
| Message a session / server / everyone | `board msg <tab words|server|all> "text" [--task T]` |
| Your messages (also shown to you automatically) | `board inbox` · `board ack <id|all>` |
| What is happening on both servers | `board feed` · web Team tab (`board serve`) |
| Health | `board status` |
| One-time import of an old CLAIMS.md | `board import-claims --dry-run`, then without `--dry-run` |

Rules: never edit a task another live session owns; never fake a review; `--json` on any read for scripts.

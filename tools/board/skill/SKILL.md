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

If `board` is not found (non-login shells, Codex shells), use `~/.local/bin/board` — same command.

**Check in (keeps owners correct on the board):** when you start or switch to a task, `board here <task>`
(claims it, or renews your claim); when you have no task, `board here --idle`. A roll call from the board
("📋 roll call …" in your context) means: run `board here` with your current tasks now, then `board ack`.
`board here` with no arguments shows what the board thinks you own.

**Shared routine for every session (this keeps both servers in sync and avoids overlap):**
1. Before picking work: `board available` and `board show <task>` (owner, next steps, last review).
2. Starting a NEW task: `board claim <slug>` *before* scaffolding, even if it isn't in codimango yet — the slug then
   shows as yours on every server, so no one builds the same idea. Also add your CLAIMS.md row as usual.
3. Presubmit — every task needs TWO on its current commit, shown as two ticks on the board:
   - **building session** (you, when the work is done): `board check run <task> --role author`. Running
     `presubmit.py <task> ...` directly from a Claude session is recorded automatically by the hook.
   - **independent agent** (a fresh agent with no build context, e.g. the §5d presubmit): when it finishes, record it
     with `board check record <task> --role independent --pass N --warn N --fail N --summary "<what to fix, one line>"`.
   The summary is what the board shows as the next step, so make it the fix, not the verdict. A new push greys both
   ticks (the old result stays visible) until they are re-run on the new commit.
4. Finished a chunk of work (a draft, a calibration round, a revision, a presubmit): report it so Stats can credit
   the right model — `board report <task> --phase <sourcing|drafting|calibration|presubmit|independent_review|
   revision|draft_fixing|validation_babysit> --model <model id> [--kind codex|muse] --summary "<one line>"`.
   Use `--kind` when the work was done by a Codex/Muse job you ran, not by you.
5. Done or handing over: `board release <task> --reason "..."` and tell the next owner with `board msg`.
6. Messages to you appear inside your session automatically (📬 workboard: …). Act, reply with `board msg`,
   then `board ack <id>`.

**Messaging:** `board msg <task> "text"` resolves and pins the task's current owner. `task:<slug>` is explicit;
you may also target a stable session/name fragment, server ID, or `all`. States mean exactly queued locally,
published in the private ledger, delivered by courier/hook, and explicitly acked. Never call published “delivered.”
Codex/Muse jobs route to their parent Claude session when known.

**Supervisor (one per server):** handles task allocation, disk usage, checklists and board status for its server.
A session takes the role with `board supervisor claim`, posts updates with `board supervisor status "<text>"
--checklist "[x] ..."` (disk use and owned/live counts are added automatically), and hands it off with
`board supervisor release`. Anyone reaches it with `board msg supervisor "..."` (this server) or
`board msg supervisor:<server> "..."`; `board supervisor` shows both servers' supervisors and their last update.

**Courier session:** keep one dedicated normal Claude session open and run `/board courier`. It repeatedly runs
`board courier-wait --json --timeout 3600` (the blocking wait costs zero model turns), delivers each returned item
with native SendMessage, then runs `board receipt <message_id> '<recipient>' delivered`. If SendMessage rejects it,
record `failed --reason "<short error>"`. Re-run the wait after every batch. Never edit a transcript/socket or claim
delivery without a positive tool result.

**Agent approvals — also two: the building session and one independent agent:**
`board review add <task> --verdict ready|changes|comment --role author|independent --note "<one line>"`
R2 = the building session AND an independent agent said ready on the same commit. A new push turns reviews into R~.
Everything you record is pushed to the shared ledger immediately; the dashboard pulls it every 30 s. Its browser
polls canonical regions conditionally (bodyless 304 when unchanged), so filters, rows, and open drawers stay put.
`board setup` installs `board serve --ensure` as a one-minute single-instance watchdog alongside sync.

**Tokens and advice:** the Team tab separates indexed lifetime/session tokens, last-hour usage, and current context
pressure. Keep/watch/rotate/unblock advice is deterministic, explains its thresholds, and never acts automatically.
Task token totals are qualified by attribution coverage. Spend remains `cost unavailable` unless private pricing and
authoritative token/model data support an estimate; never interpret unknown as `$0`.

| Want | Command |
|---|---|
| What to do next / who owns what | `board` (`--wide`, `--all`, `--group owner`) |
| Free tasks | `board available` |
| One task in full / why NEXT says that | `board show <task>` / `board explain <task>` |
| Check in / show what you own | `board here <task>…` · `board here --idle` · `board here` |
| Ask every session to check in | `board rollcall` (`--server ID`) |
| Report finished work (feeds model throughput) | `board report <task> --phase P --model M [--kind K] --summary "..."` |
| Per-server supervisor | `board supervisor` · `claim` · `status "text" --checklist "..."` · `release` · `board msg supervisor[:ID]` |
| Claim, hand to another session, give up | `board claim <task>` / `--to "<tab title words>"` / `board release <task> --reason ...` |
| Run presubmit and log it | `board check run <task>` |
| What changed | `board changes` |
| Progress, flow, funnel, rank | `board stats` (`--quality`, `--from/--to`), `board rank` |
| Message a task owner / session / server / everyone | `board msg <task|task:slug|session|server|all> "text" [--task T]` |
| Your messages (also shown to you automatically) | `board inbox` · `board ack <id|all>` |
| Operate the delivery courier | `board courier` · `board courier-wait --json` · `board receipt …` |
| What is happening on both servers | `board feed` · web Team tab (`board serve` / `board serve --ensure`) |
| Health | `board status` (includes live dashboard and watchdog health) |
| One-time import of an old CLAIMS.md | `board import-claims --dry-run`, then without `--dry-run` |

Rules: never edit a task another live session owns; never fake a review or delivery receipt; `--json` on any read for scripts.

# workboard

An action-first terminal board for one person's work spread across several machines and agent sessions.
It answers: **what do I do next, who is working on what, is anything out of sync with the server, and how
is the week going?** Built for codimango (SWE-bench) authoring; the core is generic (sources, claims,
checks, reviews, stats) with codimango/Claude specifics in adapters.

```
board                      # the board: ATTENTION / READY / WAITING, health banner, this week vs last
board show <task>          # one task in full        board explain <task>   # every input + rule behind NEXT
board available            # tasks nobody owns       board changes          # since your last look
board claim <task> [--to "<tab title words>"]        board release <task> --reason "..."
board check run <task>     # run your pre-submit gate (unchanged) and log the result against the commit
board review add <task> --verdict ready --confidence 4 --note "..."
board stats [--quality] [--from D --to D]            board rank [import <file>]
board status               # sources, ledger, claims, hooks, cron, dashboard health
board ui                   # interactive terminal app (tabs, filters, search, details)
board serve                # live web dashboard on localhost:8765 (Board / Team / Stats)
board serve --ensure       # exit 0 if healthy/already starting; otherwise start one detached server
board msg <who> "text"     # target a task, stable session/name, server, or all
board inbox · board ack <id> · board feed   # your messages, mark handled, cross-server activity
board courier              # dedicated Claude courier: block until a delivery is ready (zero tokens while waiting)
board courier-wait --json  # courier protocol output
board receipt <msg> <recipient> delivered|failed [--reason "..."]
board import-claims --dry-run   # one-time: show live rows of an old CLAIMS.md ([legacy] claims_md); drop --dry-run to import
```

## How it works

- **Sources:** codimango CLI (status, validation, review dates), git (task heads, commits), a private
  **ledger** repo (append-only per-host event files: claims, reviews, checks, session names).
- **Claims** are create-only git refs (`refs/claims/<hash>`) on the ledger remote: exactly one session wins;
  renew/steal/release are compare-and-swap on the exact commit. Expired after 24h without renewal.
- **Ownership has three independent axes:** assignment, recent task activity, and server pipeline. The page says
  `free` only when all three are clear and no remote change was observed in the last 72 hours. Other scan states are
  actively working, assigned idle, in pipeline, worked recently, never seen, conflict, and done.
- **Sessions** come from Claude's native registry with a stable kind/host/uid-domain/native-id key. Foreign-uid,
  foreign-domain, malformed, stale-PID, and PID-reused records never count as live. Codex and Muse executions appear
  as child runs under the Claude session that launched them when the link is supported by evidence.
- **Usage indexing** incrementally tails only live/recent (14-day) Claude, Codex, and Muse logs with
  path-fingerprint/inode/offset cursors under `~/.cache/workboard`. It stores numeric counters, IDs, timestamps,
  task slugs, and model names—never prompt, response, command, or message text. Task totals retain
  exact/medium/ambiguous/unattributed buckets; unknown attribution is never forced onto a task.
- **Hooks** (Claude Code) record activity, name sessions after their tab title and block edits to a task another
  live session owns. They never touch the network and always fail open; the 2-minute background `board sync`
  then attempts the atomic claim for touched free tasks (so ownership lags activity by up to one sync).
- Nothing ever writes to codimango or to task files.
- **Live dashboard regions** use strong canonical-content ETags: summary/board poll every 60s, Team every 15s only
  while open, activity every 30s while visible, and Stats on open plus every five minutes. A no-change poll is a
  bodyless `304`; elapsed clocks tick locally every 15s. Task validation/history arrays load only when its drawer
  opens. `/data.json` and the self-contained `board html` export remain compatible.

## Messaging and the courier

`board msg <task> "..."` resolves the task's current owner and pins that stable session/host into the message.
Use `task:<slug>` to be explicit; session-name fragments, stable session targets, server IDs, and `all` still work.
An unowned/ambiguous task is refused with a prompt to choose a server or everyone.

Messages now show honest states: **queued → published → delivered → acked**. Publication in the shared ledger is not
called delivery. Keep one ordinary Claude session open and run `/board courier` (or `board courier`). The blocking
wait consumes no model turns; when it returns work, that session uses native SendMessage, records `board receipt`,
and re-arms. Current hooks remain a fallback and also record a delivered receipt. Codex/Muse jobs route to their
parent Claude session; unsupported interactive transports stay visibly unavailable.

The Team tab lists each native session and its stable kind icon (🟣 Claude, 🟢 Codex, 🟠 Muse), status/age/focus,
child runs, indexed total/last-hour tokens, current context pressure, transport, restart guidance, and deterministic
keep/watch/rotate/unblock advice with visible thresholds. Advice never acts automatically. Task drawers lazily read
bounded Codimango job counts. Spend says `cost unavailable` unless a matching private `[[pricing.models]]` entry and
authoritative model/token data support an estimate; unknown spend is never shown as `$0`.
Each sync overwrites the private-ledger `hosts/<host>.json` summary, letting the peer host show a bounded, redacted
session inventory and queue health without reading the other machine's home directory.

Dashboard shortcuts: `/` focuses task search, `b` opens Board, `t` opens Team, `e` expands an open drawer, and
`Esc` closes the drawer (or clears search when no drawer is open).

## Setup

First machine: create a private ledger repo with one commit, copy `config.example.toml` to
`~/.config/workboard/config.toml` and fill it in, then run `./board setup` from this directory. Commit the
config into the ledger as `config/workboard.toml` so other machines can fetch it.

Every other machine (from a checkout of this repo):

```
git pull && tools/board/board setup --ledger <private ledger git url>
```

`setup` fetches the config from the private ledger (if missing), links `board` into `~/.local/bin`, installs the
`workboard` skill into `~/.claude/skills/`, adds the hooks (backup kept), a 2-minute `board sync` cron line, and a
one-minute `board serve --ensure` watchdog, probes claim refs and does the first sync; it exits non-zero if any of
these fail. `serve --ensure` uses a per-port lock, so concurrent cron invocations cannot create duplicate servers.
Undo: `board install-hooks --uninstall` and remove the cron line.

Tests: `python3 -m unittest discover -s tests` (stdlib only, Python ≥ 3.11).
Increment-1 stress: `python3 -m tests.stress_increment1` (synthetic data only).
Increment-2 stress: `python3 -m tests.stress_increment2 --idle-seconds 60` (300 tasks, 40 sessions, 1,000 activity
items, 200 keyed refreshes, and an idle-CPU sample; synthetic data only).
Increment-3 stress: `python3 -m tests.stress_increment3` (40 sparse 200 MB transcripts, rotation, truncation,
concurrent append, reconciliation, idle byte budget, and privacy sentinel; synthetic data only).

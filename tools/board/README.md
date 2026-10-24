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
board status               # sources, ledger, claims, hooks, cron
board import-claims --dry-run   # one-time: show live rows of an old CLAIMS.md ([legacy] claims_md); drop --dry-run to import
```

## How it works

- **Sources:** codimango CLI (status, validation, review dates), git (task heads, commits), a private
  **ledger** repo (append-only per-host event files: claims, reviews, checks, session names).
- **Claims** are create-only git refs (`refs/claims/<hash>`) on the ledger remote: exactly one session wins;
  renew/steal/release are compare-and-swap on the exact commit. Expired after 24h without renewal.
- **Hooks** (Claude Code) record activity, name sessions after their tab title and block edits to a task another
  live session owns. They never touch the network and always fail open; the 2-minute background `board sync`
  then attempts the atomic claim for touched free tasks (so ownership lags activity by up to one sync).
- Nothing ever writes to codimango or to task files.

## Setup

First machine: create a private ledger repo with one commit, copy `config.example.toml` to
`~/.config/workboard/config.toml` and fill it in, then run `./board setup` from this directory. Commit the
config into the ledger as `config/workboard.toml` so other machines can fetch it.

Every other machine (from a checkout of this repo):

```
git pull && tools/board/board setup --ledger <private ledger git url>
```

`setup` fetches the config from the private ledger (if missing), links `board` into `~/.local/bin`, installs the
`workboard` skill into `~/.claude/skills/`, adds the hooks (backup kept) and a 2-minute `board sync` cron line,
probes claim refs and does the first sync; it exits non-zero if any of these fail.
Undo: `board install-hooks --uninstall` and remove the cron line.

Tests: `python3 -m unittest discover -s tests` (stdlib only, Python ≥ 3.11).

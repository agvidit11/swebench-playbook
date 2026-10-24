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
```

## How it works

- **Sources:** codimango CLI (status, validation, review dates), git (task heads, commits), a private
  **ledger** repo (append-only per-host event files: claims, reviews, checks, session names).
- **Claims** are create-only git refs (`refs/claims/<hash>`) on the ledger remote: exactly one session wins;
  renew/steal/release are compare-and-swap on the exact commit. Expired after 24h without renewal.
- **Hooks** (Claude Code) record activity, name sessions after their tab title, auto-claim free tasks and block
  edits to a task another live session owns. They never touch the network and always fail open.
- Nothing ever writes to codimango or to task files.

## Setup

First machine: copy `config.example.toml` to `~/.config/workboard/config.toml`, fill it in, create a private
ledger repo, then `board setup`. Store the config in the ledger as `config/workboard.toml`.

Every other machine (one line):

```
cd ~/swebench-playbook && git pull && tools/board/board setup --ledger ssh://git@github.com:22/<you>/<ledger>.git
```

`setup` fetches the config from the private ledger, installs the hooks (backup kept), adds a 2-minute
`board sync` cron line, probes claim refs and does the first sync. Undo: `board install-hooks --uninstall`
and remove the cron line.

Tests: `python3 -m unittest discover -s tests` (stdlib only, Python ≥ 3.11).

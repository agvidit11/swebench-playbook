You are reviewing a design doc for a terminal tool. Read tools/board/DESIGN.md (this directory: DESIGN.md) in full.
Context you may read (read-only): the free-text claims ledger the tool replaces (configured path),
the pre-submit gate it integrates (configured command), the task-snapshot script (configured path),
`codimango --help` and `codimango task list --json | head -c 3000` for the live server data shape.

Review it wearing ALL of these hats, and label each finding with the hat:
1. Terminal UI/UX expert: readability on 80/120/200-col terminals, colour schema (incl. colour-blind safety,
   NO_COLOR, light/dark themes, piping to files), glyph choice (✓✓ ○ ⟲ ▮), legend design (must be easy to read and
   discoverable), information density vs scannability, sorting/grouping, how fast a user finds "what do I do next".
2. Software design expert: architecture, data model (append-only per-server JSONL events), consistency with the
   live codimango server (the board must NEVER silently disagree with the server: detect and ALERT on drift,
   stale data, failed sync, clock skew), hooks robustness (failure must never break a Claude session), concurrency
   between two servers, testability, performance (cache codimango calls), stdlib-only constraints.
3. Engineering manager / director: does it answer "how is the workstream going", is the stats section what a
   manager wants, is `--export md` good enough to share upward; propose an export/report design (weekly report,
   per-task one-pager doc) that is one command.
4. Architect for OPEN-SOURCING later: the author wants other people (other codimango authors, maybe other
   workflows) to use it. Propose: config file (user identity, team roster, servers, task-repo paths, thresholds,
   which columns/stats they care about), a plugin/extension model for new data sources, columns, checks and stats,
   a first-run onboarding prompt that asks new users what matters to them and generates their config, and
   "stats based on what they prefer and what works for them" (e.g. suggest stats from their own history).
   Flag anything hardcoded/private (FBIDs, names, reviewer names, internal URLs) that must be separable.
5. Naming: command and concept names (board, take, free, review, seen, heartbeat...), is there clearer wording.

Also: are more stats or tools needed? What is over-scoped and should be cut or deferred? What is missing?

Output: write your review to review/codex-review-1.md with sections:
 A. Verdict (ship as-is / revise / rethink) in 3 lines.
 B. Top 10 changes ranked by value, each: problem, concrete proposal, effort (S/M/L).
 C. Per-hat findings (concise bullets).
 D. A proposed revised command list, column list, colour+glyph legend (show the exact legend text as it would print).
 E. Proposed config schema (YAML or TOML example) and plugin interface sketch (Python signatures).
 F. Export/report design (sample of the markdown it would produce, short).
 G. Open questions for the author (max 5).
Do not edit DESIGN.md or any other file except review/codex-review-1.md. Be concrete and opinionated.

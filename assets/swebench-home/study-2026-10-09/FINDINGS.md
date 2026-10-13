# What the winning MT sessions do (study 2026-10-09, agvidit-b0)
Source: subagent study of 23 accepts since 10-01 (17 MT, 12 newly sourced; lane-i did 9/12). Raw data in raw/.

## Patterns (measured)
1. Domain-first, one theme: a library's own state/identity/position bookkeeping under a SEQUENCE of edits (undo/history, change tracking, source-preserving editors, timelines, recurring series, refactoring, layered config reload). 10/13 passes.
2. Authority = "same as an existing code path" / "same as rebuilding fresh". Lay-voice instruction (~200-300w): symptom + one entry point + one authority sentence, no cases listed. Makes dozens of unstated cases fair.
3. >=3 independent fault lines per non-exempt step. Avocado misses each repo-internal line ~1/5 -> 1 line 0.8 (fail), 2 lines 0.64, 3 lines ~0.5. Many small independent lines = gradient; one big withheld line = bimodal.
4. Server is the calibration oracle: push, mine 15 server trees, union-loop test lines to 1-3/5. Local gate = bench pinned -m meta/avocado-code-flex-5.16, non-exempt steps <=1/5.
5. Use both allowances: step 1 at 1.0 exempt (3-step tasks); rule 4 (avocado 0, gpt in band) on 8/30.
6. Reshape, don't park: add fault lines when saturated; 6-12 pushes tolerated.
Grader: 10-25 parametrized hidden cases per step, all traced to the authority.

## Why our lane got 0
Single-mechanism seams (one-line fixes) in sparse ecosystems, killed on headless Muse 4-5/5 — which is the EXPECTED rate for one fault line. We released seams that needed more fault lines added.

## Don't copy their review flags
Later steps must re-run earlier steps' cases; unforgeable parser; rule-4/union lines need Codex fairness + Vidit confirm.

## Candidate directions (not in CLAIMS, prelim dedup)
1. owen-it/laravel-auditing — selective undo / point-in-time reconstruction incl. pivots
2. ical-org/ical.net — recurring-series edits (override, split this-and-following, move)
3. dart-lang/yaml_edit — source-preserving YAML edits (check monorepo)
4. (lower) briannesbitt/Carbon — editable CarbonPeriod schedules across DST
Key sources: ~/scratch/lane-i/MT-RESHAPE-BRIEF.md, BRIEF.md, cards/*.md

# Step 11b review

## 1) VERDICT: CHANGES

Items 1 and 5 from `review/step-11.md` are fixed, and most of items 2 and 4 are present. The implementation is
stdlib-only and contains no committed private values. The live `status` check recognized all three hooks and the
installed cron sync. Item 3 is not complete: date ranges affect only the weekly rows, and a valid one-sided range
crashes human output. Item 2 still labels a latest-entry measurement as first-submission cycle time and can omit the
required tasks-per-repository measure. The rank renderer also remains wider than the requested terminal width.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 280 tests in 58.767s

OK
```

## 2) Required changes

1. `workboard/stats.py:60-163`, `workboard/__main__.py:513-609`, `tests/test_stats.py:90-113`, and
   `tests/test_cli.py:298-332` — Finish item 3's window contract. `stats --from 2026-10-01` currently raises
   `TypeError` while formatting a missing end, the displayed/JSON `to` is the internal exclusive next-day bound,
   and `week_numbers`, funnel, flow, pipeline/quality summaries remain all-time even when a range is selected.
   Keep the user-facing inclusive dates separate from the internal `[start, end)` instants; reject timestamps with
   `t >= end`; apply the window to every dated headline/flow/funnel/cohort measure, and explicitly label undated
   snapshot measures as all-time rather than implying they are ranged. Add from-only, to-only, exact-midnight
   exclusion, and out-of-window derived-metric regressions for both human and JSON output.

2. `workboard/stats.py:146-194`, `workboard/__main__.py:518-520,542-557`, and `tests/test_stats.py:103-113` —
   Finish item 2's authority/availability requirement. `DEFINITIONS` promises first-submission cycle time while
   `cycle_and_wait()` says it measures from the latest pool entry; do not publish that value as first-submission
   cycle time unless `enteredPoolAt` is authoritatively the first submission. Otherwise render it unavailable with
   source/coverage. Also always expose tasks-per-repository as a structured result and human line; when repositories
   or readable `config.json` inputs are absent, report `unavailable` plus reason and `0/N` coverage instead of
   omitting the measure/returning bare `null`. Add focused unavailable and resubmission tests.

3. `workboard/__main__.py:496-510,569-570,639-640` and `tests/test_cli.py` — Complete item 4 for standalone
   rank output. `_rank_table()` emits 88-character lines at widths 20 and 40 (and 72 characters at width 60): the
   first column is admitted even when it cannot fit, and the omitted-columns message is never wrapped by `cmd_rank`.
   Budget the first column against the actual width, truncate cells/header safely, wrap the disclosure line, and add
   `rank --plain --width 40/60` tests asserting every line fits and every hidden column name remains disclosed.

4. `workboard/rank.py:31-91` and `tests/test_stats.py:120-170` — Stabilize the rank API that later weekly reports
   consume. The signed-off interface is rows with `scope, window, metric, value, rank, of`, but imports currently
   require only `scope`, tests and documentation use `win`, and `valid_rows()` accepts arbitrary/inconsistent maps.
   Normalize supported DaiQuery/legacy column names into the documented schema at ingestion (or revise the signed-off
   interface), validate every row, and cache only normalized rows. Add missing-key, inconsistent-row, and canonical
   CSV/Markdown tests so reports need not reverse-engineer arbitrary columns.

5. `workboard/__main__.py:299-339` and `tests/test_cli.py` — Make the new status checks obey the read-command
   contract. Human output checks hooks/cron, but `status --json` returns before computing them, `--strict` ignores a
   failed hook/cron/dependency check, and any cron entry containing `board sync` is accepted regardless of its
   schedule. Compute one structured checks result for both renderers, verify the expected two-minute active command,
   include it in JSON, and make failed checks affect strict status. Add malformed settings, wrong cron cadence, JSON,
   and strict-exit regressions.

## 3) Optional suggestions

1. `workboard/stats.py:226-252` — Give `--quality` a command-wide deadline/progress indication; up to 400 sequential
   60-second subprocess timeouts can otherwise look hung for hours.
2. `workboard/stats.py:166-194` — Either use the injected `runner` argument for deterministic tests or remove it;
   the current dead parameter suggests this filesystem/Git path is testable when it is not.
3. `workboard/stats.py:137-143` — Document the percentile interpolation convention so later reports reproduce the
   same p50/p75 values.

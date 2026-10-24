# Step 11 review

## 1) VERDICT: CHANGES

The live summary is generally scannable and its hand-checked weekly totals (W41 19, W42 12, W43 13) are
credible. The implementation is stdlib-only and contains no private values. The step-10b item is fixed:
stdout and stderr use independent incremental UTF-8 decoders, only a bounded stdout tail is parsed, and the
three requested regressions now cover split multibyte input, stderr flooding, and the parser-tail bound.

Task 11 still diverges from the signed-off stats contract in several user-visible ways: the code broadens the
definition of accepted, omits required flow/funnel measures and date-range options, clips the required
definitions out of the live output, and can crash on valid-but-unexpected rank JSON/cache shapes.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 240 tests in 140.308s

OK
```

## 2) Required changes

1. `workboard/stats.py:34-49,67-77,103-117` and `tests/test_stats.py:26-60` — Apply the stated definition
   literally: accepted means the current Codimango status is `accepted` or `used_in_training`, dated by
   `reviewedAt`. Do not add `status_before_archive` records to weekly, all-time, or funnel accepted counts;
   keep those visible only in `archived_after_accept`. Change the fixture assertions to W41 = 19 and funnel
   accepted = 41, matching the fixture comment and plan. Likewise, submitted is defined solely by a valid
   `enteredPoolAt`; remove the unrelated `status != draft` gate and add a boundary test for that definition.

2. `workboard/stats.py:52-128`, `workboard/__main__.py:488-548`, and `tests/test_stats.py` — Complete the
   DESIGN.md section 10 stats surface instead of exposing only weekly counts and age: add cycle-time p50/p75
   from first submission to acceptance, reviewer-wait, and tasks-per-repository in the exact funnel, and expose
   each measure in both human and JSON output with focused tests. Preserve the already useful submitted versus
   accepted weekly series as arrivals versus completions. If a required measure lacks an authoritative input,
   render it as unavailable with its coverage/source rather than silently omitting or estimating it.

3. `workboard/__main__.py:534-548,663-665`, `workboard/stats.py:52-94`, and `tests/test_stats.py` — Implement the
   documented `stats [--from DATE] [--to DATE] [--json]` interface. Parse ISO dates in the configured timezone,
   reject reversed/invalid ranges, and apply the same inclusive/exclusive bounds consistently to weekly,
   headline, funnel-derived period measures, and JSON output. Add parser and PT week-boundary regressions.

4. `workboard/__main__.py:522-531,539-545` and `tests/test_stats.py` — Do not silently slice every rendered line.
   The supplied live output demonstrates that the mandatory Definitions line is cut off, contradicting
   “definitions are printed with every stat”; wide rank rows can lose fields the same way. Wrap prose, choose a
   width-aware set/layout for tabular columns, and include the definitions/source metadata in JSON. Add a narrow
   non-TTY rendering test that reconstructs and asserts the complete definitions without any dropped field.

5. `workboard/rank.py:31-36,58-78`, `workboard/__main__.py:522-529,565-583`, and `tests/test_stats.py:90-127` —
   Validate the decoded external/cache shape before indexing it. `refresh()` currently raises on valid JSON such
   as `42` or `{\"rows\": {}}`, while `load()` accepts `{\"rows\": []}` and both rank renderers then dereference
   `rows[0]`. Accept only a non-empty list of mappings (or return a clear “unexpected/no rows” result), fall back
   safely from a corrupt cache, and add scalar, wrong-typed `rows`, empty-list, and non-mapping-row regressions.

## 3) Optional suggestions

1. `workboard/stats.py:149-175` — Give `--quality` a command-wide deadline/progress signal; 400 sequential
   60-second subprocess timeouts can otherwise make an interactive stats command appear hung for hours.
2. `workboard/__main__.py:663-665` — Require `--weeks > 0` and cap it to a defensible display/history limit.
3. `workboard/stats.py:84-94` — Exclude or explicitly flag acceptance timestamps later than `now` so a bad future
   timestamp cannot inflate “this week” and all-time figures.
4. `workboard/__main__.py:495-508` — Expand MT/ST and define “imported” in the manager-facing legend.

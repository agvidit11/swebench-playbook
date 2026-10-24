# Step 6 review

## 1) VERDICT: CHANGES

The live board is action-first and easy to scan: ATTENTION / READY / WAITING grouping is clear, the compact
column selection is useful to an engineering manager, task-name middle truncation works, and the legend
explains the values actually present. The task-5 sequence-watermark, required-field, drift-priority,
activity-does-not-renew, CLOCK_SKEW, and NONOWNER_COMMIT regressions are covered and pass. The reviewed
implementation is stdlib-only and contains no committed private values.

Task 6 is not ready to approve because the renderer does not actually honor the requested width outside the
table, the public renderer signature and several command forms do not match the planned interfaces, and most
read commands silently discard the health / JSON / strict contracts. The live sample demonstrates the width
problem: line 2 is 124 columns. A direct 80-column render with the real header and representative legend emits
120- and 98-column lines.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 106 tests in 9.568s

OK
```

## 2) Required changes

1. `workboard/render.py:138-183,202-208`, `workboard/stats.py:29-41`, and `tests/test_render.py:45-50` — Make
   `width` a contract for the complete plain render, not just table rows. The week header, warnings, failed
   health detail, and legend currently ignore it (`legend` hard-codes 110), so the specified 80-column piped
   output and even the 120-column live sample overflow. Wrap these prose lines on word boundaries with aligned
   continuation indentation (do not truncate warnings or NEXT), and make the legend wrap at the supplied
   width. Extend the 80-column test to include the week header, a warning, failed health, and all representative
   legend tokens, then assert every ANSI-stripped line is at most 80 columns. Add the same assertion for the
   real 120-column compact shape and the 200-column wide shape.

2. `workboard/render.py:202-203`, `workboard/__main__.py:82-84`, and `tests/test_render.py:23-25` — Publish the
   Task 6 renderer interface instead of requiring callers to know the internal `Style` and clock plumbing.
   The plan promises `render_list(views, health, cfg, *, width, color, unicode) -> str`; the implementation has
   no `cfg`, requires `now` and `style`, and therefore will break later callers written to the plan. Expose the
   promised signature (additional optional `wide`, `show_all`, header/sync inputs are fine), perform style
   detection inside that boundary, and keep any deterministic clock/style injection on a private helper used
   by tests.

3. `workboard/__main__.py:271-304` and `tests/test_render.py:99-115` — Implement and test the documented read
   command grammar. Today `list --group attention`, `show <task> --history`, `show <task> --sources`,
   `available --reason expired`, and `plugins list` all exit 2 as unrecognized arguments. Add the options and
   honor their semantics: grouping choices `attention|state|owner`, opt-in history and source detail for show,
   available filtering for `never-claimed|expired|released`, and a `list` action for plugins. `doctor` may
   remain folded into `status` per the stated scope cut. Add parser and behavior regressions; the requested
   suite currently contains no CLI tests at all.

4. `workboard/__main__.py:38-46,77-86,89-95,98-245` — Enforce the read-command health contract consistently.
   `show`, `explain`, `available`, and `changes` gather potentially cached/unhealthy data but print no health
   banner and always return 0 under `--strict`; `explain`, `changes`, `status`, `legend`, and `plugins` accept
   `--json` but ignore it; list JSON omits global findings and ledger sync state. Centralize source-backed read
   completion so human output starts with the health banner, JSON contains stable `health`, `sync_state`, and
   global `findings` data alongside the command result, and every gathering command returns nonzero under
   `--strict` when `_unhealthy` is true. A failed/timed-out lazy human-review fetch must also render an explicit
   unavailable warning instead of being silently omitted. Add unhealthy-cache tests for both human and JSON
   output and strict exit codes across these commands.

5. `workboard/projection.py:136-166,207-219,233-254`, `workboard/render.py:168-169`, and
   `tests/test_projection.py:119-134,154-164` — Finish the Task 5 finding contract. `STALE_VALID` is emitted as
   a Finding even though Task 5 says finding codes are exactly the documented set. For a non-document change
   where git head differs from the codimango commit, emit and display `HEAD≠SERVER`; reserve
   `VALID≠SERVER` for `validationCommitSha != commitSha`, remove the private `STALE_VALID` finding branch and
   legend token, and keep `OK·doc` only as the deliberate cell exception. Also route `CLOCK_SKEW` and
   `NONOWNER_COMMIT` warnings to ATTENTION before the draft ladder (for example, `CHECK clock` and
   `RESOLVE ownership`); currently the tests prove only that a Finding exists while the task remains READY.
   Assert both documented codes and `(group, next)` in the regressions.

6. `workboard/projection.py:53-82` and `tests/test_projection.py:112-117` — Complete the prior review's
   liveness fix exactly: an `assign` ledger event still creates or refreshes an OWNED claim, although step 5
   required freshness to come only from `claim` / `renew` / `steal` until verified claim-ref health arrives in
   Task 7. Remove `assign` from the liveness tuple for now and add a regression showing that an assign by itself,
   or after an expired claim, does not produce OWNED.

## 3) Optional suggestions

1. `workboard/app.py:98-101` — Dedupe ledger and provisional spool events together by `event_id`; after an
   uncertain successful push, the same logical event can currently appear once from the ledger and once from
   the retained spool.

2. `workboard/projection.py:43-50` — Make repeated observations deterministic using `observed_at` and authority
   rather than input-order `dict.update`, especially because `explain` presents the result as trustworthy
   source reasoning.

3. `workboard/__main__.py:61-65` — Replace the last-look file atomically (`tempfile` plus `os.replace`) so a
   killed list render cannot erase the baseline used by `changes`.

4. `workboard/render.py:163-170` — In manager-facing text, label R0/R1/R2 as “agent-session review” so R0 beside
   `WAIT reviewer` is not mistaken for “no human/server review.”

# Step 6b re-check

## 1) VERDICT: CHANGES

The author’s reasoning on prior item 5 is sound: when `codimango.head_commit_sha` equals the Git task head,
the server has seen that head, so calling the condition `HEAD≠SERVER` / “newer push not on server” would be
false. Adding `STALE_VALID` to DESIGN §2 is the right model for “server saw head, but validated an older
commit and non-doc files changed.” The implementation does not yet enforce that premise, however: it can
emit `STALE_VALID` without equality and can emit `HEAD≠SERVER` despite equality when the repo timestamp map
is incomplete.

Prior item 2 is done: the promised public `render_list(views, health, cfg, *, width, color, unicode)` boundary
exists. Prior item 6 is done: only `claim` / `renew` / `steal` establish liveness, with regressions for an
assign alone and an assign after expiry. The main wrapping work in item 1 and the shared envelopes/strict
handling in item 4 are substantially improved, but the cases below leave items 1, 3, 4, and 5 incomplete.
The reviewed Python remains stdlib-only, and I found no private values embedded in the reviewed code.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 120 tests in 9.281s

FAILED (errors=1)
```

The sole error is discovery/import of the out-of-scope `tests/test_claims.py`: `ImportError: cannot import
name 'claims' from 'workboard'`. All 119 tests that loaded passed, including the scoped renderer, CLI, and
projection tests, but the required repository-level command is not green.

## 2) Required changes

1. `workboard/projection.py:197-223` and `tests/test_projection.py:149-178` — Make the three-SHA decision
   encode the accepted `STALE_VALID` rationale directly. If `git.task_head == codimango.head_commit_sha`,
   the result must never be `HEAD≠SERVER`, even when `git.commit_time_by_sha` lacks that SHA; classify
   non-doc changes since `commit_sha` as `STALE_VALID` and doc-only changes as `OK·doc`. Emit
   `STALE_VALID` only when that equality proves the server saw the Git head. When the heads differ, use the
   available ordering evidence for `HEAD≠SERVER` and do not fall through to `STALE_VALID`. Also emit
   `VALID≠SERVER` whenever non-empty `validation_commit_sha != commit_sha`; the current `valid != "RUN"`
   exception silently drops a documented disagreement. Add negative regressions for equal heads with a
   missing timestamp-map entry, unequal heads with `git.changed_since_validated`, and a running validation
   whose commit differs.

2. `workboard/render.py:263-278` and `tests/test_render.py:52-68` — Finish the complete-render width contract
   for the newly supported grouping modes. `--group owner` writes the raw owner/alias as a group heading, so
   a long session title produces a line wider than `width` even though the owner cell itself is bounded.
   Wrap the group heading without losing its text (the same handling should cover arbitrary state labels),
   and extend the 80/120/200 line-length regression to exercise `group="owner"` with a long alias.

3. `workboard/__main__.py:132-167,226-247,371-378` and `tests/test_cli.py:45-80` — Complete prior item 3’s
   documented grammar and opt-in semantics. A plain `show <task>` still prints and returns the last 15 ledger
   events; omit history unless `--history` is present. Accept the documented timestamp form of
   `changes --since 2h|<ts>` in addition to durations, including timezone validation. Add `plugins doctor`
   and make it report plugin load/API failures with a useful exit status instead of rejecting the command.
   Add behavior tests for all three cases; the current parser-only test does not establish their semantics.

4. `workboard/__main__.py:114-167,323-329` and `tests/test_cli.py:65-75` — Finish prior item 4’s read/JSON
   contract. `config show --json` currently emits a leading comment followed by JSON, and
   `config validate --json` emits plain text, so neither is machine-readable as promised by DESIGN §8.
   Emit one valid JSON document for both actions. In addition, a failed/timed-out lazy reviews fetch makes
   `show --strict` return 0 and leaves the JSON `health` object healthy; represent that fetch as explicit
   health/finding data so the human banner, JSON envelope, and strict exit status agree. Test JSON parsing
   for both config actions and strict/JSON behavior for review-fetch failure.

## 3) Optional suggestions

1. `workboard/__main__.py:103-109` — Have `cmd_list` call the public `render_list` boundary so production use,
   not only a signature test, protects the interface later tasks depend on.

2. `workboard/projection.py:53-55` — Remove `assign` from the `_claims` docstring now that it correctly no
   longer establishes liveness.

3. `workboard/projection.py:43-50` — Resolve repeated observations by authority and `observed_at` rather than
   input-order `dict.update`, so projection and `explain` remain deterministic.

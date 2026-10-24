# Step 5 review

## 1) VERDICT: CHANGES

The repo-wide commit-time map implements the agreed `HEAD≠SERVER` comparison, `round` correctly remains
`None`, the reviewed code is stdlib-only, and it contains no private values. The five requested step-4
fixes are present (stable spool lock, full-history git scan, configured-remote refresh, shared 20-second
deadline, and deterministic worker/retry tests), but the retry path still breaks the per-host sequence
contract on the next sync. Task 5 also does not yet publish the promised `TaskView` field shape and omits
two specified findings.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 99 tests in 9.209s

OK
```

The 33 tests in `test_projection`, `test_sync`, and `test_git` also pass independently. The green suite
does not cover the failures below.

## 2) Required changes

1. `workboard/sync.py:113-115` and `tests/test_sync.py:64-85` — Preserve monotonic, unique per-host
   sequence numbers after an uncertain successful push. `_last_seq()` calls `read_events()`, which dedupes
   repeated `event_id`s before taking the maximum. After the existing lying-push test, the physical ledger
   contains the first copies at seq 1–3 and retry copies at seq 4–6, but `_last_seq()` reports 3; the next
   unique event is stamped 4, reusing a sequence number and making the writer log non-monotonic. Compute the
   allocation watermark from every valid physical record (before event-id dedupe), or retain the original
   stamp across retries. Extend the regression by appending and syncing one new event after the uncertain
   retry, then parse the raw JSONL and require strictly increasing, unique physical sequence numbers while
   `read_events()` still returns one logical copy per `event_id`. A direct reproduction currently yields
   physical seq values `[1, 2, 3, 4, 3]`.

2. `workboard/projection.py:202-215` and `tests/test_projection.py:102-136` — Match the Task 5 interface
   before render/show code depends on private aliases. Every `TaskView.fields` must contain the documented
   `claim_health` and `pushes` keys; the implementation instead exposes `owner_state`, `pushes_draft`, and
   `pushes_after`. Publish `claim_health` (the current FREE/OWNED/EXPIRED/CONFLICT/DONE state is sufficient
   for this step) and one stable `pushes` value containing the before/after-submit counts. Prefer the plan's
   names `pushes_before_submit`/`pushes_after_submit` for any retained numeric detail, and add one assertion
   that the full required key set is present for both a codimango task and a git-only task.

3. `workboard/projection.py:127-155,182-195` and `tests/test_projection.py:79-100,138-146` — Make drift a
   real NEXT precondition and add the requested priority-order test. `VALID≠SERVER` is recorded but ignored
   by `_next()`, so a draft with stale validation can progress through checks/reviews to `SUBMIT`; and
   `HEAD≠SERVER` is placed in READY even though DESIGN §9 says findings belong in ATTENTION. Handle both
   drift codes ahead of the draft ladder (`HEAD≠SERVER` → ATTENTION/RERUN server;
   `VALID≠SERVER` → WAIT validation while running, otherwise ATTENTION/RERUN server). Replace/expand
   `test_next_priority_draft_ladder` into `test_next_priority_order` covering competing conditions plus the
   complete required ladder `RUN check → GET R1 → GET R2 → SUBMIT`.

4. `workboard/projection.py:45-73` and `tests/test_projection.py:107-122` — Do not renew a claim from
   ordinary task activity. A recent `touch`, `check`, or `review` currently makes an old claim look OWNED for
   another 24 hours, contrary to DESIGN §5: only a successful claim-ref heartbeat can refresh liveness and a
   ledger-only heartbeat is insufficient. Track freshness only from `claim`/`renew`/`steal` audit events for
   now (and let Task 7 replace it with ref-health input); add a regression where an old claim followed by a
   recent touch/check/review remains EXPIRED.

5. `workboard/projection.py:158-216` and `tests/test_projection.py` — Implement and test the two
   projection-owned finding codes promised by Task 5 but absent everywhere: `CLOCK_SKEW` and
   `NONOWNER_COMMIT`. Emit `CLOCK_SKEW` when a task event is ahead of `now` by more than
   `cfg.claims.clock_skew_warn_seconds`, and do not use that event to establish claim freshness. Emit
   `NONOWNER_COMMIT` only from explicit modification evidence (for example, a `touch` carrying a non-null
   commit after a sole live claim, from a different session); do not misclassify checks or reviews merely
   because they carry a commit SHA. Add positive and negative tests for both findings.

## 3) Optional suggestions

1. `workboard/projection.py:35-42` — Make repeated observations deterministic. `_merge()` currently ignores
   `Observation.observed_at` and `authority` and silently lets input order overwrite the same namespaced
   field, which will make `explain` difficult to trust.

2. `workboard/projection.py:186-191` — Distinguish “comparison unavailable” from `sync == "OK"`. A missing
   repo map or a server SHA absent from the map currently reports OK even though drift was never checked.

3. `workboard/sources/gitsrc.py:40-69` — The full-history map is correct, but it will become the dominant
   refresh cost on large repositories; after correctness is locked, cache it by fetched ref tip or build it
   incrementally without changing the observation contract.

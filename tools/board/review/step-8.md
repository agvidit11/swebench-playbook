# Step 8 review

## 1) VERDICT: CHANGES

The create-only claim race works: the two-clone test produces exactly one `ACQUIRED` and one `LOST`, and the
claim-ref source gives the projection an authoritative owner when its fetch is healthy. The code is stdlib-only,
and I found no committed private identities, hosts, paths, URLs, or reviewer names in the reviewed files.

The Task 7 fixes cover remote-specific probe gating, owner-checked heartbeat/release, explicit steal health
parameters, reboot-safe grace, and the configured live-claim count. One probe-cleanup edge from step 7 remains,
and Task 8 bypasses the new steal-health contract at its caller. The human-shell release is CAS-safe against a
concurrent tip change, but it is not explicit or auditable enough for the publishable core: it rewrites the
caller's session identity and has no representation of “same person.”

Requested command: `python3 -m unittest discover -s tests -v`

```text
======================================================================
ERROR: test_hooks (unittest.loader._FailedTest.test_hooks)
ImportError: cannot import name 'hooks' from 'workboard'

----------------------------------------------------------------------
Ran 153 tests in 35.745s

FAILED (errors=1)
```

`tests/test_hooks.py` appeared concurrently with this review and is outside Task 8; all discovered Task 1–8
tests passed. Findings below are against Task 8 commit `1c4c2eb` plus the requested Task 7 re-check.

## 2) Required changes

1. `workboard/coord.py:42-48` and `tests/test_claim_cli.py:65-69` — Make mutation freshness genuinely
   fail closed. A busy sync currently falls back to an arbitrarily old `sync-state.json` and can return `True`
   from an earlier successful pull; a current pull followed by a failed push is also accepted. Return failure
   immediately when `sync()` reports `busy`, and require the current run to complete both pull and push (with no
   unsynced ledger error) before claim/release proceeds. Add regressions for a busy worker with cached
   `last_pull_ok=True` and for `last_pull_ok=True, last_push_ok=False`; exercise both commands, not only this
   helper.

2. `workboard/coord.py:51-59` and `workboard/__main__.py:347-358` — Do not assert steal safety without
   evidence. `coord.claim(..., steal=True)` always passes `source_healthy=True`, while
   `clock_healthy=True` is the default, so the CLI bypasses the explicit health preconditions added in Task 7.
   Remove those permissive defaults, pass fresh claim-source and clock-health evidence from the command, and
   refuse stealing when either is absent/unhealthy. Add command-level tests for unhealthy claim source and clock
   skew; neither may start or complete the grace period.

3. `workboard/coord.py:22-35,89-116` and `tests/test_claim_cli.py:29-63` — Make the local renewal registry
   correct across sessions and processes. When `--to` assigns a claim on host 1 to a session on host 2, host 2's
   first touch sees a matching remote `HELD` claim but never adopts its OID into `claims-local.json`, so it never
   heartbeats and the claim expires. Adopt a valid remote claim when its owner session matches the touching
   actor, then renew from its authoritative OID when due. Also protect every `_local` read/modify/write with one
   `flock` transaction; concurrent same-host claims can currently overwrite each other's entries. Test
   cross-host assignment followed by renewal and two concurrent same-state-dir updates.

4. `workboard/sources/claimrefs.py:37-54` and `workboard/projection.py:180-186,255-265` — Do not report a
   partial/corrupt claim-ref snapshot as healthy. The source silently skips malformed payloads and silently
   truncates above `max_live_claims`; the projection then treats omitted tasks as `FREE`. It also treats a claim
   with a missing, invalid, or future-dated `renewed_at` as `OWNED`. Validate the complete payload and that each
   payload's entity hashes to the fetched ref, check the listing command, and make malformed/overflow/clock-skew
   snapshots unhealthy with a finding so projection falls back to explicitly advisory ledger data. Add source
   and projection regressions for each case.

5. `workboard/coord.py:71-85` — Make the human-shell override explicit and preserve the real audit actor.
   Today any caller labelled `kind="human"` has its `session_id` replaced with the owner's session ID; the
   release event consequently impersonates the agent session, and a malformed owner payload raises at
   `cur.owner["session_id"]`. Model this as a separately named owner-override operation that still validates the
   entity, owner, and exact OID, verifies the configured person relationship (store a stable configured user ID
   in new claim payloads, or define an equivalent explicit invariant), and records the human actor plus the
   released owner separately. Malformed ownership must return `REFUSED`, not raise. Test same-person human
   release, a non-matching person, malformed payload, and a concurrent renewal.

6. `workboard/claims.py:185-220` and `tests/test_claims.py:52-66` — Finish the step-7 partial-probe cleanup
   requirement. `tip` is assigned only after create/read verification, so a create push that succeeds remotely
   but reports failure (or is followed by a failed exact read) leaves a `probe-*` ref behind. Treat the candidate
   OID as a possible remote tip as soon as the push is attempted and always perform an exact-OID leased cleanup
   in `finally`; that deletion is safe even when the ref was never created. Add an uncertain-create regression
   that verifies no probe ref remains before trying the fallback namespace.

7. `workboard/__main__.py:334-367`, `workboard/identity.py:50-57`, and
   `tests/test_claim_cli.py:29-35,65-69` — Add the Task 8 CLI tests that the plan calls for. The current
   “claim to other session” test calls `coord.claim` directly and never tests alias-fragment resolution, parser
   wiring, task-fragment resolution, exit status, or output; the stale-ledger test likewise never invokes
   `cmd_claim`/`cmd_release`. Drive the public command with unique, missing, and ambiguous alias fragments and
   preserve the target actor's recorded `kind` and `host` instead of reconstructing every alias match as a
   Claude session from display text. This actor shape is consumed by later contribution/reporting work.

## 3) Optional suggestions

1. `workboard/sync.py:165-166` — Replace the mutable one-element `AUTO_CLAIM` global with an explicit injected
   option or dependency; its present shape obscures production behavior and test control.

2. `workboard/coord.py:37-39,61-68,81-85` — Surface a failed `spool_append`. A successful ref mutation with a
   silently missing audit event violates the audit contract even though rolling the ref back would be unsafe.

3. `workboard/sources/claimrefs.py:23-43` — Hide `_repo` and `_git` behind a small public claim-store reader so
   later sources do not depend on private plumbing from `claims.py`.

4. `tests/test_claim_cli.py:1,13,16,44` — Expand grouped imports, semicolon-separated statements, and list-
   comprehension side effects; conventional setup makes the concurrency tests easier to audit.

5. `workboard/sync.py:240-251` — Preserve and expose `auto_claims()` notes (especially `LOST`/`PENDING`) in
   sync state instead of discarding them, so operators can understand why a touch did not become ownership.

# Step 7 review

## 1) VERDICT: CHANGES

The create-only acquire and explicit-OID CAS mechanics are sound, including resolution of an uncertain push,
descendant commits for renew/steal, and a two-interval monotonic grace check. The real-ledger probe result is
also consistent with the local bare-remote coverage. The implementation is stdlib-only and contains no private
values.

All four required Task 6b changes are now implemented and covered: the three-SHA projection cases,
width-safe owner grouping, the documented read-command behavior, and JSON/health/strict consistency.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 136 tests in 26.707s

OK
```

## 2) Required changes

1. `workboard/claims.py:63-67,152-194` and `tests/test_claims.py:26-63` — Enforce the DESIGN §5 rule that
   claims remain disabled until a probe passes **for the exact configured remote**. `_prefix()` currently
   defaults to `refs/claims`, so every operation works without any probe (as the existing acquire tests
   demonstrate), and a cached result remains trusted after `cfg.ledger.remote` changes. Persist a
   non-sensitive remote fingerprint with the successful prefix, reject claim operations when that record is
   absent/malformed/mismatched, and only record success after exact reads confirm the renewed tip and the
   deletion. Add regressions for acquire-before-probe, failed probe, remote change, fallback-prefix selection,
   and renew/delete verification; ensure a partially successful probe cleans up its temporary ref.

2. `workboard/claims.py:197-221` and `tests/test_claims.py:65-79` — Do not let `release` bypass ownership and
   steal grace. `actor` is currently unused by `release`, so actor 2 can read actor 1's current OID, delete the
   fresh claim successfully, then acquire the now-free ref. Validate that the observed commit has a complete
   claim payload for this `entity_id`, and require the calling `session_id` to match for both heartbeat and
   ordinary release; an empty/malformed payload must fail closed instead of allowing heartbeat to replace it.
   Return `REFUSED` without changing the ref on a mismatch. Add tests for foreign release with the correct OID,
   foreign heartbeat, wrong-entity payload, and missing/malformed `claim.json`. If DONE reconciliation needs
   non-owner deletion, expose that as a separately named, explicitly constrained operation.

3. `workboard/claims.py:239-264` and `tests/test_claims.py:81-103` — Complete the steal safety preconditions.
   `steal()` neither accepts/checks claim-source and clock health nor validates `renewed_at`; malformed or naive
   timestamps can raise, and a bad local clock can make a live claim stealable. Require explicit healthy-source
   and healthy-clock evidence from the later command/sync caller, validate a timezone-aware timestamp and the
   full payload/entity identity, refuse future skew beyond `clock_skew_warn_seconds`, and return `REFUSED`
   rather than raising when any check fails. Add negative tests for each condition.

4. `workboard/claims.py:224-266` and `tests/test_claims.py:81-103` — Make the persisted monotonic grace record
   safe across reboots. Comparing only saved and current `time.monotonic()` values can incorrectly retain a
   pre-reboot timer whenever the new uptime happens to exceed the old saved value. Store a boot identity (or an
   equivalent wall/monotonic epoch guard) with each observation and restart grace when it changes. Add a
   simulated reboot regression as well as the existing changed-tip regression.

5. `workboard/claims.py:188-194` and `tests/test_claims.py:31-53` — Enforce
   `cfg.claims.max_live_claims`. Acquire currently creates unlimited live refs despite the configured/design
   bound. Before a new foreground acquire, count live refs under the probed namespace (excluding probe refs)
   and return `REFUSED` at the limit; retain create-only push as the authority for the target ref. Test below,
   at, and above the configured bound. Namespace enumeration must stay out of hooks.

## 3) Optional suggestions

1. `workboard/claims.py:197-211` — Rename `observed_oid` to `expected_oid` and make it keyword-only, or add a
   small owner-checked read-and-CAS wrapper, so Task 8 callers cannot accidentally pass a stale/unrelated value.

2. `workboard/claims.py:81-99` — Check `hash-object` and `mktree` return codes and handle `OSError` in `_git`,
   returning a fail-closed result rather than relying on a later plumbing command to fail less clearly.

3. `tests/test_claims.py:1,14` — Expand the compressed imports and semicolon-separated setup statements; this
   test module is short enough that conventional formatting would improve open-source readability.

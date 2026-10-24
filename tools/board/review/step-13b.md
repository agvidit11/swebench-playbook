# Step 13b re-check (step-13 items 1–9 only)

## 1) VERDICT: CHANGES

Items 1, 3, and 5 are fixed, and the main fixes for items 2, 4, 6, 7, and 8 are present. The branch is
stdlib-only and the full requested suite passes. It is not ready to approve yet: release can still lose its audit
event silently, claim renewal erases an existing `NONOWNER_EDIT`, rank normalization accepts invalid values, setup
can succeed without installing `board`, `import-claims --days` disagrees with projection, and one tracked review
brief still contains personal/private paths. No `review/*.log` file is tracked, `.gitignore` excludes them, and no
raw log was read during this review. Because of the tracked review brief, I cannot yet confirm that every tracked
file is free of identities, hosts, personal paths, internal URLs, and reviewer names; the focused scan otherwise
found only neutral placeholders/examples.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 355 tests in 133.048s

OK
```

## 2) Required changes

1. `workboard/coord.py:103-127`, `workboard/__main__.py:417-426`, and `tests/test_cli.py` — Preserve and expose a
   failed release audit append. Both ordinary and own-agent release discard `record(...)`'s boolean result, so a
   full/unwritable spool followed by a clean no-op sync makes `board release` exit 0 with no audit event. Return an
   explicit `audit_queued` result (or add the same warning detail used by `claim`), make JSON report it, and make the
   command exit 3 after a successful ref deletion whenever enqueue or push failed. Add ordinary and own-agent
   regressions with `record=False`, plus the existing push-pending case.

2. `workboard/projection.py:61-93,184-192,293-300` and `tests/test_projection.py` — Track claim acquisition and
   renewal separately. `_claims()` advances its sole `at` timestamp on every renewal, and `_ref_claim()` returns
   `renewed_at` as the ownership start. Consequently, an Edit/Write touch made during the claim disappears from
   `NONOWNER_EDIT` after the owner renews. Use renewal only for expiry and use the claim/steal time (or
   `claims.acquired_at`) as the lower bound for foreign edits. Test claim → foreign Edit → renew for both ledger
   fallback and authoritative ref observations.

3. `workboard/rank.py:40-78` and `tests/test_stats.py:211-218` — Make canonical rank validation actually
   integer-or-null and internally consistent. `_num()` currently truncates `1.5`, converts `True` to `1`, converts
   an invalid string to null, accepts whitespace-only scope/window, and `_row_ok()` permits `rank > of` whenever
   `value == 0`. Parse only integers or integer CSV strings, preserve only explicit nulls as null, strip/reject empty
   labels, require `of >= 1` when ranked, and always require `1 <= rank <= of`. Add a regression for each rejected
   shape for canonical and wide input.

4. `workboard/__main__.py:299-322,776-805` and `tests/test_cli.py:371-466` — Finish truthful rollout checks. Setup
   currently exits 0 when `~/.local/bin/board` or the skill destination is an unrelated regular file, so neither
   promised install occurs. It also removes every cron line matching `\bboard sync\b`, including unrelated tools,
   while status accepts any hook command matched by the broad `_ours()` regex rather than this checkout's exact
   command. Refuse destination conflicts (or verify an exact existing install), catch/report filesystem failures,
   replace only the exact managed cron entry, and validate the exact three hook commands from `board_path()`.
   Add idempotence, regular-file conflict, stale-hook-path, and unrelated-cron-preservation tests.

5. `workboard/__main__.py:706-738`, `workboard/projection.py:272-280`, and `tests/test_legacy.py` /
   `tests/test_cli.py` — Carry `--days` into the imported note's expiry contract. Import accepts 1–90 days and says
   the advisory owner lasts that many days, but projection hardcodes seven days; a 14-day-old row selected with
   `--days 30` is immediately rendered FREE, while `--days 1` can remain visible for seven days. Record an explicit
   expiry timestamp (with a seven-day compatibility fallback for old notes), project against it, and test non-default
   short and long windows.

6. `review/codex-brief-1.md:2-3` — Complete the item-9 tracked-file scrub. Remove or neutralize the private ledger
   reference `../../ledger/CLAIMS.md` and the personal tool paths under `~/swebench/`; describe them as configured
   inputs/placeholders instead. Re-run the privacy scan over `git ls-files tools/board` (excluding no tracked file)
   for identities, real hosts, personal/absolute checkout paths, repository/internal URLs, and reviewer names.

## 3) Optional suggestions

None.

# Step 2 review

## 1) VERDICT: CHANGES

The Task 1 required fixes in `workboard/config.py`, `workboard/model.py`, and `workboard/registry.py` are present and correct: nested paths load, reports configuration exists, `TaskView.health` is typed and isolated, every `Finding` requires an action and validates severity, recursive config types are checked, and duplicate plugin registrations are handled. The reviewed code is stdlib-only and contains no private values.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 30 tests in 0.051s

OK
```

Task 2 still needs changes because malformed ledger data can escape validation and crash the whole read, and two spool limits can report success without satisfying their contracts.

## 2) Required changes

1. `workboard/events.py:71-105` — Validate the complete committed-event shape before inserting a row into `seen`. At minimum, require a valid UUID event ID; non-empty string `host_id`; an integer (not boolean) non-negative `seq`; present, timezone-aware ISO `occurred_at` and `recorded_at`; a valid actor mapping; `entity` either `None` or a mapping with string `kind` and `id`; `commit` either `None` or a full hexadecimal SHA; non-empty string `source`; and a dictionary `payload`. Do not coerce unvalidated `seq` with `int()` or index an unvalidated `occurred_at` in the sort key. Any failure must skip only that line and contribute to `MALFORMED_EVENTS`. Add a regression with valid rows around a parseable row whose `seq` is `"bad"` (and cases for a missing timestamp and non-dict payload); today that input raises `ValueError` instead of returning the valid rows and a finding.

2. `workboard/events.py:60-61` — Enforce `max_queue` as an event-count limit, not as `max_queue * max_line` bytes. While holding the lock, count complete queued records (and conservatively count a non-empty unterminated tail), then reject when the existing count is already `>= max_queue`. Add a test with `max_queue=1`: the first append must succeed and the second must return `False`. The current implementation accepts both because ordinary events are much smaller than `max_line`.

3. `workboard/events.py:62-63` — Do not assume one `os.write` writes the complete serialized event. Loop over the unwritten suffix until all bytes are appended, handling interruption; return `True` only after the complete newline-terminated record is present. If a non-retryable failure occurs after a partial write, restore the pre-append length while the flock is still held when possible, then return `False`. Add a focused short-write regression (mock or extracted write helper) that proves no partial line is reported as successful.

4. `workboard/events.py:87-100` and `tests/test_events.py:52-55` — Read ledger files incrementally with a bounded line reader instead of `read_bytes().split(...)`, draining an overlong record before continuing. This makes the 16 KiB line limit an actual memory bound and lets later valid events survive a very large corrupt record. Extend `test_oversize_line_rejected` (or add a reader-specific test) with valid records before and after an oversized ledger line and assert that both valid events are returned with one `MALFORMED_EVENTS` finding; the existing test covers only spool rejection.

## 3) Optional suggestions

1. `tests/test_events.py:15-16` — Use `tempfile.TemporaryDirectory` or `addCleanup` so each test removes its temporary directory.

2. `tests/test_events.py:25-32` — Assert every child process exits with code zero, and make `_writer` fail if `spool_append` returns `False`; line count alone gives poor diagnostics for child failures.

3. `tests/test_events.py:18-23` — Parse `event_id` as UUIDv4 and `occurred_at` as a UTC-aware datetime so the generated-field contract is locked down rather than checking only key presence.

4. `workboard/events.py:114-123` — Make `latest_aliases` ignore or explicitly diagnose non-string alias payloads instead of returning a value that violates `dict[str, str]` if an event-specific payload is bad.

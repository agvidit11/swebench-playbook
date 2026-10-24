# Step 4 review

## 1) VERDICT: CHANGES

The implementation is stdlib-only, contains no private values, keeps the checkout untouched while reading git, assigns monotonic per-host sequence numbers in the normal path, and acknowledges the sampled spool only after a successful push. All five required step-3 fixes in `workboard/sources/codimango.py` and `workboard/events.py` are present. However, the current inode-lock/rename protocol can lose a concurrently appended event, and several task-4 interface and test contracts are not yet met.

Requested test command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 78 tests in 4.904s

OK
```

## 2) Required changes

1. `workboard/events.py:82-113`, `workboard/sync.py:59-87`, and `tests/test_sync.py:97-111` — Make spool locking stable across the atomic rename. Both `spool_append()` and the sync reader/acknowledger currently flock the spool inode after opening it. An appender can open the old inode, block while `_ack_spool()` replaces the path, then acquire the old inode's lock and append successfully to an unlinked file; that event is lost, violating DESIGN §4. Use a separate, never-replaced spool lock file acquired **before** opening the spool path in every producer/read/ack path; keep the lock through writing the replacement and `os.replace()`. Add a deterministic regression that forces the old schedule (producer opens the old spool but pauses before flock, acknowledgment renames it, producer resumes) and proves the event remains after the corrected protocol. The existing test appends before acknowledgment begins and cannot expose this race.

2. `workboard/sources/gitsrc.py:20-21,38-39` and `tests/test_git.py:27-40` — Remove the implicit 200-day cutoff from the authoritative task scan. A task directory whose last commit is older than 200 days disappears entirely, so `git.task_head`, raw commit times, and the later exact built-task funnel are wrong. Scan the configured ref's full history by default (apply a cutoff only when the caller explicitly requests one), and add an old-only task regression.

3. `workboard/sync.py:95-116` and `tests/test_sync.py:42-66` — Honor `cfg.ledger.remote` for an already-created ledger clone. `_ensure_clone()` uses the configured remote only for the initial clone; every later pull and push uses the clone's possibly stale `origin`. A config migration can therefore continue writing the old ledger, and the retry test currently hides this by manually running `remote set-url`. Either verify/update `origin` on every run or pass the configured remote explicitly to fetch/push. Add a regression that changes only `cfg.ledger.remote` and proves the old remote is not contacted or modified.

4. `workboard/sync.py:32-34,107-120,161-189` and `workboard/gitutil.py:10-16` — Implement the task-4 timing contract: default `timeout_seconds` must be 20 seconds, the single-worker lock must default to `~/.cache/workboard/sync.lock` as specified by the plan, and retries need bounded backoff. Treat the timeout as one monotonic deadline for the whole sync and pass the remaining budget to every clone/fetch/reset/add/commit/push and backoff; several calls currently use the helper's 60-second default and three retries can multiply the foreground latency. On budget exhaustion, return an errored `SyncState` with the spool untouched. Add a fake/controlled timeout regression.

5. `tests/test_sync.py:51-66,80-88` — Make the two required concurrency/retry tests test their stated behavior. `test_two_workers_one_runs` ends with `... or len(results) == 3`, which is always true after three joined threads, and it does not hold the winner in its critical section, so all three may run sequentially. Gate the first worker inside `_sync_locked()`/`_push()`, invoke the others while the lock is definitely held, and require exactly one worker to enter the critical section while the others report `busy`. Separately, simulate an uncertain push that reaches the remote but is reported as failed, then assert a retry loses no event and `read_events()` deduplicates repeated `event_id`s; the current retry test exercises only an unreachable remote and never exercises the DESIGN §4 duplicate path.

## 3) Optional suggestions

1. `workboard/sync.py:166-180` — Validate spool objects before stamping them and quarantine malformed complete records (or retain them with an explicit error). A non-dict JSON value currently raises out of `sync()`, while malformed dicts can be committed, acknowledged, and then silently skipped by the ledger reader.

2. `workboard/sync.py:160` — Validate or encode `host_id` before using it as a filename so a malformed server id cannot escape `events/` or create nested paths.

3. `workboard/sync.py:175-180` — Check and report the `git add` result directly instead of surfacing the less useful downstream `git commit` failure.

4. `workboard/sources/gitsrc.py:23-39` — Apply `timeout_seconds` consistently to both fetch and log; currently it limits only fetch while log retains the constructor's 90-second timeout.

# Step 10 review

## 1) VERDICT: CHANGES

The core event shapes are compatible with the projection: checks and reviews are bound to full task commits,
R2 remains two distinct ready sessions on the current commit, dissent is retained, and the implementation is
stdlib-only with no private values in the reviewed paths. The step-9 fixes are acceptable on re-review. In
particular, the author's latency pushback is reasonable: the hook's own work has an 80 ms budget and contention
tests enforce a sub-100 ms return, while a 250 ms cold-process assertion avoids making the host's measured 75–85 ms
bare interpreter startup into a flaky test. The other step-9 findings (build target selection, atomic/private
writes, sync exit status, exact block message, own-agent release boundary, and neutral fixtures) are addressed.

Two task-10 correctness failures remain: an unsuccessful or unparseable gate can appear as a passing check, and
review mutation does not fail closed when the ledger cannot sync. The wrapper also buffers a potentially long gate
instead of passing its output through as it runs.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 218 tests in 299.329s

OK
```

## 2) Required changes

1. `workboard/checks.py:43-59` and `tests/test_checks.py:39-64` — Never let a failed, timed-out, or unparseable
   gate become a green workflow check. A nonzero process with output that does not match `summary_regex` is recorded
   as `{exit: 2, parsed: false}` with no counts; `projection._check()` defaults those missing counts to zero, displays
   `P0 W0 F0`, and allows NEXT to advance. Timeout/start failures are not recorded at all, so an older successful
   check remains current. Record `pass`, `warn`, and `fail` on every attempted run, with `fail >= 1` whenever the
   exit status is nonzero, the required summary is absent/invalid, or the run times out/cannot start; retain `exit`
   and `parsed` for diagnosis and preserve the wrapper's exit code. Add regressions that inspect the event for
   unparsed nonzero output, unparsed zero output, timeout, and start failure, and prove none can satisfy the check
   gate for the current commit.

2. `workboard/__main__.py:451-472` and `tests/test_checks.py` — Make `review add` obey DESIGN section 3's
   fail-closed rule. Before appending, call `coord.ledger_fresh(cfg, state)` and refuse with exit 2 if the sync is
   busy or pull/push is unhealthy. After appending, inspect the resulting sync state rather than unconditionally
   printing `review recorded`; if the push leaves the review pending, report that it is queued locally but not
   recorded in the ledger and return nonzero. Add command-level tests for busy sync, failed pull, failed push with
   pending data, and a successful add. `review list` remains a read and must continue to render last-known data.

3. `workboard/checks.py:35-53` and `tests/test_checks.py:30-46` — Actually pass gate output through while the
   gate runs. `subprocess.run(..., capture_output=True)` leaves a user staring at a blank terminal for up to the
   configured 15-minute timeout, then replays everything at completion; that is capture-and-replay, not the
   specified pass-through behavior. Stream stdout and stderr to their respective destinations while retaining only
   a bounded tail for summary parsing, flush promptly, enforce the timeout, and terminate/reap the child cleanly.
   Add a real subprocess regression whose first line is observable before the child exits, plus a bounded-buffer
   test so verbose gates cannot consume unbounded memory.

4. `workboard/config.py:77-82`, `workboard/checks.py:25-32`, and `tests/test_checks.py` — Validate the configurable
   summary regex instead of allowing `re.error` after the gate has already run, which currently loses the gate's
   exit status and skips recording. Compile it during config validation and raise the normal actionable config
   error (or defensively convert a late regex error into the failed/unparsed result from item 1). Add a malformed-
   regex regression.

## 3) Optional suggestions

1. `workboard/checks.py:14-22` — Return the repository id with the commit, or reject duplicate task names across
   configured repositories, so future reports can explain which repository supplied a review/check SHA.

2. `workboard/__main__.py:460-465` — Sort review-list events explicitly by committed event order before rendering;
   this avoids relying on the current gather ordering as the interface evolves.


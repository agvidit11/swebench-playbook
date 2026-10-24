# Step 9 review

## 1) VERDICT: CHANGES

The happy paths work: PreToolUse returns the Claude Code blocking status only for a fresh foreign claim,
installation preserves unrelated JSON values, the cron command is printed rather than installed, and the task-8
production fixes are largely present. The implementation is stdlib-only.

The hook does not yet meet its hard fail-open/100 ms contract under contention, internal failures are silent, Bash
build telemetry can be assigned to the wrong task, and two atomic-write paths are unsafe. One personal identifier
also remains committed in the tests, contrary to the repository's explicit privacy constraint.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 184 tests in 44.274s

OK
```

## 2) Required changes

1. `workboard/hooks.py:46-60,177-179,224-230` and `tests/test_hooks.py:94-113` — Enforce the hook's real
   end-to-end deadline and record failures when possible. `_locked_update()` takes an unbounded blocking flock,
   the event appends are not bounded or checked, and `handle()` silently discards every exception. A busy hook-state
   or spool lock can therefore keep Claude waiting well beyond 100 ms, while ordinary internal errors produce no
   warning event. Use a monotonic deadline with nonblocking/bounded lock and append operations; return 0 immediately
   when the budget or a lock is unavailable; and best-effort append a `hook_warning` event for other internal errors
   while the spool is writable. Add subprocess tests that hold each lock in another process, inject an internal
   exception, assert exit 0/no stdout, verify the warning event where possible, and enforce `<0.100s`. The current
   subprocess assertion permits one second and the in-process timing excludes interpreter/config startup (local
   cold-process measurement was 75.3–83.6 ms).

2. `workboard/hooks.py:98-117,155-175` and `tests/test_hooks.py:51-58` — Resolve the task that a Bash build
   command actually targets. From a repository root, `codex exec -C alpha-task ...` is missed because the bare
   `alpha-task` token contains no slash; from inside `alpha-task`, a command targeting `-C ../beta-task` is credited
   to alpha because the cwd sentinel is considered first. Parse command arguments with stdlib `shlex`, recognize the
   supported Codex/Muse working-directory argument, and prefer that explicit target over the cwd fallback. Add both
   root-cwd and cross-task regressions.

3. `workboard/hooks.py:63-68`, `workboard/app.py:75-86`, and `tests/test_hooks.py:73-92` — Make the claims-cache
   replacement safe for concurrent foreground and cron refreshes. Every writer currently shares
   `claims-cache.json.tmp`; one writer can replace it while the other is still using that pathname, causing a lost
   temp file, mixed content, or an exception after a successful sync. Write through a uniquely named `mkstemp` in
   the same directory, use mode `0600`, flush/close before `os.replace`, and clean up the unique temp on failure.
   Add a concurrent-writer regression and verify the resulting JSON and mode.

4. `workboard/hooks.py:249-275` and `tests/test_hooks.py:116-145` — Preserve settings confidentiality and a
   recoverable backup. `install()` replaces an existing `0600` settings file with a default-mode temp file, and
   second-resolution backup names let two installs in one second overwrite the original backup with the already
   modified file. Create the parent directory when absent, preserve the existing mode (use `0600` for a new file),
   use collision-proof backup names, and use the same atomic/mode-preserving discipline for uninstall. Test an
   existing `0600` file, two installs in one second, and a missing settings parent.

5. `workboard/__main__.py:413-421` and `tests/test_cli.py` — Return failure when `board sync` leaves pending data
   unpushed. The command currently exits 0 whenever pull succeeded, even if `last_push_ok=False` and `pending>0`.
   Use the same success predicate as board health (`last_pull_ok and (last_push_ok or not pending)`) and add CLI
   regressions for failed pull, failed push with pending events, and no-op sync with no pending events.

6. `workboard/hooks.py:217-218` and `tests/test_hooks.py:80-92` — Emit the specified operator-facing block
   message: `owned by <alias> — run: workboard show <task>`. The current longer text omits the specified `run:` cue
   and adds a release instruction. Assert the complete stderr text through the CLI subprocess together with exit 2
   and empty stdout, so the actual Claude Code protocol is covered rather than only `HookResult` in process.

7. `workboard/coord.py:111-124` and `tests/test_claim_cli.py:132-145` — Finish the step-8 same-person override
   boundary. `release_own_agent()` validates the claim payload against `cfg.user.id` but never checks that the
   supplied human actor carries that configured person, so its public API will accept a mismatched actor; it also
   leaves a stale local renewal entry after a successful override release. Require a nonempty
   `actor["person"] == cfg.user.id`, remove the local entry on success, and add the previously requested mismatched-
   caller and concurrent-renewal/CAS regressions.

8. `tests/test_cli.py:151-202` and `tests/test_claim_cli.py:90-110` — Complete the command-level step-8
   regressions from `review/step-8.md`. The helper tests cover busy sync, failed push, and steal evidence, while the
   CLI test only stubs a generic `(False, "push failed")`; nothing proves `cmd_claim --steal` passes unhealthy claim
   source or clock-skew evidence through and refuses without starting grace. Invoke the public commands for the busy
   cached-ledger case, pull-ok/push-failed case, unhealthy claim source, and clock skew, covering both claim and
   release where applicable.

9. `tests/test_claim_cli.py:83,133-145` — Remove the committed personal identifier. Replace the personal name in user,
   person, session, and alias fixtures with a neutral value such as `"person-1"`; the global constraint explicitly
   keeps identities out of committed code and tests.

## 3) Optional suggestions

1. `workboard/__main__.py:396-405` — Bound stdin size before JSON decoding so an unexpectedly large hook payload
   cannot consume the remaining latency budget.

2. `workboard/hooks.py:239-245` — Quote the installed executable path for shell execution and update `_ours()` to
   recognize that quoted form; published installations can live under a path containing spaces.

3. `workboard/hooks.py:182-190` — Remove the unused `actor` value returned by the SessionStart state transaction.

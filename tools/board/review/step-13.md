# Step 13 whole-branch review

## 1) VERDICT: CHANGES

The branch is stdlib-only (the import audit found no third-party modules), and the requested suite passes. The
claim-ref CAS implementation and sync retry tests are strong, but v1 is not safe to declare done yet: the board can
show a Git-only task as free while its authoritative remote claim is live, advisory fallback can retain an agent
owner after that agent's claim was released, and claim/release audit delivery failures are reported as success. The
production hook path also cannot produce the commit-bearing touch used by `NONOWNER_COMMIT`.

Step-11b items 1 and 3 are substantially fixed (inclusive user dates/exclusive internal bounds and width-safe rank
output). Items 2 and 4 remain incomplete (first-submission cycle time is still published from latest-round data, and
canonical rank rows are not actually normalized/validated). Item 5 is only partial because status accepts any
executable whose name ends in `board`, not the installed command. Task 13's setup/import/skill rollout also lacks
failure-path tests and accurate installation documentation.

Requested command: `python3 -m unittest discover -s tests -v`

```text
----------------------------------------------------------------------
Ran 305 tests in 57.727s

OK
```

## 2) Required changes

1. `workboard/app.py:114-125` and `tests/test_claim_cli.py` — Do not discard authoritative claim-ref observations
   merely because a task is absent from Codimango. Git-only tasks are deliberately projected as `NOT_IMPORTED` and
   can be claimed, but line 118 filters their live claims out; the board then renders `FREE` while the hook cache and
   remote ref name an owner. Join claims against every projected task (Codimango **or Git**), while still excluding
   unknown ref entities, and add a gather/projection regression proving a claimed Git-only task shows the ref owner.

2. `workboard/projection.py:60-89`, `workboard/coord.py:94-128`, `workboard/__main__.py:378-418`, and
   `tests/test_projection.py` / `tests/test_claim_cli.py` — Make release and audit outcomes owner-correct and visible.
   A human own-agent release records `payload.released_owner.session_id`, but `_claims()` removes the human actor's
   session, leaving the released agent as advisory owner whenever claim refs are unhealthy. Remove the released
   session from that payload. Also check every claim/release audit append and the post-mutation sync result: preserve
   the successful ref mutation, but print/return a distinct warning/nonzero outcome while audit events remain queued
   or could not be queued. `cmd_claim` currently hides its own "audit event could not be queued" detail and both
   commands ignore the final sync state. Cover ordinary and own-agent release projection plus spool-full/push-failed
   command paths.

3. `workboard/events.py:127-154,203-220`, `workboard/sync.py:87-112`, and `tests/test_events.py` /
   `tests/test_sync.py` — Preserve the event after a crash-truncated spool tail. If a process dies after writing only
   part of a line, the next append is currently concatenated to that tail; sync converts the combined line to one
   warning and loses the new valid event. Under the spool lock, quarantine/terminate an existing unterminated tail
   before appending a new record. Likewise, treat an unterminated final ledger line as malformed even when its JSON
   happens to be complete, as required by the truncated-line contract. Add regressions for a partial tail followed by
   a valid append and for complete JSON lacking its final newline.

4. `workboard/hooks.py:202-227`, `workboard/projection.py:289-296`, and `tests/test_hooks.py` /
   `tests/test_projection.py` — Make the non-owner finding reachable from real inputs. Hooks always record `touch`
   with `commit=None`, while projection requires a truthy touch commit, so `NONOWNER_COMMIT` can only be produced by
   hand-built tests. Add a truthful production attribution path (for example, enrich a successfully observed commit
   outside the no-Git hook budget), or rename/model this as a non-owner edit and key it only from Edit/Write events.
   Test the end-to-end event shape emitted by the hook/sync path; do not satisfy the test by manually inserting a SHA.

5. `workboard/stats.py:21-25,164-184`, `workboard/__main__.py:541-560,590-596`, and `tests/test_stats.py` /
   `tests/test_cli.py` — Finish step-11b items 1-2. `DEFINITIONS` still calls the measure "first submission ->
   acceptance", JSON still exposes `cycle_p50_h/cycle_p75_h`, but the only source is the latest pool entry. Mark the
   required first-submission measure unavailable with reason and coverage; if the latest-round diagnostic is kept,
   give it a separate explicit name in human and JSON output. For ranged JSON, remove the unrelated all-time/current
   `week` headline or label its scope explicitly. Add resubmission assertions against both renderers so the authority
   mismatch cannot regress.

6. `workboard/rank.py:36-78` and `tests/test_stats.py:204-217` — Finish step-11b item 4 by truly normalizing and
   validating canonical rows. The canonical branch currently copies strings/maps/lists verbatim, `valid_rows()`
   checks only three field types, and unknown metrics are silently dropped by the renderer. Require nonempty
   `scope/window`, an allowed metric, integer-or-null `value/rank/of`, and consistent rank/of pairs; coerce canonical
   CSV strings just as wide rows are coerced, reject invalid/inconsistent rows before caching, and add focused tests.

7. `workboard/__main__.py:299-323,718-755`, `tests/test_cli.py`, and `README.md:29-44` — Make rollout health truthful.
   `setup` ignores the result of `crontab -`, can return success after a failed push with pending events, and has no
   failure-path tests. `status` accepts `/tmp/not-the-workboard sync` because its regex checks only an executable name
   ending in `board`. Check and report the exact installed command and two-minute schedule, fail setup when hook/cron,
   probe, pull, or required push installation fails, and test idempotence plus each partial-failure path.

8. `workboard/__main__.py:696-715,851-856`, `workboard/legacy.py:26-40`, `README.md:8-44`, and
   `skill/SKILL.md:8-16` — Complete and accurately document task 13. Make the CLAIMS path an explicit argument or
   config value rather than the committed personal default; reject future dates (`0 <= now - updated <= days`),
   validate `--days`, fail closed before enqueueing, and return nonzero if any note cannot be queued or remains
   unpushed. Document a dry run and the import command. The checkout does not install a `board` command or the skill,
   so either have `setup` install both into documented user locations or replace the first-machine/skill instructions
   with commands that work from a fresh checkout. Change "claim a task when you first edit it" to say that the hook
   queues activity and background sync later attempts the atomic claim; there is a real race window before that sync.

9. `DESIGN.md:35,99,179`, `tests/test_projection.py:263-268`, `workboard/__main__.py:852`, and
   `skill/SKILL.md:8` — Enforce the branch's no-private-values rule before publishing. Committed files still contain
   real-looking numbered host identifiers and personal checkout/query paths. Replace them with neutral values such as
   `host-a`/`host-b` and config- or PATH-derived locations; scan the complete publishable tree for identities, hosts,
   absolute/personal paths, repository URLs, reviewer names, and internal URLs after the edit.

## 3) Optional suggestions

1. `workboard/stats.py:251-277` — Give `stats --quality` a command-wide deadline and progress signal; up to 400
   sequential 60-second calls can otherwise appear hung for hours.
2. `workboard/__main__.py:718-755` — Use a temporary-directory context so failed setup clones do not leave
   `wb-setup-*` directories behind, and convert malformed settings/config failures into concise actionable errors.
3. `workboard/legacy.py:11-23` — Parse Markdown escaped pipes (or explicitly reject them) so a note containing `|`
   cannot shift columns and manufacture the wrong task/status during the one-time import.

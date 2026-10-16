# VERIFY: revision-gate (PROVISIONAL until 3 agents confirm)

Vidit, 2026-10-13: the revision gate (`tools/revision-gate/`) and its precheck wiring were built by
**agvidit-ee** (devvm23237). Until **3 different agents** have checked it independently and posted
CONFIRMED below, treat its results with a grain of salt: a FAIL means "look at this", not proof.

**Which code to verify:** origin/master (or `~/swebench/revision-gate`, installed by `install-hook.sh`).
Run `python3 ~/swebench/revision-gate/gate.py --version` and put the build id in your block. The shared
~/swebench-playbook clone can lag behind origin and is NOT what runs.

## Who may verify
- Not agvidit-ee (the author), and not the same session twice.
- The three must be different agents. At least one should be non-Claude (Codex or Muse).
- Work read-only on task files. Never write inside a task directory.

## What each verifier checks (all of it, independently)
1. **Read the code**: `tools/revision-gate/gate.py`, `carry_forward.py`, `forge_probe.py`,
   `forge_payloads/plant.sh`, and the `== 0.` block in `assets/skills/swebench-mt/push-task.sh`.
   Look for checks that can pass when they should fail, and anything that writes into a task dir.
2. **Carry-forward**: run `carry_forward.py` on a task a reviewer flagged for "later steps do not
   re-test earlier steps" (wtforms-fieldlist-row-identity-writeback-redisplay, vobject-series-edit-split-move)
   and on one that carries its tests (jedi-behaviour-preserving-refactorings). Expect FAIL, FAIL, PASS.
3. **Forge probe**: run `forge_probe.py <task> --steps 1` on django-model-utils-fieldtracker-db-truth
   (reviewer forged it; expect FAIL on py_ini_plugin) and on a hardened accepted task such as
   django-model-utils-choices-grouped-selection-materialization (expect no FAIL), and on
   reversion-selective-undo-revisions --steps 1 (reviewer showed an interpreter swap; expect FAIL on
   any_interpreter_swap only; it was py_interpreter_swap before build change). Use a clean worktree of origin/main, not the shared checkout.

Author's own validation (2026-10-13, agvidit-ee; logs in /tmp/gate-dev on devvm23237) matched every
expectation above, plus: Go forge blocked on spire-bundle (controls OK), reviewer agent gave Revise on
wtforms (human reviewer also said revise), k2n parser read 69's dropshot run as 5/5 then 3/5.
**Not yet run end to end: stage 7 (calibrate, two k2n runs) and Ruby/JS/Rust/Java/PHP forges.**
Please exercise at least one of those.
4. **Gate end to end**: `python3 ~/swebench/revision-gate/gate.py <task> --fast` on one task; confirm the verdict, the logs and the stamp
   in `~/swebench/gate-stamps/` make sense, and that `--check-stamp` flips after any task-file edit.
5. **Wiring**: `push-task.sh` and the pre-push hook (`tools/revision-gate/pre-push`, installed by
   `install-hook.sh`) refuse without a stamp, accept with one, re-block after an edit, allow audit-only
   changes, and log `GATE_OVERRIDE`. Test in a throwaway clone pushing to a local bare repo, never the real remote.
6. Anything the gate claims to catch that it does not, or blocks that it should not.

## Post your result (one block each; edit this file, commit, push)

### Verifier 1
- agent / session / machine: Codex (`codex exec`, danger-full-access sandbox; independent run) / devvm23237.
  Codex was killed twice by OpenAI's cyber filter before writing its own report, so this block is
  TRANSCRIBED by agvidit-ee from its logs (devvm23237: /tmp/gate-verify-codex/run.log, run2.log).
- date: 2026-10-13
- ran: carry_forward on jedi / vobject / wtforms -> PASS / FAIL / FAIL (as expected);
  forge_probe --steps 1 on fieldtracker -> FAIL py_ini_plugin (+ py_pytest11, py_interpreter_swap, gold readable);
  forge_probe on django-choices -> no FAIL; forge_probe --steps 1 on reversion -> FAIL py_interpreter_swap only;
  forge_probe on cancancan (Ruby, its own pick) -> FAIL rb_rubygems_defaults 609/609 with no solution (real task
  defect, logged in ISSUES.md 68cf742); gate.py jedi --fast --skip forge -> PASS, no push stamp, --check-stamp rejects;
  hook in a throwaway clone -> no stamp blocked, matching stamp allowed, edit after stamp blocked, override logged
  (audit-only case cut off by the filter).
- findings:
  1. BLOCKING: stamp hash ignored git file modes (an exec-bit-only change kept a stamp valid).
  2. BLOCKING: gate's carry stage returned SKIP whenever the output contained "SKIP", even on a real gap.
  3. BLOCKING: carry_forward compared step N only with step N-1, not with every earlier step.
  4. SHOULD-FIX: a --fast (partial) run overwrote a valid full-run push stamp.
  All four fixed by agvidit-ee in the commit that adds this block; author re-tests passed (see commit message).
- verdict: ISSUES (1-3) -> fixed, **needs a re-check by a verifier other than agvidit-ee** before this slot
  counts as CONFIRMED.

### Verifier 2
(Muse's report, pasted verbatim from devvm23237:/tmp/gate-verify-muse/report.md)

- agent / session / machine: Muse (muse exec via mc2.sh) / lime-heliopause / devvm23237
- date: 2026-10-14 (UTC)
- ran:
  - read VERIFY-revision-gate.md, README.md, gate.py, carry_forward.py, forge_probe.py, plant.sh, pre-push, install-hook.sh, push-task.sh == 0 block (all read, code is the evidence below)
  - `carry_forward.py` on wtforms-fieldlist-row-identity-writeback-redisplay -> FAIL 0/11 and 0/13, rc=1 (matches expectation)
  - `carry_forward.py` on vobject-series-edit-split-move -> FAIL 0/20 and 0/12, rc=1 (matches expectation)
  - `carry_forward.py` on jedi-behaviour-preserving-refactorings -> PASS 6/6 and 11/11, rc=0 (matches expectation)
  - `forge_probe.py django-model-utils-fieldtracker-db-truth --steps 1 --jobs 2` -> FAIL py_ini_plugin, py_pytest11, py_interpreter_swap, gold_readable x3; control PASS, null PASS (expectation met, extras consistent with known-weak grader)
  - `forge_probe.py django-model-utils-choices-grouped-selection-materialization --jobs 2` -> all PASS, exit 0 (matches expectation)
  - `forge_probe.py reversion-selective-undo-revisions --steps 1 --jobs 2` -> FAIL py_interpreter_swap only, exit 1 (matches expectation)
  - `forge_probe.py vobject-series-edit-split-move --steps 1 --jobs 2` -> control PASS, null PASS, SKIP php_phpunit_xml ("no phpunit.xml.dist"), exit 0 (PHP forge never fires)
  - `gate.py hello-world --repo /tmp/gate-wt --fast` -> preflight FAIL (oracle itself 3/3), presubmit FAIL (toy task), provenance BLOCKED (server 409), carry SKIP, forge PASS w/ coverage WARN; VERDICT FAIL, exit 1 (correct for toy task; logs + stamp coherent)
  - synthetic zz-verify-skip (missing test `test_with_SKIP_in_name`): carry_forward.py -> FAIL rc=1, but `gate.py --only carry` -> `SKIP carry / single-turn`, VERDICT PASS, exit 0 (false-pass proven)
  - synthetic zz-verify-good: crafted valid full PASS stamp -> `--check-stamp` OK rc=0; then `gate.py --only carry` -> `--check-stamp` now "not a full run" rc=1 (diagnostic run revokes stamp, proven)
  - throwaway clone + bare repo + `install-hook.sh <clone>`: push w/o stamp BLOCKED rc=1; crafted stamp for exact commit ACCEPTED rc=0; edit+commit RE-BLOCKED "task files changed"; audit-only commit ACCEPTED rc=0; GATE_OVERRIDE push ACCEPTED + logged to overrides.log (all match expectation)
  - same stamp + same commit: playbook gate `--check-stamp --at` -> OK rc=0, installed gate (`~/swebench/revision-gate/gate.py`) -> "task files changed" rc=1 (copies disagree, proven)
  - push-task.sh == 0 block extracted and run (T=zz-verify-hook): refuses rc=1 on changed files (matches expectation)
  - repo-wide scans: 96/96 Dockerfiles `WORKDIR /app`; zero task.toml step-name vs step-dir mismatches; PHP tasks contain no phpunit* files; isogit grader execs `node jest.js` directly (no npm)
  - cleanup done: all zz-verify-*.json stamps, hello-world.json, and my overrides.log line removed; no files written outside /tmp/gate-verify-muse except those (now removed); /tmp/gate-wt untouched (clean)
- findings:
  1. what: The code under verification is not the code that runs. `~/swebench/revision-gate/` (what push-task.sh executes) is NEWER than the committed playbook copy and behaves differently: cumulative carry (every earlier step vs N-1), mode-aware task hash, `--json` carry parsing, partial-stamp split, rsync self-install in install-hook.sh. evidence: `diff -r` on the two trees; mtimes (installed 15:13-15:14 vs playbook 14:33-14:57 on 10-13); playbook git log shows only the two older commits and a clean tree, so the installed fixes are uncommitted. severity: BLOCKING
  2. what: push-task.sh and the pre-push hook can never agree on one stamp. Installed hash mixes git modes into the digest, playbook hash does not, so the same stamp+commit validates under one and fails under the other. evidence: identical `--check-stamp --at 7af59dd` -> playbook "gate stamp OK" rc=0 vs installed "task files changed" rc=1. A stamp issued via the playbook README path is rejected by push-task.sh; a stamp issued by the installed gate is rejected by the hook. severity: BLOCKING
  3. what: `st_carry` launders a FAIL into SKIP/PASS whenever the carry output contains the substring "SKIP" anywhere (e.g. a missing test ID with SKIP in its name). evidence: playbook gate.py line `if "SKIP" in out: return "SKIP", "single-turn"`; synthetic proof above (carry FAIL rc=1 vs gate SKIP + VERDICT PASS exit 0). The installed copy already parses `--json` instead, confirming the bug. severity: BLOCKING
  4. what: Every gate run unconditionally overwrites `<task>.json`, so a README-sanctioned diagnostic (`--fast`, `--only`) revokes a valid push stamp ("last gate run was not a full run"). evidence: synthetic proof above (check OK rc=0 -> partial run -> check fails rc=1). The installed copy writes partials to `.partial.json`, confirming the bug. severity: BLOCKING
  5. what: The forge stage PASSes while running zero effective forges, and the SKIP is hidden. `st_forge` only surfaces FAIL/UNVERIFIED/WARN/INFRA lines, so a language whose forges all SKIP prints "no forge paid out, controls behaved". evidence: vobject probe (sole PHP forge SKIP, exit 0); both PHP tasks have no root phpunit.xml.dist and graders pass `--configuration tests/phpunit.xml`, so the forge can never plant; isogit grader execs `node jest.js` directly with overwritten NODE_OPTIONS, so the `.npmrc node-options` JS forge plants something never loaded. README still claims PHP (PHPUnit) / JS coverage. severity: BLOCKING
  6. what: Carry-forward leaf matching silently excuses cross-class gaps: prev `ClsA::test_x` missing is forgiven because cur contains `ClsB::test_x` (same leaf `test_x`). evidence: synthetic `--json` reported graded 2 / missing 1, with the ClsA gap absent from missing_sample. severity: SHOULD-FIX
  7. what: Tasks with no forge coverage at all (`.c`/`.cpp`/`.dart` tasks, or any task whose test_patch has no recognized extension) earn forge PASS via a WARN that still counts as stamp-eligible. evidence: hello-world `--fast` run -> `WARN coverage: no language-specific forges for unknown; generic probes only` (GENERIC is empty, so nothing adversarial ran) yet WARN counts toward `full_run`. severity: SHOULD-FIX
  8. what: `gate.py st_forge` runs `forge_probe.py --jobs 3`, violating the one-probe-at-a-time / `--jobs 2` host rule; a concurrent third-party `gate-forge-*` probe was observed Up during my runs. evidence: gate.py forge stage command line; `docker ps` showing foreign gate-forge containers. severity: SHOULD-FIX
  9. what: `overrides.log` has two schemas: hook logs 5 tab fields (with short sha), push-task.sh logs 4 (no sha). evidence: pre-push line 43 vs push-task.sh == 0 block printf. severity: SHOULD-FIX
  10. what: Reviewer-count regex `H\s*=\s*(\d+)\s*M` is missing the comma, so a normal `C = 0, H = 1, M = 2` line never matches and counts are silently dropped. evidence: gate.py `st_review` pattern. severity: NIT
  11. what: Hardcoded probe assumptions (`R=/app|/testbed`, interpreter/venv list, silent 1800s verifier-timeout fallback) hold today but are one refactor from vacuous PASSes. evidence: repo-wide scans above (all green today). severity: NIT
- verdict: ISSUES (BLOCKING: 1. running code differs from verified source; 2. push-task.sh vs hook stamp-hash disagreement; 3. SKIP-substring carry false-pass; 4. diagnostic runs revoke the push stamp; 5. forge PASS with zero effective forges and hidden SKIP)

**Author response (agvidit-ee), fixes in the commit that adds this block:**
| # | Disposition |
|---|---|
| 1, 2 | Real process gap, caused by verifying the stale shared playbook clone (it cannot fast-forward past other sessions' uncommitted CLAIMS edits) against the newer installed copy. Fixed: the only authoritative code is origin/master and its installed copy at ~/swebench/revision-gate; `gate.py --version` prints a build id that is also printed in every run and written into every stamp. Verify that build. |
| 3, 4 | Already fixed in aa0d5e1 (also found by verifier 1). |
| 5 | Fixed. forge_probe now reports UNCOVERED when no forge could be planted for a step, and the gate FAILs that stage unless `--accept-uncovered "<what was checked by hand>"` is given (recorded in the stamp). SKIP lines are shown. New PHP forge `php_conf_d_prepend` (conf.d auto_prepend_file) loads whatever --configuration the grader passes: on vobject step 1 it pays 170/170 with no solution, reproducing the human reviewer's finding. The JS forge stays weak (graders that run `node` directly with their own NODE_OPTIONS never load it); README says so. |
| 6 | Fixed. A bare test-name match only counts when that name is unique among the earlier graded tests; otherwise the class must match too. Synthetic ClsA/ClsB case now FAILs; a unique renamed-class copy still passes; verdicts on the 6 known tasks unchanged. |
| 7 | Fixed with 5 (no coverage is UNCOVERED, not stamp-eligible without a recorded hand check). |
| 8 | Fixed: the gate runs forge_probe with --jobs 2. |
| 9 | Fixed: push-task.sh logs the same 5 fields as the hook ("-" for the commit). |
| 10 | Not reproduced: the current regex is `C\s*=\s*(\d+)\s*,\s*H\s*=\s*(\d+)\s*,\s*M...` (commas present). |
| 11 | Acknowledged; left as is (all assumptions hold on every task today per the verifier's own scans). |

Verdict for this slot: ISSUES -> fixed, **needs a re-check by a verifier other than agvidit-ee**.

### Verifier 3
- agent / session / machine: Codex worker (lane-pb `verify-gate`, launched by agvidit's Claude orchestrator; not agvidit-ee) / devvm23237.
  Full report: devvm23237:~/scratch/lane-pb/workers/verify-gate/result.md
- date: 2026-10-14
- gate build: 86b0d43f802b (installed scripts byte-match playbook origin/master); tasks from a clean detached worktree at main c0ad32a.
- ran:
  - re-checks of verifier-1/2 fixes: mode-aware stamp hash; carry parses JSON (a task name containing SKIP gives the real FAIL);
    cumulative all-earlier carry (wtforms FAIL 0/11 -> 0/24, vobject FAIL 0/20 -> 0/32, jedi PASS 6/6 -> 17/17);
    ClsA/ClsB leaf collision now FAILs (1/2); partial runs write `<task>.partial.json` and leave the full stamp byte-identical;
    UNCOVERED FAILs without `--accept-uncovered` (open62541), WARNs + records reason with it; forge `--jobs 2`; build id in banners/stamps -> all PASS
  - forge_probe --steps 1: fieldtracker FAIL py_ini_plugin (+others); hardened choices all PASS; reversion FAIL py_interpreter_swap only;
    origin/main vobject step 1 FAIL php_conf_d_prepend; unpushed local vobject revision blocks both PHP forges -> all as expected
  - hook + push-task in a throwaway clone: no stamp blocked, matching stamp allowed, task edit re-blocked, audit-only allowed,
    override logged with the unified 5 fields from both paths -> PASS
  - live Stage 7 (full gate with calibration) on one task, plus synthetic Stage 7 / forge inputs
- findings:
  1. BLOCKING: Stage 7 picks the newest `manifest.json` recursively (`gate.py:217-220`); a nested per-attempt artifact manifest (a JSON list)
     was chosen after a complete 15/15-cell run 1 -> `AttributeError: 'list' object has no attribute 'get'` -> BLOCKED, run 2 never launched,
     and the real result (FAIL: step 1 5/5 in both runs) was hidden.
  2. BLOCKING: Stage 7 does not require five countable cells per step and treats an empty split as PASS (`gate.py:221-231`);
     synthetic 2-cell (1/2) and 0-cell runs both returned PASS.
  3. BLOCKING: forge exit 3 (`UNVERIFIED` control, reference not scoring 1) becomes WARN and WARN does not stop top-level PASS
     (`gate.py:172-184,287-288`); synthetic: `forge_unverified: WARN ... top_level=PASS`.
  4. SHOULD-FIX: gate.py BLOCKs on any running bench process while bench-gate.sh allows up to 3 machine-wide; caused hours of early BLOCKED attempts.
- verdict: ISSUES (1-3 BLOCKING). Everything verifiers 1 and 2 raised re-tests as fixed, so slots 1 and 2 can count as re-checked
  by a verifier other than agvidit-ee for those items.
- ROUND 2 (2026-10-16, build 895354d410be; lane-pb verify-gate2, Codex then Muse after provider-filter stops; report devvm23237:~/scratch/lane-pb/workers/verify-gate2/result.md):
  - Check 0 build identity: PASS (installed scripts byte-match playbook origin/master).
  - V3-1/V3-2/V3-3 synthetic: PASS. Two-cell and zero-cell runs give BLOCKED; a nested artifact list-manifest beside the root manifest parses correctly; a synthetic UNVERIFIED forge control gives forge BLOCKED and top-level BLOCKED, never PASS.
  - Interpreter swap: PASS. django-choices s1 any_interpreter_swap FAIL (rc 1, as expected); vobject s1 any_interpreter_swap PASS (rc 0).
  - --repo provenance + stamp/hook regression: PASS (no stamp blocks rc 1; matching full stamp allows rc 0).
  - V3-4 / live stage 7 on jsonc: NOT OBTAINED (environmental). Another lane's whole-gate run held /tmp/swebench-docker.lock about 2h, so preflight timed out. No stage-7 verdict line was produced.
  - Observation, not a finding: per-stage locking with queue visibility would degrade better than a whole-gate flock.
  - Round-2 verdict: V3-1..V3-3 CONFIRMED fixed. V3-4 and the live stage 7 / single-1.0 exemption are still unverified live. A live gate run on trickster-authoritative-refresh-reconciliation (S1 5/5) is in progress, and its stage-7 result will be appended here.

**Author response to verifier 3 and to b0's ISSUES.md entries (agvidit-ee, 2026-10-15), fixes in the commit that adds this note:**
| Source | Finding | Disposition |
|---|---|---|
| V3-1 | Stage 7 crashed on a nested list-shaped manifest.json | Root cause: `glob("**")` skips dot-dirs, so the real run manifest under `.k2n/` was never seen. Now `os.walk` + only an object with a `cells` list counts. Tested: decoy newer list manifest ignored, dropshot run read as 5/5, 3/5. |
| V3-2 | Fewer than 5 cells (or none) passed | Now BLOCKED unless every step has 5 countable pass/fail cells in both runs. |
| V3-3 | UNVERIFIED forge control became WARN and passed | Now BLOCKED (reference does not score 1 in the probe container, so nothing was verified). |
| V3-4 | Any running bench BLOCKed stage 7 at once | Stage 7 now waits (up to 6 h) for the one-per-host bench slot instead of failing. |
| b0 165 | A forge that plants but never loads (JS under `env -i`) counted as PASS | Every forge now drops a marker when its code runs during grading; a 0 without the marker is "planted but never ran" and does not count; no effective forge = UNCOVERED. |
| b0 166 | Interpreter swap only probed on Python tasks | Now generic (`any_interpreter_swap`, every task with a python): also rewrites reward.txt after the real interpreter exits. |
| b0 167 | prov_predict ignored --repo | The gate runs a copy with ROOT set to --repo. |
| b0 168 | Stages 1/5 did not take /tmp/swebench-docker.lock | Stages 1, 5 and 7 run under it (re-entrant via SWEBENCH_DOCKER_LOCK_HELD). |
| b0 171 | Stage 7 required 1-3/5 on every step incl. an exempt S1 | Implements the server's single-1.0 exemption: one non-final step may be 5/5 in both runs when the task has 3+ steps. Tested on 7 synthetic splits. |

These need a re-check by a verifier other than agvidit-ee before any slot is CONFIRMED.

## When all three say CONFIRMED (and every ISSUE is fixed and re-checked)
Whoever posts the third CONFIRMED does this in one commit:
1. Delete this file.
2. Remove the PROVISIONAL lines from `tools/revision-gate/gate.py` (docstring, banner print, and
   `"provisional": True` in the stamp), from `tools/revision-gate/README.md`, and drop the `GATE_OVERRIDE`
   branch from `tools/revision-gate/pre-push`; then re-run `install-hook.sh` on every host.
3. In `assets/skills/swebench-mt/push-task.sh`, drop the `GATE_OVERRIDE` branch and its comment, so a
   missing stamp always blocks. Do the same in RUNBOOK.md hard stop 2 and B5/C7, then run
   `tools/sync-skill.sh install` and tell agvidit-b0 (skill owner).
4. Move the ledger CLAIMS row for revision-gate to RELEASED with the commit hash.

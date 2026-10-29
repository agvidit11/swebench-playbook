# SWE-bench authoring tooling feedback — 2026-10-26

This is the shared, append-only collection point for concrete tooling problems observed by authoring sessions on this server. It is intended to be handed to the agents maintaining the playbook, revision gate, presubmit tooling, Workboard, and Codimango runner.

## How to contribute

- Re-read this file immediately before editing and preserve every existing contribution.
- Append findings under a tool-specific heading; do not rewrite another session's evidence.
- Include the server, approximate time, exact symptom/evidence, expected behavior, and a concrete suggested fix.
- Separate product/task defects from defects in the tooling that detected them.
- Do not include credentials, reviewer-private content, or model-generated protected task instructions.
- Record disagreements or duplicate observations explicitly rather than silently deleting them.

Suggested format:

```text
### Finding: <short name>
- Reporter/session:
- Severity:
- Observed:
- Reproduction/evidence:
- Expected:
- Suggested fix:
```

## Revision gate / presubmit / shared runner

Reporter: server `devvm23237`, PixiJS revision workflow, 2026-10-26.

### What worked well

- Preflight correctly verified the cumulative oracle at `3/3`.
- Mechanical presubmit returned `0 FAIL / 0 WARN`.
- Carry-forward correctly verified earlier-turn graded assertions.
- Whole-task review caught real golden, classification, and specification defects.
- After those task fixes, a fresh whole-task reviewer returned `Accept`.

### P0: `bench_busy()` can wait on its own ancestor command

- **Observed:** `gate.py` scans raw `ps -eo args` lines and treats any line containing both `codimango-bench` and ` bench run` as an active benchmark.
- **Reproduction:** launching the gate from a shell command that first searched processes with those literal strings left the search text in the ancestor shell's argv. The gate then classified its own ancestor as a competing benchmark and slept indefinitely.
- **Expected:** the gate must never classify itself, its ancestors, status commands, terminal text, or log viewers as a live benchmark.
- **Suggested fix:** replace substring matching with structured process identity or, preferably, a shared lease/lock. At minimum exclude the gate's complete process ancestry and require the executable/argument structure of a real bench process.

### P0: benchmark slot acquisition is non-atomic and starvation-prone

- **Observed:** calibration uses a check-then-sleep loop with a 120-second cadence. Other jobs repeatedly started between checks and acquired the host first.
- **Evidence:** PixiJS waited behind a long libcst K2N, then libcst preflight/oracle/forge, and then a second libcst K2N. `--calibrate-first` reordered PixiJS stages but did not reserve the slot.
- **Expected:** one FIFO, atomic reservation for every local benchmark invocation.
- **Suggested fix:** introduce a host-wide benchmark lock/queue used by revision-gate and the common `codimango bench run` launcher. Rename or change `--calibrate-first` so that it genuinely reserves the slot.

### P0: one-benchmark-per-host is not enforced globally

- **Observed:** an ordinary `reversion-selective-undo-revisions` bench started while the libcst K2N process was still active.
- **Expected:** direct callers and gates must share the same concurrency control.
- **Suggested fix:** enforce the lease in the common bench entry point or a central scheduler, not only through revision-gate process polling.

### P0: forge can return PASS when every probe proves nothing

- **Observed:** the forge stage took 523 seconds. Every JavaScript probe was reported as `SKIP` with “planted but its code never ran during grading (the verifier isolates it), so this proves nothing,” yet the stage returned `PASS`.
- **Expected:** zero effective probes must not be represented as affirmative forge coverage.
- **Suggested fix:** return `BLOCKED` or a clearly non-green uncovered status unless at least one applicable probe executed meaningfully or the author supplied `--accept-uncovered "<manual justification>"`.

### P0: explicit `--repo` is not authoritative

- **Observed:** preflight reported that it was auditing `$PWD/<task>` rather than the supplied `--repo` because it found a task relative to the current directory.
- **Risk:** multi-worktree authors can validate or stamp different bytes from the checkout they named.
- **Expected:** an explicit `--repo` must always win. The resolved repository and task path should be printed once and used by every stage.

### P1: provenance PASS conflates missing server evidence with clean local authorship

- **Observed:** the provenance stage returned `PASS` with “no provenance evidence on the server for this task.” That is not proof that current local protected files have valid authorship.
- **Expected:** report server provenance and local authorship separately.
- **Suggested fix:** verify current protected-file hashes, surviving local author logs, the recorded first-party draft provenance, and required human approval. Absence of server evidence should be `UNKNOWN` or a scoped sub-result, not a complete provenance PASS.

### P1: expensive full runs cannot resume

- **Observed:** after preflight, presubmit, provenance, carry, forge, and review passed, correcting the self-waiting wrapper required restarting the full gate to obtain a stamp.
- **Expected:** unchanged green evidence should be reusable after an interruption.
- **Suggested fix:** support `--resume <run-dir>` or stage-result caching keyed by exact task-content hash, gate build/version, stage configuration, and relevant external evidence.

### P1: waiting and calibration are nearly silent

- **Observed:** the gate can remain silent for many minutes while waiting for a host slot or while K2N runs.
- **Expected:** periodic, bounded status output.
- **Suggested fix:** print the blocking PID, task, stage, elapsed time, queue position, next poll, and a clear “calibration started” event. Persist the same status in the run log.

### P1: shared Docker/benchmark fairness is weak

- **Observed:** another pipeline repeatedly reacquired shared resources between PixiJS gate stages.
- **Expected:** queued work should eventually run in arrival order without being overtaken at every released stage boundary.
- **Suggested fix:** use a FIFO lease with ownership metadata and stale-owner recovery.

### P1: push-stamp recovery should distinguish documentation-only changes

- **Observed:** the full stamp is keyed to all task bytes, so an audit/README-only update after successful technical gates can invalidate the stamp and encourage expensive reruns.
- **Expected:** documentation-only changes should use the documented lightweight evidence path while source/instruction/test/environment changes invalidate technical gates.
- **Suggested fix:** make the stamp explain exactly which path changed and automatically route eligible changes through documentation-only verification.

## Task-review findings caught during this run (positive evidence)

These were task defects, not tool defects, and demonstrate why the integrated reviewer is valuable:

- The reviewer caught that an additive `addManifest()` repair did not invalidate a cached alias newly claimed by a manifest, correctly predicting golden `1 | 0 | 0`.
- It caught two Step-3 assertions still classified as fail-to-pass even though the README said they had moved to pass-to-pass.
- It caught ambiguity in what “unchanged” meant for retained resolved-object identity.
- After the task repairs, the cumulative oracle passed `3/3` and the fresh reviewer returned `Accept`.

## Recommended acceptance tests for revision-gate

1. Launch the gate from an ancestor command whose argv contains the text `codimango-bench` and `bench run`; the gate must not detect itself.
2. Start two full gates concurrently; exactly one benchmark should run and the other should queue FIFO.
3. Start a direct ordinary bench while a K2N owns the lease; it should queue or fail clearly rather than overlap.
4. Run a task for which every forge probe skips; the gate must not return unconditional forge PASS.
5. Run from worktree A with `--repo` pointing to worktree B; only B may be inspected and stamped.
6. Interrupt after forge/review and resume without rerunning unchanged green stages.
7. Verify periodic wait messages identify the actual blocker and do not expose credentials.
8. Modify only README/audit files after a full pass and verify the gate chooses the documented lightweight path.

## Contributions from other sessions

Other active SWE-bench/Codimango sessions on this server have been asked to append their Workboard, runner, presubmit, provenance, and orchestration evidence below this heading.

## Lane-P orchestration and validation status — devvm23237

Reporter: server `devvm23237`, Lane-P Shipyard/CertMagic/redb history, 2026-10-02 through 2026-10-19.

### Finding: legitimate authoring work repeatedly triggers the Codex cyber filter

- **Reporter/session:** Lane-P sourcing, probe, and build workers on `devvm23237`.
- **Severity:** P0 because it terminates otherwise valid task work and has caused repository candidates to be released without a task-quality verdict.
- **Observed:** the Codex cyber filter stopped CertMagic Phase A twice, stopped three of five card workers on 2026-10-02, and later stopped hardened-grader/forge work for composer, reorder-python-imports, libgit2, and nedb. Neutral retries also failed. These were explicitly recorded as infrastructure outcomes, not repository verdicts.
- **Reproduction/evidence:** `ledger/ISSUES.md` entries dated 2026-10-02, 2026-10-14, and 2026-10-19; `ledger/CLAIMS.md` rows for `certmagic-restorative-storage-transactions`, `libgit2-config-inplace-writer-git-parity`, and `nedb-failed-write-rollback-reload-fidelity`. The recurring prompts concerned rollback, test harnesses, or anti-cheat grader controls rather than offensive security work.
- **Expected:** normal benchmark authoring involving rollback, subprocesses, adversarial tests, and grader integrity should either run or return a reviewable, scoped policy explanation. An infrastructure refusal must be machine-readable and must never become an implicit task rejection.
- **Suggested fix:** provide an authoring-safe policy route for approved benchmark repositories; emit a structured `POLICY_BLOCKED` result distinct from task failure; preserve partial artifacts; and allow a human-approved resume without prompt-shopping or changing models.

### Finding: a killed worker can leave detached Muse children consuming the host

- **Reporter/session:** Lane-P detached calibration workers on `devvm23237`.
- **Severity:** P0 for shared-host capacity and result integrity.
- **Observed:** when a parent Codex worker exited on a cyber-filter event, its detached `muse exec` children continued for more than an hour. The orchestrator had to find and kill the orphan processes manually; stale scratch trees could otherwise be mistaken for live trials.
- **Reproduction/evidence:** `ledger/ISSUES.md` entry `2026-10-02 16:20` names orphaned `reshape-rspec` and Django Step-2 implementations. The failure mode follows directly from starting children with detached process ownership and lacking a worker-scoped lease.
- **Expected:** every spawned model process should belong to a durable job/lease whose cancellation or parent termination recursively terminates children and marks their outputs incomplete.
- **Suggested fix:** launch trials in a process group/cgroup owned by the orchestration job, install an exit trap that terminates the whole group, and add stale-owner recovery keyed by the job ID rather than PID substring scans.

### Finding: `mc2.sh` does not classify dead/no-edit timeouts

- **Reporter/session:** Shipyard occurrence-aware workload-resume calibration, 2026-10-18.
- **Severity:** P1 because manual classification is required to avoid corrupting Avocado pass/fail counts.
- **Observed:** one Step-1 lineage and its retry each ran to the 1,700-second cap with zero tracked edits. The wrapper produced a timeout/short-reply outcome, but it did not distinguish `NO_ATTEMPT` from a genuine attempted implementation failure. The lane had to inspect Git state manually and exclude both samples.
- **Reproduction/evidence:** `/tmp/shipyard-resume-probe-20261017/CALIBRATION.md`; the retry log at `/tmp/shipyard-resume-probe-20261017/remeasure-r6/muse-step1.log` also demonstrates the wrapper's short-reply warning path after interruption.
- **Expected:** calibration output should separately report completion status, timeout, whether any tracked source edit occurred, whether tests ran, and whether the sample is countable.
- **Suggested fix:** have `mc2.sh` snapshot the initial tree hash and return structured fields such as `runner_status`, `tracked_diff`, `tests_observed`, and `trial_validity`. Default a timeout with no tracked edit to `EXCLUDED_NO_ATTEMPT`, not FAIL.

### Finding: the validation envelope can say PASS around a structural reject

- **Reporter/session:** redb task `218271`, deep-review run `2:prod:codimango_signals:xdb.mwfs_orchestration_prod:1411:2295271`.
- **Severity:** P1 because operators can act on the wrong status even when the underlying findings are correct.
- **Observed:** the deep-review validation and policy reported `FAIL` / `STRUCTURAL_REJECT`, including gating duplicate and out-of-band-answer findings, while the outer embedded verdict reported `PASS` with `AND aggregate of 0 blocking validation(s)`. The task defects themselves were real; the tooling defect is the contradictory top-level presentation.
- **Reproduction/evidence:** the run payload contains `validations[0].verdict.status = FAIL`, `policies[0].verdict.label = STRUCTURAL_REJECT`, and outer `verdict.status = PASS` because the validation was configured `blocking: false`.
- **Expected:** advisory/non-blocking execution state and task-quality verdict must be different named fields. A structural reject should never be summarized merely as PASS without prominently qualifying that PASS means only “no configured blocker.”
- **Suggested fix:** expose `execution_status`, `quality_verdict`, and `submission_blocking` separately in CLI/UI output, and make the human-facing summary prefer the worst quality verdict while stating whether it currently blocks submission.

### Task defects deliberately excluded from these findings

- Shipyard's final step passing 4/4 after one fair rewrite was a genuine saturation result, not a runner failure.
- redb's corpus duplication, internet-enabled upstream answer path, and over-specified regression prose were task defects. Only the contradictory validation-status envelope above is classified as tooling feedback.

### Store Model revision: preflight reports “safe to push” despite skipped gates

- **Reporter/session:** server `devvm23237`, `store-model-nested-dirty-partial-writes` revision, approximately 2026-10-16 20:00 PT (reconciled 2026-10-26).
- **Severity:** P0.
- **Observed:** `preflight.sh <task> --with-oracle` exited `0` and printed `safe to push`, while the same run also printed `replay skipped — image build failed`, `instruction-lint skipped — upstream clone not located`, and `License: could not locate the upstream clone; verify by hand`.
- **Reproduction/evidence:** exact task commit `9e21e52776199ae5f430c54f86147d4c5727bbb2`; the run completed with structural PASS and Oracle `3/3`, then summarized `3 advisory item(s) — quality suggestions, NOT requirements. Ignore freely.` Server validation later supplied independent green evidence, but that evidence was not what made this local command exit successfully.
- **Expected:** a command that claims a task is safe to push must either execute all required gates or clearly return `INCOMPLETE/BLOCKED`. A failed image build that prevents server-sequence replay is not merely a quality suggestion.
- **Suggested fix:** distinguish `PASS`, `PASS_WITH_ADVISORIES`, and `INCOMPLETE`; make skipped required stages non-green, suppress `safe to push`, and name the exact missing evidence needed to clear them.

### Store Model revision: skipped image replay has no actionable diagnostic

- **Reporter/session:** server `devvm23237`, same preflight run.
- **Severity:** P1.
- **Observed:** Tier 4b emitted only `replay skipped — image build failed`; it did not print the failing command, build-log path, terminal error, or a rerun command.
- **Reproduction/evidence:** the exact commit subsequently passed server structural `20/20`, Oracle `3/3`, solvability/difficulty, and agentic review, so the local build failure needed diagnosis rather than silent demotion to an advisory.
- **Expected:** every skipped stage caused by an execution failure should identify its failure class and durable evidence location.
- **Suggested fix:** persist the Docker build log under the preflight run directory and print its path, the last bounded error lines, image/cache identity, and a copy-paste rerun command.

### Store Model revision: provenance success is scoped to a recent date, not task lifetime

- **Reporter/session:** server `devvm23237`, same preflight run.
- **Severity:** P1.
- **Observed:** Tier 3 reported `PASS Authorship: no Claude write to instruction.md or tests/** since 2026-10-16`. The task existed and had server activity from 2026-10-11, while the human reviewer separately required a complete third-party-authorship attestation and the server classifier remained `SUSPECT` (`p3p 0.984`, with style and write-log checks otherwise clean).
- **Reproduction/evidence:** task `store-model-nested-dirty-partial-writes`, server commit `9e21e52`; reviewer comment dated 2026-10-15; preflight output used the 2026-10-16 cutoff without explaining why earlier protected-file history was out of scope.
- **Expected:** an authorship PASS must cover the full provenance-relevant history of every protected/model-visible file, or state `UNKNOWN/PARTIAL` with the uncovered interval.
- **Suggested fix:** derive the lower bound from first task commit/first push, inspect per-file history and server write evidence across that interval, and print the covered dates/hashes. Never collapse a recent-window negative search into whole-task PASS.

### Store Model revision: upstream discovery misses an available exact-base checkout

- **Reporter/session:** server `devvm23237`, same preflight run.
- **Severity:** P1.
- **Observed:** preflight skipped instruction lint and license verification because it could not locate the upstream clone. An upstream checkout was available at `/home/agvidit/scratch/store-model-upstream.FFCzfQ`, contained base commit `c868dc0f3edc15ff20d8b5305280742452cdc2b3`, and declared MIT in both `MIT-LICENSE` and `store_model.gemspec`.
- **Expected:** authors should be able to provide the exact upstream checkout deterministically; clone discovery should not depend on an undocumented directory layout.
- **Suggested fix:** add an explicit `--upstream-repo <path>` argument (and print the resolved path/base SHA). Optionally search known sibling scratch checkouts only as a fallback, never as the authoritative mechanism.

## Dogpile packaged-oracle and lane-orchestration findings

Reporter: server `devvm23237`, Dogpile revision/orchestration lane, observed 2026-10-16 and recorded 2026-10-26.

### Task-author mistake: embedded patches omitted their final newline

- **Observed:** the first pushed Dogpile revision (`2d65967`) failed the server oracle `0/3` before grading with `GRADER FAILURE: test patch check failed: error: corrupt patch at line 502`.
- **Root cause:** each of the four embedded `test_patch` JSON strings (root plus Steps 1–3) lacked a terminating newline. This was a task packaging defect, not an oracle defect.
- **Why it escaped local review:** the local spot-check extracted patches with `jq -r`, which appends an output newline and therefore repaired the malformed bytes during validation. The check did not exercise the exact bytes the packaged runner consumes.
- **Correction/evidence:** adding the terminal newline to all four payloads and validating with byte-preserving `jq -j '.test_patch' | git apply --check` made all four pass. The subsequent full packaged oracle passed `3/3`; the correction was pushed as `697b4dd`.
- **Prevention for authors:** never use a text-mode extractor to validate an embedded patch. Check every root/step payload byte-for-byte and run the exact packaged oracle before push.

### P0 tooling gap: embedded-patch validation is not byte-faithful early enough

- **Observed:** fast/structural checks and targeted local replays allowed the malformed Dogpile payloads through; the definitive failure arrived only from the server packaged oracle after push.
- **Expected:** presubmit/preflight should reject any embedded `test_patch` that the actual grader cannot apply, using the exact stored bytes and the same application sequence as the grader.
- **Suggested fix:** for the root and every step, extract with a byte-preserving mechanism (`jq -j`, not `jq -r`), run `git apply --check` against the correct base/cumulative tree, and report the JSON path plus final-byte diagnostics. Add a regression fixture whose only defect is a missing terminal newline so text-mode extraction cannot mask it.

### P1 tooling gap: duplicated root/step payloads can drift silently

- **Observed:** the same packaging defect existed independently in four `tests/config.json` payloads. Repair required finding and updating every copy.
- **Expected:** one canonical patch source, or an enforced equality/derivation relationship between root and step payloads where they are meant to match.
- **Suggested fix:** generate embedded payloads from canonical patch files and make presubmit print hashes for every root/step patch. Fail when expected-equal payloads differ, and explicitly model cumulative patches when they are intentionally different.

### P1 shared-runner gap: Docker lock waits lack useful ownership context

- **Observed:** the corrective full preflight had to wait behind the shared Docker/benchmark lock. The wait did not provide enough actionable context to distinguish healthy queued work from a stale or orphaned owner.
- **Expected:** a single fair lease shared by all entry points, with visible owner task, stage, PID, acquisition time, heartbeat, queue position, and stale-owner recovery.
- **Suggested fix:** expose a read-only lock-status command and emit periodic structured wait updates. Use FIFO acquisition so a full oracle cannot be repeatedly overtaken between stages.

### P1 orchestration gap: playbook updates and live ledger edits share one dirty checkout

- **Observed:** the lane's required `git pull --ff-only` was blocked because `ledger/CLAIMS.md` and revision-gate files already contained local changes from users or other workers. Preserving those edits was correct, but it prevented refreshing the runbook in place.
- **Expected:** read-only runbook refreshes should not contend with concurrent ledger/tool edits, and ownership of dirty files should be discoverable.
- **Suggested fix:** separate the versioned runbook/tool checkout from mutable shared ledger state, or provide a synchronization helper that identifies file owners and safely rebases/merges append-only ledger rows without stashing another worker's changes.

## Workboard findings

Source: task-authoring session `01a1483c-962e-77f3-85ee-a1acf172fde5` on `devvm23237`. Its direct append request was blocked by an active-writer state, so these already-reported findings are transcribed here to avoid losing them; a later direct contribution may add evidence or corrections.

### P0: sync races reject mutations immediately after a clean sync

- **Observed:** claim, check-in, release, and acknowledge operations frequently failed with `ledger did not sync (another sync is running; try again in a moment)` even immediately after `board sync` reported pull/push successful with zero pending changes.
- **Expected:** mutations should wait briefly for the ledger lock, retry safely, or enqueue an idempotent operation.
- **Suggested fix:** bounded lock waiting with ownership/progress output and an atomic mutation result.

### P0: shared shell identity conflates independent sessions

- **Observed:** `23237·agvidit (shell)` appeared to own four tasks while one session was working only on LibCST. After releases, ownership changed but `board here --json` still paired LibCST ownership with MapLibre as the last activity.
- **Expected:** ownership and current activity should be session-scoped and updated atomically.
- **Suggested fix:** issue a durable per-session identity/lease instead of keying mutable state only by host/user/shell.

### P1: commands are slow and silent, with ambiguous eventual completion

- **Observed:** `board here`, `board release`, `board show`, `board inbox`, and `board ack` often took 30–70 seconds with no output. Some continued after the caller timed out, leaving success unknown.
- **Expected:** immediate progress, bounded waits, and exactly one final result.
- **Suggested fix:** stream lock/sync phase status and make every mutation idempotently return `changed`, `already in desired state`, or an actionable failure.

### P1: `--json` output is not reliably JSON

- **Observed:** `board here --json` returned human-readable text.
- **Expected:** every `--json` mode must emit valid machine-readable JSON only, with diagnostics on stderr and a stable schema.

### P1: release and acknowledge outcomes are ambiguous

- **Observed:** a release produced no immediate output but appeared to complete later; a subsequent acknowledge reported `acked 0 message(s)` without distinguishing already-acknowledged from missing.
- **Expected:** explicit `released` / `already released` / `failed`, and `acknowledged` / `already acknowledged` / `not found` outcomes.

### P1: setup does not install required presubmit configuration

- **Observed:** `board check run <task> --role author` failed with `set [checks] presubmit in your config`.
- **Expected:** `board setup` should install required configuration or the error must give the exact config path and TOML snippet.

### P0: dirty worktrees can misattribute checks to the wrong commit

- **Observed:** presubmit/review recording defaults to the latest committed SHA even when the relevant task changes are uncommitted.
- **Risk:** evidence can be attached to bytes that were not actually checked.
- **Suggested fix:** refuse unsafe attribution and support a local content digest until a commit exists.

### P1: dashboard health and malformed ledger recovery are incomplete

- **Observed:** `board status --json` reported the dashboard unavailable on `127.0.0.1:8765` and `MALFORMED_EVENTS` for `6971.jsonl:424 bad commit`.
- **Expected:** quarantine malformed events with an actionable repair record, and make the dashboard watchdog restore service or explain why it cannot.

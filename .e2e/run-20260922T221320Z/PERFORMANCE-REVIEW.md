# Performance review — run-20260922T221320Z

## Executive verdict

**Neither: this was an incomplete, supervised source-loop exercise, not an autonomous end-to-end task-authoring loop.** It stopped at A3 with no survivor and never created a task or entered B-build/C-drive (`DONE:1-3`; `CHECKPOINT.md:12-17`). “No survivor” is a valid A3 substantive outcome, but the evidence loop was not trustworthy: every reviewed handoff is `FAIL`, including the post-review correction handoff (`review/01-A1-review.md:3-15`; `review/02-A2-review.md:3-17`; `review/03-A3-review.md:3-19`; `review/04-A2r2-review.md:3-18`; `review/05-CORRECTIONS-review.md:3-16`).

The run did make a sound final sourcing decision: none of the four candidates should be built (`CHECKPOINT.md:29-36`; `review/03-A3-review.md:33-42`). That useful decision does not establish autonomous execution of the playbook.

## Did the loop close?

The run reached `A1 → A2 → A3 → A2 round 2 → A3 round 2`, then wrote `DONE` with `NO SURVIVOR`; B1–B5 and C1–C6 were never started (`CHECKPOINT.md:12-17,19-27`; `DONE:1-3`). It therefore closed only the sourcing attempt, not the task-authoring and calibration loop.

The unattended path would have stopped or required outside judgement at these points:

1. **A1 exit:** zero repos had the checklist's required containerized G10 measurement, and five remained unmeasured (`handoffs/01-A1.md:12-31,369-374`). The router says an unmet act must not improvise forward, but the executor proceeded to A2 (`00-ROUTER.md:268-286`; `handoffs/01-A1.md:16-17,50`).
2. **A2 self-validation:** both emitted cards violated A2 rules while the act initially claimed completion; the reviewer, not the executor's checklist, caught the recall/decorative-cascade defects and invented rubric meanings (`review/02-A2-review.md:11-17,43-50`; `handoffs/05-CORRECTIONS.md:44-83`).
3. **A3 disclosure:** the decisive merged-history kill came from an unrequired function-scoped `git log -L`; the specified file-level history did not expose it (`friction.md:297-341`; `A-source/A3-idea-gate.md:116-141`). Without that extra judgement the run could have scaffolded a reversal of merged PR #1334 (`friction.md:321-328`).
4. **A3 Gate 4:** the declared primary outcome-variance probe requires a contract, grader and built task that do not exist until B2–B4, so it cannot be executed in A3 (`A-source/A3-idea-gate.md:143-180`; `friction.md:369-395`). The executor left it unrun and let the secondary design probe decide (`review/03-A3-review.md:14-15,23-25`).
5. **A2↔A3 termination:** A3 routes a dead set back to A2 but neither act defines re-entry evidence or a stopping threshold; the executor chose two rounds and stopped by judgement (`A-source/A3-idea-gate.md:284-286`; `friction.md:397-411`; `CHECKPOINT.md:52-54`).
6. **B2 tool dependency:** before B2 was reached, a coordinator had to repair `instruction-lint.py`; its full policy check now depends on B3-created tests, despite B2 declaring lint cleanliness as its exit (`friction.md:50-75`; `B-build/B2-contract.md:3-10,203-220`; `B-build/B3-grader.md:303-309`). This was supervision, not autonomous recovery.

## Handoff audit status

| Handoff | Verdict | Why |
|---|---|---|
| `01-A1.md` | **FAIL** | No prescribed container G10 proof; an unmet exit advanced to A2 (`review/01-A1-review.md:3-15`). |
| `02-A2.md` | **FAIL** | Auto-rejects, card completeness, surface accounting and canonical self-audits were falsely ticked (`review/02-A2-review.md:11-17`). |
| `03-A3.md` | **FAIL** | Gates 2, 3 and 5 lacked the per-candidate evidence claimed; Gate 4 was not run (`review/03-A3-review.md:11-19`). |
| `04-A2r2.md` | **FAIL** | No full cards or required self-audits, and the handoff was retroactive (`review/04-A2r2-review.md:11-18`). |
| `05-CORRECTIONS.md` | **FAIL** | Corrected headlines coexist with stale `DONE` tables and 17-as-18 accounting (`review/05-CORRECTIONS-review.md:5-16`). |

No handoff remains unreviewed.

## Autonomy score by phase

| Phase | Score | Evidence |
|---|---:|---|
| A-source | **1/5** | The run screened 36 repos, surveyed 18 lego surfaces, and killed four candidates (`CHECKPOINT.md:29-36,76-84`), but no A-source handoff satisfied its own evidence contract and the corrections required reviewer feedback (`review/01-A1-review.md:3-15`; `review/02-A2-review.md:3-17`; `review/03-A3-review.md:3-19`; `review/04-A2r2-review.md:3-18`; `handoffs/05-CORRECTIONS.md:3-10`). |
| B-build | **0/5 — not demonstrated** | No task directory, instruction, tests, solution, environment or B handoff exists (`CHECKPOINT.md:12-17,76-84`). |
| C-drive | **0/5 — not demonstrated** | Nothing was pushed or calibrated, and there are no server verdict, trial-replay or repair artifacts (`CHECKPOINT.md:12-17,96-98`; `DONE:1-3`). |

## Would the output be accepted?

**No. There is no SWE-bench-Pro task to submit.** The run created no task directory and stopped before B1, so structural validation fails at existence before oracle, calibration or Agentic Full-Task Review can run (`CHECKPOINT.md:12-17,76-84`). Those four acceptance surfaces are unattempted, not failed measurements.

The candidate-level decision is nevertheless sound:

- Every-Key-Type fails Gate 0 on three assertion-pinned coined tokens and is recall-shaped (`CHECKPOINT.md:31-34`; `review/03-A3-review.md:35-38`).
- No-Silent-Fallback reverses deliberate merged PR #1334 and is independently non-causal/unobservable as a two-step task (`CHECKPOINT.md:33-35`; `handoffs/05-CORRECTIONS.md:91-107`).
- Dead-responder/accountable-revocation is not a real cascade because the revocation step is implementable from the existing parsed bundle (`review/03-A3-review.md:35-40`).
- One-port/many-challenges is a plausible cascade, but all five approach probes selected the intended design and no implementation-level outcome variance was measured (`review/03-A3-review.md:37-40`; `handoffs/03-A3.md:204-240`). If built unchanged, calibration is the first likely substantive failure; that remains a risk, not a measurement.

No protected instruction file was created, so this stopped run contains no observed instruction-authorship leak (`CHECKPOINT.md:12-17`; `review/05-CORRECTIONS-review.md:24-28`).

## Executor defects

1. Advanced from A1 despite `EXIT: NOT MET`, contrary to the router (`handoffs/01-A1.md:12-17,50`; `00-ROUTER.md:285-286`).
2. Marked unsupported A2 and A3 checklist lines complete, including auto-rejects, rubric audits and per-candidate probes (`review/02-A2-review.md:11-17`; `review/03-A3-review.md:11-19`).
3. Ran A2 round 2 without a prior complete A2 handoff, then documented it retroactively (`review/04-A2r2-review.md:11-18,26-30`).
4. Amended only handoff headlines after review, leaving contradictory detailed checklist states (`review/05-CORRECTIONS-review.md:13-16,34-40`).

## Playbook defects, ranked

### Blocking

1. **A3's primary gate is temporally impossible.** It requires implementations from the task's contract graded against authored assertions before B2–B4 create any of those artifacts (`A-source/A3-idea-gate.md:143-180`; `00-ROUTER.md:47-53`). **Fix:** move outcome-variance measurement after B4, or define an explicitly throwaway A3 probe contract/grader with legal ownership.
2. **Run handoffs are not machine-enforced or append-only.** The router mandates evidence-bearing fields, but the checker validates only playbook act templates and explicitly excludes `.e2e`; the run consequently carried false ticks and later in-place amendments (`00-ROUTER.md:266-286`; `check-playbook.py:18-24,41-59`; `review/05-CORRECTIONS-review.md:5-22`). **Fix:** validate run handoffs, checklist arithmetic, allowed exit states and artifact existence; require versioned append-only amendments.
3. **A2↔A3 has no re-entry or exhaustion protocol.** A3 says to return to A2, but neither act specifies inherited evidence, mandatory fresh artifacts, or a round limit (`A-source/A2-idea-generate.md:265-299`; `A-source/A3-idea-gate.md:251-286`; `friction.md:397-411`). **Fix:** define a round-specific handoff and a bounded, evidence-based repo-exhaustion rule.
4. **A3 omits the highest-yield history check.** It prescribes file history but not function-scoped history or the closed-issue/merged-remedy case that killed Card 2 (`A-source/A3-idea-gate.md:116-141`; `friction.md:297-354`). **Fix:** require `git log -L` for each touched function and treat closed issues whose remedy merged as disclosure.
5. **B2's exit depends on an unversioned, two-phase external lint.** The tool was stale during the run and its complete pinning check cannot run until B3, while B2 still declares lint cleanliness as its own exit (`B-build/B2-contract.md:3-10,203-220`; `B-build/B3-grader.md:303-309`; `friction.md:50-75`). **Fix:** version/self-test the lint and split B2's pre-test check from B3's mandatory full check.
6. **The run has no frozen playbook/tool snapshot.** The monitor records that the router, B/C acts, checker and lint changed during execution, so later line citations and exit semantics do not necessarily describe the contract an earlier act saw (`review/monitor-receipt.md:8-9`; `friction.md:50-76`). **Fix:** record the playbook commit and tool hashes at run start; changes start a new run or an explicit version transition.

### Degrading

1. **A2's output-health gate accepts a real failure.** A plan-only response was 930 bytes and passed the `<600` check (`A-source/A2-idea-generate.md:105-122,278`; `friction.md:254-281`). **Fix:** require structural output tokens/schema, not byte count.
2. **A2 names rubric IDs without their canonical definitions.** Both cards consequently audited invented dimensions (`A-source/A2-idea-generate.md:244-251,282`; `friction.md:427-446`). **Fix:** link the canonical rubric table and require exact dimension names.
3. **A2 requires three composition layers while quarantining one.** The rule and worked example disagree (`A-source/A2-idea-generate.md:23-39`). **Fix:** require one choice from each live layer.
4. **A2 both recommends and auto-rejects “build-then-use” without defining causal dependence.** The ambiguity admitted a decorative cascade (`A-source/A2-idea-generate.md:89-93,182-186`; `review/02-A2-review.md:29-37`). **Fix:** define the HEAD-counterfactual/parallel-API tests at card creation.
5. **A1's subsystem metric can invert A2's survey sizing.** Lego's `SUB=262` mostly measured provider fan-out, while A2 is told to trust subsystem count (`A-source/A1-repo-screen.md:144-156`; `A-source/A2-idea-generate.md:51-60`; `friction.md:234-252`). **Fix:** report `SUB_distinct` and `SUB_fanout` separately.
6. **Feature disclosure has no single owner or complete checklist step.** Repo, candidate and function sweeps were repeated, while the decisive scope was absent (`A-source/A2-idea-generate.md:270-284`; `A-source/A3-idea-gate.md:116-141`; `friction.md:413-425`). **Fix:** define one three-scope disclosure procedure and invoke it from A2/A3.
7. **A3's aggregate checklist hides per-candidate omissions.** Its proof requirements are per card, but one status is reported per gate (`A-source/A3-idea-gate.md:251-270`; `review/03-A3-review.md:11-19`). **Fix:** require a candidate-by-gate evidence matrix.

### Already mitigated during this run

The missing Docker serialization mechanism that blocked G10 is now described in the working router, including `flock`, holder identity and an A1 split (`friction.md:135-155`; `00-ROUTER.md:203-230`). It should be committed and covered by the frozen-version rule before the next run.

## What a human still has to do

1. Choose the next sourcing action: resurvey lego under a different live axis, or finish container G10 on `nmstate`, `mina-sshd` and `spire` before selecting another repo (`CHECKPOINT.md:56-74`).
2. Fix and commit the blocking playbook defects above, then start a run pinned to that playbook/tool version (`review/monitor-receipt.md:8-9`; `friction.md:50-75`).
3. Require every future A2 round to emit full numbered cards, exact canonical rubric audits and complete surface accounting before A3 begins (`review/04-A2r2-review.md:11-24`; `review/05-CORRECTIONS-review.md:13-16`).
4. Put implementation-level outcome variance at a stage where a contract, grader and image exist; do not substitute approach descriptions for executions (`A-source/A3-idea-gate.md:143-180`; `review/03-A3-review.md:21-25`).
5. If a candidate survives, execute all of B1–B5 and C1–C6: authorized contract authoring, grader construction, oracle 3/3, preflight/push, server calibration, trajectory review and replay. None was exercised here (`CHECKPOINT.md:12-17`).
6. Preserve the ownership boundary: only Avocado/MetaCode or the human may write future instruction files; Claude/Codex may not draft exact replacement prose indirectly (`00-ROUTER.md:162-197`).

## Final verdict

**Neither.** The run produced valuable rejection evidence, but it did not produce a task, did not exercise B-build or C-drive, required coordinator/reviewer intervention, and never emitted a handoff that passed its own evidence contract (`DONE:1-3`; `review/01-A1-review.md:3-15`; `review/02-A2-review.md:3-17`; `review/03-A3-review.md:3-19`; `review/04-A2r2-review.md:3-18`; `review/05-CORRECTIONS-review.md:3-16`).

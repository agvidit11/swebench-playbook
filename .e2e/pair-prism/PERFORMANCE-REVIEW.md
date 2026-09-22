# Performance Review — pair-prism

## Executive verdict

The loop did **not** close. It reached A2 and A3, produced no survivor and no task directory, then wrote `DONE` even though the A3 handoff's own `NEXT` points back to A2 (`handoffs/02-A3.md:21-24`) and the act schema prescribes the same route for no survivor (`A-source/A3-idea-gate.md:273-286`). Both reviewed acts are `FAIL`: A2 overclaimed two checklist lines and needed reviewer correction (`review/01-A2-review.md:3-15`); A3 overclaimed multiple per-card gates and misread its headline fork evidence (`review/02-A3-review.md:3-18`).

**Final classification: neither a complete autonomous loop nor a functioning supervised task-production loop.** It is a useful supervised sourcing experiment that terminated without producing a SWE-bench-Pro task.

## Did the loop close?

No. The run progressed from the inherited shortlist into eight A2 cards and then an A3 no-survivor decision. B1–B5 and all of C-drive were never entered, and the run explicitly records that no task directory exists (`CHECKPOINT.md:4-12,19-35`; `DONE:1`). That is a valid *local* A3 outcome only if the orchestrator follows the prescribed return edge. Instead it converted “back to A2” into terminal `DONE` (`CHECKPOINT.md:64-70`).

The unattended stall/failure points were:

1. **A2 dispatch integrity.** MetaCode silently shell-expanded a backticked prompt clause and returned plausible output; the executor noticed but did not restart (`friction.md:74-97`; `handoffs/01-A2.md:35-36`). An unattended run has no trustworthy prompt receipt here.
2. **A2 evidence gate.** The executor initially reported `13 of 13` although card files and four deferred audit rows were absent. The external reviewer caught both; the corrected handoff now admits `11 of 13`, with one requirement still failed (`review/01-A2-review.md:3-15`; `handoffs/01-A2.md:10-12,39-41`). Without review, A3 would have consumed a falsely complete handoff.
3. **A3 evidence gate.** A3 reports `13 of 14` despite refusing GATE 0, not running GATE 4, incompletely auditing multiple per-card gates, and misclassifying its ten prose plans (`handoffs/02-A3.md:11-12,61-91,197-233`; `review/02-A3-review.md:9-18`). No internal mechanism caught the same failure mode that had just occurred at A2.
4. **No-survivor routing.** The playbook supplies only “back to A2” for no survivor, no retry budget or repo-rejection state, and no next-shortlist selection protocol (`A-source/A3-idea-gate.md:273-286`; `friction.md:366-376`). The executor stopped instead. A human must decide whether to retry Prism, reject it, or choose the next screened repo.

## Handoff results

| Handoff | Verdict | Reason |
|---|---|---|
| `01-A2.md` | **FAIL** | Required per-card artifacts and four deferred audit rows were missing behind a `13/13` claim; one weak card was retained to hit the numeric target (`review/01-A2-review.md:3-15,39-44`). The later correction created card files but deliberately left checklist line 11 failed (`handoffs/01-A2.md:39-55`). |
| `02-A3.md` | **FAIL** | Multiple ticked per-card gates lack evidence; GATE 4 was absent; `10/10 desired` reverses outputs that chose full-buffer recomputation; the kill table is not sound under the executor's own refusal to apply GATE 0 (`review/02-A3-review.md:3-18,38-45`). |

## Autonomy score by phase

Scale: 0 = not demonstrated; 5 = closes the phase unattended with trustworthy evidence.

| Phase | Score | Evidence |
|---|---:|---|
| **A-source** | **1/5** | It generated broad evidence, independently rejected several shortlist suggestions, and found real public-disclosure and hollow-premise kills (`review/02-A3-review.md:20-24`). But both acts failed their own checklists, A2 required external correction, A3 repeated unsupported ticking, and no-survivor routing stopped rather than looping (`review/01-A2-review.md:3-21`; `review/02-A3-review.md:3-18`; `CHECKPOINT.md:64-70`). |
| **B-build** | **0/5 demonstrated** | Never entered; no task dir, contract, grader, solution, environment, oracle result, preflight, commit, or push exists (`CHECKPOINT.md:5-7,34`). |
| **C-drive** | **0/5 demonstrated** | Never entered; there is no server task, verdict, calibration cohort, repair, replay, or acceptance evidence (`DONE:1`). |

The score is not a judgement that B/C are defective in the abstract; this run provides no evidence that they operate autonomously.

## Would the output be accepted?

No output exists that could be submitted.

- **Structural checks:** fail first by absence—B1 never created a task directory or required files (`CHECKPOINT.md:5-7,34`).
- **Oracle:** cannot run; there is no contract, grader, solution patch, or environment.
- **Calibration band:** cannot run; the ten A3 outputs are prose-only design priors, not five implementations graded against assertions (`review/02-A3-review.md:13-15`).
- **Agentic review:** cannot run; there is no task artifact.

Substantively, I would green-light none of the current eight cards. Six have persuasive early kills, while C07/C08 are rejected by current GATE 0 unless a formal override is created (`review/02-A3-review.md:32-36`). I would not blacklist Prism categorically: the repo-level R05 conclusion confuses “reference is available” with “reference output exactly satisfies the graded contract,” and its own Ripper comparison is unequal (`review/02-A3-review.md:14-15,34-36`).

## Playbook defects — ranked

### Blocking

1. **No terminal routing for a repo with zero A3 survivors.** A3 says return to A2 but provides no retry budget, repo-rejection state, or next-shortlist selection (`A-source/A3-idea-gate.md:273-286`). **Fix:** add an explicit state: retry A2 at most N times, then record a repo kill and route to the next A1 survivor; reserve `DONE` for an accepted task or exhausted shortlist.
2. **A3's per-card evidence cannot be represented by its aggregate checklist.** The checklist is “per candidate card,” while the HANDOFF exposes one `n of 14` (`A-source/A3-idea-gate.md:251-276`). **Fix:** require a card × gate matrix with `PASS`, `KILLED`, or `WAIVED`, and evidence for every non-unreached cell.
3. **A3 orders two free gates after fifteen model calls.** GATE 6 and GATE 7 are free but follow GATE 4/5 in the declared “whole economy” (`A-source/A3-idea-gate.md:12-26,206-228`). **Fix:** order `0,1,2,3,6,7,4,5,8`; a killed card terminates its row explicitly.
4. **The instruction-lint contract is contradictory.** A3 says named+pinned COINED tokens are lint-legal but still need a GATE-0 override (`A-source/A3-idea-gate.md:63-72`); B2 says the lint still implements absolute never-name and fails those tokens (`B-build/B2-contract.md:203-216`). **Fix:** pin one lint version/behavior in both files and test it with named+pinned, named-unpinned, and unnamed-pinned fixtures.
5. **MetaCode prompt transport is not literal.** A2 presents `mc.sh` as the mandatory safe wrapper, but a backtick/`!` clause was executed and deleted while the command returned plausible output (`A-source/A2-idea-generate.md:105-122`; `friction.md:74-97`). **Fix:** pass prompt bytes through a literal file/stdin interface and verify a content digest before accepting output.
6. **A2 can be entered without its required input, but the router forbids that.** This assignment started at A2 with a prose shortlist; A2 requires a literal A1 HANDOFF, and the router says no act begins without it (`A-source/A2-idea-generate.md:5-8,270-272`; `00-ROUTER.md:205-216`). **Fix:** define an import/resume HANDOFF schema for pre-screened repos and make the router recognize it.

### Degrading

1. **A2's card count incentives conflict.** The output says `≥8`, while the body expects 2–4 and forbids backfill (`A-source/A2-idea-generate.md:5-8,47-60`). This directly produced a designated weak eighth card (`handoffs/01-A2.md:41-52`). **Fix:** set the numeric target on surfaces only; cards are uncapped and evidence-selected.
2. **GATE 5 lacks a predeclared scoring key.** It asks for three-sentence approaches but not a verbatim constraint or a before-run definition of desired versus wrong path (`A-source/A3-idea-gate.md:182-204`). **Fix:** freeze the constraint and classification rubric before dispatch, then quote the decisive sentence from every output.
3. **The conformance checker scans run artifacts as playbook source.** Its walker excludes only `.git` (`check-playbook.py:18-23`); on this checkout it exits 1 with 26 dangling-link failures, mostly under unrelated `.e2e` runs. **Fix:** restrict inputs to `00-ROUTER.md`, act directories, `reference/`, and `ledger/`, or exclude `.e2e`.
4. **No mechanical handoff-evidence validator exists.** Router §8 defines fields but only trusts the reported count (`00-ROUTER.md:205-216`); the same unsupported-tick failure occurred in both A2 and A3 (`review/01-A2-review.md:3-15`; `review/02-A3-review.md:3-18`). **Fix:** add a handoff lint that checks named paths, required rows, and per-card matrices before advancing state.

## What a human still has to do

1. Decide Prism's disposition: retry with a new lens, record a repo-level rejection, or select the next screened repo. The playbook cannot make this transition (`handoffs/02-A3.md:21-24`; `friction.md:366-376`).
2. Reject or formally override the seven COINED cards under current GATE 0; the executor left that decision unresolved (`handoffs/02-A3.md:66-91`).
3. If Prism is retried, commission a new A2 pass rather than repairing these cards in place, and independently validate any survivor with actual GATE 4 implementations plus a correctly constrained GATE 5 probe (`A-source/A3-idea-gate.md:10,143-180,182-204`).
4. Resolve the A3/B2 lint contradiction before a coined-interface candidate enters B2 (`A-source/A3-idea-gate.md:63-72`; `B-build/B2-contract.md:203-216`).
5. Repair prompt transport or manually inspect every dispatched prompt receipt for shell-expansion loss (`friction.md:74-97`).
6. Continue reviewing every handoff: this run demonstrates that self-reported checklist totals are not reliable without artifact inspection (`review/01-A2-review.md:3-21`; `review/02-A3-review.md:3-24`).
7. If a survivor is eventually found, perform all of B-build and C-drive; none of their structural, oracle, calibration, replay, or review obligations has been exercised here.

## Verdict

**Neither.** The run is not a complete autonomous loop because it produced no task and stopped against its own next-state edge. It is not yet a supervised task-production loop either, because supervision caught defects but did not carry a task through B-build/C-drive. The honest description is: **a supervised sourcing experiment with useful negative evidence and an unclosed control loop**.

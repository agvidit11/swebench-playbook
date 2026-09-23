# Performance review — redo-frostdb

## Did the loop close?

The re-adjudication subloop closed; the task-authoring loop did not. It reached an evidenced A3 `NO SURVIVOR` and stopped before B1 (`DONE:1-3`). It produced no task directory, commit, push, structural result, oracle result, calibration run, or agentic review (`DONE:25`). That is a legitimate result for this candidate, but it does not satisfy tonight's objective of one submitted task.

The run would not have reached this reliable conclusion unattended. Its first handoff declared C1 “ALIVE” while GATE 4 was still running (`handoffs/00-A3-interim.md:3-8,38`). The reviewer then identified the EOF proxy, wall-clock dependency, misapplied merged-precedent rule, and A2/A3 card-ownership gap (`review/00-A3-interim-review.md:13,19-38`). The final handoff explicitly says those reviewer findings were adopted (`handoffs/01-A3.md:403-411`). Without that intervention, the candidate was at risk of resurrection on incomplete evidence; after the intervention, the executor's own adversarial audit independently confirmed that S2 was a proxy (`artifacts/kill-audit-codex.md:5-13`).

There is also no autonomous no-survivor continuation. A3 says a dead candidate goes back to A2 (`A-source/A3-idea-gate.md:10`), and the router now maps `NO SURVIVOR` back to A2 (`00-ROUTER.md:24-26`), while the executor instead declared the run terminal (`handoffs/01-A3.md:417-428`). That stop may be sensible for frostdb, but it relies on the coordinator brief rather than a closed playbook route to another viable repo.

## Autonomy by phase

| Phase | Score | Evidence |
|---|---:|---|
| A-source | **2/5** | The executor generated real probe receipts, corrected the GATE-5 direction to 4/5 and 5/5 NON-DESIRED, and reached the substantively right no-survivor decision (`handoffs/01-A3.md:180-226,369-394`). It still needed reviewer intervention, mutated its A2 input, and continued to call an admitted proxy a valid GATE-4 kill (`handoffs/01-A3.md:228-290,343-350,403-411`). |
| B-build | **0/5 (unexercised)** | No survivor and no B1 task directory (`handoffs/01-A3.md:48-49`; `DONE:3,25`). |
| C-drive | **0/5 (unexercised)** | No push or server-side validation existed to diagnose or drive (`DONE:25`). |

## Would the output be accepted?

There is no task output to accept. Structural checks, oracle validation, calibration, and Agentic Full-Task Review are all unmeasured because B-build never started (`DONE:3,25`).

If C1 had been built from the measured contract, it would fail first at sourcing/review, before submission:

1. The desired “whole block is never held” property is not observable through `Upload(..., io.Reader)`; all five whole-block implementations pass the proposed black-box assertions (`handoffs/01-A3.md:271-290,343-350`).
2. Its discriminator relies on a five-second absence of EOF, violating the Tier-0 no-wall-clock rule (`probes/g4redo_assert_test.go:235-248`; `A-source/A3-idea-gate.md:330-342`).
3. The local outcome probe is 5/5, outside the 1–3/5 target even on its weaker predicate (`artifacts/gate4/graded-impl-1.txt:1-11`; `graded-impl-5.txt:1-11`; `A-source/A3-idea-gate.md:254-267`).
4. Merged commit `6169cce` publicly applied the same buffer-to-pipe remedy on `Persist`, triggering GATE 3 (`handoffs/01-A3.md:124-150`; `A-source/A3-idea-gate.md:175-177`).

My professional call: do not submit or revive this candidate. The corrected 9/10 wrong-path prior is a real fork, but it is not a gradeable fork (`cards/C1-multisink-persist.md:36-44`; `handoffs/01-A3.md:223-226`).

## Playbook defects, ranked

### Blocking

1. **A2/A3 schema and ownership do not join.** A2's mandatory card schema omits `CONSTRAINT`, `DESIRED`, and `NON-DESIRED` (`A-source/A2-idea-generate.md:124-140`), while A3 requires those fields already declared on the card before probing (`A-source/A3-idea-gate.md:279-300`). This forced Claude to edit an A2 input (`cards/C1-multisink-persist.md:9-24`). **Fix:** make the A2/MetaCode card author populate the three fields.
2. **GATE 4's control can validate the wrong thing.** The current three-way check asks for a NON-DESIRED negative control (`A-source/A3-idea-gate.md:215-230`), but the executor used an ungated buffer even though the actual countermodel is a gated buffer; all five such implementations passed (`handoffs/01-A3.md:255-290`). **Fix:** require an adversarial countermodel that violates DESIRED while satisfying every surface-level constraint; any such passing model invalidates the sketch rather than becoming a 5/5 kill.
3. **No bounded repo-exhaustion route exists.** Both A3 and the router send `NO SURVIVOR` back to A2 (`A-source/A3-idea-gate.md:10`; `00-ROUTER.md:24-26`), but define neither an exhaustion budget nor a route back to A1. **Fix:** add an evidenced `REPO EXHAUSTED -> A1`/terminal state with explicit thresholds.
4. **The evaluation contract changed during the run.** Commit `432a3cb` was created at 2026-09-23 00:39:59Z and rewrote the router, A3, and `probe-lint.py` using this run's findings; the resulting text now cites frostdb directly (`A-source/A3-idea-gate.md:78-105`; `tools/probe-lint.py:47-50`). **Fix:** pin the playbook SHA in every run and apply improvements only after its performance review.

### Degrading

5. **GATE 3's merged-PR wording is overbroad.** “Any merged public PR touching the surface” can include irrelevant maintenance (`A-source/A3-idea-gate.md:175-177`). Here the result remains a kill because `6169cce` contains the actual buffer-to-pipe remedy. **Fix:** say the diff/thread must publish the candidate's remedy or direction on that surface.
6. **Probe lint measures vocabulary overlap, not semantic clause coverage.** It warns on the deliberately non-leading B phrasing despite that prompt preserving all four clauses (`tools/probe-lint.py:82-108`; `artifacts/probe-lint.txt:1-4`; `probes/c1-step2-B.txt:7-21`). **Fix:** lint named semantic clauses, not a bag-of-words ratio.
7. **The run-start `--outputs` path was broken.** The documented option treated its directory as a probe (`e744c14:tools/probe-lint.py:47-54`). It was repaired in the mid-run commit (`tools/probe-lint.py:47-61`), but the original defect removed the branch that prints the mapping reminder. **Fix:** retained as implemented; add a regression test.
8. **Handoffs are not explicitly immutable.** The executor corrected an already-reviewed interim file in place (`handoffs/01-A3.md:409-411`; `DONE:27-28`). **Fix:** require append-only addenda so reviews remain bound to the bytes they audited.

## What a human still has to do

1. Choose another repo or explicitly authorize a fresh A2 search; frostdb has no surviving multi-turn card (`handoffs/01-A3.md:417-428`).
2. Resolve the A2/A3 schema ownership gap before the next probe so Claude never has to author fields on an A2 card (`A-source/A2-idea-generate.md:124-140`; `A-source/A3-idea-gate.md:279-300`).
3. Pin a playbook commit for the next end-to-end trial; do not merge process fixes into the contract being measured.
4. Independently reject assertion sketches that admit a DESIRED-violating countermodel; a simple positive/negative control pair was insufficient here (`handoffs/01-A3.md:255-290,343-350`).
5. Once a genuine survivor exists, complete every unexercised B-build and C-drive act through the five done surfaces (`00-ROUTER.md:126-155`).

## Verdict

**Supervised loop, incomplete end to end.** The re-adjudication ended at the correct substantive decision—C1 deserves to stay dead—but human review was material to that decision, the claimed GATE-4 instrument remained invalid, the playbook changed under the run, and no task was built or submitted.

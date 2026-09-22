# Review 02 — A3 idea gate

## Verdict: FAIL

The reported “no survivor” exit is not established. C2 is credibly dead, but C1 was tested against a weaker contract and its outputs were classified backwards. A3 requires an evidenced killing gate for every card (`A-source/A3-idea-gate.md:5-10,272-286`); C1 has none on the evidence actually saved.

## Checklist audit

| Item spot-checked | Result | Evidence |
|---|---|---|
| 2 — GATE 0 namability | Partial / unsupported tick | C1 has an explicit assertion sketch and token inventory (`handoffs/02-A3.md:44-71`). C2 has only a symbol list (`handoffs/02-A3.md:73-78`), not the exact code-level assertion Gate 0 requires (`A-source/A3-idea-gate.md:34-39`). |
| 5 — GATE 2 hollow premise | Pass | The base source contains the multi-sink refusal (`/tmp/frostdb-run/frostdb/store.go:35-38`) and the computed-operand TODO (`/tmp/frostdb-run/frostdb/query/physicalplan/aggregate.go:33-36`). The handoff records executed base behavior for both (`handoffs/02-A3.md:134-156`). |
| 6 — GATE 3 disclosure | Pass for C2; evidence-thin for C1 | C2's checked-in fixture says an ordered aggregation should be planned but records `HashAggregate` (`/tmp/frostdb-run/frostdb/logictest/testdata/plan/aggregate/aggregate:12-23`) and the handoff quotes PR #307's latent-bug warning (`handoffs/02-A3.md:189-232`). C1's six result counts are recorded only in the handoff; raw search output was not retained (`handoffs/02-A3.md:168-187`). |
| 7 — GATE 4 outcome variance | **Fail** | C2 was never probed (`handoffs/02-A3.md:383-389`), yet the checklist claims every item except GATE 8 was ticked (`handoffs/02-A3.md:14-15`). For C1, the card requires the step-1 buffer to disappear and both uploads to begin before serialization completes (`cards/C1-multisink-persist.md:9,13-15`); the implementation brief merely requires serialize-once plus concurrent uploads (`probes/c1-impl.txt:19-40`), and the test gates one upload on the other's start but never observes serialization completion (`probes/gate4_assert_test.go:153-179`). All five saved implementations fully serialize into `bytes.Buffer` before starting uploads (`probes/gate4-impl-1.patch:45-59`; `gate4-impl-2.patch:74-96`; `gate4-impl-3.patch:41-59`; `gate4-impl-4.patch:41-62`; `gate4-impl-5.patch:41-57`). Thus 5/5 measures a weaker task, not C1. |
| 8 — GATE 5 fork probe | **Fail** | Both prompts omit C1's bounded-memory / upload-before-serialization condition (`probes/c1-step2-A.txt:3-13`; `probes/c1-step2-B.txt:3-11`). The returned `bytes.Buffer` design is step 1's materialization path, which the card says step 2 must remove (`cards/C1-multisink-persist.md:9,13,51`). Calling those ten outputs “desired” (`handoffs/02-A3.md:297-315`) reverses the gate's rule: ≥4/5 choosing the non-desired path is a strong fork (`A-source/A3-idea-gate.md:194-198`). |
| 9 — GATE 6 | Partial | The measured 39–67-line, one-file implementations do fail the size target (`handoffs/02-A3.md:282-287,332-342`). But the determinism claim says there is no wall-clock dependency while the probe uses 10-second and 25-second `time.After` failures (`probes/gate4_assert_test.go:57,171,194`). |
| 10 — GATE 7 cascade | Unsupported tick | The handoff says the parallel-API test was “moot” rather than run and gives no C2 cascade audit (`handoffs/02-A3.md:344-354`). The checklist nevertheless reports only GATE 8 as N/A (`handoffs/02-A3.md:14-15`). |
| 11 — GATE 8 score | Improperly waived downstream of the C1 error | Scoring is survivors-only (`A-source/A3-idea-gate.md:230-245`), but C1 was not validly killed, so the N/A conclusion is premature (`handoffs/02-A3.md:356`). |
| 13 — rank / no survivor | **Fail** | C2 has a supported kill; C1 does not. The claimed no-survivor state (`handoffs/02-A3.md:5-13`) therefore does not meet the exit condition (`A-source/A3-idea-gate.md:5-10`). |

The explicit checklist contradiction—only item 11 waived while GATE 4 for C2 and the parallel-API test were not run—is independently sufficient for `FAIL` under the review rule that a tick without evidence fails the act (`handoffs/02-A3.md:14-15,348,383-389`).

## Evidence quality

The saved Gate-5 outputs are real and useful; all ten C1 outputs choose a full immutable buffer (for example `probes/gate5-c1A-1.out:1` and `probes/gate5-c1B-1.out:3`). The five implementation patches likewise independently converge on `bytes.Buffer` (`probes/gate4-impl-1.patch:45-59`; `probes/gate4-impl-5.patch:41-57`). Those measurements are not copied playbook examples—but they contradict the reported classification.

The 5/5 test and upstream-suite timings are asserted in a summary table (`handoffs/02-A3.md:262-270`), but no command-output log is among the declared artifacts (`handoffs/02-A3.md:16-23`). The patches and test exist, so the runs are plausible; the exact pass/timing numbers remain claims taken on trust.

## Boundary check

No instruction file exists in the run, and the handoff says none was drafted or planned (`handoffs/02-A3.md:390-391`). A3's saved products are probe prompts, model outputs, patches, and a temporary verification test, all within A3's verification role (`A-source/A3-idea-gate.md:5-10`). No protected-prose leak was found.

The act did overstep its process boundary in a different way: after declaring no survivor, its own `NEXT` points back to A2, but it instead wrote `DONE` (`handoffs/02-A3.md:26-27,402-420`; `DONE:1-7`). That is not an ownership breach, but it is an unauthorized terminal decision under the router (`00-ROUTER.md:21-24,215-216`).

## Director's call

C2 should stay dead. Its desired direction is already called out in a shipped fixture, the ordered path is dormant in those fixtures, and ten independent probes locate the same planner change (`handoffs/02-A3.md:189-232,317-328`). I would not build it.

C1 should not be green-lit for B1 yet, but it should not have been killed. The actual result is: ten models chose the buffered wrong path, exactly the behavior the card intended step 2 to invalidate (`cards/C1-multisink-persist.md:9,13-15`; `handoffs/02-A3.md:297-315`). That is evidence of a potentially strong fork. A fresh A3 pass must decide whether the stream-before-completion / bounded-retention behavior is feasible, deterministic, and grader-name-free, then probe that exact behavior. If it cannot be tested without a cost constraint or timing assumption, kill it at GATE 1 or GATE 6 with that evidence.

## Defect ownership

### Executor defects

- The C1 probe silently weakened the card, then classified the card's explicitly forbidden buffer as the desired solution (`cards/C1-multisink-persist.md:9,13-15`; `probes/c1-impl.txt:19-40`; `handoffs/02-A3.md:297-315`).
- The 5/5 result does not cover C1's claimed difficulty carrier because the assertion never observes serialization completion or bounded retention (`probes/gate4_assert_test.go:153-179`; `handoffs/02-A3.md:363-368`).
- The handoff reports 13/14 with only GATE 8 waived despite admitting GATE 4 was not run for C2 and the parallel-API test was not run (`handoffs/02-A3.md:14-15,348,383-389`). This is a false checklist claim.
- C2's Gate-0 tick lacks the exact written assertion and token-by-token proof required by the gate (`handoffs/02-A3.md:73-78`; `A-source/A3-idea-gate.md:34-39`).
- The executor stopped after A3 despite recording A2 as the required next act (`handoffs/02-A3.md:26-27,402-420`; `DONE:5-7`).

### Playbook defects

- GATE 4 requires grading five implementations but no explicit card-requirement-to-assertion coverage check, which permits a probe to measure a weaker contract (`A-source/A3-idea-gate.md:159-166,263`). Fix: require a row for every card invariant and reject the probe if any is unobserved.
- GATE 5 does not require the card's desired and named-wrong paths to be copied into a classification table before counting outputs (`A-source/A3-idea-gate.md:182-204,264`). Fix: predeclare those labels and classify each saved output against them.
- The per-candidate checklist has no explicit post-kill N/A accounting, encouraging a global “13/14” even when candidate-specific checks were skipped (`A-source/A3-idea-gate.md:251-270`). Fix: require one matrix row per candidate × gate with PASS/FAIL/SKIPPED and evidence.
- The no-survivor route loops to A2 forever and defines no evidence-based repo-exhausted terminal (`A-source/A3-idea-gate.md:273-286`; `00-ROUTER.md:21-24`). Fix: add an exhaustion budget and route exhausted repos back to A1 or to a terminal `NO TASK` state.

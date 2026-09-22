# Performance Review — pair-frostdb

## Did the loop close?

No. It completed A2 and reached an A3 decision, but then terminated without a task (`DONE:1-7`). The router says a no-survivor A3 returns to A2, and incomplete work must not improvise forward (`A-source/A3-idea-gate.md:273-286`; `00-ROUTER.md:215-216`). The executor instead declared the repository exhausted and wrote `DONE` (`handoffs/02-A3.md:402-420`).

More importantly, the terminal decision is wrong on its own evidence. C1's card says the step-1 full buffer must be removed and both uploads must start before serialization completes (`cards/C1-multisink-persist.md:9,13-15`). The A3 prompts omit that condition (`probes/c1-step2-A.txt:3-13`; `probes/c1-step2-B.txt:3-11`), the assertion never observes serialization completion (`probes/gate4_assert_test.go:153-179`), and all five implementations fully buffer before upload (`probes/gate4-impl-1.patch:45-59`; `gate4-impl-2.patch:74-96`; `gate4-impl-3.patch:41-59`; `gate4-impl-4.patch:41-62`; `gate4-impl-5.patch:41-57`). Those are the card's wrong-path implementations, not “10/10 desired.” Under A3's own mapping, ≥4/5 on the non-desired path is evidence of a strong fork (`A-source/A3-idea-gate.md:194-198`).

Without a human, the loop does not stall; it exits falsely at A3 and produces nothing. Earlier, it also had to invent local policy for the missing A1 handoff, the A2 card-authoring dispatch, and the no-survivor terminal (`handoffs/01-A2.md:204-209`; `friction.md:51-81`; `handoffs/02-A3.md:402-420`).

## Autonomy score by phase

Scale: 0 = not demonstrated, 5 = completes the phase correctly without human judgment.

| Phase | Score | Evidence |
|---|---:|---|
| A-source | **2/5** | A2 produced grounded cards and caught three hollow premises (`handoffs/01-A2.md:94-114`), and A3 correctly killed C2 on public disclosure (`handoffs/02-A3.md:189-232`). But A3 weakened C1's contract, reversed the fork classification, falsely ticked skipped checks, and stopped outside the declared route (`cards/C1-multisink-persist.md:9-15`; `probes/c1-impl.txt:19-40`; `handoffs/02-A3.md:14-15,297-315,383-420`). |
| B-build | **0/5 demonstrated** | No task directory was created and B1–B5 were never entered (`DONE:5-7`). This is untested, not evidence that B-build itself would fail. |
| C-drive | **0/5 demonstrated** | Nothing was pushed and no server state, oracle, calibration, or review loop ran (`DONE:5-7`). |

## Would the output be accepted?

No output exists to accept: there is no task directory, contract, grader, solution, environment, commit, or push (`DONE:5-7`). It therefore cannot reach structural checks, oracle validation, calibration, or Agentic Full-Task Review.

If C1 were built using the probe contract and assertion as saved, the first likely substantive failure would be calibration or task review: the measured implementations pass 5/5 (`handoffs/02-A3.md:262-273`), while the test omits the card's stream-before-serialization / buffer-removal invariant (`cards/C1-multisink-persist.md:13-15`; `probes/gate4_assert_test.go:153-179`). That is both an easy-task signal and a stated-requirement coverage gap. The intended C1 may still be viable, but it is unmeasured. C2 should not proceed because the behavior is publicly documented and the relevant path is deliberately guarded as latent-risk (`handoffs/02-A3.md:189-232`).

## Playbook defects, ranked

### Blocking

1. **No evidence-based terminal for an exhausted repo.** A3's no-survivor handoff routes back to A2 indefinitely (`A-source/A3-idea-gate.md:273-286`), while the router forbids improvising forward (`00-ROUTER.md:215-216`). **Fix:** add a finite resurvey budget and an explicit `NO TASK / return to A1` terminal.
2. **Gate 4 can measure a weaker task than the card.** It asks for five implementations “from the task's own contract” but requires no invariant-to-assertion coverage proof (`A-source/A3-idea-gate.md:159-166,263`). That omission permitted C1's actual difficulty carrier to disappear. **Fix:** require a card-invariant coverage table and a negative control for every claimed discriminator before counting the n=5 result.
3. **Gate 5 can invert desired and wrong paths without detection.** The rule defines the numerical mapping but the checklist does not require predeclared desired/wrong labels copied from the card (`A-source/A3-idea-gate.md:194-204,264`). **Fix:** classify each saved output against a frozen card-derived path table before calculating the ratio.
4. **The conformance checker cannot cleanly check the playbook in a live workspace.** It recursively ingests every Markdown file below the repo, including `.e2e` run artifacts (`check-playbook.py:18-35`), and treats inline task-relative examples such as `gate0-override.md` as repository links (`check-playbook.py:58-98`; `A-source/A3-idea-gate.md:50-51`). On this run `python3 check-playbook.py` returned `26 fail, 92 warn`, dominated by run-artifact paths. **Fix:** restrict checking to declared playbook directories and distinguish navigational Markdown links from inline example paths.

### Degrading

1. **A2 has no normalized input for a pre-existing shortlist.** Its input and checklist require an A1 HANDOFF (`A-source/A2-idea-generate.md:6,272`), while the router sends any already-picked repo directly to A2 (`00-ROUTER.md:21-24`). **Fix:** define a shortlist receipt schema equivalent to A1 FACTS.
2. **Surface sizing is not deterministic.** The LOC band and “2–3 per major subsystem” can conflict, and “major subsystem” has no threshold (`A-source/A2-idea-generate.md:51-60`). **Fix:** define the qualifying subsystem rule and a single tie-break formula.
3. **A2's audit vocabulary is internally unsafe.** A self-reported FAIL must kill or be repaired, but every card must also carry a non-PASS row or residual risk (`A-source/A2-idea-generate.md:244-263`). **Fix:** add `RISK` as a non-failing status and reserve `FAIL` for rejection.
4. **The A2 owner transition is under-specified.** Tooling documents a survey dispatch, while later checklist items require merge, rejection, card writing, and self-audit by the declared owner (`A-source/A2-idea-generate.md:5,105-122,279-282`). **Fix:** document the second MetaCode card pass explicitly.
5. **A3's per-candidate checklist collapses into one global count.** It does not prescribe how later gates are marked after an earlier kill (`A-source/A3-idea-gate.md:251-270`), enabling “13/14” while C2 Gate 4 and C1's parallel-API test were skipped (`handoffs/02-A3.md:14-15,348,383-389`). **Fix:** require a candidate × gate matrix with `PASS`, `KILL`, or `SKIPPED-BECAUSE` and evidence in every cell.
6. **The disclosure search example is Java-specific.** It searches only `<clone>/src/test`, while FrostDB's decisive public artifact was under `logictest/testdata` (`A-source/A3-idea-gate.md:122-141`; `/tmp/frostdb-run/frostdb/logictest/testdata/plan/aggregate/aggregate:12-23`). **Fix:** prescribe repository-wide test/fixture/golden discovery plus following links named in PR bodies.
7. **A3 requires execution for hollow-premise checks but supplies only a grep recipe and no clean-worktree protocol** (`A-source/A3-idea-gate.md:104-115`). **Fix:** provide a task-scoped throwaway-checkout recipe and require a clean status receipt afterward.
8. **Probe command output is not a required retained artifact.** The checklist asks for outputs but does not require logs (`A-source/A3-idea-gate.md:263-264`); this run preserved patches and prose outputs but not the Gate-4 test stdout (`handoffs/02-A3.md:16-23,262-270`). **Fix:** require raw stdout/stderr, command, commit, and exit code in `artifacts` for every measured number.

## What a human still has to do

1. Reject the current C1 “no survivor” decision and decide whether its bounded-retention, stream-before-completion behavior is a feasible behavioral contract rather than an ungradeable cost constraint (`cards/C1-multisink-persist.md:13-15`; `A-source/A3-idea-gate.md:88-97`).
2. If C1 remains viable, rerun Gate 4 and Gate 5 against that exact invariant, preserving command output and classifying the buffered implementations as the named wrong path (`cards/C1-multisink-persist.md:9,13,51`).
3. Complete C1's parallel-API and cascade checks, then score only if it survives (`A-source/A3-idea-gate.md:220-245,266-269`).
4. If C1 dies on a valid rerun, choose whether to spend a bounded second A2 round, pursue one of the parked single-turn surfaces, or retire FrostDB; the current playbook has no terminal policy (`handoffs/02-A3.md:395-420`).
5. Only after a real survivor exists, execute B1–B5 with Avocado/human owning contract prose, Codex owning `tests/`, and Claude owning solution/environment/metadata (`00-ROUTER.md:142-152`).
6. Run the server-side C phase and obtain structural, oracle, calibration, trial-review, and full-task-review evidence; none exists in this run (`00-ROUTER.md:81-110`; `DONE:5-7`).

## Verdict

**Neither.** This is not a complete autonomous loop and not yet a functioning supervised build loop: it produced useful A2 research, then made a decision-critical A3 measurement error and terminated before any task existed. Human intervention is required to reopen C1, correct the gate, and choose the repository-exhaustion policy.

# PERFORMANCE REVIEW — Round 2, curator

## Executive verdict

**Neither.** The run is not a complete autonomous loop and did not submit a task. It is not yet a dependable supervised loop either: both completed acts are `FAIL`, several checklist ticks are contradicted by their own artifacts, and `DONE` was written after one unsuccessful A2→A3 pass rather than following A3's route back to A2 (`review/01-A2-review.md:3-16`; `review/02-A3-review.md:3-16`; `DONE:1`; `A-source/A3-idea-gate.md:396-398`).

| Handoff | Verdict | One-line reason |
|---|---|---|
| `handoffs/01-A2.md` | **FAIL** | Claude authored/re-cut the candidate cards despite A2's owner rule, and the claimed two-card exit includes one explicitly incomplete fallback (`handoffs/01-A2.md:24,32-34,62-63`; `A-source/A2-idea-generate.md:5-8`). |
| `handoffs/02-A3.md` | **FAIL** | It declared measurement-based kills while waiving mandatory Gate 4, using invalid/incomplete Gate-5 probes, and ticking gates without the required evidence (`handoffs/02-A3.md:26-33,81-83`; `A-source/A3-idea-gate.md:179-199,241-267`). |

## Did the loop close?

**No.** It produced 24 surveyed surfaces, one complete card plus one partial fallback, and a no-survivor A3 result; it produced no task directory, push, validation result, or submission (`artifacts/cards.md:8-26,309-312`; `handoffs/02-A3.md:3-18`; `DONE:1`). B-build and C-drive were never entered.

It would have needed a human at four points:

1. A2 lacked its required A1 handoff and self-waived the input instead of stopping (`handoffs/01-A2.md:23`; `A-source/A2-idea-generate.md:6,272`).
2. Claude crossed A2's authorship boundary while marking that checklist line complete (`handoffs/01-A2.md:24`; `artifacts/cards.md:3-6`; `A-source/A2-idea-generate.md:5`).
3. A3 needed a reviewer to reject the Gate-4 waiver and the unsupported Gate-0/Gate-2/Gate-5 ticks (`review/02-A3-review.md:7-16`).
4. After “no survivor,” the executor stopped. A3 says to return to A2, while the router's filename-based state test would instead misroute any A3 handoff to B1 (`A-source/A3-idea-gate.md:396-398`; `00-ROUTER.md:20-26,49`; `DONE:1`).

## Round-2 ideation and director's call

The engineer **did explore the untried space at survey level**. The ask explicitly targeted injected mid-operation failures and partial rollback (`artifacts/survey-ask.txt:13-27,72-81`), and the surveys returned genuine examples such as crash-between-delete-and-requeue atomicity and ambiguous writes after connection loss (`artifacts/survey-metacode.md:250-260,270-297`). C1 also contains a real conflicting-requirement pair: preserve down-state across metadata refresh while keeping same-id/different-endpoint instances independent (`artifacts/cards.md:152-163`). This is materially different from another `expose_interface` pass.

But the promoted C1 card is mislabeled as a failure-injection contract. Its actual graded idea is identity semantics across republication, not “failure mid-operation ⇒ rollback”; the card's own contract and reproduction establish that distinction (`artifacts/cards.md:69-71,112-135,146-183`). The true failure-atomic surfaces were discarded in the merge table for disclosure, recall, scope, or reference-importability (`artifacts/cards.md:37-53`). That is legitimate exploration, but it does **not** prove Curator is dead.

My substantive call is still: **do not build C1 or C2 as written.** C1 is highly likely to be deterministic/easy and is not a real P6 cascade: all five constraint-stated outputs chose the endpoint key, and the handoff admits a parallel API can leave step 1 intact (`artifacts/probe-results.md:26-49`; `handoffs/02-A3.md:34`). C2 was never a complete card or executed premise, and direct source inspection in the prior review indicates its claimed stale-state scenario is hollow (`artifacts/cards.md:309-346`; `review/02-A3-review.md:24-26`). The correct conclusion is “these two are not buildable,” not “the repo has been conclusively exhausted.”

## Checklist and evidence quality

The saved C1 reproduction is genuine: it reports four passing checks and shows metadata/re-registration readmitting a down-marked instance (`artifacts/gate2-repro-output.txt:1-14`). The raw C1 outputs also genuinely converge on endpoint identity, although the prompt defects mean they are not a valid Gate-5 instrument (`artifacts/probes/probeA1-1.out:9-13`; `artifacts/probes/probeA1-3.out:9-12`; `artifacts/probes/probeA1-5.out:9-12`; `review/01-A2-review.md:19-23`). The issue dump's measured 121 rows is independently recorded in the prior review (`review/01-A2-review.md:21`).

The decisive evidence defects are:

- A2's `12 of 13` is false as a completion claim: checklist #2 violates the owner declaration, #10/#11 count an incomplete C2, and the mandatory “one file per card” handoff shape was not followed (`handoffs/01-A2.md:6,24,32-35,62-63`; `A-source/A2-idea-generate.md:281-291`).
- A3 Gate 4 was waived as “subsumed,” although the act says it is mandatory and explicitly different from Gate 5 (`handoffs/02-A3.md:31`; `A-source/A3-idea-gate.md:169-199`). No implementation outcome `n/5` exists.
- A3 checklist #8 claims two phrasings, but C2 has only one (`handoffs/02-A3.md:32`; `artifacts/probe-results.md:119-124`). C1's second prompt withholds the conflicting requirement instead of restating it differently (`artifacts/probes/probe-A2.txt:3-22`).
- The probe declarations were added after all probes ran, by the artifact's own admission (`artifacts/cards.md:137-150`), violating the pre-probe requirement (`A-source/A3-idea-gate.md:241-255`; `tools/probe-lint.py:58-69`). A fresh lint also rejects C1's prompts under the current card: the stated prompt covers only 47% of the declared constraint and leaks desired-design words; the other covers 28%. The enforcement thresholds are explicit in `tools/probe-lint.py:71-108`.
- A3 marked Gate 0 passed for both cards although C1 lacks the required written-out assertion and C2 lacks an Interface Contract; it marked Gate 2 complete while admitting C2 was never executed (`handoffs/02-A3.md:26,29`; `A-source/A3-idea-gate.md:34-39,104-114`; `artifacts/cards.md:188-203,309-312`).

### Boundary and provenance

No `instruction.md` exists, so no protected path was directly written (`handoffs/02-A3.md:84-85`). However, the semantic boundary did leak: Claude authored polished `CONSTRAINT`, `DESIRED`, `NON-DESIRED`, and requirement sentences in the card (`artifacts/cards.md:3-6,137-157`), and the executor admits those are “exactly the sentences a contract would use” and “one paste away” (`friction.md:212-230`). The router forbids suggesting exact prose indirectly (`00-ROUTER.md:164-174`), while B2 explicitly passes the card into the contract-authoring prompt (`B-build/B2-contract.md:45-56`). The disclaimer “not to be pasted” does not remove that provenance risk. No task exists to retire, but the current card prose must not seed a future instruction.

## Autonomy score by phase

| Phase | Score | Evidence |
|---|---:|---|
| **A-source** | **2/5** | Strong survey breadth, real fault-oriented exploration, a real base reproduction, and useful raw probes; offset by wrong ownership, an invalid exit count, post-hoc probe declarations, mandatory Gate-4 omission, and false checklist ticks (`artifacts/survey-ask.txt:13-27`; `artifacts/gate2-repro-output.txt:1-14`; `review/01-A2-review.md:3-27`; `review/02-A3-review.md:3-32`). |
| **B-build** | **0/5 — not entered** | No survivor or task directory exists; B1 requires an A3 survivor (`00-ROUTER.md:49`; `handoffs/02-A3.md:3-7`). |
| **C-drive** | **0/5 — not entered** | Nothing was pushed and no server verdict exists (`00-ROUTER.md:53-64`; `DONE:1`). |

## Would the output be accepted?

**No output exists to accept.** Structural checks, oracle validation, calibration, agentic review, and submission were never reached (`handoffs/02-A3.md:3-18`; `00-ROUTER.md:49-64`). If C1 were built unchanged, calibration is the likely first substantive failure: the raw approach outputs are unanimous, while the mandatory outcome-variance run is absent and the Gate-5 instrument is invalid (`artifacts/probe-results.md:26-49`; `handoffs/02-A3.md:81-83`; `artifacts/cards.md:137-150`). C2 should fail before build because its card and premise evidence are incomplete (`artifacts/cards.md:309-346`; `handoffs/02-A3.md:29`).

## Playbook defects, ranked

### Blocking

1. **No-survivor routing is broken.** The router treats the existence of any A3 handoff as “a survivor card” and routes to B1, while A3 permits no survivor and routes back to A2 (`00-ROUTER.md:20-26,49`; `A-source/A3-idea-gate.md:385-398`). **Fix:** route on a machine-readable A3 outcome, not filename existence.
2. **A2's ownership contract contradicts its execution path.** The header says Claude never generates ideas or surfaces, but the body/checklist allows a non-Avocado runner to continue with “contracts only”; those cards are then supplied to B2 (`A-source/A2-idea-generate.md:5,14-19,273`; `B-build/B2-contract.md:45-56`). **Fix:** make non-MetaCode candidate generation a hard stop; keep any Codex exception narrowly survey-only and prohibit contract-ready prose.
3. **A2 does not produce A3's required probe schema.** A2's mandatory card fields omit literal `CONSTRAINT:`, `DESIRED:`, and `NON-DESIRED:`, while A3 and its linter require them before probing (`A-source/A2-idea-generate.md:124-140,281-282`; `A-source/A3-idea-gate.md:241-255`; `tools/probe-lint.py:19-25`). **Fix:** add the three fields to A2's card schema and checklist, one card per file.
4. **The S1 route and A2 input contract disagree.** The router permits “repo picked, no cards” to enter A2, but A2 requires an A1 handoff and forbids remeasurement (`00-ROUTER.md:20-28,47`; `A-source/A2-idea-generate.md:6,272`). **Fix:** define an accepted imported-shortlist record carrying all A1 facts, or route through A1.

### Degrading

5. **A2's boundaries are muddy.** It says not to run gates but requires auto-rejects in the same act (`A-source/A2-idea-generate.md:10-12,279-280`). **Fix:** name those A2-local filters and reserve A3 gate claims for A3.
6. **A3's cost ordering underprices compiled-language reproduction.** Gate 2 is called “one file read,” but the same gate mandates execution at base; this run spent about 12 minutes compiling before a roughly seven-minute Gate-5 probe killed the card (`A-source/A3-idea-gate.md:14-26,104-114`; `friction.md:160-184`). **Fix:** make order language-sensitive and allow a valid cheap kill before a build-backed reproduction.
7. **A1's issue-density check does not distinguish diagnosis-rich imported trackers.** It treats fewer than about 150 real issues as normal screening, while Curator's 121 imported tickets exposed full diagnoses and patches (`A-source/A1-repo-screen.md:103-125`; `friction.md:53-76`). **Fix:** sample issue bodies/comments and tracker provenance before using the count.
8. **A2's card-count target conflicts with its own expected funnel.** It targets at least eight cards but says a 15–60k LOC repo should yield 10–12 surfaces and that 15–20 surfaces normally collapse to 2–4 cards (`A-source/A2-idea-generate.md:7,51-60,283`). **Fix:** make the checklist compare against the LOC-derived range, not a global eight-card target.
9. **The conformance checker validates syntax, not cross-act semantics.** It checks headers, handoff fields, links, ownership wording, status markers, and router mentions, but cannot catch the four blocking incompatibilities above (`check-playbook.py:41-158`). **Fix:** add semantic checks for producer/consumer schemas, no-survivor routing, and owner-to-output consistency.

The checker currently reports zero failures despite these defects; that is consistent with its implemented scope, not evidence that the contracts compose.

## What a human still has to do

1. Quarantine the Claude-authored contract-ready card prose; do not feed it into B2. Re-run candidate authoring under MetaCode/Vidit ownership (`00-ROUTER.md:164-174`; `artifacts/cards.md:137-157`).
2. Supply a valid A1 handoff or an explicitly supported imported-shortlist record (`A-source/A2-idea-generate.md:6,272`).
3. Continue A2 rather than treating the first no-survivor pass as terminal (`A-source/A3-idea-gate.md:396-398`; `DONE:1`).
4. For each real card, persist it separately with predeclared probe fields, run `probe-lint.py`, then run Gate 0's exact assertion/token proof, Gate 2's executed premise check, Gate 3's full disclosure sweep, mandatory Gate 4 implementations, and two valid Gate-5 phrasings (`A-source/A3-idea-gate.md:34-39,104-199,241-267,363-382`).
5. Once a valid survivor exists, execute B1–B5, push it, and drive every server result through C1–C6 until all five done criteria are green (`00-ROUTER.md:49-64,126-156`).
6. Repair the blocking playbook contradictions above before calling a future run autonomous.

## Final verdict

**Neither — useful supervised research, but not a trustworthy task-authoring loop and not a submission.**

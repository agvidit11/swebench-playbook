# Review 02 — A3 IDEA GATE

## Verdict: FAIL

The no-survivor exit is not established. C1 and C2 have strong evidence of model convergence, but C3's five probes did not test its constraint-stating step. The handoff nevertheless reports `5/5 desired path` for C3 and counts the fork-probe checklist line as complete (`handoffs/02-A3.md:7-15`, `handoffs/02-A3.md:175-185`). Under the review rule for unsupported ticks, that is a failure.

## Checklist audit

The reported `CHECKLIST: 11 of 14 ticked` is materially overstated (`handoffs/02-A3.md:175-185`). The three stated waivers are not the only incomplete lines.

| A3 line | Audit | Evidence |
|---|---|---|
| 1 — read A2 | PASS | The handoff lists all three cards and uses their premises (`handoffs/02-A3.md:9-13`, `handoffs/02-A3.md:19-21`). |
| 2 — Gate 0 namability | **FAIL** | The required proof is an exact graded assertion, complete token inventory, and an IN-BASE/COINED grep per token (`A-source/A3-idea-gate.md:34-39`, `A-source/A3-idea-gate.md:257-259`). The handoff gives only C1's coined-token count and no assertion/token grep, and gives no Gate-0 evidence for C2 or C3 (`handoffs/02-A3.md:52-68`, `handoffs/02-A3.md:88-117`). C1 also had no required override file, so under the written rule it died at Gate 0, not Gate 5 (`A-source/A3-idea-gate.md:50-61`; `handoffs/02-A3.md:52-56`). |
| 3–4 — Gate 1 | PARTIAL | The cards contain argued families and behavioural/cost labels (`artifacts/cards.md:193-216`, `artifacts/cards.md:373-390`, `artifacts/cards.md:540-555`), but A3 is a verification act and the handoff does not show independent rechecking of all three free filters per card. |
| 5 — Gate 2 | **FAIL** | C1 has a genuine executable reproduction (`artifacts/repro-results.md:18-35`, `artifacts/repro-results.md:37-76`). C2 has a static code observation only, and C3 has no executed base-commit reproduction (`handoffs/02-A3.md:97-117`). The checklist requires both code-path reading and executed reproduction for each candidate (`A-source/A3-idea-gate.md:261`). |
| 6 — Gate 3 | **FAIL** | The handoff does not preserve the required 4–6 queries with `total_count`, comment reads, roadmap sweep, and candidate-symbol peer sweep for each card (`A-source/A3-idea-gate.md:262`). It gives prose summaries and selected issue IDs only (`handoffs/02-A3.md:23-32`, `handoffs/02-A3.md:90-103`). |
| 7 — Gate 4 outcome variance | **FAIL / invalid waiver** | The handoff admits no five-implementation, assertion-graded outcome probe was run (`handoffs/02-A3.md:175-181`). Gate 4 defines that measurement explicitly (`A-source/A3-idea-gate.md:159-172`) and the checklist says gates are run in order (`A-source/A3-idea-gate.md:251-264`). “Expensive after Gate 5” does not make the earlier gate unreachable. |
| 8 — Gate 5 fork probe | **FAIL** | C2's five outputs do converge on the required retry/stop policy (`artifacts/probes/D-1.out:14`, `artifacts/probes/D-2.out:12`, `artifacts/probes/D-3.out:13`, `artifacts/probes/D-4.out:14`, `artifacts/probes/D-5.out:13`). C3 does not. Its card's Step 2 requires stopping before later resolvers run (`artifacts/cards.md:421-427`), but the prompt asks only for observable decline-vs-failure attribution (`artifacts/probeC3.txt:7-12`). The outputs do not commit to fail-fast: C-2 says to keep resolution semantics unchanged, C-4 says to keep chain behavior unchanged, and C-5 leaves “short-circuit or aggregate” unresolved (`artifacts/probes/C-2.out:11`, `artifacts/probes/C-4.out:12`, `artifacts/probes/C-5.out:12`). This measures Step 1 novelty, not the constraint-stating Step 2 required by Gate 5 (`A-source/A3-idea-gate.md:200-202`, `A-source/A3-idea-gate.md:264`). |
| 9 — Gate 6 | **FAIL** | No one-line verdict exists for each Tier-0 filter per card, as the checklist requires (`A-source/A3-idea-gate.md:265`). The A2 card self-audits are neither complete nor independent A3 evidence (`artifacts/cards.md:165-191`, `artifacts/cards.md:341-371`, `artifacts/cards.md:508-538`). |
| 10 — Gate 7 | **FAIL** | The handoff supplies no executed HEAD counterfactual or parallel-API result; it inherits assertions from the cards. C2's own probe prompt and answers actually describe Step 2 using the document's existing `EncryptedKey` elements without Step 1's extension-preservation artifact (`artifacts/probeC2.txt:6-12`, `artifacts/probes/D-3.out:13`), contradicting the card's “cannot compute without Step 1” claim (`artifacts/cards.md:262-266`). |
| 11–12 — Gate 8 scoring | WAIVED, conditionally valid | A3 says scoring is for survivors only (`A-source/A3-idea-gate.md:230-245`). The waiver would be valid only after every card had a valid prior-gate kill; C3 does not. |
| 13–14 — result and handoff | Handoff exists; result FAILS | The block exists (`handoffs/02-A3.md:161-222`), but “no survivor” is unsupported because C3 remains unmeasured on its actual Step 2. |

## Evidence quality

The reproduction evidence is unusually good. It records exact test output for flat versus nested limits, nested suppression, and early abort (`artifacts/repro-results.md:18-35`, `artifacts/repro-results.md:37-76`), and the throwaway clone is pinned to the stated SHA (`handoffs/02-A3.md:195-208`). The 20 probe files also exist and contain real MetaCode responses.

The aggregate `20/20 desired path` is not a measurement supported by those files. For C3, zero of five responses explicitly chooses the mandatory fail-fast policy; one explicitly preserves current semantics and another refuses to choose (`artifacts/probes/C-2.out:11`, `artifacts/probes/C-5.out:12`). No outcome-variance number exists at all, which the handoff acknowledges (`handoffs/02-A3.md:175-181`). The JIRA total of 33 and the status/content of SANTUARIO-635 and SANTUARIO-618 were independently rechecked; the claimed zero-result JIRA searches and branch-by-branch novelty conclusion remain taken on trust because their raw output was not retained (`handoffs/02-A3.md:23-32`, `handoffs/02-A3.md:200-204`).

## Boundary check

The protected-file boundary held. No task directory was created, no instruction file exists, and the only source-tree write is a Codex-authored probe under the throwaway clone's upstream test tree (`CHECKPOINT.md:264-273`). That file is not a benchmark `tests/` artifact and was within A3's probe role (`handoffs/02-A3.md:191-194`). No solver-facing instruction text was written.

The act also stayed short of B1: no benchmark scaffold, solution, grader, environment, or manifest was produced (`CHECKPOINT.md:213-216`). That is correct once a valid no-survivor result exists, but the result here was not validly established for C3.

## Director's call

- C1: do not build. Its high-level no-abort/reporting path is strongly model-preferred, and without an override it already fails written Gate 0 (`handoffs/02-A3.md:52-86`).
- C2: do not build. Five of five probes implement the retry classification, and the supposed cascade is contradicted by those same answers because they need only existing document-carried keys (`artifacts/probes/D-1.out:14`, `artifacts/probes/D-3.out:13`).
- C3: do not green-light yet, but do not call it dead on the present evidence. Its fail-fast Step 2 was never probed. It is independently weak because its card admits an R06 gap and makes difficulty depend on classifying more than 100 null-return sites (`artifacts/cards.md:402-420`, `artifacts/cards.md:520-555`). The correct disposition is “unmeasured; re-probe or kill on another evidenced gate.”

Santuario remains a poor multi-turn bet: its standard-defined behaviors are recallable, while its remaining local-policy space clusters around explicit reporting APIs (`handoffs/02-A3.md:121-143`). That conclusion is plausible, but three cards with one invalid probe do not prove the intersection empty.

## Executor defects vs playbook defects

Executor defects:

- Reported C3 as `5/5 desired` from a prompt that omitted its Step-2 fail-fast constraint (`handoffs/02-A3.md:88-95`; `artifacts/probeC3.txt:7-12`).
- Claimed 11 checklist items while Gate 0, Gate 2, Gate 3, Gate 6, and Gate 7 lacked their required evidence, and Gate 4 was not run (`handoffs/02-A3.md:175-185`).
- Marked the run DONE after a no-survivor A3 result even though A3's required NEXT is back to A2 (`A-source/A3-idea-gate.md:284-286`; `DONE:1`; `CHECKPOINT.md:213-216`).

Playbook defects:

- Gate 4 requires five implementations “from the task's own contract” graded against assertions before B2 has written the contract and B3 has written the grader (`A-source/A3-idea-gate.md:159-166`; `00-ROUTER.md:24-27`). Fix: move this gate after B3/B4, or define an authorized, executable pre-task contract/grader artifact.
- Gate 0 requires `<task>/audit/gate0-override.md` before B1, although B1 is the act that creates `<task>/` (`A-source/A3-idea-gate.md:50-61`; `B-build/B1-scaffold.md:4-8`). Fix: store the override in the run directory and have B1 copy/reference it after scaffold creation.
- A3 says probes run at stage 0, but its ordered table and checklist put them after Gates 0–3 (`A-source/A3-idea-gate.md:12-26`, `A-source/A3-idea-gate.md:251-264`). Fix: choose one order and make prose, table, and checklist identical.
- Gate 3 supplies only GitHub commands, so it can return a false-clean on a JIRA-only repo (`A-source/A3-idea-gate.md:116-139`; `/home/agvidit/swebench/runs/shortlist-proto.md:65`). Fix: require discovery and query of the repository's authoritative tracker before calling disclosure clean.
- A3's no-survivor route has no retry budget or repo-exhaustion terminal; it always points back to A2 (`A-source/A3-idea-gate.md:284-286`). Fix: define a bounded A2/A3 retry count and an evidenced repo-abandon exit.

# Review 01 — A2 IDEA GENERATE

## Verdict: FAIL

The act did real, useful survey work, but it did not meet A2's own exit condition. A2 requires every card to be axis-composed and to carry the complete self-audit (`A-source/A2-idea-generate.md:7-8`, `A-source/A2-idea-generate.md:244-251`). The three delivered cards do not name a P1–P6 A-shape, omit required audit rows, and retain explicit self-audit failures even though A2 says such a card must be repaired or discarded.

## Checklist audit

The reported `CHECKLIST: 12 of 13 ticked` is not supported (`handoffs/01-A2.md:168-174`). At most 10 lines are complete, one is validly waived, and lines 10–11 fail.

| A2 line | Audit | Evidence |
|---|---|---|
| 1 — read A1 handoff | WAIVED, reasonable for this assignment | The run was explicitly started at A2; the executor records that the shortlist substituted for the absent handoff and re-derived the SHA and clone (`handoffs/01-A2.md:168-172`). |
| 2 — authorship lane | PASS for protected prose | The runner identifies itself as Claude and says no solver prose was created (`handoffs/01-A2.md:9-16`); MetaCode's run log says it wrote `cards.md` (`/tmp/santuario-pair/notes/cards.out:13-16`). |
| 4 — derive surface count | PASS | 73,128 LOC maps to the 15–20 band and the ask was 18 (`handoffs/01-A2.md:37-41`), matching the playbook (`A-source/A2-idea-generate.md:51-60`). |
| 6–7 — survey prompt and run | PASS WITH EVIDENCE DEFECT | The prompt contains the lens, control, citation requirement, diversity requirement, admissions, and containment (`artifacts/survey.txt:32-68`, `artifacts/survey.txt:92-145`, `artifacts/survey.txt:189-204`). The final survey reports 16 surfaces (`artifacts/survey.out:189-195`, `artifacts/survey.out:420-441`). However, the same stdout also contains an abandoned 18-surface draft (`artifacts/survey.out:13-18`), so byte count alone was not a meaningful integrity check. |
| 8–9 — merge and auto-rejects | PASS | All 16 final surfaces are mapped (`artifacts/cards.md:559-578`) and 14 rejected merges name their reason (`artifacts/cards.md:582-628`). |
| 10 — complete card per survivor | **FAIL** | A2 requires an Observable Schema whenever the deliverable is records (`A-source/A2-idea-generate.md:132-140`). C1's deliverable is a position-aligned ledger (`artifacts/cards.md:68-70`) and C3's is an ordered per-resolver ledger (`artifacts/cards.md:411-427`), but neither card has the required schema field: each jumps from Interface Contract directly to Named Wrong Shape (`artifacts/cards.md:104-128`, `artifacts/cards.md:458-477`). The handoff also requires one numbered file per card (`A-source/A2-idea-generate.md:286-295`), but all three were placed in one `artifacts/cards.md` file. |
| 11 — self-audit | **FAIL** | The required audit has 13 card-stage items plus four explicitly deferred items (`A-source/A2-idea-generate.md:244-251`, `A-source/A2-idea-generate.md:281-282`). Each delivered table omits R03 and all deferred R10/R12/R13 rows and collapses N01–N04 into one row (`artifacts/cards.md:165-191`, `artifacts/cards.md:341-371`, `artifacts/cards.md:508-538`). Worse, C1 retains `R08 FAIL`, C2 retains `R02 FAIL`, and C3 retains `R06 FAIL` (`artifacts/cards.md:182-186`, `artifacts/cards.md:347-351`, `artifacts/cards.md:520-524`), despite the act's rule that a self-reported FAIL is repaired or discarded (`A-source/A2-idea-generate.md:249-251`). |
| 12 — honest count | PASS | It reports 3 cards against the ≥8 target and does not pad (`handoffs/01-A2.md:147-156`), as A2 permits (`A-source/A2-idea-generate.md:59-60`). |
| 13 — handoff | PASS | The required block is present (`handoffs/01-A2.md:143-221`). |

There is also an exit-level composition miss. A2 defines composition as a C-axis plus a P1–P6 A-shape (`A-source/A2-idea-generate.md:27-31`). C1 instead names “same-loop / two-seam split” and explicitly says it is not revert-and-redo (`artifacts/cards.md:29-46`); C2 names “capture-then-constrain” (`artifacts/cards.md:222-236`); C3 names “channel-then-policy” (`artifacts/cards.md:396-409`). These may be useful merge descriptions, but they are not the declared A-shape field.

## Evidence quality

The main counts are real: the final response contains 16 surfaces (`artifacts/survey.out:193-195`), the merge table maps 16 (`artifacts/cards.md:559-578`), and the kill log has 14 entries (`artifacts/cards.md:582-628`). The cold build claim is supported by `EXIT=0 SECONDS=43` in the retained runtime log, while the 0.443-second class timing is also quoted in the handoff (`handoffs/01-A2.md:124-126`).

Several other claims are attestations rather than preserved command output: the zero-hit JIRA searches, remote-branch reading, 151,277-file peer sweep, and full-suite 6m35 timing appear only as summaries (`handoffs/01-A2.md:125-139`). The JIRA count and the existence/status/content of SANTUARIO-635 and SANTUARIO-618 were independently rechecked; the zero-hit search set and branch-by-branch conclusion were not.

## Boundary check

The iron-clad boundary held: no task directory or instruction file exists, and the run explicitly records that no contract prose was written (`handoffs/01-A2.md:218-219`; `CHECKPOINT.md:264-273`). MetaCode wrote the card deliverable (`/tmp/santuario-pair/notes/cards.out:13-16`).

The broader act ownership is ambiguous and should not be treated as clean evidence. A2 says Claude never generates ideas or surfaces (`A-source/A2-idea-generate.md:5`), while this Claude runner selected the lenses (`handoffs/01-A2.md:18-35`) and authored a highly candidate-specific survey prompt (`artifacts/survey.txt:32-68`). A2's checklist nevertheless tells an unspecified runner to choose the lens (`A-source/A2-idea-generate.md:272-275`). That ambiguity is a playbook defect; there is no protected-file leak here.

## Director's call

I would not green-light any delivered card. C1 and C2 later showed model convergence, while C3 entered A3 with an acknowledged unclosed R06 gap and difficulty tied to triaging more than 100 `null` sites (`artifacts/cards.md:520-538`, `artifacts/cards.md:540-555`). The repo itself was a defensible screen: the shortlist had a fast deterministic harness and broad subsystems (`/home/agvidit/swebench/runs/shortlist-proto.md:56-73`). The engineer correctly treated its suggested surfaces as hypotheses: canonicalization was killed as recallable and secure-validation customization was killed by SANTUARIO-635 (`handoffs/01-A2.md:157-167`). The gates, however, did not prevent three structurally non-conforming cards from being handed forward.

## Executor defects vs playbook defects

Executor defects:

- Marked checklist lines 10–11 complete without the required card fields and audit evidence (`handoffs/01-A2.md:168-174`; `artifacts/cards.md:165-191`).
- Kept cards carrying explicit FAIL rows, contrary to A2's discard-or-repair rule (`A-source/A2-idea-generate.md:249-251`).
- Replaced the required P1–P6 A-shape with ad-hoc merge-shape labels (`A-source/A2-idea-generate.md:27-31`; `artifacts/cards.md:35-46`).

Playbook defects:

- The owner declaration forbids Claude ideation, but checklist line 3 tells the generic runner to choose the lens without assigning that substep to MetaCode/Codex (`A-source/A2-idea-generate.md:5`, `A-source/A2-idea-generate.md:272-275`). Fix: assign checklist lines 3–11 explicitly by owner.
- The header advertises a ≥8 card target while the sizing section says 15–20 surfaces normally collapse to 2–4 cards and that exit is quality, not count (`A-source/A2-idea-generate.md:7-8`, `A-source/A2-idea-generate.md:59-60`). Fix: remove the numeric target from the header or make it a non-gating planning estimate.
- The self-audit permits only PASS/FAIL/N-A, requires a named non-PASS or residual risk, and separately requires every FAIL card to be repaired or discarded (`A-source/A2-idea-generate.md:244-259`). Fix: add an `AT-RISK` status and reserve `FAIL` for rejection.

# Review 01 — A2 idea generation

## Verdict: PASS WITH DEFECTS

A2 met its stated exit: it produced two axis-composed cards with the required fields and self-audits (`A-source/A2-idea-generate.md:5-8`; `cards/C1-multisink-persist.md:9-72`; `cards/C2-computed-operand-ordering.md:10-70`). Falling below the dispatch target is permitted when the count is derived and not backfilled (`A-source/A2-idea-generate.md:47-60`). The count derivation and checklist accounting are defective, but neither leaves the A2 exit wholly unevidenced.

## Checklist audit

| Item spot-checked | Result | Evidence |
|---|---|---|
| 1 — read A1 handoff | Waiver justified | The assignment starts at A2 and the shortlist supplies FrostDB's licence, LOC, subsystems, issue count, provenance, dedup, and timings (`/home/agvidit/swebench/runs/shortlist-data.md:106-143`). The required A1 handoff did not exist, as disclosed (`handoffs/01-A2.md:204-209`). |
| 4 — derive the surface count | Defective | The report calls 14–16 “the overlap” of 10–12 and 16–24 (`handoffs/01-A2.md:24-36`; `notes/A2-survey-brief.txt:32-35`), but those ranges do not overlap. A2 says to trust subsystem count when the two disagree (`A-source/A2-idea-generate.md:51-58`). The actual two surveys returned 15 and 16 surfaces, so the survey was not starved (`handoffs/01-A2.md:33-36`). |
| 5 — admissions sweep | Pass | The handoff records ten admissions with live/stale dispositions (`handoffs/01-A2.md:77-92`). The consequential claims are borne out at base: multi-sink refusal is at `/tmp/frostdb-run/frostdb/store.go:35-38`, computed-aggregate uncertainty at `/tmp/frostdb-run/frostdb/query/physicalplan/aggregate.go:33-36`, and sampler sorting at `/tmp/frostdb-run/frostdb/query/physicalplan/sampler.go:244-254`. |
| 6–7 — survey brief and runs | Pass | The brief contains containment, a 14–16 target, composed axes, shape diversity, admissions, and the HEAD-citation requirement (`notes/A2-survey-brief.txt:6-84`). Saved outputs are 49,601 and 43,155 bytes, matching the handoff's figures (`handoffs/01-A2.md:213-215`). |
| 8–9 — merge and rejection accounting | Pass with defect | The MetaCode survey maps all 15 surfaces (`notes/A2-survey-metacode.md:468-486`), the Codex survey has its own surface mapping (`notes/A2-survey-codex.md:259-280`), and the final rejection list accounts for both survey candidate sets (`cards/00-rejected-and-ranking.md:3-14`). “10 merged candidates” counts two labels for the same multi-sink candidate (`cards/00-rejected-and-ranking.md:8,12`), so it is ten survey outputs but nine distinct candidates. |
| 10–11 — cards and self-audits | Pass with defect | Both card bodies are preserved in the MetaCode card-pass output (`notes/A2-cards-metacode.md:21-157`) and contain all mandatory fields. However, C1 records `N03 FAIL` (`cards/C1-multisink-persist.md:70`) and C2 records `R09 FAIL` (`cards/C2-computed-operand-ordering.md:64`) while A2 says a self-reported FAIL must be repaired or discarded (`A-source/A2-idea-generate.md:244-251`). The playbook simultaneously requires a non-PASS row *or* residual risk (`A-source/A2-idea-generate.md:258-263`), making the intended status vocabulary unclear. |
| 12 — honest count | Pass | The handoff reports two cards rather than padding to eight and supplies the survey funnel (`handoffs/01-A2.md:24-36,219-220`). |
| 13 — handoff | Pass | All required HANDOFF fields are present (`handoffs/01-A2.md:3-21,116-240`). |

No ticked A2 item is wholly unsupported. The count formula is wrong and the self-audit statuses conflict with the act's prose, hence `PASS WITH DEFECTS` rather than `PASS`.

## Evidence quality

The strongest evidence is repository-grounded: the cards quote current source and identify existing entry points (`cards/C1-multisink-persist.md:17-35`; `cards/C2-computed-operand-ordering.md:18-35`). The predicted arm rates are clearly labelled predictions, not measurements (`cards/C1-multisink-persist.md:45-47`; `cards/C2-computed-operand-ordering.md:43-45`). The survey byte counts and the 15/16 surface counts are backed by saved outputs (`handoffs/01-A2.md:33-36,214-215`).

The weak points are the impossible “overlap” arithmetic (`handoffs/01-A2.md:26-32`) and treating two independently named versions of C1 as two merged candidates (`cards/00-rejected-and-ranking.md:8,12`). Neither changes the two-card output, but both make the numerical narrative less reliable.

## Boundary check

Clean. No instruction file exists in the run. The two card bodies appear verbatim in the saved MetaCode output (`notes/A2-cards-metacode.md:21-157`), and the cards identify MetaCode as author (`cards/C1-multisink-persist.md:3-5`; `cards/C2-computed-operand-ordering.md:3-4`). Codex stayed on the explicitly permitted wide-survey lane, while Claude reported validation/collation (`A-source/A2-idea-generate.md:5,14-19`; `handoffs/01-A2.md:38-48`).

## Director's call

FrostDB was worth this A2 pass. The shortlist's strongest facts—clean provenance/dedup, fast targeted tests, and several existing public seams—are concrete, while its own fit warning is explicit (`/home/agvidit/swebench/runs/shortlist-data.md:106-143`). A2 did not blindly accept the suggested surfaces: it killed `avg`, hash-path multi-aggregation, and sampler sorting after reading the actual code (`handoffs/01-A2.md:94-114`).

C1 deserved an A3 probe: the refusal contradicts the public multi-sink model and uses existing APIs (`cards/C1-multisink-persist.md:17-35`). C2 also deserved cheap gating, but its public-fixture and dormant-planner risks were already substantial (`cards/C2-computed-operand-ordering.md:18-25`). I would green-light the repo and C1 for verification, not either card for construction at A2.

## Defect ownership

### Executor defects

- The surface-count derivation says two disjoint ranges overlap and does not follow A2's “trust subsystem count” instruction (`handoffs/01-A2.md:24-36`; `A-source/A2-idea-generate.md:51-58`).
- The checklist says “13 of 13 ticked, 1 partially waived,” an internally inconsistent count (`handoffs/01-A2.md:8-9,204-220`).
- Both cards advance with rubric rows literally marked `FAIL`, contrary to A2's “repaired or discarded” sentence (`cards/C1-multisink-persist.md:70`; `cards/C2-computed-operand-ordering.md:64`; `A-source/A2-idea-generate.md:244-251`).

### Playbook defects

- A2 requires an A1 HANDOFF even though the router can place an externally shortlisted repo directly in S1; there is no normalization step for shortlist evidence (`00-ROUTER.md:21-24`; `A-source/A2-idea-generate.md:6,272`). Fix: define a shortlist-to-A1 receipt with the exact required fields.
- “Major subsystem” is undefined, so the LOC and subsystem formulas can diverge without a deterministic tie-break (`A-source/A2-idea-generate.md:51-60`). Fix: define qualifying subsystem size and use one explicit formula.
- The self-audit simultaneously says any `FAIL` must kill/repair the card and requires a non-PASS row or residual risk (`A-source/A2-idea-generate.md:244-263`). Fix: reserve `FAIL` for a kill and add a distinct `RISK` status.
- The documented dispatch covers the survey but not the owner-sensitive merge/card pass later required by the checklist (`A-source/A2-idea-generate.md:105-122,279-282`). Fix: add a second explicit MetaCode card-authoring dispatch.

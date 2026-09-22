# Review — 02-A3.md

## Verdict: FAIL

The substantive decision—no round-1 survivor—is supported by an independent kill for each card. However, the checklist contains at least two falsely completed items: Gate 3 lacks the mandated persisted query/count/comment evidence, and the Gate 7 “no call edge” proof is factually contradicted by the source and by the card's own planned guard tests. Under the review rule that a tick without evidence is a failure, the act fails even though its final routing back to A2 is correct.

## Checklist audit

- **2 — supported for C02.** The card marks `plan` COINED and admits no spelling-indifferent test (`/tmp/oxigraph-run/cards.out:113-125`); A3 rejects it without an override (`handoffs/02-A3.md:58-72`), matching Gate 0 (`A-source/A3-idea-gate.md:28-61`).
- **5 — supported.** The successful logs show the query-side test passing and print the actual SILENT behavior plus plan/statistics outputs (`/tmp/oxigraph-run/gate2-spareval.log:61-79`). The fixed update probe prints the missing-source graph mutations (`/tmp/oxigraph-run/gate2-update.log:5-25`). These are executions at the pinned SHA, not restated examples.
- **6 — FAIL for evidence completeness.** The checklist requires 4–6 searches with `total_count`, comments for each touched issue, and a roadmap/feature sweep where applicable (`A-source/A3-idea-gate.md:131-139`). The handoff merely says “8 issue searches + 1 PR search + git log,” supplies no queries or `total_count`, explicitly skips the roadmap sweep, and names no disclosure-log artifact (`handoffs/02-A3.md:204`, `handoffs/02-A3.md:242-248`). A merged PR is enough to kill C01, but not enough to tick this checklist line.
- **10 — FAIL.** The handoff claims the two error types are separate with “no call edge” (`handoffs/02-A3.md:164-173`). In the pinned tree, `lib/oxigraph/src/sparql/error.rs:4` imports `spareval::QueryEvaluationError`, and `lib/oxigraph/src/sparql/error.rs:56-81` implements `From<QueryEvaluationError> for UpdateEvaluationError`. More importantly, C01 explicitly placed two query-side SERVICE guards in step 2's graded set and said they fail when step 1 is deleted (`/tmp/oxigraph-run/cards.out:99`, `/tmp/oxigraph-run/cards.out:102`). The asserted HEAD-counterfactual result therefore was not demonstrated and contradicts the proposed grader.
- **7/8/11/12 — correctly waived.** Both cards had cheaper independent kills before the expensive outcome/fork probes and scoring (`handoffs/02-A3.md:205-210`), consistent with the gate-order rule (`A-source/A3-idea-gate.md:12-26`).
- **13 — supported.** C02 has a measured hollow-premise kill and C01 has a verified merged-PR kill, so “no survivor” remains justified even after discarding the bad Gate 7 claim (`handoffs/02-A3.md:216-234`).

## Evidence quality

The cold/warm timings and behavioral outputs are real measurements: the logs show a 48.59-second compile (`/tmp/oxigraph-run/gate2-spareval.log:57-59`), plan/statistics behavior (`/tmp/oxigraph-run/gate2-spareval.log:70-79`), and the update mutations (`/tmp/oxigraph-run/gate2-update.log:12-20`). Commit `4a611b81` exists locally and its diff buffers LOAD input before insertion, matching the quoted public change (`handoffs/02-A3.md:119-145`). By contrast, the disclosure sweep's claimed counts and issue-comment review are not reproducible from any listed artifact (`handoffs/02-A3.md:242-248`).

The statement that the plan subtrees are “byte-identical” is imprecise but directionally supported: the full JSON differs in the planning-duration value while the nested `plan` object printed in P2a/P2b is identical (`handoffs/02-A3.md:38-47`; `/tmp/oxigraph-run/gate2-spareval.log:70-71`).

## Boundary check

No task directory existed and no protected instruction path was written (`CHECKPOINT.md:21-24`). The repro tests were created only in `/tmp/oxigraph-work`, outside a benchmark task (`handoffs/02-A3.md:242-247`), so they do not violate task `tests/` ownership. I found no instruction prose written or suggested for later paste.

## Director's call

The no-survivor decision is right. C02 is mostly existing behavior plus a coined convenience method (`handoffs/02-A3.md:36-52`), and its own projected first-step saturation made it a poor multi-turn bet (`handoffs/02-A3.md:66-72`). C01 exposes a worthwhile real bug (`handoffs/02-A3.md:99-113`), but the same SILENT/atomic-update direction is publicly active in PR #1938 (`handoffs/02-A3.md:116-147`). I would not build either. A fresh A2 pass can test the remaining material, but the repo itself is not green under the literal playbook because the supplied shortlist records `AGENTS.md` (`/home/agvidit/swebench/runs/shortlist-data.md:75`) and A1 makes that a hard G2 kill (`A-source/A1-repo-screen.md:25-30`).

## Defect attribution

### Executor defects

- Ticked Gate 3 without the required query totals, issue-comment evidence, or an artifact preserving them (`handoffs/02-A3.md:204`; `A-source/A3-idea-gate.md:262`).
- Ticked Gate 7 using an incomplete grep of only `update.rs`; the adjacent error module contains the cross-crate conversion, and the intended step-2 guards directly depend on step-1 behavior (`handoffs/02-A3.md:157-178`; `/tmp/oxigraph-run/cards.out:99-102`).
- Called Gate 6 a “partial tick” while skipping most filters, instead of waiving the unrun portions (`handoffs/02-A3.md:207`, `handoffs/02-A3.md:236-240`).

### Playbook defects

- **No upstream-churn field before expensive card elaboration.** A1 checks liveness only at repo level (`A-source/A1-repo-screen.md:127-142`) and A2's mandatory card fields omit target-file churn (`A-source/A2-idea-generate.md:124-140`), while A3 waits until disclosure to inspect file history (`A-source/A3-idea-gate.md:116-141`). Fix: require recent target-file/PR churn on each surface before card elaboration.
- **Gate 7 lacks a mechanical dependency proof.** It asks conceptual counterfactual questions (`A-source/A3-idea-gate.md:220-228`) but does not require tracing imports/conversions or executing the proposed step-2 guards without step 1. Fix: require a symbol/dependency trace plus the actual HEAD-counterfactual grader run when a card claims a cascade.
- **Early-kill checklist semantics are underspecified.** A3 orders cheap kills first (`A-source/A3-idea-gate.md:12-26`) but its checklist says “per candidate, in order” without specifying that all later lines may be waived after a kill (`A-source/A3-idea-gate.md:251-270`). Fix: state the waiver rule explicitly and forbid “partial tick” status.

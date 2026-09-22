# PERFORMANCE REVIEW — pair-santuario

## Executive verdict

**Neither.** This was a useful but supervised sourcing experiment, not a complete autonomous loop. It stopped after A3 with no task directory (`CHECKPOINT.md:213-216`), A2's reported checklist contains unsupported ticks (`review/01-A2-review.md:5-31`), and A3's no-survivor decision rests on a false `5/5 desired path` classification for C3 (`review/02-A3-review.md:5-35`).

## Did the loop close?

No. The executor completed one A2 pass and declared A3 terminal (`DONE:1`), but A3's own handoff contract routes a no-survivor result back to A2 (`A-source/A3-idea-gate.md:284-286`). No benchmark task, contract, grader, oracle, image, manifest, commit, or server verdict was produced (`CHECKPOINT.md:213-216`).

The unattended progress was substantive: it resolved the Maven harness, generated a wide survey, produced cards, ran a real base-commit reproduction, and collected 20 approach probes (`handoffs/01-A2.md:37-90`; `handoffs/02-A3.md:34-50`; `handoffs/02-A3.md:186-199`). It would nevertheless have stalled or made an invalid decision at these points:

1. A2's complete-card gate: required schema and audit rows were absent, while all three cards retained prohibited self-audit FAILs (`artifacts/cards.md:165-191`, `artifacts/cards.md:341-371`, `artifacts/cards.md:508-538`; `A-source/A2-idea-generate.md:244-251`).
2. A3 Gate 0: the one coined-token card had no override, but the executor proceeded (`handoffs/02-A3.md:52-70`; `A-source/A3-idea-gate.md:50-61`).
3. A3 Gate 4: the required full-implementation/outcome probe needs a contract and grader that the router does not create until B2/B3, so the executor waived it (`A-source/A3-idea-gate.md:159-166`; `00-ROUTER.md:24-27`; `handoffs/02-A3.md:175-181`).
4. A3 Gate 5: the C3 prompt omitted the fail-fast Step-2 constraint, so the `5/5 desired` claim cannot be derived from the outputs (`artifacts/probeC3.txt:7-12`; `artifacts/cards.md:421-427`; `artifacts/probes/C-2.out:11`; `artifacts/probes/C-5.out:12`).
5. The run used coordinator-supplied rule corrections during execution, so it was not unattended even on its own account (`friction.md:65-86`, `friction.md:100-132`).

## Autonomy score by phase

| Phase | Score | Evidence |
|---|---:|---|
| A-source | **3/10** | A2/A3 produced useful evidence, including executable source characterization (`artifacts/repro-results.md:18-76`), and correctly killed two shortlist suggestions rather than treating them as prevalidated (`handoffs/01-A2.md:157-167`). But A2 failed its card contract and A3 falsely closed C3, skipped the required outcome probe, and stopped contrary to `NEXT` (`review/01-A2-review.md:5-31`; `review/02-A3-review.md:5-35`; `DONE:1`). |
| B-build | **0/10 demonstrated** | Never entered; no task directory exists (`CHECKPOINT.md:213-216`). Structural checks and oracle behavior are untested. |
| C-drive | **0/10 demonstrated** | Never entered; there is no pushed SHA or server verdict (`CHECKPOINT.md:213-216`). |

## Would the output be accepted?

No task exists to accept. It fails before structural validation because there is no task directory or required artifact set (`CHECKPOINT.md:213-216`; compare the B1 required layout at `B-build/B1-scaffold.md:19-38`). Oracle, calibration, TBD review, and Agentic Full-Task Review are therefore all unmeasured.

If the question is whether the current ideas should advance:

- C1 should not: its reporting approach is strongly model-preferred and it lacked the written Gate-0 override (`handoffs/02-A3.md:52-86`).
- C2 should not: all five probes converge, and the answers demonstrate that its Step 2 can operate on existing document-carried keys without Step 1's claimed artifact (`artifacts/probes/D-1.out:14`, `artifacts/probes/D-3.out:13`; `artifacts/cards.md:262-266`).
- C3 is not accepted or rejected: its actual fail-fast Step 2 was never probed (`artifacts/cards.md:421-427`; `artifacts/probeC3.txt:7-12`). Its self-identified R06 gap and mechanical breadth make it weak, but the recorded Gate-5 kill is invalid (`artifacts/cards.md:520-555`).

The output would thus fail first at task existence/structure, not at oracle or calibration. There is no evidence on which to predict an Agentic Full-Task Review verdict for a built task.

## Playbook defects, ranked

### Blocking

1. **A3 Gate 4 is chronologically impossible as written.** It requires five implementations from the task's own contract and grading against assertions before B2 creates the contract and B3 creates the grader (`A-source/A3-idea-gate.md:159-166`; `00-ROUTER.md:24-27`). One-line fix: move outcome-variance measurement after B3/B4, or formally define an authorized executable pre-task contract and grader.
2. **No bounded no-survivor termination exists in A-source.** A3 always routes no survivor back to A2, with no retry budget or evidenced repo-abandon state (`A-source/A3-idea-gate.md:284-286`; `00-ROUTER.md:21-24`). One-line fix: add an A2/A3 attempt budget and a terminal “repo exhausted” handoff.
3. **The Gate-0 override must be written into a task directory that does not exist yet.** A3 requires `<task>/audit/gate0-override.md` before B1, while B1 creates that directory (`A-source/A3-idea-gate.md:50-61`; `B-build/B1-scaffold.md:4-8`). One-line fix: make the override a run artifact that B1 later copies, or create it as B1's first gated action.
4. **Disclosure search assumes GitHub Issues.** Gate 3 offers only GitHub issue/PR commands and no authoritative-tracker discovery (`A-source/A3-idea-gate.md:116-139`). Santuario has GitHub Issues disabled and a live JIRA disclosure that the GitHub path cannot see (`/home/agvidit/swebench/runs/shortlist-proto.md:65`; `friction.md:169-189`). One-line fix: require tracker discovery at A1 and tracker-specific behavior/comment searches at A3.
5. **The conformance checker traverses generated run directories.** `md_files()` walks the entire repository and excludes only `.git` (`check-playbook.py:18-23`), so `python3 check-playbook.py` currently reports failures from `.e2e` artifacts rather than only the playbook. One-line fix: exclude `.e2e` and other generated directories, or explicitly enumerate source roots.
6. **Attempt accounting contradicts the router.** The router counts only a completed diagnosis that produced a pushed commit (`00-ROUTER.md:69-77`), while C5 says entering C1 counts as an attempt before repair/push (`C-drive/C5-cohort-loop.md:118-135`). One-line fix: increment only after the pushed repair commit.

### Degrading

7. **A3 gives two incompatible gate orders.** Its prose says probes run at stage 0, while the numbered table and checklist put Gates 4–5 after Gates 0–3 (`A-source/A3-idea-gate.md:12-26`, `A-source/A3-idea-gate.md:251-264`). One-line fix: publish one canonical order in all three places.
8. **A2's owner split is underspecified.** The header says Claude never generates ideas or surfaces, while the generic checklist tells the runner to choose the C-axis/A-shape (`A-source/A2-idea-generate.md:5`, `A-source/A2-idea-generate.md:272-275`). One-line fix: assign each checklist row to MetaCode, Codex, or orchestrator explicitly.
9. **A2's self-audit vocabulary invites false completion.** It allows only PASS/FAIL/N-A, requires a non-PASS or residual risk, and says any FAIL card must be repaired or discarded (`A-source/A2-idea-generate.md:244-259`). One-line fix: add `AT-RISK` and define whether it may advance.
10. **A2's count contract conflicts with its own expected funnel.** The header advertises ≥8 cards, but the sizing section expects 15–20 surfaces to collapse to 2–4 and says quality, not count, controls exit (`A-source/A2-idea-generate.md:7-8`, `A-source/A2-idea-generate.md:59-60`). One-line fix: remove ≥8 as a dispatch target or scope it to a multi-pass portfolio, not one repo.

## Executor defects, separate from playbook defects

- A2 claimed completion despite two materially incomplete checklist lines and explicit card FAILs (`handoffs/01-A2.md:168-174`; `review/01-A2-review.md:20-31`).
- A3 claimed completion despite missing Gate-0, Gate-2, Gate-3, Gate-6, and Gate-7 evidence and an unrun Gate 4 (`handoffs/02-A3.md:175-185`; `review/02-A3-review.md:12-35`).
- C3's `5/5 desired path` classification is contradicted by the actual responses (`artifacts/probes/C-2.out:11`, `artifacts/probes/C-4.out:12`, `artifacts/probes/C-5.out:12`).
- The executor stopped after A3 even though the handoff contract routes no-survivor back to A2 (`DONE:1`; `A-source/A3-idea-gate.md:284-286`).
- The predecessor A1 artifact violated A1's “screen repos, not ideas” boundary by supplying three candidate surfaces (`A-source/A1-repo-screen.md:7-10`; `/home/agvidit/swebench/runs/shortlist-proto.md:75-88`). The current executor did correctly treat those as hypotheses and re-gated them (`artifacts/survey.txt:155-187`; `handoffs/01-A2.md:157-167`).

## Claims still taken on trust

- The five zero-result JIRA behavior searches and the complete 28-branch novelty conclusion were summarized but their raw outputs were not retained (`handoffs/02-A3.md:23-32`).
- The 151,277-file peer-corpus zero-hit claim is summarized without the raw hit log (`handoffs/01-A2.md:138-139`).
- The 6m35 full-suite timing was inherited from the shortlist rather than rerun in this run (`/home/agvidit/swebench/runs/shortlist-proto.md:73`; `handoffs/01-A2.md:124-126`).
- Card authorship is supported by the MetaCode run log, not an independent provenance record (`/tmp/santuario-pair/notes/cards.out:1-16`).

The JIRA open count and the status/content of SANTUARIO-635, SANTUARIO-618, and SANTUARIO-489 were independently rechecked; they agree with the run's substantive disclosure claims (`friction.md:159-182`; `handoffs/02-A3.md:23-32`).

## What a human still has to do

1. Decide whether Santuario is exhausted or authorize another bounded A2 pass; the playbook has no terminal rule for this decision (`A-source/A3-idea-gate.md:284-286`).
2. Reject or rework the A2 cards until every card has a valid P1–P6 composition, required schema, complete audit, and no unresolved FAIL (`A-source/A2-idea-generate.md:124-140`, `A-source/A2-idea-generate.md:244-251`).
3. Re-run C3's Gate-5 probe on the actual constraint-stating step, then perform all earlier mandatory gates with retained evidence (`A-source/A3-idea-gate.md:251-270`).
4. Resolve where and when Gate 4 can legally obtain its contract, grader, and implementations (`A-source/A3-idea-gate.md:159-166`; `00-ROUTER.md:24-27`).
5. If a survivor emerges, execute all of B1–B5 and C-drive; none of their structural, oracle, calibration, or review exits has been exercised here (`00-ROUTER.md:24-39`).
6. Repair the checker scope before relying on it as a playbook conformance gate (`check-playbook.py:18-23`).

## Final verdict

**Neither a complete autonomous loop nor a completed supervised loop.** It is a partially supervised A-source run with valuable repo evidence, but no valid A3 terminal result and no benchmark task.

# Review — 03-A2r2-A3r2-FINAL.md

## Verdict: FAIL

Stopping without manufacturing a task is the right portfolio decision, especially because the repo fails literal A1. But this file does not validly complete either act it claims to combine: A2 has no checklist or HANDOFF, and A3 starts without a prior A2 HANDOFF. Its decisive S01 disclosure kill also conflates two different behaviors.

## Checklist audit

- **A2 — FAIL, no checklist to audit.** The file reports the dispatch and zero-card result (`handoffs/03-A2r2-A3r2-FINAL.md:9-23`) but contains neither A2's 13-line checklist nor a `HANDOFF A2` block. Every act must emit its own HANDOFF and no next act may begin without it (`00-ROUTER.md:196-216`; `A-source/A2-idea-generate.md:265-299`). Combining A2 and A3 erased that boundary.
- **A3 line 1 — FAIL.** It ticks “Read HANDOFF A2” using raw `/tmp/oxigraph-run/cards2.out` (`handoffs/03-A2r2-A3r2-FINAL.md:176-181`), but no round-2 A2 HANDOFF exists. This directly conflicts with `00-ROUTER.md:215-216`.
- **A3 line 5 — FAIL.** It marks Gate 2 ticked for S02 based on a source excerpt (`handoffs/03-A2r2-A3r2-FINAL.md:42-59`, `handoffs/03-A2r2-A3r2-FINAL.md:184`). Gate 2 explicitly requires an executed reproduction at `base_commit`, not code reading alone (`A-source/A3-idea-gate.md:104-114`, `A-source/A3-idea-gate.md:261`). No round-2 execution command or output is given.
- **A3 line 6 — evidence exists, conclusion overreaches.** The disclosure artifact does preserve nine query totals, branch output, issue comments, and the feature sweep (`artifacts/A3-disclosure-log.md:5-196`). However, issue #1624 discusses an **unregistered/unsupported** custom function being raised while determining a SERVICE clause's output variables (`artifacts/A3-disclosure-log.md:151-172`). S01 concerns allowing a **registered callback**—currently `Fn(&[Term]) -> Option<Term>`—to propagate its own failure (`handoffs/03-A2r2-A3r2-FINAL.md:61-72`). The cited thread neither proposes `Option`→`Result` nor a callback-error channel, so it does not satisfy Gate 3's required same “direction, workaround, API or remedy” test (`A-source/A3-idea-gate.md:116-120`).
- **A3 line 13 — supported only at the multi-turn level.** There is no viable multi-turn card after round 2 (`/tmp/oxigraph-run/cards2.out:80-110`). But S01 remains acknowledged as a live single-turn surface (`handoffs/03-A2r2-A3r2-FINAL.md:27-36`, `handoffs/03-A2r2-A3r2-FINAL.md:61-72`), and the required fallback ladder says single-turn is considered only after the cascade ladder (`A-source/A3-idea-gate.md:220-228`). That fallback was not probed.

## Evidence quality

The byte counts are measurements and match the files on disk (`handoffs/03-A2r2-A3r2-FINAL.md:13-17`). The S01 signature and call site are accurately quoted from the pinned tree (`handoffs/03-A2r2-A3r2-FINAL.md:61-72`; `/tmp/shortlist-data/clones/oxigraph/lib/spareval/src/expression.rs:28-29,631-642`). The disclosure query totals and branch list are persisted (`artifacts/A3-disclosure-log.md:5-103`, `artifacts/A3-disclosure-log.md:103-131`). The S02 hollow claim is plausible from the quoted source, but was labelled an executed Gate-2 completion without execution. The S01 public-disclosure claim is not supported by the quoted issue text.

## Boundary check

No task directory was created and no `instruction.md` or task `tests/` path was written (`handoffs/03-A2r2-A3r2-FINAL.md:267-275`). MetaCode produced the round-2 text while Claude dispatched and verified it (`handoffs/03-A2r2-A3r2-FINAL.md:9-17`), which respects authorship. However, the executor appended post-review corrections to already-completed handoffs (`handoffs/03-A2r2-A3r2-FINAL.md:195-197`). That does not violate file ownership, but it destroys the append-only audit assumption behind “do not re-review a file already covered.” Corrections should have been new numbered handoffs or errata artifacts.

## Director's call

Do not build a task from this run. The literal A1 gate already disqualifies oxigraph because `AGENTS.md` is present (`/home/agvidit/swebench/runs/shortlist-data.md:75`; `A-source/A1-repo-screen.md:25-30`). Even if a human narrows that overbroad rule, there is no defensible multi-turn survivor: C01 is publicly burned and C02 is hollow (`handoffs/03-A2r2-A3r2-FINAL.md:207-232`). But S01 is still a potentially viable single-turn candidate, not proven dead by #1624; the executor should have run the single-turn fallback gates rather than claim every surface dead.

## Defect attribution

### Executor defects

- Combined two acts and omitted the A2 checklist/HANDOFF (`handoffs/03-A2r2-A3r2-FINAL.md:1-23`, `handoffs/03-A2r2-A3r2-FINAL.md:176-202`).
- Ticked A3 checklist line 1 without a round-2 A2 HANDOFF (`handoffs/03-A2r2-A3r2-FINAL.md:180`).
- Ticked executed Gate 2 using only source inspection for S02 (`handoffs/03-A2r2-A3r2-FINAL.md:42-59`, `handoffs/03-A2r2-A3r2-FINAL.md:184`).
- Overstated issue #1624 as disclosing S01's registered-callback error channel (`handoffs/03-A2r2-A3r2-FINAL.md:100-123`; `artifacts/A3-disclosure-log.md:151-172`).
- Stopped without testing the surviving single-turn fallback despite A3's ladder (`handoffs/03-A2r2-A3r2-FINAL.md:156-172`; `A-source/A3-idea-gate.md:220-228`).
- Mutated completed, already-reviewed handoffs instead of issuing numbered correction artifacts (`handoffs/03-A2r2-A3r2-FINAL.md:195-197`).

### Playbook defects

- **No finite no-survivor termination rule.** A3's HANDOFF always routes no-survivor back to A2 (`A-source/A3-idea-gate.md:272-287`), while A2 permits zero as valid (`A-source/A2-idea-generate.md:60`) and routes unconditionally to A3 (`A-source/A2-idea-generate.md:286-299`). Fix: add an evidence-based exhaustion/maximum-round stop and specify when parked single-turn candidates must be evaluated.
- **No immutable/corrective handoff protocol.** The router requires numbered handoffs and forbids re-reviewing covered files operationally, but says nothing about corrections after review (`00-ROUTER.md:196-216`). Fix: require corrections as a new numbered erratum that references, but never modifies, the reviewed handoff.
- **A1's `AGENTS.md` rule is overbroad or was silently waived.** Literal presence is a hard kill (`A-source/A1-repo-screen.md:25-30`), yet this repo's file is ordinary contribution/test guidance (`/tmp/shortlist-data/clones/oxigraph/AGENTS.md:1-49`). Fix: define the content threshold or enforce presence strictly.

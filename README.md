# SWE-bench-Pro authoring playbook

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

A complete, dispatchable process for taking a SWE-bench-Pro task from "no repo picked" to
"accepted by the server" — single-turn or multi-turn.

**Agents start at [`00-ROUTER.md`](00-ROUTER.md) and read nothing else first.** That file
determines your state in one command and sends you to exactly one act-file. Humans can start
here.

## How it is organised

Every file is **one act**: one owner, one input state, one output artifact, one exit
condition, stated in its header. That is what makes a file handable to a subagent without
writing a bespoke brief — the act-file *is* the brief.

```
00-ROUTER.md      state → act-file · field authority · concurrency · hard stops

A-source/         no repo ──────────────→ a candidate worth building
  A1-repo-screen   A2-idea-generate   A3-idea-gate
  A4-corpus-prior        search the WHOLE org corpus by concept, before ideating

B-build/          a candidate ──────────→ a pushed task
  B1-scaffold  B2-contract  B3-grader  B4-solution-env
  B7-local-calibration   classify every trial, then read the band
  B6-review-gate         run the server's own reviewers locally, first
  B5-preflight-push      preflight 0, then push

C-drive/          a server verdict ─────→ a green task
  C1-read-verdict  C2-repair-grading  C3-harden  C4-loosen-salvage  C5-cohort-loop
  C6-replay-verify       prove a change against real prior trajectories
  C7-revision-response   answer a HUMAN reviewer and re-submit
  C8-retire              park is not retire · the commit budget

reference/        pulled on demand, never read front-to-back
  R1-field-authority  R2-signal-integrity  R3-landmines  R4-ownership
  R5-search-axes      R6-fork-patterns     R7-algo-catalogue (QUARANTINED)
  R8-finding-to-file  R9-review-ledger     R10-step1-calibration

assets/avocado/   the four immutable Avocado prompts + shared _INVARIANTS
tools/            review-gate · bundle-hash · authorship-audit · task-budget
                  avocado-brief · probe-lint · reviewer-relay

ledger/           RUNS.md (evidence) · RULES.md (precedence) · PROVENANCE.md
                  POSTMORTEM-MT-2026-09.md (every MT task, per-task cause)
```

**Build order is `B1 B2 B3 B4 → B7 → B6 → B5`, not numeric.** Calibrate and classify before you
review, review before you push. The server's reviewer cannot see an unpushed tree, so `B6` is the
last place a rubric failure is cheap.

## Three rules that keep it from rotting

1. **No rule appears in two files.** If another file owns it, link to it. Two copies drift,
   and drift is the defect both source pipelines kept shipping.
2. **Every rule carries a status** — `LIVE`, `SUPERSEDED-BY`, `SCOPED-TO`, or
   `UNVALIDATED-PRIOR` — and a pointer to the run that produced it. See
   [`ledger/RULES.md`](ledger/RULES.md).
3. **Every measurement keeps its number.** A rule without its n is an opinion.

## Model assignment

Ownership is not a style preference — provenance is scored by path, and one wrong write
retires a task. The matrix is in [`00-ROUTER.md`](00-ROUTER.md) §5; the reasoning and the
violation-capture protocol are in [`reference/R4-ownership.md`](reference/R4-ownership.md).

Short version: **Codex or 1P owns everything under `tests/`. MetaCode/1P owns the
instruction, and only during `B2`. Claude owns the solution, environment, diagnosis, and
every push.**

## Running it in parallel

Repo screening, ideation, probes and artifact reads fan out freely. Repairs never do — each
spawns Docker work and parallel runs have exhausted host memory. Full table in
[`00-ROUTER.md`](00-ROUTER.md) §6.

## Where it came from

Merged from two independently-measured pipelines. See
[`ledger/PROVENANCE.md`](ledger/PROVENANCE.md) for what each contributed, the evidence-density
comparison, the three decisions taken at merge time, and the conflicts still open.

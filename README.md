# SWE-bench-Pro authoring playbook

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
  A1-repo-screen        A2-idea-generate        A3-idea-gate

B-build/          a candidate ──────────→ a pushed task
  B1-scaffold  B2-contract  B3-grader  B4-solution-env  B5-preflight-push

C-drive/          a server verdict ─────→ a green task
  C1-read-verdict  C2-repair-grading  C3-harden  C4-loosen-salvage  C5-cohort-loop

reference/        pulled on demand, never read front-to-back
  R1-field-authority  R2-signal-integrity  R3-landmines  R4-ownership
  R5-search-axes      R6-fork-patterns     R7-algo-catalogue (QUARANTINED)

ledger/           RUNS.md (evidence)  ·  RULES.md (precedence)  ·  PROVENANCE.md
```

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

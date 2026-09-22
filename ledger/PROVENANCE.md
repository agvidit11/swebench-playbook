# PROVENANCE — what this playbook is made of

## Sources

This playbook is a merge of two independently-developed SWE-bench-Pro authoring pipelines,
both graded by the same internal server, neither of which knew about the other.

| | files | lines | centre of gravity |
|---|---:|---:|---|
| **OURS** — `~/.claude/skills/swebench-mt/` + `~/swebench/*.md` | 13 | 5,715 | **Phase A** (58% of lines) — sourcing, novelty, fork/outcome-variance prediction before a task dir exists |
| **PEER** — `codimango/badahal-swe-bench/.ideas_pipeline/steps` | 10 | 3,116 | **Phase C** (61% of lines) — reading server verdicts, repair, cohort driving |

The shapes were inverted, which is why the merge is mostly placement rather than rewriting:
we had built a selection pipeline, they had built a repair pipeline.

An independent 552-line comparison of the two, with line-cited conflicts, was produced by
Codex (`gpt-5.6-sol`, xhigh) and is preserved at `/tmp/pipeline-compare/CODEX-OUTPUT.md`.

## Evidence density, measured

| set | lines | measured-n lines per 1k | quoted server verdicts per 1k | distinct named tasks |
|---|---:|---:|---:|---:|
| PEER | 3,116 | 14.4 | **15.7** | 9 |
| OURS | 5,715 | **22.6** | 6.3 | **32** |

We measured more; they quoted the server 2.5× more often and tied each quotation to one
mechanical remedy. Both properties are wanted, and the merged files are expected to carry
both — a rule without its measurement is an opinion, and a measurement without a remedy is
a war story.

## What each set contributed

**From PEER, largely wholesale:** the four-layer over-pinning taxonomy (Name/Value/Shape/
Semantic, and the finding that shape dominates); mirror drift and the SHRANK detector;
cross-step duplicate divergence; executed-but-ungraded failures; "a mutant is a floor, not a
proof"; the R06 seed-independence protocol and its three proofs; TBR/Agentic independence;
the Eval-GT-is-a-tool clarification; the provenance violation-capture protocol; commit-bound
review verdicts; measurement hygiene; and the cohort driver in `C5`.

**From OURS, largely wholesale:** everything predictive — the fork probe (argued fork
strength was wrong 11 times out of 11), the outcome-variance probe, the three free
pre-filters; intra-benchmark dedup against the 133k-task corpus; the AI-authorship sourcing
gate; the public-PR sourcing prohibition; repro-verify at `base_commit` before scaffolding;
the 17 named scaffold landmines in `preflight.sh`; the eval-GT `base_commit` root cause;
the Harbor pull race; the single-turn delta; and the `R5`/`R6` idea libraries.

## Three mechanisms neither source had

1. **One act per file** — one owner, one input state, one output artifact, one exit
   condition, and a `HANDOFF` block. PEER's files were dispatchable but split by stage;
   ours were navigable but bundled up to four owners per file.
2. **A precedence channel** (`RULES.md`). Both sets rotted identically: PEER's stage 07 still
   mandated cumulative patches that stage 05 had retracted; OUR `2-build.md` carried five
   contradictory naming rules, two of which each declared the *other* superseded.
3. **A field-authority layer** (`00-ROUTER.md` §2, `reference/R1`). Zero of `tbdReviewStatus`,
   `tbrNotFinalized`, `validationDetails`, `qualitativeResult`, `oraclePassCount` or
   `__validation_stage` appeared anywhere in our 13 files. Our router said *which document*;
   it never said *which field to believe*.

## Decisions taken at merge time

| id | decision | why |
|---|---|---|
| **D1** | The naming rule is a **sourcing filter**. `A3` rejects any candidate whose graded assertion needs a name absent at `base_commit`; `B2` then names what the grader pins and nothing else; `B3` proves every unnamed symbol has a name-agnostic assertion. | Reconciles our "name nothing" with PEER's measured `BAD_GRADING_WRONG` on 4 of 4 tasks built under an absolute never-name rule. The illegal configuration is *silent spec + pinning test*; D1 forbids it from the sourcing end rather than by widening every spec. |
| **D2** | **IRON-CLAD: Claude and Codex never write `instruction.md` or `steps/*/instruction.md` in any phase or state. Only Avocado (MetaCode) or Vidit by hand.** Indirect routing through an agent, script, heredoc or patch file is the same violation, as is suggesting the exact replacement text. A finding that can only be fixed there is recorded `Owner: Avocado/human` and the thread stops; every other thread continues. | Strengthened past PEER's own boundary, which scoped the ban to its repair prompt only and left stage 06 handing instruction edits to Avocado with no version marker saying which was current. Here there is no phase-dependence to get wrong. |
| **D3** | The playbook is a git repo, and the `swebench-mt` skill shrinks to a pointer. | Shareable with teammates and with Codex sessions; the ledger gets real history. |

## Known unresolved conflicts

Carried forward as `CONFLICT — UNRESOLVED` markers at their sites rather than silently
decided. Each needs an external answer, not more reading:

- **Licence policy.** Our kill sheet hard-blocks AGPL-3.0/SSPL/Commons Clause; our own
  brainstorm runbook says only CreativeML OpenRAIL-M is prohibited and copyleft is a plus;
  `codimango-external-repos-spec.md:178` hard-blocks. Two screening agents hit this
  independently on 2026-09-22.
- **Top-level MT `tests/config.json`** — stub versus real aggregate record.
- **Step patch format** — cumulative-from-base versus sequential delta (PEER `07` appears
  stale against PEER `05` and ours, but no version marker says so).

## What is deliberately not here

Per-task Codex briefs and run write-ups from `~/swebench/*.md` (30 files, 9,538 lines) are
run artifacts, not process. They belong in `RUNS.md` entries. The act-files *are* the briefs
now — if you find yourself writing a bespoke brief for a subagent, that is a signal the
act-file it should have been handed is missing or too broad.

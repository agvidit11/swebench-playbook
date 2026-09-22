# R1 — Field authority: which server field is true, and which ones lie

```
OWNER:  Claude (reference — pulled on demand, never read front to back)
INPUT:  one unanswered question about a task's server state, plus any of
        `codimango task show <task> --json`, `task errors`, `job review`, `job list`
OUTPUT: a correct reading of one field. This file writes nothing.
EXIT:   for the question you are asking you can name (a) the one authoritative field and
        (b) every field that must be ignored while answering it.
```

`00-ROUTER.md` §2 is the eight-row summary of this file. **If the two disagree, this file is
right and the router is the bug** — fix it here, then re-summarise there. Find your field, read
that section, go back to your act-file.

---

## 1. The eight `validationDetails` labels

`validationDetails` is a **list**, and the label set differs by format. **Map by label, never
by position.** `STATUS: LIVE` — measured across one draft cohort.

```bash
codimango task list --filter mine --limit 100 --json > /tmp/tl.json
jq -r '(.tasks//.)[] | select(.status=="draft") |
  .name as $n | ((.validationDetails//[])[]) |
  [$n,.label,.status,(.detail|gsub("\n";" "))] | @tsv' /tmp/tl.json
```

| # | Label | Gates | Present in |
|---|---|---|---|
| 1 | `Structural checks` | scaffold and packaging legality | both formats |
| 2 | `Oracle validation` | the golden satisfies the graded suite | both formats |
| 3 | `Metacode or Opus pass/fail balance` | the calibration / step gate → §5 | both formats |
| 4 | `Agentic trial-output review` | rubric review of the trials | MT: **sometimes** |
| 5 | `AI assessment` | not decoded by either source | **single-turn only** |
| 6 | `LH: Solvability & Difficulty` | long-horizon solvability | MT: **sometimes** |
| 7 | `Contamination check` | must not read `failed` | both formats |
| 8 | `Provenance check` | authorship → §6 | both formats |

**There is no Eval GT row.** → §3.

Format differences, measured on the current cohort:

- Multi-turn carries **either** `Agentic trial-output review` **or** `LH: Solvability &
  Difficulty` — not always both.
- Single-turn adds `AI assessment` and has **no step decomposition at all**.

Two consequences that have each cost a round:

- **`Structural checks` FAIL ⇒ zero trials were dispatched.** Local `bench validate
  --structural-only` *lags* the server — it missed `track_assignment` entirely. Trust the
  server's `structuralCheckResult`.
- **`Oracle validation` red skips every other gate.** Diagnose it first whatever else is red.

---

## 2. Question → authoritative field

`STATUS: LIVE`

| Question | Read | Never read |
|---|---|---|
| Did gate X pass? | the `validationDetails` row **matched by label** | row position |
| How hard is the task? | `job review <task> --commit <40-hex>` → `Task difficulty:` | `qualitativeResult.difficulty.classification` → §4 |
| How many oracle/agent runs passed? | `job list` / `trial list` | `oraclePassCount`, `agentPassCount` → §4 |
| Is the quality review clean? | `tbdReviewStatus` **with** `tbrNotFinalized` → §3 | anything labelled "Eval GT" |
| Did the golden build cold? | the `codimango bench tbd evalgt` run output | any `validationDetails` row |
| Grader rejected a good solution, or agent wrong? | `attemptResults[].result` → §4 | the aggregate pass rate |
| Does the test patch apply and grade? | `job list` filtered on `.config.env.__validation_stage` → §4 | — |
| Was a protected file written by an agent? | `provenanceCheck.agentWrites.agentModified` → §6 | `classifierResult.p3p` |
| Is this step in band? | the per-step `avocado …: N/M` figures → §5 | any aggregate or averaged rate |

---

## 3. `tbdReviewStatus`, and the Eval GT that is not a gate

### `tbdReviewStatus` is the TBD **quality review**

`STATUS: LIVE`. Its payload is a set of dimensions, not a build result:

`spec_clarity`, `test_quality`, `hackability`, `code_patch_quality`, `information_leakage`,
`output_ambiguity`, `repo_integration`, `scope_creep`, plus **three `revised_task_specification`
variants**.

**It is not the Eval-GT verdict.** Both source pipelines made this mistake in their own
prompts. Labelling it "Eval GT" invites reading a *review* failure as a *golden* failure and
**sends the repair in the wrong direction**.

Read it together with `tbrNotFinalized`:

- **`tbrNotFinalized: true` means PENDING, not failed.** Only a *finalised* `fail` is
  actionable. Measured: **9 of 10 drafts in one cohort carried `tbrNotFinalized: true`** — this
  is the common case, not the exception. Spend no attempt on it.
- All four headline dimensions can read `Good` while the status is `fail`. When that happens
  the reason is in the prose, not a rating field (`valid_task_rating_value` is often empty):
  `jq -r '.tbdReviewDetails.full_assessment'`.
- Dimension bands are not stable run to run: one task read `Good` in the morning and `Requires
  Some Guessing` that afternoon on nearly the same tree. Treat a one-band move as noise unless
  the explanation text changed with it. Ladder: `Good` > `Requires Some Guessing` >
  `Under Specified`.

### Eval GT is a TOOL, not a gate

`STATUS: LIVE`. Verified against the live task record:

- The schema **does** carry a top-level `evalGtNotFinalized` key — so Eval GT is a real
  concept — but it is **null across the cohort**, there is **no companion status field**, and
  there is **no `validationDetails` row**. Nothing blocks on it.
- `codimango bench tbd evalgt -p <task> -f swe` is a **manual, stateless** build plus
  ground-truth run. **Its verdict never reaches the task record.** It prints a numeric Workflow
  Run ID; capture it or you re-run the build. Resume/poll:
  `codimango bench tbd fetch-workflow <RUN_ID> -f swe --output json`.
- Its value is that it is the only check that runs the golden **cold** — the in-situ oracle
  runs inside an inherited session with prior-step residue on disk, so it structurally cannot
  catch the "passes locally, fails in the cloud" class. Run it, do not wait on it, do not score
  it. → repair routing lives in `C-drive/C2-repair-grading.md`.

---

## 4. Fields that lie, and the two that disambiguate

### `qualitativeResult.difficulty.classification` contradicts the review

`STATUS: LIVE`. Measured on two named tasks: the field read `TOO_HARD` for both
`aasm-error-census-attribution` and `resque-hook-phase-accounting` while
`codimango job review <task> --commit <40-hex>` rated each **`GENUINELY_HARD`**.

**The review's `Task difficulty:` line is authoritative.** The field is not. A `TOO_HARD` there
is never a reason to re-open a task whose gates are green.

### Summary counters go stale

`STATUS: LIVE`. `oraclePassCount`, `agentPassCount` and friends read `null` or `0/N` for arms
that **completed successfully**. One task showed `oracle null/null, agent 0/5` while its jobs
had finished with the oracle passing **3× at reward 1.0, 80/80**, and its review recorded **4
of 15** non-oracle attempts passing.

Read `job list` / `trial list` or the `validationDetails` gate strings. Treat the summary
columns as a UI convenience only.

### A missing row is not a gate that did not run

`STATUS: LIVE`. **A missing `Agentic trial-output review` row does not mean the gate did not
run.** Measured: `aasm-error-census-attribution` had no such row while `job review` at the same
SHA returned `GOOD / GENUINELY_HARD`.

The row and the standalone review are **two different surfaces**. A task can pass the row while
the standalone is stale, and can have **no row at all** while the standalone returns `GOOD`.
Resolve per task:

```bash
codimango job review <task> --commit <full-40-char-sha>   # Verdict: / Task difficulty:
```

### `attemptResults[].result` — the only field that separates our bug from their miss

`STATUS: LIVE`.

| Value | Meaning |
|---|---|
| `GRADING_FAILURE` | the grader rejected a **valid** solution — our defect |
| `FAIL_REASONING` | the agent was wrong — the task did its job |

```bash
codimango job review <task> --json | jq -r '
  .review.rubrics.items[] | select(.verdict|test("FAIL";"i")) | "[\(.id)] \(.dimension)\n   \(.evidence)\n",
  (.review.attemptResults[]? | "\(.model) \(.result)")'
```

**Fix every `GRADING_FAILURE` before reading any pass rate.** Two of them, from one
over-specific fault injection, made every other number on that task unreadable.

### Job stages — where patch/build health actually lives

`STATUS: LIVE`. Filter `job list` on `.config.env.__validation_stage` to separate
`test-patch-validation` from `test-patch`.

| Failing | Means |
|---|---|
| `test-patch-validation` | the test patch does not apply, **or** applies and grades nothing |
| manual `evalgt` / stateless build | the image or toolchain is broken — passes locally, fails cold |
| `Oracle validation` | the patch applies and builds, but the golden does not satisfy the tests |

> **Gap.** Both sources name the `test-patch` stage as a filter value but decode only
> `test-patch-validation`. The meaning of a `test-patch` stage failing *on its own* is not
> stated in either source. Do not guess it — read the job log.

### `Oracle validation: pending — No oracle trials run`

`STATUS: LIVE`. With every other gate green this is an **unstarted arm, not a defect**.
Trigger it; repair nothing.

---

## 5. The MT calibration gate, decoded

`STATUS: LIVE` for multi-turn. The `Metacode or Opus pass/fail balance` detail string encodes
`avocado s1|s2, opus s1|s2, gpt s1|s2`. Expand it **per step and per model** — this is the axis
most often missed and it is frequently the binding constraint.

| Task | avoc s1 | avoc s2 | opus s1 | opus s2 | gpt s1 | gpt s2 | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| thor | 0.4 | **0** | 1.0 | **0** | 0 | NA | s2 too hard |
| circuit-probe | 0 | NA | 0 | NA | 0.4 | **1.0** | s2 no gradient |
| paper-trail | **1.0** | 0 | 0 | NA | 0.2 | 0 | s1 too easy |

**Decode rules — none of this is inferable from pass/fail alone:**

- **The passing rule**, confirmed against two accepted multi-turn tasks: *every step has a pass
  and a fail on the same model, and avocado is never at 1.0.* `maglev` at
  `avocado 0.6|0.6, opus 0.2|1, gpt 0.2|0.8` is the reference shape.
- **The ceiling is 3/5 per step.** In-band is **1–3 of 5**; `4/5` fails. OURS records the
  ceiling as observed on **2026-09-17**; the server's own string calls the prior regime *"the
  pre-9/15 rules"*. Both phrasings appear verbatim in the sources; they are the same tightening.
- **`NA` is not zero.** It means that model never reached the step. Step-2 effective n is
  bounded by step-1 successes, so an `NA` column says nothing about that step's difficulty.
- **`minimum_steps_for_nonfinal_all_pass_exception = 3`.** A two-step task gets **no**
  saturation exemption. The exemption is **one per task**, and **the last step is never exempt**
  regardless of step count.
- **The gate is skipped entirely unless the oracle is 3/3.** `codimango bench run -p <task>
  -a oracle -k 3` must read 3/3 before any of this means anything.
- Grandfathering: a task can read `Passed under the pre-9/15 rules (current rules: … too easy …)`
  and remain marked passed. That is fragile — a rerun or policy cleanup exposes the
  current-rule failure. `jsonschema` sat in exactly this state at `avocado 0.2|0.8`.

### Avocado 0/5 is not itself a failure — and the two rules are not the same rule

`STATUS: LIVE`. **`CONFLICT — RESOLVED BY MEASUREMENT`, recorded because OURS has been
conflating these two statements:**

1. **The server rule.** The gate needs **one pass and one fail on the same model**, and that
   model **may be Opus or GPT**. The server reports *too hard* only when **all three** are
   zero: `"<step>" too hard — no model passed it (avocado 0, opus 0, gpt 0)`.
2. **The operational target.** "1–3/5 avocado on every step" is a *stricter* self-imposed aim,
   adopted so a task never depends on an Opus/GPT rescue to clear the gate.

These are **not the same validation condition**. Do not report a task as failing the gate
because avocado is 0/5 when another single model carries both a pass and a fail. Do not report
a task as done against rule 1 when your own standard is rule 2 — say which one you applied.

### The five verdict strings

| String | Meaning | Difficulty signal? |
|---|---|---|
| `"<step>" too hard — no model passed it` | every arm 0 on that step | **only after grader artifacts are excluded** → `C-drive/C4-loosen-salvage.md` |
| `"<step>" has no gradient` / `1.0 pass-rate` | every model that reached it passed every attempt | yes — too easy |
| `"<step>" too easy — avocado passed N of 5` | avocado over the 3/5 ceiling | yes — too easy |
| `Not solvable — no agent passed` | 0 across all arms, all steps | usually a **grader defect**, not difficulty |
| `Insufficient legitimate sample` / `no countable runs` | **infrastructure** — no usable result | **never.** → `reference/R2-signal-integrity.md` |

The last row has cost real cycles: one task's `0/10, 0/8, 0/0` was read as difficulty when every
trial carried `status=error` from `Classified failed command as ApiRateLimitError`.

### Single-turn uses a different rule

`STATUS: SCOPED-TO single-turn`. The rule is **"avocado not trivial AND ≥1 agent solved"**. A
single-turn task at **avocado 4/5 with opus 0/5 and gpt 0/5 PASSES** — server verbatim:
`Passed — avocado not trivial and >=1 agent solved`. Applying the MT band to a single-turn task
nearly had an agent harden a task that had already passed its balance gate with two of three
models at 0/5. **Check `format` in `task.toml` before reading any pass rate.**

---

## 6. The provenance payload

`STATUS: LIVE`. `Verdict: SUSPECT — review recommended` is common and is usually **not** what it
sounds like. Read the payload before escalating anything:

```bash
codimango task show <task> --json | jq '.qualitativeResult.provenanceCheck
  | {verdict, p3p:.classifierResult.p3p, agentWrites:(.agentWrites|{verdict,agentModified,maxMatchScore}), note:.combinationNote}'
```

| Field | Authority |
|---|---|
| `agentWrites.agentModified` | **authoritative.** `false` with `maxMatchScore: 0` = no agent write recorded against the protected file |
| `classifierResult.p3p` | stylometry on the prose. Reaches **0.96–0.996** on human/Avocado-written specs routinely. On its own it is *flagged, not blocked* — the note says so verbatim: *"classifier ≥0.99 but uncorroborated (stylometric & trajectory clean)"* |
| `combinationNote: "carried forward from the previous run (not re-observed here)"` | the write log was **not** re-checked this run. It neither confirms nor clears anything since. A CLEAN carried forward across a round in which an agent touched the file is **not** evidence of safety |
| `presentInCurrent` | **unreliable.** A one-token edit flips it to `false` while the block survives verbatim; **12 of 12** logged blocks were still present on a task matching the supposed false-positive signature. Substring-match the logged blocks yourself |

Measured: in one cohort **four tasks read SUSPECT simultaneously with `agentModified: false`
throughout** — a portfolio-wide classifier artifact, not four incidents. Do not spend a repair
round on it.

The genuinely serious case is different: a 3P model **writing** to a protected file at all.
That is not a score, it is a write, and re-editing does not undo it. → `reference/R4-ownership.md`.

---

```
HANDOFF R1
  EXIT:      the field you came for is decoded, and you can name what you must ignore
  CHECKLIST: n/a — lookup table, not an act (`00-ROUTER.md` §8)
  ARTIFACTS: none — this reference writes nothing
  FACTS:     the authoritative field for your question, and the verdict string verbatim
  OPEN:      `AI assessment` and `Contamination check` payloads are undecoded in both sources;
             a failing `test-patch` stage (as distinct from `test-patch-validation`) is undecoded
  NEXT:      return to the act-file that sent you (§1 of `00-ROUTER.md` if you have none)
```

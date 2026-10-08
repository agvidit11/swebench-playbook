# R8 — Finding → the file that owns it

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
OWNER:  Claude (reference — pure lookup, pulled on demand)
INPUT:  one finding: a rubric id, a gate string, a review verdict, a TBD dimension, or a
        failing `validationDetails` row / `__validation_stage`
OUTPUT: the artifact that owns the defect, the act-file that repairs it, and its legal author.
        This file writes nothing.
EXIT:   the finding is bound to exactly one artifact, one act-file and one author.
```

**Pointers only.** What a field *means* → `reference/R1-field-authority.md`. Whether a number is
real → `R2`. Trap catalogue → `R3`. Ownership reasoning → `R4`. Do not look for repair procedure
here; look for its address.

**Two routing rules are encoded as rows below and override any other reading:**

| Rule | Row form |
|---|---|
| **Any finding whose owning artifact is an instruction file** | author is **`Owner: Avocado/human`**, and that thread **stops**. Never Claude. Never Codex. Never indirectly. → `R4` §2 |
| **`BAD_GRADING_WRONG` and `BAD_GRADING_WEAK`** | **mutually exclusive remedies** — *remove* an assertion vs *add* a test. Never route both to the same action |

---

## 1. Agentic Review verdicts

| Verdict | Means | Owning artifact | Repair act | Author |
|---|---|---|---|---|
| `GOOD` | done on this surface | — | none — **park it** | — |
| `BAD_GOLDEN` | the gold does not satisfy a stated requirement. **Outranks everything** — a wrong gold invalidates every other number | `solution/*` (+ its mirror in `tests/config.json .patch`) | `C-drive/C2-repair-grading.md` **first** | Claude (`solution/*`) / Codex (the mirror under `tests/`) |
| `BAD_GRADING_WRONG` | correct solutions are **rejected**. Graded ⊃ stated | the graded suite | `C2` — **REMOVE an assertion** | Codex |
| `BAD_GRADING_WEAK` | wrong solutions are **paid**. Stated ⊃ graded; usually thin p2p or unrequired tests | the graded suite | `C2` — **ADD a test** | Codex |
| `BAD_AMBIGUOUS` | the contract cannot be read one way | the contract | `B-build/B2-contract.md` | **Avocado/human — thread stops** |

Severity ladder (for judging whether a change made things worse):
`GOOD` > `BAD_GRADING_WEAK` > `BAD_GRADING_WRONG` > `BAD_AMBIGUOUS` > `BAD_GOLDEN`.

---

## 2. Rubrics R01–R13, N01–N04

Focus lines are the reviewer's own. **Default repair is always the artifact you are allowed to
touch**; escalate to prose only when the contract genuinely cannot be graded fairly without it.

| # | Focus — it fails when you… | Owning artifact | Repair act | Author |
|---|---|---|---|---|
| R01 | Spec sufficiency — grade something the prompt does not state | graded suite (drop the ungrounded assertion) | `C2` | Codex |
| R01↑ | …and the behaviour genuinely cannot be graded without more prose | instruction file | `B2` | **Avocado/human — stops** |
| R02 | Spec-test alignment — add a test with no line in the spec behind it | graded suite | `C2` | Codex |
| R03 | Trajectory-informed spec — many arms fail one test ⇒ the **spec** is unclear, not the models | graded suite first; contract only if ungradeable | `C2`, else `B2` | Codex, else **Avocado/human** |
| R04 | Reasoning required — spell out the recipe, or pin the implementation shape | pinning → graded suite; recipe → instruction file | `C2` / `C-drive/C3-harden.md` | Codex / **Avocado/human** |
| R05 | Information isolation — leak the solution via env, fixtures or expected outputs | `environment/Dockerfile`, fixtures | `B-build/B4-solution-env.md`, `C2` | Claude (env) / Codex (fixtures) |
| R06 | Test coverage — leave a stated requirement ungraded (**`p2p = 0` counts**) | graded suite | `C2` (authoring-time: `B-build/B3-grader.md`) | Codex |
| R07 | Reward-hacking — tests executed but not required; thin p2p; hard-codeable scenario | graded suite | `C2` | Codex |
| R08 | Accepts alternatives — over-pin API names, key names, symbol vocabulary, accessors | graded suite | `C2`, `C-drive/C4-loosen-salvage.md` | Codex |
| R09 | Test reliability — flakiness, network/timing dependence, unpinned env, timeouts | graded suite (+ env if it is a race) | `C2`, `B4` | Codex, Claude |
| R10 | Test validity — an `f2p` that **already passes at base** | `tests/config.json` f2p/p2p lists | `C2` | Codex |
| R11 | Verification efficiency — grading needs long runtimes or manual work | `tests/test.sh` | `C2` | Codex |
| R12 | Golden correctness — gold does not satisfy a stated requirement | `solution/*` + its `config.json` mirror | `C2` — **before anything else** | Claude / Codex (mirror) |
| R13 | Golden reliability — oracle not green on every trial | `solution/*`, `environment/Dockerfile` | `C2`, `B4` | Claude |
| N01 | Real-world relevance — a contrived change no maintainer would make | the candidate itself | `A-source/A3-idea-gate.md` | Claude + Codex |
| N02 | Knowledge depth — trivia rather than specialist reasoning | the candidate itself | `A3` | Claude + Codex |
| N03 | Data realism — toy fixtures unlike real data | fixtures under `tests/` | `C2` | Codex |
| N04 | Training signal — difficulty from incidental friction rather than reasoning. **Downstream of R01/R02 — do not chase directly** | the contract's interface | `B2` | **Avocado/human — stops** |

Two that bite most often: **R08** (loosened too little) and **R06/R07** (loosened too much). A
change that fixes one and breaks the other is not progress.

---

## 3. Gate strings → where they land

| Server string | Means | Owning artifact | Repair act | Author |
|---|---|---|---|---|
| `Oracle validation: N/3 passed (all must pass)` | **everything else is skipped**; often a race that only appears under load | `solution/*`, `environment/Dockerfile`, `tests/test.sh` | `C2` (check `R2` first) | Claude / Codex |
| `Oracle validation: pending — No oracle trials run` | an **unstarted arm**, not a defect | — | trigger it | — |
| `Step gate failed — "<step>" too hard — no model passed it (avocado 0, opus 0, gpt 0)` | all three at 0. **Usually a false negative** — prove it before narrowing | graded suite | `C4` | Codex |
| `Step gate failed — "<step>" too easy — avocado passed 4 of 5, over the 3/5 ceiling` | over the ceiling; needs a **structural fork**, not more edge cases | graded suite + contract | `C3` | Codex (+ **Avocado/human** for prose) |
| `Step gate failed — "<step>" too easy — 1.0 on every model` | same, more severe | graded suite + contract | `C3` | Codex (+ **Avocado/human**) |
| `"<step>" has no gradient — avocado never reached it and every model that did passed every attempt` | **not reached ≠ failed.** Read the Steps view, check seeds | step decomposition / graded suite | `C3` | Claude (structure) + Codex |
| `has a 1.0 pass-rate and the single-1.0 exemption needs 3+ declared steps` | add a step, **or** harden. Exemption is one per task, never the last step | `task.toml` `[[steps]]` + a new step | `C3` | Claude (toml) + **Avocado/human** (new prose) |
| `the single-1.0 exemption is already spent on an earlier step` | a second step hit 1.0 — adding steps will not help again | graded suite | `C3` | Codex |
| `Not solvable — no agent passed` | 0 across all arms, all steps — **usually a grader defect, not difficulty** | graded suite | `C2` before `C4` | Codex |
| `Insufficient legitimate sample` / `no countable runs` | **infrastructure.** Never a difficulty reading | none — revalidate | `reference/R2-signal-integrity.md` | — |
| `Benchmark canary string found` | the scaffold canary on line 1 of the Dockerfile | `environment/Dockerfile` | `R3` §A.3 → `B-build/B1-scaffold.md` | Claude |
| `task.toml is missing required [task].track_assignment` | **derivable from `format`** — do not ask | `task.toml` | `B4` | Claude |
| `Passed under the pre-9/15 rules (current rules: … too easy …)` | grandfathered and fragile. Counts today; do not build on it | graded suite | `C3` when you next touch it | Codex |
| `Passed — every step has a pass and a fail on the same model, and avocado is never at 1.0` | **done** on this gate | — | `B-build/B5-preflight-push.md` → submit | — |
| `Passed — avocado not trivial and >=1 agent solved` | **single-turn only** — done on this gate | — | submit | — |
| `(no jobs on Nest)` | the validation job was never created | none | `codimango task rerun <task>` | Claude |

---

## 4. `validationDetails` rows → act-file

| Row `failed`/`error` | Repair act | Author |
|---|---|---|
| `Structural checks` | `reference/R3-landmines.md` → `C2` | Codex / Claude by path |
| `Oracle validation` | `C2` — **diagnose first, it skips every other gate** | Claude / Codex |
| `Metacode or Opus pass/fail balance` | `C3` (too easy) or `C4` (too hard) — decode per `R1` §5 | Codex (+ **Avocado/human**) |
| `Agentic trial-output review` | §1 of this file, by verdict | per verdict |
| `AI assessment` | **undecoded in both sources** — read the detail string, do not guess | — |
| `LH: Solvability & Difficulty` | `C4` if unsolvable, `C3` if saturated | Codex |
| `Contamination check` | the candidate + sourcing | `A-source/A1-repo-screen.md` | Claude |
| `Provenance check` | `reference/R4-ownership.md` | 1P re-author |

---

## 5. TBD quality-review dimensions (`tbdReviewStatus` payload)

Read with `tbrNotFinalized` first — `true` is **pending, not failed** (`R1` §3).

| Dimension | Owning artifact | Repair act | Author |
|---|---|---|---|
| `spec_clarity` | **two legal routes**: pin it in the prose, **or** make the tests indifferent to it | `B2` **or** `C2` | **Avocado/human** *or* Codex |
| `test_quality` | graded suite | `C2` | Codex |
| `hackability` | graded suite (R07 surface) | `C2` | Codex |
| `code_patch_quality` | patch packaging + golden | `R3` §B → `C2` | Claude (`solution/*`) / Codex (`tests/` mirrors) |
| `information_leakage` | fixtures, env, expected outputs — or the prose | `C2` / `B2` | Codex / **Avocado/human** |
| `output_ambiguity` | the contract | `B2` | **Avocado/human — stops** |
| `repo_integration` | the candidate and the scaffold | `A3` / `B1` | Claude |
| `scope_creep` | the contract's breadth (+ tests that follow it) | `B2` / `C4` | **Avocado/human** / Codex |
| `revised_task_specification` ×3 | reviewer-proposed prose | `B2` | **Avocado/human — never paste it yourself** (`R4` §2) |

**Widening graded tests moves `spec_clarity` but not the Agentic verdict.** Two tasks went
"Requires Some Guessing" → Good and `tbd` fail → pass and still returned `BAD_GRADING_WRONG`.
Do not route a `BAD_GRADING_*` finding to a `spec_clarity` remedy.

---

## 6. `__validation_stage` failure classes

`job list` filtered on `.config.env.__validation_stage`.

| Failing stage | Means | Owning artifact | Repair act | Author |
|---|---|---|---|---|
| `test-patch-validation` | the test patch does not apply, or applies and grades nothing | `tests/config.json .test_patch`, `tests/test.sh` | `C2` | Codex |
| `test-patch` | **undecoded in both sources** — read the job log before acting | — | `C1` | — |
| manual `evalgt` / stateless build | the image or toolchain is broken — passes locally, fails cold | `environment/Dockerfile` | `B4` | Claude |
| `Oracle validation` | the patch applies and builds, but the golden does not satisfy the tests | `solution/*` | `C2` | Claude |

---

## 7. Findings that have no file

| Finding | Why no file owns it |
|---|---|
| `qualitativeResult.difficulty.classification: TOO_HARD` on a green task | the field contradicts the review and is not authoritative → `R1` §4. **Do not re-open** |
| an arm at 0/N inside a gate that reports `passed` | not a defect → `00-ROUTER.md` §4 |
| a "too easy" note inside a gate reporting `passed`, avocado ≤ 3/5 | not a defect → §4 |
| a reviewer complaint about an artifact the reviewer **builds itself** | packaging artifact, not a task defect → `R3` §B.2 |
| a reviewer's suggested **remedy** | a hypothesis, not an instruction — verify it. One suggested locking a parent directory, which would have deleted the contents its own assertion checked |

---

> **CONFLICT — UNRESOLVED IN SOURCES, SETTLED HERE BY `00-ROUTER.md` §5.** PEER `05`/`07`
> assign solution code to Codex; PEER `08` Phase 5 (lines 935–943) and OURS `RUNBOOK.md`
> (lines 32–49) assign `solution/*` to Claude, while PEER `08` Phase 5.5 (lines 953–962) routes
> R12/R13 golden repairs to Codex. This file follows the router: **`solution/*` is Claude; the
> golden's mirror inside `tests/config.json` is Codex, because provenance scores by path.**
> PEER has not formally retired its earlier ownership rule.

```
HANDOFF R8
  EXIT:      the finding is bound to one artifact, one act-file and one author
  CHECKLIST: n/a — lookup table, not an act (`00-ROUTER.md` §8)
  ARTIFACTS: none — this reference writes nothing
  FACTS:     artifact + act-file + author for each finding you routed
  OPEN:      `AI assessment` and a bare `test-patch` stage are undecoded in both sources
  NEXT:      the act-file named in the row. If the author is `Avocado/human`, record the
             finding and STOP that thread — every other thread continues (`R4` §2).
```

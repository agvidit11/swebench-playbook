# PAIR B — RATING SHEET

Written 2026-09-30, **before any candidate was generated or seen**. Applied identically to every
card. Scores are 0–4. A stage has a *gate*, and the gate returns one of the four A3 §0 verdict
kinds: KILL / AMEND / DOWNGRADE / MEASURE.

Git-committed at the start of the run so the timestamp is checkable.

---

## Verdict kinds — what I am allowed to conclude from what

| kind | the ONLY evidence that licenses it |
|---|---|
| **KILL** | a *fact*: already fixed at base · cause+remedy publicly disclosed (issue/PR/doc/TODO naming the mechanism) · same-seam peer task · licence · the premise is false at HEAD |
| **AMEND** | a *quality defect*: over-pinned, coined-but-unstated, thin surface, step 2 mechanical, contract vague where grader is narrow. → back to Codex with the exact narrowing |
| **DOWNGRADE** | no viable second step, but step 1 stands alone → **ship single-turn** |
| **MEASURE** | fork strength, local band, predicted difficulty, branch count → **build it and find out** |

Rule I bind myself to: **a low score is never by itself a KILL.** Only the fact-list above kills.
Everything else is AMEND or MEASURE. If a whole stage returns no survivor I re-read every verdict
for mis-typing before reporting it.

---

## STAGE 1 — CARD GATE (scored from the card alone, no build)

Seven axes, 0–4 each, max 28.

| # | axis | 0 | 2 | 4 |
|---|---|---|---|---|
| **P1** | **premise reality** — is the gap real at `base_commit`? | inferred from reading code, no citation | `file:line` citation + nearest-presence quote | citation + I or Codex *executed* something at base showing the absence |
| **P2** | **seam novelty** — vs peer corpus AND vs the repo's own shipped task | same seam as an existing task on this repo | different subsystem, same *shape* as a peer elsewhere | different subsystem AND the shape is not in the `A4` hit list |
| **P3** | **branch independence** — how many ways can a competent impl be incomplete | 1 (every arm fails the same assertion) | 2–3, mutant-proven only | ≥3, and ≥1 confirmed against a *cold* implementation |
| **P4** | **contract statability** — can the obligation be written without either hiding a graded token or dictating the algorithm | graded names coined and unstated | pinned + narrow tests, or open + tolerant tests | coined API named with signature, grader provably accepts nothing broader |
| **P5** | **cascade strength** — is step 2 a *different kind of operation* over step 1's artifact | same property at a 2nd site, or a report/view over step 1 | depends on step 1 but could be done mechanically once step 1 exists | cannot be *stated* without step 1, and not mechanical given it |
| **P6** | **grading integrity** — can the suite be satisfied without doing the work | assertion reachable by stub/alias | name-agnostic through an in-base entry point | that, plus an adversarial case for every "only/never/must-not" |
| **P7** | **calibration plausibility** — predicted avocado band per step | "it'll be hard" with no mechanism | a named mechanism for why avocado misses | a named mechanism **and** a reason step 1 is not a warm-up (step-1 difficulty is its own) |

**Gate 1 decision:**

| condition | verdict |
|---|---|
| any fact in the KILL list is true | **KILL** |
| total ≥ 18 **and** P1 ≥ 2 **and** P5 ≥ 3 **and** P7 ≥ 2 | **MEASURE** → build it |
| total ≥ 18 but P5 ≤ 2 | **DOWNGRADE** → single-turn, keep step 1 |
| total 12–17, or any single axis = 0 that is not P1 | **AMEND** → named narrowing back to Codex, one round |
| total < 12 after one AMEND round | retire the card (not a KILL — a *no-further-spend*) |

P1 = 0 is special: it is not AMEND, it is "go measure the premise", which is a Codex task, not a
card rewrite.

---

## STAGE 2 — BUILD GATE (after scaffold + graded tests + solution, before `instruction.md`)

| # | axis | bar |
|---|---|---|
| **B1** | oracle 3/3 local, stable across 3 consecutive runs | binary; below it nothing else is measurable |
| **B2** | `f2p` at base: every `f2p` id fails at `base_commit`; set-diff clean | binary (the baseline-diff gate) |
| **B3** | `p2p` stability: 3 runs at base, zero flake | binary |
| **B4** | branch count against **cold** implementations Codex writes blind to the grader, n≥3 | ≥2 distinct branches hit → forward; 0 → AMEND (widen the obligation, not the tests) |
| **B5** | test.sh materialises graded tests via `git cat-file blob`, fails closed on a smudge filter | binary |
| **B6** | `artifacts` under `[task]` in `task.toml` | binary |
| **B7** | authorship: `tools/authorship-audit.sh` exit 0 — zero Claude writes under `<task>/` | binary, absolute |

Any binary row red → back to Codex. **Never forward.** B4 = 0 is the one AMEND, and the amendment
is always *state one more obligation*, never *add one more assertion* — that is the measured lever.

---

## STAGE 3 — CONTRACT GATE (after MetaCode writes `instruction.md`)

| # | axis | bar |
|---|---|---|
| **C1** | every graded symbol is STATED in the contract or IN-BASE | zero unstated graded tokens |
| **C2** | word count in `clamp(45 × obligations, 250, 600)`, and ≥250 | the measured accepted median is 314; ours have run 154–230 and that is the gap |
| **C3** | **MetaCode scope diff** — diff the *whole* task dir after every dispatch | only `instruction.md` changed, or every other change reviewed and kept deliberately |
| **C4** | contract does not dictate the algorithm, only the observable | reads as obligations, not as a recipe |
| **C5** | no Claude/Codex prose in the file, ever | `authorship-audit.sh` + my own non-authorship |

C3 failing is not a KILL — it is a revert-and-review. C1 failing is AMEND via a *re-dispatch*,
never via my editing.

---

## STAGE 4 — SHIP GATE

| # | axis | bar |
|---|---|---|
| **S1** | `B5` preflight exit 0 | binary |
| **S2** | `B6` review gate (`tools/review-gate.sh`), isolated reviewer subagents | no reviewer returns Reject |
| **S3** | review ledger: zero OPEN findings | binary |
| **S4** | two steps exactly, step 2 a different kind of operation | binary — 0 of 48 accepted tasks have 3+ |
| **S5** | route named (R11 Route 1/2/4) before push | binary |

All five green → push. Any red → the specific act-file, not a general polish round.

---

## What I will NOT do

- I will not kill a card for a low score. Scores route; facts kill.
- I will not write a single byte under any task directory, `audit/` included.
- I will not write or dictate `instruction.md` prose, nor suggest replacement text for it.
- I will not treat a hand-written mutant as a confirmed branch (R11's measured correction).
- I will not polish past the first server verdict — a pushed task that clears the factual vetoes
  beats a local round (`00-ROUTER` §3 "ship early").
- I will not report a count I cannot point at a SHA for.

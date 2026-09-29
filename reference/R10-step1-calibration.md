# R10 — Step 1 is the task

`STATUS: LIVE`, 2026-09-29. Measured across 13 multi-turn tasks with server verdicts — every MT
task in the portfolio that has been graded. This file exists because **multi-turn is the priority
format and step 1 is where it dies.**

## The one number that matters

| | |
|---|---:|
| MT tasks failing validation | **9** |
| of those, blocked by the balance gate | **9 — all of them** |
| of those, the failing step is **step 1** | **8** |
| MT tasks failing provenance, structure, or oracle | **0** |

Everything else in the MT pipeline works. `B1`–`B4` produce structurally sound tasks with clean
oracles and clean provenance, and then step 1 lands outside the band and the task dies. **An MT
task is a step-1 calibration problem wearing a task costume.**

## The distribution is bimodal, and that is the real problem

Step-1 avocado pass rates actually observed:

```
0.0   0.0   0.0        <- too hard / no gradient   (3)
0.2   0.2   0.4        <- IN BAND                  (3)
0.8                    <- over ceiling, grandfathered under pre-9/15  (1)
1.0   1.0   1.0   1.0   1.0   1.0                  <- too easy  (6)
```

Nine of thirteen sit at one of the two extremes. This is not noise around a target — it is a
**binary outcome with a narrow accident in the middle**, and it follows directly from the scoring
mechanism: `fail_to_pass` entries compose as **AND** with binary reward and `min_reward 1.0`
(`reference_swebench_f2p_and_composition`). A step is all-or-nothing per trial. A pass rate of
0.2 does not mean "the model got 20% of it right" — it means **one trial in five cleared the
entire conjunction.** In-band is a *probabilistically borderline* step, not a partially-correct
one. Every intuition about "make it a bit harder" is aiming at a quantity the scorer does not
measure.

## What predicts it: the size of the conjunction

| step-1 `f2p` count | tasks | step-1 outcome |
|---:|---|---|
| **2** | chromem-go, spire-bundle | `1.0`, `1.0` |
| **4** | spire-workload | `1.0` |
| **5** | go-zero-flush, protoc-gen-go-mcp | `1.0`, `1.0` |
| **5** | connect-go, zendesk-biz | `0.2`, `0.0` |
| **8** | django-model-utils, jsonschema | `0.4`, **`0.8` — over ceiling, grandfathered** |
| **10** | franz-go-kadm | `0.0` |
| **13** | sparql-ruby | `0.0` |
| **17** | open62541 | `0.2` |

Read it as two one-directional rules, which is all the data supports:

- **`f2p` ≤ 4 on step 1 has never survived. 3 for 3, all `1.0`.** Below five ANDed conditions a
  competent implementation satisfies all of them. This is a floor, and it is *mechanical* — you
  can count it from `config.json` with no judgement at all, which makes it a better gate than any
  estimate.
- **`f2p` ≥ 8 has come back too easy once in five — CORRECTED 2026-09-29.** The original claim
  here was "never, 5 for 5" and it was wrong: `jsonschema` sits at `f2p=8` with a step-1 rate of
  **`0.8` = 4 of 5, which is over the 3/5 ceiling and therefore too easy.** It is recorded as
  *accepted* only because it passed under the **pre-9/15 rules**; its own gate string says so.
  I counted an accepted-but-grandfathered task as evidence that the floor holds. The honest
  reading is **4 of 5**, and two of the remaining four went to `0.0`. `≥8` is a weak necessary
  condition, not a guarantee.
- **`f2p` = 5 is a coin flip** — two saturated, one landed in band, one went to zero.

So `≥8` buys you out of the failure mode that killed six tasks, and buys you into a different one
that killed two. That trade is worth taking: too-easy is 6 of 9 MT failures and too-hard is 2, and
a too-hard step has a diagnosable cause (`C4`) while a saturated step often has none.

## CALIBRATED AGAINST A WORKING PORTFOLIO — the floor was far too timid

`STATUS: PROVISIONAL`, 2026-09-29. **Do not act on the ~20 target yet.** The counts below are
real and re-measurable; what is unresolved is whether they transfer. The reference portfolio's
tasks are a **different genre** — their instructions are specification documents that name every
class and method signature, where ours are bug reports in a user's voice. A graded-set size that
works for "implement this stated API" may not be reachable for "find and fix this subtle bug",
and our own `B5` R04/R08 axes treat signature-pinning as a failure mode. Resolution needs their
human-review scores, which are not in the repo. Downgraded from LIVE the same day it was written,
before anyone could build on it. Everything above was derived from **our own 13 graded MT tasks, a
portfolio that mostly fails.** A floor fitted to failing data tells you where failure starts, not
where success lives. Measured against `codimango/swe-bench-pro-bekap` (49 MT tasks, ~30-45
accepted — the reference portfolio in the org):

| | ours | **theirs** |
|---|---:|---:|
| MT tasks | 23 | **49** |
| step-1 `f2p` — **median** | **5** | **20** |
| step-1 `f2p` — min | 2 | **7** |
| step-1 `f2p` — max | 17 | 83 |
| step-2 `f2p` — median | 7 | **21** |
| step-1 instruction, words (median) | 161 | **415** |
| shape | 2- and 3-step, mixed with single-turn | **48 of 52 are 2-step MT** |

**Their minimum is above our median.** Thirteen of our twenty-one step-1s sit below the smallest
graded set they have ever shipped. Our step-1 `f2p` distribution is
`[2,2,3,4,4,4,5,5,5,5,5,7,7,8,8,10,11,13,13,16,17]`; theirs starts at 7 and runs to 83.

**Revised target: step-1 `f2p` ≈ 20, and treat 7 as the hard floor, not 8 as the goal.** The
`≥8` rule above is not wrong — nothing at ≥8 came back too easy — it is just the bottom of the
working range being mistaken for the target. Aim at the median of a portfolio that gets accepted,
not at the edge of one that does not.

### The length finding, corrected

Our own data said step-1 instruction length carries no signal, and *within our range* it does not
— but our range is the problem. Their median step 1 is **415 words to our 161**, 2.6×.

These are the same fact, not two: **an assertion needs a contract sentence behind it (`B3` §①b),
so twenty graded conditions cannot be supported by a 160-word contract.** Our instructions are
short because they grade almost nothing. Length follows from the size of the conjunction.

This also resolves the tension with de-scaffolding. De-scaffolding removes **hand-holding** — the
how-to, the recipe, the implementation shape. It does not remove **requirements**. A 415-word
contract that states twenty obligations and no method is not scaffolded; a 200-word one that
walks the model through the fix is. Cutting words without asking which kind you are cutting is
how a task ends up at `f2p` 5 with a 161-word contract and a `1.0` band.

## The floor is STEP-1 ONLY. It does not transfer.

`STATUS: LIVE`, 2026-09-29 — established the same day the floor was, by testing it instead of
assuming it. **Step-2 `f2p` count carries no signal whatsoever:**

| step-2 outcome | step-2 `f2p` counts |
|---|---|
| in band | 7, 30, 9 |
| too easy | 4, 11, 5, 6, **8** |
| too hard | 7 |

`7` appears in both *in band* and *too hard*. `11` is too easy while `7` is in band. The bolded
`8` is `connect-go`'s step 2 — **it satisfies the step-1 floor exactly and came back `1.0`.** Had
this file shipped with "f2p ≥ 8" as a whole-task rule, it would have blessed the step that is
currently failing.

The mechanism is seeding: step 2 does not run against a fresh cohort, it runs against **the
snapshots that already passed step 1** (`reference_swebench_mt_step_seeding`). Its population is
pre-filtered to winners, so its own graded-set size is not what sets its difficulty. Count step 2
if you like — it tells you nothing about its band.

### What step 2's band does track: step 1's

| step 1 | step 2 | task |
|---|---|---|
| in band | in band | django `0.4→0.2`, open62541 `0.2→0.4`, jsonschema `0.8→0.4` |
| in band | **too easy** | connect-go `0.2→1.0` |
| `1.0` | `1.0` / `0.8` | chromem-go, spire-bundle, spire-workload, go-zero-flush |
| `1.0` | `0.0` | protoc-gen-go-mcp |

They agree in **7 of 9**. Step 1 saturating and step 2 saturating is mostly one fact about the
task, not two.

**Do not over-read this into an intervention.** This is observational — hard tasks are hard at
both steps. There is a *separate*, measured, interventional result pointing the other way:
tightening step 1 homogenises the snapshots step 2 inherits and can push step 2 **toward** `5/5`
(`reference_swebench_mt_step_seeding`). Both hold. What follows is that step 1 is the highest-
leverage place to work, **not** that fixing step 1 fixes step 2 — after any step-1 change,
step 2's band is unverified until re-measured.

## What does NOT predict it — stop reaching for this one

**Step-1 instruction length is uncorrelated.** Word counts by outcome:

| outcome | step-1 words |
|---|---|
| in band | 230, 154, 206 |
| too easy | 232, 143, 220, 92, 209, 322 |
| too hard | 228, 110 |

Complete overlap. The shortest step 1 in the portfolio (92 words, `protoc-gen-go-mcp`) came back
`1.0`; a 154-word one landed in band; a 322-word one saturated.

This narrows a rule we have been over-applying. De-scaffolding **did** move one step from `1.0` to
`0.4` (`reference_swebench_what_moved_calibration`) — but that was a **623 → 217 word** cut, a
2.9× reduction. Nothing in this sample varies by more than 3.5× end to end, and within that range
length carries no signal. **De-scaffolding is a lever for grossly over-scaffolded prose, not a
calibration dial.** Trimming a 230-word step 1 to 180 is not a calibration change; it is editing.

## What to do, in order

1. **Count step 1's `f2p` before anything else.** ≤4 and the task is already dead — do not
   proceed to `B4`, do not push, widen the graded set first. Now enforced at `B5` §6 line `6a2`.
2. **Widen by adding independent conditions, not more tests of the same condition.** The count is
   a proxy for branch count (`B3` §④) and the proxy breaks the moment you pad it. Eight assertions
   on one behaviour is one branch and it will still read `1.0`.
3. **Do not chase `f2p` upward past ~17 without a reason.** The two `0.0` tasks sat at 10 and 13.
   There is no evidence that more is monotonically better and some that it is not.
4. **The last step is never exempt, and the single-1.0 exemption needs 3+ declared steps**
   (`00-ROUTER.md` §252). A 2-step task must land *both* steps. Seven of the nine MT failures are
   2-step — not because 2-step is wrong, but because it has no slack.

## What the accepted tasks actually prove — and it is less than three

`STATUS: LIVE`, 2026-09-29. Per-task review of all three accepted MT tasks:

| task | why it was accepted | reproducible? |
|---|---|---|
| `open62541` | an **observable ownership/lifetime fork** — lent-and-released vs materialized-then-used — produced real outcome variance where **four other candidate forks did not** | **yes** — `R6` §P3 + `A3` GATE 4, and the rejected alternatives prove the probe ran |
| `django-model-utils` | **unknown.** Bands look deliberate (`0.4|0.2`) but without trial-level failures we cannot tell discrimination from sampling luck | no |
| `jsonschema` | **grandfathered.** Step 1 at `4/5` is over today's ceiling; accepted under pre-9/15 rules | **no — it would fail today** |

**We have exactly one multi-turn success we can explain and repeat.** That is the honest state,
and it should change what we weight: the **outcome-variance probe** (`A3` GATE 4, `R6` §P3) is
the one mechanism with a clean causal record — it moved `open62541` from `5/5` into band and it
rejected four forks that would not have. Counting `f2p` is a proxy for the same underlying
thing and a weaker one. **Prefer the probe; use the count as a cheap pre-filter.**

Do not cite `review=accepted` as evidence a shape satisfies today's gate without reading the
gate string for `pre-9/15 rules`.

## The live prediction this makes

`kustomize-localize-source-fidelity` has **`f2p` = 3 on step 1** (`1_preserve_unknown_fields`) and
is currently `pending`. This file predicts it returns **step 1 too easy at or near `1.0`**. If it
comes back in band, the ≤4 floor is wrong and this section is the evidence that says so — record
the result here either way. A rule that cannot be embarrassed is not a rule.

## CHECKLIST

```
[ ] 1. Step 1 f2p counted from config.json, not estimated
       proof: the count
[ ] 2. >=8, or a written reason why this step is the exception
       proof: the number, or the reason
[ ] 3. The count is independent CONDITIONS, not repeated assertions on one
       proof: one line per condition naming what it alone can catch (B3 §4)
[ ] 4. Step 2+ counted for the record, with NO floor applied — the count does not
       predict their band; their seeds do. Last step still never exempt.
       proof: the per-step counts, and the step-1 band they inherit from
[ ] 5. Declared step count checked against the exemption rule (3+ buys one)
       proof: task.toml [[steps]] length
```

## HANDOFF

```
EXIT:       <per-step f2p counts, and whether step 1 clears the floor>
CHECKLIST:  <5 lines above with proofs>
ARTIFACTS:  the per-step counts; the branch-condition list for step 1
FACTS:      <declared step count; which steps are exemption-eligible>
RUNG:       <L0-L3>
UNVERIFIED: <any step whose branch count is estimated rather than mutant-proven>
OPEN:       <steps below the floor and the plan to widen them>
NEXT:       B5 §6 — 6a2 blocks on this
```

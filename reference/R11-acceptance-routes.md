# R11 — Every way a task has actually been accepted

`STATUS: LIVE`, 2026-09-30. Built from all 8 of our accepted tasks and 40 accepted peer tasks
(peer status is readable — `codimango task show <name>` works on other authors' tasks; only
`task list` narrows to you).

This is a record of **what actually got accepted and why**, not a theory of what should. Where
the mechanism is unknown, it says so — a success we cannot explain is not a route.

## The scoreboard

| | tasks | accepted | rate |
|---|---:|---:|---:|
| ours | 48 | 8 | **17%** |
| reference portfolio | 52 | 40 | **77%** |

Theirs ran ~1.7 accepted/day through September, sustained. Same inventory size, four times the
conversion. **The gap is conversion, not throughput** — we are not out-worked, we are out-landed.

## Route 1 — build-then-use, with an observable fork `CONFIRMED`

**`open62541-numericrange-canonical-form-composition`.** The only accepted task whose mechanism
we can name and repeat.

- shape: `1_canonical_print → 2_range_difference` — build a canonical form, then difference two
- the fork: **lent-and-released vs materialised-then-used** — an ownership/lifetime contract
  that produced real outcome variance where **four other candidate forks did not**
- coined API named outright, full C signature in a fenced block in the contract
- `f2p` 17 / 30 · avocado `0.2|0.4`
- it moved from `5/5` into band *because of the fork*, and the four rejected alternatives are
  the evidence that the probe was doing work

**How to repeat it:** `A3` GATE 4 outcome-variance probe + `R6` §P3. Find a property where two
correct-looking implementations diverge observably — lifetime, ownership, laziness, ordering —
not one where they diverge in how they *report* a failure. (Error-representation-only divergence
is `A3`'s retirement condition; a full run died on it, 20 implementations, zero mechanism
variance.)

## Route 2 — build-then-use, with several proven discriminators `CONFIRMED`

**`django-model-utils-fieldtracker-related-snapshot`.**

- shape: `1_related_snapshot → 2_partial_invalidation` — build a snapshot, then invalidate part
- coined API named with a literal example: `FieldTracker(related=['author'])`
- `f2p` 8 / 7 · avocado `0.4|0.2`
- the commit that mattered: *"step 2 gains **four verified discriminators**, and fixes a real
  oracle non-termination bug"*

**How to repeat it:** four discriminators, each *verified* — one mutant per branch, rejected by
that entry alone. Note the counts: `f2p` 8 and 7, not 20. **Branch count carried this, not test
count.**

## Route 3 — grandfathered `NOT REPEATABLE`

**`jsonschema-schema-subsumption-checker`.** Its own gate string says *"Passed under the pre-9/15
rules"* and its step 1 is `4/5`, over today's ceiling. It would fail if pushed now.

Recorded so nobody cites it as evidence a shape works. **Before treating any accepted task as a
model, read its gate string for `pre-9/15`.**

## Route 4 — analogue transfer at volume `CONFIRMED, THEIRS`

38 of the 40 accepted peer tasks. The paired names give it away — `sql2o-ktorm`,
`nanodbc-piccolo`, `requests-cache-gofr-ref`: a **source task** whose engineering pattern is
transferred to a **target repo**.

- a skill searches the corpus for tasks whose *engineering shape* transfers
- a human picks from a ranked table
- the authoring model selects the feature **blind to the reference**, then sees the reference
  only as a size/specificity calibrator, then writes the instruction
- the reference supplies **pattern and size, never behaviour**

**What to take:** the search (`A4`) and the size calibration. **What not to take:** their
novelty tool excludes their own repo by default, which is how 52 tasks became 25 upstream repos
in one domain. Ours must include our own repo first.

## What every accepted task has in common

| property | evidence |
|---|---|
| ~~exactly 2 steps~~ **2 or 3 steps** | **FALSIFIED 2026-10-01**: kustomize is 3-step and accepted. 3 steps buys the single-1.0 exemption for one NON-final step. The last step must carry a real discriminator |
| **step 2 is a different KIND of operation** | invalidate / decide / difference — never the same property at a second site, never a reporting layer |
| **coined API named in the contract** | 2 of 3 ours verbatim; their standing policy |
| oracle 3/3, structural clean | universal — necessary, never sufficient |

**Profile to aim at**, from 40 accepted peer tasks: step-1 `f2p` median **19** (range 4–57),
step-2 median **23**, step-1 instruction median **314 words**. Ours sit at `f2p` 2–5 on the
failing ones and 154–230 words. Both gaps point the same way.

**But do not hit the number mechanically.** `f2p` is a proxy and pads trivially — `sparql-ruby`
has 13 graded tests and a branch count of **1**, every arm failing the identical assertion.
Count independent ways a competent implementation can be incomplete, then prove each with a
mutant.

> ### A HAND-WRITTEN MUTANT PROVES A BRANCH EXISTS. IT DOES NOT PROVE ANYONE FALLS INTO IT.
>
> `STATUS: LIVE`, measured 2026-09-30 on `authelia/authelia`. A card carried **nine** branches,
> each with a hand-written mutant that only that branch's entry rejected — the discipline this
> section asks for, done properly. Against **five cold implementations of the same contract the
> real branch count was 0**: all five passed every assertion, three separate times, across
> three different contracts over the same package.
>
> A mutant you write samples the space of *wrong programs*. The branch count that decides the
> band samples the space of *programs a competent solver actually writes*, and those two spaces
> barely overlap once the contract is stated — the solver population clusters hard.
>
> So the mutant discipline stays (it is still what stops `f2p` padding), with one addition:
> **a branch is only confirmed when a real cold implementation fails it.** That is `A3`
> GATE 4's n=5, and it is cheap — the implementations are the same artefacts GATE 4 already
> produces. Grade your branch list against them before you believe the count. Same lesson as
> `C6`'s replay rule and `A2` §3b0's transcription finding, moved earlier: measure against real
> implementations, never against variants you authored.

## What was CHANGED to make ours land

From the commit logs of the three accepted MT tasks — four moves recur, and none is "tune the
number":

1. **add verified discriminators** — *"four verified discriminators"*, *"replace step 2's
   discriminator"*, *"discriminates via a lazy-vs-materialised timing contract"*
2. **hunt false negatives before believing "too hard"** — *"fix step-1 false negatives behind
   the 'too hard' verdict"*. jsonschema's *too hard* was wrong tests, not hard requirements
3. **de-recipe and de-scaffold** — *"state the problem, not the answer"*
4. **unpin** — *"unpin residual counts"*

## What the accepted peer portfolio does that our rules forbid

`STATUS: LIVE`, 2026-09-30. Measured across their 40 accepted tasks. Every row is a practice
one of our rules rejects, in a portfolio accepted at 77%.

| they do | our rule said |
|---|---|
| **33 of 40 instructions exceed 350 words** | we treat length as a calibration risk and ship 154–230 |
| **57 use bullets, 47 use multiple headings** | our form guidance pushes unstructured prose |
| **exact API signatures and coined record fields** | `A2` §6 REJECT, `A3` GATE 0 "almost never" — both now withdrawn |
| **15 contain fenced worked examples** | treated as giving the answer away |
| **contracts of 29, 35 and 14 words** | our floor rejects a short contract outright |
| **a sub-20-line second step** (Dominate) | `A2` §6 auto-rejects "fix under ~20 lines" |
| **7 accepted steps have `p2p` = 1** | we read thin `p2p` as a reward-hacking signal |
| **20 of 40 are a second or later task on the same upstream repo** | our dedup instinct treats a mined repo as spent |

That last row is the one to sit with. **Half their accepted output comes from repos they had
already used.** We treat a repo as exhausted after one task and go looking for a new one —
which is most of why three runs spent themselves on repo screening and produced nothing.
Re-mining a repo at a *different seam* is not a collision; `A4`'s `COLLIDES` row was narrowed
to same-seam for exactly this reason.

**None of these is a licence to copy them.** They are evidence that the specific thing our rule
forbids is not what gets a task rejected.

## How we make it work

1. **2 or 3 steps — the last step must be in band.** ~~Never three~~ was falsified by kustomize (3-step, accepted). One non-final step may be at 1.0 under the exemption.
2. **build-then-use only.** Ask *what representation does this codebase lack* before asking what
   is broken. The other two merge shapes are where our failures live.
3. **Coin the API and name it.** Not a veto — an obligation (`A3` GATE 0 banner).
4. **Prove branches with mutants** before pushing, not `f2p` counts.
5. **Never trust a "too hard"** until every failing trajectory is classified (`B7` §1–2).
6. **Run the reviewers yourself** (`B6`) — the server's cannot see an unpushed tree.
7. **Search the whole corpus first** (`A4`), our own repo included.

## CHECKLIST

```
[ ] 1. Which route is this task taking? Named, before building
       proof: the route number and why it fits
[ ] 2. Two steps, and step 2 is a different KIND of operation from step 1
       proof: could step 2 be stated to someone who has not seen step 1? (must be NO)
[ ] 3. Step 2 is not the same property at a second site, nor a view over step 1
       proof: the one-line reason it is neither
[ ] 4. Branch list with one mutant each, not an f2p count
       proof: the mutants and what each alone rejects
[ ] 5. Any accepted task cited as a model checked for `pre-9/15` grandfathering
       proof: its gate string
```

## HANDOFF

```
EXIT:       <route taken; the two steps named>
CHECKLIST:  <5 lines above with proofs>
ARTIFACTS:  the branch/mutant table
FACTS:      <step-1 f2p and words against the 19 / 314 medians>
RUNG:       <L0-L3>
UNVERIFIED: <anything asserted about why this shape will land>
OPEN:       <where this task departs from the route and why>
NEXT:       A3 gates it
```

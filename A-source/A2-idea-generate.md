# A2 — IDEA GENERATE

| | |
|---|---|
| **Owner** | MetaCode (Avocado). Codex may run the wide survey; **Claude never generates ideas or surfaces** |
| **Input** | one screened repo **+ its `HANDOFF A1`** (clone path, HEAD sha, LOC, subsystem count, the existing entry point that makes a name-free assertion possible) |
| **Output** | candidate cards — dispatch target **≥8**, scaled to the repo per §2 |
| **Exit** | cards written, **each axis-composed (§1) and carrying the self-audit (§7)**. The exit is the quality of the cards, not their count |

Nothing here is verified. Every card is a claim; `A3-idea-gate.md` measures them. Do not run gates
here — cards that are pre-filtered by their own author lose the weak-fork surfaces that merge
usefully into a cascade later.

**Provenance — read `→ 00-ROUTER.md` §5 before writing anything.** This act's owner is Avocado
(MetaCode), which *is* an authorised author for contract prose. **Anyone else running any part of
A2 — Claude, Codex, any 3P model — cannot write `instruction.md` or `steps/*/instruction.md`, and
cannot supply prose for someone else to paste there.** For those runners, cards **stop** at
observable contracts plus the grader API surface, and the `Interface Contract` table is the
deliverable in place of prose. The instruction itself is written in `B2`, by its own owner.
`STATUS: LIVE`

## 1. Stage 0 — compose the lens before surveying

A task is not found by staring at a repo. It is **composed** from three independent choices, and a
strong candidate has one from each layer. `STATUS: LIVE`

| Layer | Library | Question it answers |
|---|---|---|
| **C — search axis** | `→ reference/R5-search-axes.md` (18 axes + AXIS 19) | *How do I look at this repo?* |
| **A — fork shape** | `→ reference/R6-fork-patterns.md` (P1–P6) | *What shape of divergence am I building?* |
| **B — technique** | `→ reference/R7-algo-catalogue.md` — **QUARANTINED**, do not source from it | *What makes it genuinely hard?* |

Worked composition:

> **C1 late-bound unknowns** × **P6 revert-and-redo** × *(B layer omitted — quarantined)* → step 1
> parses unresolved references and resolves eagerly against a single registry; step 2 adds a
> concurrent-reconfiguration requirement that makes eager single-registry resolution untenable,
> forcing snapshot-consistent resolution. Step 2 must rewrite step 1's files, so the file set is
> pinned.

Composing beats surveying: one grep per layer, and it inherits a grading shape that already calibrated. A blind survey costs an agent-hour and averaged **~1 task per hitting repo** (8 repos → ~86 surfaces → ~20 merged candidates → **4 buildable**).

**Self-collision is the binding constraint on reuse.** The same A-shape in the same subsystem across two repos IS a peer collision — our own jCasbin-vs-casbin rule turned on us. A-shapes self-collide after **~3 instantiations** (P1 is already at 3 and closed). Vary the *domain*, not just the repo, and log every instantiation in `ledger/RUNS.md`.

**Priors are UNPROBED until measured in the target language.** The axis library's "why models get it wrong" fields are assertions: axis 3 claims models "overwhelmingly reach for whole-document pretty-printing" and measured **0 of 10** pretty-printing on casbin — yet axis 3 still produced object-rs's single best candidate (30/35). Use the axis; distrust its stated reason. Priors also invert by language: Rust returned **3/3** `Arc::make_mut` + path-copying unprompted, Ruby **10/10** wrapped state in an object with a lifecycle. `STATUS: LIVE`

## 2. How many cards — derive it, never pick a number

`STATUS: LIVE`. A fixed count makes the model pad a thin repo and truncate a rich one.

**Step 1 — surfaces**, sized from the `A1` HANDOFF (do not re-measure):

| Non-test LOC | Ask for | Cross-check |
|---|---|---|
| < 15k | 6–8 surfaces | roughly **2–3 surfaces per major subsystem**. If LOC and subsystem count disagree badly, **trust the subsystem count** — 200k LOC in three packages has less usable surface than the LOC suggests |
| 15k – 60k | 10–12 | |
| 60k – 150k | **15–20** | |
| > 150k | 20–25, or split the ask by subsystem | |

**Step 2 — cards.** Expect **15–20 surfaces to collapse to 2–4 real candidates**; that ratio is the point, not a loss. So the ≥8 dispatch target is reachable only on a 60k+ LOC repo with many subsystems, and only by running the survey in subsystem passes. **On a smaller repo, report the real number and the derivation.** Zero is a valid and expected outcome, and a round that discards every premise with quoted evidence is a *successful* round. **Never backfill** — both source pipelines agree on this and both were burned by ignoring it.

A *surface* at survey time is: an invariant or behaviour area, the files it lives in, its candidate fork, rough net-line size, and whether asserting it needs real network / wall-clock / concurrency. It is **not** a task — cheap to produce, cheap to discard. Do not filter weak forks at survey time; label them and keep them.

## 3. What goes in the survey ask

1. **Drive it from the composed lens.** Name the C-axis and the A-shape in the prompt. A lens-driven
   survey returns half-validated candidates; a blank-page survey returns existing-gap bugs, our worst
   axis. Still ask for some **unlensed surfaces as a control**, so a bad lens choice does not
   silently cost the repo.
2. **Grep the repo's own admissions FIRST**, before proposing anything:
   `TODO | FIXME | NotImplementedError | "not supported" | "unsupported"` in each target subsystem.
   **An in-code admission is the strongest premise receipt there is.** The best card of a PEER
   cohort — the only new one to reach Agentic `GOOD` on its first review — rested on two admissions
   in the library's own source: a guard comment saying a case "is not allowed for now", and a TODO
   conceding the interplay was unresolved. Cards whose premises were *inferred* from reading code
   struggled. Re-verify the admission against current HEAD; comments get fixed. `STATUS: LIVE (PEER)`
3. **Put the hollow-premise question INSIDE the prompt** — the single cheapest fix found:
   > State what HEAD does TODAY for this behaviour, with a `file.ext:line` citation. Then state
   > whether the behaviour I am describing is already fully implemented there. If it is, say so and
   > keep the surface in the list anyway.

   Demand the citation, not a yes/no. Graphiti got **6 of 6** citations accurate; go-zero returned
   **zero hollow premises across 18 surfaces**, because it forced the merge stage to build from what
   is *absent around* existing behaviour. Compare jackson (**8 of 20** hollow) and bc-java (top
   candidate fully shipped). This shifts work left; it does **not** replace `A3`'s verification.
4. **Demand shape diversity.** Left alone an ideating model returns almost entirely existing-gap bug
   surfaces — measured **~85%** `semantic_bugs` + `expose_interface` across 38 tasks (17 and 15).
   Require: at least a third net-new capability, and at least two **revert-and-redo** shapes.
5. **Then merge surfaces into tasks.** Most good 2–3 step cascades are two or three related surfaces
   combined, not one idea with a second step bolted on. Three merge shapes that work:
   build-then-use (introduce the representation → consume it in a decision), narrow-then-widen
   (correct one site → extend the invariant across call sites), observe-then-enforce (expose the
   state → act on it).

**Gradient recipes, ranked by evidence** — bias the ask toward the top of this list. `STATUS: LIVE (PEER)`

| # | Recipe | Evidence |
|---|---|---|
| 1 | **Cross-cutting step 2** — transactional rollback, an authorization boundary over an existing model, an external stateful dependency | *autolab 52%, devise 68%* |
| 2 | **Conflicting requirements inside one step** — two constraints that pull against each other (snapshot synchronously but shed asynchronously; emit notifications but don't overflow the queue you're draining). **The dilemma is the difficulty** | — |
| 3 | **Failure-injection contracts** — "if X fails mid-operation, everything rolls back" | **the strongest multi-model discriminator in the whole set**; autolab's step 2 is the only one where all three models land partial |
| 4 | **Idiomatic traps** — the upstream-idiomatic code is subtly wrong for your requirement | durable, but tends to catch only one model |
| 5 | **Foundation step 1** — step 1 introduces a model or abstraction rather than a transformation | *maglev 61%, 3 models partial* |

**Tooling — all of these fail with exit 0. Always check output size; ~200 bytes + exit 0 is a
banner, not an answer.** `STATUS: LIVE`

```bash
codex exec -s read-only --skip-git-repo-check -C <clone> \
  --add-dir /tmp/<repo>-run -o /tmp/<repo>-run/survey.md \
  "Read /tmp/<repo>-run/survey.txt and follow it." < /dev/null

~/.claude/skills/swebench-mt/mc.sh /tmp/<repo>-run/survey.txt <clone> /tmp/<repo>-run/survey.out
```

`mc.sh` is mandatory. A hand-rolled `script -qec` line breaks two ways: a missing TTY returns a
192-byte banner at exit 0 (it bit three dispatches before the cause was found), and embedding
`"$(cat prompt)"` lets any apostrophe terminate the quoting — **measured best case, the apostrophes
are silently deleted and the model receives a corrupted prompt, exit 0**; worst case the shell
executes prompt fragments (one agent got 2.5 KB of `command not found`). Keep Codex's inline prompt
~2 KB with the payload in a file: a 46 KB prompt returned only its opening plan. Give MetaCode 1700s
via the backgrounded pty wrapper; the Bash tool caps at 600s.

## 4. Card contents — every field is mandatory

| Field | Requirement |
|---|---|
| **Composition** | the C-axis and A-shape it instantiates, named |
| **Step 1 / Step 2 requirements** | plus **one compositional invariant per step**, and **the tension** — the two things that conflict — in one sentence |
| **HEAD citation** | `file.ext:line` for what HEAD does today, and the **nearest presence**: quote verbatim the closest thing that exists to the claimed absence, and state which case it fails to cover. You cannot cite an absence |
| **Motivating caller** | who needs this and why now — a concrete caller, scale requirement, compatibility obligation or operational constraint. Abstract "nice API" additions are discounted on realism, which is a scored axis. Not a rejection, a rewrite |
| **Interface Contract** | table of every symbol the graded tests will touch that is not already in the base repo: `Symbol / Kind / Shape / Reachability (STATED or IN-BASE) / Alternatives (PINNED or accepted synonyms)`. **The Alternatives column is mandatory** — R08 permits *pinned spec + narrow tests* or *open spec + tolerant tests*, never a vague spec with narrow tests. A symbol that is neither STATED nor IN-BASE is an R01/R02 failure before any code exists |
| **Observable Schema** | required when the deliverable is a collection of records. Six levels, each pinned or explicitly opened — see §5 |
| **Named wrong-shape per contract** | **plus one sentence on why a capable model would plausibly produce it** — which shipped primitive, which adjacent idiom, which reading of the prose leads there. If you cannot write that sentence it is a strawman and will not discriminate: measured, a hardening round added three cases, a purpose-built mutant failed all three, and the strongest arm stayed at **1.0** |
| **Determinism seam [R09]** | if the premise involves time, concurrency, ordering or retries, name the **injection point** — a clock, a scheduler, a barrier. The `GOOD` exemplar was praised for an injectable clock defaulting to the monotonic clock and `Queue` handoffs instead of `sleep`; the task that flaked on **~30% of random seeds** had no such seam |
| **Predicted per-arm rate, per step** | step 1: avocado ≤ 3/5 **and opus ≥ 3/5, gpt ≥ 3/5**; step 2: avocado ≤ 3/5, others mixed. Step-2 effective n is bounded by step-1 successes — one task moved opus 0.6 → 0.2 on a **byte-identical** config, leaving exactly **one** step-2 sample, which passed, and the gate reported *"step 2 has no gradient"*. Nothing was wrong with step 2. If step 1 is the harder step, **you have the steps backwards for measurement purposes**. Answer: *what stops avocado passing step 1 outright?* — two tasks saturated step 1 at **5/5** |
| **Step-1 guard cases owned by step 2** | for each step-1 invariant, the **step-2 `fail_to_pass` case** that would fail if it regressed. Never step 1's `fail_to_pass` IDs in step 2's `pass_to_pass`. The finding *"step 2 does not require step 1's fail-to-pass tests to keep passing"* hit **three tasks** in one cohort, a full repair round each. Any card whose step 2 says *continues* / *restates* / *the same guarantees hold* must ship this field in the same breath |
| **Inter-step file overlap** | which files each step touches, and whether step 2 is *incremental on step 1* or *cumulative from base*. **Two tasks broke on patch composition because both steps rewrote the same file from the same base.** Heavy overlap is a yellow flag, not a disqualifier — it tells the scaffolder step 2 must be a delta. Barely-overlapping file sets are a legitimate tiebreak |
| **Size estimate** | files, ~lines, primitives reused. Target **80–150 net lines across 2–4 files** |
| **Rubric self-audit** | §7 |

## 5. Observable Schema — six levels, when the deliverable is records

The Interface Contract alone is not enough: its `Shape` column gets read as "the shape of this
field" and the **container** goes unstated — the single most expensive omission measured.
`STATUS: LIVE (PEER)`

| Level | What the card must answer | Cost when unstated |
|---|---|---|
| **Container** | Array, Hash, or an object exposing `#entries`? Indexable by position? | tests did `census.fetch(0)`; a custom collection failed **8 of 9 tests** with `undefined method 'fetch'` while every field name was already correct |
| **Element** | Hash, Struct, or an object with readers? | *"directly calls `key?` on ledger entries, so an otherwise valid object-based entry can be rejected"* |
| **Field names** | exact accessor per field | `revoke_outcome` vs reusing the existing `outcome` |
| **Value domain** | the legal values **and their spelling** | `:created` vs Thor-native `:create`; `:empty_directory` vs `:directory` |
| **Config option names** | the exact option key the tests set | a subtask omitted `correction_conflict_threshold` |
| **Lifetime / persistence scope** | what survives an object boundary, a process, a restart | *"the requirement that per-file counters persist across separate `Team` instances"* — **not a name at all**, so a card author checking "did I name every symbol?" answers yes and still fails |
| **Test-only lifecycle hooks** | anything the suite needs to isolate itself | a reset hook *"recoverable only from the hidden tests"*. If the card cannot describe the task without one, that is a design smell to fix at the card stage, not a token to pin |

**The "two defensible answers" test [R01/R03].** For every field name and value: *could a competent
domain expert reading the prose reasonably choose a different symbol?* If yes, it must be pinned.
The signature in the wild is **two independent models converging on the same answer that disagrees
with gold** — and when that happens the gold is usually the outlier. Real case: the spec said "which
handler absorbed it", the tests required the absorbing *method* name (`:swallow_error`), and two
independent attempts both recorded the *callback option* name (`:error_on_all_events`).

**Every "only X" / "never Y" / "must not touch Z" needs its adversarial case written on the card**
[R06/R12]. A spec said *"only manifest-marked-created paths are destroyed"* and there was neither a
test for user content under a generated directory nor a golden that survived it, because the golden
delegated to a library call that recursed. Same for *durable* / *cross-process* / *atomic* /
*idempotent*: name **the test that actually crosses the boundary**, or the reviewer finds *"claims
durable manifest behavior, but the required tests only check that some metadata file exists."*

## 6. Auto-rejects at ideation

Reject outright, no card written:

- step 1 = split / extract / move a large class — punishing but shallow
- step 1 = recall-only. bc-java's best surviving step 1 was
  `org.apache.commons.io.output.TeeOutputStream.close()` verbatim: passes every gate, teaches
  nothing, and the cascade rested on it
- step 1 whose requirements include *"behaviour and returns are unchanged"* — that is recording what
  the library already does. **A gate, not a step**; no competent model fails it
- step 2 = "now use what you built in step 1", or step 2 extends the same function step 1 wrote —
  that pattern accounts for the four worst cascades
- step 2 computable from data the codebase already reaches at step 2's own seam. State in one
  sentence what step 2 **cannot** compute without step 1's artifact; no answer → discard (killed
  cards 60 and 62)
- difficulty that comes from the volume of mechanical edits
- any step whose contract you cannot state as observable behaviour
- **process-global or class-level mutable state as the natural implementation.** One task's
  path-keyed class hashes failed **three axes at once**: ~30% seed flakiness (R09), *"Functionally
  Correct but Poor Engineering"*, and an unstated cross-instance persistence requirement (R01) — and
  it forced a test-only reset hook into production code. If the card cannot describe the state as
  belonging to an instance the caller holds, redesign or discard
- **fix under ~20 lines, or composing two shipped functions** [N04 anti-overcorrection]. Verification
  alone selects trivia: absent *and* substantial

### The three-word recall test — verbatim, apply to every premise

> **Three-word recall test** — If you can name the hard part in three words or fewer (LRU eviction,
> singleflight, circuit breaker), the model recalls it from training data. Fail the idea.

Measured: one card self-rated R01 PASS while its step 1 was nameable in two words as "LRU eviction".
Related — for a library implementing a famous spec (semver, CSV, git), claiming a seam is "emergent
interplay" is not evidence. Quote the doc section covering the interplay and show it does **not**
specify the behaviour you target. Card 47 claimed emergence and was dead because the README
documents the interplay verbatim.

### The observability line — where PEER's auto-reject actually bites

PEER auto-rejects *"a premise whose deliverable is an observability surface"* — ledger, census,
manifest, accounting record, audit trail, trace. Measured: **capability 8 for 8 GOOD; invented
observability surfaces 0 for 10**, each needing two to four repair rounds. In an earlier ten-task
cut, six capabilities scored spec_clarity `Good` and Full-Task `GOOD` while four ledger/census/
manifest/accounting tasks all scored `Requires Some Guessing` and `BAD_GRADING_WRONG` — ten for ten,
no exceptions. **You cannot buy your way out with tolerant tests**: three such tasks were repaired
by widening the graded tests only; two moved spec_clarity to `Good` and `tbdReviewStatus` to pass
**and still returned `BAD_GRADING_WRONG`**.

But PEER's own positive exemplar exposes one small **existing** counter (`arrivals`), and OURS treats
*silent per-item failure → expose outcome → enforce policy* as its strongest pattern (independently
rediscovered 3× in one day across 2 languages and 3 domains). Neither source states the line
sharply. **It is this:**

| | Verdict |
|---|---|
| A **newly coined record or schema whose field names become the task** | **REJECT.** Its entire contract is vocabulary you coined, so the spec either enumerates every invented field — and the task becomes transcription, not reasoning — or it does not, and the graded tests assert on names the prose never stated. **There is no third option**, which is why widening never rescues it |
| An observable **effect** — behaviour visibly changes through an entry point that already exists | **FINE** |
| A **minimal existing-vocabulary signal** — one counter, one flag, one field the library already defines | **FINE** |

This is the same rule as `A3`'s namability gate seen from the generation side: the coined schema
fails because its names do not exist at `base_commit` (`→ A3-idea-gate.md §GATE 0`). So run the
**existing-vocabulary test** on every card: write out every noun in the observable contract and mark
each *already in the library* or *coined by you*. If most are coined, the spec cannot reach
spec_clarity `Good` without enumerating them all, and it will land `Requires Some Guessing` — which
predicted `BAD_GRADING_WRONG` on **4 of 4** tasks and never occurred on the **6** that passed. Two
ways out, in order: restate the contract in terms the library already defines, or keep the coined
vocabulary and enumerate every token. When conciseness and spec_clarity pull against each other,
**spec_clarity wins** — over-specification is explicitly advisory, spec_clarity is blocking.

For P1-shaped cards specifically: **grade the enforcement, not the record.** If step 2 is graded on
its return value or a boolean flag it collapses to an inline computation and one-shots — grade a
**cross-cycle** or **per-source** behaviour instead. `STATUS: LIVE`

## 7. The self-audit each card carries

Thirteen Agentic Full-Task Review items are judgeable from a card before any code exists: **R01 R02
R04 R05 R06 R07 R08 R09 R11 N01 N02 N03 N04**. R10, R12, R13 need a build; R03 needs rollouts. List
those four as deferred, naming the stage that will decide each. **Do not claim PASS on an item the
card cannot judge.** One row per item, verdict PASS / FAIL / N-A, one line of evidence pointing at
the card's own content — **a row with no evidence is not an audit**. A card with a self-reported FAIL
is repaired or discarded, never elaborated.

**The all-PASS table is worthless.** Measured across five cards from one round: **all five reported
13 of 13 PASS.** One was then archived on a Tier-0 seam failure, two had a step 1 with no capability
at all, and one self-rated R01 PASS on a two-word "LRU eviction" premise. The table caught **none**
of it; the checklist gates caught all five. Therefore:

- **Every card must record at least one non-PASS row or one named residual risk**, with evidence.
  "This card has no weaknesses" is an unrun audit.
- For each PASS on **R01, R02, R08**, the evidence line must name **the thing that nearly failed it**
  — the token you considered leaving unstated, the alternative implementation you had to widen for.
  A PASS with no tension behind it was not tested.
- Where a rubric is genuinely clean, say *why the risk does not arise here*.

## 8. THE TASK-IDEATION CHECKLIST

Run top to bottom, once per screened repo. Tick each line with the artifact that proves it, or
waive it with a reason.

| # | Step | Proof |
|---|---|---|
| 1 | Read `HANDOFF A1` | LOC, subsystem count, HEAD sha and the named existing entry point copied into your run notes. **Do not re-measure** |
| 2 | Confirm your authorship lane | state the runner. If it is not Avocado/Vidit, declare "contracts only, no prose" for this run (`→ 00-ROUTER.md` §5) |
| 3 | Choose the C-axis and A-shape | named in the run notes, with the `R5` / `R6` entry; check `ledger/RUNS.md` for prior instantiations — **A-shape at 3 already = pick another** |
| 4 | Derive the surface count | the §2 band, the subsystem cross-check, and the number you will ask for, written down before the ask |
| 5 | Grep the repo's own admissions | `TODO\|FIXME\|NotImplementedError\|"not supported"\|"unsupported"` per target subsystem, output saved; re-verify any quoted admission against current HEAD |
| 6 | Write `survey.txt` | contains: the lens, the unlensed control ask, the HEAD-`file:line`-citation requirement verbatim, the shape-diversity clause, the admissions found, and a containment clause |
| 7 | Run the survey | `mc.sh` or `codex exec` per §3 — **check the output byte size**; <600 bytes is a silent failure, re-run |
| 8 | Merge surfaces into candidates | the merge table: every surface mapped to a candidate or marked dropped/parked-single-turn, with the reason |
| 9 | Apply the §6 auto-rejects | one line per rejected premise naming the rule that killed it — including the three-word recall test and the existing-vocabulary test |
| 10 | Write one card per survivor | every §4 field present; §5 Observable Schema present whenever the deliverable is records; continue card numbering from the highest existing card, **never reuse a number** |
| 11 | Self-audit each card | §7 table, 13 card-stage items + 4 deferred, **≥1 non-PASS row or one named residual risk** per card |
| 12 | Confirm the count honestly | cards written vs the ≥8 target, with the derivation. If under, say why; **do not backfill** |
| 13 | Emit the HANDOFF | block below, `CHECKLIST: n of m` filled in |

```
HANDOFF A2
  EXIT:      <N cards written; the derivation of N from LOC/subsystems; every discarded premise with
             the reason and quoted evidence that killed it>
  CHECKLIST: <n of m ticked; every waived line with its reason>
  ARTIFACTS: <card paths, one file per card, numbered — never reuse a card number>
  FACTS:     repo clone path + HEAD sha; per card — composition (C-axis × A-shape), the HEAD citation
             and nearest-presence quote, the Interface Contract table, the named wrong-shape and why a
             capable model writes it, the determinism seam, predicted per-arm rates, file overlap,
             and the residual risk the self-audit recorded
  OPEN:      every card field that could not be filled, with the reason. Any premise parked as
             single-turn-only. Any card whose observable contract is mostly coined vocabulary.
  NEXT:      A-source/A3-idea-gate.md
```

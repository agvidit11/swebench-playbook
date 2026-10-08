# C3 — Harden a task measured too easy

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
ACT:    C3-harden
OWNER:  Avocado/MetaCode for the contract · Codex for the graded suite · Claude dispatches,
        verifies and pushes
INPUT:  a task whose step gate reads "too easy", "no gradient", or avocado >3/5 on any step
OUTPUT: a proven gradient
EXIT:   the gradient is PROVEN against a replayed real passing trial (→ C6),
        or it is reported UNPROVEN — never assumed
```

**Claude and Codex may not write the contract.** Every contract lever in this file is an
**Avocado (MetaCode) dispatch** or a hand edit by Vidit. Routing prose through a script, a
heredoc, a patch file, or another agent is the same violation, and so is drafting the exact
replacement sentence for someone else to paste. → `00-ROUTER.md` §5.

This act exits through `C-drive/C6-replay-verify.md`. → `00-ROUTER.md` §8b.

---

## When hardening CANNOT work: step 2 is a transcription of step 1

`STATUS: LIVE`, measured 2026-09-24. Before you widen a too-easy step 2, check whether its solver
population is a single implementation wearing five hats.

Step-2 cells fan out from step-1 snapshots. If step 1 passed only once, **all five step-2 cells
descend from that one run**, and if step 2's requirement can be satisfied by re-applying a
predicate step 1's golden already defines, every seed arrives already carrying the answer.

**The check, and it is cheap:** recover the final file contents from each step-2 trajectory and
diff them against each other. Identical implementations means branch count **0** against the real
population, and **no graded set can move the band** — measured, with a controlled A/B in which the
same two branch classes moved step 1 by −0.8 and step 2 by exactly **0**.

**When this is the diagnosis, hardening the grader is the wrong act.** The only lever is a step-2
**contract** change requiring something step 1's solution does not define — and that is
`instruction.md`, which is Avocado's or the human's. Record it `Owner: Avocado/human`, say so
plainly, and do not spend a round widening tests that cannot separate anybody.

Note the trap in the obvious response: tightening step 1 to raise its band makes step-2 seeds
*more* uniform, not less. → `A-source/A2-idea-generate.md` §3b0.

## Update the review ledger before you hand off

Set the disposition on every finding you touched → `C-drive/C2-repair-grading.md`
§Update the review ledger. `B5` blocks the next push on anything left `OPEN`.

## 0. Never harden by making the interface vaguer

The rule itself lives in `B-build/B2-contract.md` (interface never vaguer; approach vaguer is
good). **The hardening-specific consequence is what belongs here:** the source pipeline deleted
the line *"you can make these requirements a bit more vague"* from its own hardening prompt
because that line produced the defect that failed **every task built from the pipeline**. A vague
spec over narrow tests is the one illegal configuration under R08, and the difficulty it creates
is name-guessing, which the review scores as an **N04** failure:

> *"much of the observed difficulty comes from guessing hidden schema names, not only from
> hook-control reasoning. With the ledger API and vocabulary specified, the task would provide
> stronger implementation signal."*

So when you dispatch a hardening brief:

- **Deleting a recipe, an algorithm hint, a worked example or a file pointer is legitimate** and
  improves R04.
- **Deleting an accessor, method, key, enum value, error class or its shape is not hardening** —
  it converts reward into guessing and lands `BAD_GRADING_WRONG`.
- If you genuinely want a symbol unnamed, that is the **open** R08 route and it obligates the
  tests to accept every reasonable alternative. **Say so explicitly in the §5 handoff** — do not
  leave Codex to infer it.

**Do not over-harden either.** R04 is more permissive than it reads: a detailed recipe is
acceptable *if* implementation remains hard — *"if the whole recipe/algorithm is laid out in
detail, then it should be complex enough that the agents are struggling to implement or code it
correctly and pass the tests."* The failure mode to avoid is not "too much detail about what"; it
is "too little detail about the interface, or a recipe for how."

---

## 1. Before you harden anything — four preconditions

1. **Confirm the passes were EARNED.** A band built on `source_diffing`, `verifier_gaming` or
   `pattern_matching` is a leaking task, not an easy one, and hardening it makes a broken task
   harder instead of closing the leak. → `C1` §6, the conditional pass audit. Measured: one task
   read 4/5 and 5/5; after the verifier was hardened against pytest-hook and flexible-equality
   tricks the same task read **2/5 and 2/5** — the first pair was never real.
2. **Confirm the number is not stale or noise.** At n=5, one trial moves the rate by 0.2. Django
   step 1 read `0.4` then `0.8` on byte-identical blobs; franz-go step 2 read `0.8` then `1.0`
   unchanged. **A single 0.8 is a current gate failure but weak redesign evidence** — get a second
   server read before redesigning otherwise sound artifacts, and do not aim at the 0.6/0.8
   boundary. → `reference/R2-signal-integrity.md`.
3. **Confirm the grader is not the thing that is broken.** After any grading fix the difficulty is
   UNMEASURED; recalibrate before hardening. Never tune difficulty on top of a broken grader.
4. **Check `format` in `task.toml` before reading any pass rate.**

> **CONFLICT — UNRESOLVED · does the ≤3/5 ceiling apply to single-turn tasks?**
> - `00-ROUTER.md` §4 criterion 2 states the ceiling format-agnostically: *"Avocado ≤ 3 of 5 per
>   step … never better than 3/5 on any step."*
> - OURS `runbooks/3-harness.md:62–73` records a different single-turn rule, quoting the server
>   verbatim: *"`Passed — avocado not trivial and >=1 agent solved`"* — i.e. **a single-turn task
>   at avocado 4/5 with opus 0/5 and gpt 0/5 PASSES.** The same file records the cost of missing
>   this: *"I applied the MT band to a single-turn task and nearly had an agent add a
>   discriminator to a task that had already passed its balance gate, with two of three models
>   already at 0/5."*
> Multi-turn is not in doubt: **per-step, in-band is 1–3 of 5 on avocado, every step, and the last
> step is never exempt.** Until the single-turn case is re-measured, read the gate's own verbatim
> string before hardening a single-turn task, and do not harden a gate that reports `passed` under
> its own stated rule.

---

## 2. Legitimate hardening levers, strongest first

Owner column is binding. **Avoid adding more enumerated bullets to the contract** — bullets invite
bullet-by-bullet implementation and saturate. One sharper compositional invariant beats three more
requirements.

| # | Lever | Owner | Why it is strong |
|---|---|---|---|
| 1 | **Add a conflicting requirement in the same step** | Avocado | two constraints that pull against each other — the dilemma is the difficulty and it cannot be recalled |
| 2 | **Add a failure-injection contract** — "if X fails mid-operation, everything rolls back" | Avocado | the strongest multi-model discriminator in the set |
| 3 | **Make step 2 reach further back into step 1's design**, so step 1's natural shape no longer suffices | Avocado | creates real cascade dependence instead of a decorative one |
| 4 | **Edge cases that fall out of the existing invariant** — boundary, empty, duplicate, reentrant, ordering | Codex (tests) | already inside the stated contract, so no R01/R02 cost |
| 5 | **Remove a giveaway** — a named file, an implied call order, a worked example that shows the shape rather than the outcome | Avocado | de-scaffolding; see below |
| 6 | **One discriminating behavioural assertion** on a property a successful solver's shortcut violates | Codex (tests) | cheapest and most reversible; requires a probe first |

### On lever 4/6 — the assertion must discriminate, not merely exist

Adding tests along an axis models already satisfy changes nothing: **one task went 2 → 19 f2p and
stayed 15/15.** Create gradient on an axis a plausible *wrong* implementation actually fails.
Prefer cases that defeat hard-coding to the single graded scenario — vary sizes and shapes so
count- or case-based post-processing cannot pass. Push **one assertion at a time** and re-read the
per-step cells; batch only when you can predict the combined effect against every extracted
implementation.

A Codex brief for lever 6 reads:

> Work only on `<task>/<step>`. Do not edit the contract file. First reproduce `<solver shortcut>`
> as an alternative implementation and run the current grader. If it already fails, stop and
> report that this is not a discriminator. If it passes, add the smallest behaviour-level
> assertion that distinguishes `<required property>` from that shortcut. Do not assert private
> helper names or the oracle's implementation. Prove the oracle and at least two independently
> valid implementations pass while the probed shortcut fails. Report the exact test ID and
> results.

### On lever 5 — de-scaffolding is NECESSARY, NOT SUFFICIENT

De-scaffolding is removing the structure that lets a model transcribe a spec instead of reasoning:
bullet lists, numbered requirements, headings, emphasis, worked examples, branch enumerations. The
API contract is untouched — this is **not** "making it vaguer" (§0).

**Measured across 37 steps: every in-band step was under 230 words, and every step over 300 words
or carrying a bullet list was judged too easy or worse.** But franz-go
`1_acl_resource_scope_matching` was **245 words with zero bullets and still returned 1.0**, because
the task had no structural fork. De-scaffold because it is cheap and removes a known cause of
one-shotting — then go find the fork (levers 1–3).

The Avocado dispatch:

> Rewrite only `<step>`'s contract file. Preserve every grader-visible public name, signature,
> error/empty behaviour, dependency on prior steps, and acceptance boundary. Remove worked examples
> that reveal the implementation, collapse case-by-case enumerations into one invariant, and state
> the observed symptom or desired behaviour instead of the algorithm. Do not add file paths, helper
> names, test names, pseudocode, or new requirements. Return a concise contract that a maintainer
> can implement from the repository.

Overshoot risk: removing a required public identifier creates guessing and false negatives.
WebAuthn proved wording can be binary — **when every wording probe is all-pass or all-fail, stop
wordsmithing and move on to a structural lever.**

### Structural levers, when the cheap ones are exhausted

Expanding a step, or adding a genuinely dependent final step, are available and are Avocado
dispatches. Two constraints bound them: **the legacy 1.0 exemption is at most one per task,
requires 3+ declared steps, and never applies to the last step.** Franz-go's `1|1|0.8` proved that
adding a third step does not excuse two easy steps — under the current ceiling even `0.8` must be
tightened. A decorative or 5/5 new step cannot save a task.

---

## 3. Prove the gradient — the exit condition

**A mutant is a floor, not a proof**, and a self-authored variant is circular. The proof is a
replayed real trajectory; where that is impossible, an n=5 cold split plus an explicit **UNPROVEN**
verdict. Protocol, commands, the three required runs and the measured caveats →
`C-drive/C6-replay-verify.md`.

`C3` is not complete until `C6` has returned **PROVEN**, or until the report says **UNPROVEN** in
those words.

---

## 4. Name the mutant the current contract permits (R07)

The review asks whether the task is reward-hackable. At contract-hardening time you cannot change
tests, but you can find the hole and specify it closed.

Write down the plausible-but-wrong implementation that **satisfies the current contract as
written** and would still pass. Harden the contract so that implementation is excluded by the
text, and **record the mutant in the §5 handoff so the grader author can add the probe that
rejects it.**

Two real examples worth pattern-matching:

- A golden that **recursively deleted a directory including user-created files inside it** —
  permitted by a contract that said only "revoke what was created", and the reference solution
  itself did it.
- A solution satisfying the exact tested callbacks while **breaking other lifecycle phases
  entirely**, because the graded set was synthetic fixtures plus new spec files only.

**If you cannot name a mutant the current contract permits, the step is probably not
under-specified** — it may simply be easy, and the fix is a new requirement (§2), not a rewording.

---

## 5. Hardening invalidates downstream work — hand it off explicitly

Changing the contract invalidates work already done: the tests were written against the old text.
Emit a short handoff note listing:

| Item | Why the next act needs it |
|---|---|
| **Every requirement added, changed or removed** | Codex must re-derive the spec-to-test mapping (R02/R06) |
| **Any symbol whose pinned/open status changed** | newly *named* ⇒ narrow tests are now correct; newly *unnamed* ⇒ the tests must accept alternatives (R08) |
| **The mutant from §4** | so the probe that rejects it gets written |
| **Whether the card's Interface Contract needs updating** | it is the record of the pinned surface and must match the revised contract |

A full downstream re-audit after any contract change → `B-build/B2-contract.md`
§contract-change re-audit.

### The tolerance flip — re-audit every widening you are carrying

**STATUS: LIVE.** While the prose is silent, the legal remedy for an unstated behaviour is a
**tolerant test** (open prose + tolerant tests). The moment that behaviour is pinned, **the same
tolerance becomes illegal leniency**: the test now accepts a solution that violates a stated
requirement, which is an **R07/R09** finding instead of the **R08** one you started with.

Measured: a duplicate-call test was widened to accept *either* a silent no-op *or* a raised
already-rolled-back error, because the step text stated neither. The text was then pinned to "a
second time with the same id is a no-op", and the widened test would have passed a raising
implementation that plainly violated it.

So whenever the contract changes, before triggering anything:

1. Diff the contract against the version each tolerance was written for.
2. For every behaviour the new text **pins**, narrow the matching tolerance back **and prove it**:
   the now-illegal variant must score **0** where it previously scored 1.
3. For every behaviour the new text still leaves **open**, keep the tolerance. Narrowing
   everything is the opposite error — in the case above the group id's storage location remained
   unstated, so that half of the widening correctly stayed.
4. Re-grep every token the tests assert on against the new prose and confirm the counts are
   non-zero.

---

## 6. The step-1 measurement floor

**STATUS: LIVE.** Step-2 effective n is **bounded by step-1 successes**. A step-1 arm passing 1 in
5 yields exactly **one** step-2 observation — and the gate will render a verdict on that single
observation.

- **`NA` in a step column is not zero.** It means that model never reached the step, and it says
  nothing about that step's difficulty.
- `"<step>" has no gradient` means avocado never reached the later step *and* every model that did
  passed every attempt. **The later step still fails even though its apparent conditional pass rate
  is perfect.**
- Therefore: **hardening step 1 shrinks the sample you can measure step 2 with.** If step 2 is the
  step you actually need to move, harden step 2 first, or accept that the next cohort will not
  measure it.
- `minimum_steps_for_nonfinal_all_pass_exception = 3`: a two-step task gets **no** saturation
  exemption, and the last step is never exempt regardless of step count.

---

## 7. Two stale-source warnings

- **Do not "restore" step-1 `fail_to_pass` into step-2 `pass_to_pass`.** PEER
  `07-codex-rebuild-solution-and-tests.md:199` lists that as a regression bar; it is **retracted**
  by PEER `05-codex-finish-the-scaffolding.md:110–117`, which states the rule was wrong and
  corrects it. Seeded cells score 0 regardless of their own work and it breaks the step-p2p
  independence check. The correct construction lives in `B-build/B3-grader.md`.
- **Do not convert step patches to satisfy a reviewer complaint about the aggregate.** PEER `07`
  §5's "must stay cumulative-from-base" is likewise retracted by PEER `05` B.1. →
  `reference/R3-landmines.md`.

---

## 8. CHECKLIST

```
[ ]  1. format read from task.toml; the gate's verbatim string read, not a summary    §1
[ ]  2. Passes audited as earned (C1 §6) — no source_diffing/verifier_gaming/pattern  §1
[ ]  3. Second server read obtained, or the reading is not at the 0.6/0.8 boundary    §1
[ ]  4. Grader confirmed sound first; difficulty not tuned on a broken grader         §1
[ ]  5. Lever chosen from the ranked table, with its owner named                      §2
[ ]  6. Contract lever (if any) dispatched to Avocado/Vidit — never Claude/Codex  router §5
[ ]  7. No interface symbol, shape, enum or error class removed from the contract     §0
[ ]  8. No new enumerated bullet list added to the contract                           §2
[ ]  9. Mutant the current contract permits NAMED and recorded                        §4
[ ] 10. ONE assertion at a time pushed, unless the combined effect was predicted      §2
[ ] 11. C6 run: gradient PROVEN | UNPROVEN | DISPROVEN, stated in those words         §3
[ ] 12. Oracle still 1.00 x3 after the change                                         §3
[ ] 13. Handoff note emitted: requirements delta, symbol pin/open changes, mutant     §5
[ ] 14. Every tolerance re-audited against the new contract text, both directions     §5
[ ] 15. Step-1 sample impact considered before hardening a non-final step             §6
[ ] 16. Neither stale-source rule in §7 reintroduced                                  §7
```

---

## HANDOFF

```
HANDOFF C3-harden
  EXIT:      <gradient PROVEN against trial <id>, with the three C6 run results>
             | <EXIT: NOT MET — gradient UNPROVEN, reason>
  CHECKLIST: <n of 16 ticked; every waived line with its reason>
  ARTIFACTS: <paths changed, all under <task>/>; the §5 handoff note; commit SHA
  FACTS:     which lever was used; requirements added/changed/removed; every symbol
             whose pinned/open status changed; the named mutant; the measured split
  OPEN:      any contract change still owed by Avocado/Vidit; tolerances not yet
             re-audited
  NEXT:      C6 (if the replay has not run) | C1 (re-read the new verdict) | C5 | park
```

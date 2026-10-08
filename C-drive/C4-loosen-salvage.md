# C4 — Loosen or salvage a task measured too hard

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
ACT:    C4-loosen-salvage
OWNER:  Codex for the graded suite · Avocado/Vidit for any contract lever ·
        Claude dispatches, verifies and pushes
INPUT:  a task whose step gate reads "too hard" / 0 on every model, or a suspected false negative
OUTPUT: a measured band
EXIT:   the band is MEASURED, not assumed — a real implementation was run against the
        graded suite and the result quoted (→ C6)
```

**Standing instruction: almost every task is salvageable. Abandoning an idea is the WORST
outcome and requires proof, not judgement.** Shifting to a new idea costs the whole of phase A
and B again.

Contract levers in this file are **Avocado (MetaCode) dispatches or hand edits by Vidit** —
never Claude, never Codex, not even to unblock the gate. → `00-ROUTER.md` §5.
This act exits through `C-drive/C6-replay-verify.md`. → `00-ROUTER.md` §8b.

---

## Update the review ledger before you hand off

Set the disposition on every finding you touched → `C-drive/C2-repair-grading.md`
§Update the review ledger. `B5` blocks the next push on anything left `OPEN`.

## 1. Prove it is NOT a false negative before you loosen anything

**STATUS: LIVE. This is rung 1 and it is never skipped.**

Two OURS cases where "0/5 on every model" was not difficulty at all:

- one task had **three independent grader defects**, and only **1 of 4** rollout failures was a
  genuine bug;
- one was **100% `GRADING_FAILURE`** — a change that left the bug **entirely unfixed** still
  scored **6/6**.

A band can also be **unfairly hard** without any grader defect: one PEER task scored **1/5** only
because the modules its contract told the solver to read **were not shipped in the image**; once
they were, it scored **4/5**. Ask what the passing agents could actually see.

And the name case: `webauthn-ruby-assertion-algorithm-policy` reported **0 across
avocado/opus/gpt**. All three trials implemented the feature correctly using the repository's own
`verify_item` pattern and chose reasonable error names (`AlgorithmVerificationError`,
`PublicKeyVerificationError`); the grader required `CredentialAlgorithmVerificationError`, a name
absent from the contract. Once the public contract was named and the unfair pins removed the task
swung to **`1|1`** — **the missing name had been the only "difficulty".**

Three more measured over-pins, all of which read as difficulty:

| The grader asserted | What valid solutions did instead |
|---|---|
| a shared backing pointer | used HAMTs |
| a count of heap examinations | used intrusive LRU lists |
| on-disk framing | satisfied the contract with an atomic rename |

### The probe — dispatch this before any loosening lever

> In a disposable worktree, implement an alternative solution to `<step>` that satisfies the
> written public contract but differs from the oracle in `<representation / control flow /
> ownership>`. Do not edit task files. Run the exact grader and report **every** required test. If
> it fails, identify whether the assertion is **stated**, **inferable**, or an **oracle-specific
> pin**.

Deliverable: full per-test output and a contract-to-assertion map. The overshoot risk on the probe
itself is calling an implementation valid without checking every written invariant.

### Before any of that: is the 0/N even a measurement?

A `0/N` assembled from artifacts — refusals, build breaks, errored arms, `4/4` where the batch was
5 — is **UNMEASURED, not "too hard"**, and loosening on it is unrecoverable. → `C1` §6 and
`reference/R2-signal-integrity.md`.

Also read the gate's own verbatim string before believing "too hard":

> **Avocado 0/5 is not by itself a failure.** The gate needs one pass **and** one fail on the
> **same** model, and that model may be opus or gpt. The server says *too hard* only when all
> three are zero. OURS' operational target — 1–3/5 avocado on every step — is **stricter than the
> server rule** and exists so a task does not depend on rescue by another arm. **STATUS: LIVE as a
> target; the server rule is the validation condition.** Do not present the two as the same thing.

---

## 2. An unfair test can BE the difficulty

**STATUS: LIVE.** The counter-rule to §1, and it is measured in both directions.

> *"Before removing a test that looks unfair: check whether that test IS the difficulty. Fixing a
> false-negative test can collapse calibration to 5/5."*

On one task, one implementation's **9 failures were the entire difficulty** — remove the test and
there is nothing left to grade. *(Provenance: the operator's run ledger, not either source
document — see `ledger/RUNS.md`. **STATUS: SCOPED-TO that task** until a second instance is
recorded.)*

So run both reads before touching an assertion:

| Question | If yes |
|---|---|
| Does a *valid alternative* implementation fail this assertion? | it is a false negative — reshape it (§3) |
| Would removing it leave the step with no failing surface at all? | it **is** the difficulty — pair its removal with a proven discriminator in the same pass, or leave it |

WebAuthn is the measured overshoot: removing the pin moved the task **`0|0` → `1|1`**, which is
in-band, but a further relaxation would have taken it past the ceiling.

---

## 3. Loosening must not delete a graded behaviour

**Reshape the assertion, do not drop it.** Remove requirements the contract never states, make
helpers tolerant, keep the behaviour and drop incidental shape pinning.

A widening is audited for what it **introduces**, not only for what it removes — a tolerant
rewrite has replaced one over-pinning with a worse one and cost rubrics 13/17 → 12/17.
→ `C-drive/C2-repair-grading.md` §4.

The Codex brief for rung 2:

> Modify only `<step>/tests/` so all implementations satisfying `<contract>` pass, including the
> proven alternative from the probe, while `<specific wrong shortcut>` still fails. Replace exact
> representation / private-structure assertions with behaviour-level checks. Do not edit the
> contract file.

Measure: the proven alternative **and** the oracle pass; the known wrong solution still fails.

---

## 4. "Every model failing the same gate" is AMBIGUITY, not difficulty

**STATUS: LIVE. It has been the spec every time.** A uniform near-miss across models with
different strengths is not a hard problem; it is one nobody could read correctly. It maps to
**R03** (trajectory-informed spec clarity), and R03's remedy is prose.

Therefore it is **`Owner: Avocado/human`**: record what the contract says now, what the tests
require, the impact and the direction of the remedy, and **continue every other thread**. Do not
write the prose, do not delegate it, do not draft the replacement sentence. → `00-ROUTER.md` §5.

A task can reach green on every other gate with one open prose finding. Say that, rather than
calling the task blocked.

---

## 5. The loosening ladder — first applicable rung, owners are binding

| # | Rung | Owner | When | Overshoot risk |
|---|---|---|---|---|
| 1 | **Prove or disprove the false negative** (§1) | Codex | always first | calling an implementation valid without checking every written invariant |
| 2 | **Relax an unfair harness pin** (§3) | Codex | rung 1 found a valid alternative rejected by representation, exact error text/class, ordering, a private helper, or another unstated choice | removing the only discriminator → 4/5 or 5/5 |
| 3 | **Clarify the public contract** — name the missing public surface and its observable semantics | **Avocado / Vidit** | failures come from an undiscoverable public name, signature, return shape, empty/error behaviour or cross-step dependency — not algorithmic work | a recipe can swing the task straight to 5/5 |
| 4 | **Collapse breadth into one invariant** | **Avocado / Vidit** | the step fails because it enumerates many separate cases or unrelated surfaces, not because its core invariant is hard | removing the only discriminator |
| 5 | **Narrow or split an oversized step** | **Avocado / Vidit** | full attempts time out or leave several independent deliverables unfinished *after* the contract is clear | the new final step can have no gradient; splitting creates more gates, not fewer |
| 6 | **Reduce the capability, or convert to single-turn** | **Avocado / Vidit** | every fair implementation is still 0/5, or relaxing further would destroy the contract | a thin, mechanical task |

Rungs 3–6 are **reports** from this act, not actions in it. Write the finding, mark the owner,
and keep working rungs 1–2 and everything `C2` owns. The single-turn conversion mechanics —
layout, oracle rebuild, `format` / `track_assignment` fields — live in `B-build/B1-scaffold.md`
and `B-build/B4-solution-env.md`.

**Do not jump rungs.** Every rung skipped in the source pipelines cost a cycle.

---

## 6. Do not over-recommend abandoning

**STATUS: LIVE.** Local calibration reads and memorization reads have both been wrong. A task
called abandon-worthy — sqlfluff — **cleared the server at 4/5 avocado.**

So: **state the risk once, with its evidence, and leave the call to Vidit.** Do not re-argue it in
the next report, and do not let an abandon recommendation stop you from executing the rest of the
ladder in the meantime.

"Retire it" is acceptable only when you can show the idea is already public, or that **no
gradeable variance exists after you have actually looked for it** — which means the n=5
disagreement analysis was run and the five implementations agreed everywhere that matters
(→ `C-drive/C6-replay-verify.md` §5), not that it felt unpromising.

---

## 7. Exit — the band must be MEASURED

The act is complete when a **real** implementation has been run against the graded suite and the
result quoted:

- the probe's alternative implementation, per-test output, with each failing assertion classified
  **stated / inferable / oracle-specific pin**; and
- the replay verdict from `C-drive/C6-replay-verify.md` — **PROVEN**, **UNPROVEN** or
  **DISPROVEN** — in those words.

**After any grading fix the difficulty is UNMEASURED again.** Recalibrate before anyone reads the
new band as difficulty.

---

## 8. CHECKLIST

```
[ ]  1. The 0/N confirmed to be a measurement, not artifacts (C1 §6 / R2)            §1
[ ]  2. Gate's verbatim string read; avocado 0/5 not assumed to be a failure         §1
[ ]  3. Image contents checked: everything the contract tells the solver to read
        is actually shipped                                                          §1
[ ]  4. Alternative-implementation probe DISPATCHED and its per-test output read     §1
[ ]  5. Each failing assertion classified stated | inferable | oracle-specific pin   §1
[ ]  6. Asked of every assertion being removed: does this test IS-the-difficulty?    §2
[ ]  7. No graded behaviour deleted — assertions reshaped, not dropped               §3
[ ]  8. Widening audited for what it INTRODUCES (C2 §4)                              §3
[ ]  9. Uniform cross-model failure recorded as R03 ambiguity, Owner: Avocado/human  §4
[ ] 10. Ladder worked in order; no rung jumped; owner honoured on every rung         §5
[ ] 11. No contract file touched by Claude or Codex, directly or indirectly  router §5
[ ] 12. Abandon risk (if any) stated ONCE, with evidence, decision left to Vidit     §6
[ ] 13. C6 verdict recorded: PROVEN | UNPROVEN | DISPROVEN                           §7
[ ] 14. Oracle still 1.00 x3; proven alternative passes; known wrong solution fails  §7
[ ] 15. Band reported as measured, with the command output behind it                 §7
```

---

## HANDOFF

```
HANDOFF C4-loosen-salvage
  EXIT:      <the measured band and the command output behind it; the probe's
              per-test result>  |  EXIT: NOT MET + reason
  CHECKLIST: <n of 15 ticked; every waived line with its reason>
  ARTIFACTS: <paths changed, all under <task>/>; the probe implementation path;
             commit SHA
  FACTS:     false negative or genuine difficulty, with the evidence line; which
             assertions were reshaped; which rung was used; what is still UNMEASURED
  OPEN:      every rung 3-6 finding, Owner: Avocado/human; any abandon risk stated
  NEXT:      C6 (if the replay has not run) | C1 (re-read the new verdict) | C5 | park
```

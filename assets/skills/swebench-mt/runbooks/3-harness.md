# RUNBOOK 3 — HARNESS (stages 5 → 7, and salvage)

Read the server verdict, prove what it means, and move the task into band by
changing the HARNESS — not the idea. If you were dispatched to tune or salvage,
read this and nothing else.

**Standing instruction: almost every task is salvageable. Abandoning an idea is
the WORST outcome and requires proof, not judgement.** Two tasks that looked
like real difficulty (0/5 on every model) turned out to be false negatives —
one had three independent grader defects and only 1 of 4 rollout failures was a
genuine bug; the other was 100% grader failure, and a change that left the bug
entirely unfixed still scored 6/6.

Companion: `references/signal-integrity.md` — **read it before believing any
verdict.** ~30% of trials once died to a binary-pull race and scored as
legitimate `reward 0.0`.

---

# PART A — THE STAGES

## Contract and reward path first — before calibration

After any task edit, calibration is forbidden until the exact current bytes
have a fresh green RUNBOOK hard-stop 1b proof: bidirectional 1:1 atomic
requirement ↔ graded-behavior mapping, mutually exclusive and collectively
exhaustive rows, and positive-control plus fake-pass evidence showing every
adversarial path earns zero. A calibration run from before the latest edit is
historical evidence only, never release evidence. Fixing a finding invalidates
the proof and requires a new proof before another calibration run.

## 5 — Read the verdict

```bash
codimango task errors <task>
```
Route on the exact message using the table in `SKILL.md`.

**STOP.** Before tuning anything, run the one-minute audit in
`references/signal-integrity.md`. ~30% of trials once died to a binary-pull race and
scored as legitimate `reward 0.0`; `n_errored_trials` undercounts. Per-step
only, never aggregate.

## 6 — Tighten or relax

Both ladders are in RUNBOOK 3; take the rungs in order. Do not
substitute judgement for the ladder — every rung we skipped cost a cycle.

The loop is much cheaper if `artifacts` was declared at stage 3 — optional, and
unverified in our harness so far. With it: extract each canonical cell's implementation → diff the *passing* ones against
each other → dry-run the candidate test against all of them in Docker → keep it
only if ≥1 fails and ≥1 passes on the same model → push **one** new
`fail_to_pass` → re-read. One at a time.

## 7 — Submit

```
Can you take a look at <TASK> on codimango and summarize remaining blocking
issues along with all human reviewer concerns and whether we have addressed all
reviewer concerns/issues? Is the task ready to be submitted?
```

**Green server gates are NOT "ready to submit"** (Vidit, 2026-09-30). Before
reporting a task as submittable, run an impartial reviewer pass (master Codex,
read-only) with the review-task-swebench-v2 rubric AND a failure-quality audit:
every failing trial classified via `codimango trial analysis <tid>` +
ctrfResults as GENUINE / STATEMENT-CAUSED / GRADER-CAUSED / ENVIRONMENT. If the
failures are not mostly genuine reasoning failures, the task is not worth
submitting. Fix everything that reviewer would flag first, so the human review
passes directly.

**STOP — human review.** Then a retro: fold anything new into `00`–`03`, not
into this file.

---

---

# PART B — CALIBRATION RULES AND BOTH LADDERS

> **Use the current server verdict, not a historical format exception.**
>
> - **Multi-turn:** the gate is per step; in-band is **1-3 of 5 on avocado**, and
>   the last step is never exempt.
> - **Single-turn:** also treat **4/5 as too easy** unless the current validation
>   report explicitly grants an exception. On 2026-10-02 the server rejected
>   `ruby-auth0-configurable-retry-classes` and
>   `dropshot-option-return-nullable-openapi` at 4/5, contradicting the older
>   `avocado not trivial` wording formerly recorded here.
>
> Check `format` in `task.toml`, then treat `codimango task errors <task>` for the
> exact submitted commit as authoritative. Do not tune against remembered rules.

# Calibration: MAX 3/5 Avocado successes per step

**Current target: every step must land at 1–3 Avocado successes out of 5
(`0.2–0.6`). `4/5` (`0.8`) is too easy.** Treat this as a per-step server gate,
not an aggregate target. Local Avocado is not predictive; use it only for gross
debugging if the server gives no usable signal. See
`references/signal-integrity.md`.

The shortest loop is: read the named failing step, choose the first applicable
play below, make one measurable change, run oracle plus structural checks, push,
and read `codimango task errors <task>`. Skip plays whose precondition is false.

## Current server rules (observed 2026-09-17)

```text
"2_range_difference" too easy — avocado passed 4 of 5, over the 3/5 ceiling,
  and the last step is never exempt

"2_..." has no gradient — avocado never reached it and every model that did
  passed every attempt

Step gate failed — "<step>" too hard —
  no model passed it (avocado 0, opus 0, gpt 0)
```

- The normal in-band result is **Avocado 1–3/5 on every step**.
- `0/5` is too hard unless another model supplies the success required by the
  exact server verdict; operationally, target an Avocado success instead of
  depending on rescue.
- `4/5` fails. The former “anything below 1.0” rule is obsolete.
- “No gradient” means Avocado never reached a later step and every model that
  did reach it passed every attempt. The later step still fails even though its
  apparent conditional pass rate is perfect.
- The legacy 1.0 exemption is at most one per **task**, requires 3+ declared
  steps, and never applies to the last step. It is not a target.
- Oracle must pass `3/3`; otherwise calibration is skipped.

The server currently evaluates both rulesets. An older task can say:

```text
Passed under the pre-9/15 rules (current rules: ... too easy ...)
```

and remain marked passed. **That grandfathering is fragile and must not be
relied on.** A rerun or policy cleanup can expose the current-rule failure.
`jsonschema` demonstrated this exact state at `avocado 0.2|0.8`.

Score strings are per-step pass rates: `avocado 0.2|0.6` means 1/5 passed step 1
and 3/5 passed step 2. Never average them. Two agents reported an in-band
aggregate while one step was silently at 1.0.

## First classify the signal

Before changing difficulty:

1. Confirm server oracle is `3/3`.
2. Read the per-step Avocado split and current-rules explanation.
3. Exclude dead trials and load flakes with `references/signal-integrity.md`.
4. Verify the server commit is the artifact you intended to measure.

At `n=5`, one trial moves the rate by `0.2`. Django step 1 moved `0.4 -> 0.8`
on byte-identical step artifacts, and franz-go step 2 moved `0.8 -> 1.0`
unchanged. If one noisy reading is the only evidence, rerun before redesigning;
do not aim at the `0.6/0.8` boundary.

## THE HARDENING LOOP — prove the gradient LOCALLY before you push

Do not push a candidate assertion and wait for the server to tell you. Build the
gradient locally, from two independent sources, and only push once it splits.

### 1. Sample implementations from PREVIOUS TRIALS — the better source
These came from the models that actually grade the task (avocado / opus / gpt),
not from a local stand-in. **Prefer them.**

```bash
codimango trial artifacts <tid> --json | jq '.files[] | select(.name|contains("<impl>")) | {name,key}'
codimango trial artifacts <tid> --key "<s3-key>" > /tmp/<task>/trial-<tid>.ext   # 1-2s
```
Pull one per canonical cell, across all three models, and record
`seedFromStepRunId` so five cells from one seed are not mistaken for five
independent solutions. Needs `artifacts = [...]` in `task.toml` — declare it at
scaffold time or this source does not exist.

### 2. Generate fresh implementations IN PARALLEL — the supplement
```bash
for i in 1 2 3 4 5; do
  ~/.claude/skills/swebench-mt/mc2.sh /tmp/<task>/build-prompt.txt <clone> /tmp/<task>/impl-$i.out &
done; wait
```

**Why both:** measured 2026-09-18, a purely local n=5 predicted the server
correctly on 2 of 4 tasks. Local said 2/5 for two tasks that came back avocado
4/4 and 5/5. The local generator is not the graded model, so treat local-only
numbers as a lower bound on difficulty and trial artifacts as ground truth.

### 3. Apply the candidate assertion to EVERY implementation
```bash
docker run --rm -w /app -v /tmp:/tmp -v $(pwd):/task <task-image> bash -c "
  bash /task/steps/<N>/solution/solve.sh
  cp /tmp/<task>/<impl> <path>
  cp /tmp/<task>/candidate_test.<ext> <testpath>
  <test command>"
```

### 4. Read the split — this IS the gradient
| result | meaning |
|---|---|
| 0 of N fail | not a discriminator. Discard the assertion; do not push it. |
| **>=1 fails AND >=1 passes on the SAME model** | **gradient. Push it.** |
| all N fail | 0/N — check it is not a false negative before believing it |
| an EXISTING test fails | that test is over-pinned. Fix that first. |

### 5. Push ONE assertion at a time
Batch only when you can predict the combined effect against every extracted
implementation. Then re-read the per-step cells.

**This is the whole of stage 6.** Everything below is which assertion to try;
this is how you know whether it worked before spending a validation cycle.

## Measurement validity — read before choosing a rung (measured 2026-09-29, kustomize step 1)

| lever type | valid evidence | INVALID evidence |
|---|---|---|
| test-only (statement unchanged) | replay ≥8 reconstructed real implementations (`/tmp/overnight/replay.py`) | — |
| wording change | n=4 fresh `mc2.sh` (Muse) implementations under the NEW statement, scored by a probe grader, BEFORE Codex authors tests | replaying old trials: they never saw the requirement, so they fail it by construction (CLI lever: replay 0/5 → fresh 4/4) |

- **Stated requirements are not forks.** Models implement what is written. Look first for a property the
  current words already imply that the natural implementation silently breaks ("same value" vs a
  float64 round-trip: 3 of 10 real implementations).
- **A failure shared by every implementation is not a gradient.** 10 of 15 probed properties failed
  identically on all 14 implementations. Grade only properties that split the population; compute
  P(≤3 of 5) from the split before pushing, aim p≈0.4.
- **Filter later-step replays by the NEW earlier-step grader.** Step N+1 only runs on seeds that
  passed step N. A discriminator graded in step 1 removes the failing lineages, so its "regression"
  copy in step 2 passes by inheritance. spire-workload replay said 0.4|0.4; honest prediction after
  filtering was 0.4|1.0 (every other step-2 probe was 5/5). Count only step-2 cells whose step-1
  parent passes the new step-1 grader.
- **No splitting property → go structural** (rung 5) instead of another wording round.
- Never put concrete test cases in a MetaCode brief; they get echoed into the statement verbatim.

## Too easy: ordered escalation ladder

Use the first applicable play. This ladder is deliberately cheapest and most
reversible first. It is **not exhaustive**; append newly proven plays, including
their probe evidence and measured server effect.

### 1. Harness: add one discriminating behavioral assertion

**When:** A successful solver used a reasonable shortcut that the current tests
do not distinguish, and a disposable probe proves the shortcut passes today.

**Tell Codex exactly:**

> Work only on `<task>/<step>`. Do not edit `instruction.md`. First reproduce
> `<solver shortcut>` as an alternative implementation and run the current
> grader. If it already fails, stop and report that this is not a discriminator.
> If it passes, add the smallest behavior-level assertion that distinguishes
> `<required structural/timing/visibility property>` from that shortcut. Do not
> assert private helper names or the oracle's implementation. Prove the oracle
> and at least two independently valid implementations pass, while the probed
> shortcut fails. Report the exact test ID and results.

**Expected effect:** Convert some 5/5 or 4/5 solutions into real failures without
changing the public contract.

**Measure:** Probe passes before the assertion and fails after it; oracle and two
valid shapes remain green; server rate for that step moves into 1–3/5.

**Overshoot risk:** High if the assertion pins ordering, allocation, private
structure, or a representation the instruction does not require. A failing
valid alternative is a false negative, not useful difficulty.

### 2. Instruction: DE-SCAFFOLD the route, not the public contract

**De-scaffolding** = removing the structure that lets a model transcribe a spec
instead of reasoning: bullet lists, numbered requirements, headings, emphasis,
worked examples, branch enumerations. The API contract is untouched. This is not
"making it vaguer" — ambiguity is a validity defect (SWE-bench Verified *rejects*
tasks for "underspecified issue description"), so never trade away specificity.

Target shape: 1–2 paragraphs of informal prose, 2–4 requirements, no lists, no
headings beyond a title, under ~230 words. `preflight.sh` lints all of this.

**When:** The instruction contains worked examples, exhaustive branch lists, or
a recipe that maps almost line-for-line to the solution. Skip when names,
signatures, or externally observable semantics would become undiscoverable.

**Necessary, not sufficient.** Measured across our 37 steps: every in-band step
was under 230 words, and every step over 300 words or carrying a bullet list was
judged too easy or worse. But franz-go `1_acl_resource_scope_matching` was 245
words with zero bullets and still returned 1.0, because the task had no
structural fork. De-scaffold because it is cheap and removes a known cause of
one-shotting — then go find the fork (rung 1).

**Tell MetaCode exactly:**

> Rewrite only `<step>/instruction.md`. Preserve every grader-visible public
> name, signature, error/empty behavior, dependency on prior steps, and
> acceptance boundary. Remove worked examples that reveal the implementation,
> collapse case-by-case enumerations into one invariant, and state the observed
> symptom or desired behavior instead of the algorithm. Do not add file paths,
> helper names, test names, pseudocode, or new requirements. Return a concise
> contract that a maintainer can implement from the repository.

**Expected effect:** Solvers must infer the implementation while still knowing
what public surface is graded.

**Measure:** Diff the instruction to verify only recipe leakage disappeared;
rerun the oracle unchanged; server rate moves toward 1–3/5.

**Overshoot risk:** Removing a required public identifier or ambiguity boundary
creates guessing and false negatives. WebAuthn proved wording can be binary:
when every wording probe is all-pass or all-fail, stop wordsmithing and move on.

### 3. Instruction: widen work across multiple call sites or files

**When:** The feature is still a one-function translation and real integration
points already exist in several call sites/files.

**Tell MetaCode exactly:**

> Revise `<step>/instruction.md` so `<capability>` must work through all of these
> existing integration points: `<call site/file A>`, `<B>`, and `<C>`. State one
> shared behavioral invariant, not per-file implementation steps. Preserve the
> public API and do not prescribe helpers or control flow. Make partial support
> at only one call site observably incomplete.

**Then tell Codex exactly:**

> Update only `<step>/tests/` to exercise the stated invariant through `<A>`,
> `<B>`, and `<C>`. Reuse public entry points. Prove a one-call-site
> implementation fails, and prove the oracle plus two complete implementation
> shapes pass. Do not edit `instruction.md`.

**Expected effect:** Force proper segmentation/integration instead of a local
patch while keeping one coherent capability.

**Measure:** A one-site probe fails named tests; full alternatives and oracle
pass; server step lands at 1–3/5.

**Overshoot risk:** Invented breadth becomes scope creep. Use only call sites
that are natural consumers of the same invariant.

### 4. Instruction/design: force different existing code paths

**When:** Multiple branches of the architecture should implement the feature,
but all tests travel through one branch.

**Tell MetaCode exactly:**

> Revise `<step>/instruction.md` so the same observable contract applies through
> `<code path A>` and `<code path B>`, including their interaction with
> `<shared state/ownership/lifetime boundary>`. Describe outcomes, not the
> internal branching mechanism. A solution wired into only one path must be
> incomplete under the written contract.

**Then tell Codex exactly:**

> Add behavioral coverage for both `<path A>` and `<path B>` and one composition
> case that crosses their shared boundary. First prove a path-A-only solution
> passes the old grader; after the change it must fail. Keep the oracle and two
> valid cross-path designs passing. Do not edit `instruction.md`.

**Expected effect:** Expose architectural understanding that a single-path
implementation lacks.

**Measure:** The single-path probe fails only the new coverage; server rate falls
into 1–3/5.

**Overshoot risk:** Two unrelated features disguised as one step, excessive
runtime, or pinning an internal dispatch scheme rather than behavior.

### 5. Structural: add a new, harder dependent step

**When:** An existing step is stuck at 5/5 after cheaper proven levers, and the
repository supports a genuine next capability that consumes its artifact.

**Tell MetaCode exactly:**

> Author a new final step `<N_name>` that consumes `<artifact/API from step
> N-1>` to deliver `<new capability>`. It must be impossible to complete
> independently of the prior step, must exercise a new structural fork, and
> must state public behavior without an implementation recipe. Do not rewrite
> prior steps.

**Then tell Codex exactly:**

> Add the new step's tests and manifest wiring. Prove the dependency by testing
> through the prior step's public artifact. Probe one plausible shortcut and
> require it to fail while the oracle and two valid shapes pass. Do not edit any
> `instruction.md`.

**Expected effect:** Add real failure surface and, only incidentally, make a
legacy exemption structurally available.

**Measure:** Plain-apply cascade succeeds, oracle passes every step, and the
**new last step itself is 1–3/5**.

**Overshoot risk:** Highest structural cost. The exemption is one per task and
the last step is never exempt, so a decorative or 5/5 new step cannot save the
task. Franz-go's `1|1|0.8` proved that adding a third step does not excuse two
easy steps; under the current ceiling even `0.8` must be tightened.

### 6. Structural: expand an existing step

**When:** A coherent capability belongs in the failing step but is too large or
too coupled to justify a separate dependency step.

**Tell MetaCode exactly:**

> Expand `<step>/instruction.md` from `<current narrow capability>` to the
> coherent end-to-end capability `<expanded scope>`, spanning `<surfaces>`.
> Keep one invariant and explicit public boundaries; do not turn it into an
> unrelated feature list or prescribe the implementation.

**Then tell Codex exactly:**

> Extend `<step>/tests/` to cover the expanded contract through each stated
> surface. Probe the old narrow implementation and require it to fail. Prove
> the oracle and at least two valid full implementations pass. Do not edit
> `instruction.md`.

**Expected effect:** Raise reasoning/integration load without adding cascade
machinery.

**Measure:** Old narrow solution fails; base set-diff, oracle, alternatives, and
server 1–3/5 all pass.

**Overshoot risk:** A monolithic step can become too hard, slow, or review-hostile.
Prefer play 5 if the expansion has a clean dependency boundary.

### 7. Last resort: downgrade to single-turn

**When:** Codex **and** Claude independently conclude that the repository/idea
cannot support a genuine MT dependency and sub-ceiling final step. Use this to
land useful work rather than endlessly tune an invalid MT shape.

**Tell both reviewers exactly (run independently):**

> Decide whether `<task>` can support a genuine multi-turn cascade under the
> current per-step 1–3/5 Avocado ceiling. Look for a dependent artifact and a
> fair structural fork. Do not edit files. Give concrete evidence. If no such
> design exists, recommend single-turn explicitly.

If both say no:

1. Ask Muse to author one top-level `instruction.md` that describes the
   final user-visible capability; do not concatenate step recipes.
2. Move to the single-turn layout: top-level `instruction.md`, `solution/solve.sh`,
   and `tests/`; remove the `steps/` declarations and directories only after the
   replacement files are verified.
3. Rebuild the oracle as one **base-to-final source-only** patch and combine the
   graded tests into one `test_patch`; keep tests out of the oracle patch.
4. Set `[task].format = "swe_bench_single_turn"`,
   `[task].track_assignment = "swe-bench-external-repos"`, and keep
   `workstream = "swe_public_repo"`.
5. Re-run base set-diff, oracle, local structural validation, then server checks
   and single-turn calibration.

**Expected effect:** Preserve a valid task without pretending it has a real
multi-turn dependency.

**Measure:** Single-turn structure and oracle pass; server calibration is in its
single-turn band; both independent design reviews are recorded.

**Overshoot risk:** Loss of useful staged context or accidental provenance
violation while recreating `instruction.md`. This is a conversion, not a way to
hide a fixable MT design.

## Too hard: mirror ladder for relaxing

Always begin with play 1. The first job is to separate unfair rejection from
genuine difficulty.

### 1. Prove or disprove a false negative with an alternative implementation

**When:** Any step is 0/5, no model passed, or full trials cluster on one check.

**Tell Codex exactly:**

> In a disposable worktree, implement an alternative solution to `<step>` that
> satisfies the written public contract but differs from the oracle in
> `<representation/control flow/ownership>`. Do not edit task files. Run the
> exact grader and report every required test. If it fails, identify whether the
> assertion is stated, inferable, or an oracle-specific pin.

**Expected effect:** Establish whether the zero is a false negative before scope
is removed. **Measure:** full per-test output and a contract-to-assertion map.
**Overshoot risk:** Calling an implementation valid without checking every
written invariant.

### 2. Relax an unfair harness pin

**When:** Play 1 finds a valid alternative rejected by representation, exact
error text/class, ordering, private helper, or another unstated choice.

**Tell Codex exactly:**

> Modify only `<step>/tests/` so all implementations satisfying `<contract>`
> pass, including the proven alternative, while `<specific wrong shortcut>`
> still fails. Replace exact representation/private-structure assertions with
> behavior-level checks. Do not edit `instruction.md`.

**Expected effect:** Remove false failures. **Measure:** alternative plus oracle
pass, known wrong solution fails. **Overshoot risk:** WebAuthn moved `0|0 ->
1|1`; add a proven discriminator in the same pass when removing the pin would
make the step trivial.

### 3. Clarify the public contract

**When:** Failures come from an undiscoverable public name, signature, return
shape, empty/error behavior, or cross-step dependency—not algorithmic work.

**Tell MetaCode exactly:**

> Clarify only the grader-visible contract in `<step>/instruction.md`: name
> `<missing public surface>` and its observable semantics. Do not reveal file
> paths, helpers, control flow, data structures, test cases, or the oracle
> algorithm. Remove ambiguity without adding new scope.

**Expected effect:** Turn guessing failures into implementation attempts.
**Measure:** prior failures can now locate the API; oracle unchanged; server
produces at least one success but no more than 3/5. **Overshoot risk:** a recipe
can swing the task directly to 5/5.

### 4. Collapse breadth into one invariant

**When:** The step fails because it asks for many separately enumerated cases or
unrelated surfaces, not because its core invariant is hard.

**Tell MetaCode exactly:**

> Rewrite `<step>/instruction.md` around the single required invariant
> `<invariant>`. Remove `<nonessential surfaces/cases>` while preserving public
> compatibility and the dependency on prior steps. Do not prescribe the
> algorithm.

**Expected effect:** Reduce workload while retaining the structural fork.
**Measure:** full trials reach the core tests and at least 1/5 succeeds.
**Overshoot risk:** Removing the only discriminator produces 4/5 or 5/5.

### 5. Narrow or split an oversized existing step

**When:** Full attempts time out or leave several independent deliverables
unfinished even after the contract is clear.

**Tell MetaCode exactly:**

> Redesign `<step>` so it contains only `<coherent capability>`. If the removed
> work is still valuable, place it in a genuinely dependent later step that
> consumes `<artifact>`. Keep each step independently testable and avoid a
> decorative dependency.

**Expected effect:** Make at least one complete solution reachable per step.
**Measure:** no timeout/incomplete-work cluster, plain cascade applies, every
step lands at 1–3/5. **Overshoot risk:** The new final step can have no gradient
or be too easy; splitting work creates more gates, not fewer.

### 6. Reduce the capability or abandon MT

**When:** Every fair implementation is still 0/5, or relaxing further would
destroy the contract. Remove the least central surface and re-probe. If the
remaining work has no genuine cascade, use the single-turn conversion above.

**Tell MetaCode exactly:**

> Remove `<least central surface>` from `<step>/instruction.md` while preserving
> `<core invariant>` and all public compatibility. State the smaller outcome
> precisely without an implementation recipe.

**Expected effect:** Recover a solvable task. **Measure:** at least 1/5 and at
most 3/5 on every surviving step. **Overshoot risk:** A thin, mechanical task;
switch to another idea rather than accumulating ceremony around it.

## Fast validation loop

```bash
codimango bench run -p <task> -a oracle -k 1
# Required: Mean: 1.000 and every per-step reward is 1.

codimango bench validate -p <task> --structural-only
# Required locally: Overall: PASS. Local and server check sets differ.

# Push the exact reviewed task commit, then:
codimango task errors <task>
```

Do not spend 20–40 minutes on local Avocado by default. The same sparql commit
was 3/5 locally and 5/5 server-side; unchanged local runs also produced 1/3 then
3/3. Use server per-step results for tuning.

Record the commit, exact oracle count, per-step Avocado split, current-rules
message, dead-trial audit, and every probe (including failed discriminators).

---

# PART C — SALVAGING A FAILED TASK

# Salvage brief — rescuing a failed task (2026-09-18)

**Standing instruction from Vidit: almost every task is salvageable. Abandoning
an idea is the WORST outcome and requires proof, not judgement.** Your default
is to find the change that makes the task work. "Retire it" is only acceptable
when you can show the idea is already public, or that no gradeable variance
exists after you have actually looked for it.

Governing reference: this runbook — both ladders are in PART B above
— both escalation ladders, in order. Work the rungs; do not jump.

## The method that replaces guessing: FIND THE DISCRIMINATOR EMPIRICALLY

This is the core technique and it applies to every too-easy task.

1. **Generate n=5 fresh implementations** of the task from its own
   `instruction.md`, cold:
   ```bash
   ~/.claude/skills/swebench-mt/mc2.sh <prompt-file> <clone> /tmp/<task>/impl-$i.out
   ```
2. **Diff the five against each other.** Where they agree, there is no variance
   and nothing to grade. **Where they DISAGREE is the only place a
   discriminator can live.**
3. **For each disagreement, ask: is one of these behaviours worse?** Wrong under
   an edge condition, lossy, unsafe under concurrency, quadratic where linear is
   available, leaks a resource, breaks an existing caller.
4. **Write an assertion for that property and run it against all five.** Keep it
   only if it splits them — ideally 1-3 of 5 pass. That is the band, measured
   locally, before any push.
5. If all five agree everywhere that matters, the task has no outcome variance
   as scoped. Go to "widening" below.

This is the same instrument as the server's gradient loop, driven by fresh local
implementations instead of trial artifacts — which matters because most of our
tasks never declared `artifacts`.

## Too easy (5/5) — ladder, cheapest first
1. **Discriminator hunt above.** Add ONE assertion at a time, re-measure.
2. **Widen the graded surface to an interaction**, not more edge cases. Edge
   cases do not create difficulty — measured repeatedly. Look for a second
   subsystem the change must stay correct with respect to.
3. **Grade a QUALITY property rather than existence** — robustness under an
   adversarial input, resource behaviour under pressure, correctness when an
   existing caller is present. The artifact always gets built; whether it is
   good varies.
4. **De-scaffold the instruction** — state the issue, never the remedy. Strip
   mechanism, file names, ordering, algorithm. Search is a variance source.
5. **Add a dependent step** (MT only) — the exemption is one per task and the
   last step is never exempt.
6. Only then consider re-cutting the scope.

## Too hard (0/5 on ALL models) — ladder
**Rung 1 is always: prove it is a FALSE NEGATIVE before you make it easier.**
Write an alternative-but-valid implementation and run it against the graded set.
If it fails, the test is over-pinned and the harness is the bug — we have three
measured instances (a grader asserting a shared backing pointer while valid
solutions used HAMTs; one counting heap examinations while half of valid
solutions use intrusive LRU lists; one asserting on-disk framing while atomic
rename satisfied the contract). Only after ruling that out should you narrow.

Note: **Avocado 0/5 is NOT a failure by itself.** The gate needs one pass AND
one fail on the SAME model, and that model may be Opus or GPT. The server says
too hard only when all three are zero.

## BAD_GRADING_WRONG / BAD_GRADING_WEAK
The reviewer is telling you the grader is defective, not that the idea is. WRONG
and WEAK are different failure modes with different remedies — check
`runs/bad-grading-diagnosis.md` if it exists yet. Do not respond by changing the
idea.

## Hard constraints
- **Claude writes NOTHING inside a task directory** — not `tests/`, not
  `solve.sh`, Dockerfile, `task.toml`, README or `audit/`, and not via a heredoc
  or generated script. Route every task-file change through Codex;
  `instruction.md` is Muse-only. Before any push, `prov_predict.py <task>` must
  show 0 surviving blocks (RUNBOOK.md → "Who writes what").
- Re-run `preflight.sh <task> --with-oracle` before declaring done; oracle must
  stay 3/3.
- Do NOT commit or push — the coordinator commits centrally.
- Report DONE / NOT DONE / BLOCKED with evidence: the n=5 implementation diff,
  which property you found, and the measured split of your new assertion.

---

## Reporting contract

Any agent running this reports **DONE / NOT DONE / BLOCKED per stage with
evidence**, never a summary. For a new `fail_to_pass`: the cell and seed IDs
downloaded, superseded attempts excluded, per-model counts, and the full Docker
dry-run table. If a stage is incomplete, write `NOT DONE: <reason> — BLOCKED`
and do not claim validation. If you skipped an expensive step, say so.

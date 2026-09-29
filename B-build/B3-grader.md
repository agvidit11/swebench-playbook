# B3 — THE GRADED SUITE

```
OWNER:   Codex  (or 1P/human. NEVER Claude — provenance scores by PATH, and one
                 `claude_code` write under tests/ has retired a task)
INPUT:   HANDOFF B2 — the contract, and the list of symbols left unnamed
OUTPUT:  everything under tests/ — config.json, test.sh, run_script.sh, parser.py,
         the test patches
EXIT:    f2p/p2p sets verified by SET-DIFFERENCE at base_commit (§4), and §2's
         alternative-spelling proof run and pasted
```

**The instructions are read-only — absolutely, in every phase.** Make the tests and the golden
match the instruction, never the reverse. If the instruction is wrong, record the finding, mark it
`Owner: Avocado/human`, and continue everything else. → `00-ROUTER.md §5` **If this run changes a
graded assertion on a task that already has server results, it exits through
`C-drive/C6-replay-verify.md`, not straight to `B4`** — a change verified only against the golden
and against variants you wrote yourself is green by construction. → `00-ROUTER.md §8b` **The
two-way contract:** every requirement in the instruction is graded, **and nothing is graded that is
not in the instruction.** `preflight.sh` flags both directions advisory-only; the detection is
regex-based and false-positives.

## 1. R06–R13 and N03 — the Agentic Full-Task Review

Across four tasks built from the peer pipeline, **R08 failed 4/4, R06 and R07 failed 3/4, and R12
failed once.** Every one had a mechanical cause. `STATUS: LIVE`

### R06 — Test coverage

| # | Rule | Observed failure |
|---|---|---|
| 1 | **Executed is not graded.** Every test the verifier runs appears in `fail_to_pass` or `pass_to_pass`. Compute the set difference, assert empty, print it | *"the verifier runs `hook_phase_ledger_test.rb`, but none of those seven Step 1 tests are included in `fail_to_pass` or `pass_to_pass`, so their failures would not affect reward"* |
| 2 | **Run the repo's existing suite for the touched subsystem as `pass_to_pass`** — not a spot-check. The passing reference carries **261 and 279** regression tests alongside **22 and 18** f2p | *"they do not run the existing AASM suite and only spot-check 'return values and raising behavior are unchanged'"* |
| 3 | **Map every requirement sentence to at least one f2p test** and record the mapping. A requirement with no test is an automatic fail | — |
| 4 | **Cover everything the golden instruments, not a subset** | *"the hidden tests only cover `before`, `guard`, `transition`, and `before_enter` among many lifecycle phases the golden instruments"* |
| 5 | **Step 1's `fail_to_pass` must NOT appear in step 2's `pass_to_pass`** → §3 | — |
| 6 | **A requirement whose point is crossing a boundary needs a test that crosses it.** Same for **atomic** (inject a mid-operation failure) and **idempotent** (call it twice) | *"Step 2 claims durable manifest behavior, but the required tests do not run a required cross-process revoke and only check that some metadata file exists"* |

### R07 — Reward-hacking

| # | Rule | Observed failure |
|---|---|---|
| 1 | `parser.py` must fail on any failing test in the **executed** set, not only the configured ones | *"A Step 2 solution could regress the prior ledger tests and still receive reward"* |
| 2 | **Fail closed on an empty `fail_to_pass` set.** Zero graded tests score zero, never one | — |
| 3 | Parse named test results; never infer success from the test command's exit code | — |
| 4 | Restore base test files before scoring — but see §6, and **do not restore candidate-modified test files wholesale**: a correct solution may have had to change them. Prove both directions with mutants or leave it out | — |
| 5 | Do not grade only new spec files against synthetic fixtures | *"could satisfy the exact tested callbacks and reentrant fixtures while missing other lifecycle phases… and still receive full reward"* |
| 6 | **Ask whether the golden itself is the shortcut** | *"an implementation can pass while using recursive directory deletion… The golden itself has this behavior, so the weakness is not hypothetical"* |

### R08 — Accepts alternatives — **failed 4 of 4, read it twice**

| # | Rule |
|---|---|
| 1 | **Search plausible receivers** rather than hard-coding one accessor name |
| 2 | **Normalise every graded entry through one helper, and let no assertion bypass it.** *Observed:* one assertion called `key?` directly on `second.ledger` entries, so a valid object-based entry was rejected |
| 3 | **Accept richer return types** |
| 4 | **Normalise the CONTAINER, not just the element — two layers, both mandatory.** The graded tests did `census(machine).fetch(0)`, which requires an Array or Hash. A solution whose census was a custom object exposing `#entries` failed **8 of 9 tests** with `undefined method 'fetch'` — while **every field name it produced was already correct.** Two prior repair rounds widened names, then values, and moved nothing. Unwrap before indexing (`entries` / `to_a` / `each`), then normalise each element per rule 2 |
| 5 | **Inject faults at the contract boundary, never at an internal primitive.** A revoke-fault test stubbed `FileUtils.rm_rf`; an implementation using type-specific unlinking never triggered it and **two otherwise-valid attempts were recorded `GRADING_FAILURE`.** Stub the API the spec names |
| 6 | Do not pin algorithms, formats, or key names the instruction never states |
| 7 | **Synthetic fakes must accept the real API shape too.** *Observed:* tests rejected solutions calling real RuboCop APIs such as `cop.cop_name` |
| 8 | Assert on externally observable behaviour, not the golden's file layout |

### R09 — Test reliability · *"oracle 3/3" is NOT sufficient*

*Observed:* *"`spec_helper` sets random ordering; running the 6 FAIL_TO_PASS tests together fails
on **~30% of seeds** because quarantine suspension state (class-level global) leaks from
`correction_quarantine_spec` into `correction_conflict_ledger_spec`, turning its expected
`:dropped` outcome into `:suspended`."* Three per-file runs, or three runs on one seed, all pass
that. So the gate is: run **every** `fail_to_pass` test **in a single process**, across **at least
5 distinct `--seed` values** if the suite randomises, and report the seeds. **Do not pin the seed
to make it pass.** Cross-file state leakage is the specific thing you are looking for. No network —
start any service from inside the harness; give every timing window explicit slack.

Isolation must not depend on a production reset hook: that task relied on
`reset_correction_quarantine!`, existing only so the suite could reset global state — two findings
at once (R01, *"recoverable only from the hidden tests"*, plus an engineering finding against the
golden). **The remedy is to remove the global state, not to document the hook.**

### R10 · R11 · R13

| Axis | Requirement |
|---|---|
| **R10** | Run the test patch at `base_commit` with **no** solution applied; confirm every f2p fails; paste the output. An f2p that already passes is a vacuous pass and fails outright → §4 |
| **R11** | Time the verifier, report the wall clock. The passing reference notes grading *"remains within a few minutes and below the configured 900-second timeout."* No GPU, no human step |
| **R13** | Three oracle trials, reward 1.0 on each, both steps. **One flake is a fail** |

### R12 — Golden correctness — graded against the instruction text, not against your suite

A golden that passes every test you wrote can still fail here. For every *"only X"* / *"never Y"* /
*"must not touch Z"* sentence: (1) identify what the golden **delegates to** and read that
implementation upstream at `base_commit`; (2) build the adversarial case and run it against the
golden; (3) add it as a graded test — simultaneously R12 and R06, and fixing one leaves the pair.
*Observed:* *"invoking a directory, then adding `user.txt` under that created directory before
revoke, results in `USER_DELETED` because `Directory#revoke!` ultimately calls `empty_directory`
on the root and recursively removes unmanifested children."* **The golden does not contain the
offending code** — grepping the diff for `rm_rf` returns **nothing**. The violation lives in what
the golden delegates to. **Mirror every golden change to all copies** — the `.patch` in each
`tests/config.json`, `solution/solve.sh`, any `code_patch.diff` — and prove it with
`git apply --check`. An **unchanged `.patch` md5 after a golden-logic fix is the failure signal,
not the success signal.**

### N03 — Data realism

| # | Rule |
|---|---|
| 1 | **Prefer the repository's own fixtures** — the passing reference *"mainly uses the repository's existing Rails test app and generated users/tokens, not an artificial dataset"* |
| 2 | **Exercise the real API, not a fake protocol.** *Observed:* *"tiny `abcde` sources and fake report structs rather than exercising realistic Ruby files or actual RuboCop autocorrect runs"* |
| 3 | **Same decision that fails R08** — the synthetic fakes *"only accept a narrow hidden shape."* One fixture choice, two axes. If you are writing a stub standing in for a library type the solution will legitimately use, **stop** |
| 4 | **Toy-scale inputs trivialize.** If the premise is conflict, crowding, ordering or volume, the fixture must produce that condition at realistic size |

## 2. The D1 proof obligation — mechanical

For every symbol `B2`'s HANDOFF lists as **deliberately left unnamed**, the graded suite must be
**indifferent to its spelling**, proven by running code. `STATUS: LIVE`
Take the unnamed-symbol list from HANDOFF B2 (if empty, say so and skip). Per symbol, write an
**alternative-spelling implementation** — functionally correct, satisfying the instruction, naming
that symbol something a competent engineer would plausibly choose instead, never re-using the
golden's spelling anywhere observable. Apply it to a clean checkout at `base_commit` in place of
the golden and run the full graded suite. **Required result: reward 1.0.** Paste the alternative's
declarations and the reward line.

| outcome | meaning → action |
|---|---|
| alternative scores 1.0 | name-agnostic for that symbol → done |
| fails **a new** assertion | that assertion pins a name the instruction does not carry — the `BAD_GRADING_WRONG` shape → remove or loosen it; adding tests makes it worse |
| fails an **existing** assertion | over-pinned, a live false negative → fix before calibration |

**Do not substitute a variant built from your own alias list** — it ranges over exactly the
spellings you just accepted. Write the alternative to the instruction, not to the test.
Assert instead of a name: an error **is raised** and something true about it (it carries the
offending input; it derives from an error type the repo **already** defines); the observable effect
through an **existing** public entry point; state and consequences — what a second call sees, what
an observer counts, what survives a failure, what an existing caller still gets; `len(got) == 0`,
never equality against `nil`. Highest-yield check in the pipeline, and it has caught a false
negative every time it has been run: `open62541` rejected **4 of 5** candidate forks this way;
`franz-go` found **5 of 7** alternative implementations already passed the shipped graded set;
`django` skipped probing once, added three tests Avocado already satisfied, and spent a full server
cycle with no movement.

## 3. The R06 seed-independence protocol

`SCOPED-TO: multi-turn`. Recurred on **three tasks in one cycle**; one correct answer.
`STATUS: LIVE` **The finding** always reads: *"step 2 does not require the step-1 fail-to-pass
tests to keep passing, even though the step-2 prompt says it continues step 1's contract."*
**The obvious fix is forbidden.** Adding step-1 `fail_to_pass` into step-2 `pass_to_pass` makes
step 2 score on another trajectory's work — step-2 cells fan out from step-1 snapshots, many
unsolved, so seeded cells score 0 regardless of their own output. It also breaks the
`step p2p independence` check. Attempted and reverted on two tasks; on a third it was found already
shipped and had to be removed. It produced a confident *"step 2 too hard — no model passed it"*
while step 2's own test passed in **5 of 5** trials.

> **Step 1's `fail_to_pass` must NOT appear in step 2's `pass_to_pass`.** Use only controls that
> pass at step-2 base regardless of the seed.

**The correct fix — guard step 1 from inside step 2's own graded set.** Author step-2
`fail_to_pass` tests whose expected result depends on step 1 still being correct; they live
entirely in step 2, so there is no seed dependence. Find the interlock — the two steps almost
always share a substrate (step 2 extends a classifier, a ledger, an analysis step 1 built).
**Three proofs, all mandatory. The third is the point:**

| # | Setup | Required result |
|---|---|---|
| 1 | step 1 + step 2 applied | new tests **pass**; oracle 1.0 on both steps |
| 2 | step 1 only | new tests **fail** — this is what makes them legitimate step-2 `fail_to_pass` |
| 3 | **both steps applied, then step 1's logic reverted** | new tests **fail** |

**If proof 3 passes, the tests are not guarding step 1 and the work is not done** — report it
rather than shipping. **The trade-off is real and must be stated, not hidden:** a step-2 solution
can still regress step 1 in ways the new tests do not cover, and a reviewer will flag it as R07
(*"Step 2 selects `ledger_contract_spec` but excludes it from the reward allowlist, so step-1
ledger regressions can be ignored"*). Both cannot be satisfied at once — **the measurement rule
wins**, because violating it corrupts every difficulty number the task ever produces. Record it in
`TEST_RATIONALE.md`; to make the finding vanish, stop *selecting* the step-1 spec at step 2.

## 4. The f2p baseline-diff gate — the exit condition

Run the graded suite at `base_commit` with no source patch and **set-difference** against
`fail_to_pass`. **A mislabelled `pass_to_pass` has cost two tasks a Request-changes.** Run it; do
not infer it. `STATUS: LIVE`

| Check | Detail |
|---|---|
| f2p / p2p | every `fail_to_pass` fails, every `pass_to_pass` passes. Compare **sets**, not counts |
| unrelated base failure | a test already failing at base for another reason is **not** a legitimate f2p |
| uncollectable pre-patch | ImportError / SyntaxError / build failure is not one either — **100% of SWE-Factory's false positives.** `preflight.sh` raises it as `error2pass` when `parser.py` never matches `ERROR` |
| casing mirrors | both present and identical — the harness **hard-errors** when they disagree |
| test user | run graded tests as the **verifier user (uid 1000)**, not root — root ignores `chmod` and gives false reds on permission tests |
| hunk headers | every `@@ -0,0 +1,N @@` equals its body line count. **A short header makes `git apply` silently truncate the file, exit 0, and pass `--check`** |

## 5. grader-lint — what may never appear in an assertion

`python3 ~/.claude/skills/swebench-mt/grader-lint.py <task>` — from the 2026-09-18 agentic-review
diagnosis over **8 tasks**; each detector caught a real failure with **0 false positives on the 4
GOOD tasks**. `STATUS: LIVE`

| Finding | Patterns | Why |
|---|---|---|
| **Private-state grading** — BLOCKING | `unsafe.Pointer`, `UnsafeAddr`, `NumField()`, `IsExported()`, `reflect.ValueOf(...).Elem()`, `instance_variable_get`, `.send(:`, `__dict__`, `getattr(x, "_…")` | the grader may only touch what the instruction names → R08 → `BAD_GRADING_WRONG`. **circl named its whole public boundary and still failed on exactly this; all nine non-oracle attempts died on that one test** |
| **nil-vs-empty pin** — advisory | `reflect.DeepEqual(x, nil)` | representation is not contract unless stated. Assert `len(got)==0` |
| **nil-for-collection** — advisory | a helper whose expected-value parameter is `[]T`/`map[...]` called as `helper(..., nil)` | `awaitPendingFlushes(t, fn, nil)` with DeepEqual makes an empty non-nil slice fail with the unreadable `got = [], want []` |

After **any** widening, grep the changed test for `instance_variable_get`, `__send__`, `:@`,
`instance_variable_set`, `.to eq(`, `==`, `assert_equal`, and ask of each hit: *is this symbol or
shape named in the step text?* If not you have **moved** the pin, not removed it. Measured: a
step-2 example widened away from a thread-interruption requirement left
`instance_variable_get(:@entries)` behind, rejecting any implementation calling its map `@flights`
or `@inflight`. Rubrics fell **13/17 → 12/17** — the round was net negative.

## 6. Never add a refusal path to the grader

Prefer **restore-and-grade**. A `go.mod` guard and a test-edit gate **each zeroed correct solutions
before a single test ran.** A grader that refuses to score is indistinguishable from a task that is
too hard, and it contaminates every number downstream. `STATUS: LIVE`

## 7. Part IV — `code_patch_quality` (the TBR review)

R06–R13 is the *Agentic Full-Task Review*; a separate *Agentic Review (TBR)* scores `spec_clarity`,
`test_quality`, `hackability` and `code_patch_quality` — and on the four peer-pipeline tasks,
**`code_patch_quality` was the only dimension that decided pass vs fail.** Targets: spec clarity
`Good`, output ambiguity `Unambiguous`, test quality `Good`, information leakage `None`,
hackability `low`, code patch quality `Good`.

**A. Write the golden as a reviewer would accept it.**

| # | Rule |
|---|---|
| 1 | **No global or class-level mutable state.** *Observed:* *"the quarantine mechanism relies on global mutable state on the `Team` class… cleared only by a test-only reset method, which is a fragile design that would be questioned in review."* Rated *Functionally Correct but Poor Engineering* — **the tests all passed and the task still failed.** The rule was already documented when that task shipped the defect, so treat it as a **gate, not advice**. The same global state made the suite fail ~30% of random seeds (R09) and cost an R01 rating too — **one design choice, three failing axes.** Grep for `@@`, class-level `Hash.new`, constants holding mutable state, and **say in your report that you did** |
| 2 | **No test-only hooks in production code.** If the tests *need* one, the design is already wrong |
| 3 | **Wire through the library's own extension points**, not around them |
| 4 | **No leftover scaffolding or dead code**, including paths the spec does not require |
| 5 | Ask: *would this survive review as an upstream contribution?* That is the literal standard |

**B. Patch packaging — mechanical, and it sank one task.** The full trap catalogue, with its
measurements, is `reference/R3-landmines.md §B`. These are the gates **you** run here:

| § | Gate |
|---|---|
| **B.2** | **Sequential apply — run it, paste the output.** Every task in the peer cohort (**8 of 8**) has the risky shape (same `base_commit`, overlapping files), so a static check is not enough: `git checkout <base_commit>`, then per step `git apply --unidiff-zero --check <step_N>` followed by `git apply --unidiff-zero <step_N>`. This is also what decides §8 |
| **B.4/B.5** | **Top-level `patch`/`test_patch` non-zero, and no cross-step duplicate silently dropping a test.** Derive `fail_to_pass` by **running**, never assuming it is the union of the steps → `reference/R3-landmines.md §B.5, §B.6`; what that record must contain is contested → `B4 §8` |
| **II** | **A change in the wrong file does nothing.** Multi-turn grading reads `steps/*/tests/config.json`. A change made only to the top-level `tests/config.json` is **inert**: it ships, it reviews clean, and it grades nothing. This has already cost a full round. Land it in **every** step config it applies to; the step configs differ in length so they cannot be copy-pasted — **regenerate each**; keep `steps/N/tests/prior_test_patch.diff` byte-identical to step N−1's `test_patch`; **report the per-file grep hit count as proof** |

**C. Spec clarity — two legal routes, both give `Good`.** Either the instruction pins the token,
**or** your tests are indifferent to it. What fails is pinning it in the tests while leaving it out
of the prose — *observed:* *"the exact record/ledger attribute names and the
`:performed_with_hook_error` outcome literal are design tokens the tests pin that must be inferred
from prose."* The passing reference's residual ambiguity (`generate_token` receiver, digest
algorithm) *"is intentionally absorbed by implementation-agnostic tests."* → `B2-contract.md §1`
**N04 is downstream of R01/R02 — do not chase it directly.** After an oracle run, ask whether a
failing rollout would fail for the *intended* reason or for name-guessing. If the latter, the
contract is still underspecified — **report it rather than papering over it with more tests.**

## 8. CONFLICT — UNRESOLVED: the step-patch format

| Source | Position |
|---|---|
| PEER `07-codex-rebuild-solution-and-tests.md`:64–68 | *"Each step patch must stay **cumulative-from-base** for independent per-step evaluation; converting to sequential deltas … breaks real grading."* |
| PEER `05-codex-finish-the-scaffolding.md`:401–408 | explicitly **corrects** that — *"Taken literally that is what **produces** the resque failure"* → *"**Step N's patch must apply cleanly on top of the state left by step N−1**, and applying every step in order from `base_commit` must produce the final solution."* |
| OURS `runbooks/2-build.md`:505–520 | agrees with the correction: *"Step N's source `patch` must be the delta from step-(N-1)-solved to step-N-solved. A base-to-final patch re-adds prior code and can fuzz locally while failing server-side."* Prove with plain `git apply` — no `--3way`, `--fuzz`, `--recount` — in a fresh disposable clone |

**`07` appears stale** — `05` names it as the text it is correcting, and OURS reached the same
correction independently. **Recorded as a flagged conflict rather than a silent choice** because
`07` was never formally retired and no version marker says so. **Both positions agree on the only
gate that matters:** run B.2 and see which shape actually applies in order. A step patch touching
no file an earlier step touched satisfies the corrected rule whether or not it is cumulative; both
shapes ship in the peer cohort (paper-trail's step 2 edits a file step 1 created and composes
correctly, resque's does not). `franz-go`'s third step was rebuilt against the shipped step-2 tree
after a stale local branch was found **109 lines behind.** Each step must ship **both** `patch`
and `test_patch` — the training pipeline silently drops incomplete steps.

## ④ BRANCH COUNT — the discriminating power of a graded set

`STATUS: LIVE` — 51 failing server trials across 19 non-degenerate arms, `.e2e/w3-3/artifacts/FAILURE-TAXONOMY.md`.

**A graded set's discriminating power is BRANCH COUNT, not test count.** A *branch* is an
independent way an otherwise-correct implementation can be incomplete that your set will actually
catch. Twenty tests exercising one condition is one branch.

The three measured cases:

| task | f2p tests | branches that ever discriminated | outcome |
|---|---:|---:|---|
| `dropshot-option-return-nullable-openapi` | 6 | **0** — zero partial rows in 10 trials | **5/5 too easy** |
| `object-rs-atomic-rewriter-modify` | 14 | **1** | 3/5 and 1/5 — in band |
| `connect-go-trailing-metadata-parity` | 3 | ~1 (broad contract, ~30% of domain graded) | **5/5 too easy** |

Six tests that never separate anybody are six tests, not six branches. **This is the mechanism
behind `BAD_GRADING_WEAK` and behind "too easy" alike** — and it is the thing the whole
contract-domain enumeration above is really buying you.

**Estimate it before you push.** For each independent condition in your enumeration, ask: *could a
competent implementation get this one wrong while getting every other one right?* Count only those.

| branch count | read |
|---|---|
| **≤2** | expect a degenerate band. The set cannot separate. Widen it or do not push. |

**When branch count and `GATE 4` disagree, BRANCH COUNT WINS.** `STATUS: LIVE`, 2026-09-23 — they
disagreed on a real candidate (`GATE 4` 3/5 in band, branch count 2) and nothing said which
governed. The precedent settles it: `connect-go` measured `GATE 4` **3/5 local** and returned
**avocado 5/5** from the server. A local n=5 is five draws from one generator; branch count is a
structural property of the graded set. Trust the structure.

If widening the set to reach 3 branches is not possible, that is the answer — the contract does
not have enough independently-checkable surface to carry a task.
| 3–6 | workable |
| 7+ | good, provided each is genuinely independent |

**Why this matters more than it looks:** 33 of 51 failing trials failed **exactly one** graded
test (median 1, suites of 10–153), and the population study independently measures a median failed
fraction of 0.077 — about one test in thirteen. **Nobody fails wholesale.** A failing
implementation is a passing one with one hole in it, so the only question that decides your band is
how many distinct holes your set can see.

## ⑤ THE ANTI-`BAD_GRADING_WRONG` GATE — prove the grader ACCEPTS correct work

`STATUS: LIVE`, 2026-09-24. **We had no gate for this and shipped one anyway.**

Everything else on this page asks *"does the grader catch wrong work?"* — the mutant, the branch
count, the contract-domain enumeration. `BAD_GRADING_WRONG` is the opposite failure: **the grader
rejects work that is right.** Nothing here tested for it.

What we *did* have was the D1 alternative-**spelling** proof (§2) — which covers exactly one of the
four over-pinning layers, and not the dominant one:

| layer | what the test demands the spec never stated | covered before today? |
|---|---|---|
| **Name** | a specific accessor / method / key name | yes — §2 |
| **Value** | a specific enum value, symbol, or String-vs-Class form | **no** |
| **Shape** | the *container* or element type — Array vs Hash vs custom object | **no — and this layer dominates** |
| **Semantic** | genuinely different behaviour | n/a, that is the task |

On one measured task, widening names (round 1) left it at 0 of 9 and widening values (round 2) left
it at 0 of 9; **8 of the 9 failures were one line** that indexed the observable with `.fetch(0)`,
requiring an Array where the agent returned a custom object. Widening shape took it to 6 of 9.

### The gate

**At least one independently-written correct implementation must PASS your graded set.**

You already have the implementations — `GATE 4`'s n=5, or better, real trajectories pulled per
`C6`. Run them against the **real** grader, not the A3 sketch.

```
0 of N pass   -> BAD_GRADING_WRONG. Do not push. The grader rejects correct work.
1..N-1 pass   -> good; this is also your branch-count evidence
N of N pass   -> no separation; that is §④, a different problem
```

**`0 of N` is the signature, and it co-occurs with a "too hard" band.** A step reading `0/0/0` and
`BAD_GRADING_WRONG` together is almost never a hard task — it is a grader rejecting everyone.
Measured on `kustomize-localize-source-fidelity` step 1.

**When it fires, remove or loosen an assertion. Never add tests** — adding tests to a grader that
already rejects correct work makes it reject more.

**Diagnose by layer before you touch anything**, using the table above and the actual exception
text: a `NoMethodError` on the *collection* is a shape failure, not a naming one, and widening the
wrong layer costs a full round each time.

## THE THREE CHECKS THAT CATCH `BAD_GRADING_WEAK`

`STATUS: LIVE` — added 2026-09-23 after `connect-go-trailing-metadata-parity` returned
`BAD_GRADING_WEAK` with R06, R07 and R12 all failing. **Every gate we had was green when it
shipped.** Oracle was 3/3 four times locally. These are the three questions nothing asked.

### Why `oracle 3/3` can never catch this, by construction

Oracle 3/3 asks **"does the golden pass MY tests."** It never asks **"does the golden satisfy the
CONTRACT."** Those two diverge exactly when the tests under-cover the contract — which *is* the
definition of `BAD_GRADING_WEAK`. A green oracle is therefore not evidence against it. You need
checks that reach outside your own test list.

### ① Contract-domain enumeration → catches R06

For every **universal** claim in the contract — "all X", "parity across Y", "never Z" — enumerate
the input domain **from the platform, spec or library**, not from the tests you already wrote.
Then show the graded set samples each class.

The measured miss: the contract said strictest-wire *parity*. The tests covered NUL, CR, LF, DEL,
padding, repeated values and protocol-owned trailers. They did **not** cover invalid UTF-8 values
or **HTTP-forbidden trailer names** (`Authorization`, `If-*`) — a class you find by asking "what
does Go's `net/http` treat specially in trailers?", never by re-reading your own test file.

**Range over the AXES, not just the values.** `STATUS: LIVE` — this task missed the same class
twice, and the second miss survived a `GOOD` review at 17 of 17 rubrics:

| axis | the miss it caused |
|---|---|
| **value bytes** | the obvious one — NUL, CR, LF, invalid UTF-8 |
| **library-reserved names** | 17 protocol-reserved names lived in a *different* map from the 21 HTTP-forbidden ones. The golden filtered only the latter, so the in-process path kept trailers all three wire protocols drop |
| **transport / RPC shape** | the defect appeared only on one transport and only on one RPC shape — a unary-only enumeration would have found nothing |

The second miss was caught by probing **98 input classes × 4 transports × 2 RPC shapes = 784
observations**, against a tree built from the golden and a second built from a real solver
implementation. 18 diverged, all one class, and the **golden** was the wrong one.

Write the enumeration down as a product of axes. An unlisted class is an ungraded requirement, and
an unlisted *axis* is a whole family of them.

### ①b The REVERSE direction — every assertion must trace to a contract sentence → catches R02

`STATUS: LIVE`, 2026-09-25. §① walks **contract → tests** and catches under-coverage. Nothing
walked **tests → contract**, so an assertion grading a rule the contract never states passed every
local gate.

A human reviewer on `concourse` asked for exactly this, and the AI assessment had independently
found the same two: *"Both are cases where a test checks something your instruction only hints at."*
The remedy they wanted was a contract sentence, not a test change — which means the defect is
cheap to fix **before** a push and needs Avocado **after** one.

**The check, one line per graded assertion:**

| assertion | the contract sentence that requires it |
|---|---|
| … | quote it, or the assertion is unsupported |

"Hints at" is not support. If the contract gestures at a behaviour without stating it, you have two
legal moves: **have Avocado state it**, or **drop the assertion**. Grading an unstated rule is R02,
and it reads to a solver as an unfair test.

Do this for **every** `fail_to_pass` entry and every assertion inside it. It is the cheapest gate on
this page and it is the one a human reviewer will run by hand.

### ② Golden-vs-contract differential → catches R12, the serious one

**Run the golden against the classes your tests do NOT cover.** If the golden violates the
contract on any of them, the task is broken no matter how green the oracle is.

The measured miss: *"A temporary check against the golden showed an `Authorization` trailer
survives Connect and gRPC-Web but is dropped by gRPC, violating the stated strictest-wire parity
rule."* **The golden itself did not satisfy the contract the instruction states.** That is R12,
and every local gate passed it.

This is the single highest-value check on this page. It costs one scratch run per class from ①.

### ③ The tested-cases-only mutant → catches R07

Write an implementation that handles **exactly the inputs your tests exercise and nothing else**.
If it passes the graded set, the set is thin and a partial solution will be paid for.

The measured miss: *"A partial solution that filters only the tested bad values and protocol-owned
keys can pass while still allowing legal-looking but HTTP-forbidden trailer fields to diverge."*

This is the same mutant discipline `C-drive/C3-harden.md` applies **after** a "too easy" verdict.
It belongs here too — running it before the first push costs one scratch implementation and saves
a whole validation cycle. → `C-drive/C3-harden.md` for the mutant-is-a-floor caveat.

## 9. CHECKLIST

```
[ ]  1. Requirement -> f2p mapping written, one row per requirement sentence (R06.3)
[ ]  2. Executed-vs-configured set difference computed and EMPTY (R06.1)
[ ]  3. Existing subsystem suite in pass_to_pass, not a spot-check (R06.2)
[ ]  4. parser.py fails on a failing test in the EXECUTED set; fails closed on empty
        fail_to_pass; parses named results, never an exit code (R07.1-3)
        proof: a deliberately-failing unlisted test and the reward it produced
[ ]  5. §2 D1 proof: for EVERY symbol B2 left unnamed, an alternative-spelling
        implementation scores reward 1.0 — declarations diff + reward line, per symbol
[ ]  6. R09: every f2p in a SINGLE process across >=5 seeds; seeds reported; not pinned
[ ]  7. §4 baseline diff at base_commit: every f2p fails, every p2p passes, SET-wise
[ ]  8. No f2p uncollectable pre-patch (ImportError / SyntaxError / build failure)
[ ]  9. Casing mirrors identical: `jq -e '(.fail_to_pass==.FAIL_TO_PASS) and
        (.pass_to_pass==.PASS_TO_PASS)' steps/*/tests/config.json`
[ ] 10. grader-lint clean: `python3 ~/.claude/skills/swebench-mt/grader-lint.py <task>`
[ ] 11. No refusal path anywhere in the grader (§6)
[ ] 12. R12: every "only / never / must not" sentence has its adversarial case built, run
        against the golden, and added as a graded test
[ ] 13. Golden change mirrored into EVERY copy; .patch md5 CHANGED (md5 before and after)
[ ] 14. Part II: the change landed in every steps/*/tests/config.json it applies to
        proof: per-file grep hit count for a token from the change
[ ] 15. B.2 sequential apply from base_commit succeeds for every step, in order
[ ] 16. B.4 top-level patch/test_patch non-zero; B.5 no cross-step duplicate dropping a test
[ ] 17. R11 wall clock recorded, well inside 900s
[ ] 18. A.1 golden grepped for class-level mutable state — and SAY you did
[ ] 19. MULTI-TURN steps-validation: (a) §3 three proofs run and pasted, proof 3 FAILS as
        required; (b) step 1's fail_to_pass appears NOWHERE in step 2's pass_to_pass;
        (c) every step ships BOTH patch and test_patch; (d) every allowed step-N encoding
        replayed through every later gold delta and required set, not just the oracle's
        preferred one; (e) cascade shape decided by RUNNING B.2, not by asserting §8;
        (f) prior_test_patch.diff byte-identical to step N-1's test_patch
[ ] 20. No write by this session to any instruction path  -> 00-ROUTER.md §5
        proof: `git status --porcelain -- '<task>/steps/*/instr*.md'` is empty
[ ] 20b. RE-RUN instruction-lint now that test_patch exists — B2 could only run
        half the D1 check before this act, and the half it could not run is the
        one that catches silent-contract + pinning-test (4 of 4 BAD_GRADING_WRONG)
        proof: `python3 ~/.claude/skills/swebench-mt/instruction-lint.py <task> <clone>`
               must report PASS, and must NOT print "no test_patch yet"
[ ] 19b. REVERSE TRACE: every graded assertion quoted against the contract sentence
        that requires it. "Hints at" is not support -- either Avocado states it or
        the assertion is dropped. An unstated graded rule is R02            [R02]
[ ] 20a. ANTI-WRONG: >=1 independently-written CORRECT implementation PASSES the
        real graded set (not the A3 sketch). 0 of N = BAD_GRADING_WRONG, do not push
        proof: the per-implementation reward lines, and which layer any failure sits
        in (Name/Value/Shape/Semantic) -- shape dominates and is easiest to miss
[ ] 20b2. BRANCH COUNT estimated and >=3: how many INDEPENDENT ways can a competent
        implementation be incomplete such that this graded set catches it?
        proof: the list, one line each. Test count is not branch count -- one task
        shipped 6 f2p tests that produced ZERO partial rows across 10 trials
[ ] 20c. CONTRACT-DOMAIN ENUMERATION written: every universal claim in the contract,
        with its input classes derived from the platform/spec -- NOT from your tests
        proof: the enumeration, and which graded test samples each class      [R06]
[ ] 20d. GOLDEN-vs-CONTRACT DIFFERENTIAL run on every class the tests do NOT cover
        proof: one scratch run per class; the golden must satisfy the contract on
        all of them. A violation here is R12 and the task is broken regardless
        of oracle 3/3 -- oracle only proves the golden passes YOUR tests        [R12]
[ ] 20e. TESTED-CASES-ONLY MUTANT written and run: an implementation handling
        exactly the inputs your tests exercise and nothing else
        proof: it must FAIL the graded set. If it passes, the set is thin       [R07]
[ ] 21. IF a graded assertion changed on a task with existing server results:
        routed to C-drive/C6-replay-verify.md before B4
```

```
HANDOFF B3
  EXIT:      base-commit set-difference output (§4); §2 alternative-spelling reward line
  CHECKLIST: <n of 21 ticked; every waived line with its reason>
  ARTIFACTS: steps/<N>/tests/{config.json,parser.py,run_script.sh,test.sh}; top-level tests/config.json
  FACTS:     f2p and p2p sets per step; the R09 seeds; the executed-vs-configured set
             difference; the §3 three-proof results; the cascade shape B.2 actually proved;
             the path the solver writes (so B4 can declare it as an artifact)
  OPEN:      any R08 symbol on the open route; any deliberate R06 residue recorded in
             TEST_RATIONALE.md; any instruction defect — Owner: Avocado/human
  NEXT:      B-build/B4-solution-env.md
             (graded assertion changed on an existing task -> C-drive/C6-replay-verify.md first)
```

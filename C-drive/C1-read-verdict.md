# C1 — Read the verdict: server state → written diagnosis

```
ACT:    C1-read-verdict
OWNER:  Claude
INPUT:  a task carrying any server verdict (router §1, state S9)
OUTPUT: a written diagnosis + plan at <task>/audit/plan-<utc>.md
EXIT:   every failing gate has a named root cause with a quoted evidence line
```

You are diagnosing, not repairing. Nothing in this act edits a task file. The output is one
markdown file and the HANDOFF block at the bottom of this page. Field authority — which field is
true and which lies — is **not** restated here: → `00-ROUTER.md` §2 and
`reference/R1-field-authority.md`, read before you believe any number on this page.

---

## FIRST: pull everything and write the ledger version entry

> **Freshness check — a dead remote reports everything as UNPUSHED.** `STATUS: LIVE`, 2026-09-24.
> Comparing local files against `origin/main` has a third failure mode beyond "stale" and
> "ahead": if the remote is unreachable, `origin/main` is a **stale local ref** and every file
> reads as unpushed. The HTTPS fetch fails silently here because a global `insteadOf` rewrite
> forces it — fetch over `ssh://git@github.com:22/...` and compare against `FETCH_HEAD`, not
> against `origin/main`.

`STATUS: LIVE`. Before diagnosing anything, pull the **complete** evidence set and append this
version's entry to `<task>/audit/REVIEW-LEDGER.md`. Commands, format and the carry-forward rules
are in `reference/R9-review-ledger.md`.

Pull all of it — `task errors`, `task show`, `job review`, the TBD full assessment, **the human
reviews** (`tasks reviews --full`, authoritative and carrying sourcing/novelty rejections that
`job review` never surfaces), and **every failing trial's artifacts including trajectories**. The
reviewer's prose is a summary; the quoted exception in `run-script-stdout.txt` is the evidence.

Then regenerate the carry-forward table: every finding ever raised on this task, with its current
status. **Anything still `OPEN` is input to this diagnosis, not history** — `B5` will block the
next push on it.

## 1. Freshness first — a stale read is not an attempt

**STATUS: LIVE.** If `commitSha` on the task record ≠ your latest pushed commit for that task,
you are reading results for code that no longer exists. Stop. Do not analyse, do not consume an
attempt (→ `00-ROUTER.md` §3).

```bash
codimango api tasks show <task> --json --no-cache   # commitSha, validationStatus, tbdReviewStatus
git log --format=%h -1 origin/main -- <task>
# both directions, CONTENT not SHA identity:
for f in <task>/steps/*/tests/config.json; do
  [ "$(git show origin/main:"$f" | md5sum)" = "$(md5sum < "$f")" ] \
    && echo "PUSHED   $f" || echo "UNPUSHED $f"
done
```

Calibration measures `origin/main`, not your working tree: a fix committed locally and never
pushed is invisible to the run, and the run then measures old prose against new tests. And
everything lands here by cherry-pick, which produces a different SHA for identical content — so
`git merge-base --is-ancestor` reports "unpushed" for work that is already live. **That produced a
confident false alarm on three tasks at once.**

If the remedy is a push, note that **you must not cherry-pick a commit that touches an
instruction file yourself** — that makes your shell the writer of a protected file and the
provenance pipeline scores the write log, not your intent. Hand that push to Vidit;
`Owner: Avocado/human`. → `00-ROUTER.md` §5, the iron-clad rule.

## 2. Capture the baseline before touching anything

You cannot prove absence of regression later without it. Write to a scratch file:

- per step, the full `fail_to_pass` and `pass_to_pass` **lists** — sets, not counts
- oracle result ×3, the no-op result, and exactly which tests passed in the no-op
- the server's `structuralCheckResult` — every check and its status
- the review verdict plus which rubrics currently **PASS**

`C2` proves non-regression against this file. A diagnosis that did not write one forces the
repair to guess what it is allowed to change.

## 3. Is there anything to analyse at all?

| Observation | Meaning |
|---|---|
| Structural check FAILED | **zero trials were dispatched.** Nothing else on the task is measurable. → `reference/R3-landmines.md`, then `C2` |
| `Oracle validation` red | skips every other gate. Diagnose it first regardless of what else is red |
| `Oracle validation: pending — No oracle trials run`, everything else green | an **unstarted arm**, not a defect. Trigger it; repair nothing |
| Arm shows `0/0`, `error`, `cancelled`, "no trials" | **infrastructure, not difficulty.** Never report it as a pass rate |
| `Insufficient legitimate sample` / `no countable runs` | infrastructure. Revalidate; do not touch the task |

**Measured:** one task's `0/10, 0/8, 0/0` was read as difficulty when every trial carried
`status=error` from `Classified failed command as ApiRateLimitError`.

---

## 4. Classify every trial — failures **and** passes — from downloaded artifacts

**STATUS: LIVE. Never infer from the results matrix alone.** Before classifying anything read all
four of: the instruction (what the agent was told), the graded test patch (what it was graded on),
`solution/` (what the real fix was), and the base tree (what it started from). **A verdict not
checked against all four is a guess.** Download commands, the anatomy of a trial artifact, and the
rule that only real trial output is evidence → `C-drive/C6-replay-verify.md` §1–§2: pull the
artifacts there, classify them here.

### The trial-signature table

| Signature in the artifact | Classification |
|---|---|
| `Required tests that passed: N` **equal to the no-op baseline** | the agent's work never counted — **artifact** |
| `refusing to grade` / any harness abort | grader refusal — **artifact** |
| `PARSER: no test result lines matched` | build failure or parser breakage — **artifact** |
| compile error in a test file | harness/patch defect — **artifact** |
| `NoMethodError` / nil-deref **inside a test helper** | over-pinned hidden schema — **artifact**, go to §5 |
| a clean assertion failure, 60-of-66 style | **genuine** |

## 5. The four-layer over-pinning taxonomy — SHAPE DOMINATES

**This is the highest-value diagnosis in either source pipeline. Read the exception text and
place the failure in a layer before you dispatch any repair — fixing the wrong layer costs a
full round each time.**

| Layer | What the test demands that the contract never stated | Signature in the trial output |
|---|---|---|
| **Name** | a specific accessor / method / key name | `NoMethodError: undefined method 'x'` on the *observable*, or a missing key |
| **Value** | a specific enum value, symbol, or String-vs-Class form | `expected :created, got :create` |
| **Shape** | the *container* or *element* type — Array vs Hash vs custom object | `undefined method 'fetch'` / `'key?'` / `'each'` **on the collection itself** |
| **Semantic** | genuinely different behaviour | a clean assertion failure on values that are all correctly named and shaped |

**The measurement.** On one task, widening **names** (round 1) left it at **0 of 9**. Widening
**values** (round 2) left it at **0 of 9** and did not move `spec_clarity`. The tests indexed the
observable with `.fetch(0)`, which requires an Array; the agent returned a custom object exposing
`#entries`. **8 of the 9 failures were that one line.** Widening **shape** took it to **6 of 9 in
a single round.** The agent's field names had been correct the whole time.

**A `NoMethodError` on the collection is never a reasoning failure** — before classifying any
failure as `reasoning`, confirm the test can even *read* what the agent produced. Name- and
value-layer widenings are cheap and feel like progress: record which layer you widened last round,
because **two consecutive rounds at the same layer with no movement is the shape signature.**

**Quote the recorded exception text in the diagnosis, never a summary of it** — and never a
self-authored variant, which is circular. → `C-drive/C6-replay-verify.md` §2.

## 6. The three buckets, and only one counts

| Bucket | Meaning |
|---|---|
| `reasoning` | The agent misunderstood the problem, missed the coupled requirement, or wrote something that does not work. The task did its job. **The only bucket that counts toward difficulty.** |
| `task_defect` | The agent wrote something a reviewer would accept and the task failed it anyway: the test asserts at a seam nobody named; the fixture is in a state no real caller would be in; the contract is ambiguous enough that the agent's reading is defensible; the test asserts on implementation rather than behaviour; the graded behaviour needs something the contract promised was present and was not. **Ours. Never counted as difficulty.** |
| `infra` | The agent was prevented from working: auth, network, a dead container, a runner that never handed it the repo. A per-step timeout too low for a slow agent is a timeout to raise, not difficulty to count. A trial that spent its time thrashing is **not** this — see question 3. |

Ask in this order:

1. **Would the agent's diff work in production?** If yes and it still failed → `task_defect`
   until you can show otherwise.
2. **Could a competent engineer, given ONLY the instruction, have known to do what the tests
   require?** If no → `task_defect`. Grep the instruction for the exact tokens the test requires;
   absence is proof.
3. **Did the agent engage** — read the right files, form a theory, act on it? If it thrashed or
   gave up early → `reasoning`.

Where unsure, choose `reasoning` for a failure — the conservative reading keeps a real defect
visible rather than inventing one.

### Emit one machine-readable line per trial

```
VERDICT <trial-id> <reasoning|task_defect|infra|earned|source_diffing|verifier_gaming|pattern_matching>
```

Every `task_defect` also gets a `FIX <tests|env|spec>` routing line — the label alone covers both
a suite that will not compile and a contract that never named a signature, and those are repaired
differently:

- `tests` — the graded suite is wrong: asserts at an unstated seam, collides with a file at base,
  is coupled to the reference, does not compile. → `C2`
- `env` — the image or runner is wrong: the suite never executed, a service was missing. → `C2`
- `spec` — the contract is wrong: never named a required signature, is defensibly ambiguous,
  promised something absent.

**Where both the suite and the contract are wrong, say `tests`** — the contract is written from
the suite, and `tests` is the one that is in scope.

**`FIX spec` is a report, not an action.** Record it under "Findings you cannot fix" with
`Owner: Avocado/human` and continue every other thread. Neither you nor Codex may write that
file, route prose into it, or draft the replacement text for someone else to paste.
→ `00-ROUTER.md` §5.

### Route each finding to the artifact that owns it

Before writing the plan, name for every finding the artifact it lives in and the act-file that
repairs it. Do not rebuild that mapping by reasoning — → `reference/R8-finding-to-file.md`
(finding / rubric id / gate string → artifact → act-file). **A finding with no route is a finding
you will re-diagnose next round.**

### Auditing *passing* trials is conditional

**STATUS: SCOPED-TO an imminent hardening decision.** Across roughly **fifteen** repair rounds it
never once changed a decision — the blockers were artifacts and grading defects, not leaking
passes. Run it only when a step reads saturated and `C3` is next: classify each pass `earned` /
`source_diffing` / `verifier_gaming` / `pattern_matching`. The last three are `task_defect` with
the label as the reason — a band built on them is a leaking task, not an easy one. **If any trial
is `verifier_gaming` the whole band is suspect until the harness is fixed and it is re-measured**
— one task read 4/5 and 5/5; after the verifier was hardened against pytest-hook and
flexible-equality tricks the same task read **2/5 and 2/5**.

### UNMEASURED is a verdict

**STATUS: LIVE.** A `0/N` assembled from artifacts — refusals, build breaks, errored arms,
`4/4` where the batch was 5 — is **UNMEASURED, not "too hard".** Write the word UNMEASURED in the
plan. Never let a downstream act loosen a contract on such a number. Detection commands →
`reference/R2-signal-integrity.md`.

## 7. Read both reviews — they are independent

```bash
codimango job review <task> --json | jq -r '
  .review.rubrics.items[] | select(.verdict|test("FAIL";"i")) | "[\(.id)] \(.dimension)\n   \(.evidence)\n",
  (.review.attemptResults[]? | "\(.model) \(.result)")'
```

`GRADING_FAILURE` vs `FAIL_REASONING` is the split that matters. **Fix every `GRADING_FAILURE`
before reading any pass rate** — two of them, from one over-specific fault injection, made every
other number on that task unreadable.

**TBR and the Agentic Review predict nothing about each other. STATUS: LIVE.**

| Evidence | What it kills |
|---|---|
| `tbd=pass` + `spec_clarity=Good` + **`BAD_GRADING_WRONG`** — **2 tasks** | "TBR pass means ready" |
| **`tbd=fail`** + **`GOOD / GENUINELY_HARD`, 17/17 rubrics** — **1 task** | "TBR fail means the task is bad" |

The second is the expensive one: that task was the best in the cohort and was blocked only by a
**0-byte top-level record**. Read both, always.

Four more reading rules:

- **Dimension bands are not stable run to run.** One task read `Good` in the morning and
  `Requires Some Guessing` that afternoon on nearly the same tree; the report comes from a
  reasoning model with roughly **20%** run-to-run deviation. **Treat a one-band move as noise
  unless the explanation text changed with it.** Ladder: `Good` > `Requires Some Guessing` >
  `Under Specified`.
- **All four dimensions `Good` but `tbd=fail`** ⇒ the reason is in the prose, not a rating field
  (`valid_task_rating_value` is often empty): `jq -r '.tbdReviewDetails.full_assessment'`.
- **A reviewer's suggested remedy is a hypothesis and its evidence can be stale.** One suggested
  locking a parent directory, which would have deleted the very contents its own assertion
  checked; one R08 finding described an assertion a previous round had already widened. Check the
  current file before acting on a quoted line.
- **If the two reviews contradict, find the shared root cause rather than ping-ponging.** Real
  case: TBR called chmod-based tests environment-sensitive while the agentic review demanded
  coverage of that same behaviour — the root cause was an agent-root / verifier-nonroot split,
  not the tests.

---

## 8. The plan file — `<task>/audit/plan-<utc>.md`

Write it **before** executing anything. Writing it down is what stops you repairing a number you
have not classified, and it is the record `C2` checks its non-regression against.

1. **State** — current SHA and freshness; the per-arm matrix, every failing cell labelled
   `artifact` or `genuine` with its quoted evidence line.
2. **Verdicts** — validation gates, TBR, Agentic Review, and which rubrics currently fail.
3. **Diagnosis** — one sentence per distinct root cause. Say plainly which numbers are
   **UNMEASURED** and must not be acted on.
4. **Actions** — numbered, each with: **owner** (Claude or Codex only — → `00-ROUTER.md` §5); the
   rubric(s) it should move **and the rubrics it could plausibly break**; how it will be verified;
   whether it risks regressing anything in the §2 baseline.
5. **Order** — **golden defects → grading defects → difficulty.** Never tune difficulty on top of
   a broken grader. Within grading, take `C2`'s packaging rungs first.
6. **Findings you cannot fix** — every finding whose only remedy is contract prose: what it says
   now, what the test requires, the impact, the direction of the remedy, `Owner: Avocado/human`.
   Do not act, do not delegate, and name them again in the HANDOFF. **A task can reach green on
   everything else while one stays open** — say that rather than calling the task blocked.

---

## 9. CHECKLIST — the reviewer-feedback check

Copy this into the plan file; tick each line with the command output or artifact that proves it.

```
[ ]  1. commitSha on the record == my latest pushed commit for this task
        codimango api tasks show <task> --json --no-cache | jq -r .commitSha
[ ]  2. origin/main content == my working tree, per file (md5, not SHA identity)   §1
[ ]  3. Baseline written to a scratch file: f2p+p2p SETS per step, oracle x3, no-op,
        structuralCheckResult, currently-PASSING rubrics                            §2
[ ]  4. Structural row read; if FAILED stop here — zero trials were dispatched      §3
[ ]  5. Oracle row read; red => diagnose first; "no oracle trials run" => trigger   §3
[ ]  6. Every arm's status checked for 0/0 | error | cancelled | no countable runs  §3
[ ]  7. Trial artifacts DOWNLOADED for every arm (C6 §1) — not read off the matrix
[ ]  8. Every trial classified against the signature table, failures AND passes     §4
[ ]  9. Every over-pinned failure placed in a LAYER: Name | Value | Shape | Semantic §5
        (a NoMethodError on the collection is Shape and is never `reasoning`)
[ ] 10. Every classification quotes a real exception line from the artifact          §5
[ ] 11. VERDICT line per trial; FIX <tests|env|spec> per task_defect; UNMEASURED
        numbers written as the word UNMEASURED                                       §6
[ ] 12. Each finding routed via reference/R8-finding-to-file.md                      §6
[ ] 13. job review read: GRADING_FAILURE vs FAIL_REASONING split recorded            §7
[ ] 14. tbdReviewStatus read WITH tbrNotFinalized; pending != failed; one-band
        dimension moves treated as noise unless the prose changed                    §7
[ ] 15. Reviewer evidence re-checked against the CURRENT file before acting on it    §7
[ ] 16. Plan written to <task>/audit/plan-<utc>.md with all six sections, actions
        ordered golden -> grading -> difficulty                                      §8
[ ] 17. "Findings you cannot fix" listed with Owner: Avocado/human; no prose drafted §8
```

---

## HANDOFF

```
HANDOFF C1-read-verdict
  EXIT:      <plan file path; and for each failing gate, the root cause + the quoted line>
  CHECKLIST: <n of 17 ticked; every waived line with its reason>
  ARTIFACTS: <task>/audit/plan-<utc>.md   (+ the baseline scratch file path,
             + the downloaded trial dir)
  FACTS:     commitSha measured; freshness verdict; per-trial VERDICT/FIX lines;
             over-pinning LAYER if any; which numbers are UNMEASURED;
             baseline f2p/p2p sets; R8 route per finding
  OPEN:      every "Findings you cannot fix" item, Owner: Avocado/human
  NEXT:      C2 (grading/artifact defect) | C3 (too easy) | C4 (too hard / false negative)
             | C5 (more than one task in flight) | park (router §4)
```

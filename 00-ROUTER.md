# 00-ROUTER — the only file you read first

SWE-bench-Pro task authoring, single-turn and multi-turn. Built by merging two
independently-measured pipelines (see `ledger/PROVENANCE.md`).

**How to use this.** Determine your state from §1 in one command. Open the ONE act-file
it names. Execute it. Emit its HANDOFF block. Stop. Do not read other files speculatively —
every act-file names the references it needs.

**Never believe a number before reading §2.** Most wasted rounds in both source pipelines
were spent repairing a field that was lying.

**And never read a green local gate as a green server gate** without knowing which of three it is
— the real check, a stand-in for it, or a proxy measuring a different subject. Five defects
reached the server on gates that were locally green, one per class.
→ `B-build/B5-preflight-push.md` §WHY LOCAL GATES MISS THINGS.

---

## 1. State → act-file

**Determine your state with this, in order. Stop at the first line that matches.**

```bash
# no task name in hand? you are local — walk S0-S3:
ls <task-dir>/steps/*/tests/config.json 2>/dev/null   # exists -> S5 or later
ls <task-dir>/steps/*/instruction.md    2>/dev/null   # exists -> S5
ls -d <task-dir>                        2>/dev/null   # exists -> S4
grep -lE 'EXIT: *SURVIVOR' .e2e/*/handoffs/*A3* 2>/dev/null      # a SURVIVOR -> S3
grep -lE 'EXIT: *NO SURVIVOR' .e2e/*/handoffs/*A3* 2>/dev/null   # -> A2 or A1, NOT B1
# ^ the NO-SURVIVOR line MUST be checked with an anchored pattern. `EXIT:.*SURVIVOR`
#   also matches "EXIT: NO SURVIVOR", so the loose form routed an exhausted repo
#   straight into B1 to build a task that does not exist. Caught on redo-lego.
ls .e2e/*/handoffs/*A2*                 2>/dev/null   # cards, unprobed  -> S2
# a repo chosen but no cards -> S1 ;  nothing at all -> S0
#
# NEVER route on filename existence. An A3 handoff exists whether or not a
# candidate survived; treating its presence as "a survivor card" sends the next
# agent into B1 to build a task that does not exist. Read the EXIT line.
# A3 must write exactly one of `EXIT: SURVIVOR` or `EXIT: NO SURVIVOR`.
# task name in hand:
codimango task show <task> --json
```

**Two states can match at once. Precedence, highest first — this is not optional:**

| # | If this is true | Go here, whatever else matches |
|---|---|---|
| 1 | `Oracle validation` red | `C2` — nothing else on the task is measurable |
| 2 | `Structural checks` red | `R3` → `C2` |
| 3 | **No written diagnosis at `<task>/audit/plan-*.md` for the current SHA** | **`C1`** — every C-act except `C1` requires a C1 diagnosis as input. A specific verdict (S12–S15) tells you what `C1` will conclude; it does not let you skip `C1`. |
| 4 | a current diagnosis exists | the act its plan names (S12–S15) |
| 5 | more than one task in flight | `C5`, which sequences the above per task |

So `BAD_GRADING_WRONG` on a task you were just handed is **S9 → `C1`**, not S12 → `C2`.
S12–S15 name the *destination* `C1` will route you to, not a shortcut past it.

| # | Observable state | Go to | Owner |
|---|---|---|---|
| S0 | No repo picked | `A-source/A1-repo-screen.md` | subagents ×N |
| S1 | Repo picked, no candidate cards | `A-source/A2-idea-generate.md` | MetaCode |
| S1b | Cards exist, no corpus verdict | `A-source/A4-corpus-prior.md` | Claude |
| S2 | Cards carry a corpus verdict, no probe measured | `A-source/A3-idea-gate.md` | Claude + Codex |
| S3 | Survivor card, no task dir | `B-build/B1-scaffold.md` | Claude |
| S4 | Dir exists, no contract | `B-build/B2-contract.md` | MetaCode / 1P |
| S5 | Contract written, no graded suite | `B-build/B3-grader.md` | Codex |
| S6 | Suite exists, oracle not 3/3 local | `B-build/B4-solution-env.md` | Claude |
| S6a | Oracle 3/3, no local band over VALID TERMINAL attempts | `A-source/A4-corpus-prior.md` | search the WHOLE org corpus by engineering concept. `task list --filter all` narrows to you; `gh repo list` caps at 1000 of 5,105. Both blind past our own work. |
| `B-build/B7-local-calibration.md` | Claude |
| S6b | Local band read, reviewers not yet run locally | `A-source/A4-corpus-prior.md` | search the WHOLE org corpus by engineering concept. `task list --filter all` narrows to you; `gh repo list` caps at 1000 of 5,105. Both blind past our own work. |
| `B-build/B7-local-calibration.md` | forecast, freeze, ladder. Classify every failure and read WHY before the band counts. PROVISIONAL — contradicts A3 §399 on purpose. |
| `assets/avocado/` + `tools/avocado-brief.sh` | the four Avocado prompt templates, a computed word cap, and a lint that refuses to send drafted prose. → `B2`. |
| `B-build/B6-review-gate.md` | Claude + 1 subagent per reviewer |
| S7 | Oracle 3/3 local, reviewers Accept, not pushed | `B-build/B5-preflight-push.md` | Claude |
| S8 | Pushed, `validationStatus=pending`, sha matches yours | **wait** — see §3 | — |
| S9 | Any server verdict, not yet diagnosed | `C-drive/C1-read-verdict.md` | Claude |
| S9b | `needs_revision`, or **any human review with scored rubrics** | `C1` for the diagnosis, then `C-drive/C7-revision-response.md` | Claude routes · Avocado owns the prose |
| S10 | `Oracle validation` red | `C-drive/C2-repair-grading.md` | Codex |
| S11 | `Structural checks` red | `reference/R3-landmines.md` → `C2` | Codex |
| S12 | `BAD_GRADING_WRONG` | `C2` — **remove an assertion** | Codex |
| S13 | `BAD_GRADING_WEAK` | `C2` — **add a test** | Codex |
| S14 | Step gate "too easy" / avocado >3/5 on any step | `C-drive/C3-harden.md` | MetaCode + Codex |
| S15 | Step gate "too hard" / 0 on every model | `C-drive/C4-loosen-salvage.md` | Codex |
| S16 | All five done-criteria green (§4) | **park it. Do not re-open.** | — |
| S16c | >10 commits, or a terminal condition | `C-drive/C8-retire.md` | Claude proposes · **Vidit decides** |
| S16b | A change to any graded artifact is proposed but unverified | `C-drive/C6-replay-verify.md` | Claude pulls, Codex runs |
| S17 | More than one task in flight | `C-drive/C5-cohort-loop.md` | Claude |

`Oracle validation` red **skips every other gate** — nothing else on the task is measurable
until it is green. Diagnose it first regardless of what else is red.

---

## 2. Field authority — which field is true, which lies

| Question | Authoritative source | Do NOT use |
|---|---|---|
| Did a gate pass? | the matching row of `validationDetails`, **matched by label** | row position — label sets differ by format |
| Task difficulty | `codimango job review <task> --commit <40-hex>` → `Task difficulty:` | `qualitativeResult.difficulty.classification` — **it contradicts the review** |
| Oracle / agent pass counts | `job list` / `trial list` | `oraclePassCount`, `agentPassCount` — read `null` for arms that finished |
| Quality review | `tbdReviewStatus` read **with** `tbrNotFinalized` | — |
| Golden built cold | `codimango bench tbd evalgt` run output (never written to the record) | any `validationDetails` row — **there is no Eval GT row** |
| Grader rejected vs agent wrong | `attemptResults[].result`: `GRADING_FAILURE` vs `FAIL_REASONING` | the aggregate pass rate |
| Patch applies / grades | `job list` filtered on `.config.env.__validation_stage` | — |
| Provenance | `provenanceCheck.agentWrites.agentModified` | `classifierResult.p3p` — hits 0.99 on clean human prose |
| **Avocado's pass count** | **`metacodePassCount` / `metacodePassTotal`** | **any `avocado*` field — they are null even when avocado ran 5 trials** |
| Was the quality review actually run? | `structuredReviewTbrAgenticReviewRawResult` — check `skipped_due_to_build_failure` | **`tbdReviewStatus` alone** — see below |
| Did the run even happen? | `quotaSkippedAt` — if set, **there is no verdict at that SHA** | any band field; they will be empty and read as 0 |

Five traps that each cost a real round:

- **`tbdReviewStatus: "fail"` is NOT a quality verdict.** Measured on two tasks 2026-09-24: it read
  `fail` while the quality review itself said `Accept` / `GOOD`, because
  `structuredReviewTbrAgenticReviewRawResult` was
  `{"build_error_category":"docker_auth","skipped_due_to_build_failure":true,"pass":false}`. The
  review never ran; the field reports the *infrastructure* outcome. On the other task every backing
  object was `null` and it still read `fail`. **Open the raw result before believing it.**
- **`quotaSkippedAt` means there is no verdict at all.** A task can carry it at the validated SHA
  while an *earlier* commit has real numbers — do not read the earlier commit's bands as this
  version's. There is no `S8` row for this state; treat it as "not run" and re-trigger.
- **`difficulty.classification` can deny that completed runs exist.** Measured: `"NO_DATA"`,
  `"No Opus/Claude agent runs yet"`, `passed: 0, total: 0` — while **five opus trials had
  completed** and `job review` returned `GENUINELY_HARD`. Worse than merely disagreeing.
- **`tbdReviewDetails` is `null` on every task checked**, so anything reading
  `.tbdReviewDetails.full_assessment` yields nothing. Use `codimango task reviews --full`
  (**singular `task`** — `tasks reviews` is rejected by the CLI).

- **`tbrNotFinalized: true` is PENDING, not failed.** Do not spend an attempt on it.
- **A missing `Agentic trial-output review` row does not mean the gate did not run.** Resolve per task with `job review --commit`.
- **`tbdReviewStatus` is the quality review, NOT the Eval-GT verdict.** Reading a review failure as a golden failure sends the repair the wrong way.
- **`presentInCurrent: false` on a provenance block is unreliable** — a one-token edit flips it while the block survives verbatim. Substring-match the logged blocks yourself.
- **A `0/N` built from artifacts is UNMEASURED, not "too hard."** Never loosen on it. → `reference/R2-signal-integrity.md`

---

## 3. What counts as an attempt

An attempt is **a completed diagnosis that produced a pushed commit.** A stale read, an
infra wait, or a round that shipped no change is not an attempt. Without this rule a
5-attempt budget evaporates on polling.

A review verdict is **bound to a commit SHA**. Re-running validation on the same SHA returns
the cached verdict — `task rerun` will look like it did nothing. A new commit is the trigger.
`rerun` is correct only when the prior run was infrastructure. Rerun budget: 3 per model.

**The rerun budget is NOT a limit on pushing.** It caps `task rerun` against an *unchanged* SHA.
A new commit is always a fresh trigger and always free. Do not ration pushes against it — that
was a misreading, and it argued for exactly the hoarding posture `A3` §0a now rejects.

### Ship early, repair on the server

`STATUS: LIVE`. The local instruments do not predict the band (`A3` §0a), the server does, and
`C1`–`C6` exist to repair a task from real trial data. So:

- **A task that clears the factual vetoes and has branch count ≥3 should be pushed, not polished.**
  The first server verdict is worth more than another local round.
- **Push the first version early**, then iterate on evidence. `C3` hardening on a 5/5 return is a
  normal round, not a failure — you have real trajectories to work from.
- **Do not wait on one task to finish before starting the next.** `C5` sequences a cohort; the only
  serial constraints are the Docker mutex and, per task, `B2 → B3 → B4 → B5`.
- **Unattended is the target.** Every act has a machine-readable `EXIT:` line and a `HANDOFF` so a
  run can be resumed by a different agent. Checkpoint often; that is what makes hands-free work.

### S8 — what "wait" actually means

`S8` is a **state, not an act**. There is no act-file; this is the whole procedure.

```bash
codimango task show <task> --json | jq '{commitSha, validationStatus}'
```

| What you see | Do |
|---|---|
| `commitSha` ≠ your pushed SHA | you are reading a stale record. Sleep 30m. **Not an attempt.** |
| `validationStatus = pending`, SHA matches | sleep 30m, re-check. **Not an attempt.** |
| `(no jobs on Nest)` | the job was never created — `codimango task rerun <task>` |
| any terminal status | leave S8 → **`C1`** |
| 3 consecutive checks, nothing moved, no jobs running | stop polling. Nothing is in flight; trigger a run or move to another task. |

Poll only while something is actually in flight. Polling an idle task forever is a no-op, and
the attempt budget is defined in §3 precisely so waiting never consumes it. If you hold other
work, go do it — `C5` exists to sequence exactly this.

---

## 3b. THE QUALITY LADDER — what to aim for, and what to sacrifice

`STATUS: LIVE`. The five criteria in §4 are a binary check. **This is the target**, and its order
tells you what to give up when you cannot have everything.

| rung | what it is | the gates that get you there |
|---|---|---|
| **L0** | structure bad · oracle bad · agentic review bad | — |
| **L1 — THE FLOOR** | **every validation passing except calibration, AND the agentic review says `GOOD`** | `preflight` clean · oracle 3/3 *stable* · `B3` §①②④ · `B5` p2p flake screen |
| **L2** | L1, plus **calibration 2/5–3/5 avocado on every step** | branch count ≥3 · two steps · step 1 carries real difficulty |
| **L3** | L2, plus the review rates it **`GENUINELY_HARD`** and the problem is one a maintainer would actually prioritise | a real defect or a real capability gap in code that matters |

**The floor is L1, and calibration is not part of it.** A task can miss the band and still be a
good task — 0/5 is accepted 81.2% of the time, 4/5 80.7%. What is *not* acceptable is failing
structure, oracle or the agentic review. Those are craft, not luck.

**`connect-go` was L0** — oracle 2/3, step gate too easy, and `BAD_GRADING_WEAK`. All three of the
things you control, wrong at once. That is the worst outcome available and it is the one we
shipped. Do not repeat it.

Read the ladder downward when you are deciding what to spend effort on:

- **Never trade L1 for L2.** Hardening a task whose grader is weak makes a bad task harder. Fix
  the grader first; that is what `B3` §①②④ is for.
- **L2 is 2/5–3/5, deliberately tighter than the 1–3/5 gate band.** Aim at the middle, not the
  edge — you are sampling five trials, and the edge of a band is a coin flip away from outside it.
- **L3 is not a harder contract, it is a better problem.** `GENUINELY_HARD` comes from the problem
  mattering, not from you withholding information — de-specifying was measured and changes nothing
  (`B-build/B2-contract.md` §6b).

**Delivery mode is autonomous, or minimal input.** A rung reached only because a human stepped in
mid-run is recorded as reached *with* intervention, and the intervention is a friction entry.

## 4. Definition of done — five surfaces, read each at its own source

| # | Criterion | Read at | Green when |
|---|---|---|---|
| 1 | Validation passing | `validationStatus` + every `validationDetails` row | `passing`, no row `failed`/`error` |
| 2 | Balance gate — **the rule differs by format, see below** | the `avocado [...]: N/M` figure in the balance detail | per the format's own rule |
| 3 | Agentic trial-output review | that `validationDetails` row | `passed` |
| 4 | TBD quality review | `tbdReviewStatus` + `tbrNotFinalized` | `pass` **and** finalised |
| 5 | Agentic Full-Task Review | `job review <task> --commit <40-hex>` | `Verdict: GOOD` |

### 0/5 IS NOT A FAILURE, AND IT IS NOT SYMMETRIC WITH 5/5

`STATUS: LIVE` — n=23,524, `.e2e/avocado-study/FINDINGS.md`. We had been treating "too hard" and
"too easy" as equally costly. They are not, by a factor of nearly two:

| avocado band | tasks accepted or in training |
|---|---:|
| in band | 84.9% |
| **0/5** | **81.2%** |
| 4/5 | 80.7% |
| **5/5** | **45.5%** |

**0/5 passes the single-turn gate outright** — verbatim: `Passed — avocado can pass at most 3/5 and
>=1 model solved (avocado: 0/5, opus: 1/5, gpt: 0/5)`. Of 462 tasks graded under the current
single-turn rule, **every 0/5 passed; every failure was over-ceiling.** In multi-turn a 0-rate step
survives whenever a third-party model shows a gradient on it — measured, 2-step `('in','0')` passes
92.6%.

On a 0/5 task the oracle still passes 98.8% of the time and **opus averages 44.2%**; only 16.8%
defeat opus entirely. "Too hard" usually means *avocado specifically* could not, not that the task
is broken.

**Aim away from 5/5, not toward the middle.** Erring hard is cheap; erring easy is what gets
rejected.

### Criterion 2 — SINGLE-TURN AND MULTI-TURN HAVE DIFFERENT RULES. Do not mix them.

**Read `format` in `task.toml` before reading any pass rate.**

| format | the rule | server's own words |
|---|---|---|
| **multi-turn** | per-step gate; in-band is **1–3 of 5 on avocado**, on *every* step; the last step is never exempt; the single-1.0 exemption needs 3+ declared steps and is one per task | — |
| **single-turn** | **"avocado not trivial AND ≥1 agent solved."** A single-turn task at **avocado 4/5 with opus 0/5 and gpt 0/5 PASSES.** | `Passed — avocado not trivial and >=1 agent solved` |

`STATUS: LIVE` — measured. Applying the multi-turn band to a single-turn task nearly had an
agent add a discriminator to a task that had **already passed** its balance gate, with two of
three models at 0/5. In both formats **avocado 0/5 is not itself a failure**: the gate needs one
pass and one fail on the *same* model, which may be Opus or GPT. Full decode →
`reference/R1-field-authority.md` §5.

**Before you push a revision, criterion 0 is the review ledger.** Zero `OPEN` findings from any
prior version → `B5` §GATE ZERO. The five criteria below judge the *current* run; the ledger is
what stops you re-shipping a defect the server already told you about.

3 and 5 are **different surfaces** — a task can pass 3 while 5 is stale, and can have no
row 3 at all while 5 returns `GOOD`. Never substitute one for the other.

**A task meeting all five is DONE.** Do not re-open it for a `TOO_HARD` label, a 0/N arm
inside a passing gate, or a "too easy" note in a gate that reports `passed`. A repair round
on an already-acceptable task has pushed it from `BAD_GRADING_WEAK` to `BAD_GRADING_WRONG`.

---

## 5. Ownership — enforced, not stylistic

### THE IRON-CLAD RULE

> **Claude and Codex NEVER touch `instruction.md` or `steps/*/instruction.md.` Not in any
> phase, not in any state, not to fix a typo, not to unblock a gate, not when a reviewer
> asks for it, not when it is the only thing standing between the task and green.**
>
> **Only Avocado (MetaCode) or Vidit by hand may write those files. There is no exception
> and no override.**

### THE SECOND IRON-CLAD RULE — Claude writes NOTHING in a task directory

`STATUS: LIVE`, 2026-09-29. Set after two tasks died of it.

> **Claude does not write any file under `<task>/`. Not `tests/`, not `solution/`, not
> `environment/`, not `task.toml`, not `README.md`. The one carve-out is `<task>/audit/**`.**
>
> **Codex makes every change except `instruction.md`. Claude validates, triggers runs, reads,
> routes and dispatches. That is the whole of Claude's role inside a task.**

**Why it had to become absolute.** `rustcrypto-x509` and `dropshot-websocket` both returned
`CONTAMINATED`, `agentModified: true`. On both, **`instruction.md` was CLEAN** — the first iron-clad
rule held perfectly. The kill was `tests/run_script.sh` and `tests/parser.py`, written by
`claude_code`.

Three things make this unrecoverable, and each one is why the rule has no soft version:

1. **The gate fires on the write LOG, not on current content.** `dropshot` failed at
   `matchScore` **0.061** — the file had almost entirely changed since and the record still
   stood. Rewriting it, renaming it, or having Avocado re-author it afterwards does not clear
   the write.
2. **The team-aai guard only fires on `Edit`/`Write`.** The concourse violation was
   `cp "$S/tests/config.json" "$D/tests/config.json"` — a Bash copy walks straight through
   (`feedback_tests_guard_bypass_via_bash`).
3. **Subagents do most of the writing.** 226 of 237 transcripts on this box are subagent
   transcripts. A rule the orchestrator follows and its delegates do not is not a rule.

Enforce it, do not trust it:

```bash
~/swebench-playbook/tools/authorship-audit.sh <task>    # exit 1 on any Claude write
```

Measured the day it was written: **all four live tasks failed it** — concourse 3 violations,
kustomize 10, plus the two already-contaminated. This rule is new precisely because we were
breaking it constantly without noticing.

This binds in every act-file `A1`–`C7`, including the loop, the auto-checks and the harness
work. It binds *indirectly* too: routing prose through another agent, a script, a heredoc,
or a patch file into that path is the same violation as typing it. Suggesting the exact
replacement text for someone else to paste is the same violation.

When a finding can only be fixed in that file:

1. Record it in the plan under **"Findings you cannot fix"** — what the prose says now, what
   the test requires, the impact, the direction of the remedy, `Owner: Avocado/human`.
2. **Continue every other item.** A task can reach green on all other gates with one open
   prose finding; say so plainly rather than calling the task blocked.
3. Name it again in the final report so it is not lost.

If a contract change *does* land (Avocado ran, or Vidit edited it), the task's other
artifacts are now suspect → `B-build/B2-contract.md` §contract-change re-audit.

### The rest of the matrix

| Artifact | Who may write it |
|---|---|
| `instruction.md`, `steps/*/instruction.md` | **Avocado (MetaCode) or Vidit only.** Never Claude. Never Codex. Never any 3P model. |
| **Everything under `tests/`** — `config.json`, `test.sh`, `run_script.sh`, `parser.py`, test patches | Codex or 1P/human. Provenance scores by **path**; one `claude_code` write there retires a task. |
| `solution/*`, `environment/Dockerfile`, `task.toml`, `README.md`, `audit/*` | Claude |
| Diagnosis, verification, mutants, git, pushes | Claude |

The guard fires on Edit/Write only — **script-written files slip through.** Ownership is
yours to honour, not the guard's to enforce. Violation protocol → `reference/R4-ownership.md`.

---

## 6. Concurrency

### The Docker mutex — the actual protocol

`STATUS: LIVE`. "One at a time" without a mechanism cost three repos their harness timing on
2026-09-22, because two acts both believed they were allowed to proceed.

```bash
flock /tmp/swebench-docker.lock <your docker command>          # blocks until free
flock -w 1800 /tmp/swebench-docker.lock <cmd> || echo "waited 30m, still held"
```

- **Holder identity:** write `<pair>/<act>/<pid>` to `/tmp/swebench-docker.holder` on acquire,
  truncate on release, so a blocked act can name who it is waiting on.
- **There is no TTL.** `flock` releases when the process exits, including on kill. A stale lock
  means a live holder — find it before breaking it.
- **Scope the lock to the Docker call, never to a whole act.** Holding it across an `A1` lane
  serialises the entire fan-out.

### `A1` fan-out versus the mutex — they conflict, and here is the resolution

`STATUS: LIVE`. `A1` is the canonical parallel act, yet its exit gate (G10 harness timing)
requires a container. Both rules cannot be obeyed as written. **Split the act:** run every
non-container gate in parallel across lanes, then queue *only* the G10 timing runs through the
mutex. A lane that cannot get the lock reports `G10: not measured — lock contention`, which is
an honest unmet line, not a waiver.

| Parallel-safe | Serial-only |
|---|---|
| repo screening — every gate except G10 | **G10 timing, and anything else spawning Docker** — parallel runs exhaust host memory |
| ideation, fork probes, novelty sweeps | `contract → solve → submit` for a given task |
| reading trial artifacts | repairs — one at a time, always |
| independent tasks in **separate worktrees** | shared git index; shared `/tmp` paths |

Use task-scoped temp paths (`/tmp/<task>-oracle.patch`, never `/tmp/oracle.patch`) — generic
names collide across parallel sessions and silently swap one task's oracle into another.

### ONE TASK PER AGENT CONTEXT. Never two.

`STATUS: LIVE`, 2026-09-24. An agent that has just diagnosed task A carries A's conclusions into
task B, and the failure is silent — it looks like speed.

Measured: one agent repaired `kustomize` (diagnosis: **packaging**, `test_patch` collided with a
pre-existing test) and then immediately diagnosed `crossplane` in the same context. The second
diagnosis was sound, but nothing in the record distinguishes "measured independently" from
"pattern-matched from the task I just finished". That distinction is the whole value of the
evidence.

Three reasons, in order of how much they cost:

1. **Judgement bleed.** Priors from task A are indistinguishable from evidence in task B. A
   diagnosis reached by analogy reads identically to one reached by measurement.
2. **Context exhaustion.** That agent spent 294k tokens across two tasks; the second got the
   depleted half, and the deepest work always comes late in an act.
3. **Unattributable friction.** When one context produces findings for two tasks, a defect in the
   record cannot be traced to which run produced it.

**So: one agent, one task, fresh context, its own reviewer.** If a second task needs work, that is
a second pair. Sequencing tasks is `C5`'s job and it sequences *pairs*, not acts inside one head.

The one exception: a **resume** of the same task after a stall, where recovering prior state is
the point.

### Building N tasks at once

The one orchestration shape that is proven. Do not improvise a different one.

| stage | fan-out | why |
|---|---|---|
| `A1` across N territories | **N agents in parallel** | independent; 3 lanes ran clean on 2026-09-22 |
| `A2` + `A3` per surviving repo | **parallel, one agent per repo** | independent; probes are cheap and read-only |
| `B1` scaffold | **parallel, separate worktrees** | no shared index, task-scoped temp paths |
| `B2 → B3 → B4 → B5` | **STRICTLY SERIAL per task, and one task at a time** | the contract→grader→solution chain is a two-way contract; and `B4`/`B5` spawn Docker |
| `C1` reads and artifact downloads | **parallel** | read-only |
| `C2`–`C6` repairs | **one at a time, always** | each spawns Docker; parallel runs have exhausted host memory and killed a poller mid-flight |

So: fan out hard through `A`, fan out through `B1`, then **queue**. One task is pushed before
the next one's contract is written. `C5` owns the queue once more than one task is live.

---

## 7. Hard stops

1. **Never source from a merged public PR**, regardless of obfuscation, contamination score, or post-cutoff timing.
2. **Never push or commit** unless the act-file you are executing says to, and then only paths under `<task>/`.
3. **Never act on an UNMEASURED number.** → §2, `R2`.
4. **Never edit an instruction file during C1–C5.** Record it, `Owner: human`, keep going.
5. **Never harden by making the contract vaguer.** Approach vaguer is good; interface never. → `B2`.
6. **Never let Claude write inside `<task>/`** — any path, any tool, any mechanism, including
   Bash `cp`/`mv`/redirect and including delegated subagents. `audit/**` is the only carve-out.
   Codex makes the change; Avocado owns `instruction.md`. → §5, `tools/authorship-audit.sh`.
7. **Never push a task with an OPEN finding in its review ledger.** Every finding from every
   prior version must be `FIXED`, `OBSOLETE-BY-PIVOT` or `WAIVED`, each with evidence.
   → `B-build/B5-preflight-push.md` §GATE ZERO, `reference/R9-review-ledger.md`.

---

## 8. Every act-file has a CHECKLIST and a HANDOFF

**CHECKLIST.** Every act-file carries a numbered, copy-pasteable checklist of its own steps,
each with the command or artifact that proves it done. Prose explains *why*; the checklist is
what you execute and what you report against. An act is not complete until every line is
ticked or explicitly waived with a reason.

**HANDOFF.** Every act-file ends by emitting:

```
HANDOFF <act-id>
  EXIT:      <the exit condition, and the command output proving it met>
  RUNG:      <L0|L1|L2|L3 believed reached, per §3b, and the evidence -- or "pre-push" with
              the rung you are targeting and what currently blocks it>
  UNVERIFIED:<every authoritative check that did NOT run, and every local gate that is a
              STAND-IN or a PROXY rather than the real thing -- see B5. A rung claimed
              over an unavailable check is claimed, not verified.>
  CHECKLIST: <n of m ticked; every waived line with its reason>
  ARTIFACTS: <paths written>
  FACTS:     <named facts the next act needs and cannot re-derive cheaply>
  OPEN:      <anything left undone, with an owner>
  NEXT:      <act-id per §1>
```

No act begins without the prior HANDOFF in hand. An act that cannot meet its exit condition
emits the HANDOFF anyway with `EXIT: NOT MET` and a reason — it does not improvise forward.

## 8a. The runbook is the contract. Deviations are defects in the runbook.

`STATUS: LIVE`

**Follow this playbook precisely.** If an act tells you to do something that seems wrong, do it,
and log the friction. Improvising a better local process destroys the only signal that tells us
which rule is broken — a run that quietly worked around three defects looks identical to a run
that had none.

**When the resulting task is not good enough, the runbook is what changes.** Not the standard, not
the gate, not this run's interpretation of a rule. The loop is:

```
follow precisely -> the task fails (locally or on the server)
                 -> find which act let it through
                 -> change THAT act, with the measurement attached
                 -> the next run is bound by the new text
```

Both directions of that loop are load-bearing. Three worked examples, all from 2026-09-22/23:

| the task failed on | the act that let it through | what changed |
|---|---|---|
| `avocado 5/5` too easy after a fork-1 override | `A3` GATE 8 let a `GATE 4` reading beat the fork veto | the exception was **falsified and reverted**; fork ≤2 is absolute again |
| `BAD_GRADING_WEAK` (R06/R07/R12) | `B3` never asked whether the golden satisfies the **contract**, only whether it passed our tests | three new `B3` gates |
| `Oracle 2/3` from a flaky inherited `p2p` test | `B5` screened `f2p` against base but never screened `p2p` for stability | the p2p flake screen |

**Rejecting an idea is cheap and correct; abandoning an idea shape is not.** A kill tells you this
candidate is dead. It does not tell you the *class* is dead — and the reason a kill is worth
writing down properly (`A3` kill ledger, `reversible-if`) is so the class can be re-entered when a
rule changes. Two kills on 2026-09-22 were later shown to rest on a broken probe.

## 8b. Two obligations that cross several acts

**Replay before you believe a change worked.** Any change to a graded artifact — a grading
repair, a hardening lever, a loosening — must be checked against *real prior trajectories*
pulled from past trials, not against a variant you wrote. A self-authored "representation
variant" ranges over the alias list the fix just added: it is green by construction and has
passed two consecutive rounds while the real blocker went untouched.
→ `C-drive/C6-replay-verify.md`. `C2`, `C3` and `C4` all exit through it.

**A contract change invalidates everything downstream.** If `instruction.md` changed, the
graded suite, the solution, the environment, the README and the rationale are all suspect
until re-checked against the new text.
→ `B-build/B2-contract.md` §contract-change re-audit.

**Every task keeps a versioned review ledger, and validation checks against it.**
`<task>/audit/REVIEW-LEDGER.md` — written by `C1` on every server verdict, gating `B5` before
every push. Pull the complete evidence set each version: gate strings, the full agentic review,
the TBD assessment, the **human** reviews, and **every failing trial's artifacts and
trajectories**. A finding stays OPEN across versions until it is fixed with evidence or proven
obsolete by a pivot — and a pivot needs the artifact *and* the requirement gone, not just the
artifact. → `reference/R9-review-ledger.md`.

`connect-go` came back `BAD_GRADING_WEAK` on three rubrics that were fully stated in its review,
while every local gate was green. Nothing forced the next version to answer them. This is that
mechanism.

**Tracing a finding to the file that owns it** → `reference/R8-finding-to-file.md`.

---

## 9. File index

| File | Boundary — what it alone owns |
|---|---|
| `A-source/A1-repo-screen.md` | repo → shortlist. Licence, size, issue density, peer dedup, AI-authorship, harness timing. |
| `A-source/A2-idea-generate.md` | repo → candidate cards. Axis/shape/technique composition. |
| `A-source/A3-idea-gate.md` | cards → survivors. Fork probe, outcome-variance probe, kill criteria, **the grader-namability gate**. |
| `B-build/B1-scaffold.md` | survivor → task dir. Scaffold, landmine patching, step decomposition. |
| `B-build/B2-contract.md` | the instruction. **The only file that states the naming rule.** |
| `B-build/B3-grader.md` | the graded suite. f2p/p2p, parser, test.sh, name-agnostic assertion proof. |
| `B-build/B4-solution-env.md` | `solve.sh`, Dockerfile, `task.toml`. Oracle to 3/3 local. |
| `B-build/B5-preflight-push.md` | local gates → first push. `preflight.sh`, scoped commit. |
| `C-drive/C1-read-verdict.md` | server state → written diagnosis. Trial forensics, plan. |
| `C-drive/C2-repair-grading.md` | artifacts, golden defects, `BAD_GRADING_*`. |
| `C-drive/C3-harden.md` | too easy. **Replay-a-real-passing-trial protocol.** |
| `C-drive/C4-loosen-salvage.md` | too hard, false negatives, salvage. |
| `C-drive/C5-cohort-loop.md` | which task to work, in what order, when to park. |
| `C-drive/C6-replay-verify.md` | replay real prior trajectories against a proposed change. `C2`/`C3`/`C4` exit through it. |
| `A-source/A4-corpus-prior.md` | search the WHOLE org corpus by engineering concept. `task list --filter all` narrows to you; `gh repo list` caps at 1000 of 5,105. Both blind past our own work. |
| `B-build/B7-local-calibration.md` | forecast, freeze, ladder. Classify every failure and read WHY before the band counts. PROVISIONAL — contradicts A3 §399 on purpose. |
| `assets/avocado/` + `tools/avocado-brief.sh` | the four Avocado prompt templates, a computed word cap, and a lint that refuses to send drafted prose. → `B2`. |
| `B-build/B6-review-gate.md` | run the server's own reviewers locally before pushing. The self-scored 17-axis walk is not a review. |
| `reference/R10-step1-calibration.md` | **MT priority.** step-1 f2p floor, the bimodal band, and why instruction length is not a calibration dial. |
| `C-drive/C8-retire.md` | park is not retire. The commit budget (accepted: median 6.5, **max 10**) and the terminal conditions. |
| `C-drive/C7-revision-response.md` | answer a HUMAN reviewer and re-submit: route each ask to its owner, independent re-read, full re-validation. |
| `reference/R1-field-authority.md` | full decode of every gate string and CLI field. |
| `reference/R2-signal-integrity.md` | is this number real. |
| `reference/R3-landmines.md` | scaffold + packaging traps. |
| `reference/R4-ownership.md` | provenance, violation capture. |
| `reference/R5-search-axes.md` | 18 axes + AXIS 19. |
| `reference/R6-fork-patterns.md` | P1–P6. |
| `reference/R7-algo-catalogue.md` | **QUARANTINED** — measured dead weight in 3/3 A/B runs. Research history only. |
| `reference/R8-finding-to-file.md` | review finding / rubric / gate string → the artifact that owns it → the act-file that repairs it. |
| `ledger/RUNS.md` | per-task history and evidence. |
| `ledger/RULES.md` | every live rule, its status, and the run that produced it. |

**No rule appears in two files.** If you need one stated elsewhere, link to it. Two copies
drift, and drift is the defect both source pipelines kept shipping.

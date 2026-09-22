# R3 — Landmines: scaffold and packaging traps

```
OWNER:  Claude (reference — pulled on demand; §A is also the B1 patch list)
INPUT:  a freshly scaffolded task dir, OR a red `Structural checks` row, OR a packaging
        complaint in a review
OUTPUT: a list of named traps present in this task. This file writes nothing itself.
EXIT:   every trap in §A and §B has been checked on this task and is either absent or patched.
```

Two sections. **§A scaffold** — what `codimango task init` ships broken, and the 17 checks
`preflight.sh` TIER 3 runs that no validator does. **§B packaging** — what survives scaffolding
and dies at review. None of these are style; every row is a measured failure. Router state
**S11** (`Structural checks` red) lands here, then goes to `C-drive/C2-repair-grading.md`.

---

## A. Scaffold traps

### A.1 — The eleven `task init` ships broken

`STATUS: LIVE`. Patch **all** of these on every new task.

| # | Trap | Fix | Why it bites |
|---|---|---|---|
| 1 | `tests/parser.py` regex hardcodes `tests/` | change to `tests?/` | upstream repos using singular `test/` match **zero** tests, and reward is **1.0 for free** |
| 2 | `tests/test.sh` reads UPPERCASE `FAIL_TO_PASS`/`PASS_TO_PASS`; the spec mandates lowercase | accept **both** casings, emit **both** in `config.json`, verify equality | `franz-go` would have forced reward 0 if only lowercase was updated; `test.sh` hard-errors when they disagree |
| 3 | Base image carries the `public.ecr.aws/docker/library/` prefix | use the bare Docker Hub name (`ruby:3.3-slim`) | the validator rejected the scaffold prefix in wave 1. Re-read the validator's `Base Image Registry` check rather than trusting this line |
| 4 | Multi-line `before_repo_set_cmd` | collapse to one line with `&&` | `test.sh` runs **only the last line**. Measured: `git reset --hard SHA\ngit clean -fd` lost the reset to `split('\n')[-1]` → state drift → tests passed against the wrong tree |
| 5 | `before_repo_set_cmd = "git clean -fd"` | set it to `""` when the oracle patch adds any `new file mode` | it **wipes files the oracle creates and files a valid alternative solution creates**. **`--exclude` is not sufficient — do not use it.** smoltcp's inline tests also made broad restores unsafe |
| 6 | Non-Python base images have no `python3` | add `python3` to `apt-get` on every Ruby/Node/Go/Rust image | `test.sh` and `parser.py` both require it |
| 7 | Dockerfile `git fetch --depth 1` | drop **only** `--depth 1` | structural WARN. `git fetch origin <sha>` already restricts to that SHA's ancestors; fetching by SHA does not pull post-base tips |
| 8 | `task.toml` missing `format` / `workstream` under `[task]` | MT: `format = "swe_bench_multi_turn"`, `workstream = "swe_public_repo"` | **every** scaffold required metadata repair |
| 9 | `category_usecase` set to generic English | use a valid enum value | valid picks: `semantic_bugs`, `api_misuse_bugs`, `boundary_condition`, `null_reference`, `concurrency_bugs`, `expose_interface`, `swap_implementation`, `architecture_refactor`, `dependency_addition`, `dependency_removal`, `algorithm_optimization`, `caching` |
| 10 | v9 `test.sh` may **lack the `test_patch` apply block** | insert it between `GOLD_CHECKOUT` and `TEST_FILES`, with clean → `--3way` → `--recount` fallbacks | symptom is high "Passed tests", low "Required tests that passed". `mlx` reported all four f2p missing until the block was added |
| 11 | Ruby `bundle config set --local path 'vendor/bundle'` | install gems system-wide (`gem install bundler && bundle install`) | **Harbor's cleanup wipes `vendor/bundle` and rspec vanishes at test time** |

Also measured, same class:

| Trap | Fix | Evidence |
|---|---|---|
| Reward derives from `$?` / `PIPESTATUS` | parse per-test results and set-compare; fail closed on empty or build failure | four wave-1 tasks needed this |
| Oracle patch contains test files | source changes only; tests live in `test_patch` | Dropshot oracle collided with `already exists in working directory` |
| New test file omitted from the diff | `git add -N <file>` before `git diff` | Protoc failed with `does not exist in index` |
| Slim image lacks native headers | add the leaf `-dev` package | WebAuthn needed `libssl-dev`; the Docker build had exited 5 |
| Go `pass_to_pass` uses the package only | use `<import_path>::<TestFunc>` | bare package IDs never match parser output and force reward 0 |
| Repeated test names overwrite | AND-aggregate **every** occurrence | Expat ran each name 12 times; last-result parsing could mask 1 of 12 failures |
| A Go graded test referencing new API in the package under test | put it in its own sibling package dir | a `package <pkg>` test referencing not-yet-existing API breaks compilation at base and takes the **entire** `pass_to_pass` set down with it |

### A.2 — The eval-GT root cause: a placeholder in the TOP-LEVEL `tests/config.json`

`STATUS: LIVE`. **This hit 16 MT tasks.**

The top-level `<task>/tests/config.json` *looks* like an inert stub. It is not: the eval-GT /
TBR harness **renders `/eval.sh` from it**, and it interpolates `base_commit` **unquoted**. A
placeholder value produces

```
/eval.sh: line 5: syntax error near unexpected token '||'
```

in **both** the baseline and the golden phase, scoring `F2P=0/0, SCORE 0.0` before a single
test runs.

**None of this is visible locally.** `harbor/trial/multi_step.py` never imports
`load_swe_bench_config`, so the oracle, `bench run` and calibration **physically cannot read
this file**: 3/3 green locally, `SCORE 0.0` on the server. An *absent* top-level file is worse
— it permanently zeroes the DQE review signal while eval-gt still looks fine.

Required, and checked by `preflight.sh` TIER 0:

- `base_commit` is a real 40-hex sha, identical in every step config **and** present in
  `environment/Dockerfile`
- `repo` is a real `owner/name`, not `<owner>/<repo>` — **the server's License gate reads this
  field, so a placeholder is a silent false-pass**
- no `<base_commit`, `<repo>`, `TODO_REPLACE`, `FIXME_SCAFFOLD` or merge marker anywhere in the
  tree. Excluding `config.json` from that scan is precisely what let 16 tasks through.

> **CONFLICT — UNRESOLVED.** OURS `MT-BATCH-KILL-CRITERIA.md:125` states *"Top-level
> `tests/config.json` is a STRUCTURE-CHECK STUB — do NOT populate it"*, and OURS
> `runbooks/2-build.md:593` labels it `# structure-only stub`. OURS `preflight.sh` TIER 0
> (lines 133–182) and OURS `2-build.md:836–842` say the opposite, and PEER `05` §B.4 requires
> `jq '.patch|length, .test_patch|length'` non-zero at the top level. The measured evidence
> favours a **real, non-placeholder** record on both sides (16 zeroed tasks here; three of
> eight empty/reconstructed aggregates and both zero-byte records at `tbd=fail` there). What
> the sources do **not** settle is whether the server requires **full non-empty aggregate
> `patch`/`test_patch`** for every MT format, or merely real identity fields plus a
> reviewer-facing aggregate. Populate identity fields always; treat the aggregate question as
> open and check the current server behaviour.

### A.3 — `preflight.sh` TIER 3: the 17 checks no validator runs

`STATUS: LIVE`. Run `~/.claude/skills/swebench-mt/preflight.sh <task-dir> --with-oracle`; exit 0
means safe to push. The list is here so you can reason about a failure without re-reading the
script.

| # | Check | Fails when |
|---|---|---|
| 1 | contamination canary | the scaffold's canary marker (line 1 of `environment/Dockerfile`) is still in the tree — server verdict `Benchmark canary string found`. **Strip it** |
| 2 | oracle patch carries source only | the `patch` touches a test file → collides with `test_patch` |
| 3 | new files in `test_patch` have `new file mode` headers | a file is added without one → **3-way merge fails** |
| 4 | mirrored casing keys agree | `fail_to_pass` ≠ `FAIL_TO_PASS` → `test.sh` hard-errors, **reward 0 on every trial** |
| 5 | reward is not derived from exit status | `$?` or `PIPESTATUS` appears in `test.sh` |
| 6 | Go ids are `<import_path>::<TestFunc>` | a Go id has no `::` → can never match |
| 7 | cascade delta | step N's patch is not the delta from step N−1 (warn: verify with **plain** `git apply`, no `--3way`, no fuzz) |
| 8 | `solve.sh` executable, no literal `/tmp` paths | not `chmod +x`, or a hardcoded `/tmp/...` → §C |
| 9 | `artifacts` declared in `task.toml` | **advisory only.** Without it you cannot extract what the models wrote and the gradient loop degrades to guessing |
| 10 | size floor | a step adds **< 20 net behavioural lines** — advisory; SWE-bench Pro excludes 1–10 LOC edits, mean is 107 lines |
| 11 | xfail/xpass handling in `parser.py` | upstream counts **XFAIL as PASSED** and **SKIPPED as MAINTAINED**; a parser that does not is a silent false-negative generator on every trial |
| 12 | `error2pass` | the parser never matches `ERROR`. A test that is **uncollectable** pre-patch (ImportError, SyntaxError, build failure) is not a legitimate `fail_to_pass` — this was **100% of SWE-Factory's false positives** |
| 13 | de-scaffolding lint | bullets, >1 heading, >4 emphasis markers, or >350 words in an instruction — advisory |
| 14 | contract coverage | the grader depends on a **new** symbol the instruction does not name → the candidate is the wrong shape. → `A-source/A3-idea-gate.md`, `B-build/B2-contract.md` |
| 15–16 | grading-correctness detectors (`grader-lint.py`) | private-state and nil-pin graders (R08 / `BAD_GRADING_*`) |
| 17 | instruction-lint | the instruction names a symbol the repo does **not** contain at base — by definition the answer handed over. Validated: open62541 (1/5) clean; graphiti (5/5) flagged for `include_decisions` / `not_allowlisted` |

Two additions carried in the same script, both worth running:

- **Verifier idempotency (TIER 3, blocking, ~50 ms).** The server's multi-turn runner calls
  `_maybe_run_step_baseline_precheck`: for the oracle agent it runs each step's verifier **once
  before `solve.sh`** and again after. `codimango bench run` uses `codimango-bench.par`, whose
  bundled `harbor/trial/multi_step.py` has **no such pass** — so a `test.sh` that is not
  idempotent scores **3/3 locally and 0/3 on the server**.
  `spire-workload-api-delivery-readiness` died exactly this way on 2026-09-18. Fix: purge the
  test-patch paths in `cleanup()`, **after** the reward is final.
- **TIER 4b server sequence replay (`--with-oracle`, ~90 s warm).** Replays baseline verifier →
  `solve.sh` → graded verifier in one container. Catches a step that **passes before `solve.sh`**
  (a no-op step — an eval-GT defect) and a step that cannot score 1 after a prior verifier pass
  in the same tree.

---

## B. Packaging traps

These survive scaffolding, pass the oracle, and die at review. **Measured over one drive cycle:
four of six gate flips came from mechanical artifact fixes, not test semantics** — one mirror
resync flipped three gates green in a single round, and test authoring never did better than
one gate in two rounds.

### B.1 — Hunk headers must equal their body line count

`STATUS: LIVE`. Every `@@ -0,0 +1,N @@` must equal the number of lines in its body. **A short
header makes `git apply` silently truncate the file, exit 0, and pass `--check`.** Nothing else
reports it.

Count with a prefix-aware parser, never an awk one-liner (→ `reference/R2-signal-integrity.md` §8).

### B.2 — Who reads which artifact

`STATUS: LIVE`. The grader and the reviewer do not read the same files. Several findings are
about an artifact the reviewer **constructs**.

| Consumer | Reads |
|---|---|
| **Grader** (`test.sh`) | `/tests/config.json` — the **embedded** `patch` / `test_patch` |
| **Agentic reviewer** | the on-disk `tests/test_patch.diff`, and a `/review_materials/code_patch.diff` **it builds itself** by concatenating the per-step patches |

So before treating any packaging finding as real, ask: **does this artifact exist in the repo,
or does the reviewer build it?** A complaint that "the aggregate patch does not apply" may be
about a file **no one ships**. And a task whose grading is already correct can fail **four
rubrics** because the reviewer read a stale on-disk mirror — grading was right for days while
the reviewer described a contract that no longer existed.

### B.3 — The mirror inventory

`STATUS: LIVE`. Every value that exists in two places is a drift hazard, and drift is invisible
to the oracle, to the hunk-header check and to `git apply`. Map the whole graph:

```
config.json .patch        ↔  solution/reference_patch.diff  ↔  solution/gold_patch.diff
                          ↔  the patch embedded in solution/solve.sh
config.json .test_patch   ↔  tests/test_patch.diff
steps/N/.../prior_test_patch.diff  ↔  step N−1's .test_patch
top-level tests/config.json        ↔  the step it is supposed to mirror
```

Measured: **2 of 9 tasks carried drift**, and in one case it was the entire cause of four
failing rubrics.

**`sync_config.py` is a live landmine.** It typically assigns `config["patch"]` and
`config["test_patch"]` from the on-disk files, treating **disk as the source of truth** and
overwriting the embedded values. On two tasks, running it would have silently reverted a landed
fix. After any repair, confirm the script is a no-op.

**A field that SHRANK when your change only adds is the signal.** Diff each `patch` /
`test_patch` length against `HEAD`, not only against the sibling step. The measured case: a
round added three normalisers to all three configs; the next round, authored from the
pre-widening file, **dropped all three from step 2 and the top-level record** (13657 → 13269 B)
while step 1 kept them. The asymmetry read downstream as *"step 2 too hard, no model passed
it"*. Every conventional check passed.

### B.4 — Step patches must compose; the top-level patch is derived, never concatenated

`STATUS: LIVE`. The requirement is a **property, not a format**:

> **Step N's patch must apply cleanly on top of the state left by step N−1**, and applying every
> step in order from `base_commit` must produce the final solution.

A step patch touching no file an earlier step touched satisfies this whether or not it is
cumulative. A step patch that *does* touch such a file must be **incremental** — the diff
against the previous step's state. Both shapes ship: paper-trail's step 2 edits a file step 1
created and composes; resque's does not — `error: patch failed: lib/resque/job.rb:73`, because
both steps rewrite one file from the same base, so **no order exists in which both apply**.
Rated *Other Major Quality Issues*.

**Every task in one cohort (8 of 8) had the risky shape**, so a static check is not enough:

```bash
git -C <co> checkout <base_commit>
for s in 1 2 ... N; do
  git -C <co> apply --unidiff-zero --check <step_${s}_patch> || exit 1
  git -C <co> apply --unidiff-zero        <step_${s}_patch>
done
```

The top-level `patch` must be a **single, self-applying diff** — never a concatenation. If every
step patch is cumulative-from-base the last one already is that diff, but **check, do not
assume**. Otherwise derive it mechanically (never hand-write it): apply the steps in order,
`git add -A`, `git diff --cached --binary`. Deriving it this way also emits real context, so it
then applies with **plain `git apply`**, no `--unidiff-zero`.

### B.5 — The empty top-level record

`STATUS: LIVE`. Nothing fails locally. One task shipped with `patch` and `test_patch` both at
**0 bytes**; the reviewer then built its own aggregate from the step patches, which
create-then-edited one file and duplicated a spec file across both halves — **two separate
rubric complaints**.

**Three of eight tasks shipped an empty or reviewer-reconstructed aggregate, and both tasks with
a 0-byte top-level record were `tbd=fail`** — including one scoring **17/17 rubrics and
`GOOD / GENUINELY_HARD`** on the Full-Task review. A perfect task held up by an empty config
field. Populating an empty instance record took one task's `tbd` from fail → pass.

Set `.test_patch` to the step whose test patch already contains every spec file exactly once,
and derive `fail_to_pass` by **running** — do not assume it is the union of the steps.

### B.6 — Cross-step duplicate files: the later copy wins, silently

`STATUS: LIVE`. Any file created by more than one step's `test_patch` is a drift hazard.
Measured across one cohort: **6 of 8 tasks carried such a duplicate and every one diverged;
three shrank.**

The signature case: a concatenated aggregate contained one spec file **twice** — a 176-line
version including a 9th negative test (*"does not expose the circuit breaker behavior"*)
followed by a 172-line version without it. `git apply` exits 0, the later definition wins, **and
that negative test is silently dropped from the graded set.** The reviewer called it *"a
cosmetic diff defect"*; it is lost coverage. `verify_task.sh` reports it only as a **WARN**
(*"N file(s) re-created by a later step — aggregate applies, last step wins"*) — do not dismiss
that warn.

```bash
python3 -c "import json,glob,collections;c=collections.Counter()
[c.update({l[6:] for l in (json.load(open(f)).get('test_patch') or '').split(chr(10)) if l.startswith('+++ b/')}) for f in sorted(glob.glob('<task>/steps/*/tests/config.json'))]
print([k for k,v in c.items() if v>1])"
```

Compare the shared files' **bodies**, not their names:

- **Legitimate divergence**: a step-1 negative control asserting step-2 behaviour is *not yet*
  present must be dropped by step 2, because it correctly fails once step 2 lands. Name it in
  the summary and exclude it from the top-level lists.
- **Everything else is drift.** A step-2 copy missing helpers the step-1 copy has will fail
  step-1's own tests at step 2 — which then reads as step-2 difficulty.

### B.7 — Verify mechanically before reporting done

```bash
git -C <base_checkout> checkout <base_commit>
git -C <base_checkout> apply --check <top_level_patch>
```

Two other multi-turn tasks scored `Good` on this axis, so **a concatenated top-level patch is a
defect you introduced, not an artifact of the format.**

Run §B.3–B.6 **across every task in the cohort at once**, not task by task. The empty-record
defect was only obvious once two failing tasks were seen side by side; per-task triage reads it
as a one-off.

---

## C. Generic `/tmp` paths collide across parallel sessions

`STATUS: LIVE`. `/tmp/oracle.patch` and `/tmp/tests.patch` are written by every parallel task
session, and have **silently swapped one task's oracle into another**. Always use task-scoped
paths: `/tmp/<task>-oracle.patch`, `mktemp -t <name>.XXXXXX`. `preflight.sh` TIER 3 check 8
flags a literal `/tmp` path inside `solve.sh` for the same reason.

---

```
HANDOFF R3
  EXIT:      every trap in §A and §B checked on this task; `preflight.sh --with-oracle` exit 0
  CHECKLIST: n/a — lookup table, not an act (`00-ROUTER.md` §8)
  ARTIFACTS: none written by this file; the patches land in the task dir
  FACTS:     which traps were present, and what each was patched to
  OPEN:      §A.2 CONFLICT — whether the top-level aggregate patch/test_patch must be non-empty
             for every MT format is not settled by either source
  NEXT:      `C-drive/C2-repair-grading.md` if you came from a red `Structural checks` row;
             otherwise back to `B-build/B1-scaffold.md` or `B-build/B5-preflight-push.md`
```

# B1 — SCAFFOLD

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
OWNER:   Claude
INPUT:   a survivor card + its HANDOFF from A-source/A3-idea-gate.md
OUTPUT:  a task directory under the tasks repo
EXIT:    the directory exists and every known scaffold landmine is either patched
         or recorded in the HANDOFF with an owner (see §2 ownership split)
```

`codimango task init` produces a directory that **validates locally and grades wrongly**. Every
item in §2 is a silent defect: no validator catches it, the task ships, and the number you read
back is a lie. Patch them at scaffold time. Do not defer.

## 0. The command, and the one ownership carve-out

```bash
codimango task init <task-name> --format swebench-multi     # or swebench for single-turn
```

Run it from the tasks repo root. It creates the directory tree, including **empty placeholder
`steps/*/instruction.md` files**.

**That placeholder creation is the single carve-out to the iron-clad rule, and it is narrow.**
`STATUS: LIVE`

> The rule (`→ 00-ROUTER.md` §5) bans Claude and Codex from writing contract prose, including
> indirectly through a script. Running the official scaffold tool, which materialises an **empty**
> file at that path, is **not** a content write and is permitted — the tool is the author of the
> placeholder, and there is nothing in it to attribute.
>
> What remains absolutely banned: **the first byte of actual content at that path must come from
> Avocado or the human.** Do not seed it with a heading, a TODO, a template, a copied card
> paragraph, or a "structure for Avocado to fill in". Do not `sed`/`cat`/heredoc into it. Do not
> hand Avocado a draft to edit. If the tool ships a non-empty template, leave the template bytes
> untouched — do not improve them.
>
> Verify before you hand off, and paste the output:
> ```bash
> find <task> -name 'instr*.md' -size +0 -exec echo "NON-EMPTY: {}" \;
> ```
> Any hit at `B1` means someone wrote content that should not have. Stop and report it.

Nothing here decides *what* the task is. That was settled by the card. Do not re-open it.

---

## 1. The layout you are creating

### 1.1 Multi-turn (`swe_bench_multi_turn`) — the default

```text
<task>/
  task.toml
  environment/Dockerfile          # SHARED across all steps
  tests/config.json               # top-level — see B4 §8, the status of this file is CONTESTED
  steps/1_<name>/
    instruction.md
    solution/solve.sh
    tests/{config.json,parser.py,run_script.sh,test.sh}
  steps/2_<name>/
    instruction.md
    solution/solve.sh
    tests/{config.json,parser.py,run_script.sh,test.sh}
```

**No top-level `instruction.md`. No top-level `solution/`.** The server `Structure` check fails
on either. `STATUS: LIVE`

`[[steps]]` ordering in `task.toml`:

| Field | Step 1 | Step N>1 |
|---|---|---|
| `name` | must match the directory name **exactly** | same |
| `dependencies` | `[]` | `["<previous step name>"]` |
| `min_reward` | `1.0` | `1.0` |
| `inherit_prior_session` | absent / `false` | `true` |

There is **no** `format =` field inside `[[steps]]`. It lives once, under `[task]`.

### 1.2 Single-turn (`swe_bench_single_turn`) — fallback only

Attempt multi-turn first and work the four-rung ladder before downgrading; a multi-turn task is
worth roughly 3x. Vidit's framing: **one single-turn ≈ 0.3 of a multi-turn, and shipping
something beats shipping nothing.** `STATUS: LIVE`

| | multi-turn | single-turn |
|---|---|---|
| `format` | `swe_bench_multi_turn` | `swe_bench_single_turn` |
| `track_assignment` | `swe-bench-multi-turn` | `swe-bench-external-repos` |
| `workstream` | `swe_public_repo` | `swe_public_repo` |
| layout | `steps/<N_name>/...` | **no `steps/` dir at all** |
| `instruction.md` | one per step | one at task root |
| `solution/solve.sh` | one per step | one at task root |
| top-level `tests/config.json` | contested — B4 §8 | **THE config: all 7 fields required and real** |
| `[[steps]]` | required | **omit entirely** |
| calibration | per-step gate | whole-task |

The 7 single-turn fields: `repo`, `instance_id`, `base_commit`, `patch`, `test_patch`,
`fail_to_pass`, `pass_to_pass`.

### 1.3 `track_assignment` is derivable — do not ask for it

Read it off the manifest's own `format` using the table in §1.2. It is **not** an AMT allocation
and does not require asking a human. Never use an org label (`applied-ai-labs`,
`meta-consulting`, `eval-instruction-following`) as `track_assignment`. `STATUS: LIVE`

---

## 2. The `task init` landmine checklist

**Ownership split — read before patching.** The `Who` column below is binding and is not yours to
adjust → `00-ROUTER.md §5`. Two shipped tasks failed provenance with `Unauthorized third-party
model authorship detected` — `go-zero-mr-cancellation-accounting` and
`object-rs-atomic-rewriter-modify` — on **`tests/run_script.sh`**, with `contentByteExact: true`,
`matchScore: 1`, `presentInCurrent: true`, `agentPlatform: claude_code`. The restriction is the
**directory**, not the assertions, and a Bash heredoc or a generated script is the same
violation. → `reference/R4-ownership.md`

So: patch the `Claude` rows now. Record every `Codex` row verbatim in the HANDOFF `FACTS` block
so `B3` lands it. That is what "patched or recorded" means in the exit condition.

| # | Landmine as shipped | Fix | Who | Measured cost |
|---|---|---|---|---|
| 1 | `tests/parser.py` regex hardcodes `tests/` | accept `tests?/` — upstream often uses singular `test/` | Codex | stock scaffold matched **zero** tests and could award reward **1.0** |
| 2 | `tests/test.sh` reads UPPERCASE `FAIL_TO_PASS`/`PASS_TO_PASS`; the spec mandates lowercase | accept **both** casings and emit both in `config.json`; verify equality | Codex | `franz-go` would have forced reward 0 if only lowercase was updated; disagreeing keys make `test.sh` hard-error → reward 0 on every trial |
| 3 | Base image carries the `public.ecr.aws/docker/library/` prefix | use the bare Docker Hub name (`ruby:3.3-slim`); re-read the validator's `Base Image Registry` check rather than trusting this line | Claude | validator rejected the scaffold prefix in wave 1 |
| 4 | multi-line `before_repo_set_cmd` | collapse to one line with `&&` | Codex | `test.sh` executes only the **last** line |
| 5 | `before_repo_set_cmd = "git clean -fd"` | if the oracle patch adds any `new file mode`, set it to `""`. **Do NOT use `--exclude`** | Codex | wipes files the oracle creates *and* files a valid alternative solution creates; smoltcp's inline tests also made broad restores unsafe |
| 6 | non-Python base image has no `python3`, but `test.sh`/`parser.py` need it | add `python3` to apt-get on every Ruby/Node/Go/Rust image | Claude | `parser.py` cannot run at all |
| 7 | Dockerfile `git fetch --depth 1` | drop **only** `--depth 1` — `git fetch origin <sha>` already scopes to that SHA's ancestors | Claude | structural WARN |
| 8 | `task.toml` missing MT metadata | `[task] format`, `workstream`, `track_assignment` per §1.2 | Claude | every scaffold required metadata repair |
| 9 | `category_usecase` set to generic English | closed enum: `semantic_bugs`, `api_misuse_bugs`, `boundary_condition`, `null_reference`, `concurrency_bugs`, `expose_interface`, `swap_implementation`, `architecture_refactor`, `dependency_addition`, `dependency_removal`, `algorithm_optimization`, `caching` | Claude | structural fail |
| 9b | `category_subdomain` set by guess | also a closed enum, and the valid list is printed **only** by `bench validate`. `systems_and_infra` is valid; `backend_and_distributed_systems` is not | Claude | structural fail |
| 10 | v9 `test.sh` may **lack** the `test_patch` application block | insert it between `GOLD_CHECKOUT` and `TEST_FILES`, with clean → `--3way` → `--recount` fallbacks | Codex | symptom is high "Passed tests", low "Required tests that passed"; `mlx` reported all four f2p missing until the block was added |
| 11 | Ruby: `bundle config set --local path 'vendor/bundle'` | install gems system-wide (`gem install bundler && bundle install`) | Claude | Harbor cleanup removed `vendor/bundle` and rspec vanished at test time |
| 12 | reward derived from `$?` / `PIPESTATUS` | parse per-test results and set-compare; fail **closed** on empty parse or build failure | Codex | four wave-1 tasks needed this correction |
| 13 | oracle `patch` contains test files | source changes only; tests belong exclusively to `test_patch`. Generate with explicit paths (`git diff <base> -- lib/ src/`), never a bare `git diff` | Codex | dropshot: `error: <testfile>.rs: already exists in working directory` → `Gold test patch could not be applied` |
| 14 | a brand-new test file is invisible to `git diff` | `git add -N <file>` before diffing | Codex | protoc-gen-go-mcp: `does not exist in index` → `could not apply test_patch - refusing to grade` |
| 15 | slim image lacks native-extension headers | add the **leaf** `-dev` package from the error trace | Claude | webauthn-ruby needed `libssl-dev`; the Docker build had exited 5 |
| 16 | Go `pass_to_pass` uses a bare package id | use `<import_path>::<TestFunc>` | Codex | bare package ids never match parser output and force reward 0 |
| 17 | a repeated test name overwrites its earlier result | AND-aggregate **every** occurrence | Codex | Expat ran each name 12 times; last-result parsing could mask 1 failure of 12 |
| 18 | the contamination canary | strip it. It has **three homes**: line 1 of `environment/Dockerfile`, and the headers of `tests/test.sh` and `tests/run_script.sh`. `preflight.sh` greps the whole tree, so do not spot-check the Dockerfile | Claude + Codex | `Benchmark canary string found` is an automatic contamination fail |
| 19 | Go: the hardened `run_script.sh` pins `PATH=/usr/local/sbin:...:/bin`, which has no `/usr/local/go/bin` | `export PATH="/usr/local/go/bin:$PATH"` | Codex | `go: command not found` → empty parser output → **oracle 0/3**, indistinguishable from a broken task. Cost a full build cycle. That PATH shape was written for Ruby/Python |
| 20 | Go: a graded test referencing not-yet-existing API declared `package <pkg>` | put it in its **own** sibling package dir (`core/limit/tokendegradation_test/`), or reach the new API through `reflect.MethodByName` so the package compiles at each baseline | Codex | breaks compilation of the whole package at base and takes the **entire** `pass_to_pass` set down with it. Structural, not stylistic |
| 21 | Reward Provenance warns on a plain `$?` grep | it clears only when **every** `$?` read is gone, including one inside a trap. A bash EXIT trap that does not itself call `exit` preserves the status anyway, so removing them is behaviour-preserving | Codex | corpus-wide — an already-submitted task emits this identically |

`STATUS: LIVE` for all 21. Every one is a correctness failure observed in a real task, not a
style preference. Packaging traps found *after* the scaffold exists →
`reference/R3-landmines.md`.

---

## 3. Step decomposition and the over-execution guards

Step 1 must fail if later-step artifacts already exist; later steps must reassert earlier
behaviour. But **do not leak held-out tests through the inherited session.**

Measured: `net-imap` step 1 left its graded test file in the container. In **2 of 3** trials a
later agent interacted with it — one read it, one deleted it. The fix removed the graded file
after recording reward, and the absence was verified in-container. `STATUS: LIVE`

- [ ] Step 1 asserts later public artifacts are absent **without naming hidden implementation
      details**.
- [ ] `inherit_prior_session = true` on step 2+ only.
- [ ] Each verifier removes prior held-out test files before copying its own.
- [ ] Guard tests do not force the agent to delete whole test directories — an early `franz-go`
      shape induced exactly that reward-hack behaviour.

Cross-step consistency, and why it is decided here rather than later: **every representation
step 1 allows becomes an input contract for every later step.** `jsonschema-schema-subsumption-checker`
relaxed step 1 to allow `"number"` as `{number}` or `{number, integer}`; step 2 still assumed the
wider set, and under the newly valid narrow encoding the oracle's own step 2 failed **3 of 8**
required tests. After adding numeric closure and removing a private lossy-lowering pin, the
oracle and two independent encodings passed **14/14**. `STATUS: LIVE`

Whether step N's patch is cumulative or a delta is **contested** — → `B3-grader.md §9`. Do not
settle it here.

---

## 4. `artifacts` — suggested default, never a gate

```toml
artifacts = ["/app/path/the/solver/writes.ext"]
```

Captures what each model actually wrote, which lets the tightening loop dry-run a candidate test
against real implementations instead of re-running trials. Add it at scaffold time — one line,
paths derivable from the oracle patch.

**Never block on it.** Nothing server-side requires it: a task without it validates, calibrates
and is accepted normally, and **none of our 5 accepted tasks has an `artifacts` line**.
`preflight.sh` reports it ADVISORY and never exits 1. Failure mode if the path is wrong: nothing
is captured and nothing breaks.

`STATUS: UNVALIDATED-PRIOR` — **0 of 38 tasks declare it, so we have never actually pulled one.**
The throughput claim comes from a peer's writeup, not our own measurement. Test it on one task
before relying on it. Do not add it to an accepted, rejected or `validation=passing` task —
editing `task.toml` there means a new commit and re-validation on something already decided.

---

## 2b. Row 22 — a live `origin` remote is a SOLUTION-LEAKAGE vector

`STATUS: LIVE`, 2026-09-23. **Not in the 21 rows above, and it was found in every one of the 11
tasks in one author's repo.** `allow_internet = true` is often required (a module proxy, a package
index), and the scaffold leaves `origin` configured — so a solver can `git fetch origin` and read
the upstream fix directly. This is the R05/R07 `BAD_LEAKAGE` that failed `redb` and got `sqlfluff`
rejected.

```dockerfile
# after the fetch/checkout, before the image is finalised:
RUN git remote remove origin
```

**Verify in the REBUILT image, not the Dockerfile:**

```bash
git remote -v                  # empty
git fetch origin main          # must be fatal
git rev-list --all --count     # base ancestry only
```

Check this on existing tasks too — it is invisible to every other gate.

## 2c. Row 19 amended — `ENV PATH` does not survive `bash -l`

`STATUS: LIVE`, 2026-09-23. A login shell re-reads `/etc/profile`, which overwrites `PATH` — so a
toolchain installed under `ENV PATH` vanishes when the verifier runs under `bash -l`, even though
the reference Dockerfile uses that pattern. Measured: `go` disappeared.

```dockerfile
RUN printf 'export PATH=%s\n' "$PATH" > /etc/profile.d/10-toolchain.sh
```

Prove it the way the verifier will: `docker run ... bash -lc 'command -v go'`.

## 5. CHECKLIST

Tick every line or waive it with a reason. The full preflight run belongs to `B5`; here you only
need TIER 0 green.

```
[ ]  1. Task dir created at the assigned name; format chosen per §1.2
        proof: `codimango task init <task> --format <fmt>` output, then `ls -R <task> | head -40`
[ ] 1b. Every instruction path is still EMPTY — no content seeded by anyone (§0)
        proof: `find <task> -name 'instr*.md' -size +0 -exec echo NON-EMPTY: {} \;`  (must print nothing)
[ ]  2. track_assignment + workstream DERIVED from format (§1.3), not asked for
        proof: `grep -E 'format|track_assignment|workstream' <task>/task.toml`
[ ]  3. base_commit is the 40-hex value pinned on the card, NOT HEAD
        proof: `grep -rho '[0-9a-f]\{40\}' <task> | sort -u`
[ ]  4. Every §2 row marked `Claude` patched (3, 6, 7, 8, 9, 9b, 11, 15, 18-Dockerfile)
        proof: one line each naming the file and the change
[ ]  5. Every §2 row marked `Codex` recorded verbatim in the HANDOFF FACTS block
        proof: the list itself
[ ]  6. Canary gone from ALL THREE homes (Dockerfile line 1, tests/test.sh header,
        tests/run_script.sh header) — grep the whole tree, do not spot-check
        proof: `! grep -ril 'canary\|BENCHMARK DATA SHOULD NEVER' <task>`
[ ]  7. TIER 0 inventory clean: no strays, no zero-byte files, no merge markers, no
        `<base_commit` / `<owner>/<repo>` placeholders anywhere in the tree
        proof: `~/.claude/skills/swebench-mt/preflight.sh <task> --fast --no-server`
[ ]  8. Task-scoped temp paths only — `/tmp/<task-name>/...`, never `/tmp/oracle.patch`
        proof: `grep -rn '/tmp/' <task>` shows no generic path  → 00-ROUTER.md §6
[ ]  9. No write by this session to any instruction path  → 00-ROUTER.md §5
        proof: `git status --porcelain -- '<task>/steps/*/instr*.md'` is empty
[ ] 10. MULTI-TURN steps-validation:
        a. every step dir holds instruction.md, solution/solve.sh, and
           tests/{config.json,parser.py,run_script.sh,test.sh} — a missing parser.py on
           ONE step is the server's `SWE Step Parsers` fail
        b. `[[steps]].name` matches its directory EXACTLY, for every step
        c. dependencies: step 1 `[]`, step N `["<prev>"]`; min_reward 1.0 everywhere
        d. inherit_prior_session true on step 2+ ONLY
        e. no `format =` inside any `[[steps]]` block
        f. NO top-level instruction.md and NO top-level solution/
        g. the cascade delta-patch trap is NOT settled here — carry it to B3 §8 and B4 §4
           as an OPEN item; do not assert cumulative-vs-delta at scaffold time
        proof: the `[[steps]]` block and `find <task>/steps -type f | sort`, side by side
[ ] 11. Single-turn only: no steps/ dir, no [[steps]], instruction.md + solution/ at root
        proof: `ls <task>`
```

---

```
HANDOFF B1
  EXIT:      <task dir path>; `preflight.sh <task> --fast` TIER 0 output pasted
  CHECKLIST: <n of 11 ticked; every waived line with its reason>
  ARTIFACTS: <task>/task.toml, <task>/environment/Dockerfile, steps/<N>/ skeletons
  FACTS:     format + track_assignment + workstream chosen; base_commit (40-hex);
             upstream repo owner/name; step names and their [[steps]] order;
             EVERY §2 row marked `Codex` that is still unpatched, verbatim
  OPEN:      tests/* landmines — Owner: Codex, land them in B3;
             cascade patch shape — undecided, see B3 §8
  NEXT:      B-build/B2-contract.md
```

# B4 — SOLUTION AND ENVIRONMENT

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
OWNER:   Codex builds · Claude verifies (00-LANES.md §1)
INPUT:   HANDOFF B2 (the contract) + HANDOFF B3 (the graded suite)
OUTPUT:  solution/solve.sh (per step), environment/Dockerfile, task.toml
EXIT:    oracle 3/3 locally — `codimango bench run -p <task> -a oracle -k 3`
```

You may write `solution/*`, `environment/Dockerfile`, `task.toml`, `README.md`, `audit/*`.
**Nothing under `tests/`, and nothing in any `instruction.md`, ever.** → `00-ROUTER.md §5`

**Oracle must be 3/3, not 2/3.** At 2/3 the server **skips calibration entirely** and you get no
signal at all — a worse outcome than a failing task, because it burns a cycle and returns
nothing. `STATUS: LIVE`

---

## 1. `solve.sh`

| Rule | Why |
|---|---|
| shebang present, `chmod +x`, meaningful content | the server's `Solution` / `Step Solution` gates check exactly this |
| **source changes only — no test files** | the oracle applies first and `test_patch` then collides. → `B1 §2` row 13 |
| no literal `/tmp` paths — use `mktemp -t NAME.XXXXXX` | the validator flags `mktemp /tmp/…` and `> /tmp/<name>`; generic paths also collide across parallel sessions → `00-ROUTER.md §6` |
| one per step under `steps/<N>/solution/solve.sh` | there is **no** top-level `solution/` for MT → `B1 §1.1` |

Whether step N's patch is cumulative-from-base or a delta from step N−1 is **contested** and is
settled by running the sequential-apply gate, not by asserting a position →
`B3-grader.md §8` and `§7 B.2`.

---

## 2. Dockerfile — the standing traps

Every row has been paid for. `STATUS: LIVE` unless marked otherwise.

| Trap | Requirement | Measured consequence |
|---|---|---|
| **Final `USER`** | **The image must end as root.** | Harbor creates mount targets with an in-container exec a non-root final user cannot perform. `USER tester` **killed a whole cohort with `EnvironmentStartTimeoutError` while the local oracle was 3/3.** |
| `ENTRYPOINT` | bare `ENTRYPOINT []` | an inherited entrypoint swallows the harness's command |
| `/logs` | create it | the verifier writes `/logs/verifier/reward.txt`; a missing dir means no reward is ever recorded |
| `safe.directory` | configure it for the repo path | git refuses to operate on a tree owned by another uid, and every `git apply` in the harness fails |
| `PATH` | must not be shadowed by `$HOME/go` | a `$HOME/go`-first PATH masks the real toolchain; the Go variant of this is the hardened `run_script.sh` PATH pin → `B1 §2` row 19, which produced **oracle 0/3** |
| `python3` | present on every non-Python base | → `B1 §2` row 6 |
| base image name | bare Docker Hub name, no ECR prefix | → `B1 §2` row 3 |
| native-extension headers | leaf `-dev` package | → `B1 §2` row 15 |
| canary | line 1, and two more homes | → `B1 §2` row 18 |

**The Dockerfile is SHARED across all MT steps.** One image, every step. A dependency only step 2
needs still belongs here.

---

## 3. `task.toml` — what B4 adds

The structural fields (`format`, `track_assignment`, `workstream`, `category_usecase`,
`category_subdomain`, the `[[steps]]` block) were set in `B1 §1` and `B1 §2`. Do not re-derive
them. B4 only revisits what the golden's existence now makes checkable:

- [ ] `artifacts` paths are real — now derivable from the actual oracle patch rather than guessed.
      Still ADVISORY, still never a gate → `B1 §4`.
- [ ] `allow_internet` matches reality. The server's `Internet Access` gate reads it, and the
      tests must not reach the network regardless (R09).
- [ ] `build_timeout_sec` is large enough for a cold build. **Rust cargo builds are the risk —
      raise it to 3600.**
- [ ] Declared step names still match the directories exactly after any rename.

---

## 4. `patch` ↔ `solve.sh` parity — confirm the layout before asserting it

**At least three layouts exist in this corpus.** Identify which one this task uses *before*
claiming the golden and the config agree; a parity check run against the wrong layout is a
confident false defect. `STATUS: LIVE`

| # | Layout |
|---|---|
| 1 | the patch is **embedded verbatim** in `solve.sh` |
| 2 | `config.patch` equals a cumulative `reference_patch.diff`, while `solve.sh` embeds the **step-delta** `gold_patch.diff` |
| 3 | `solve.sh` **applies** `gold_patch.diff` **by path** |

Layout 3 is the one that breaks in the cloud — see §5.

Two measurement traps while checking parity, both of which manufactured false defects:

- **Never diff `jq -r` stdout against a file.** `jq -r` appends a newline, so `diff`, `wc -c` and
  `md5sum` are all off by one trailing byte. The follow-up "fix" of `sed '$a\'` does not help.
  Compare parsed values instead:
  `python3 -c "import json;print(json.load(open(C))['test_patch']==open(P).read())"`
- **Never count hunk bodies with an awk one-liner.** It miscounts `-` lines and the trailing
  newline. Use a prefix-aware parser that resets on `diff --git` / `index` / `---` / `+++`.

---

## 5. Untracked files and the hidden-state class

**Any untracked file a `test.sh` or `solve.sh` reads must be committed.** It works locally and
fails in the cloud, and nothing local reports it. `STATUS: LIVE`

```bash
git ls-files --error-unmatch <path>      # run it for every runtime dependency you add
```

Measured shape: `solve.sh` referencing a `step1_patch.diff` that exists only in the working tree.
Green locally, dead cold. The same class covers a step that relies on residue the cold run does
not have — a prior step's applied patch, a build cache, a file a previous verifier left behind.

---

## 6. Idempotency — the defect that is 3/3 locally and 0/3 on the server

**An "already applied" branch that detects the prior state and no-ops is safe in-situ and broken
cold. One such branch produced a 1-in-3 oracle flake that took a full cycle to attribute.**
`STATUS: LIVE`

The mechanism — the server runs each step's verifier once **before** `solve.sh` and again after,
while `codimango bench run` does not — and the task it killed are in
`reference/R3-landmines.md §A.3`. `preflight.sh` checks it statically (BLOCKING) and replays it in
Docker under `--with-oracle` (TIER 4b: baseline verifier → `solve.sh` → graded verifier, per step).
Two failure strings to recognise:

- `replay: <step> passes BEFORE solve.sh` — a no-op step, an eval-GT defect.
- `replay: <step> graded reward=<G> after a prior verifier pass in the same tree` — the
  non-idempotency itself.

The strongest fix is a `cleanup()` that purges the test-patch paths **after the reward is final**.
Leaning on the `--reverse --check` "already present" branch works today and breaks the moment
anything reverts part of the patch.

The only check that runs the golden **cold** is `codimango bench tbd evalgt -p <task> -f swe`; its
verdict is never written to the task record → `00-ROUTER.md §2`. It is not a gate and must not be
reported as one.

---

## 7. Running the oracle

```bash
codimango bench run -p <task> -a oracle -k 3     # every per-step reward 1, Mean: 1.000
```

**Docker concurrency.** The host caps near **15 bridge networks** and one `k=5` job creates 5.
Another build agent is usually running. **Never more than one `bench run` at a time, and never
with `k>3`.** → `00-ROUTER.md §6`

**Do not run local Avocado to "check difficulty."** Correlation with the server is **0.07** over
**120 paired samples**; the same commit has read `3/5` locally and `1.0` on the server, and `0/5`
locally against `5/5` on the server. It is a one-sided kill gate only: local 0/5 or 5/5 means fix
something first; anything between tells you nothing. `STATUS: LIVE`

**OPEN RISK — a warm local cache may be hiding server failures.**
`spire-workload-api-delivery-readiness` ran **oracle 3/3 locally, twice, independently — and 0/3
on the server**, with structural 19/19 PASS. Leading hypotheses: a narrowed warm-up build that
works against a warm Docker/Go module cache but not a cold server build, or the Go PATH defect
(`B1 §2` row 19). **Six of seven tasks passed the server oracle, so this is not systemic — but our
gate did miss it once.** If the task is Go, check the PATH explicitly, and prefer a
`docker build --no-cache` oracle run before declaring done.
`STATUS: SCOPED-TO Go tasks and any task whose oracle is green only on a warm cache`

---

## 8. CONFLICT — UNRESOLVED: the top-level MT `tests/config.json`

| Source | Position |
|---|---|
| OURS `runbooks/2-build.md`:587 | the layout tree annotates it `tests/config.json  # structure-only stub` |
| OURS `MT-BATCH-KILL-CRITERIA.md`:120–125 | *"Top-level `tests/config.json` is a STRUCTURE-CHECK STUB — do **NOT** populate it."* |
| OURS `runbooks/2-build.md`:836 | the opposite, in the same document: *"Top-level `<task>/tests/config.json` is **NOT a stub**."* Eval-GT reads `base_commit` from it; it demands a full 40-hex matching every step **and** the Dockerfile, and a real `owner/name` in `repo` because the server License gate reads it |
| PEER `05-codex-finish-the-scaffolding.md`:447–462 | wants **non-zero `patch` and `test_patch`** at the top level: *"Check `jq '.patch|length, .test_patch|length'` is non-zero."* Reports **three of eight** tasks shipping an empty or reviewer-reconstructed aggregate, and **both tasks with a 0-byte top-level record are `tbd=fail`** — including one that scored **17/17 rubrics and `GOOD / GENUINELY_HARD`** on the Full-Task review |

**Our measured consequence, which neither "stub" line accounts for.** A placeholder `base_commit`
in that file is interpolated **UNQUOTED** into `/eval.sh`, producing

```
/eval.sh: line 5: syntax error near unexpected token '||'
```

in every baseline **and** golden phase, scoring **0.0 with F2P=0/0 before a single test runs**.
**16 of our MT tasks shipped this way.** It is invisible locally — `harbor/trial/multi_step.py`
never imports `load_swe_bench_config`, so the oracle, `bench run` and calibration physically
cannot read the file. An **absent** file is worse still: it permanently zeroes the DQE review
signal while eval-GT looks fine.

**What both sides agree on, and what is genuinely open.** Agreed: the identity fields
(`base_commit`, `repo`) must be real and must agree with every step config and the Dockerfile —
`preflight.sh` enforces exactly that and it is not in dispute. Open: whether the server also
requires **non-empty aggregate `patch` / `test_patch`** at the top level for every MT format. The
sources do not settle it — the peer measurement is a review-quality outcome (`tbd=fail`), not a
schema statement. **The "stub" language is unsafe regardless and is internally obsolete within
OURS itself.**

**Until it is resolved:** populate the identity fields for certain, and populate `patch` /
`test_patch` too — a non-empty aggregate has no measured downside and an empty one has two. Derive
the aggregate mechanically, never by concatenation → `B3-grader.md §7 B.3`.

---

## 9. CHECKLIST

```
[ ]  1. solve.sh per step: shebang, executable, meaningful, source-only, no literal /tmp
        proof: `head -1 steps/*/solution/solve.sh; ls -l steps/*/solution/solve.sh`
[ ]  2. Dockerfile ends as root — no non-root final USER
        proof: `grep -n '^USER' <task>/environment/Dockerfile` (expect none, or a final root)
[ ]  3. bare `ENTRYPOINT []`; `/logs` created; `safe.directory` configured; PATH not
        shadowed by $HOME/go
        proof: `grep -nE 'ENTRYPOINT|/logs|safe.directory|PATH' <task>/environment/Dockerfile`
[ ]  4. python3 present on a non-Python base; leaf -dev headers present; bare base image
        proof: the FROM line and the apt-get line
[ ]  5. task.toml: artifacts paths real, allow_internet honest, build_timeout_sec adequate
        proof: `cat <task>/task.toml`
[ ]  6. §4 layout identified BEFORE asserting patch <-> solve.sh parity, and named here
        proof: "layout 1 / 2 / 3", plus the parsed-value comparison (never `jq -r` + diff)
[ ]  7. Every runtime dependency of test.sh / solve.sh is tracked
        proof: `git ls-files --error-unmatch <each path>`
[ ]  8. Idempotency: preflight's static check PASSes and TIER 4b replay is green
        proof: the `idempotency:` and `replay:` lines from preflight
[ ]  9. Oracle 3/3 — not 2/3
        proof: `codimango bench run -p <task> -a oracle -k 3` -> `Solved: 3/3`, `Mean: 1.000`
[ ] 10. Only ONE bench run in flight, k<=3
        proof: `docker network ls | wc -l` before starting
[ ] 11. Top-level tests/config.json: 40-hex base_commit agreeing with every step AND the
        Dockerfile; real owner/name repo; non-empty patch and test_patch (§8)
        proof: `jq '{repo,base_commit,p:(.patch|length),t:(.test_patch|length)}' \
                <task>/tests/config.json`
[ ] 12. No write by this session to tests/* or any instruction path  -> 00-ROUTER.md §5
        proof: `git status --porcelain -- '<task>/tests' '<task>/steps/*/tests' \
                '<task>/steps/*/instr*.md'`
[ ] 13. MULTI-TURN steps-validation:
        a. one solve.sh per step; NO top-level solution/
        b. base_commit identical across every step config, the top-level config and the
           Dockerfile
        c. the cascade applies in order from base with PLAIN `git apply` — no --3way, no
           fuzz, no --recount — in a DISPOSABLE clone, never the shared task repo
        d. per-step oracle reward is 1 for EVERY step, not just the mean
        e. Dockerfile serves every step (a step-2-only dependency is installed here)
        proof: the disposable-clone apply log and the per-step reward lines
[ ] 14. Go tasks only: `docker build --no-cache` oracle run before declaring done (§7)
        proof: the no-cache build + oracle output
```

---

```
HANDOFF B4
  EXIT:      `codimango bench run -p <task> -a oracle -k 3` output, verbatim
  CHECKLIST: <n of 14 ticked; every waived line with its reason>
  ARTIFACTS: steps/<N>/solution/solve.sh, environment/Dockerfile, task.toml
  FACTS:     the §4 layout in use; per-step oracle rewards; the base_commit as it appears
             in the top-level config, every step config and the Dockerfile; whether a
             no-cache build was run
  OPEN:      §8 remains UNRESOLVED — record which shape this task shipped;
             anything still owned by Codex or by Avocado/human
  NEXT:      B-build/B5-preflight-push.md
```

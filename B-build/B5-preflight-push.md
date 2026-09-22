# B5 — PREFLIGHT AND PUSH

```
OWNER:   Claude
INPUT:   HANDOFF B4 — a locally-green task, oracle 3/3
OUTPUT:  one pushed commit containing only this task's paths
EXIT:    `preflight.sh <task> --with-oracle` exits 0, and a scoped commit has landed
         on origin/main
```

This is the last act before the server sees anything. Everything past here costs a cycle.

---

## 1. `preflight.sh` — the tiers and the two severities

```bash
~/.claude/skills/swebench-mt/preflight.sh <task> --with-oracle   # before push
~/.claude/skills/swebench-mt/preflight.sh <task> --fast          # while iterating (skips TIER 1)
~/.claude/skills/swebench-mt/preflight.sh <task> --no-server     # skip the lifecycle lookup
```

| Tier | What it is |
|---|---|
| **TIER 1** | the **16** checks local `bench validate --structural-only` runs (~400s) |
| **TIER 2** | the **3** checks **only the server** runs — `License`, `SWE Step Configs`, `SWE Step Parsers` — replicated so a local PASS means something |
| **TIER 3** | the landmines **no validator catches**, that cost real pushes |
| **TIER 4** | the oracle |

The script also runs a **TIER 0** full-file inventory before TIER 1 (§3) and a **TIER 4b** server
sequence replay after TIER 3 (`B4 §6`). The four named tiers are the design; six blocks execute.

### The two severities

| Severity | Behaviour |
|---|---|
| **BLOCKING** | the task will fail server-side or grade wrongly. Prints `FAIL`, **sets the exit code to 1** |
| **ADVISORY** | authoring quality. Prints `ADV`, **never exits 1, and is never promoted to blocking by any flag** |

**Do not promote an advisory to blocking.** `STATUS: LIVE` The advisory set buys a small quality
gain at near-zero turnaround cost; the moment one becomes a requirement it costs more than it
returns. `artifacts` is the archetype — nothing server-side requires it, a task without it
validates and is accepted normally, and **none of our 5 accepted tasks declares one**. Read the
advisories, act on what is worth it, push regardless.

**STOP. Exit 0, or do not push.**

### Lifecycle suppression

Advisory output is suppressed entirely on tasks that are `accepted` / `rejected` /
`used_in_training` / `validation=passing`. A **settled** task runs **no checks at all** and exits
0 with `SETTLED` — editing it means a new commit and re-validation on something already decided.
Override with `--no-server` only if you genuinely need to lint one anyway.

### The 17 TIER-3 landmine checks

The catalogue — every check, what it detects, and the task it was paid for — is
`reference/R3-landmines.md §A.3`. Do not repair a finding here; route it to the file that owns
the artifact (`B1 §2` for scaffold rows, `B2 §6` for instruction-lint, `B3 §5` for grader-lint,
`B4 §1`/`§6` for `solve.sh` and idempotency).

What B5 owns is the **severity split**, because it decides whether you push:

| Severity | Checks |
|---|---|
| **BLOCKING** | canary · oracle-patch-carries-tests · missing `new file mode` · casing keys disagree · Go ids without `::TestFunc` · `solve.sh` not executable · empty-or-<40-word instruction · contract coverage (grader needs a NEW symbol) · grader-lint private-state · instruction-lint · verifier idempotency (static) · TIER 4b replay |
| **WARN** (no exit code) | reward may derive from exit status · literal `/tmp` in `solve.sh` · cascade *not verified here* — prove it per `B3 §7 B.2` |
| **ADVISORY** | `artifacts` · size floor (<20 net lines rarely calibrates; SWE-bench Pro excludes 1–10 LOC edits, mean 107) · `xfail`/`xpass` handling · `error2pass` · de-scaffolding lint · grader-lint nil-vs-empty and nil-for-collection · contract names an internal the test never grades |

### Local PASS does not imply server PASS

The two check sets genuinely differ. **Local** runs `Track assignment`, `Workstream`, `Format`,
which the server set does not; **the server** runs `License`, `SWE Step Configs`,
`SWE Step Parsers`, which local does not. TIER 2 exists to close that gap, but read both.
`STATUS: LIVE`

Two things the script cannot do: rerun a timing-sensitive suite under load to expose a race
(→ `B3 §1` R09), and judge anti-tautology on a net-new-capability task (→ `B3 §2`).

---

## 2. The agentic-reviewer precheck

Run the reviewer's own dimensions locally **before** pushing, so a predictable FAIL is caught here
rather than a cohort later. State **PASS** or **AT-RISK** for each, one line of reasoning, and
focus on the ones this task's build could plausibly have broken. The rules behind each axis live
in `B3-grader.md §1` and `§7` — this is the walk, not a second copy. `STATUS: LIVE`

| | Focus | You fail it by |
|---|---|---|
| R01 | Spec sufficiency | grading something the prompt does not state |
| R02 | Spec–test alignment | adding a test with no line in the spec behind it |
| R03 | Trajectory-informed spec | many arms failing one test ⇒ the spec is unclear, not the models |
| R04 | Reasoning required | spelling out the recipe, or pinning the implementation shape |
| R05 | Information isolation | leaking the solution via env, fixtures or expected outputs |
| R06 | Test coverage | leaving a stated requirement ungraded (`p2p = 0` counts) |
| R07 | Reward-hacking | tests executed but not required; thin p2p; hard-codeable scenario |
| R08 | Accepts alternatives | over-pinning API names, key names, symbol vocabulary, accessors |
| R09 | Test reliability | flakiness, network/timing dependence, unpinned env, timeouts |
| R10 | Test validity | an f2p that already passes at base |
| R11 | Verification efficiency | grading that needs long runtimes or manual work |
| R12 | Golden correctness | gold not satisfying a stated requirement |
| R13 | Golden reliability | oracle not green on every trial |
| N01 | Real-world relevance | a contrived change no maintainer would make |
| N02 | Knowledge depth | trivia rather than specialist reasoning |
| N03 | Data realism | toy fixtures unlike real data |
| N04 | Training signal | difficulty from incidental friction rather than reasoning |

**Two bite most often: R08 (loosening too little) and R06/R07 (loosening too much). A change that
fixes one and breaks the other is not progress.**

The separate TBR review scores `spec_clarity`, `test_quality`, `hackability` and
`code_patch_quality`. Target: spec clarity `Good`, output ambiguity `Unambiguous`, test quality
`Good`, information leakage `None`, hackability `low`, code patch quality `Good`. On the peer
cohort **`code_patch_quality` was the only dimension that decided pass vs fail** → `B3 §7`.

---

## 3. The pre-push file-structure review

**Walk every file in the pushed set. Confirm nothing was broken by an agent.** Multiple models
write into one task directory; this review assumes nothing about *which* file broke.
`STATUS: LIVE`

preflight TIER 0 does the mechanical half and it is BLOCKING:

- every required file exists, per step — `instruction.md`, `solution/solve.sh`,
  `tests/{config.json,parser.py,run_script.sh,test.sh}`
- no stray `*.orig`, `*.rej`, `*~`, `*.bak`, `*.swp`, `.DS_Store`, `*.tmp`, `nohup.out`, `*.log`,
  `core`, `*.pyc`
- **no zero-byte files** — almost always a half-finished agent write
- no merge markers, `TODO_REPLACE`, `<owner>/<repo>`, `<base_commit`, `FIXME_SCAFFOLD`,
  `XXX_PLACEHOLDER` **anywhere in the tree, `config.json` included.** Excluding `config.json`
  from that scan is precisely what let an unsubstituted `<base_commit_sha>` through on **16 MT
  tasks** → `B4 §8`
- the top-level `tests/config.json` identity fields agree with every step and the Dockerfile

You do the other half by hand, because a file can be present, non-empty and still wrong:

```bash
git -C "$REPO" status --porcelain -- "$T"     # preflight prints this too
git -C "$REPO" diff -- "$T"                   # READ IT. Do not skim it.
```

Read the full diff before pushing. Confirm each changed file is one the act that owns it was
supposed to write, and that no agent truncated, reformatted or half-rewrote a file it was only
meant to read. Ownership by path → `00-ROUTER.md §5`.

---

## 4. Re-check `origin/main` before you push

A peer may have landed the same fix while you were working. **Three dispatches in one cycle were
spent that way, and twice the peer's version was already better — the right move was to drop the
local commit and sync, not to force a duplicate.** `STATUS: LIVE`

```bash
git fetch origin && git log --oneline HEAD..origin/main -- "$T"
```

If `origin/main` moved, or local carries other sessions' commits, cherry-pick **only your commit**
onto `origin/main` in a throwaway worktree, diff that tree against your verified copy, then push
from there.

---

## 5. The scoped commit

Use the script. It encodes every rule below:

```bash
~/.claude/skills/swebench-mt/push-task.sh <task> [--dry-run]
```

The sequence, and why each step exists:

1. **preflight `--with-oracle` must exit 0.** The script refuses to push otherwise.
2. **`git reset -q`** — isolate the index first. The shared repo routinely holds dozens of
   unrelated uncommitted files: other agents' in-progress task dirs, another session's
   remediation, old sweeps.
3. **`git add -A -- "$T/"`** — one path. **Never `git add .`, never `git add -u`, never
   `git commit -a`.** `git add -u -- <path>` scopes what it *adds*, not what is already staged —
   **that distinction has silently shipped unreviewed work twice.** The checkout is shared and a
   concurrent session's commit has swallowed staged files, so **stage and commit in one call.**
4. **Verify the staged set** — `git diff --cached --name-only`, and **abort on anything outside
   the task**:
   ```
   ABORT: files staged OUTSIDE $T/
   ```
   Unrelated uncommitted files left behind are expected, not an error.
5. **Commit.** The message records the evidence: what was measured, what changed, what was
   deliberately not changed, and what remains unmeasured.
6. **Push over the explicit port** — a global `insteadOf` rewrite forces HTTPS and 403s:
   ```bash
   git push ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git HEAD:main
   ```
   If the push fails, the commit is local — **retry the push only.**

**Never `--no-verify`. Never `SKIP_TASK_VERIFY=1`.** The pre-push checks encode defects that each
voided a real calibration run. `STATUS: LIVE`

---

## 6. PRE-SUBMISSION CHECKLIST

```
[ ]  1. HANDOFF B2, B3 and B4 all in hand, each with its CHECKLIST line
        proof: the three blocks
[ ]  2. Every OPEN item from B1-B4 is either closed or restated here with its owner
        proof: the list
[ ]  3. preflight --with-oracle exits 0
        proof: `~/.claude/skills/swebench-mt/preflight.sh <task> --with-oracle; echo $?`
[ ]  4. Every ADV line read; none promoted to blocking; the ones acted on are named
        proof: the ADV lines and a one-line disposition each
[ ]  5. TIER 0 inventory clean (§3), and the FULL diff read, not skimmed
        proof: `git -C $REPO diff -- <task> | wc -l`, plus your read-through note
[ ]  6. Agentic-reviewer precheck walked (§2): PASS / AT-RISK for all 17 axes
        proof: the 17 lines
[ ]  7. Local structural PASS, knowing it does not imply a server pass (§1)
        proof: `codimango bench validate -p <task> --structural-only` -> `Overall: PASS`
[ ]  8. origin/main re-checked; no peer has landed the same work (§4)
        proof: `git log --oneline HEAD..origin/main -- <task>`
[ ]  9. `--dry-run` first: the staged set is exactly <task>/ and nothing else
        proof: `push-task.sh <task> --dry-run`
[ ] 10. Push executed with the explicit :22 URL; no --no-verify, no SKIP_TASK_VERIFY
        proof: the push output and the resulting SHA
[ ] 11. MULTI-TURN steps-validation, final pass:
        a. every step present in `[[steps]]` ships files, and every shipped step is declared
        b. per-step oracle reward 1, not just the mean
        c. TIER 4b replay green for every step
        d. the cascade applied in order with plain `git apply` (B4 §9.13c)
        proof: the preflight step lines and the B4 apply log
```

---

## 7. POST-SUBMISSION CHECKLIST — the minutes after the push lands

```
[ ] 1. Record the pushed SHA. Everything below is read AGAINST it.
       proof: `git rev-parse HEAD`
[ ] 2. Confirm the server picked up YOUR commit, not an earlier one
       proof: `codimango task show <task> --json | jq -r .commitSha`  == your SHA
       If it differs you are reading STALE results. Do not analyse. This is not an attempt.
[ ] 3. Confirm jobs were created
       proof: `codimango job list <task> --json`
       `(no jobs on Nest)` means the validation job was NEVER created ->
       `codimango task rerun <task>`. That is the one correct use of rerun here.
[ ] 4. Read the server structural result — all 19 labels, not a guessed subset
       proof: `codimango task errors <task>`
       Labels: License, Structure, Instruction Links, task.toml, Track assignment,
       Workstream, Format, Reward Type, Taxonomy Fields, Dockerfile, Internet Access,
       Solution, Tests, SWE Config, SWE Step Configs, SWE Step Parsers, Declared Steps,
       Step Tests, Step Solution.
       Require `Structural overall: PASS`. A structural pass alone is NOT a task pass —
       the top-level gates are Structural checks, Oracle validation, Metacode or Opus
       pass/fail balance, Contamination check, Provenance check. All five are read.
[ ] 5. Append one line to <task>/audit/drive-log.md
       `<utc> | pushed | <sha> | preflight=0 oracle=3/3 | <what changed> | next check <when>`
```

### While the task is pending — what NOT to do

| Do not | Why |
|---|---|
| repair on a stale read | `commitSha` ≠ your SHA means the numbers belong to an older commit. Not an attempt → `00-ROUTER.md §3` |
| `task rerun` on the same SHA | a review verdict is **bound to a commit SHA**; rerunning returns the cached verdict and will look like it did nothing. **A new commit is the trigger.** `rerun` is correct only when the prior run was *infrastructure*. Budget: **3 per model** |
| re-run hoping for a better draw | TBR is generated by a reasoning model with roughly **20% run-to-run deviation** — the same commit has returned different `test_quality` and `hackability` ratings on consecutive pulls. Fix what the evidence describes concretely |
| plan off the `task list` summary counters | `oraclePassCount` / `agentPassCount` go stale and read `null` for arms that **finished**. One task showed `oracle null/null, agent 0/5` while its jobs had finished with the oracle passing **3× at reward 1.0, 80/80** → `00-ROUTER.md §2` |
| treat `tbrNotFinalized: true` as a failure | it is **PENDING**. Do not spend an attempt on it → `00-ROUTER.md §2` |
| act on a `0/N` built from artifacts | that is **UNMEASURED, not "too hard."** Never loosen on it → `reference/R2-signal-integrity.md` |
| start the next task's contract | `B2 → B5` is **strictly serial per task, one task at a time** → `00-ROUTER.md §6` |

Poll only helps while something is in flight. If nothing is running and nothing changed, polling
forever is a no-op.

---

```
HANDOFF B5
  EXIT:      `preflight.sh <task> --with-oracle; echo $?` -> 0; the pushed SHA
  CHECKLIST: <n of 11 pre-submission + n of 5 post-submission ticked; waivers with reasons>
  ARTIFACTS: one commit on origin/main touching only <task>/
  FACTS:     the SHA; the staged file list; the server `Structural overall` line; whether
             jobs were created; the 17-axis precheck verdicts; every advisory left unactioned
  OPEN:      anything owned by Codex or by Avocado/human that shipped unresolved;
             the B4 §8 shape this task used
  NEXT:      S8 — wait (00-ROUTER.md §3). On any server verdict: C-drive/C1-read-verdict.md
```

# RUNBOOK — the driver

**This file holds no rules.** It says which runbook to open, in what order, who
owns each artifact, and where the hard stops are. Everything else lives in the
three phase runbooks.

```
 PHASE 1  BRAINSTORM   runbooks/1-brainstorm.md   stages 0 -> 1d
 PHASE 2  BUILD        runbooks/2-build.md        stages 2 -> 4
 PHASE 3  HARNESS      runbooks/3-harness.md      stages 5 -> 7 + salvage
          always       references/signal-integrity.md
```

A dispatched agent reads **one** phase runbook. Do not hand it four files.

---

## The phases

| # | Runbook | Does | Entry condition | Exit condition |
|---|---|---|---|---|
| 1 | `1-brainstorm.md` | pick repo, find candidates, **measure** variance | — | a candidate with a MEASURED 1-3/5 split |
| 2 | `2-build.md` | instruction, tests, solve/docker/toml, preflight | phase 1 measured the split | `preflight.sh --with-oracle` exit 0 |
| 3 | `3-harness.md` | read verdict, tune the harness, salvage | a server verdict exists | in band, or an evidenced kill |

**Phase 1's exit condition is not negotiable.** Eleven candidates scored
24-33/35 on argued strength; every one measured Fork 1 when finally probed. A
score without a measurement is not an entry ticket to phase 2.

---

## Who writes what — provenance is contractual

This table is the single source of truth. Any older wording elsewhere in this
skill ("Codex or MetaCode", "1P-only tests", "Claude writes solve.sh") is
superseded by it.

| Artifact | Author | Claude |
|---|---|---|
| `instruction.md`, incl. every `steps/*/instruction.md` | **Muse only** (`mc2.sh`) | NEVER |
| **everything under `tests/`**: `config.json`, `test.sh`, `run_script.sh`, `parser.py`, graded test files | **Codex** (`codex exec … < /dev/null`); Muse if clearly better, and say why | NEVER |
| `solution/solve.sh`, `environment/Dockerfile`, `task.toml`, `README.md`, `audit/` | **Codex** | NEVER |
| probes, extractors, replay scripts, briefs | Claude | yes, under `/tmp` or `~/swebench/` only, never inside a task dir |

### Project override: Muse is approved for `instruction.md`

Vidit's rule (2026-10-04): for this SWE-bench workflow, Muse/MetaCode is an
approved 1P author and is the required model author for `instruction.md`. A
generic `verify-task-provenance` policy note that says `instruction.md` must be
human-only must **not** block a task merely because Muse authored it. The live
pipeline wording ("1P drafting is permitted with human review") and the table
above govern this project.

This is not a provenance bypass. Continue to run the classifier, write-log/L3,
and contamination checks, and block unauthorized third-party authorship. Never
rewrite, conceal, or launder provenance evidence to make a check pass.

Vidit's rule (2026-09-30, reaffirmed 2026-10-02): **Claude writes nothing inside
a task directory.** Claude briefs, verifies and measures. Not via Edit/Write, not
via a Bash heredoc, not via a generated script. A Claude-authored file found in a
task dir is archived under `audit/` and redone by Codex.

Two tasks failed provenance with byte-exact `claude_code` evidence on
`tests/run_script.sh` because an earlier version of this table said "tests/
**assertions**". It means the whole directory.

### Provenance: why tasks still fail when nobody writes with Claude any more

The gate (`agentWrites`, "L3") compares the submitted files with a **permanent
log of every file Claude ever wrote** on that path. Almost all of the evidence
dates from Jul 23 and Sep 14–18, before this rule existed, and the gate only
re-checks a task when it is pushed. So reviving an old task surfaces its old
Claude writes, even if nobody has touched the file since.

1. **Before any push, run** `python3 ~/swebench/prov_predict.py <task>` (missing ~/swebench? run ~/swebench-playbook/tools/bootstrap-swebench-home.sh).
   It must report 0 surviving flagged blocks. `mk_prov_brief.py <task> <out.md>` writes a
   Codex brief listing the exact spans to eliminate.
2. **Re-author with Codex from a requirements contract, and forbid it from
   reading the tainted file**, or the content launders forward. Give forbidden
   byte sequences as output constraints, never replacement code.
3. **Expect the evidence to move.** Each scoring can flag a *different* set of
   spans. Clearing the current set does not guarantee the next scoring is clean,
   so budget for a second pass.
4. **Fixed values Claude once typed cannot be cleared by editing around them**:
   `base_commit`, `instance_id`, repo name, upstream test names, the oracle patch.
   If a flagged block is a fixed value, have Codex **regenerate `config.json` from
   the task's own sources**, not edit it in place. `instance_id` may be set to the
   task slug, which is the convention on every accepted task.
5. **Do not shrink a file to "clean it up".** The score is relative to file
   length, so deleting unrelated content raises it.
6. A score around 0.03 has been seen to clear (0.0298 CLEAN with a block present).
   Zero surviving blocks has cleared every time it has been measured.

### `before_repo_set_cmd` may NOT contain `git clean` — server-only check
The server's structural "SWE Config" check fails any `before_repo_set_cmd` that runs
`git clean`, **even path-scoped** (`git clean -fdx -- spec/`), and validation halts
there, so nothing else runs. Missed once (ruby-auth0-lazy 9d208f4, 2026-10-02);
`preflight.sh` TIER 2 now fails on it ("SWE Config: no git clean in
before_repo_set_cmd", added 2026-10-06). Keep `before_repo_set_cmd` to a path-scoped `git checkout <base> --
<test dirs>` only, and do any untracked-file cleanup inside `tests/test.sh` right
after it runs and before the hidden test patch is applied. That keeps the verifier
idempotent (the server runs it twice) and stops solver-planted support files from
loading.

The local transcript audit is an **early warning**, not the provenance verdict.
It must inspect both restricted surfaces (`instruction.md` and all of `tests/`).
Server provenance for the submitted commit is authoritative; permitted README,
plumbing, and author-side audit edits are not instruction/test violations.

**Every artifact is checked by a model that did not write it.** Codex verifies
Muse's instruction; Claude verifies Codex's tests by running an alternative
valid implementation against them; Claude verifies Codex's plumbing (`solve.sh`,
Dockerfile, `task.toml`: cascade applies, oracle 3/3) and reports defects back to Codex.

---

## The four hard stops

0. **Before starting or reviving any task — pull server truth first.** Run
   `codimango task show <task> --json`, `codimango task errors <task>`, inspect
   the current validation commit/generation and reviews, and pull the relevant
   trials. Reconcile that server commit with the local checkout before any edit,
   pivot, replay, or archive decision. Never begin proper work from stale local
   state, an old report, or remembered calibration numbers.
1. **End of phase 1** — no measured 1-3/5 split, no build.
2. **Before push** — README check first (Vidit 2026-10-16; presubmit FAILs on it): the README has
   **no internal links** (internalmeta.com, workplace.com, fburl.com, internalfb.com), and its
   **Completion Rates / Model Analysis describe the commit being pushed** — no stale "0/5 / not reached /
   not calibrated / RELEASE / WAITING / out of band" text left by a calibration loop. commonmark d711592
   shipped a stale 4/5|0/5|not-reached table; a bounce for this costs a revision round. Then
   `revision-gate/gate.py <task>` must pass (it runs `preflight.sh --with-oracle` plus presubmit, provenance, step carry-forward, fake-pass probes, the reviewer agent and k2n x2). PROVISIONAL until `ledger/VERIFY-revision-gate.md` has 3 sign-offs; see the playbook's `tools/revision-gate/README.md`.
3. **After the verdict** — is the number real? `references/signal-integrity.md`
   before touching anything.
4. **Before submit** — human review, preceded by a **deep-review pass**.
   Green gates are not enough. Calibration, provenance and the AI assessment do
   not check sourcing or duplication; only the server's deep review (Validation
   Engine) does. dropshot-option-return-nullable-openapi went fully green on
   2026-10-04 and was then flagged in deep review for three blockers no gate saw:
   - its fix was upstream PR #152 (2021), an ancestor of the base commit, reachable
     with `allow_internet = true` (out-of-band answer);
   - an originality fail (a canonical idiom);
   - a near-duplicate of a corpus task.
   Before anyone submits, run, and fix what they flag:
   - `review-task-swebench-v2` (by hand if the Skill tool is broken);
   - a **public-fix check**: no upstream commit before or after base, merged PR,
     open PR/issue naming the fix, or release contains it, and the repo ships no
     test asserting the answer;
   - a **dedup check** against codimango peers on the same repo and seam
     (`team-aai:dedup-judge`).
   Do these at sourcing time too, so a task never gets built on a public fix.

---

## Tools

> **PRECHECK (Vidit 2026-10-13, PROVISIONAL):** before ANY push, first push or revision, run `python3 ~/swebench/revision-gate/gate.py <task>` (full run) and fix every FAIL. `push-task.sh` refuses to push without its stamp. Until 3 agents sign off in `ledger/VERIFY-revision-gate.md`, a FAIL means "look at this", not proof, and `GATE_OVERRIDE="<reason>"` is allowed and logged.

`~/swebench/<tool>` paths below are host-local: missing ~/swebench? run ~/swebench-playbook/tools/bootstrap-swebench-home.sh (and
`~/swebench-playbook/tools/sync-skill.sh install` to install this skill itself).

```bash
preflight.sh <task> [--with-oracle] [--fast] [--no-server]   # the push gate
mc2.sh <prompt-file> <workspace> [out]                       # the ONLY supported way to run Muse (MetaCode retired 2026-09-29)
codex exec -C <dir> -s workspace-write --skip-git-repo-check "<brief>" < /dev/null   # Codex; without < /dev/null it hangs on stdin
python3 ~/swebench/prov_predict.py <task>                    # provenance: must be 0 surviving blocks before push
grader-lint.py <task>                                        # private-state / nil-pin graders
instruction-lint.py <task> <clone>                           # does the instruction leak the answer
push-task.sh <task> [--dry-run]                              # scoped commit + push
```

Always run Muse through `mc2.sh`, which passes the prompt as a file. Never
hand-roll `muse exec`, `metacode run` or `script -qec` with an inline prompt: an
inline prompt silently loses apostrophes and exits 0, and one agent lost an
entire step-2 contract that way. `metacode run` itself now forwards to
`muse exec`, which rejects `--format`, so any old `metacode run --format text`
snippet returns a banner and does nothing. (`mc.sh` was patched to forward to
`muse exec` too and works, but `mc2.sh` is the canonical wrapper.)

---

## Routing on a server verdict

`codimango task errors <task>` -> find the line -> open the runbook.

| Server says | Go to |
|---|---|
| `Oracle validation: N/3 passed` | `3-harness.md` — everything else is skipped until this is 3/3 |
| `too easy — avocado passed N of 5` | `3-harness.md` -> too-easy ladder |
| `too hard — no model passed it` | `3-harness.md` -> **prove false negative first** |
| `BAD_GRADING_WRONG` | `2-build.md` -> graded is a superset of stated; **remove** an assertion |
| `BAD_GRADING_WEAK` | `2-build.md` -> stated is a superset of graded; **add** a test |
| `Unauthorized third-party model authorship` | `2-build.md` -> provenance; 1P re-author |
| `Passed` | `3-harness.md` -> stage 7, submit |
| `needs_revision` / any human review (green OR failed validation) | `~/swebench-playbook/C-drive/C7-revision-response.md` (after a `C1` diagnosis). A failed gate is fixed in the same revision via `3-harness.md`. Ready to resubmit only with `RESUBMIT-PROOF.md` lines 1-8 green; C7 also drafts the reviewer reply for Vidit to send |

Full verdict-string table with exact wording: `SKILL.md`.

---

## Libraries the brainstorm phase consults

Data, not process — they grow independently of the runbooks.
(missing ~/swebench? run ~/swebench-playbook/tools/bootstrap-swebench-home.sh)

| File | Layer |
|---|---|
| `~/swebench/SEARCH-AXES.md` | 18 ranked ways to look at a repo |
| `~/swebench/FORK-PATTERNS.md` | reusable divergence shapes; indexes all three |
| `~/swebench/ALGO-CATALOGUE.md` | 46 techniques — **check saturation before using one** |

---

## Reporting contract

Report **DONE / NOT DONE / BLOCKED per stage, with evidence** — never a summary.
If a stage is incomplete write `NOT DONE: <reason> — BLOCKED`. If you skipped an
expensive step, say so. A well-evidenced kill is a good outcome; three of the
best results this month were kills.

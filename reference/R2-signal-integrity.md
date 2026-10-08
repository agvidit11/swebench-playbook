# R2 — Signal integrity: is this number real?

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
OWNER:  Claude (reference — pulled on demand)
INPUT:  a pass rate, a gate string, or a trial count you are about to act on
OUTPUT: the number classified MEASURED or UNMEASURED. This file writes nothing.
EXIT:   you can say, in one line with a command behind it, why the number does or does not
        describe the task.
```

**Never act on an UNMEASURED number.** That is hard stop 3 in `00-ROUTER.md` §7, and it is the
single largest source of wasted rounds in both source pipelines. This check is meant to save
cycles, not become ceremony: run §1; escalate only where §1 finds a reason.

Field decode (what a gate string *says*) lives in `reference/R1-field-authority.md`. This file
only answers whether to believe it.

---

## 1. The one-minute triage — run this before believing anything

```bash
cd /home/agvidit/swe-bench-pro-agvidit
git rev-parse HEAD
git status --short -- <task-dir>/
codimango task errors <task>
uptime
pgrep -af 'codimango bench run|bench run|metacode|codex exec'
docker ps --format '{{.Names}}\t{{.Status}}'
```

Read, in order:

1. Is the server oracle exactly **3/3**? If not, calibration was skipped and every agent number
   below it is meaningless.
2. Is this the intended commit, with no local artifact being confused for it?
3. What is **each** Avocado step rate? Target is 1–3/5; 4/5 fails. Never average steps.
4. Does the message say grandfathered, no-gradient, pending, or no trials?
5. Is the host visibly contended, or another bench job alive?

Clean on all five → act. A zero, an `NA`, an oracle miss, or an implausible jump driving the
decision → §3, then the targeted audit in §5.

---

## 2. Evidence hierarchy

Never average local and server runs, and never average steps.

| Rank | Signal | Use for | Measured |
|---:|---|---|---|
| 1 | Current **server per-step** Avocado verdict | calibration truth | the gate is per step and rejects 4/5 |
| 2 | Repeated server verdicts on **identical artifacts** | directional only | Django moved 0.4 → 0.8 and franz-go 0.8 → 1.0 with nothing changed |
| 3 | Local oracle + structural checks | breakage checks | oracle must be green; local and server structural check **sets differ** |
| 4 | Local Avocado | gross debugging only | same sparql commit: **3/5 local, 5/5 server**; unchanged local runs produced 1/3 then 3/3 |

---

## 3. Four signatures that mean the numbers do not describe the task

`STATUS: LIVE`. Treating any one of these as a verdict costs a whole round.

| # | Signature | Reading |
|---|---|---|
| 1 | **`0/0`**, or *"N errored — excluded from %"* | no trial was dispatched; the image did not build. Read the build log, report `infra`, **never tune difficulty on it** |
| 2 | **`4/4` where the batch was 5** | not a four-of-five band — an **insufficient legitimate sample**. The task is unmeasured |
| 3 | **A pass the harness should have refused** | reward-hacked passes inflate a band. One task read **4/5 and 5/5**; after the verifier was hardened against pytest-hook and flexible-equality tricks the same task read **2/5 and 2/5**. The first pair was never real. **If any trial is `verifier_gaming` the whole band is suspect** until the harness is fixed and it is re-measured |
| 4 | **Every model failing the same gate** | **ambiguity, not difficulty** — it has been the spec every time. A uniform near-miss across models with different strengths is a problem nobody could read correctly, not a hard one. Maps to rubric R03 |

Signature 1 is the one that fires regularly; the other three are rarer — consult them when a
band looks implausible rather than walking the list every round.

**The reverse error costs as much.** A band can be *unfairly hard*: one task scored 1/5 only
because the modules its spec told the solver to read were **not shipped in the image**; once
they were, it scored 4/5. Ask what the passing agents could actually see.

> **A `0/N` built from artifacts is UNMEASURED, not "too hard". Never loosen a contract on the
> strength of such a number.** Fix the artifact and recalibrate first.

---

## 4. Every known way the number can lie

Each row gives the cheapest detection. Escalate only suspicious rows.

| Lie | Looks like | Detect it |
|---|---|---|
| Wrong commit / dirty local artifact | you explain a server result using files it did not run | `git rev-parse HEAD; git status --short -- <task-dir>/; codimango task show <task> --json`; compare `headCommitSha` vs `validationCommitSha` |
| Aggregate hides one bad step | overall looks in-band while one step is 4/5 or 5/5 | `codimango task errors <task>`; read **every** position in the Avocado split |
| Grandfathered pass hides a current failure | status `passed` although current rules say too easy | same command; search `Passed under the pre-9/15 rules (current rules: ...)` |
| Local/server mismatch | local in-band, server not | `codimango task errors`; never substitute `bench run -a metacode` |
| Sampling noise | same code reads 0.4, then 0.8 | compare blob IDs with `git rev-parse <commit>:<path>`; get a second server read before redesign |
| Dead agent counted as reward 0 | a "hard" rate including attempts that never ran | §5 |
| `n_errored_trials` **undercounts** | summary claims clean execution despite dead binaries | `rg -n -e AgentInstallError -e 'n_tool_calls[^0-9]*0' <audit-dir>` |
| Cascade reachability / survivor bias | a later step is `NA`, or few survivors reached it and all passed | per-model per-step split in `task errors`; inspect per-trial step dirs |
| No-gradient failure | avocado never reaches the step; everyone who does, passes | read the exact `has no gradient` text; a conditional 1.0 is not a healthy step |
| Oracle failure suppresses calibration | agent rates absent or stale | require `Oracle validation: All 3/3 passed` |
| Load-sensitive oracle/test race | casual local oracle passes; loaded server intermittently fails | §6 |
| MetaCode binary-pull race | install failure, ~44-byte log, zero edits | §5 |
| Docker address-pool exhaustion | many trials fail before agent work | `docker network ls; docker ps; pgrep -af 'bench run'` |
| Stale / pending / missing server job | output describes an older commit, or says no trials | `codimango job list <task> --json`; rerun only if no current job exists |
| Synthetic / unconfigured local model | zero API time, or `"model":"<synthetic>"` | `rg -n -e '<synthetic>' -e 'api[_ -]?time[^0-9]*0' <job-dir>` |
| Parser matched zero tests | reward 1.0 awarded without grading anything | `rg -n '0 tests\|0 required\|matched 0\|Required tests\|Passed tests' <trial>/steps` and compare with config |
| Reward follows exit status, not parsed results | suite exits 0 while the required set is incomplete | `rg -n -F -e '$?' -e PIPESTATUS -e reward steps/*/tests/{test.sh,run_script.sh,parser.py}` |
| Mirrored config keys disagree | one component grades lowercase keys, another uppercase | `for f in steps/*/tests/config.json; do jq -e '(.fail_to_pass == .FAIL_TO_PASS) and (.pass_to_pass == .PASS_TO_PASS)' "$f"; done` |
| Repeated test names overwrite | the last occurrence passes and masks earlier failures | compare raw occurrences with parsed result keys |
| Test patch was not applied | many tests "pass" but required tests are missing | compare `Required tests that passed` vs `Passed tests`; verify the apply block in every `test.sh` |
| Wrong cascade delta | local fuzz/3-way apply hides a base-to-final step patch | apply step patches in order with **plain** `git apply` in a disposable checkout |
| Daily harness drift | an unchanged task changes because `LATEST` changed | `date -Is; codimango --version; git rev-parse HEAD`; record the relevant blob SHAs |

**Sampling variance, measured.** Django step 1 read `0.4` and later `0.8` although its
instruction, config and oracle had **identical Git blobs** at commits `6dd8848` and `8623647`
(`fff657e…`, `f01a7de…`, `5b8e806…`). At five samples one outcome moves the rate by 0.2. A
single 0.8 is a current gate failure but weak redesign evidence — get a second server read
before changing otherwise sound artifacts, and do not aim at the 0.6/0.8 boundary.

---

## 5. Dead trial versus real failure

List and download the exact server trials whenever a zero drives a decision:

```bash
codimango job list <task> --json
SWEBENCH_MT_AUDIT_DIR=$(mktemp -d -t swebench-mt-trials.XXXXXX)
codimango trial artifacts <task> --trials --download "$SWEBENCH_MT_AUDIT_DIR"

find "$SWEBENCH_MT_AUDIT_DIR" -path '*/agent/metacode.txt' -exec wc -c {} +
find "$SWEBENCH_MT_AUDIT_DIR" -name trajectory.json -print
rg -n 'AgentInstallError|n_tool_calls[^0-9]*0|segfault|No such file or directory.*metacode-bin' "$SWEBENCH_MT_AUDIT_DIR"
```

| Evidence | Classification |
|---|---|
| missing `steps/`, ~44-byte `agent/metacode.txt`, zero tool calls, no trajectory | **dead trial** — exclude from difficulty reasoning |
| full trajectory, substantial log, edits, verifier output, a specific missed assertion | real solver attempt |
| every full attempt misses the **same narrow** assertion | suspect deterministic false negative |
| full attempts miss **different fair** assertions | genuine difficulty or unstable tests — reproduce before editing |

Measured: Django's initial 0/3 was **three `AgentInstallError` failures**. Circl's reported 0/3
contained **one real attempt, one install error and one dead binary**. Conversely net-imap's
useful failures had **93/106 turns**, multi-megabyte logs, and each missed exactly **one of 17**
tests.

### The Harbor metacode pull race

`STATUS: LIVE — re-apply after every codimango update.`

`version == "LATEST"` skipped the cache, so **every trial re-pulled 197 MB and raced**.
Measured: the race killed **11 of 37 trials (~30%)**, and each death scored as a legitimate
`reward 0.0`. The fix is a local `flock` + TTL patch:

```bash
PATCH=/home/agvidit/.local/share/uv/tools/codimango/lib/python3.12/site-packages/harbor/agents/installed/metacode.py
rg -n 'LOCAL PATCH \(agvidit|pull\.lock|HARBOR_METACODE_CACHE_TTL|fcntl\.LOCK_EX' "$PATCH"
python3 -m py_compile "$PATCH"
```

Expected: the marker `LOCAL PATCH (agvidit, 2026-09-15)`, an architecture/version lock, and TTL
`3600`. **A `uv` reinstall erases it.** The sources identify no canonical backup or reapply
script — recover it only from a verified copy, never from a reconstruction from memory.

### Docker exhaustion and orphaned children

Each `k=5` job creates five bridge networks; the observed host pool capped near **15**. Run one
bench job at a time. Killing an agent does **not** kill its bench children or containers — one
stopped agent left **ten containers alive for two hours**. Never globally prune a shared host;
identify ownership first.

---

## 6. Load-induced flakiness versus a genuine task bug

Snapshot contention first (`uptime`, `nproc`, `docker stats --no-stream`, `docker network ls
--filter driver=bridge`, `pgrep -af 'codimango bench run|metacode|codex exec'`). For
timing/concurrency-adjacent work run the packaged oracle **twice** while the host is quiet.

- Install, network, container or address-pool errors **before** verifier execution, especially
  across unrelated tasks → infrastructure.
- The same assertion failing **only as load rises** → a load-sensitive task or harness race. It
  is still a genuine correctness bug in the oracle/test contract and must be fixed; *"the
  machine was busy"* does not make 2/3 usable.
- The same assertion failing under quiet **and** busy conditions → deterministic.
- Different sporadic assertions after full execution → test isolation or shared-state
  flakiness; reproduce separately.

Net-imap is the measured case: before synchronisation it was **0/300 clean under heavy load and
78/80 unloaded**; after the fix, **420/420 and 280/280** under the same loaded harness, then
packaged oracle 3/3 twice. Load exposed a real `C:`/`S:` trace-order race.

---

## 7. Local Avocado is not predictive

`STATUS: LIVE`. Same commit: **3/5 locally, 1.0 on the server.** Correlation measured at
**0.07 over 120 paired samples**. Separately, a purely local n=5 predicted the server correctly
on only **2 of 4** tasks (2026-09-18) — local said 2/5 for two tasks that came back avocado
**4/4 and 5/5**.

**Use it as a one-sided kill gate only:** local 0/5 or 5/5 means fix before pushing. Anything
between tells you nothing. Do not spend 20–40 minutes on local Avocado by default.

The one local instrument that *is* strong evidence is replaying an **exact prior server
implementation** against one changed assertion — that is causal, and it is the protocol in
`C-drive/C6-replay-verify.md`. Running a fresh local agent and treating its pass rate as the
cloud arm's future rate is the weak instrument. Do not conflate them.

---

## 8. Your own tooling manufactures false defects

`STATUS: LIVE`. Three confident false defects in one session, same root cause. Each nearly
triggered an unnecessary repair round; one appeared to contradict a Codex report that was in
fact correct.

- **Never diff `jq -r` stdout against a file.** `jq -r` appends a newline, so `diff`, `wc -c`
  and `md5sum` are all off by one trailing byte. `sed '$a\'` does **not** help. Compare parsed
  values: `python3 -c "import json;print(json.load(open(C))['test_patch']==open(P).read())"`.
- **Never count hunk bodies with an awk one-liner** — it miscounts `-` lines and the trailing
  newline. Use a prefix-aware parser that resets on `diff --git`/`index`/`---`/`+++` and counts
  only lines starting with `+` or space.
- **Do not gate on `check-symbol-reachability.py` after widening tests.** Every alias added to
  *accept* an alternative counts as another required symbol, so the UNREACHABLE count **rises**
  after a fix that made the task easier — one task went from **30 to 36** asserted symbols.
  Without `--repo` it also flags ordinary library API. Use it at the card stage only.

General rule: **when a measurement contradicts a report, re-derive the measurement before
believing it.** A regex measuring the wrong surface produces a confident false defect — the way
grepping for `:create` returned zero because the mapping was a Ruby hash whose keys render as
`create:`.

---

```
HANDOFF R2
  EXIT:      the number is classified MEASURED or UNMEASURED, with the command that proved it
  CHECKLIST: n/a — lookup table, not an act (`00-ROUTER.md` §8)
  ARTIFACTS: none — this reference writes nothing
  FACTS:     the classification, and for UNMEASURED the artifact to fix first
  OPEN:      no canonical backup/reapply script exists for the Harbor flock+TTL patch
  NEXT:      MEASURED → back to your act-file. UNMEASURED → fix the artifact, recalibrate,
             and do not touch difficulty (`C-drive/C1-read-verdict.md`).
```

## The contamination gate is content-addressed to the prompt, and is currently empty

`STATUS: LIVE`, 2026-09-30. Both found by a reviewer told to treat a null result as no signal.

### 1. Editing `instruction.md` voids the stored contamination verdict

The check keys on a `prompt_hash` over the instruction text. On `gzhttp` the stored gate JSON
recorded a hash over a **2018-byte** prompt; the file had since been rewritten to **2222 bytes**
with a different hash. **The verdict on disk was void three hours before anyone re-read it**,
and nothing in the artifact says so — it looks like a result.

This is the same hazard `B7` §4 fixes with `bundle-hash.sh`, one layer down: a stored verdict
that outlives its input reads as evidence. **Any instruction edit invalidates the contamination
key.** Re-run it, or record the verdict as stale — never carry it forward.

### 2. The decontamination index itself is empty, so the gate carries no information

The authoritative snapshot returns `{"row_count": 0, "by_prompt_hash": {}, "tasks": {}}`. Two
consecutive exports three hours apart, both empty; the freshness gate passes (1.25h against a
48h bound), so **staleness does not explain it — the upstream delta is genuinely empty.** The
API fallback returns `401` without a provisioned key.

A lookup against an index of length zero misses on *every* key. It cannot distinguish a clean
task from a contaminated one.

**What follows, and it applies to passes as much as failures:** a server-side
`Contamination check: passed / Risk: LOW` on any task validated in this window is a **vacuous
pass**, not a clearance. Treat contamination as **unmeasured** until a non-empty delta exports.
Do not cite it as evidence in either direction, and do not let a green row on the dashboard
stand in for a check that did not run.

# Signal integrity: prove the number before tuning

A pass rate is evidence only when it belongs to the intended commit, every
counted trial actually ran, the oracle is stable, and the **per-step current
server verdict** is being read. This check should prevent wasted calibration
cycles, not become ceremony: run the one-minute routine below; do the deeper
audit only when it finds a reason.

## Evidence hierarchy

| Rank | Signal | Use | Evidence |
|---:|---|---|---|
| 1 | Current server per-step Avocado verdict | Calibration truth | The gate is per step and now rejects 4/5. |
| 2 | Repeated server verdicts on identical artifacts | Directional evidence | Django moved 0.4 -> 0.8 and franz-go 0.8 -> 1.0 unchanged. |
| 3 | Local oracle and structural checks | Breakage checks | Oracle must be green; local/server structural sets differ. |
| 4 | Local Avocado | Gross debugging only | The same sparql commit was 3/5 local and 5/5 server; unchanged local runs produced 1/3 then 3/3. |

Never average local and server runs or average steps.

## Every known way the number can lie

Each row gives the cheapest detection command. Escalate only the suspicious
rows; otherwise keep moving.

| Lie | What it looks like | Detect it |
|---|---|---|
| Wrong commit or dirty local artifact | You explain a server result using files it did not run | `git rev-parse HEAD; git status --short -- <task-dir>/; codimango task show <task> --json` and compare validation/head SHAs |
| Aggregate hides one bad step | Overall rate looks in-band while one step is 4/5 or 5/5 | `codimango task errors <task>`; read every position in the Avocado split |
| Grandfathered pass hides current failure | Status says passed although current rules say too easy | Same command; search for `Passed under the pre-9/15 rules (current rules: ...)` |
| Local/server mismatch | Local Avocado looks in-band, server does not | `codimango task errors <task>`; never substitute `bench run -a metacode` |
| Sampling noise | Same code reads 0.4, then 0.8 | Compare blob IDs with `git rev-parse <commit>:<path>`; obtain a second server read before redesign |
| Dead agent counted as reward 0 | “Hard” rate includes attempts that never ran | Download/inspect every failed trial; commands below |
| `n_errored_trials` undercounts | Summary claims clean execution despite dead binaries | `rg -n -e AgentInstallError -e 'n_tool_calls[^0-9]*0' <audit-dir>` plus trajectory/log checks below |
| Cascade reachability / survivor bias | Later step is `NA`, or only a few survivors reached it and all passed | Read each model's per-step split in `codimango task errors`; inspect per-trial step directories |
| No-gradient failure | Avocado never reaches the step and every model that does passes | Read the exact `has no gradient` server text; do not treat conditional 1.0 as evidence of a healthy step |
| Oracle failure suppresses calibration | Agent rates are absent or stale | `codimango task errors <task>`; require server `Oracle validation: All 3/3 passed` |
| Load-sensitive oracle/test race | Casual local oracle passes; loaded server intermittently fails | Capture host load, run repeated oracle, compare the exact failed assertion; commands below |
| MetaCode binary-pull race | Install failure, ~44-byte log, zero edits | Verify the local Harbor patch and inspect trial signatures below |
| Docker address-pool exhaustion | Many trials fail before agent work | `docker network ls; docker ps; pgrep -af 'bench run'` |
| Stale, pending, or missing server job | Output describes an older commit or says no trials | `codimango job list <task> --json`; compare commit/status; rerun only if no current job exists |
| Synthetic/unconfigured local model | A “model” run has zero API time or `"model":"<synthetic>"` | `rg -n -e '<synthetic>' -e 'api[_ -]?time[^0-9]*0' <job-dir>` |
| Parser matched zero tests | Reward 1.0 is awarded without grading anything | `rg -n '0 tests|0 required|matched 0|Required tests|Passed tests' <trial>/steps` and compare with config |
| Reward follows exit status, not parsed required results | Suite exits 0 while required set is incomplete | `rg -n -F -e '$?' -e PIPESTATUS -e reward steps/*/tests/{test.sh,run_script.sh,parser.py}`; inspect parsed set counts |
| Mirrored config keys disagree | One component grades lowercase keys, another uppercase | `for f in steps/*/tests/config.json; do jq -e '(.fail_to_pass == .FAIL_TO_PASS) and (.pass_to_pass == .PASS_TO_PASS)' "$f"; done` |
| Repeated test names overwrite | Last occurrence passes and masks earlier failures | Compare raw occurrences with parsed result keys; `rg '<test-name>' <trial>/steps/*/verifier/test-stdout.txt` |
| Test patch was not applied | Many tests “pass,” but required tests are missing | Inspect `Required tests that passed` versus `Passed tests`; verify the test-patch apply block in every `test.sh` |
| Wrong cascade delta | Local fuzz/3-way apply hides a base-to-final step patch | Apply step patches in order with plain `git apply` in a disposable checkout |
| Daily harness drift | Unchanged task changes because `LATEST` changed | `date -Is; codimango --version; git rev-parse HEAD`; record relevant blob SHAs |

## Artifact identity and server truth

```bash
cd ~/swe-bench-pro-agvidit
git rev-parse HEAD
git status --short -- <task-dir>/
codimango task show <task> --json
codimango task errors <task>
```

Use the task JSON to compare `headCommitSha` and `validationCommitSha`. A clean
local tree is still not proof that local Avocado matches the server: the
unpinned `LATEST` harness can differ.

## Sampling variance: the same code measured 0.4 then 0.8

Django step 1 read `0.4` and later `0.8` although its instruction, config, and
oracle had identical Git blobs at commits `6dd8848` and `8623647`:

```bash
cd ~/swe-bench-pro-agvidit
for commit in 6dd8848 8623647; do
  git rev-parse "$commit:django-model-utils-fieldtracker-related-snapshot/steps/1_related_snapshot/instruction.md"
  git rev-parse "$commit:django-model-utils-fieldtracker-related-snapshot/steps/1_related_snapshot/tests/config.json"
  git rev-parse "$commit:django-model-utils-fieldtracker-related-snapshot/steps/1_related_snapshot/solution/solve.sh"
done
```

The repeated blob SHAs were `fff657e…`, `f01a7de…`, and `5b8e806…`.
At five samples, one outcome moves the rate by 0.2. A single 0.8 is a current
gate failure, but it is weak redesign evidence; obtain a second server read
before changing otherwise sound artifacts. Aim below the 0.6/0.8 boundary.

## Dead trial versus real failure

List and download the exact server trials when a zero drives a decision:

```bash
codimango job list <task> --json
codimango trial artifacts <task> --trials
SWEBENCH_MT_AUDIT_DIR=$(mktemp -d -t swebench-mt-trials.XXXXXX)
codimango trial artifacts <task> --trials --download "$SWEBENCH_MT_AUDIT_DIR"

find "$SWEBENCH_MT_AUDIT_DIR" -path '*/agent/metacode.txt' -exec wc -c {} +
find "$SWEBENCH_MT_AUDIT_DIR" -name trajectory.json -print
find "$SWEBENCH_MT_AUDIT_DIR" -path '*/verifier/reward.txt' -o -path '*/verifier/test-stdout.txt'
rg -n 'AgentInstallError|n_tool_calls[^0-9]*0|segfault|No such file or directory.*metacode-bin' "$SWEBENCH_MT_AUDIT_DIR"
```

| Evidence | Classification |
|---|---|
| Missing `steps/`, ~44-byte `agent/metacode.txt`, zero tool calls, no trajectory | Dead trial: exclude from difficulty reasoning |
| Full trajectory, substantial log, edits, verifier output, specific missed assertion | Real solver attempt |
| Every full attempt misses the same narrow assertion | Suspect deterministic false negative |
| Full attempts miss different fair assertions | Genuine difficulty or unstable tests; reproduce before editing |

Measured evidence: Django's initial 0/3 was three `AgentInstallError` failures.
Circl's reported 0/3 contained one real attempt, one install error, and one dead
binary. Conversely, net-imap's useful failures had 93/106 turns, multi-megabyte
logs, and each missed exactly one of 17 tests.

## Load-induced flakiness versus a genuine task bug

First snapshot contention:

```bash
uptime
nproc
docker stats --no-stream
docker ps --format '{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Networks}}'
docker network ls --filter driver=bridge
pgrep -af 'codimango bench run|bench run|metacode|codex exec'
```

For timing/concurrency-adjacent work, run the packaged oracle twice when the host
is quiet:

```bash
codimango bench run -p <task> -a oracle -k 3
codimango bench run -p <task> -a oracle -k 3
```

Interpretation:

- Install, network, container, or address-pool errors before verifier execution,
  especially across unrelated tasks, are infrastructure failures.
- The same task assertion failing only as load rises is a load-sensitive task or
  harness race. It is still a genuine correctness bug in the oracle/test
  contract and must be fixed; “the machine was busy” does not make 2/3 usable.
- The same assertion failing under quiet and busy conditions is deterministic.
- Different sporadic assertions after full execution suggest test isolation or
  shared-state flakiness; reproduce them separately.

Net-imap is the measured case: before synchronization it was 0/300 clean under
heavy load and 78/80 unloaded; after the fix it was 420/420 and 280/280 under
the same loaded harness, then packaged oracle 3/3 twice. Load exposed a real
`C:`/`S:` trace-order race.

## Local infrastructure traps

### MetaCode binary-pull race

```bash
PATCH=~/.local/share/uv/tools/codimango/lib/python3.12/site-packages/harbor/agents/installed/metacode.py
rg -n 'LOCAL PATCH \(agvidit|pull\.lock|HARBOR_METACODE_CACHE_TTL|fcntl\.LOCK_EX' "$PATCH"
sed -n '259,290p' "$PATCH"
python3 -m py_compile "$PATCH"
```

Expected: marker `LOCAL PATCH (agvidit, 2026-09-15)`, architecture/version lock,
and TTL `3600`. The race killed 11/37 trials (~30%). A `uv` reinstall can erase
the patch. The available records do not identify a canonical backup or reapply
script, so recover it only from a verified copy—not a reconstruction from memory.

### Docker exhaustion and orphaned children

Each `k=5` job creates five bridge networks; the observed host pool capped near
15. Run one bench job at a time. After interruption, use the load snapshot
above: killing an agent does not kill its bench children or containers. One
stopped agent left ten containers alive for two hours. Never globally prune a
shared host; identify ownership first.

## Before you believe this number: under one minute

```bash
cd ~/swe-bench-pro-agvidit
git rev-parse HEAD
git status --short -- <task-dir>/
codimango task errors <task>
uptime
pgrep -af 'codimango bench run|bench run|metacode|codex exec'
docker ps --format '{{.Names}}\t{{.Status}}' 
```

Read, in order:

1. Is the server oracle exactly 3/3?
2. Is this the intended commit, with no local artifact being confused for it?
3. What is **each** Avocado step rate? Current target is 1–3/5; 4/5 fails.
4. Does the message say grandfathered, no-gradient, pending, or no trials?
5. Is the host visibly contended or another bench job alive?

If those are clean, act. If a zero, `NA`, oracle miss, or implausible jump is
driving the decision, perform the targeted artifact audit above before editing.

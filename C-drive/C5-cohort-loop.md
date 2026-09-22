# C5 — The cohort loop: which task to work, in what order, when to park

```
ACT:    C5-cohort-loop
OWNER:  Claude
INPUT:  N tasks in flight (router §1, state S17)
OUTPUT: every discovered draft task is green or parked with a stated reason
EXIT:   the draft list is empty, or every remaining task is parked
```

```
WAVE:         3          # tasks driven per wave, worked strictly one at a time
MAX_ATTEMPTS: 5          # repair attempts per task before parking it and moving on
POLL:         30m        # sleep between freshness checks while jobs are in flight
```

This file decides **which** task to work, in what order, when to stop on it, and when to move on.
It owns no repair rule. The acts it schedules — `C1`, `C2`, `C3`, `C4`, `C6` — own those.

Two definitions this file deliberately does **not** restate:

- **What counts as an attempt** → `00-ROUTER.md` §3.
- **The definition of done** → `00-ROUTER.md` §4.

Run unattended. No act in the chain has an approval gate: `C1` writes a plan and then executes
it. **`instruction.md` findings are recorded and skipped, never escalated into an edit and never
routed through another agent** — that binds inside this loop exactly as it binds everywhere else
(→ `00-ROUTER.md` §5).

The goal of one run is: **the draft list is empty, or every task left in it is parked with a
stated reason.** Not "three tasks looked at".

---

## Phase A — Inventory every draft task, fresh, before any repair

**Discover the list; never accept one.** One call gives every axis for every task; no per-task
`task show` is needed to build the table. Read it fresh — never from a cached earlier run.

```bash
codimango task list --filter mine --limit 100 --json > /tmp/tl.json
python3 - <<'PY'
import json
ts = json.load(open('/tmp/tl.json'))
ts = ts.get('tasks', ts) if isinstance(ts, dict) else ts
for t in [t for t in ts if t.get('status') == 'draft']:
    q = t.get('qualitativeResult') or {}
    print(f"\n{t['name']}  [{t.get('format')}]  sha={str(t.get('commitSha'))[:8]}")
    print(f"  validation={t.get('validationStatus')}  "
          f"tbr={t.get('tbdReviewStatus')} (final={not t.get('tbrNotFinalized')})  "
          f"overall={q.get('overall')}")
    for v in (t.get('validationDetails') or []):
        print(f"    {v['label']:<36} {v['status']:<8} {v['detail'][:96]}")
PY
```

Which field is authoritative and which lies — including why you must match rows **by label** and
never by position — → `00-ROUTER.md` §2. Two cohort measurements worth carrying as anchors:

- Label sets differ by format. Multi-turn tasks carry either `Agentic trial-output review` **or**
  `LH: Solvability & Difficulty`, not always both; single-turn tasks add `AI assessment` and have
  no step decomposition at all.
- `aasm-error-census-attribution` had **no** `Agentic trial-output review` row while
  `job review` at the same SHA returned `GOOD / GENUINELY_HARD`; the same field that said
  `TOO_HARD` for it and for `resque-hook-phase-accounting` was contradicted by the review's own
  `Task difficulty: GENUINELY_HARD` on both.

Then, per task, expand the step gate **per step and per model** from the
`Metacode or Opus pass/fail balance` detail string, and record the done-count as `n/5` against
`00-ROUTER.md` §4.

## Phase B — Rank by cost-to-done, and say why

**STATUS: LIVE for the tiering (Tier-1 gates cost a full authoring round and a fresh cohort;
Tier-2 gates flip on a packaging fix — measured). STATUS: UNVALIDATED-PRIOR for the specific cost
integers below** — they are a working estimate, never measured against actual round counts, which
is exactly why "rank is advisory, evidence is not" (see Stop conditions).

Order **closest-to-done first, most-calibration-needed last.** The ordering is a cost estimate,
not a gate count: a Tier-1 gate (the step gate, Agentic `GOOD`) costs a full authoring round *and*
a fresh cohort to win back, while a Tier-2 gate (Structural, Oracle, TBD review) can flip on a
packaging fix.

| Remaining work | Cost |
|---|---|
| Tier-2 gate red — Structural, Oracle, TBR finalised `fail` | **1** each |
| TBR `fail` with `tbrNotFinalized: true` | **0** — pending, not a defect. Do not work it |
| A gate `pending` only because the arm never ran (`No oracle trials run`, `no countable runs`) | **1** — trigger it, do not analyse it |
| Tier-1 gate red with a **packaging or grading** root cause (`BAD_GRADING_WEAK`/`WRONG`, mirror drift, empty top-level record) | **3** |
| Tier-1 gate red needing a **difficulty or authoring** change (too hard / no gradient / too easy, `BAD_GOLDEN`, `BAD_AMBIGUOUS`) | **5** |
| **+1 per additional calibration cohort** the fix must round-trip through | **+1** each |
| The difficulty reading is **UNMEASURED** (`0/0`, all-error arms, `Insufficient legitimate sample`) | **+1**, and **never score it as "too hard"** |

Ties break on: fewer cohorts needed → more gates already green → the task that moved last round
over the one that did not.

Emit the ranked table before doing any work, with one row per task: name, done `n/5`, each gate's
state, cost, the blocking thing, and the next lever. Show a pending TBR as `pending`, never as a
bare `fail`.

**Two buckets sit outside the ranking and do not consume a wave slot:**

- **Human-blocked** — everything else is green and the only residue needs contract prose. Working
  it cannot reach done. List it with `Owner: Avocado/human` and the exact gap.
- **In flight** — jobs still running at the current SHA. Nothing to analyse yet; it re-enters the
  ranking at the next wave once results land.

Write the ranked table and both buckets to `.review/drive-<utc>.md` — the one file this act writes
outside a task directory. If the checkout has no `.review/`, write `/tmp/drive-<utc>.md` and say so
in the report. Once Phase C starts on a task, **nothing outside `<task>/` is touched.**

## Phase C — Drive the top `WAVE` tasks, one at a time

**Never run two repairs concurrently** — each spawns Docker work and parallel runs have exhausted
host memory and killed a poller mid-flight. The wave's *reading* is different: inventory calls and
trial-artifact downloads are parallel-safe and should be batched. → `00-ROUTER.md` §6.

For each of the top `WAVE` tasks in rank order, loop until the exit condition:

1. **Read state.**
   ```bash
   codimango task show   <task> --json    # validationStatus, validationDetails, tbdReviewStatus, commitSha
   codimango job review  <task> --json    # verdict, difficulty, failing rubrics, authorFeedback
   codimango task errors <task> --json    # per-gate breakdown
   ```
2. **Freshness check before analysis.** If `commitSha` ≠ your latest pushed commit for that task,
   you are reading stale results: sleep `POLL`, do not analyse, and **this does not consume an
   attempt.** → `C-drive/C1-read-verdict.md` §1.
3. **Classify:** green (§ router §4) → done, next task. Jobs still running → sleep `POLL`, repeat;
   not an attempt. Blocked → run `C1` from the top. **That counts as one attempt.**
4. **Repair** through the act `C1` routes to — `C2`, `C3` or `C4` — honouring its ownership table
   and its verification step, and exiting through `C6`.
5. **Commit and trigger**, then sleep `POLL` and return to 1.

Exit a task when green, when `MAX_ATTEMPTS` attempts are spent, or when a stop condition fires.
Then move to the next task; do not linger.

## Phase D — Next wave, until the draft list is empty

When every task in the wave has exited, **re-run Phase A from scratch.** Other sessions commit
into this checkout and gates move underneath you; a cached inventory ranks against a world that no
longer exists. Re-rank, take the next `WAVE`, repeat until either no task remains in `draft`, or
every remaining draft task is parked.

**A task parked at `MAX_ATTEMPTS` does not re-enter a later wave in the same run.** Report it.

---

## Stop conditions — report to Vidit

| Condition | What to report |
|---|---|
| All drafts green or parked | the final matrix per task plus every parked reason |
| `MAX_ATTEMPTS` reached on a task | what moved, what did not, and your best hypothesis. Move on rather than spinning |
| **Two attempts with no measurable change in any gate** | something is being treated as a fix that is not one. **Park it early** — do not spend the remaining attempts |
| Only contract-prose findings remain | report them `Owner: Avocado/human` and park — but say plainly that every other gate is green, rather than calling the task blocked |
| Rerun budget gone (3 per model) | a push is then the only trigger; say so rather than polling a dead loop |
| A change would require editing a contract file | never do it, never delegate it; record the finding, skip that thread, keep going |
| Host pressure — `MemFree` low or swap in use | stop **between** tasks, never mid-repair |

**Rank is advisory; evidence is not.** If Phase A's cost estimate is contradicted by what `C1`
measures, re-rank at the next wave and say so — do not defend the estimate.

Polling only helps while something is in flight. If nothing is running and nothing changed,
polling forever is a no-op — trigger a run or move to the next task.

---

## The learning write-back — at the end of every wave

Neither source pipeline had this, and both rotted the same way: a rule was corrected in one file
and left standing in another, with no marker saying which was current.

At the close of each wave, in **one commit**:

1. **Append every new finding** to `ledger/RULES.md` with its run anchor in `ledger/RUNS.md` —
   the id, the status, the act-file that will home it, and one sentence. A rule with no run anchor
   is a prior, not a rule: mark it `SCOPED-TO unvalidated` and say so at its site.
2. **Flip any rule this wave contradicted to `SUPERSEDED-BY <new id>` in the same commit.** Never
   leave both `LIVE`. This is the single discipline that keeps the playbook from becoming the
   thing it replaced.
3. **Count incidents, not retellings.** Repeated accounts of one incident are **one data point** —
   both source sets failed this, reading evidence volume as evidence count. If two rules cite the
   same run, say so explicitly in the ledger row.
4. Anything that contradicts a rule owned by an act-file is written **only** in the ledger here;
   the act-file's own text is amended by whoever owns that file, not by the loop.

---

## Logs

Per attempt, append one line to `<task>/audit/drive-log.md`:

```
<utc> | attempt N/5 | sha | validation=<s> tbr=<s> agentic=<verdict> | action taken | next check
```

Per wave, append the re-ranked table to `.review/drive-<utc>.md`, so the ordering history survives
a restart and a later run can see which estimates were wrong.

---

## CHECKLIST — the loop

```
[ ]  1. Inventory DISCOVERED this wave, not carried over or supplied              Phase A
        codimango task list --filter mine --limit 100 --json
[ ]  2. Rows matched by LABEL, not position; format recorded per task      router §2
[ ]  3. Step gate expanded per step AND per model for every draft task            Phase A
[ ]  4. Done score n/5 recorded per task against router §4                        Phase A
[ ]  5. Cost computed per the table; UNMEASURED tasks scored +1 and never
        labelled "too hard"                                                       Phase B
[ ]  6. Ranked table + human-blocked + in-flight buckets written to
        .review/drive-<utc>.md (or /tmp, stated)                                  Phase B
[ ]  7. Exactly one repair running at any moment; reads/downloads batched  router §6
[ ]  8. Freshness checked per task BEFORE analysis; stale read != attempt         Phase C
[ ]  9. Each blocked task entered through C1, not through a guess at the lever    Phase C
[ ] 10. Every repair exited through C6 before its commit                   router §8b
[ ] 11. Attempt counter incremented only on a pushed commit                router §3
[ ] 12. No contract file edited or delegated anywhere in the wave          router §5
[ ] 13. Tasks parked at MAX_ATTEMPTS recorded and NOT re-entered this run         Phase D
[ ] 14. "Two attempts, no gate movement" checked per task and parked early        Stop
[ ] 15. Phase A re-run FROM SCRATCH before the next wave                          Phase D
[ ] 16. Learning write-back committed: new rules appended with run anchors,
        contradicted rules flipped to SUPERSEDED-BY in the SAME commit            Write-back
[ ] 17. Per-attempt lines appended to <task>/audit/drive-log.md                   Logs
```

---

## HANDOFF

```
HANDOFF C5-cohort-loop
  EXIT:      <draft list empty | every remaining task parked, with its reason>
  CHECKLIST: <n of 17 ticked; every waived line with its reason>
  ARTIFACTS: .review/drive-<utc>.md (ranked tables, one per wave);
             <task>/audit/drive-log.md per task; ledger/RULES.md + ledger/RUNS.md commit
  FACTS:     final matrix per task; attempts spent per task; which estimates the
             evidence contradicted; rerun budget remaining
  OPEN:      every parked task with its reason; every Owner: Avocado/human finding
  NEXT:      none — report to Vidit
```

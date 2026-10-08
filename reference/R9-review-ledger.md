# R9 — the per-task REVIEW LEDGER

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

`STATUS: LIVE`, 2026-09-23. Every task carries `<task>/audit/REVIEW-LEDGER.md`. It is written by
`C1`, read by `C2`–`C4`, and **gated by `B5` before every push**.

## Why

`connect-go` shipped with every local gate green and came back `BAD_GRADING_WEAK` on R06, R07 and
R12. Those findings existed, in full, in the agentic review — and nothing in the pipeline forced
the next version to answer them. Without a ledger, each push is judged only against the checks the
author happened to run *this* round, so a defect can be reported, not fixed, and re-shipped.

**The rule: a finding raised at any version stays OPEN until it is fixed with evidence, or is
proven obsolete by a pivot. Never "we changed a lot since then".**

## What to pull — all of it, every version

```bash
# Evidence lives OUTSIDE the task bundle. Trial artifacts are tens of MB of *.log
# and zero-byte files, which preflight TIER 0's file inventory flags -- and they are
# not part of the task. Keep only the LEDGER inside <task>/audit/.
T=<task>; V=<n>; D=~/swebench-playbook/.e2e/evidence/$(basename $T)-v$V; mkdir -p $D

codimango task errors  $T --json          > $D/task-errors.json      # per-step bands, gate strings
codimango task show    $T --json          > $D/task-show.json        # validationDetails, tbdReviewStatus
codimango job review   $T --json          > $D/job-review.json       # rubrics + evidence + attemptResults
# NOTE: .tbdReviewDetails is null on every task checked so far -- this yields nothing.
codimango task show    $T --json | jq -r '.tbdReviewDetails.full_assessment // "null"' > $D/tbd-assessment.txt
codimango task reviews $T --full          > $D/human-reviews.txt     # SINGULAR 'task'; 'tasks reviews' is rejected

# trials + trajectories — the part most often skipped
# NOTE: every one of these prints a one-line support banner BEFORE the JSON.
# Pipe through `tail -n +2` or jq dies on "Invalid numeric literal at line 1".
codimango job list  $T --json | tail -n +2 > $D/jobs.json
# jobs.json is an OBJECT: {jobs:[...], commitTimes:[...], total, ...} -- not an array.
# The arm and the commit live in .config, not at the top level, and the top-level
# avocado*/agent* fields are null. Map the arms first:
jq -r '.jobs[] | [.id, (.config.agentName//"-"), (.config.commitSha//"none")[0:7], .status] | @tsv' $D/jobs.json
# `codimango api ...` does NOT exist -- the subcommand is `trial`, singular, top level.
for J in <the job ids you actually want>; do
  codimango trial list $J --json | tail -n +2 > $D/trials-$J.json
done
# every non-degenerate arm, and EVERY failing trial in it:
codimango trial artifacts <trialId> --download $D/trials/<trialId>
# the per-test failure census -- this is the C6 corpus, and it is one line:
grep -ho 'Missing tests: \[.*\]' $D/trials/*/verifier/test-stdout.txt
```

**The trajectories are not optional.** `verifier/test-stdout.txt`, `verifier/output.json` and
`steps/*/verifier/run-script-stdout.txt` (whose JSON carries `examples[].exception.message`) are
where the *actual* failure lives. A reviewer's prose is a summary of these; the quoted exception is
the evidence. → `C-drive/C6-replay-verify.md` for replaying them against a proposed change.

**Read the human reviews too.** `codimango task reviews --full` (singular `task`) is authoritative and carries
sourcing and novelty rejections that `job review` does not surface at all.

## Ledger format

One section per version, append-only. **Never edit or delete a past entry** — supersede it.

```markdown
## v3 — sha 689577d — 2026-09-23 — verdict: FAILED
pulled: task-errors, task-show, job-review, tbd-assessment, human-reviews,
        trials 3 jobs / 11 trials / 6 failing  -> audit/evidence/v3/
bands:  avocado 1|1  opus 0.4|1  gpt 0.8|1     oracle 2/3

| id | rubric | finding | evidence | status |   <!-- status column is what B5 greps -->
|---|---|---|---|---|
| F3-01 | R06 | tests miss invalid UTF-8 and HTTP-forbidden trailer names | job-review.json:R06 | OPEN |
| F3-02 | R12 | golden lets an Authorization trailer diverge across protocols | job-review.json:R12 | OPEN |
| F3-03 | R09 | flaky inherited p2p context-deadline test -> oracle 2/3 | trials/…/test-stdout | OPEN |
```

Plus a **carry-forward table at the top**, regenerated every version — every finding ever raised,
with its current status:

| status | meaning |
|---|---|
| `OPEN` | not yet addressed. **Blocks the next push.** |
| `FIXED v<n>` | addressed, with the commit and the check that proves it |
| `OBSOLETE-BY-PIVOT v<n>` | the thing it describes no longer exists — see the pivot test below |
| `WAIVED v<n>` | deliberately accepted, with a named owner and a reason |
| `ESCALATED v<n>` | **only an external owner can fix it** — Avocado for contract prose, or the human. Does **not** block `B5` GATE ZERO. |
| `DEFERRED-TO-POST-PUSH v<n>` | **the remedy is an action that cannot run before the push it applies to** — a rerun, a missing model arm, anything measured against the new SHA. Does **not** block GATE ZERO; picked up by `B5` §7 instead. |

**Why `ESCALATED` exists.** `STATUS: LIVE`, 2026-09-25 — without it the ledger deadlocks. A
finding whose only remedy is `instruction.md` cannot be fixed by the agent that found it, cannot be
self-waived twice, and therefore stays `OPEN` forever — which means `B5` GATE ZERO blocks **every
future push of that task** with no change in its facts. A task can then be unpushable because it
correctly reported something it is forbidden to repair.

`ESCALATED` requires, every version, all four:

- the named owner — `Avocado` or `human`, never the agent itself
- exactly what the external owner would have to change
- why the agent may not do it (the rule and its section)
- **re-statement in the current version's section.** It does not decay into silence; an escalation
  nobody acts on stays visible, it just stops blocking.

**Why `DEFERRED-TO-POST-PUSH` exists.** `STATUS: LIVE`, 2026-09-29 — the same deadlock as
`ESCALATED`, one step later. A reviewer asked for a model arm to be run *at the commit under
review*; that arm can only be dispatched against a pushed SHA, so the finding cannot be closed
before the push and GATE ZERO blocks the push that would let it close. It requires, every version:

- the exact command that will close it, written out
- execution **in the same working session as the push** — it is a deferral of minutes, not of
  intent. Carry it into `B5` §7 POST-SUBMISSION and close it there with the output.
- if the session ends with it unclosed, it reverts to `OPEN` and blocks the next push.

It is **not** for work you would rather do later. If the remedy could run before the push, it is
`OPEN` and it runs now.

An agent may **not** self-assign `ESCALATED` to something it could fix. If the remedy is a test, a
patch, a config or an environment change, it is `OPEN` and it is yours.

## The pivot test — the only way a finding leaves OPEN without being fixed

A task changes shape over versions, and some findings genuinely stop applying. But
*"we rewrote a lot"* is not a disposition. **Both of these must hold, each with evidence:**

1. **The artifact it cites is gone.** The test, assertion, file, or contract sentence the finding
   points at no longer exists at the current SHA. Show the `grep` returning nothing.
2. **The behaviour it describes is no longer in the contract.** Not merely graded differently —
   the requirement itself is gone. Quote the contract line that used to carry it and show its
   absence.

If only (1) holds, the finding is **still OPEN** — you moved the code, not the requirement. That
is the case that re-ships a defect under a new file name.

**A pivot large enough to obsolete findings wholesale is a different task.** If more than half the
prior findings would go `OBSOLETE-BY-PIVOT` in one version, stop and say so: you are rebuilding,
and the honest move is a fresh task with the old one's ledger cited as prior art.

## Escalation — this is where the playbook gets better

**A finding that appears on two different tasks is not a task defect, it is a playbook defect.**
When you record one, check the other tasks' ledgers for the same rubric and shape. If it recurs:

- fix the task, then
- fix the **act that let it through**, with the measurement attached (`00-ROUTER.md` §8a), and
- note the playbook commit in the ledger entry.

R06/R07/R12 on `connect-go` produced three new `B3` gates and the `B5` p2p flake screen this way.
That is the intended output of this file, not a side effect.

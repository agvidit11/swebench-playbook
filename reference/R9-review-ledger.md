# R9 — the per-task REVIEW LEDGER

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
T=<task>; V=<n>; D=$T/audit/evidence/v$V; mkdir -p $D

codimango task errors  $T --json          > $D/task-errors.json      # per-step bands, gate strings
codimango task show    $T --json          > $D/task-show.json        # validationDetails, tbdReviewStatus
codimango job review   $T --json          > $D/job-review.json       # rubrics + evidence + attemptResults
# NOTE: .tbdReviewDetails is null on every task checked so far -- this yields nothing.
codimango task show    $T --json | jq -r '.tbdReviewDetails.full_assessment // "null"' > $D/tbd-assessment.txt
codimango task reviews $T --full          > $D/human-reviews.txt     # SINGULAR 'task'; 'tasks reviews' is rejected

# trials + trajectories — the part most often skipped
codimango job list  $T --json             > $D/jobs.json
for J in $(jq -r '.[].id' $D/jobs.json); do
  codimango api trials list $J --json     > $D/trials-$J.json
done
# every non-degenerate arm, and EVERY failing trial in it:
codimango api trials artifacts <trialId> --download $D/trials/<trialId>
```

**The trajectories are not optional.** `verifier/test-stdout.txt`, `verifier/output.json` and
`steps/*/verifier/run-script-stdout.txt` (whose JSON carries `examples[].exception.message`) are
where the *actual* failure lives. A reviewer's prose is a summary of these; the quoted exception is
the evidence. → `C-drive/C6-replay-verify.md` for replaying them against a proposed change.

**Read the human reviews too.** `codimango tasks reviews --full` is authoritative and carries
sourcing and novelty rejections that `job review` does not surface at all.

## Ledger format

One section per version, append-only. **Never edit or delete a past entry** — supersede it.

```markdown
## v3 — sha 689577d — 2026-09-23 — verdict: FAILED
pulled: task-errors, task-show, job-review, tbd-assessment, human-reviews,
        trials 3 jobs / 11 trials / 6 failing  -> audit/evidence/v3/
bands:  avocado 1|1  opus 0.4|1  gpt 0.8|1     oracle 2/3

| id | rubric | finding | evidence | status |
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

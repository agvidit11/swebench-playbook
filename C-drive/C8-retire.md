# C8 — Retire a task, and the budget that forces the question

```
ACT:    C8-retire
OWNER:  Claude proposes with evidence · Vidit decides · nothing is deleted
INPUT:  a task that has hit a budget line or a terminal condition
OUTPUT: a RETIRED verdict with its reason, or an explicit written decision to continue
EXIT:   the task is either retired with its ledger preserved as prior art, or carries a
        named reason it is still alive and what will be different next commit
```

`STATUS: LIVE`, 2026-09-29.

## Park is not retire, and we only had park

`C5` can **park** a task: stop for now, come back later. Nothing in this runbook could ever say
*this task will not work, stop spending on it.* So every draft stays in the cohort loop
forever. We have **31 drafts**. At three new tasks a day that list grows faster than it clears,
and the loop re-examines dead tasks indefinitely because nothing is allowed to kill one.

| verdict | meaning | re-enters the loop? |
|---|---|---|
| `PARKED` | blocked on something external or cheaper later | **yes** |
| `RETIRED` | will not be worked again under this task name | **no** |

## The budget — measured on our own corpus, not borrowed

Commits per task, against outcome, over the whole portfolio:

| | n | median | max |
|---|---:|---:|---:|
| **accepted** | 8 | 6.5 | **10** |
| failed | 23 | 6 | 22 |

**No task has ever been accepted after more than 10 commits.** Meanwhile failures run to 22 —
`ruby-terraform-plan-model-empty-container-path-loss` sits at 22 and is still failing, twelve
commits past the point where anything in our history has ever paid off.

```bash
git -C ~/swe-bench-pro-agvidit rev-list --count HEAD -- <task>
```

| count | what it means |
|---|---|
| ≤ 6 | normal. Half of all accepted tasks reached acceptance by here. |
| 7–10 | **still plausible, but you are in the tail.** Name what is different about this one. |
| > 10 | **outside the entire accepted distribution.** Continue only with a written reason that identifies something not yet tried — not "one more calibration run". |

This is a forcing question, not an execution limit. A task at 11 commits is not forbidden; it
is required to justify itself against the fact that nothing has ever been accepted from there.

### The budget applies GOING FORWARD. It is not retroactive.

`STATUS: LIVE`, 2026-09-29 — set the hour the budget was written, because the first version of
this file got it wrong.

**The distribution above was measured on tasks built without the gates that now exist.** Every
one of those commits predates `B6` (run the reviewers yourself), `B7` (classify before you
count), `A4` (search the whole corpus), `C8` (this file), the authorship audit and the Avocado
templates. A task that took 22 commits was not necessarily a bad task — it was a task iterating
blind, discovering server-side what a local gate would now catch in one pass.

So:

- **Do not retire an existing task on commit count alone.** The count measures the absence of
  structure at least as much as it measures the task.
- The budget binds tasks **built under the current gates**. For those, the count is a real
  signal, because the cheap discoveries have already been made locally.
- **Re-derive the distribution** once there are enough post-gate tasks to measure. The numbers
  above are a baseline from a worse process and should be expected to fall.

The eight tasks currently over budget are **flagged, not condemned**. Review them later, on
their merits and with the new gates run against them — not on a number produced by the era
that made them expensive.

There is a general lesson here worth more than the rule: **a threshold fitted to how you used
to work will condemn exactly the work that taught you to change.** Check what a distribution
was measured under before you make it a law.

## Terminal conditions — retire without needing the count

1. **Unclearable provenance.** An L3 `CONTAMINATED` record that survived a genuine re-author.
   `dropshot` is the case: MetaCode re-authored the flagged file, the push validated at that
   commit, and the verdict held at `matchScore 0.061`. If the pending verdicts confirm it, the
   record is keyed to task+file and the task name is spent. **Retire the name, not the idea.**
2. **Late `COLLIDES`.** A peer task on the same upstream repo or the same seam
   (`A4`). The work is not salvageable by tuning; it was never novel.
3. **Already fixed at base.** The reporter's example passes at `base_commit`
   (`feedback_swebench_repro_verify_before_scaffold`).
4. **Two consecutive commits with no measurable movement in any gate.** `C5` already says park
   early here; past 10 commits the same signal means retire.

## What retiring does NOT mean

**Nothing is deleted and nothing is wasted.** A retired task keeps its review ledger (`<task>/audit/`, per `reference/R9-review-ledger.md`),
and that ledger is *prior art for the replacement*: the findings, the bands, the trajectories
and the reason it died all transfer. A re-created task that cites a retired one's ledger starts
with the failure modes already mapped.

**Retire the name, not the idea.** For a provenance death in particular, the sourcing, the
contract and the graded set are all still good — only the task identity is burned.

## Proposing a retirement

Claude proposes; Vidit decides. A proposal is not an argument, it is evidence:

```
RETIRE PROPOSAL: <task>
  commits:        <n>   (accepted distribution: median 6.5, max 10)
  terminal:       <which condition, or none>
  gates still red: <list>
  what moved in the last 3 commits: <per-gate delta, or "nothing">
  what has NOT been tried: <be specific, or write "nothing material">
  salvageable:    <the sourcing / contract / graded set worth carrying forward>
  recommendation: RETIRE | CONTINUE because <what will be different>
```

If "what has NOT been tried" is non-empty and cheap, that is a `CONTINUE`, whatever the count
says. The budget exists to force the question, not to answer it.

## CHECKLIST

```
[ ] 1. Commit count measured, not estimated
       proof: the rev-list output
[ ] 2. Checked against the accepted distribution (median 6.5, max 10)
       proof: which band it falls in
[ ] 3. Every terminal condition checked explicitly, each yes/no
       proof: the four-line list
[ ] 4. Per-gate movement over the last 3 commits stated
       proof: the deltas, or "nothing moved" said plainly
[ ] 5. "What has not been tried" answered honestly, including "nothing material"
       proof: the line
[ ] 6. Ledger preserved and named as prior art for any replacement
       proof: the path
[ ] 7. Proposal put to Vidit. Claude never retires a task unilaterally.
       proof: the proposal block
```

## HANDOFF

```
EXIT:       RETIRED | CONTINUE, with the reason
CHECKLIST:  <7 lines above with proofs>
ARTIFACTS:  the retire proposal; the preserved ledger path
FACTS:      <commit count; terminal conditions met; last-3-commit movement>
RUNG:       <rung at retirement — a task can die at L1>
UNVERIFIED: <anything asserted about why it cannot work that was not measured>
OPEN:       <the salvageable parts and where they should go next>
NEXT:       A4 corpus check before re-creating the idea under a new name
```

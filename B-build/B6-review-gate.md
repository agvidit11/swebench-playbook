# B6 — Run the reviewers yourself, before the server does

```
ACT:    B6-review-gate
OWNER:  Claude dispatches · one isolated subagent per reviewer · findings route to the
        act that owns the artifact (never repaired here)
INPUT:  a task that has passed B5 §1-§5 — preflight 0, oracle 3/3, diff read
OUTPUT: <task>/audit/review-gate/<reviewer>.json, one per installed reviewer
EXIT:   `tools/review-gate.sh <task> check` exits 0 — every installed reviewer returned
        the exact verdict `Accept` with zero Critical and zero High
```

`STATUS: LIVE`, 2026-09-29. **This act exists because of one fact:**

> `codimango job review` **cannot review an unpushed local tree.** It resolves a server-side
> commit and its validation artifacts.

So every rubric failure is discovered a cohort late — unless you run the reviewers yourself
first. **Do not wait until the push to discover rubric failures.** Treat the server's Agentic
Full-Task Review as confirmation of something you already know, not as the thing that tells you.

## Why this is the highest-leverage act we have

The target is **2 of 3 accepted on first try**. That is not reachable by repairing faster; it
is only reachable by being right before the server sees anything. And we were leaving the
cheapest possible check on the table: **four of these reviewer skills were installed on this
machine and we ran none of them.** `B5` §2 walks the same 17 axes *from memory* — a self-scored
recollection of what a reviewer would say, instead of the reviewer.

A self-score is not a review. It shares an author with the thing it is reviewing.

## The reviewers

```bash
~/swebench-playbook/tools/review-gate.sh <task> plan     # resolve paths, print dispatch plan
~/swebench-playbook/tools/review-gate.sh <task> check    # validate verdicts, exit 1 if not clean
```

| reviewer | resolves from |
|---|---|
| `review-task-swebench-v2` | `~/.llms/skills/claude-templates/` |
| `review-task-swebench-multiturn` | team-aai bundle (newest by `sort -V`) |
| `aai-code-review` | `~/.llms/` |
| `review-quality-swebench-skills` | bundle — the G5/G6–G14/G15/G17–G19 quality gates |
| `check-contamination-v2` | `~/.llms/` |
| `verify-task-provenance` | `~/.llms/` |
| `test-quality-verifier` | **NOT INSTALLED.** A named gap, not a silent omission — record it in the ledger every version until it is available. |

The runner resolves `~/.llms` first, then the newest team-aai bundle. It reports an unresolved
reviewer rather than skipping it.

## Dispatch — one subagent per reviewer, and they do not talk

**Each subagent reads only its own `SKILL.md` and reviews only the task directory.** Do not hand
one agent several reviewers and do not summarise one reviewer's findings into another's prompt.
Two reasons, both measured elsewhere in this playbook:

- a reviewer told what a previous reviewer found will confirm it instead of looking (`C7` §3 —
  the independent re-read found a defect the author had already talked themselves out of)
- shared context is how one agent's paraphrase becomes another's evidence, which is exactly the
  boilerplate failure the checker below blocks

Brief each with: the skill path, the task path, and *nothing about what you expect*. Require the
verdict JSON the `plan` output specifies.

## The bar

**Exact verdict `Accept`, zero Critical, zero High.** Not "mostly clean", not a count.

Three rules the runner enforces mechanically, all borrowed from a portfolio that clears this bar
routinely:

1. **No aggregates.** `11 / 17 passed` is not evidence and neither is an `all_pass` boolean.
   Every rubric is recorded by identifier with its own evidence line.
2. **Identical evidence reused across more than three checks blocks the gate.** This is the
   anti-boilerplate rule. "Reviewed against current bundle" pasted six times is one check done
   once and five not done at all.
3. **`NOT_FOUND`, `NOT_SUPPORTED`, skipped and unavailable are NO SIGNAL — not clearance.**
   A contamination check that found nothing because it could not run has not cleared anything.

## What this act may NOT do

**It finds; it does not fix.** Every finding routes to the act that owns the artifact
(`00-ROUTER.md` §5) — `C2` for a graded-set defect, `B2`/Avocado for contract prose, `B4` for
packaging. Repairing in place here means the reviewer that found it never re-runs against the
repair.

And ownership is decided by the mismatch, not the label: **a rubric name is not ownership
evidence.** A spec–test mismatch caused by an over-constrained *test* is a test defect, not an
instruction defect, however the rubric is worded. Reaching for `instruction.md` first is both
the wrong fix and the one we are least allowed to make.

## Re-review after a repair

Re-run the **whole** gate, not the reviewer that complained. A fix that clears R06 by widening
the graded set can break R08 by over-pinning, and only the reviewer you didn't re-run would
have caught it. On re-review, re-execute each prior finding and mark it `fixed`, `still_open`
or `inconclusive` — never carry a finding forward as "addressed" without re-running its check.

## CHECKLIST

```
[ ] 1. `review-gate.sh <task> plan` run; every reviewer resolved or recorded UNRESOLVED
       proof: the plan output
[ ] 2. One subagent per reviewer, isolated — no shared context, no expectations in the brief
       proof: the dispatch list
[ ] 3. A verdict JSON exists for every installed reviewer
       proof: `ls <task>/audit/review-gate/`
[ ] 4. `review-gate.sh <task> check` exits 0
       proof: the output and `echo $?`
[ ] 5. Every finding routed to its owning act — none repaired inside this act
       proof: finding -> act table
[ ] 6. test-quality-verifier's absence recorded in the ledger this version
       proof: the ledger line
[ ] 7. After any repair, the FULL gate re-run, not just the complaining reviewer
       proof: the second check output
```

## HANDOFF

```
EXIT:       <check exit code; per-reviewer verdict line>
CHECKLIST:  <7 lines above with proofs>
ARTIFACTS:  <task>/audit/review-gate/*.json
FACTS:      <reviewers installed vs resolved; which bundle version supplied which>
RUNG:       <L0-L3>
UNVERIFIED: <any reviewer that could not run, and what it would have covered>
OPEN:       <findings routed but not yet closed, with their owning act>
NEXT:       B5 §6 — the pre-submission checklist, with 6d satisfied
```

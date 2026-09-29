# A4 — Search the whole corpus, by engineering concept

```
ACT:    A4-corpus-prior
OWNER:  Claude
INPUT:  a candidate repo (from A1) or a candidate shape (from A2), before A3 gates it
OUTPUT: peer tasks on the same SHAPE across the whole org, with a same-shape verdict
EXIT:   every candidate carries a corpus verdict — CLEAR, ADJACENT, or COLLIDES —
        with the queries that produced it
```

`STATUS: LIVE`, 2026-09-29.

## The capability we were missing

`codimango task list --filter all` **silently narrows to caller-owned tasks.** We proved it —
it returns our own 48 no matter what is asked. And `gh repo list codimango` caps at 1000 of
~5,105 repos (`reference_swebench_dedup_corpus`). So both of our routes into the corpus are
blind past our own work, which means **every novelty and dedup judgement we have made was made
against 1% of the corpus.**

Content search is not subject to either limit:

```bash
gh search code '<engineering concept> multi-turn org:codimango' --limit 100 \
   --json repository,path,url
```

Measured 2026-09-29: `connection pool multi-turn org:codimango` → 20 hits across **17 distinct
author repos**, none of them ours. That is the corpus we have been unable to see.

**Search concepts, not repository names.** A peer task on the same *shape* in a different
language and a different library is the collision that matters and the one a name search never
finds. Concepts that have paid: caching, migrations, connection pools, query typing, lifecycle
management, storage engines, replication, reactive subscriptions, data ingestion, retry and
backoff, cancellation, atomicity, pagination, schema evolution.

## Two uses, and the dedup one is the stronger

### 1. Dedup — this is the load-bearing use

`feedback_swebench_intra_benchmark_dedup` says public novelty is not benchmark-cleanliness, and
that a peer can be on the same repo and commit as you. That gate has been running against a
corpus slice we now know was ~1%. Run these **before scaffolding**, not after:

```bash
T=<owner>/<repo>
gh search code "$T org:codimango" --limit 100 --json repository,path,url        # same upstream
gh search code "<your shape in words> org:codimango" --limit 100 --json repository,path,url
gh search code "<the key symbol you will grade> org:codimango" --limit 50 --json repository,path
```

| result | verdict |
|---|---|
| no peer on the upstream repo, none on the shape | `CLEAR` |
| peers on the shape, different upstream and different seam | `ADJACENT` — record them, proceed, say why they differ |
| a peer on the **same upstream repo**, or the same shape at the same seam | `COLLIDES` — do not scaffold. → `A3` GATE 1 |

### 2. Prior — weaker, and be honest about why

You can read peer task *content* across the org. You **cannot** read peer task *status* — the
server scopes `task show` to you. So this gives you **what shapes are being built, not what
shapes get accepted.** It is a prior on saturation and convention, not on acceptance.

Do not launder it into more than that. A shape appearing forty times means forty people had the
idea, which is an argument against it on novelty at least as much as it is an argument for it
on calibration.

## Analogue does not mean clone

Borrowed, and it is the right rule:

> **"Reuse the engineering pattern. Never reuse the reference task's exact behavior, names,
> instruction, tests, or solution."**

| weak analogue — worthless | strong analogue — usable |
|---|---|
| same language or library name | same abstraction or **architectural seam** |
| overlapping keywords | comparable state transition or failure mode |
| superficially similar feature | a real dependency between the two steps |
| copying the behavior | transferring the **challenge shape** without the behavior |

The transferable unit is a sequence like *stateful capability → dependent observability*, not a
feature. If you can describe what you are reusing without naming a single symbol from the peer
task, it is a pattern. If you cannot, it is a clone.

## Where we must NOT copy the reference implementation

The tool this act is modelled on **excludes its own author's repo from analogue search by
default.** For them that suppresses ~49 of the most similar tasks in existence — convenient,
not safe, and it is the mechanism behind a portfolio of 52 task dirs across only 25 upstream
repos, overwhelmingly one domain.

**We do the opposite: always include our own repo.** Our failure mode is not theirs. They risk
homogenising toward a template; we risk re-mining a repo we already used and shipping a peer
collision with ourselves. `swe-bench-pro-agvidit` is the *first* thing to search, not the
excluded one.

## What this act does not do

It does not gate. It produces a verdict that `A3` GATE 1 consumes. A `COLLIDES` here is a
factual veto there; an `ADJACENT` is recorded and argued, not silently dropped.

And it does not replace the reporter-example repro (`feedback_swebench_repro_verify_before_scaffold`).
A clean corpus verdict on a task already fixed at base is still a dead task.

## CHECKLIST

```
[ ] 1. Upstream-repo search run across the whole org, not just ours
       proof: the query and hit count
[ ] 2. Shape search run in CONCEPT words, not repo or symbol names
       proof: the concepts queried
[ ] 3. Our own repo included in the search, never excluded
       proof: the query string
[ ] 4. Verdict recorded: CLEAR / ADJACENT / COLLIDES, with the peers named
       proof: the verdict line and the peer list
[ ] 5. For ADJACENT, a written reason the seam differs
       proof: the reason, one line per peer
[ ] 6. Prior used as saturation evidence only — NOT claimed as acceptance evidence
       proof: the wording of the claim
```

## HANDOFF

```
EXIT:       <CLEAR | ADJACENT | COLLIDES, with peer task paths>
CHECKLIST:  <6 lines above with proofs>
ARTIFACTS:  the queries run and their raw hit lists
FACTS:      <peers found on the same upstream; peers found on the same shape>
RUNG:       n/a — this act precedes a task
UNVERIFIED: <peer acceptance status, which is not visible to us by construction>
OPEN:       <ADJACENT peers whose seam difference is asserted but thin>
NEXT:       A3 GATE 1 consumes this verdict
```

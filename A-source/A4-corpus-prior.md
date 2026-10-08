# A4 — Search the whole corpus, by engineering concept

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

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
| a peer on the **same upstream repo at the same seam**, or the same shape at the same seam | `COLLIDES` — do not scaffold. → `A3` GATE 1 |
| a peer on the **same upstream repo at a different seam** | `ADJACENT` — record it, write a **hard exclusion zone** naming the files, the defect class and the era it owns, and carry that zone into `A3` GATE 1 as a factual veto list |

> **Why the `COLLIDES` row says "at the same seam" and did not always.** `STATUS: LIVE`,
> 2026-09-30. As originally written the row read *"a peer on the same upstream repo"*, full stop —
> which kills any repo that has ever hosted one peer task. That is not what the rest of the
> playbook says: `A1` G1's kill threshold is *"any peer task on this repo's **subsystem/invariant**"*
> and `A1` §3 ranks collisions by commit and struct, not by repo (*"same repo + same commit + same
> struct beats same-file-different-commit"*). Read literally the old row would have killed every
> repo in a distributed-systems lane and most of our own portfolio. Measured on `belaban/JGroups`:
> one peer exists (`codimango/CtrlG_DetectPatch`), on the message-authentication gate applied to
> membership-coordination responses, pinned to a 2016 CVE-fix commit, in a different benchmark
> family — a decade and a subsystem away from anything the run went on to propose. The right
> output there is an exclusion zone, not a dead repo.

### 2. Prior — weaker, and be honest about why

You can read peer task *content* across the org. You **cannot** read peer task *status* — the
server scopes `task show` to you. So this gives you **what shapes are being built, not what
shapes get accepted.** It is a prior on saturation and convention, not on acceptance.

Do not launder it into more than that. A shape appearing forty times means forty people had the
idea, which is an argument against it on novelty at least as much as it is an argument for it
on calibration.

## Read the accepted task's instruction — as a SIZE and SPECIFICITY exemplar

`STATUS: LIVE`, 2026-09-30. Do this at the START, before authoring, not as a rescue.

**Source the exemplar from OUR repo, because peer acceptance is invisible by construction.**
`STATUS: LIVE`, 2026-09-30. This section says to read an *accepted* peer's instruction; the section
immediately above it says the server scopes `task show` to us, so we cannot see any other author's
acceptance. Both are true, and the only way to satisfy them together is to take the exemplar from
`swe-bench-pro-agvidit`, where acceptance **is** visible:

```bash
codimango task list --filter all --json | jq -r '.[] | select(.validationStatus=="passing" and .tbdReviewStatus=="pass") | .name'
```

Then pick one whose **subject matter is unrelated to your candidate** — that is a feature, not a
compromise. An exemplar from an adjacent domain is the transposition risk this section forbids;
an exemplar from a distant one can only teach size, structure and altitude. Reading a peer task on
your own upstream's *family* is the maximal-risk case and should not be done at all.

Once `A4` finds peer tasks on your shape, **open the instruction of an accepted one and measure
it**: how long is it, how specific does it get about observable behaviour, where does it stop.
That calibrates the two dimensions we are worst at — our accepted instructions run 154–230 words
against a reference portfolio median of 393, and our contracts routinely defer the thing that is
graded.

It feeds `B2`'s computed cap directly: `initial` mode uses `clamp(45 × obligations, 250, 600)`,
and a real accepted instruction on a similar shape tells you whether your obligation count is
plausible before you have written a word.

**The hard boundary, and it is the whole difference between this and plagiarism:**

> The reference supplies an instruction **pattern and size example, never target behaviour.**

Never send the reference to Avocado as content to rewrite. Never transpose its domain concepts,
API names, state machine or feature structure. You are reading it the way you would read a
well-written bug report from another team — for register and altitude, not for subject.

If you cannot state what you took from it without naming a single symbol from that task, you
took the right thing.

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

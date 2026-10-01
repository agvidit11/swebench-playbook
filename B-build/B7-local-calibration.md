# B7 — Local calibration: forecast, freeze, ladder

```
ACT:    B7-local-calibration
OWNER:  Claude
INPUT:  HANDOFF B4 — oracle 3/3 — and a B6 review gate that exits 0
OUTPUT: a per-step local band from FIVE VALID TERMINAL attempts, bound to a bundle hash
EXIT:   every step in 1-3 of 5 valid terminal attempts, or a written decision to push
        anyway with the reason
```

`STATUS: PROVISIONAL`, 2026-09-29. **This act contradicts `A3` §399 and that conflict is the
point of the file.** Read this section before using it.

## The conflict, stated honestly

`A3` §399 says local Avocado calibration is worthless as a predictor:

> "Local Avocado pass-rate is **NOT** predictive. Same commit: **3/5 locally, 1.0 on the
> server**; correlation **0.07 over 120 paired samples**. It is a one-sided kill gate only."

That is 120 paired samples and it is ours. It is not lightly set aside.

But the org's highest-throughput author local-calibrates to 1–3/5 before every push and clears
review at a rate we do not approach. Both cannot be simply true — and their protocol says why:

> "Before counting any model failure as difficulty, **classify it from the terminal verifier
> evidence**. `GRADING_FAILURE`, verifier/environment failure, missing or malformed reward, and
> an unclassified failure **do not establish difficulty**. Repair the owning surface and rerun
> until each required job contains **five valid terminal attempts**. Keep infrastructure
> exclusions visible, but **do not include them in the five-attempt denominator**."

And, asked directly why local and server diverge: *"Most of the time, it's because of timeout.
You have to change your AI agent when you review your avocado failures to make sure that you are
not treating local failures as legit failures."*

**The hypothesis this file tests: our 0.07 correlation measured raw pass rates, and raw pass
rates are mostly infrastructure noise.** A denominator that silently includes timeouts, agent
install failures and malformed rewards cannot correlate with anything. If that is right, local
calibration over *valid terminal attempts only* is a different instrument from the one we
measured and rejected.

**It is a hypothesis.** It stays `PROVISIONAL` until we have paired samples of our own with
classified denominators. Until then `A3` §399 still governs the *kill* decision: local 0/5 or
5/5 means fix before pushing. What this act adds is a cheaper, classified read — not permission
to trust a middling local number.

**How to settle it:** record `(local valid-terminal band, server band)` on every task from here.
Twenty pairs decides it. If the correlation stays near zero with a classified denominator, this
file is wrong and `A3` §399 wins outright — delete this act and say so.

## 1. Classify before you count — the whole idea

A trial contributes to the denominator only if it reached a **terminal verifier verdict**.
Everything else is replaced, not counted:

| outcome | counts as difficulty? |
|---|---|
| numeric terminal reward (0 or 1) | **yes** — even if the agent phase threw an HTTP 500 |
| `GRADING_FAILURE` | no — repair the grader, rerun |
| agent timeout | no — see §2 |
| environment / verifier failure, agent-install error | no |
| missing or malformed reward | no |
| unclassified | **no** — an unclassified failure is not evidence of anything |

Keep exclusions **visible** in the record. An invisible exclusion is indistinguishable from a
result you did not like.

### A terminal verdict is NOT the bar. Knowing why is.

`STATUS: LIVE`. The table above is only the cheap half — it removes infrastructure. It does not
tell you that the *remaining* failures are real. The actual rule:

> "Every single time you have a failure, **do not treat them as valid failures. Always verify
> the trajectory. See why it failed. If you see the reasoning failure, then you are good.**"

**Read the trajectory of every failing trial and name its cause before the band means anything.**
Not a sample. Every one. A 2/5 where you have read three trajectories and each is a distinct
reasoning failure is a task. A 2/5 where you have read none is a number.

What you are looking for, per failing trial:

| what the trajectory shows | what it means |
|---|---|
| the model understood the contract and got the engineering wrong | **reasoning failure — this is the difficulty you are selling** |
| the model never found the call site / ran out of turns exploring | search failure, not reasoning. Stochastic and thin |
| the model solved it and the grader rejected the shape | **grading defect** — `C2`, and the band is unreadable until fixed |
| the model did something reasonable the contract did not forbid | **contract gap** — `B2`/Avocado. This is R02 arriving early and cheap |
| several arms failed the *same* test | the spec is unclear, not the models (R03) |

The last three are the valuable ones: each is a defect you found **before** the server, at the
stage where fixing it costs one local rerun instead of a cohort and a review cycle. This is the
whole reason the long local loop pays — not that it predicts the band, but that **it surfaces
the contract and grading defects that a human reviewer would otherwise find for you.**

A band you cannot explain trial-by-trial is not evidence you may push on.

## 2. A 0/5 does not establish "too hard"

`STATUS: LIVE`. If **every** valid attempt ended in an agent timeout, that is not design
evidence. Raise the step timeout by 50% and at least 300s, cap 3600s, at most twice per stage,
and rerun the *same* contract. Record it as `semantic_change: false` — the task did not change.

**A timeout-only retirement is invalid lifecycle evidence.** We have two MT tasks sitting at
"no model passed" — `sparql-ruby-query-execution-budget` and `franz-go-kadm-acl-authorization`.
Neither has been classified. Until they are, we do not know they are too hard.

Non-timeout 0/5 needs a trajectory read and an ownership call before any redesign.

## 3. Forecast before you spend a campaign

Before every countable campaign, **write down a predicted 1–3/5 and the evidence for it.**

| situation | evidence required |
|---|---|
| prior campaign exists | replay all five preserved candidate trees, or an exact counterfactual (`C6`) |
| first campaign, no priors | repo complexity + an analogous accepted task + a static solver-path audit. Label it `initial_static`, low confidence, valid for one campaign only |

> "Prediction evidence guides whether to launch; it never counts as calibration."

And the rule that would have saved us a retraction: **a redesign needs at least five usable
prior trajectories. Do not extrapolate from the sole failure or the sole pass.** We committed a
peer's n=1 finding as LIVE and retracted it within the hour on contradicting data; this is the
general form of that mistake.

## 4. Freeze the bundle, or the number means nothing

```bash
~/swebench-playbook/tools/bundle-hash.sh <task>     # every task file except README.md and audit/
```

Record the hash with every campaign result. **Any change to the instruction, tests, solution,
verifier, task metadata, dependency or environment invalidates the campaign** — a hash mismatch
blocks regardless of timestamps or what you remember doing.

This is the gap that lets a green number from tree A get quoted as evidence for tree B. We have
no equivalent today, and we have already graded one task against another task's source.

## 5. The ladder — in order, and cancel forward on failure

1. deterministic base / intermediate / oracle checks (base reward **0**)
2. forced clean-rebuild oracle **3/3** (`-a oracle -k 3 -f`)
3. **step 1, k=5**, with checkpoints
4. one **diagnostic** full-task smoke, once the last step exists — non-counting
5. targeted later-step k=5, seeded from a verified passing step-1 checkpoint
6. full-task k=5
7. `B6` review gate, then `B5` push

**Do not run later stages speculatively. When a stage fails, cancel the queued later stages for
that bundle.** Step 5 is seeded deliberately: it tests inherited-session restoration rather than
re-solving step 1, which is the thing `reference/R10` says makes step-2 numbers unreadable.

**Cancel the campaign at the fourth valid pass.** 1–3/5 is arithmetically impossible from there
— the remaining trials are pure spend. This is free and we have never done it.

## 5b. The long loop is not a throughput cost — it is pipelined

`STATUS: LIVE`. This ladder is slow per task, and that is fine, because **the expensive stages
are background jobs, not agent work.** While task A's k=5 campaign runs, you are authoring task
B and reviewing task C. Wall-clock per task goes up; tasks per day does not go down.

What this does **not** license is relaxing context isolation (`00-ROUTER.md` §6):

- **one task per agent context, still.** A calibration campaign running in the background is not
  an agent context. Working task B while task A calibrates is pipelining; handing one agent both
  tasks is context bleed, and we already have a finding on it.
- **submission stays serial** where the tasks share a repo or subsystem — the reason is peer
  collision, not throughput.

The practical shape at 3/day: roughly three tasks in flight at different stages at any moment,
each in its own context, with the ladder's background stages overlapping. The binding constraint
is not your attention, it is the one-Avocado / two-Docker lane limit — run more concurrent
campaigns than that and they contend, fail on infrastructure, and land in the exclusion column
of §1 having taught you nothing.

## 6. What a result licenses

| band (valid terminal) | read |
|---|---|
| 0/5, all timeouts | **not** difficulty evidence — §2, escalate and rerun |
| 0/5, real failures | trajectory read; may be genuinely too hard, may be a contract gap |
| 1–3/5 | in band. **Accept it — do not chase 1–2/5.** |
| 4–5/5 | too easy. Cancel at 4. Requires a repair *and* five-trajectory replay before relaunch |

Never call a task "passing locally" on the strength of oracle 3/3 alone. **A base failure and a
clean oracle establish grader and golden correctness; they say nothing about model difficulty.**

## When calibration cannot run at all — execute variants instead

`STATUS: LIVE`, 2026-09-30. On `gzhttp`, `B7` produced **zero valid terminal attempts** across
ten trials: the AI-gateway sidecar was not routable from task containers, every trial died
`FailedToOpenSocket`, and `--allow-bridge-networks` failed identically. No band, no forecast
confirmation, nothing to classify.

**A reviewer then measured discrimination directly, and got a better answer than a band would
have given.** It cloned the repo at `base_commit`, applied the `test_patch`, and ran the graded
package under **13 distinct partial implementations**:

```
BASE                      8/8 FAIL        ORACLE  8/8 PASS
10 of 13 partial variants 8/8 PASS        <- the finding
1 variant                 split 6/2       <- and only by magic-prefix arithmetic
```

Ten competent-looking partial implementations clear the entire graded set in one step. The
8 `f2p` collapse to **two equivalence classes separated by one numeric threshold**.

**This is strictly better evidence than a 5-trial band**, and not only as a fallback:

- it is **deterministic** — no sampling noise, no infrastructure to classify
- it measures **discrimination**, which is what the band is a proxy for
- each variant **names the behaviour it omits**, so a non-separating variant tells you *which*
  branch is decorative

**Do this whenever the band is unavailable, and consider it even when it is not.** Write 8–12
implementations that are each correct-but-incomplete in a *different, nameable* way, run the
graded set against each, and read the partition. If most pass, the set does not discriminate,
and no number of trials will change that. → `feedback_swebench_prove_gradient_locally`.

Two things it surfaces that a band never does: a graded entry that **never diverges from
another** in any variant is redundant (`F6` was `F1` with assertions that cannot fail
independently), and a behavioural change in the oracle with **no `f2p` coverage at all** shows
up as a variant that omits it and still scores 8/8.

## CHECKLIST

```
[ ] 1. Every trial classified from terminal verifier evidence before counting
       proof: the per-trial table with exclusions VISIBLE
[ ] 2. Denominator is five VALID TERMINAL attempts, infra replaced not counted
       proof: the count, and what was excluded and why
[ ] 3. A written 1-3/5 forecast with its evidence, made BEFORE the campaign
       proof: the forecast, dated ahead of the run
[ ] 4. Bundle hash recorded with every result
       proof: `tools/bundle-hash.sh <task>` output alongside each band
[ ] 5. Ladder run in order; later stages cancelled on an earlier failure
       proof: the stage log
[ ] 6. Campaign cancelled at the 4th valid pass if it got there
       proof: the cancellation, or "never reached 4"
[ ] 7. Any 0/5 classified for timeout-only BEFORE calling it too hard
       proof: the failure-mode breakdown
[ ] 8. Paired (local valid-terminal band, server band) recorded for the A3 §399 test
       proof: the ledger line
```

## HANDOFF

```
EXIT:       <per-step local band over valid terminal attempts, with the bundle hash>
CHECKLIST:  <8 lines above with proofs>
ARTIFACTS:  the forecast, the per-trial classification table, the bundle hash
FACTS:      <excluded trials and why; timeout escalations applied>
RUNG:       <L0-L3>
UNVERIFIED: <every step whose band rests on fewer than 5 valid terminal attempts>
OPEN:       <steps out of band and the act that owns the remedy>
NEXT:       B6 review gate -> B5 push
```

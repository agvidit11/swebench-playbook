# C7 — Answer a human reviewer and re-submit

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

> **PRECHECK (Vidit 2026-10-13, PROVISIONAL):** before ANY push, first push or revision, run `python3 ~/swebench/revision-gate/gate.py <task>` (full run) and fix every FAIL. `push-task.sh` refuses to push without its stamp. Until 3 agents sign off in `ledger/VERIFY-revision-gate.md`, a FAIL means "look at this", not proof, and `GATE_OVERRIDE="<reason>"` is allowed and logged. **Documentation-only exception (2026-10-17):** if the task diff from the exact green server commit touches only `README.md` and `audit/**`, run `gate.py <task> --documentation-only` instead (re-verifies server results, reviews, the closed review ledger and presubmit; no Docker/oracle/calibration) and push with `PUSH_MODE=documentation-only`. Any other changed path refuses the exception.

```
ACT:    C7-revision-response
OWNER:  Claude routes and re-validates · Muse via mc2.sh ("Avocado/MetaCode" below) for every contract sentence
        · Codex for tests/* and for the independent re-read · never Claude in tests/
INPUT:  a task at `needs_revision` (or any human review with scored rubrics), plus a
        C1 diagnosis of that review
OUTPUT: every reviewer ask dispositioned with evidence, re-validated, re-pushed
EXIT:   zero OPEN reviewer asks in the ledger, C6 verdict on every changed graded
        artifact, B5 pre-submission checklist clean, new SHA pushed
```

`STATUS: LIVE`, 2026-09-29. Written off the first external human review we received.

## Why this act exists separately from `C1`

A machine verdict tells you a **band** and leaves the cause to you. A human review tells you the
**cause** and leaves the band alone. They fail differently, so they are worked differently:

| | machine verdict | human review |
|---|---|---|
| what you are given | a number per model | named, specific asks |
| the usual mistake | mis-diagnosing the cause | **over-correcting** — rebuilding around a small ask |
| who owns the remedy | mostly Codex (`tests/*`) | **mostly Avocado** (`instruction.md` prose) |
| cost of getting it wrong | one more cohort | a re-review, and the reviewer's scores reset |

**The scores are the signal you protect.** A review reading `Realistic 4 · Domain Expertise 4 ·
Original 4` with `Request changes` is a *good task with two small holes*. Those fours were earned
by the sourcing and the contract. A rebuild throws them away and re-rolls them. → `R9` pivot test:
if more than half the asks would be answered by "we changed that area anyway", you are rebuilding,
and you should say so rather than do it quietly.

## 0. Before touching anything: one owner, a clean base, a claim

`STATUS: LIVE`, 2026-10-13. Three things go wrong before the first edit:

```bash
T=<task>
# (a) is anyone else already on it? Any hit = STOP and ask Vidit. One agent per task.
ps aux | grep -i "$T\|${T%%-*}" | grep -v grep
ls ~/scratch/lane-pb/workers/ | grep -i "${T%%-*}"; ls ~/scratch/lane-pb/ADOPT-* 2>/dev/null
git -C ~/swebench-playbook fetch -q && git -C ~/swebench-playbook show origin/master:ledger/CLAIMS.md | grep -i "$T"
# (b) work from REMOTE main in your own worktree, never the shared checkout (it lags and other
#     agents stage into its index). Reconcile the server commitSha with the remote head.
git -C ~/swe-bench-pro-agvidit fetch -q ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git main
git -C ~/swe-bench-pro-agvidit worktree add /tmp/rev-$T FETCH_HEAD
codimango task show $T --json | jq -r .commitSha     # must equal the remote head for $T, or say why
# (c) claim the row (from a playbook worktree; never --autostash the shared clone)
```

- **Read the CURRENT playbook, not the shared clone.** `~/swebench-playbook` often lags
  `origin/master` and cannot fast-forward, because other sessions leave uncommitted `CLAIMS.md`
  edits there. Check `git -C ~/swebench-playbook rev-list --count HEAD..origin/master` after a
  fetch. If it is non-zero, read every act-file from a fresh `git worktree add /tmp/pb-<you>
  origin/master`. Never `pull --autostash` the shared clone. Also read the clone's *uncommitted*
  `CLAIMS.md` diff (`git diff origin/master -- ledger/CLAIMS.md`): an unpushed claim on your task
  is still a claim, and you ask Vidit before taking it. Re-fetch the task repo before declaring
  ready; if the task moved upstream, rebase and re-run the gates.
- **One local `bench run` per host.** Check `ps aux | grep -i codimango-bench` and take
  `flock /tmp/swebench-docker.lock` for every Docker or bench call. A second concurrent bench kills
  both with gateway 400s.
- **`needs_revision` with a FAILED validation is two jobs, not one.** Answer the reviewer (§1–§3)
  *and* fix the harness: route the failing gate through `C1` → `C2`/`C3`/`C4` (skill:
  `runbooks/3-harness.md`) in the same revision. A reply that answers every ask but ships a red
  gate is not resubmittable.

## 1. Pull EVERY review, every version, and treat every ask as a ledger finding

```bash
codimango task reviews <task> --full > $D/human-reviews.txt   # SINGULAR 'task'
```

Everything else in the pull set is `R9` — run it whole, including trials and trajectories. The
human review is **not** a substitute for the machine artifacts; the reviewer read the same
artifacts you can, and their prose is a summary of what is in them.

**"All reviews" means all sources and all commits**, not the latest human comment:

| source | command | what to extract |
|---|---|---|
| every human review, every round | `task reviews --full` | each decision + every requested change, every reviewer |
| contamination / QRA / TBR bot entries | same file | risk level, any non-pass |
| agentic full-task review per pushed SHA | `job review <task> --commit <sha>` for **each** SHA in `job list` | verdict + each finding |
| AI assessment counts | `task show --json` | non-zero Low/Medium counts → go find them (`C1` ①) |
| the validation record | `task errors --json` | every failing or warn row |
| the existing ledger | `<task>/audit/REVIEW-LEDGER.md` | every prior `OPEN`/`ESCALATED`/`DEFERRED` |

**Proof of completeness:** write `$D/REVIEW-INVENTORY.md`: one line per review entry pulled
(source · date · SHA · reviewer · decision), and next to each, the ledger row IDs it produced. An
entry that produced zero rows says why ("bot pass, no asks"). The count of entries in the inventory
must equal the count in `human-reviews.txt` + one per reviewed SHA. This is what lets you say "every
review is addressed" and back it up.

Then, in the ledger, **one row per ask, in the reviewer's own words.** Not your paraphrase — the
paraphrase is where an ask quietly narrows. A reviewer's sentence is the acceptance criterion you
will be re-read against.

| the review says | the ledger row says |
|---|---|
| "this test checks something your instruction only hints at" | `F<n>-01 | R02 | test X grades a rule the contract never states | human-reviews.txt | OPEN` |
| "there are no claude-code trials at this commit" | `F<n>-02 | — | gate passed with one solving model; opus arm unstarted | task-errors.json | OPEN` |

## 2. Route each ask to its owner BEFORE proposing any change

This is the step that decides whether the revision is legal. Ownership is by path
(`00-ROUTER.md` §5, `R4`), and the iron-clad rule does not bend for a reviewer's request:

| the ask needs | owner | act |
|---|---|---|
| a contract sentence added, clarified or scoped | **Avocado / MetaCode / human, only** | `B2` |
| an assertion removed or added | Codex | `C2` |
| a missing model arm run | Claude (it is a rerun, not an edit) | `B5` §"one model short" |
| a flaky or timing-dependent entry | Codex | `C2` + `B5` p2p flake screen |
| sourcing, novelty, or realism | **human** — record `ESCALATED`, do not argue it in files | — |

**A reviewer asking for a sentence does not make it yours to write.** "The reviewer told me to"
is not an exception to D2 — the rule is temporal, not spatial: no Claude or Codex text ever
enters `instruction.md`, at any point, for any reason. Brief Avocado with the *requirement*, never
the prose (`feedback_metacode_brief_no_prose`). If you write the sentence and ask 1P to reword it,
that is laundered authorship and it fails provenance.

**The two-remedy trap.** Most `R02` asks ("the test grades something unstated") have two legal
fixes: state it in the contract, or drop the assertion. They are not equivalent — dropping an
assertion removes a branch and can collapse the band, and adding a sentence can make the task
easier. Decide with `B3` §④ branch count in hand, not by which is cheaper to execute.

## 3. Re-read every file — with an agent that did not write it

`STATUS: LIVE`. After the last change lands and before any validation, hand the **whole task tree**
to Codex for an independent read. Not the diff — the tree. The agent that wrote a file is the worst
reader of it, and by this point Claude has read its own diff at least twice.

Brief it with the reviewer's asks and nothing else about your fixes:

> Read every file under `<task>/`. For each reviewer ask below, decide independently whether the
> current tree answers it, and cite the line that does. Then run `B3` §①b: for every
> graded assertion, quote the contract sentence that requires it, or flag it. Do not propose
> fixes. Report per-file.

Two things this catches that nothing upstream does: an ask answered in the commit message but not
in the tree, and a fix that answered ask A by breaking the file that answered ask B.

## 4. Re-validate — full, not incremental

**A revision is a push, so it takes the whole `B5` pre-submission checklist.** There is no short
form. The temptation is strong here, because you changed two lines and the last push was green;
that is exactly the state in which a regression is invisible.

Specifically non-skippable on a revision:

- **`C6` on every changed graded artifact.** A change to `tests/*`, the golden, or the contract is
  unverified until it is replayed against real prior trajectories. This is the only check that
  speaks to *"will the band still hold"* — see §5.
- **the p2p flake screen**, if any test file moved at all
- **oracle 3/3 per step**, not the mean
- **GATE ZERO** — every ask from this review AND every finding from every prior version

## 5. What actually protects the band — and what does not

Be honest about this, including to Vidit: **nothing guarantees calibration holds.** The band is a
sample of stochastic runs; the server's avocado is not reproducible locally (`A3` GATE 4, the cold
probe reproduces opus). What you can do is make a regression *detectable before the push* rather
than after:

| the change | what it does to the band | the check that sees it first |
|---|---|---|
| an assertion **removed** | can collapse to `too easy` — one fewer branch | `B3` §④ branch count, recounted |
| an assertion **added** | usually nothing; occasionally `too hard` | `C6` replay: did a passing arm now fail? |
| a contract sentence **added** | the big one — states a rule models were failing on | `C6` replay against the arms that failed it |
| a sentence **clarified only** | typically inert | none needed; record it |

The rule: **a change that answers an `R02` ask by stating a requirement is a difficulty change, not
a wording change.** It hands the model the thing it was losing on. Replay it before you push, and
if you cannot replay it, say `UNPROVEN` in the handoff rather than implying the band is safe
(`C6` §5).

And per the quality ladder (`00-ROUTER.md` §3b): **the floor is L1, and the band is not part of
it.** A revision that answers every ask, passes every gate, and lands out-of-band is a *successful*
revision. Do not trade an answered finding for a band guess.

## 5b. Prove nothing else broke — baseline before, diff after

`STATUS: LIVE`, 2026-10-13. "Answers the review" and "breaks nothing" are separate claims and need
separate proof. A revision has broken an already-green gate before (`00-ROUTER.md` §4: WEAK → WRONG).

1. **Before the first change**, snapshot every surface at the current server SHA into
   `$D/baseline.md`: every `validationDetails` row by label, per-step avocado/opus/gpt bands,
   agentic verdict, `tbdReviewStatus`, provenance `agentModified`, plus local `gate.py --fast`
   stage results (preflight, presubmit, provenance, carry, forge).
2. **After the last change**, run the full `gate.py <task>` (all 7 stages, issues the stamp) and
   write `$D/after.md` with the same rows.
3. **Diff them.** Any green → red is a blocker. Any stage that was not run says `NOT RUN` with a
   reason, never blank. Calibration that cannot be measured locally (gateway, slot) is `UNPROVEN`
   and stays visible in the handoff and in the reviewer message's risk line.

**No new issues** is shown by three readers that did not write the change, all clean on the
final tree: the `gate.py` stage-6 reviewer agent (`review-task-swebench-v2`) with zero new
findings, the §3 Codex whole-tree re-read, and `authorship-audit.sh <task>` exit 0 plus
`prov_predict.py` 0 surviving blocks. A finding any of them raises is either fixed or becomes a
ledger row with a disposition. It is never dropped silently.

## 5c. RESUBMIT-READY — the proof bundle, then the reviewer message

A task is **ready to resubmit** only when `$D/RESUBMIT-PROOF.md` exists and every line is green
or explicitly dispositioned. It lives in the evidence dir, **outside** the task tree (Claude may
write it there). The task's own `audit/REVIEW-LEDGER.md` is written by Codex.

```
RESUBMIT-PROOF <task>  base <old sha> -> <new sha>
1 ALL REVIEWS PULLED   REVIEW-INVENTORY.md: <n> entries, <n> mapped, 0 unmapped
2 ALL ASKS ANSWERED    ledger: <n> rows · FIXED <a> · ESCALATED <b> · OPEN 0   (grep cmd + output)
3 EACH FIX HAS A CHECK per row: commit + the test/probe/gate that now fails on the old behaviour
3b FINAL-COMMIT RECHECK each reviewer 'Fixed when:' condition re-verified against the FINAL pushed SHA (not an earlier one),
                 incl. README per-step rates citing that exact SHA (presubmit does not check this)
4 NOTHING ELSE BROKE   baseline vs after diff: 0 green->red   (paste the diff)
5 NO NEW ISSUES        reviewer agent: <verdict, n new> · Codex re-read: <n flags> · authorship 0 · prov 0
6 GATE                 gate.py full: PASS, stamp <hash>  (or GATE_OVERRIDE "<reason>", logged)
6b FAILURES LEGIT      presubmit `failure legitimacy`: every failed trial is FAIL_REASONING in the agentic review's attemptResults,
                 and any trial the review did not classify is read by hand (verifier/test-stdout.txt or jest/ctrf results)
7 HARNESS              oracle 3/3 per step · per-step band <local/replay> · C6 PROVEN|UNPROVEN per change
8 SERVER               after push: validationStatus, every row, balance string with every arm (B5)
```

Line 8 can only be filled after the push. Note that "validationStatus=passing" alone is not enough: run presubmit WITHOUT
`--local-only`, because it catches hard-blocking engine stages (e.g. Eval GT `gt_resolved=0`) that the status hides. Until it is filled the task is **pushed, not ready**.
Nobody presses resubmit or replies to the reviewer before line 8 is green.

**Then draft the reviewer message, for Vidit to send.** Claude never posts it. Replying to a
reviewer is outward-facing, so Vidit sends it. Write it in Vidit's voice: first person,
plain, short, no headings, no bold, no marketing words. One line per ask, in the reviewer's order,
saying what changed and where to look. One honest line on anything escalated or unproven. Nothing
the proof bundle cannot back up.

```
Hi <reviewer>, thanks for the review. Pushed <short sha>.
- <ask 1 in their words, shortened>: <what changed, one clause>. <file/test name>.
- <ask 2>: ...
- <anything not changed>: <why, one clause>.
Re-ran oracle, the full gate and validation on the new commit, all green. <one risk line if any>
```

Keep it under ~120 words unless the review had more than six asks.

**No reviewer message before §5d says READY.** Not a draft "for when it passes", not a
placeholder. Vidit, 2026-10-21: a jedi reply was handed over twice off green gates alone, and both
times the task still had a stale README, unclassified failures and a half-answered review ask.

## 5d. INDEPENDENT PRESUBMIT — a fresh agent runs the whole checklist

`STATUS: LIVE`, Vidit 2026-10-21. Mandatory before every first submit AND every resubmit.

**Who runs it.** A *separate* agent that did not build or revise the task: a fresh `codex exec`
or a fresh Claude subagent with no conversation history. Never the session that wrote the fix. The
author has already convinced itself the fix is right; that belief transfers through a summary, so
**the brief carries only the task name, the pushed SHA, the evidence-dir path and this section.** No
rationale, no "we already checked X", no prior verdicts, no reviewer-reply draft.

**What it does, in order — each line reported with its proof:**

```
INDEPENDENT-PRESUBMIT <task> @ <sha>   agent: <codex|claude-subagent>   playbook: <sha after pull>
0 RUNBOOK     git pull ~/swebench-playbook (and sync-skill.sh install); re-read the swebench-mt
              RUNBOOK, B5, B6 and this file AT THAT SHA before anything else
1 SERVER      task show/errors on <sha>: validationStatus passing, every row green, balance string
              with every arm; presubmit.py WITHOUT --local-only: 0 FAIL, every WARN dispositioned
2 README      tools/readme-server-check.py <repo> <task> exit 0, plus a read: the four headings; no
              internal links or paths; Completion Rates cite THIS sha with the per-step, per-model
              numbers from the balance string; no "TBD", "pending", "not reached", "will be
              refreshed" left over
3 FAILURES    tools/failure-audit.py <task> --repo <checkout> --judge exit 0, and every failed trial on <sha> read (agentic attemptResults, else ctrf / test-stdout):
              each is a genuine reasoning miss, or named as infra (AgentTimeoutError,
              ApiServerShuttingDown, 0 tests, grader) with its fix or written justification;
              0 unexplained
4 REVIEW      review-task-swebench-v2 (multi-turn: review-task-swebench-multiturn) run on the
              final tree by this agent: verdict Accept; every Medium+ finding fixed, not argued
5 COVERAGE    requirement <-> test matrix per step, BOTH directions: every requirement in each
              step's instruction maps to >=1 graded test (0 UNTESTED / COVERED-BUT-UNASSERTED,
              lh-coverage --auto matrix or equivalent), and every graded test maps to a stated
              or repo-derivable requirement (0 unstated-but-graded); carried tests re-run in
              later steps
6 PROOF       C7 RESUBMIT-PROOF lines 1-8 (or B5 block on a first submit) all green
VERDICT       READY | NOT READY: <the failing lines>
```

It writes the report to `$D/INDEPENDENT-PRESUBMIT.md`, outside the task tree, and edits nothing.
NOT READY goes back to the author, gets fixed (Codex / Muse per the authorship table), is pushed,
and §5d is re-run by a **new** fresh agent. Only on READY does the author draft the §5c reviewer
message.

## 6. CHECKLIST — the reviewer-feedback check

```
[ ] 1. `task reviews --full` pulled; full R9 pull set alongside it, trials included
       proof: the evidence dir listing
[ ] 2. One ledger row per ask, IN THE REVIEWER'S WORDS, not paraphrased
       proof: the ledger rows next to the quoted review
[ ] 3. Each ask routed to a named owner before any file changed (§2)
       proof: the routing table, filled in
[ ] 4. Every contract-prose ask went to Avocado as a REQUIREMENT, never as prose
       proof: the brief you sent; zero Claude/Codex bytes in instruction.md
[ ] 5. Any ask only a human can answer is ESCALATED, with owner and reason (R9)
       proof: the ledger rows
[ ] 6. Independent Codex re-read of the WHOLE tree, per-file, after the last change (§3)
       proof: the per-file report and its citations
[ ] 7. C6 verdict on every changed graded artifact — PROVEN or explicitly UNPROVEN
       proof: the C6 report per artifact
[ ] 8. Branch count recounted if any assertion was removed (B3 §4)
       proof: the count, before and after
[ ] 9. FULL B5 pre-submission checklist, no short form
       proof: the B5 block
[ ] 10. Every missing model arm from the prior gate triggered and read (B5)
       proof: the new balance string
[ ] 0.  No other agent on the task; own worktree off remote main; claim row pushed (§0)
       proof: the ps/workers/CLAIMS output, the worktree path, the claim commit
[ ] 11. EVERY review from EVERY source and SHA inventoried and mapped to rows (§1)
       proof: REVIEW-INVENTORY.md, 0 unmapped
[ ] 12. Failing harness gate (if any) repaired in the same revision via C1→C2/C3/C4 (§0)
       proof: the C1 plan + the gate now green, or UNPROVEN with reason
[ ] 13. Baseline vs after diff: 0 green->red (§5b)
       proof: baseline.md, after.md, the diff
[ ] 14. RESUBMIT-PROOF.md complete; lines 1-7 green before push, line 8 after (§5c)
       proof: the file
[ ] 16. Independent presubmit by a FRESH agent on the pushed SHA: VERDICT READY (§5d)
       proof: $D/INDEPENDENT-PRESUBMIT.md, lines 0-6 with proof
[ ] 15. Reviewer message drafted in Vidit's voice and handed to Vidit, NOT sent (§5c) —
       only after line 16 is READY
       proof: the draft in the final report
```

## HANDOFF

```
EXIT:       <asks answered N/N · new SHA · re-review requested y/n>
CHECKLIST:  <10 lines above, each with its proof>
ARTIFACTS:  audit/REVIEW-LEDGER.md (new version section), the C6 reports,
            the Codex per-file re-read, the Avocado brief(s)
FACTS:      <rubric scores before · which asks were contract vs test vs rerun>
RUNG:       <L0-L3 after the revision>
UNVERIFIED: <every change with no C6 replay behind it, named>
OPEN:       <ESCALATED rows, and anything the reviewer may still contest>
PROOF:      $D/RESUBMIT-PROOF.md (lines 1-8) · $D/REVIEW-INVENTORY.md
REPLY:      <the reviewer message draft, verbatim, for Vidit to send>
NEXT:       S8 — wait on the new SHA (00-ROUTER.md §3); resubmit only once PROOF line 8 is green
```

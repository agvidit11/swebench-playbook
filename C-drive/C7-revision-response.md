# C7 — Answer a human reviewer and re-submit

```
ACT:    C7-revision-response
OWNER:  Claude routes and re-validates · Avocado/MetaCode for every contract sentence
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

## 1. Pull, and treat every ask as a ledger finding

```bash
codimango task reviews <task> --full > $D/human-reviews.txt   # SINGULAR 'task'
```

Everything else in the pull set is `R9` — run it whole, including trials and trajectories. The
human review is **not** a substitute for the machine artifacts; the reviewer read the same
artifacts you can, and their prose is a summary of what is in them.

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
NEXT:       S8 — wait on the new SHA (00-ROUTER.md §3)
```

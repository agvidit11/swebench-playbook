# friction.md — pair-oxigraph

One entry per place the playbook was unclear, missing, wrong, self-contradictory, or slower
than it should have been. File + line where possible. Appended as I go.

---

## F1 — `B2-contract.md` is missing two rules the source pipeline had

**File:** `B-build/B2-contract.md` (whole file)
**Status:** flagged by the common brief (`/tmp/pipeline-compare/PAIR-COMMON.md:55-59`) and
confirmed by me on read.
Missing rules: **"step 2's spec must be self-contained"** and **"no 'deferred to step 2'
language in step 1"**. I will apply both when I brief Avocado, but they are not in the file,
so a pair that only read the file would not apply them.
**Time cost:** none for me (pre-warned); would be one repair round for anyone not pre-warned.

---

## F2 — `instruction-lint.py` shipped stale relative to policy D1, and `B2`'s exit condition depended on it

**File:** `~/.claude/skills/swebench-mt/instruction-lint.py` (the tool), referenced as
`B-build/B2-contract.md`'s exit condition ("instruction-lint clean").
**Reported to me mid-run by the coordinator; fixed in place before I reached B2.**

The old version enforced an absolute never-name rule and hard-FAILed on *any* symbol absent
at `base_commit`. D1 (stated at `A-source/A3-idea-gate.md` GATE 0 and
`B-build/B2-contract.md`) requires the opposite for one of the two lawful configurations: a
new name that the graded tests **pin** MUST be named in the contract. So the old tool made
`B2`'s exit condition **unreachable** for any task whose grader pins a new symbol — i.e. for
every `expose_interface`-shaped or net-new-capability task.

This is a playbook-level defect, not a user error: an act-file's exit condition was bound to
a tool that contradicted the policy stated two files earlier. The two copies drifted, which
is exactly the failure `00-ROUTER.md` §9 says the file index exists to prevent
(*"No rule appears in two files"*) — the rule lived in `A3`/`B2` prose **and** in tool code,
and the tool copy was the stale one.

Fixed version is three-way and reads each step's `test_patch` from `tests/config.json`:
- absent at base + pinned by graded tests + named in contract -> OK
- absent at base + NOT pinned by tests + named in contract -> FAIL (gratuitous leak)
- absent at base + pinned by graded tests + contract SILENT -> FAIL (the illegal
  configuration; `BAD_GRADING_WRONG` on 4 of 4 peer tasks)

Second-order friction worth recording: before `B3` exists there is no `test_patch`, so at
`B2` time the tool can only run the leak half and prints WARN. **`B2`'s exit condition is
therefore only half-checkable at `B2`.** The act-file does not say to re-run it after `B3`;
I was told out of band. That instruction belongs in `B2` (or in `B3`'s checklist) in writing.

**Time cost:** zero for me, because I was told before reaching B2. Would have been one full
blocked act for a pair that hit it cold.

---

## F3 — `A2` §2's card target is unreachable-by-construction on most repos, and the act-file half-admits it

**File:** `A-source/A2-idea-generate.md:7` vs `:60`
Line 7 sets `Output | candidate cards — dispatch target **>=8**`. Line 60 then says the >=8
target "is reachable only on a 60k+ LOC repo with many subsystems", and that 15-20 surfaces
collapsing to **2-4** candidates "is the point, not a loss". oxigraph is 97k LOC across 13
crates — nominally in the ">=8 is reachable" band — yet the same paragraph's own collapse
ratio predicts 2-4. Both cannot be true. The header number is the one an agent copies into
its plan; the correction is 53 lines later. Recommend deleting the `>=8` from the header row
and putting the derivation there instead.
**Time cost:** ~10 min reconciling before I could write step 4 of the checklist honestly.

---

## F4 — `A2` §3's tooling note does not say whether MetaCode can read a path outside `--dir`

**File:** `A-source/A2-idea-generate.md:105-122`
`WASTE:` The section warns that a 46 KB inline prompt "returned only its opening plan" and says
to keep the payload in a file — but only for `codex exec`, which takes an explicit
`--add-dir`. For `mc.sh` it gives no equivalent. My card-generation brief needed the 33 KB
survey output as payload, which would have made a 48 KB prompt. I had to spend a **separate
~90 s probe dispatch** to establish that MetaCode *can* read an absolute `/tmp` path outside
its `--dir`. One sentence in A2 §3 ("mc.sh's model can read absolute paths outside `--dir`;
pass large payloads by path") removes that probe for everyone.
**Time cost:** ~3 min (probe + re-assembling the brief). Small, but it is pure repetition —
every pair on a large-payload dispatch pays it.

---

## F5 — `A2` §7 demands a 13-item self-audit whose item list is nowhere in `A2`

**File:** `A-source/A2-idea-generate.md:245-247`
`PINPOINT:` §7 says *"Thirteen Agentic Full-Task Review items are judgeable from a card: R01 R02
R04 R05 R06 R07 R08 R09 R11 N01 N02 N03 N04"* — the identifiers, but not what any of them
means. `A2` names no reference for them. The definitions live in `B5-preflight-push.md:88-107`,
an act three files downstream that an A2 runner has no reason to open, and the *rules* behind
them live in `B3 §1`. To put a usable self-audit into the MetaCode brief I had to read `B5`
during `A2`. Either `A2` §7 should link `B5` §2 explicitly, or the 17-axis table should move to
a reference file both can point at. This is exactly the "no rule appears in two files, link
instead" principle in `00-ROUTER.md` §9 being violated by *omission* — there is no link at all.
**Time cost:** ~5 min and one extra file read.

---

## F6 — the `A2` -> `A3` boundary makes you pay for verification twice

**File:** `A-source/A2-idea-generate.md:130` (HEAD citation field) vs
`A-source/A3-idea-gate.md:71-81` (GATE 2 hollow premise)
`REPEAT:` A2 requires every card to carry a HEAD `file:line` citation and a verbatim
nearest-presence quote — i.e. the card author must read the code. A3 GATE 2 then says *"Verify
the card's nearest-presence quote yourself"* and *"Grep is not reproduction. Execute at
`base_commit`."* That second half is right and must stay. But the *first* half — re-reading the
same function to confirm the citation — is a straight repeat, and for a survey that returned 18
surfaces it is 18 repeats. The cheap fix is for A2 to require the citation as a **pasted code
excerpt** rather than a line number, so A3's verification step degrades to "does the excerpt
match the file today" (one `grep -F`) instead of "go read it again".
**Time cost, this run:** I re-read `explain`, `QueryExplanation`, `EvalNodeWithStats`,
`eval_node_label`, `can_be_silent` and `oxrdf::Dataset` during A2 *and* they are all A3 GATE-2
inputs. ~25 min of reading that is about to be re-justified under a different act's checklist.

---

## F7 — `A2` never tells you to check upstream commit recency, and it is a free kill

**File:** `A-source/A2-idea-generate.md` §3 (the survey ask) and §6 (auto-rejects)
`EARLIER:` A2 §3.2 rightly makes in-code admissions (`TODO`, `not supported`) the strongest
premise receipt. What it does not say is that **an admission next to a hot file is worth less
than an admission next to a cold one**. One command at survey time —
`git log --oneline -15 -- <target file>` — told me that three of my 18 surfaces (S07 SILENT
taxonomy, S08 EXISTS-in-expression-evaluator, S09 filter pushdown) sit on lines that upstream
changed in the last few dozen commits: `bb2fb65b SPARQL: EXISTS: fixes error propagation`,
`460f8c5b SPARQL: properly propagate storage error during expression evaluation`,
`b5db4d18 SPARQL: fixes wrong filter propagation through projection`. Those are A3 GATE-3
disclosure hits and GATE-2 hollow-premise risks, and I found them by accident while verifying
something else. A3 GATE 3 does list `git log --oneline --all -- <target-files>` — but at GATE 3,
which is *after* the survey has already spent its budget describing those surfaces in full.
**Where the check belongs:** in the A2 survey ask itself, as a per-surface field
(`upstream churn: <n commits touching these lines in the last 100>`). It costs one command per
surface and it would have down-ranked three of eighteen before a single card was written.

---

## F8 — `A1`'s output format is not specified, so `A2` step 1 ("Read HANDOFF A1") is unverifiable

**File:** `A-source/A2-idea-generate.md:272` vs `00-ROUTER.md` §8
`PINPOINT:` A2's checklist line 1 is *"Read `HANDOFF A1` — LOC, subsystem count, HEAD sha and
the named existing entry point copied into your run notes. **Do not re-measure**"*. My input was
a shortlist log, not a HANDOFF block, and it did not carry a HEAD sha at all — I had to run
`git log -1` in the clone to get one, which is technically re-measuring. It also did not state
whether the sha it screened was the sha I should pin as `base_commit`. `00-ROUTER.md` §8 defines
the HANDOFF shape generically but `A1` is the one act whose output another act consumes by name,
and nothing pins its `FACTS` keys. A named minimum key set for `HANDOFF A1`
(`clone_path`, `head_sha`, `loc_nontest`, `subsystems`, `grading_cmd`, `grading_secs`,
`peer_tasks`, `ai_authorship`) would make A2 step 1 mechanically checkable.
**Time cost:** ~2 min, but it is the kind of gap that silently becomes "I re-screened the repo".

---

## F9 — `A3` GATE 3's disclosure query list omits the one search that actually killed my candidate

**File:** `A-source/A3-idea-gate.md:89-96`
`EARLIER:` The GATE-3 command block lists `git log --oneline --all -- <target-files>`,
`gh issue list --search`, `gh issue view --comments`, `gh api repos/.../issues/<n>`,
`gh pr list --search '<keywords>' --state all`, and a test grep. What killed C01 was
`gh pr list --state all --search "SILENT OR MOVE OR COPY update"` returning **PR #1938, MERGED
2026-09-12** — ten days before base_commit, in the same file, implementing the candidate's
step-2 contract. That IS in the list. But the list is ordered issues-first, and the prose around
it is almost entirely about issues (`--comments` is mandatory, `gh issue view` returns empty,
spire #7199's title hides its body). **The hard-kill rule leads with "any merged public PR", yet
the guidance mass is on issues.** On a repo maintained by one prolific author, the merged-PR arm
is the one that fires. Recommend reordering the block to put `gh pr list --state all` first with
the merged-PR rule quoted next to it.
`PINPOINT:` also — a *closed* issue whose fix has already shipped is neither a hard kill (the
rule says "open issue") nor harmless (it is training-data exposure for the direction). I hit two
of those (#1889, #1878) and GATE 3 gives no verdict for that case. It needs one.

---

## F10 — nothing in `A1`-`A3` measures UPSTREAM CHURN, and on this repo churn was the binding constraint

**File:** `A-source/A1-repo-screen.md` (screening criteria) and `A-source/A3-idea-gate.md` GATE 3
`EARLIER:` The A1 screen measured licence, LOC, subsystem count, open issues, remote branches,
agentic files, **AI authorship**, inline issue refs, peer dedup and harness timing. oxigraph
scored best-in-territory on every one of those — 0 peer tasks, 0/1000 AI-authored commits, 47 s
build. It ranked #1. What it does *not* measure is **how fast the maintainer is currently
moving through the subsystems you would target**, and that is what killed both of my candidates:
one on a merged PR from ten days before base_commit, the other on a premise the maintainer had
already implemented.

A repo with 0 peer tasks and 0% AI authorship is *attractive to us for the same reason it is
attractive to its maintainer*: it is unmined because it is well-tended. The two screening
metrics we do have are both about **other task authors**; neither is about the **upstream
author**. Concretely, this repo carries 394 lifetime issues, 24 open PRs, and merged PRs landing
within days of HEAD across every crate.

**Proposed A1 field, one command:**
`git log --since="90 days ago" --oneline -- lib/<subsystem> | wc -l` per candidate subsystem,
plus `gh pr list --state merged --limit 50 --json mergedAt` to get a merge cadence. A repo whose
target subsystem takes a merged PR every few days will kill candidates at GATE 3 faster than it
generates them, and that is worth knowing at screening time rather than after two MetaCode
dispatches and a Docker harness.
**Time cost:** the entire first A2+A3 cycle — roughly 2 hours — produced zero survivors, and a
churn column would have predicted it.

---

## F11 — `A3` GATE 2 says "execute at base_commit" but no act-file tells you how to get an execution harness

**File:** `A-source/A3-idea-gate.md:81`
`PINPOINT:` GATE 2 is emphatic and correct: *"Grep is not reproduction. Execute at
`base_commit`... a task whose `fail_to_pass` passes at base is unsalvageable."* It was the
highest-value gate of my run — it killed C02 outright, something no amount of reading would
have. But **nothing in `A1`, `A2` or `A3` tells you to build an execution harness, and the
Docker/base-image/toolchain material all lives in `B1 §2` and `B4 §2`**, two acts later.

I had to invent the harness at A3: `git archive HEAD | tar -x` into a task-scoped dir (a plain
`cp -r` of the shared clone fails on root-owned `target/debug/incremental/*.lock` files left by
the screening run), a persistent `CARGO_HOME` volume so the second run is 0.9 s instead of
48.6 s, and `flock /tmp/swebench-docker.lock` around the `docker run`. None of that is written
down anywhere, and all of it is reusable by every pair on every repo.

`REPEAT:` the same harness is then needed again at `B3` (baseline diff) and `B4` (oracle). It
should be created once, at A3, and handed forward in the HANDOFF as a named artifact. Recommend
a short `reference/R-harness.md` with the three-line recipe, linked from GATE 2, `B3 §4` and
`B4 §7`.

---

## F12 — `A3` has no cheap structural check for "do the two steps share any code at all"

**File:** `A-source/A3-idea-gate.md:187-193` (GATE 7)
`EARLIER:` GATE 7's two operational tests (HEAD counterfactual, parallel-API) are the right
tests, but they are posed as questions to reason about. C01 died on a version of them that is
**one grep**: its two steps live in different crates, over different error enums
(`QueryEvaluationError` vs `UpdateEvaluationError`), and
`grep -rn "can_be_silent\|QueryEvaluationError" lib/oxigraph/src/sparql/update.rs` returns
nothing — there is no call edge between the halves. The card had nonetheless *argued* that the
counterfactual passes.

**Proposed GATE 7 pre-filter, free, before the two reasoning tests:**
> Name one symbol that step 1 introduces or changes and step 2's *solution* must reference.
> Grep for it in step 2's file set. If the answer is "none", the cascade is decorative and no
> amount of argument fixes it.

That is the mechanical form of *"two tasks in a trench coat"*, and R6 already records that P6
was *"narrated in all 8 candidates and engineered in none"* on casbin — i.e. this exact failure
recurs and is still only checked by argument.

---

## F13 — the `>=8 cards` target and the "never backfill" rule pull in opposite directions under a churn-heavy repo

**File:** `A-source/A2-idea-generate.md:7` and `:60`, with `A-source/A3-idea-gate.md:10`
`WASTE:` Related to F3 but now measured rather than predicted. A2 asks for cards; A3 says *"a
well-evidenced kill is a good outcome — three of four A/B repos returned zero survivors and
those were the correct answers"*. On this repo the honest yield was 2 cards and 0 survivors, and
the *expensive* part was that neither card's author had any way to check freshness — A2's card
template has 16 fields and **not one of them is "has upstream touched this recently"**. So A2
spent a full dispatch writing two beautifully-specified cards that GATE 3 and GATE 2 disposed of
in twenty minutes. Adding a single `Upstream churn` field to A2 §4's card template would move
that check left by a whole act, at a cost of one `git log` per card.

---

## F14 — `A1` G2 makes the *presence* of `AGENTS.md` a hard kill, and this repo has one. It should never have reached me.

**File:** `A-source/A1-repo-screen.md:25` (gate G2), vs
`/home/agvidit/swebench/runs/shortlist-data.md:75`
`EARLIER:` — and it is the earliest-possible check, which is what makes it expensive.

G2's kill threshold, verbatim: *"`claude/*`, `codex/*`, `copilot/*` merged or closed-unmerged
branches; `.claude/`, `CLAUDE.md`, **`AGENTS.md`**, `docs/claude/`; claude-code-action in CI"*.
The shortlist row for oxigraph reads `agentic files | AGENTS.md only — a contribution guide`,
i.e. **the screening log records the kill condition and waives it in the same cell**, in a
parenthetical, with no authority cited. I copied that cell into my run notes and did not
challenge it; my reviewer caught it.

Having read the file: it is 49 lines of human-written contribution guidance — a W3C spec URL per
crate, where to put test files, which fuzz targets to run. No agent fingerprint. G3 independently
measured **0 of 1000** AI-attributed commits. So the *spirit* of G2 is plainly not violated, and
the gate as written is over-broad: since `AGENTS.md` became a cross-vendor convention it no
longer implies agent authorship the way `.claude/` or a `claude/*` branch does.

**But the gate is presence-based and it does not have an exception clause,** so either it means
what it says or it needs rewriting. The failure mode to avoid is the one that actually happened:
an informal waiver buried in a data cell, inherited silently by the next act.
**Fix:** make G2 content-based for `AGENTS.md` specifically (kill on agent-authorship markers
inside it, not on its existence), or keep the literal gate and require any waiver to be a signed
line in the HANDOFF rather than a parenthetical. Either is fine; the status quo is not.
**Time cost:** the entire run — roughly 4 hours — was spent on a repo the playbook kills at its
second gate.

---

## F15 — the remote-branch figure I was handed was wrong by 23 of 26, and the error hid three disclosure hits

**File:** `/home/agvidit/swebench/runs/shortlist-data.md:74` ("remote branches | **27**, all
dependabot. Zero agentic branches")
`EARLIER:` Measured by me at A3 round 2:

```
total remote branches: 26     dependabot: 3     NON-dependabot: 23
```

"Zero agentic branches" is correct and was the point of the G2 sub-check. "All dependabot" is
false 23 ways, and those 23 are the maintainer's in-flight feature branches. Three land on
surfaces that reached carding: **`origin/sparql-exist`** (surface S08),
**`origin/custom-aggregations`** (S02, S10), and `lateral`/`lateral-opt`/`path-opt` (adjacent to
S04, S09). Under `R6`'s published-roadmap rule and A3 GATE 3's feature arm, an in-flight public
branch is disclosure of direction.

Two separate defects here and they should be fixed separately:
1. **A1 recorded a branch count for the wrong purpose.** It asked "are any branches agentic?" and
   reported the answer as if it also characterised what the branches *are*. A downstream act
   reading "all dependabot" reasonably concludes there is no in-flight feature work to collide
   with. **Fix:** split the field into `agentic branches: N` and `non-dependabot branches: N`.
2. **No act asks for a branch sweep at surface level.** A3 GATE 3 has
   `git branch -r | grep -iE "feat|feature"` but only under the feature-side arm, and these
   branch names (`sparql-exist`, `custom-aggregations`, `lateral`) match neither pattern. **Fix:**
   sweep branch names against the *surface's own symbols*, not against the word "feature".

---

## F16 — my own worst error: I answered a dependency question by grepping one file

**Where:** `handoffs/02-A3.md` GATE 7, withdrawn in the correction block appended to that file.
`PINPOINT:` I claimed C01's cascade was decorative because

```
$ grep -rn "can_be_silent\|QueryEvaluationError" lib/oxigraph/src/sparql/update.rs
(no output)
```

The answer was in the sibling module: `lib/oxigraph/src/sparql/error.rs:4` does
`use spareval::QueryEvaluationError;` and `:56` implements
`From<QueryEvaluationError> for UpdateEvaluationError`, mapping `UnboundService`,
`UnsupportedService`, `InvalidServiceName`, `Service` and `Dataset` across the crate boundary.
The reviewer also pointed out the sharper version: the card's step-2 graded set is two
*query-side* SERVICE guard probes, so the HEAD counterfactual fails by construction, and I could
have read that off the card without any grep at all.

This is a playbook gap as much as an executor error, and the reviewer named the fix
independently: **GATE 7 asks conceptual questions where a mechanical one is available.** A
dependency claim should be answered by tracing a symbol through the module that *owns the type*,
not by grepping the file the step would edit. Concretely, the pre-filter I would add:

> Name one symbol step 1 introduces or changes that step 2's *solution* must reference. Grep for
> it across step 2's whole crate — not just the file — including `use` lines and `From`/`Into`
> impls. Then check whether any step-2 `fail_to_pass` test exercises step-1 behaviour. If the
> answer to both is no, the cascade is decorative; if the answer to either is yes, you may not
> claim it is.

`EARLIER:` and the cheap version of this belongs at **A2**, not A3: the card template already has
an "inter-step file overlap" field (`A2:138`), and it would cost nothing to make it
"inter-step **symbol** overlap" and require the grep.

---

## F17 — the gate that killed the most surfaces is the one the playbook spends the least ink on

**File:** `A-source/A3-idea-gate.md:83-108` (GATE 3)
`EARLIER:` Final tally across both rounds: the three-word recall test killed 6 surfaces, BAN 2
killed 2, the observability line killed 2, namability killed 2 — and **GATE 3 disclosure killed
the two cards and the last live surface**, i.e. everything that got far enough to matter.

The three disclosure channels that fired were, in order of how much they cost me to find:
1. a **merged PR** (`gh pr list --state all`) — one command, killed C01;
2. an **open issue's comment thread** (`gh issue view N --comments`) — one command, killed S01,
   and I skipped it in round 1;
3. **in-flight remote branches** (`git branch -r`) — one command, and no act asks for it at
   surface level (F15).

GATE 3's prose is ~80% about issues and their traps. The merged-PR arm gets one clause of one
sentence. On a repo maintained by a single prolific author, the merged-PR and branch arms are
the ones that fire. **Fix:** reorder GATE 3 to run PR-then-branch-then-issue, and give each arm
one worked example rather than giving issues three.

`WASTE:` the corollary is that GATE 3 is cheap — under two minutes for the full sweep once I
scripted it — and it invalidated work that had cost two MetaCode dispatches and a Docker
harness. **Any gate this cheap and this lethal should run before card elaboration, not after.**
That is the same conclusion as F7 and F10 arriving from a third direction.

---

## F18 — there is no act-file for "the repo is dead, write it up"

**File:** `00-ROUTER.md` §1 state table; `A-source/A3-idea-gate.md:253`
`PINPOINT:` A3's NEXT says *"back to `A-source/A2-idea-generate.md` if no survivor"* — an
unbounded loop with no termination condition. Nothing says how many rounds to run, what evidence
licenses stopping, or where the write-up goes. The router's §1 table has no state for "repo
exhausted". I got the stopping rule from my run brief
(`/tmp/pipeline-compare/PAIR-COMMON.md:83-85`), not from the playbook.

This matters because A3 is emphatic that a well-evidenced kill is a *good* outcome
(`A3:10`) — but an outcome the process treats as good should have a defined exit, an artifact,
and a place in the ledger. As written, the only way to stop is to decide to, which is exactly the
pressure that produces a manufactured survivor.
**Fix:** add a state `S2b | A2/A3 cycled twice with no survivor -> write ledger/RUNS.md entry and
stop`, and say what that entry must contain (the kill ledger, the disclosure log, and the
structural reason, so the next person does not re-screen the repo).

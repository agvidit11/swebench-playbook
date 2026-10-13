# RUNBOOK 1 — BRAINSTORM (stages 0 → 1d)

Pick a repo, find candidates, and prove each one has measured outcome variance
BEFORE it gets a score. This is the whole ideation phase in one file — if you
were dispatched to source candidates, read this and nothing else.

Companion: `references/signal-integrity.md` — read before believing any number.
Idea libraries this stage consults live in `~/swebench/`:
`FORK-PATTERNS.md`, `SEARCH-AXES.md`, `ALGO-CATALOGUE.md`.

## Role split (Vidit's direction, 2026-09-17)

| Model | Does | Never does |
|---|---|---|
| **Codex** | idea sourcing — the wide survey, merging, scoring, step breakdown; the grading tests; and every other task file (`solve.sh`, Dockerfile, `task.toml`, README) | — |
| **Muse** | `instruction.md` (provenance-mandatory); optional second-opinion survey | — |
| **Claude** | **validation only** — hollow-premise checks, novelty sweeps, running probes, reading code to confirm claims, preflight | **generate ideas or surfaces**; write **any** file inside a task directory |

Rationale from wave 1: Claude-as-analyst was the error source (repo pre-screen
wrong on 2 of 4, a false "standards-pinned has no fork" rule, a dedup method
that returned 0 on a repo with 11 peer tasks). Claude-as-verifier held up — four
independent spot-checks of agent claims, zero inflated. Play to that.

Revisit if the results say otherwise.

---

---

## NON-NEGOTIABLES FOR THIS PHASE

- **Do not accept any pre-screen.** The coordinator's repo screens were wrong 4
  times out of 4 — most damningly `commons-lang`, reported as "0 hits" when it
  has 18 peer tasks. Run every gate yourself.
- **Do not manufacture a survivor.** Three of four A/B repos returned zero and
  those were the correct answers. A well-evidenced "this repo is dead" is worth
  more than a candidate that dies at calibration two days later.
- **Do not pad the surface list to hit a number.** If the repo supports 11 real
  surfaces, report 11.
- Deliverable when shortlisting repos: **5-7 ranked repos** with full gate
  evidence, and say plainly which you would NOT pick and why.

# PART A — THE STAGES

## 0 — COMPOSE THE LENS (do this before any survey)

A task is not found by staring at a repo. It is **composed** from three
independent choices, and a strong candidate has one from each layer:

| Layer | Library | Question it answers |
|---|---|---|
| **C — search axis** | `~/swebench/SEARCH-AXES.md` (18 ranked) | *How do I look at this repo?* |
| **A — fork shape** | `~/swebench/FORK-PATTERNS.md` Part A (P1-P6) | *What shape of divergence am I building?* |
| **B — technique** | `~/swebench/ALGO-CATALOGUE.md` (46 entries) | *What makes it genuinely hard?* |

Worked composition:
> **C1 late-bound unknowns** × **P6 revert-and-redo** × **B: MVCC snapshot
> isolation** → step 1 parses unresolved references and resolves eagerly against
> a single registry; step 2 adds a concurrent-reconfiguration requirement that
> makes eager single-registry resolution untenable, forcing snapshot-consistent
> resolution. Step 2 must rewrite step 1's files, so the file set is pinned.

Composing beats surveying: it costs a grep per layer, and it inherits a grading
shape that already calibrated. A blind survey costs an agent-hour and averaged
~1 task per hitting repo.

### The selection criteria, in priority order

0. **OUTCOME VARIANCE IS THE TARGET, not design divergence.** Ask: *what makes
   one competent solver fail where another succeeds?* If the answer is "nothing,
   it just takes a while", it is a 5/5 whatever else is true. Measured: 59% of
   our scored tasks land at 0/5 or 5/5; only 23% in band. **Run the
   outcome-variance probe (RUNBOOK 1) before anything else** — build it
   n=5, grade the five outputs, want 1-3/5. Three sources of variance, strongest
   first: SEARCH (must find the defect), QUALITY (must build it to a standard it
   does not reliably hit), DESIGN (picks path X vs Y — weakest, and what we
   wrongly optimised for).

1. **OBSERVABILITY BEATS DIFFICULTY.** The advantage must be a visible contract
   change, not a speedup — we cannot grade a stopwatch. This eliminated half of
   classical algorithmics: the ALGO-CATALOGUE top-15 has **zero DP entries and
   zero classic string structures**, because they are asymptotically better and
   behaviourally identical. What survives clusters in persistence/versioning,
   ownership/lifetime, and ordering/visibility.
2. **MEASURE THE FORK, DO NOT ARGUE IT.** Run the n=5 cold model-prior probe
   (RUNBOOK 1) before investing. >=4/5 converging on the WRONG path =
   build it. >=4/5 on the desired path = it will one-shot, drop it. franz-go
   argued its way to a good fork score and returned 1.0.
3. **PREFER NET-NEW CAPABILITY.** Hollow premise, peer collision, public-PR
   sourcing and AI-authorship density bite ONLY on existing-gap sourcing — the
   axis that produced 5 zero-yield repos out of 8. New capability is immune to
   all four and has no per-repo ceiling.
4. **GROUND IT — name the motivating caller.** Reviews accept invented
   capability when it is tied to a concrete caller, scale requirement,
   compatibility obligation or operational constraint; abstract "nice API"
   additions are discounted on realism. If you cannot name who needs it and why
   now, rewrite the candidate.
### THE FORK-COLLAPSE RULE — criteria 2 and 5 are in direct conflict

Measured on casbin, and it invalidated two candidates that had already cleared
hollow-premise, novelty, grounding AND a full scoring pass.

**For some axes the fork IS the contract.** You are required to name the
contract (criterion 5) or the task dies at 0/0/0 — but naming it tells the model
exactly what to do, so the fork collapses to zero. Measured 5/5 on the DESIRED
path twice, and **5/5 again with the observable deliberately withheld**.

**The test, and it costs nothing:**
> Write the contract sentence. Write the observable-consequence sentence.
> **If they are the same sentence, the fork is zero.** Discard or re-cut.

rom's C5 died of exactly this before we had a name for it — mandatory `by:`
identities ruled out the positional/LCS alternative that WAS the divergence.
The escape is the boundary rule in RUNBOOK 2: the contract names entry
points, signatures and error classes; the observable lives in behaviour the
instruction does not describe.

**PROBE THE STEP THAT STATES THE CONSTRAINT — usually step 2, never only step 1.**
A 30/35 candidate was scored on a step-1 probe and inherited that score. But
**P6's whole premise is that step 2 states the constraint**, so step 2 is exactly
where collapse happens. Measured: step 1 held at Fork 5 (0/3 on the desired
path), while step 2 measured **5/5 desired** — and the prescribed re-cut, stating
the capability without the strategy, still gave **3/3**. 8 of 8 overall.

What "handing it over" looked like concretely: 5/5 refused the rebuild path
*because it suffix-merges the string table*, two naming the exact sorting/dedup
function, and all five found the string-sharing trap unprompted with the right
remedy. The claim carrying the score — "invisible to anyone who has not read
`src/write/string.rs`" — was refuted by measurement.

### COST CONSTRAINTS COLLAPSE BY CONSTRUCTION — the rule behind three deaths

**A step-2 constraint that is a COST constraint is a fork-collapse candidate by
construction.** "Must be O(1)", "bounded memory", "stop materialising", "don't
scan the whole map" — **none of these can be stated without naming the
technique**, because the cost clause IS the technique. And grading them pushes
you toward white-box assertions, so they fail twice over:

1. **Fork zero** — stating the constraint hands over the design.
2. **Over-pinned grader** — you end up asserting an implementation detail.

Measured on go-zero S4 (28/30): phrasing B, never saying "O(1)", returned 5/5
copy-on-write verbatim; phrasing A returned 5/5 immutable HAMT with path-copying,
and **three of five spontaneously criticised our intended answer** ("copy-on-write
makes the first mutation after cloning O(n)"). Its intended grader — "two clones
share the same backing pointer" — would have **failed 5/5 of the valid
solutions**, which are HAMTs with no shared map at all.

**Every step-2 constraint that has survived has been BEHAVIOURAL** — an
observable mode or state, not a cost. Before accepting a P6 candidate, classify
its step-2 constraint:

| Constraint shape | Verdict |
|---|---|
| "must be O(1) / bounded memory / stop materialising" | **cost — expect collapse** |
| "a reader holding an earlier handle must not observe X" | behavioural — viable |
| "old versions must remain readable after the update" | behavioural — viable |
| "the spill decision must be visible via `Storage()`" | **NOT a rescue — refuted below** |

**The behavioural-shadow rescue is REFUTED as a fork rescue (measured).** F3 was
ranked most rescuable because `Storage()` exposes the spill decision as a
first-class observable. It does — and F3 still measured **10/10 on the desired
path**. `Storage()` only *reports* a decision the cost clause already forced:
5/5 emitted that exact accessor when given the contract clause, and 5/5 built
the two-tier backing without it being mentioned at all.

**A behavioural observable rescues the GRADER, not the FORK.** It is
necessary-not-sufficient — the same shape as de-scaffolding. If the constraint
is a cost constraint, finding its shadow makes the task gradeable but still
one-shot.

### TWO FREE PRE-FILTERS — run these BEFORE the probe, they cost nothing

**1. Can you write the grader without naming the data structure?**
If not, **the fork is already zero.** Measured across three candidates whose
graders asserted a representation that would fail most valid answers: S4 (shared
backing pointer vs HAMTs), S5, and F5 ("count heap examinations" fails 5/10,
because half the valid solutions are intrusive LRU lists with no heap — and they
are *better*, amortised O(1) vs O(log n)). In every case the author reached for
the representation **because the two approaches were behaviourally identical**.
The white-box grader is a symptom of a dead fork, readable before any probe.

**2. How many materially different designs satisfy your observable sentence?**
**One family = fork zero.** This is the sharpest of the three and it catches
what the cost/behavioural split misses.

"A teardown must not damage a sibling container" is genuinely BEHAVIOURAL, not
a cost constraint — and it measured **10/10** anyway. The constraint does not
name the technique, but **refcounting is the only way to satisfy it**: the
lead's three "competing forks" collapsed on inspection to one (last-owner-wins
is behaviourally identical to refcounting, and clean-only-what-this-container-
uniquely-activated is outright invalid — if A and B both activate P, neither
uniquely owns it and the hook never fires).

So: **behavioural is necessary, not sufficient.** After writing the observable
sentence, enumerate the implementation families that satisfy it. If you cannot
name two that a competent engineer would genuinely choose between, there is no
fork to grade.

**3. Can step 1's signature express step 2's requirement?**
If not, a P6 cascade is **impossible in principle** — the constraint forces a
sibling API rather than a rewrite, and step 1 survives. F2's `([]T, error)`
cannot deliver an early record, so 5/10 kept the old function as a one-line
collector over a new streaming API; four said so explicitly. That sibling API
was also F2's own step 3, so steps 2 and 3 collapsed as well.

### RUN THE FORK PROBE AT STAGE 0, NOT AT 1c
Ten cheap calls invalidate candidates that otherwise consume hollow-premise,
novelty, grounding and a seven-axis scoring pass. Probe as soon as you have a
one-sentence capability statement — before any of it.

5. **NAME ONE ENTRY POINT, NOTHING ELSE — R-008** (the 2026-09-22 "name
   nothing" rule is SUPERSEDED 2026-10-13; evidence and the surviving parts are
   in `runbooks/2-build.md` → "The rule — R-008"). Exactly one public entry point
   with its signature, in lay voice; no internal symbols, no case lists, and the
   grader never depends on any other name. The text below is the 2026-09-22
   version — read "name-free" as "free of every name except the stated entry
   point".

   This is a constraint on the CANDIDATE, not just the prose: **the new
   behaviour must be observable through the repo's EXISTING public API.** Tests
   drive an existing entry point and assert effects, state, and that an error is
   raised with some property — never a new symbol's spelling or a new return
   shape. If the graded assertion cannot be written without naming something new,
   **reject the candidate**; do not name the symbol.

   This makes most `expose_interface` tasks unwritable. That category is
   1 passed / 13 failed, so the trade is worth taking. Prefer tasks where
   existing behaviour becomes correct, observable or safe.

### Self-collision is the binding constraint on reuse
The same **A-shape** in the same subsystem across two repos IS a peer collision —
our own jCasbin-vs-casbin rule turned on us. A-shapes self-collide after ~3
instantiations (P1 is already at 3 and closed). **B-techniques barely
self-collide at all**, because the domain and API carry the novelty — a
persistent tree in a cache and in a schema registry are different tasks. So
prefer varying the B layer when you need volume, and log every instantiation.

## 0b — Repo

Gates: RUNBOOK 1 (taxonomy, dedup, issue density, licence, toolchain,
can-it-carry-MT). Pick **few repos, many tasks** — target 5-6 tasks per repo, so
the Dockerfile, dedup sweep and toolchain fight amortize.

**We measured ~1 task per hitting repo and that number is an artefact, not a
limit.** Every wave-1/3 survey hunted EXISTING GAPS, which are finite and are
exactly the population contamination gates destroy. Feature ideation has no such
ceiling: one repo can host many net-new capabilities.

So a repo that has PASSED stage 0 is a durable asset, not a one-shot. Re-survey
it for **net-new capability** even if — especially if — gap-hunting returned
nothing. rom-rb returned zero gaps and has a 2.2s offline suite and one peer in
the whole corpus; that is a good feature-ideation target, not a dead repo.

### Stage 0 gate: AI-authorship density in release notes

**Check this before you invest a survey in a repo.** It is cheap and it
disqualifies repos nothing else catches.

```bash
f=$(ls <clone>/release-notes/VERSION* 2>/dev/null | head -1)
grep -ohE '\(fix by [^)]*\)' "$f" | sort | uniq -c | sort -rn | head
grep -ohE '\(fix by [^)]*\)' "$f" | grep -ci "claude\|copilot\|w/ AI"
# no release notes? try: git log --since=1.year -n 400 --format=%s%n%b | grep -ciE "claude|copilot|co-authored-by: .*(claude|copilot)"
```

Measured on jackson-databind 3.x: **86 of 154 attributed fixes (55.8%) are
authored "w/ Claude code"** — `(fix by @cowtowncoder, w/ Claude code)` is the
most common line in the file, 77 occurrences, accelerating (48 in 3.2.0 alone)
at ~157 commits/month.

Why this is disqualifying and why no per-candidate check finds it: grading a
Claude-family solver on a codebase whose maintainer publishes Claude-authored
fixes measures **recall as much as reasoning**. It is family-level solution
leakage. The observable symptom is a high hollow-premise rate — jackson came in
at **8 of 20 surfaces already implemented at HEAD**, and the Claude-assisted
fixes landed in precisely the subsystems the surfaces targeted.

Rough bar: above ~25% AI-attributed, treat the repo as contaminated for our
purposes regardless of how clean any individual candidate looks.

**Same family: agentic working notes checked into the repo.**
```bash
ls -d <clone>/docs/claude <clone>/.claude <clone>/AGENTS.md 2>/dev/null
```
`docs/claude/`, `.claude/`, `AGENTS.md` and similar are the maintainer's own AI
mining log. They describe **completed** work in proposal-shaped prose, which
reads exactly like a task idea — two bc-java candidates were sourced from there
and both were already implemented or public. Use the directory **in reverse**:
everything it covers is burned, so ideate from the code it does not mention.

## 1 — Wide survey (Codex)

Go wide. **Derive the count from the repo — measure first.**

Never ask for "5 ideas". A fixed count makes the model pad a thin repo and
truncate a rich one, and it pushes it to present each surface as a finished task
when at this stage you only want raw material. Do not filter weak forks here
either — label them and keep them; 1b is where filtering happens, and a surface
with a weak fork can still merge usefully into a cascade.

Measure before you ask:

```bash
R=~/repos-ext/<repo>
# NOTE: `xargs wc -l | tail -1` is only correct while xargs does not split.
# On a big tree it splits and each chunk prints its own "total", so tail -1
# silently reports the LAST chunk. Sum the totals instead — a silent undercount
# puts the repo in the wrong sizing band.
LOC=$(find $R -name '*.go' -o -name '*.rb' -o -name '*.rs' -o -name '*.py' -o -name '*.java' \
      | grep -vE '/(vendor|node_modules|third_party)/|_test\.|/test/|_spec\.' \
      | xargs wc -l 2>/dev/null | awk '/ total$/{s+=$1} END{print s+0}')
SUB=$(find $R -mindepth 2 -maxdepth 3 -type d | grep -vE '/(\.|vendor|node_modules|testdata)' \
      | while read d; do ls "$d"/*.go "$d"/*.rb "$d"/*.rs 2>/dev/null | head -1; done | wc -l)
echo "LOC=$LOC subsystems=$SUB"
```

| Non-test LOC | Ask for |
|---|---|
| < 15k | 6–8 surfaces |
| 15k – 60k | 10–12 |
| 60k – 150k | **15–20** |
| > 150k | 20–25, or split the ask by subsystem |

Cross-check against subsystem count: roughly **2–3 surfaces per major
subsystem**. If the two numbers disagree badly, trust the subsystem count — a
repo with 200k LOC in three packages has less usable surface than the LOC
suggests.

At this stage a *surface* is: an invariant or behaviour area, the files it
lives in, its candidate fork, rough net-line size, and whether asserting it
needs real network / wall-clock / concurrency. It is **not** a task. Cheap to
produce, cheap to discard.

**Drive the survey from the composed lens (stage 0), not from a blank page.**
Name the C-axis, the A-shape and the B-technique in the prompt and ask for
surfaces that fit them. A lens-driven survey returns candidates that are already
half-validated; a blank-page survey returns whatever the model finds easiest,
which is existing-gap bugs — our worst axis.

Still ask for some unlensed surfaces as a control, so a bad lens choice does not
silently cost you the repo.

**Demand shape diversity in the ask.** Left alone an ideating model returns
almost entirely existing-gap bug surfaces — which is the population every
contamination gate destroys. We measured our own output at ~85%
`semantic_bugs` + `expose_interface`. So require explicitly:

> At least a third of the surfaces must be NET-NEW CAPABILITY rather than an
> existing bug or gap: something the library does not do today and plausibly
> should. For each of those, name the public API contract it would need —
> module, exact symbol names, argument order, return shape, error type.
> Also include at least two REVERT-AND-REDO shapes: a capability whose obvious
> first implementation becomes untenable under a second, later constraint.

Net-new capability is structurally immune to hollow premise, peer collision,
public-PR sourcing and AI-authorship contamination — see the shape catalogue in
RUNBOOK 1. It has its own failure mode (unnamed contract → 0/0/0 too
hard), which is why the contract must be stated at survey time.

**Put the hollow-premise question INSIDE the survey prompt.** This is the
single cheapest fix found so far. Require for every surface:

> State what HEAD does TODAY for this behaviour, with a `file.ext:line`
> citation. Then state whether the behaviour I am describing is already fully
> implemented there. If it is, say so and keep the surface in the list anyway.

Demand the **file:line citation**, not just a yes/no — that is what converts
stage 1a2 from research into verification. The graphiti run got 6 of 6 citations
accurate and its Claude verifier only had to confirm them.

Two agents converged on this fix independently. The graphiti run put it plainly:
**a merge model will describe existing behaviour back to you as a proposal
unless the brief forces a HEAD-gap answer first** — its first merge round
returned 3 candidates of which 2 were already fully at HEAD, and a re-brief with
HEAD line numbers produced 4 real ones. The go-zero run did the same and
returned **zero hollow premises** across 18 surfaces — all 18 came back marked implemented, which forced the merge stage to
build candidates out of what is *absent around* existing behaviour rather than
re-proposing what exists. Compare jackson (8 of 20 hollow) and bc-java (top
candidate fully shipped). Stage 1a2 still runs as an independent Claude check —
this shifts the work left, it does not replace verification.

The prompt that produced our first good survey is
`/tmp/spire-run/survey.txt` — copy its shape: ask for surfaces numbered 1..N,
~5 lines each, spread across subsystems, `FORK: none` allowed and kept.

Codex is now primary for the survey:
```bash
codex exec -s read-only --skip-git-repo-check -C ~/repos-ext/<repo> \
  --add-dir /tmp/<repo>-run -o /tmp/<repo>-run/survey.md \
  "Read /tmp/<repo>-run/survey.txt and follow it." < /dev/null
```
MetaCode remains available as a second opinion, and is still the ONLY model
allowed to write `instruction.md`:
```bash
# USE THE WRAPPER. Do not hand-roll the script -qec line.
~/.claude/skills/swebench-mt/mc2.sh /tmp/<repo>-run/survey.txt \
  ~/repos-ext/<repo> /tmp/<repo>-run/survey.out
```
`mc2.sh` passes the prompt as a file to `muse exec`, which removes both silent
failures (`metacode run` is retired and no-ops). Historically the second was
quoting: embedding `"$(cat prompt)"` inside the `script -qec` string means any
apostrophe — *"the crate's API"*, *"don't"* — terminates the quoting. **Measured
best case: the apostrophes are silently DELETED and the model receives a
corrupted prompt, exit 0.** Worst case the shell executes prompt fragments
(one agent got 2.5 KB of `command not found`). The wrapper passes the prompt as
a single argv element and warns when output is under 600 bytes.
**The Bash tool caps at 600s**, so `timeout 1700` only works when the call is
backgrounded — which is exactly what the pty wrapper enables. If you must stay
in the foreground, split the survey into subsystem passes at `timeout 560`
each; on a `>150k` repo you should be splitting by subsystem anyway.
The banner-only failure (192 bytes, **exit 0**, no error) is a **missing TTY**,
not backgrounding. `script -qec ... /dev/null` supplies one and the call works
detached — which is what makes parallel surveys possible at all, since the Bash
tool caps at 600s and a 147k-LOC survey runs far longer. It bit three separate
dispatches before the cause was found.

`--format text` is still load-bearing. Give it 1700s, not 900. The containment
clause in the prompt is not optional; a `--yolo` run renamed sibling task
directories three times in one day.

**Always check the output size before trusting it.** A ~200-byte result with
exit 0 is the banner, not an answer.

## 1a — Merge surfaces into tasks (Codex)

This is where multi-turn tasks actually come from, and it is the stage we were
missing. Most good 2-3 step cascades are **two or three related surfaces
combined**, not one idea with a second step bolted on afterwards.

Look for surfaces that share state, a type, or a code path, and ask whether one
is a precondition for another. Three merge shapes that work:

| Shape | Step 1 | Step 2 |
|---|---|---|
| **Build-then-use** | introduce the representation | make a decision that consumes it |
| **Narrow-then-widen** | correct behaviour at one site | extend the same invariant across call sites |
| **Observe-then-enforce** | expose the state | act on it, changing observable behaviour |

Drop a surface if merging it adds nothing. Expect 15-20 surfaces to collapse to
**2-4 real task candidates** — that ratio is the point, not a loss. A surface
that cannot merge and cannot stand alone is a single-turn task; park it, do not
force it.

## 1a2 — Hollow-premise check (Claude) — is it actually broken at HEAD?

**Do this before novelty and before scoring.** Two of three jackson-databind
candidates died here: the behaviour they proposed to add *already held at HEAD*,
so step 2's assertion would have passed at base on an empty patch. An ideating
model will confidently describe a gap that was closed years ago.

For each merged candidate, open the actual code path and confirm the gap exists:

```bash
grep -rn "<the function that supposedly lacks the behaviour>" --include=*.<ext> <clone>/src
```
Read the function. If the precedence / ordering / guard the candidate proposes
to introduce is already implemented, the candidate is dead — say so and move on.
jackson's `CoercionConfigs.findCoercion()` already documents its own
class → logical-type → shape-default precedence in comments.

This is the cheapest kill available and it costs one file read. It is also the
early form of the base-commit repro rule: a task whose `fail_to_pass` passes at
base is unsalvageable, and finding that out at scaffold time costs a full cycle.

## 1b — Novelty gate (Claude) — run this BEFORE scoring

**Order matters: novelty runs before scoring.** Scoring costs a full Codex pass
over the repo; novelty kills a candidate for free. On the spire run C4 scored
highest of five and was then killed outright by two open issues — that scoring
pass was pure waste.

Repo-level dedup does not cover this. Run it **per surviving candidate**, on the
specific behaviour, before any authoring. This is the last point where dropping
a candidate costs nothing.

**REFRESH THE CORPUS FIRST, AND RUN THE LIVE SEARCH BEFORE YOU CLONE.**
`/tmp/llc` is a git checkout and goes stale — it was **2 weeks behind** on
2026-09-17, which is long enough to miss same-commit MT peers entirely:

```bash
cd /tmp/llc && git pull            # do this every session
gh search code --owner codimango "<repo>" --limit 30   # PRIMARY gate, not a supplement
```
Measured misses from a stale corpus: `paper_trail` showed **0 local hits** while
a live search found a 2-step MT pinned to **the repo's own HEAD** on its single
strongest invariant; `rexml` showed 1 local hit while live search found an MT
whose slug embeds the exact commit that had just been cloned. Two of three
runner-up repos in one lane died to peers the local corpus could not see.

Run the live search **before cloning**, so a dead repo costs a search instead of
a clone plus a survey.

**Do NOT screen by org/repo slug.** Peer `instruction.md` files are
de-identified — they say "the codebase" and never name the slug. Screening for
`casbin/casbin` returned 0 while the repo actually had ~11 peer tasks, including
a 2-step MT task on the same repo 5 commits behind HEAD. That false negative
cleared a repo that should have been rejected outright.

Run all three, in this order:

```bash
cd /tmp/llc
# 1. FILENAME sweep — highest signal. Peer task files are named after the repo.
find . -iname "*<repo>*" -type f
# 2. bare-name CONTENT sweep — then READ the hits, do not count them
grep -rli "<repo>" tmp/tasks
# 3. distinctive API symbols — the invariant, not the repo
grep -rliF -- "<distinctive symbol>" tmp/tasks
```

Read every hit. Both directions of error are live:
- **False positives from homographs.** A `spire` sweep returns 24 files that are
  all *Slay the Spire*, *Aspire-Mobile* and "inspired"; 17 of 18 `SVID` hits were
  the substring inside "exportAsVideo"; `opa` returned 7,587.
- **False negatives from slugs**, as above.

**Cross-port peers count.** A task on jCasbin, casbin-rs or php-casbin burns the
same invariant as one on casbin. "Different language" does not waive a
collision. Same for sibling modules — a jackson-core task can collide with a
jackson-databind candidate. Watch for homograph noise: a `spire` screen returned 22 hits that
were all *Slay the Spire* and *Empire State Building*, and 17 of 18 `SVID` hits
were the substring inside "exportAsVideo". Read the hits, do not just count them.

**Check the remote branches too, not just the tracker.** casbin passes the
issue-density gate with 37 open issues but carries ~60 `copilot/*` remote
branches, mostly closed-unmerged agentic PRs each implementing a named gap —
public disclosure an order of magnitude beyond what the tracker shows.

```bash
git -C <clone> branch -r | head -50
```
Treat **closed-unmerged** PRs as a hard kill alongside merged ones. The fix is
public either way, which is what the rule is about.

Then search the repo's own tracker **on the invariant, not the symbol**, and
read the comment bodies:

```bash
gh issue list --repo <org>/<repo> --state all --search "<behaviour phrase>" --limit 20
gh issue view <n> --repo <org>/<repo> --comments
# `gh issue view` has silently returned EMPTY on some repos. If a body looks
# blank, confirm with the API before concluding the issue is thin:
gh api repos/<org>/<repo>/issues/<n> --jq '.title, .body'
# NOTE: `gh search issues --state all` is INVALID — only open|closed.
```
`--comments` is mandatory. spire #7199's *title* gives no hint that its body
proposes three concrete remedies with maintainer agreement — which is precisely
what makes a candidate dead. A title-only scan passes it.

**Symbol searches miss behaviour-phrased issues.** jackson #959 ("Schema
generation: consider active view") contains neither `acceptJsonFormatVisitor`
nor `depositSchemaProperty` — the symbols the candidate was built on. Search the
tracker by *behaviour phrase*, and search the **test tree** for an existing test
of the behaviour:

```bash
grep -rln "<behaviour keyword>" <clone>/src/test | head
```
A shipped test for the behaviour is proof the direction is already public.

**Inline issue markers are a cheap contamination metric.** Repos that embed
`[databind#1234]`-style references in source let you measure per-file
disclosure density: jackson carries 1,110 markers naming 625 distinct public
issues. A high-density file is a mined file.

```bash
grep -rohE '\[[a-z-]+#[0-9]+\]' <clone>/src/main | sort -u | wc -l
grep -rcE '\[[a-z-]+#[0-9]+\]' <path/to/candidate/file>
```

**Public-PR sourcing is PROHIBITED** — no exception for obfuscation, claimed
contamination-safety, or post-cutoff timing. If the fix exists in a merged PR,
issue thread, SO answer or blog post, the candidate is dead. Record what you
searched, not just the verdict.

## 1c — Score and rank the surviving candidates (Codex)

MetaCode proposes; a **different** model scores. Ask Codex to read the repo and
return a table, 1–5 on each axis, no prose until the table is done:

| Axis | 1 | 5 |
|---|---|---|
| **Novelty** | exists on SO/blogs/peer tasks | no public analogue found |
| **Difficulty** | a competent model one-shots it | needs real domain reasoning |
| **Fork strength** | "more edge cases" | two reasonable designs diverge observably |
| **Harness-ability** | timing/network/flaky to assert | deterministic, cheap to grade |
| **Observability** | advantage is only "faster" / internal | the advantage IS a visible contract change |
| **Realism / fit** | the capability invents machinery this repo has no place for | a maintainer would plausibly want it, and the host subsystem already exists |
| **Cascade** | steps are independent chunks | step 2 is impossible without step 1 |
| **Scope** | <20 net lines | 80–150 net lines across 2-4 files |

**Threshold: build only at >= 28/40, and never with Fork strength <= 2,
Observability <= 2, or Realism/fit <= 2.** Three veto axes.

**Realism/fit was added 2026-09-17 because the rubric contradicted the library:**
FORK-PATTERNS mandates naming a motivating caller, and then nothing scored it. A
bc-java candidate scored 29 while proposing a write-ahead log inside `bcmls` —
a protocol codec **with no I/O layer at all**. The capability was real, the
observable was clean, and the host was imaginary. Score this axis by asking: does
the subsystem that would own this capability already exist?

Observability is a veto because it is the constraint that eliminated half the
algorithm catalogue: a technique that is asymptotically better but behaviourally
identical cannot be graded at all, however hard it is to implement. Score it
from the ALGO-CATALOGUE entry's "observable consequence" field — if that field
says *none*, the candidate is dead regardless of every other score.

Score Harness-ability from the GRADING path, not the project build system —
bc-java scored 3 on "needs Gradle + JDK 25" when a direct `javac --release 8`
compiles 4,501 files in 11.6s.

Calibration target, since it is easy to get backwards:

- In-band on Avocado is **1-3 of 5, and LOWER IS BETTER.** 1/5 is ideal, 3/5 is
  the ceiling, 4/5 is over it. A step reading 1/5 is a success to leave alone.
- **Avocado 0/5 is NOT a failure.** The gate is one pass AND one fail **on the
  same model** — and that model may be Avocado, Opus or GPT. The server only
  says *too hard* when NO model passed: `avocado 0, opus 0, gpt 0`. So when
  Avocado is 0/5, go read Opus and GPT before touching anything.
- Corollary: harder is cheap, easier is expensive. Overshooting into Avocado
  0/5 usually still passes on another model; overshooting into 4/5 does not.
Fork strength is a veto axis — franz-go scored well on everything else, had no
fork, and returned 1.0. Below threshold, either re-ideate or convert to
single-turn.

Make Codex justify each score in one line with a concrete repo reference. An
unjustifiable 4 is a 2.

**Score Fork strength from the model-prior probe, not from argument.** Run the
n=5 cold probe in RUNBOOK 1 §model-prior fork before assigning this axis.
≥4/5 converging on the WRONG path = 5. ≥4/5 on the desired path = 1, do not
build. Even split = 3. Fork is the veto axis, so it is the one worth measuring
rather than debating — franz-go argued its way to a good fork score and returned
1.0.

## 1d — Step breakdown (Codex)

Before any authoring, state for each step: what it adds, what it depends on from
the previous step, and the delta size. Then the honest question — **could a
solver do step 2 without step 1?** If yes it is not a cascade, it is two tasks
in a trench coat.

### ALWAYS ATTEMPT MULTI-TURN FIRST (policy, 2026-09-17)

A multi-turn task is worth roughly 3x a single-turn one, so single-turn is a
**fallback, never a first choice** — even for a candidate that scored low.
Before declaring single-turn, work the ladder in order:

1. **Can the cascade be rescued by moving information?** The usual fix is making
   step 1 own an artifact step 2 is *required* to consume. go-zero C1 needed
   `PendingFlushes()` or a solver could do step 2 with a private `recover()`;
   spire C3 holds only because step 2 is graded on the readiness payload. The
   question is not "are these two steps related" but **"does step 2's grader
   assert on something only step 1 can produce?"**
2. **Can a constraint be added that makes step 1's obvious implementation
   untenable?** That is P6 revert-and-redo, and it converts a weak cascade into
   the strongest shape we have — it pins the file set as a side effect.
3. **Can a third step carry the dependency?** Rung 5 of the escalation ladder.
   A 3-step task also buys the single-1.0 exemption, which a 2-step cannot use.
4. **Only then**, single-turn — and record WHY in the run log, so the next
   person does not re-litigate it.

Legitimate reasons to go single-turn, all seen today: step 2 is +2 net lines
(object-rs C4); step 2 is a predicate flip doable inline (graphiti C4); the
grading-relevant information already exists at HEAD so step 1 creates nothing
(casbin S9). Note each of these is a *proof* that no dependency exists, not a
judgement that the cascade is weak.

---

# PART B — SOURCING RULES AND GATES

# Sourcing: choose a repo and an idea that can carry multi-turn work

Sourcing is a fast kill-gate, not an investment thesis. Clear license, public
novelty, peer dedup, base reproduction, test feasibility, and multi-turn
carrying capacity before scaffolding, then start building. Do not turn this
file into approval ceremony: if the repo and idea were already assigned, skip
taxonomy optimization and repeat only the hard blockers (license, public/peer
novelty, executable base behavior, and MT carrying capacity).

The current calibration target is **1–3/5 Avocado successes on every step**.
`4/5` is too easy. Source an idea with enough architectural surface to create
a fair structural fork; calibration cannot rescue a thin idea.
`RustCrypto/formats` proved that after both steps stayed 5/5 through every
normal lever.

Read `references/signal-integrity.md` before interpreting any calibration number. Carry the selected structure into RUNBOOK 2 (`runbooks/2-build.md`).

## Taxonomy: optimize for real gaps, label honestly

Live snapshot: 39,434 tasks on 2026-09-14. Negative `gap_pct` means under-supplied.

| Language | gap_pct | Sourcing consequence |
|---|---:|---|
| Ruby | **-5.81** | Best language gap. |
| Java / Kotlin | -2.95 | Strong gap. |
| Rust | -2.11 | Gap. |
| Go | -1.95 | Gap. |
| JS / TS | -1.32 | Mild gap. |
| C / C++ | -0.17 | Neutral. |
| Python | **+24.66** | Heavily over-supplied. |

| Sub-domain | gap_pct | Sourcing consequence |
|---|---:|---|
| web_frontend | **-6.05** | Largest gap, but deterministic testing is harder. |
| security_and_privacy | **-4.22** | Best risk-adjusted gap: deep and testable. |
| web_backend | -3.91 | Strong gap. |
| systems_and_infra | -3.60 | Strong gap. |
| ml_ai_infra | -3.58 | Strong gap. |
| source_control | -2.52 | Gap. |
| networking | -1.64 | Gap. |
| graphics_and_rendering | -1.01 | Mild gap. |
| database_internals | +0.51 | Near neutral. |
| compilers_and_languages | **+4.69** | Saturated despite high technical depth. |
| devops_and_tooling | +4.88 | Saturated. |
| algorithms_and_data_structures | **+16.36** | Most saturated sub-domain. |

Counter-intuitive measured result: parser/compiler work can score high on domain depth while losing taxonomy value at `+4.69`; pure algorithms are worse at `+16.36`. The evidence-backed sweet spot is security, networking, or systems work in Ruby, Java, or Rust. Do not mislabel a compiler task as security to game the table.

## Search THREE axes: pattern-first, repo-first, category-first

**Pattern-first is the highest-yield axis and should usually be tried first.**
See `~/swebench/FORK-PATTERNS.md`.

A repo is not a finite pool of bugs. Measured 2026-09-17, repo-first gave 8
repos → ~86 surfaces → ~20 merged candidates → **4 buildable**: a 1-in-2 repo
hit rate and ~1 candidate per hitting repo. That does not reach 20 accepted
tasks in any reasonable time.

Two things break that ceiling:

1. **New capability has no per-repo limit.** Existing gaps are finite and are
   exactly the population contamination gates destroy. Capability the library
   does not have yet is unbounded, and immune to hollow premise, peer collision,
   public-PR sourcing and AI-authorship density.
2. **A proven fork pattern ports across repos, and carries its grading shape
   with it.** That second half is the real saving — the expensive part of a task
   is not the idea, it is the harness back-and-forth to land in band. Reusing a
   grading shape that already calibrated skips most of it.

The evidence that patterns transfer was accidental: our three strongest
independent candidates — spire `publishBundle`, go-zero flush accountability,
graphiti include authorization — are **the same pattern** (silent per-item
failure → expose per-item outcome → enforce a policy on it) across two languages
and three unrelated domains. Nobody was looking for it. That is P1 in the
library.

**Search for the precondition, not for bugs.** Each pattern in the library
states a greppable precondition, which turns sourcing into a scan of many repos
rather than a deep survey of one.

**Self-collision is the binding constraint.** The same pattern in the same
subsystem across two repos IS a peer collision — the identical rule we apply to
jCasbin vs casbin. Record every instantiation, vary the *domain* rather than
just the repo, and treat ~3 instantiations as the ceiling before a reviewer sees
a template.

## Search axes two and three: repo-first AND category-first

Repo-first (pick a repo, survey its surfaces) is what we do by default. It has a
structural weakness: it can only find **gaps that already exist**, which is
exactly the population that contamination gates destroy.

Category-first is the other axis: start from a task SHAPE and a domain, then
find a repo that can host it. Use both.

### What we have actually been building (measured 2026-09-17, 38 tasks)

| `category_usecase` | count |
|---|---:|
| `semantic_bugs` | 17 |
| `expose_interface` | 15 |
| everything else (`regression_bugs`, `null_reference`, `dependency_removal`, `concurrency_bugs`, `caching`) | 1 each |

Two shapes are ~85% of our output. That is a search-space problem, not a
sourcing-difficulty problem. (Some tasks also carry invalid enum values —
`feature`, `bug`, `Fix Bug`, `Data Processing`. Check the current enum before
using a value you have not seen accepted.)

### Net-new capability is the contamination-proof shape

Every gate that killed a repo today bites **only on existing-gap sourcing**:

| gate | applies to an existing gap? | applies to net-new capability? |
|---|---|---|
| hollow premise (already fixed at HEAD) | yes | **no — it does not exist yet** |
| peer-task collision | yes | **no** |
| public-PR / closed-unmerged PR | yes | **no** |
| AI-authorship density in release notes | yes | **largely no** |

So when a rich, well-engineered repo is disqualified on contamination, the
answer is not always to abandon the repo — it may be to switch shape. A
capability upstream has never built cannot have been built by anyone's model.

**The trap, and it is severe:** `expose_interface` tasks fail server calibration
as *too hard* (0/0/0 on every model) when the instruction does not name the API
contract. webauthn lost all three Avocado trials on an error class name the
instruction never mentioned, while implementing the feature correctly. For
net-new work the instruction MUST name the one public entry point with its exact
signature (R-008) — and the grader must not depend on any name beyond it (the
webauthn error class is exactly that defect). That is contract, not scaffolding,
and de-scaffolding never removes it.

### Shape catalogue — including the ones we have never built

| Shape | Exists-gap? | Notes |
|---|---|---|
| semantic bug fix | yes | our default; maximum contamination exposure |
| expose new interface | no | contamination-proof; name the contract or it dies at 0/0/0 |
| **revert-and-redo** | no | step 1 builds approach A; step 2 replaces it under a new constraint that makes A untenable. Strong natural cascade — step 2 is meaningless without step 1 |
| **behaviour-preserving refactor** | partly | graded on invariants held, not output changed |
| **migration / deprecation with a compatibility window** | no | old and new must coexist observably; rich in lifetime forks |
| **performance under a stated budget** | no | hard to grade deterministically — check harness-ability early |
| **observability / instrumentation** | no | "what an observer sees" is literally the fork |
| **API versioning / compat shim** | no | two contracts alive at once |
| concurrency / ordering | yes | good forks, but watch flakiness |

**Steps may mix shapes.** We have only ever built same-shape cascades. A step 1
that adds a capability and a step 2 that *reverts part of it and redoes it
differently* under a newly stated constraint is a genuine cascade and a shape no
peer task in our corpus uses.

## OUTCOME VARIANCE IS THE TARGET — not design divergence (2026-09-18)

**Measured across 22 scored tasks: 59% land at an extreme (0/5 or 5/5), only
23% in band.** The whole fork model was aimed at the wrong quantity.

- The **fork probe** asks *which implementation path does the model choose?* —
  a question about DESIGN. Design choice is largely deterministic: a frontier
  model, given the same problem, picks the same approach.
- The **gate** asks *does this trial pass?* — a question about OUTCOME. A task
  can have two genuinely different valid designs and have both pass every time.
  That is most of our 5/5s: real forks, zero variance.

**The only question that matters:**
> **What makes one competent solver fail where another succeeds?**
If the answer is "nothing, it just takes a while", it is a 5/5 regardless of
format, step count, or how elegant the fork is. Evidence: one task passed 5/5 at
903-1236s and $6-7/trial; another passed 5/5 with **four of five trials hitting
`AgentOOMError` and passing anyway**. Effort is not variance.

### THE THREE SOURCES OF OUTCOME VARIANCE

| Source | Mechanism | Evidence |
|---|---|---|
| **1. SEARCH** — the solver must FIND something (the defect, the relevant invariant, the interacting call site) before it can act | finding is stochastic; sometimes you look in the right place | `semantic_bugs` **7 passed / 7**; `expose_interface` **1 / 13** |
| **2. QUALITY** — the solver always produces *something*, but whether it is correct / robust / efficient enough varies | the artifact exists either way; the standard is what varies | Vidit, 2026-09-18 — and this is what rescues net-new capability |
| **3. DESIGN** — the solver picks path X vs Y | mostly deterministic; **this is what we were measuring and it is the weakest of the three** | 11 candidates measured Fork 1 after scoring 24-33/35 |

**Search variance is why bug tasks work.** The instruction states a symptom; the
model must locate the cause. `expose_interface` names the contract up front, so
there is nothing to find — execution is deterministic, giving 5/5, or 0/5 if you
overshoot. One of our tasks went straight from 5/5 to **0/5 on all three
models** with nothing in between: the signature of a deterministic task.

**Quality variance is how net-new capability can still work** — but only if you
grade a property the model achieves *sometimes*. Building the feature is
deterministic; building it correctly under an adversarial condition is not.
Grade robustness, edge-condition correctness, resource behaviour under
pressure, interaction with an existing subsystem — properties where a competent
implementation can plausibly fall short. Do NOT grade "did you build it".

### THE OUTCOME-VARIANCE PROBE — replaces the fork probe as the primary gate

Stop asking which path the model takes. **Make it build the thing, n=5, then
grade the five outputs against your actual grading property.**

```bash
for i in 1 2 3 4 5; do
  ~/.claude/skills/swebench-mt/mc2.sh /tmp/<task>/build-prompt.txt <clone> /tmp/<task>/impl-$i.out
done
# then run YOUR graded assertion against each of the five
```

| Result | Reading |
|---|---|
| **5/5 pass your grader** | too easy — no outcome variance. Do not build. |
| **1-3/5 pass** | **in band. This is the target.** |
| **0/5 pass** | too hard, or the grader is wrong — check for a false negative first |

This is a local mini-calibration and it measures the same quantity the server
does. It costs five calls and no Docker. **It is the single highest-value gate
in this playbook** — it would have caught every one of the 5/5 tasks before a
build cycle was spent.

### VALIDATED 2026-09-18 — it reproduced the server exactly

On `ruby-terraform-plan-model-empty-container-path-loss`: five cold MetaCode
implementations generated from the task's own `instruction.md`, then graded in a
local rebuild of the task image.

| | graded set (77) | full upstream suite (1547) |
|---|---|---|
| impl-1 | **9 failures** | 9 |
| impl-2/3/4/5 | 0 | 0 |
| oracle | 0 | 0 |

**4 of 5 — an exact match for the server's `avocado 4/5`.**

This is the first direct evidence that a local measurement tracks the gate.
Note what it is NOT: it is not the old local-Avocado run, whose correlation with
the server was 0.07. The difference is that this measures *outcome* (does the
produced implementation pass the graded set) rather than a harness pass-rate, so
the model-catalog and continuation-critic divergences that break local
calibration do not apply.

It also told us something no server reading could: **impl-1's 9 failures were
the entire difficulty.** Remove that one assertion cluster and all five
implementations pass, taking the task to 5/5 and flipping a passing gate to
failing. Use the probe to find out WHICH assertion is carrying the task before
you touch anything.

## The model-prior fork — a DESIGN probe, now secondary

"Two competent engineers would plausibly diverge" is a judgement call, and
judgement calls are why franz-go scored well and returned 1.0.

Sharper, and measurable **before you build anything**: a good fork is one where
**the model has a strong prior toward path X while the graded answer is Y**.

Probe it directly. State the problem cold — no hints, no repo context beyond
what a solver would get — and ask n=5 times, fresh each time:

```bash
for i in 1 2 3 4 5; do
  printf '%s\n' 'Describe in 3 sentences how you would implement <the capability>. Approach only, no code.' > /tmp/<repo>-run/prior-q.txt
  timeout 600 ~/.claude/skills/swebench-mt/mc2.sh /tmp/<repo>-run/prior-q.txt <clone> /tmp/<repo>-run/prior-$i.out
done
```

**Run it TWICE with different phrasing.** One probe cannot separate "the model
prefers this path" from "I led the witness". A rom candidate returned 5/5 on the
desired path, then 5/5 again on a deliberately non-leading variant — that second
run is what made the kill trustworthy at 10/10.

| Result | Reading |
|---|---|
| ≥4/5 take the SAME path, and it is NOT the desired one | **strong fork.** Build it — the model reliably goes the wrong way |
| ≥4/5 take the desired path | **no fork.** It will one-shot. Do not build |
| roughly even split | weak fork — some trials pass by luck; expect a noisy pass-rate |

This costs five cheap calls and replaces an argument with a measurement. It is
the same instrument as the alternative-implementation probe in
RUNBOOK 2 (`runbooks/2-build.md`), moved earlier — here it selects the idea,
there it validates the grader.

## Dedup: use the local corpus first

The Aug-31 corpus at `/tmp/llc` represents **133,263 unique tasks** and **151,249 copied `instruction.md` files**; the later local count was 154,135 files. Real task copies are under `/tmp/llc/tmp/tasks/<participant>/<task>.md`.

Two-stage search:

```bash
# Stage 1: candidate tasks naming the upstream.
grep -rl -i '<repo-name>' /tmp/llc | grep -v '/tmp/.*\.json'

# Stage 2: decisive repo + subsystem/invariant intersection.
grep -rl -i '<repo-name>' /tmp/llc \
  | grep -v '/tmp/.*\.json' \
  | xargs -r grep -l -iE '<invariant-term-1>|<distinctive-API-symbol>|<subsystem-term>'

# Highest-signal collision when the SHA appears in task text or names.
grep -rl -i '<first-7-of-base-commit>' /tmp/llc/tmp/tasks
```

Search distinctive API symbols even if the repo-name query is empty. In the `zendesk/biz` pass, two real same-gem peers were missed by repo-name/embedding search and exposed by symbol-level inspection. Verify that a hit is the same project and language: wave 1 had false alarms where “webauthn” meant a PHP project and “jsonschema” meant a Go project.

Interpretation:

| Finding | Action | Evidence |
|---|---|---|
| Same repo + same subsystem/invariant | Kill or move to a truly different subsystem and commit | `chromem-go` had six participants on `fbeda8a`; one peer's “rich metadata filtering” overlapped directly. |
| Same base commit, different subsystem | High risk; prefer a different commit | `redb` shared `fe01411` with another participant in an upstream with ~20 participants. |
| Same-sounding term, different project/language | Not a collision | Wave-1 `webauthn`/`jsonschema` false alarms. |
| Embedding search says LOW | Still run corpus/SHA checks | `similar-tasks` scored `zendesk/biz` top match only 0.652 and missed two same-gem peers. |

### Why GitHub search is only a freshness supplement

| Tool | Observed failure |
|---|---|
| `gh search code` | About 10 queries/minute, silently 403s in loops, and caps around 60 results/query. Counts are lower bounds. |
| `gh repo list --limit 1000` | Silently stops at 1,000 although the org had **5,105** `swe-bench-pro-*` repos and ~22,000 total repos. |
| Search against renamed repos | Observed 422 responses were consumed as empty/clean by loose scripts. Any nonzero exit or non-JSON response is **unknown**, never clean. |

Use live search only after the local corpus to cover its ~two-week staleness:

```bash
set -o pipefail
SWEBENCH_MT_SCAN_DIR=$(mktemp -d -t swebench-mt-dedup.XXXXXX)
gh search code --owner codimango '<owner/repo>' --limit 60 --json repository,path \
  > "$SWEBENCH_MT_SCAN_DIR/repo-hits.json" || { echo 'UNKNOWN: GitHub search failed'; exit 1; }
gh search code --owner codimango '<distinctive-API-symbol>' --limit 60 --json repository,path \
  > "$SWEBENCH_MT_SCAN_DIR/symbol-hits.json" || { echo 'UNKNOWN: GitHub search failed'; exit 1; }
gh search code --owner codimango '<first-7-of-base-commit>' --limit 60 --json repository,path \
  > "$SWEBENCH_MT_SCAN_DIR/sha-hits.json" || { echo 'UNKNOWN: GitHub search failed'; exit 1; }
jq length "$SWEBENCH_MT_SCAN_DIR"/*-hits.json
```

Do not infer “clean” from `[]` until stderr and exit status are clean. Do not infer population counts from the 60-result cap.

## Public sourcing policy

The safest shape is a net-new capability that upstream has never discussed.

Hard kill:

- Any merged public PR touching the proposed surface.
- Any open issue whose body or comments propose the direction, workaround, API, or remedy—even without code.
- Rewinding to a public PR's parent and reimplementing the public fix.

Checks:

```bash
git log --oneline --all -- <target-files>
gh issue list --search '<repo-specific keywords>' --state all
gh issue view <number> --comments
gh pr list --search '<repo-specific keywords>' --state all
```

Then execute the base behavior. Grep is not reproduction:

- Bug-shaped idea: run it and observe the failure at `base_commit`.
- Feature-shaped idea: compile or call the proposed capability and observe that it is absent.

Evidence: RustCrypto's first SPKI conversion idea was killed because open issue `#1604` asked for that capability. Circl's first FROST idea was killed by issue `#316` and PR `#349`. These are sourcing failures regardless of technical quality.

## Issue-density gate

Screen density before spending the ideation budget:

| Open issues | Policy | Evidence basis |
|---:|---|---|
| `< ~150` | Normal issue/PR screening | `franz-go` had 2 open issues and supported an undiscussed net-new offline ACL capability. |
| `~150–500` | Search each surface before deep exploration | Lower expected hit rate; this is an operational threshold from the backlog pass. |
| `> ~500` or “track every gap” culture | High sourcing risk; prefer another repo | Mbed TLS had **1,649** open issues. Four explored surfaces—ciphersuite policy, SKI/AKI linkage, X.509 profile policy, DTLS anti-replay—were all already public. |

Issue density and peer dedup are independent. Mbed TLS was peer-clean but public-sourcing hostile.

## License hard blocks

```bash
head -5 LICENSE* COPYING* 2>/dev/null
```

| Status | Licenses | Evidence |
|---|---|---|
| Hard block | AGPL-3.0, SSPL, Commons Clause, non-commercial Creative Commons, CreativeML OpenRAIL-M | Batch kill gate 1. |
| Eligible | MIT, Apache-2.0, BSD, GPL-2/3, LGPL, MPL-2.0 | Batch kill gate 1. |

Read the repository's license file; 14 backlog candidates were `NOASSERTION` through the API but resolvable locally. For dual licenses, cite the eligible arm actually used: Mbed TLS under Apache-2.0, H2 under MPL-2.0, JTS under EDL-1.0/BSD-3.

## Toolchain and suite gate

Proceed only if the repository has a deterministic, offline, container-runnable graded subset under 10 minutes.

| Requirement | Evidence |
|---|---|
| No network during tests | All selected backlog suites were screened as offline; network-dependent suites are not stable verifier surfaces. |
| Execute at base and after each gold delta | Three of five wave-1 tasks passed static validation but failed their first real oracle run. |
| Toolchain available in Docker | Host lacks Ruby and Cargo; `net-imap` and RustCrypto were validated in `ruby:3.3-slim` / `rust:1-slim` containers. |
| Build fits timeout | Hickory/Rust work needs `build_timeout_sec = 3600`; H2's full suite exceeded the 10-minute gate and required a subset. |
| Dependencies can install | Ruby slim needed `libssl-dev` for WebAuthn's native OpenSSL gem; Maven Central rate-limited ten concurrent Java tracks. |

Host inventory measured in wave 2: Java, Maven, GCC, CMake, Go, and Python were present; Ruby and Cargo were not. Docker had ample compute, but container DNS required `--network host` for dependency fetches on that host. Availability is host-specific—verify it, do not assume it.

## Can the repository carry a multi-turn task?

A valid multi-turn task needs a real dependency chain and enough architectural surface for a structural fork. “Two methods in sequence” is not sufficient.

Kill the idea if any answer is no:

1. Does step 2 consume a public artifact or state created by step 1?
2. Is step N's gold patch a clean delta from step N-1, not base-to-final?
3. Can two reasonable implementations diverge observably on timing, visibility, ownership, state, or composition?
4. Does each step require more than a small local translation of the named contract?
5. Can at least two valid implementation shapes pass the tests?
6. Is there a plausible final-step fork that can itself land at 1–3/5? The last
   step is never exempt, and the single 1.0 exemption is only one per task.

RustCrypto is the decisive negative example:

| Attempt | Measured outcome |
|---|---:|
| Step tests widened | 11 -> 24 and 11 -> 25 |
| Added surfaces | unused-bit sweep, nesting, truncation, malformed lengths, ~200 KB payload, pointer identity, lifetimes, delegation, idempotency |
| Symptom-only instructions | Still 5/5 and 5/5 |
| Avocado implementations | Reproduced the same ~12-line method on two types, effectively verbatim |

Conclusion: no grader can calibrate a task when every fair assertion falls out of the same obvious 12 lines. The redesign had to span crates (`der` -> `spki`/`sec1`/`pkcs8`/`x509-cert`) and introduce a real architectural choice. This is a repo/idea carrying-capacity failure, not a grader failure.

## Six-minute sourcing decision

| Gate | Pass evidence | Kill evidence |
|---|---|---|
| License | Eligible text in repo | Blocked license |
| Public novelty | No issue/PR/log remedy; base behavior reproduced | Any public fix direction |
| Peer novelty | Corpus repo + symbol + SHA checks clean; live refresh clean | Same repo and invariant, or hot base commit |
| Issue density | Searchable tracker with reasonable density | Mbed-TLS-like backlog where every explored gap is filed |
| Testability | Offline, deterministic subset executes in Docker under budget | Network, flake, or excessive runtime |
| MT carrying capacity | Genuine cascade plus observable structural fork | RustCrypto-style obvious local method |

If ambiguous after roughly six minutes, switch ideas. That budget came from the
batch kill criteria; Mbed TLS demonstrated the cost of spending an entire
ideation pass in a hostile tracker. Record only the decisive evidence and move
on—long sourcing narratives do not raise more tasks.

---

# PART B2 — REPO SHORTLISTING GATES

## Gate order — cheapest kill first

**1. Peer dedup — the method matters, the naive one returns 0 on mined repos.**
Peer `instruction.md` files are de-identified, so an org/repo slug search finds
nothing. Run all three and READ the hits:
```bash
cd /tmp/llc && git pull            # it goes stale; measured 16 days behind
find . -iname "*<repo>*" -type f   # filename sweep — highest signal
grep -rli "<repo>" tmp/tasks       # bare name — then read them
gh search code --owner codimango "<repo>" --limit 30   # PRIMARY gate, not a supplement
```
`/tmp/llc` has repeatedly missed same-commit MT peers that live search found.
Watch homographs: a `spire` sweep returns *Slay the Spire*; `opa` returned 7,587.
Cross-port peers count — a jCasbin task burns a casbin invariant.

**2. AI-authorship density — a stage-0 kill nothing else catches.**
```bash
f=$(ls <clone>/release-notes/VERSION* 2>/dev/null | head -1)
grep -ohE '\(fix by [^)]*\)' "$f" | grep -ci "claude\|copilot\|w/ AI"
ls -d <clone>/docs/claude <clone>/.claude <clone>/AGENTS.md 2>/dev/null
```
jackson-databind is **55.8% Claude-authored** (86 of 154 attributed fixes) —
family-level leakage no per-candidate check finds. Above ~25%, reject.
`docs/claude/` is a CONTAMINATION ORACLE: it describes COMPLETED work in
proposal-shaped prose. Everything it covers is burned.

**3. Issue density + disclosure.** <150 open is good, >500 reject. But the
tracker UNDERSTATES: casbin passes at 37 open while carrying ~60 `copilot/*`
closed-unmerged PRs each implementing a named gap. Check `git branch -r` on a
FULL clone (a `--depth` clone shows nothing and is not evidence). Closed-unmerged
PRs are a hard kill when the diff or thread contains the remedy.

**4. Licence.** Only CreativeML OpenRAIL-M / Ethos is prohibited. Copyleft is a
PLUS (contamination-resistant). AGPL/SSPL: warn, do not reject.

**5. Size.** Measure, don't guess. `xargs wc -l | tail -1` UNDERCOUNTS when xargs
splits — sum the totals: `| awk '/ total$/{s+=$1} END{print s}'`. Want 60k-150k
non-test LOC and many subsystems; 2-3 usable surfaces per major subsystem.

**6. Grading path, not build system.** bc-java looked like Gradle+JDK25 and was
scored Harness 3; a direct `javac --release 8` compiles 4,501 files in 11.6s and
a test class runs in 0.046s. Measure how a GRADED TEST would actually run.

## THE NEW GATE — can this repo host a NAME-FREE task?

Policy changed 2026-09-22 to "`instruction.md` names nothing"; **that is
SUPERSEDED 2026-10-13 by R-008** (one public entry point + signature is allowed
and is what every recent pass does — see `runbooks/2-build.md` → "The rule —
R-008"). What still holds: **the graded test must not depend on any new name
beyond that one stated entry point**. That means:

> **The best repos are ones with RICH EXISTING PUBLIC API where behaviour can go
> wrong**, not ones where you would add a new surface.

For each shortlisted repo, answer concretely: *if a defect existed in subsystem
X, could I assert it through an existing public entry point without naming
anything new?* Repos whose value is "you could add feature Y" score LOW now —
`expose_interface` is **1 passed / 13 failed** corpus-wide.

Favour: parsers/serialisers with existing round-trip APIs, engines with an
existing execute/apply entry point, clients with existing request paths, stores
with existing read/write APIs, anything with an existing observer/callback/hook.

---

# PART C — LEARNINGS THAT APPLY TO THIS PHASE

## The seven things that actually killed wave 1

**0. Put the hollow-premise question INSIDE the survey prompt** — cheapest fix
found so far. Require for every surface: *"State whether this is ALREADY
IMPLEMENTED at HEAD, and quote the line that implements it. If it is, say so and
keep the surface anyway."* The go-zero run did this and got **zero hollow
premises across 18 surfaces**, because it forced the merge stage to build from
what is *absent around* existing behaviour. Still run 1a2 as an independent
check — this shifts the work left, it does not replace verification.

**1. The hollow premise — the top killer.** In 2 of 4 repos the
HIGHEST-SCORING candidate proposed behaviour that **already exists at HEAD**.
jackson's `CoercionConfigs.findCoercion()` already documents the precedence it
was asked to add; bc-java's entire `X509CertificateReviewer` already ships and
Codex scored it 26/30 **while citing line numbers inside the finished code**.
A merge or score pass structurally cannot tell "this exists" from "this should
exist". Open the code path and prove the gap is real — BEFORE scoring.

**2. Dedup by slug is worthless.** Peer `instruction.md` files are
de-identified; they say "the codebase" and never name the repo. Use:
```bash
cd /tmp/llc
find . -iname "*<repo>*" -type f          # filename sweep — highest signal
grep -rli "<repo>" tmp/tasks              # bare name — then READ the hits
grep -rliF -- "<distinctive symbol>" tmp/tasks
```
**Read** hits, never count them. Both error directions are live: a `spire`
sweep returned 24 files that were all *Slay the Spire* / *Aspire* / "inspired";
`opa` returned 7,587. Cross-port peers count — jCasbin/casbin-rs/php-casbin
burn the same invariant as casbin, and a jackson-core task collides with a
jackson-databind candidate.

**3. The issue tracker understates disclosure.** casbin passes the density gate
with 37 open issues while carrying ~60 `copilot/*` closed-unmerged agentic PRs,
each implementing a named gap. Run `git branch -r` (on a full clone — a
`--depth` clone shows almost nothing and is not evidence) and search closed PRs.
**Treat closed-unmerged as a hard kill**: the fix is public either way.
Read issue **comment bodies** with `--comments`; spire #7199's title gives no
hint that its body proposes three remedies with maintainer agreement.
Symbol searches miss behaviour-phrased issues — search the **test tree** too.

**4. A spec constrains the OUTPUT, not the implementation strategy.**
~~Standards-pinned behaviour has no fork~~ — **RETRACTED 2026-09-17, it is
false.** RFC 5280 §4.2.1.10 says an implementation "MUST either process the
constraint or reject the certificate" — the spec writes the fork down for you.
Line 713 defers CRL currency to local policy. And bc-java's own HEAD commit is
"Clarify PKIXNameConstraints divergence from bc-csharp": same org, same RFC, two
conformant answers, deliberately unaligned. A candidate vetoed on this claim
re-scored 22-23/30 once the veto was lifted.

Forks in standards-implementing code live in: what the spec leaves to local
policy, error classification and recoverability, ordering of independent checks,
caching and lifetime, and what is surfaced to the caller. Do not reject a
protocol or crypto repo on this basis. Measure the fork with the model-prior
probe instead of arguing about the spec.

**5. Recall-only steps don't count as difficulty.** bc-java's best surviving
step 1 was `org.apache.commons.io.output.TeeOutputStream.close()` verbatim —
passes every gate, teaches nothing, and the cascade rested on it. If a step is
reproducible from memory of a well-known library, it is not a step.

**6. `docs/claude/`, `.claude/`, `AGENTS.md` in a repo is a CONTAMINATION
ORACLE, not an idea source.** It is the maintainer's own agentic working log and
it describes **completed** work in proposal-shaped prose — which reads exactly
like a task idea. Two bc-java candidates were sourced from there; both were
already implemented or public. Use it in reverse: anything it covers is burned,
so ideate from the code it does NOT mention. This is the same family as the
release-notes AI-authorship gate in RUNBOOK stage 0.

**7. Measure harness-ability from the GRADING path, not the build system.**
bc-java looked like it required Gradle + JDK 25 (`:core:test` ≈ 8 min), and was
scored Harness 3 on that basis. A direct `javac --release 8` across four modules
compiles 4,501 files in **11.6s**, and a standalone JUnit class runs in
**0.046s** — no Gradle, no JDK 25, no network. True harness-ability 4-5. A heavy
project build system does not imply an expensive grader; check before you
down-score.


## THREE FREE PRE-FILTERS — cheaper than the probe, run them first
0. **How many materially different designs satisfy your observable sentence?**
   **One family = fork zero.** Behavioural is necessary, NOT sufficient — a rom
   candidate had a genuinely behavioural constraint ("teardown must not damage a
   sibling container") and still measured 10/10, because refcounting is the only
   way to satisfy it. Its three claimed competing forks collapsed to one on
   inspection. If you cannot name two designs a competent engineer would
   genuinely choose between, there is nothing to grade.
1. **Can you write the grader without naming the data structure?** If not, the
   fork is already zero. A white-box grader is a SYMPTOM of a dead fork — the
   author reached for the representation because the approaches are
   behaviourally identical. Killed S4, S5, F5.
2. **Can step 1's signature express step 2's requirement?** If not, a P6 cascade
   is impossible in principle: the constraint forces a sibling API and step 1
   survives. F2's `([]T, error)` cannot deliver an early record.

Also: a behavioural observable (e.g. `Storage()`) **rescues the grader, not the
fork** — necessary-not-sufficient. F3 had one and still measured 10/10.

## THE PROBE GATE — run it BEFORE authoring anything

Two of our highest-scored candidates (27/30 and 30/35) were killed here after
passing every other gate. Argued fork strength has been wrong 3 for 3.

1. **Probe the step that STATES THE CONSTRAINT — usually step 2, never only
   step 1.** object-rs S7 was scored on a step-1 probe and inherited that score;
   step 1 genuinely held at Fork 5 (0/3 desired) while **step 2 measured 5/5
   desired**. P6's premise is that step 2 states the constraint, so step 2 is
   exactly where collapse happens.
2. **Probe TWICE with different phrasing.** One run cannot separate "the model
   prefers this" from "I led the witness". A rom candidate returned 5/5, then
   5/5 again on a deliberately non-leading variant — that second run is what
   made the 10/10 kill trustworthy.
3. **The fork-collapse test, free:** write the contract sentence; write the
   observable sentence. **If they are the same sentence, the fork is zero.** You
   must name the contract or the task dies at 0/0/0 — but for some axes the
   contract IS the fork. Escape by putting the contract on the BOUNDARY (entry
   points, signatures, error classes) and leaving the internal representation
   unnamed.
4. Reading: >=4/5 on the WRONG path = build it. >=4/5 on the desired path =
   BLOCKED, report and stop. Even split = weak, say so.
5. **CORRECTED 2026-09-18 — the old item 5 here was WRONG and cost a candidate.**
   It said: "does the step-2 constraint appear in ANY answer? 0 of n = real
   cascade." That conflates **un-volunteered** with **un-executable**.

   **"0 of n volunteered it" measures NOVELTY, not FORK and not CASCADE.**
   Clean counterexample: bc-java's caller-scoped MLS registry had **0/10
   volunteer** the constraint and **10/10 execute it correctly once stated**,
   including the non-obvious slice-propagation plumbing. The old rule was used
   to overturn Codex's "two tasks in a trench coat" verdict and inflate the
   score to 33/35. **Codex was right.**

   What actually matters: `instruction.md` MUST state the step-2 constraint. So
   the only question is whether the model can execute it once told. Measure that
   by probing step 2 WITH the constraint stated — >=4/5 correct = dead.

   Use un-volunteered only as weak evidence of novelty, never of difficulty.

## Language-specific priors — they invert
Persistence, COW and generational handles are **model-PREFERRED in Rust**
(3/3 returned `Arc::make_mut` + path-copying unprompted) → Fork 1, not 5.
Probably fine in C/Java/Go. Probe in the target language.

## SELECTION ERROR TO NOT REPEAT — read the per-axis scores, not the total

I dispatched bc-java C5 as a multi-turn build off its **30/35 headline**. The
same report's 1d table said, in plain text:
`| C5 ITS snapshots | single-turn | unchanged (not probed) |` — Cascade **2**,
never probed, and its realism concern was flagged two paragraphs later. A full
cycle was spent rediscovering a verdict already written down.

**Before dispatching anything: open the source report's per-axis table and the
1d cascade line. A high total with Cascade <= 2 is a single-turn candidate at
best.** Veto axes are Fork, Observability and Realism/fit — a total cannot
outvote them.

## Collision — check OUR OWN work, not just the peer corpus
The worst collision found for object-rs S7 was our own in-flight task: identical
`base_commit`, same struct, same file, same grading primitive. **Same repo +
same commit + same struct beats same-file-different-commit.** Diff every
candidate against `~/swe-bench-pro-agvidit/*/tests/config.json`.

## Tooling — all of these fail with exit 0
- Muse (MetaCode retired 2026-09-29): use `~/.claude/skills/swebench-mt/mc2.sh <prompt-file> <repo> <out>`.
  Never hand-roll `script -qec` — an apostrophe or backtick in the prompt
  silently deletes characters or command-substitutes, and one agent lost an
  entire step-2 contract that way (MetaCode then wrote the inverse of the rule).
- codex: keep the inline prompt ~2 KB, put the payload in a file reached via
  `--add-dir`, capture with `-o`. A 46 KB prompt returned only its opening plan.
- **Always check output size.** ~200 bytes + exit 0 is a silent failure.

---

## Reporting contract

Any agent running this reports **DONE / NOT DONE / BLOCKED per stage with
evidence**, never a summary. For a new `fail_to_pass`: the cell and seed IDs
downloaded, superseded attempts excluded, per-model counts, and the full Docker
dry-run table. If a stage is incomplete, write `NOT DONE: <reason> — BLOCKED`
and do not claim validation. If you skipped an expensive step, say so.

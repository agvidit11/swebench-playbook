# A3 — IDEA GATE

| | |
|---|---|
| **Owner** | Claude (verification, probes, novelty sweeps) + Codex (scoring, step breakdown). Neither may write contract prose — `→ 00-ROUTER.md` §5 |
| **Input** | the candidate cards from `HANDOFF A2` |
| **Output** | survivors, ranked — or an evidenced **"no survivor"** |
| **Exit** | **≥1 survivor carrying a MEASURED fork**, or an honest "no survivor" naming the gate that killed each card |

You measure claims; you do not generate replacements. A candidate that dies here goes back to `A2`, it is not repaired in place. Claude-as-analyst was the wave-1 error source (repo pre-screen wrong on 2 of 4, a false "standards-pinned has no fork" rule, a dedup method returning 0 on a repo with 11 peer tasks); Claude-as-verifier held up across four spot-checks with zero inflated. **A well-evidenced kill is a good outcome** — three of four A/B repos returned zero survivors and those were the correct answers.

## 0. Gate order — and why order is the whole economy

Novelty runs **before** scoring: on the spire run C4 scored highest of five and was then killed by two open issues, making the entire scoring pass waste. Probes run at stage 0, **not** after scoring: ten cheap calls invalidate candidates that otherwise consume hollow-premise, novelty, grounding and a seven-axis pass. Budget **~6 minutes per candidate** through GATE 0–3; still ambiguous → kill. `STATUS: LIVE`

**The canonical order is `0 → 1 → 2 → 3 → 6 → 7 → 4 → 5 → 8`.** `STATUS: LIVE`, two reviewers.

> **Why the PRIMARY gate runs seventh.** "Primary" means *most decisive*, not *first*. GATE 4 is
> the gate whose verdict you should trust above the others — and it is also the most expensive, so
> it runs after every free and cheap gate has had its chance to kill the card first. Order is
> economy; primacy is authority. Do not reorder GATE 4 earlier, and do not downgrade its verdict
> because it ran late.
Gates 6 and 7 are **free** and were previously listed after the two probe gates, which cost 15
model calls before a free check could kill the card. Where the prose elsewhere implies a different
order, this table wins. A killed card terminates its row immediately — do not run later gates on it.

One language-sensitive exception: GATE 2 is priced "one file read" but mandates execution at
`base_commit`. In a compiled language that is a build — curator spent ~12 minutes compiling before
a ~7-minute GATE 5 probe killed the card. **In compiled languages, take any cheap kill available
from GATE 3, 6 or 7 before paying for the GATE 2 build.**

| Gate | Kills | Cost | Run at |
|---|---|---|---|
| **0** | grader needs a name absent at `base_commit` | free | 1st |
| **1** | the fork is zero by construction, or the difference is unobservable | free | 2nd |
| **2** | the premise is already true at HEAD | one file read — **a BUILD in compiled languages** | 3rd |
| **3** | the direction is public | a few searches | 4th |
| **4** | no outcome variance — **PRIMARY** | 5 calls | **7th** |
| **5** | the model already prefers the desired path | 10 calls | **8th** |
| **6** | ungradeable / nondeterministic / trivial seam | free | **5th** |
| **7** | the cascade is decorative | free | **6th** |
| **8** | scoring and ranking — **survivors only** | a Codex pass | last |

## GATE 0 — can the graded assertion be written using only names that exist at `base_commit`?

**If no → reject the candidate. Do not proceed and name the symbol.** `STATUS: LIVE` (policy D1)

This is the gate that makes the naming policy work. The illegal configuration is a **silent spec plus a pinning test**: PEER measured `BAD_GRADING_WRONG` on **4 of 4** tasks built under an absolute "never name anything" rule, because the spec withheld the accessor name and the hidden tests asserted on it. Two lawful escapes exist — widen every spec, or forbid the configuration at sourcing. D1 takes the second. Note what that means here: if a candidate can only be saved by naming a new symbol in the contract, **this act's owners cannot write that prose** (`→ 00-ROUTER.md` §5) — reject the candidate, do not hand the sentence to someone else.

**Mechanical, four steps, no judgement:**

1. **Write the graded assertion out in code**, exactly as the test would express it — the call, the comparison, the expected value.
2. **Inventory every token in it**: entry point, method/accessor names, argument order, option keys, enum values *and their spelling*, error class, return/container shape, persistence scope, any test-only lifecycle hook.
3. **Classify each token** against the clone at `base_commit`: `grep -rn "<token>" <clone> --include=*.<ext>` → **IN-BASE** or **COINED**.
4. **Verdict.** All IN-BASE → PASS. Any COINED token the assertion depends on → **REJECT**, unless you rewrite the assertion to be genuinely indifferent to that token's spelling and shape, then re-run from step 1. Indifferent means the test accepts any spelling — **not** that the test keeps the pin and the prose gains a sentence.

5. **The one escape: a recorded GATE-0 OVERRIDE.** `STATUS: LIVE`

   REJECT is the default and should stay the answer almost always. But a blanket
   REJECT is wrong in one measured case: a feature/`expose_interface` task fails the
   server at **0/0/0 "too hard"** unless the contract names module, signature and
   error type — so for that shape, coining and *naming* is the only configuration
   that works at all. Against that, this gate's own corpus figure is **1 passed / 13
   failed**. The odds are bad; they are not zero.

   So a COINED token may pass GATE 0 **only** with an override written to
   `<task>/audit/gate0-override.md` before `B1`, containing:

   - the exact COINED token(s) and the assertion that depends on each
   - why the assertion cannot be made spelling-indifferent — the specific thing that
     breaks if you try
   - who decided (a human, or the act owner naming themselves) and the date
   - explicit acknowledgement of the 1-in-14 base rate

   An override is a **debt, not a pass**. It obligates `B2` to name every listed
   token in the contract, and `B3` to prove the grader accepts nothing broader.
   No file, no override — the candidate is rejected.

**How this squares with `instruction-lint.py`, which says the same tokens are legal.**
`STATUS: LIVE` — the two are not in conflict once you see they answer different
questions. This gate asks *should we build this candidate at all* and answers "almost
never". The lint asks *given a task that exists, is its contract/grader pair legal*,
and there the rule is absolute: a token the graded tests pin must be named in the
contract, because silent-contract-plus-pinning-test is the configuration that produced
`BAD_GRADING_WRONG` on 4 of 4 peer tasks. The lint will report `OK` for a named+pinned
coined token; that is a statement about legality, **not** a licence to have coined it.
Without a `gate0-override.md` on disk, a task in that state is one that should never
have left `A3`.

Mechanical proxy once tests exist: `check-symbol-reachability.py <task_dir> --repo <base_checkout>` classifies every asserted symbol STATED / IN-BASE / TEST-LOCAL / UNREACHABLE. **Any UNREACHABLE is the R01/R02 pattern.** The stated ratio ran **3/30, 6/25 and 4/25** on the three tasks that failed R01/R02/R08 — a low ratio is the signal before you read a single name.

Two consequences to accept: this makes most `expose_interface` tasks unwritable (**1 passed / 13 failed** corpus-wide, so the trade is worth taking — prefer candidates where existing behaviour becomes correct, observable or safe); and it **subsumes the coined-observability auto-reject** (`→ A2-idea-generate.md §6`), since a ledger whose invented field names carry the contract fails at step 3 every time. What the contract may still state later is `B2`'s business, not this gate's.

## GATE 1 — the four free pre-filters

**4. OBSERVATIONAL EQUIVALENCE — can a NON-DESIRED implementation be made indistinguishable from
DESIRED through the interface the grader can actually see?** If yes, outcome variance is **zero by
construction** and no amount of fork saves the candidate. `STATUS: LIVE`

This is the sharpest of the four and it is *not* the same as pre-filter 2. A candidate can pass
2 completely — behavioural observable, zero coined tokens, no data structure named — and still
die here.

**Measured, frostdb C1, 2026-09-22.** The constraint was "both sink uploads begin before
serialization completes". Design divergence was real and large: **9 of 10** cold implementations
produced a NON-DESIRED shape, a genuinely strong fork. Outcome divergence was **0 of 5** — every
one passed. The reason: `Upload(ctx, name, io.Reader)` is the entire surface a grader can observe,
and **a materialised buffer behind a gated reader replays every byte, block, EOF, error and
cleanup that a live stream produces.** All five satisfied the constraint by withholding EOF while
keeping the whole-block buffer. The property was not expressible as a predicate over the
interface, so it could not be graded, so there was nothing to measure.

An adversarial audit briefed to argue the candidate was ALIVE reached the same impossibility
independently. **That retires the surface, not just the card** — no re-cut of the constraint helps,
so do not spend an `A2` round on it.

**The check, in one question:** write down the interface the grader can call. Can you name a
sequence of observations through *only* that interface which a `NON-DESIRED` implementation cannot
reproduce? If you cannot, stop here.

### The original three



Run before any probe. They killed candidates that had already cleared hollow premise, novelty, grounding **and** a full scoring pass. `STATUS: LIVE`

**1. How many materially different implementation families satisfy your observable sentence? One family = fork zero.** The sharpest of the three. "A teardown must not damage a sibling container" is genuinely behavioural, not a cost constraint — and measured **10/10** on the desired path, because refcounting is the only way to satisfy it. The three claimed competing forks collapsed to one: last-owner-wins is behaviourally identical to refcounting, and clean-only-what-this-container-uniquely-activated is invalid (if A and B both activate P, neither uniquely owns it and the hook never fires). **Behavioural is necessary, not sufficient.**

**2. Can you write the grader without naming the data structure?** If not, the fork is already zero — a white-box grader is a *symptom* of a dead fork, because the author reached for the representation when the approaches are behaviourally identical. Killed S4 ("two clones share the same backing pointer" would have **failed 5/5** of the valid solutions, which are HAMTs with no shared map), S5, and F5 ("count heap examinations" fails **5/10**, because half the valid solutions are intrusive LRU lists with no heap — and they are *better*, amortised O(1) vs O(log n)).

**3. Can step 1's signature express step 2's requirement?** If not, a P6 cascade is impossible in principle: the constraint forces a sibling API and step 1 survives. F2's `([]T, error)` cannot deliver an early record, so **5/10** kept the old function as a one-line collector over a new streaming API, four saying so explicitly — and that sibling API was F2's own step 3, so steps 2 and 3 collapsed too.

**Cost constraints collapse by construction.** "Must be O(1)", "bounded memory", "stop materialising", "don't scan the whole map" — **none can be stated without naming the technique**, because the cost clause IS the technique. They fail twice: fork zero, *and* a white-box grader. Measured on go-zero S4 (scored 28/30): phrasing B, never saying "O(1)", returned **5/5 copy-on-write verbatim**; phrasing A returned **5/5 immutable HAMT with path-copying**, and **three of five spontaneously criticised our intended answer** ("copy-on-write makes the first mutation after cloning O(n)"). Classify every step-2 constraint:

| Shape | Verdict |
|---|---|
| "must be O(1) / bounded memory / stop materialising" | **cost — expect collapse** |
| "a reader holding an earlier handle must not observe X" | behavioural — viable |
| "old versions must remain readable after the update" | behavioural — viable |
| "the spill decision must be visible via an existing accessor" | **not a rescue** |

**The behavioural-shadow rescue is REFUTED as a fork rescue (measured).** F3 was ranked most rescuable because an existing accessor exposes the spill decision as a first-class observable — and F3 still measured **10/10 on the desired path**: 5/5 emitted that exact accessor when given the contract clause, and 5/5 built the two-tier backing without it being mentioned at all. **A behavioural observable rescues the GRADER, not the FORK** — necessary-not-sufficient, the same shape as de-scaffolding.

**The fork-collapse test, free, run it on every card:**
> Write the contract sentence. Write the observable-consequence sentence. **If they are the same sentence, the fork is zero.** Discard or re-cut.

For some axes the fork IS the contract. Measured on casbin: **5/5 on the desired path twice, and 5/5 again with the observable deliberately withheld.** rom's C5 died of this before it had a name — mandatory `by:` identities ruled out the positional/LCS alternative that WAS the divergence. The escape is `B2`'s boundary rule: contract on entry points and error classes, observable in behaviour the instruction does not describe.

## GATE 2 — hollow premise: is it actually broken at `base_commit`?

The cheapest kill available, one file read. **Two of three jackson-databind candidates died here.** `STATUS: LIVE`

```bash
grep -rn "<the function that supposedly lacks the behaviour>" --include=*.<ext> <clone>/src
```

Read the function. If the precedence / ordering / guard the candidate proposes is already implemented, it is dead — jackson's `CoercionConfigs.findCoercion()` already documents its own class → logical-type → shape-default precedence in comments. A merge or score pass **structurally cannot** tell "this exists" from "this should exist": in 2 of 4 repos the HIGHEST-SCORING candidate proposed behaviour already at HEAD, and bc-java's entire `X509CertificateReviewer` already ships while Codex scored it **26/30 citing line numbers inside the finished code**.

**Grep is not reproduction. Execute at `base_commit`** — bug-shaped: run it and see the failure; feature-shaped: call the capability and observe it absent, not merely differently named. Grep-based leakage checks miss silent fixes from aggressive refactors, and a task whose `fail_to_pass` passes at base is unsalvageable. Verify the card's **nearest-presence** quote yourself; an absence cannot be cited, only bounded.

## GATE 3 — public and peer disclosure, per candidate

> **Run these four FIRST. Each one killed a candidate on 2026-09-22 that had already cleared
> earlier gates.** `STATUS: LIVE`
>
> ```bash
> # 1. FUNCTION-scoped history. The file-scoped form returns noise and hides this.
> git log -L :<func>:<path> --oneline | head -40
> # 2. remote branches — count them properly; "all dependabot" was false 23 of 26
> git branch -r | grep -vE 'dependabot|^\s*origin/HEAD'
> git diff --stat origin/main...origin/<branch>        # for anything related
> # 3. issues WITH comments; a maintainer answer hides in the thread, not the title
> gh issue view <n> --comments
> # 4. JIRA-only repos: gh returns zero because the tracker is elsewhere. Sweep JIRA.
> ```
>
> **① is the highest-value command in this act and it was in no act-file.** On the lego run it
> caught step 1 being a **character-for-character revert of merged PR #1334** — a candidate that
> had already passed `GATE 0` at 14/14, `GATE 1`, and an *executed* `GATE 2` reproduction. The
> file-level form returned 12 commits of noise and showed nothing.
>
> **② found an 8,306-line finished implementation** on `origin/comments` in prism, with a
> 2,229-line test file, on a repo every other gate passed.
>
> **③ found the maintainer of santuario naming the fix** in a comment, and **④** found santuario's
> real issue count is 33, not the 12 `A1` recorded.


Repo-level screening does not cover this. Run per surviving candidate on the **specific behaviour** — the last point where dropping a candidate costs nothing. `STATUS: LIVE`

Hard kill, no exception for obfuscation, contamination score or post-cutoff timing: any **merged** public PR touching the surface; any **closed-unmerged** PR whose diff or thread contains the remedy; any open issue whose **body or comments** propose the direction, workaround, API or remedy — even informally, even with no code, even if our oracle would be more robust; rewinding `base_commit` to a public PR's parent; a **documented design decision** rejecting the capability, unless explicitly overruled with new justification. **Finding the premise in open issues is a disqualifier, not a confirmation** — it feels like validation and is training-data exposure.

```bash
git log --oneline --all -- <target-files>
gh issue list --repo <org>/<repo> --state all --search "<behaviour phrase>" --limit 20
gh issue view <n> --repo <org>/<repo> --comments          # --comments is MANDATORY
gh api repos/<org>/<repo>/issues/<n> --jq '.title, .body' # gh issue view has silently returned EMPTY
gh pr list --repo <org>/<repo> --search '<keywords>' --state all
grep -rln "<behaviour keyword>" <clone>/src/test | head   # a shipped test = the direction is public
```

- **4–6 identifier searches per premise** (issues/PRs plus code search), each recorded with its `total_count`. No candidate proceeds with its duplicate check marked "preliminary".
- **Search by behaviour phrase, not only symbol.** jackson #959 ("Schema generation: consider active view") contains neither `acceptJsonFormatVisitor` nor `depositSchemaProperty` — the symbols the candidate was built on.
- `--comments` is mandatory: spire #7199's *title* gives no hint its body proposes three concrete remedies with maintainer agreement. `gh search issues --state all` is **INVALID** — only `open|closed`.
- **The novelty gate has no feature-side arm.** Nothing above looks for a published **roadmap**. casbin carries open roadmap issue **#1608 enumerating 11 planned capabilities**, **96** `[feature]` issues and **36** feature-shaped branches. For feature candidates add:
  ```bash
  gh api "search/issues?q=repo:<org>/<repo>+label:feature+state:open" --jq '.items[].title'
  gh api "search/issues?q=repo:<org>/<repo>+roadmap+in:title" --jq '.items[].number,.items[].title'
  ls <clone>/{ROADMAP*,docs/roadmap*,CONTRIBUTING*} 2>/dev/null
  ```
- **Inline issue markers measure per-file disclosure density** — jackson carries **1,110** markers naming **625** distinct public issues, and a high-density file is a mined file: `grep -rcE '\[[a-z-]+#[0-9]+\]' <path/to/candidate/file>`
- **Peer dedup on this candidate's own invariant and symbols** — method and traps are owned by `→ A1-repo-screen.md §3`. **Sweep the concept under several plausible names, not one**: a P6-adjacent peer was found only because someone searched the concept — the searcher grepped `with_budget`, the peer's symbol was `ExecutionBudget`.

## GATE 4 — the outcome-variance probe (PRIMARY)

> ### First: GATE 4 as written could not run, and every run tonight waived it
>
> `STATUS: LIVE` — found independently by three runs on 2026-09-22. The probe below grades
> implementations "against your own assertions", but the contract comes from `B2` and the grader
> from `B3`, **neither of which exists at `A3`.** So the PRIMARY gate was waived every time and
> the decision fell to `GATE 5`, which this file itself calls *"weakest, and what we wrongly
> optimised for."* Thirteen candidates died that way.
>
> **Run GATE 4 in the A3-LOCAL form below. It is not optional and it is not the same as GATE 5.**
>
> **A3-LOCAL form.** You do not need `instruction.md` or a real grader — you need the card's
> `CONSTRAINT` and a *throwaway* assertion sketch:
>
> 1. Take `CONSTRAINT` verbatim from the card. That is your contract; do not improve it.
> 2. Write **3–5 throwaway assertions** that distinguish `DESIRED` from `NON-DESIRED` — in a
>    scratch file, never in `<task>/tests/`. They must **observe the discriminating behaviour**,
>    not a proxy for it. frostdb's assertion never observed serialization completion, which is
>    why its 5/5 meant nothing.
>    3. **Validate the sketch THREE ways before you trust it.** One check is not enough — the
>    frostdb redo showed a sketch can fail at base and still be blind to the real property.
>    - it **FAILS at `base_commit`** (an assertion that already passes measures nothing)
>    - it **FAILS on a negative control** — a hand-written implementation of a `NON-DESIRED`
>      shape. If your sketch passes the wrong shape, it does not observe the property.
>    - it **PASSES on a hand-written `DESIRED` implementation.**
>
>    All three are required. On frostdb the negative control was decisive: the old buffered
>    implementation showed "sink b reached the end of its copy, 2,739,919 bytes, while sink a
>    had consumed nothing."

> 4. Generate n=5 cold implementations from `CONSTRAINT` alone and run the sketch against them.
> 5. Want **1–3 of 5**. 0/5 or 5/5 kills the candidate — *and 5/5 after step 3 passed is a real
>    kill, unlike a GATE 5 convergence reading.*
>
> If the assertion sketch cannot be written without naming the data structure, stop: that is
> `GATE 1` pre-filter 2 and the fork is already zero.
>
> **A candidate may only be killed on `GATE 5` alone if GATE 4 A3-LOCAL was run and is
> inconclusive.** Record which form you ran in the handoff.


**Outcome variance is the target, not design divergence.** Across **22 scored tasks, 59% land at an extreme (0/5 or 5/5) and only 23% in band.** A task can have two genuinely different valid designs and have both pass every time. `STATUS: LIVE`

> **The only question that matters: what makes one competent solver fail where another succeeds?** If the answer is "nothing, it just takes a while", it is a 5/5 however elegant the fork.

Effort is not variance: one task passed **5/5 at 903–1236s and $6–7/trial**; another passed 5/5 with **four of five trials hitting `AgentOOMError` and passing anyway**.

| Source of variance | Mechanism | Evidence |
|---|---|---|
| **SEARCH** — must FIND the defect/invariant/call site before acting | finding is stochastic | `semantic_bugs` **7 passed / 7**; `expose_interface` **1 / 13** |
| **QUALITY** — the artifact exists either way; the standard varies | this is what rescues net-new capability | — |
| **DESIGN** — picks path X vs Y | mostly deterministic; **weakest, and what we wrongly optimised for** | 11 candidates measured Fork 1 after scoring 24–33/35 |

`expose_interface` names the contract up front so there is nothing to find: deterministic execution gives 5/5, or 0/5 if you overshoot. One task went **5/5 → 0/5 on all three models** with nothing in between — the signature of a deterministic task. For net-new capability grade a property the model achieves *sometimes*: robustness, edge-condition correctness, resource behaviour under pressure, interaction with an existing subsystem. **Do NOT grade "did you build it".**

**The probe: n=5 cold implementations from the task's own contract, graded against your own assertions.**

```bash
for i in 1 2 3 4 5; do
  ~/.claude/skills/swebench-mt/mc.sh /tmp/<task>/build-prompt.txt <clone> /tmp/<task>/impl-$i.out
done
# then run YOUR graded assertion against each of the five
```

| Result | Reading |
|---|---|
| **5/5 pass your grader** | too easy — no outcome variance. Do not build |
| **1–3/5 pass** | **in band. This is the target** |
| **0/5 pass** | too hard, or the grader is wrong — check for a false negative first |

**Validated once, exactly.** On `ruby-terraform-plan-model-empty-container-path-loss`: five cold MetaCode implementations from the task's own `instruction.md`, graded in a local rebuild of the task image. impl-1 produced **9 failures** in the graded set (77 tests) and **9** in the full upstream suite (1,547); impl-2/3/4/5 and the oracle produced **0** in both. **4 of 5 — an exact match for the server's `avocado 4/5`.**

**State the other half honestly.** A later check measured a purely local n=5 predicting the server on only **2 of 4 tasks**: local said 2/5 for two tasks that came back **avocado 4/4 and 5/5**. The local generator is not the graded model. Treat local-only numbers as a **lower bound on difficulty**, and prefer implementations pulled from real prior trials where they exist (`→ C-drive/C3-harden.md`). Both readings are LIVE; neither supersedes the other.

**Local Avocado pass-rate is NOT predictive.** Same commit: **3/5 locally, 1.0 on the server**; correlation **0.07 over 120 paired samples**. It is a **one-sided kill gate only** — local 0/5 or 5/5 means fix before pushing, anything between tells you nothing. The outcome-variance probe is a different instrument: it measures *outcome*, not a harness pass-rate, so the model-catalog and continuation-critic divergences that break local calibration do not apply.

The probe also reveals **which assertion carries the task**: impl-1's 9 failures were the entire difficulty — remove that one assertion cluster and all five implementations pass, taking the task to 5/5 and flipping a passing gate to failing. Before removing a test that looks unfair, check whether that test IS the difficulty.

## GATE 5 — the model-prior fork probe (SECONDARY, design)

> ### MANDATORY PRE-CHECKS — two of four kills on 2026-09-22 were invalid without them
>
> `STATUS: LIVE`
>
> **① The card must declare `CONSTRAINT:`, `DESIRED:` and `NON-DESIRED:` BEFORE you probe.**
> Direction is fixed in advance and never read off the outputs afterwards.
>
> **② Lint every probe prompt before it counts:**
> ```bash
> python3 ~/swebench-playbook/tools/probe-lint.py <card.md> <probeA.txt> <probeB.txt>
> ```
> It fails the probe if the prompt does not state the constraint, if it leaks the desired design,
> or if the two phrasings are the same phrasing twice. **frostdb C1 and santuario C3 were both
> killed by prompts that omitted the card's own constraint.** A probe that does not state the
> constraint measures nothing.
>
> **③ Apply the mapping in the stated direction, and say which direction you applied.**
>
> | Result | Meaning |
> |---|---|
> | ≥4 of 5 produce **DESIRED** | fork ~1 — candidate DEAD |
> | ≥4 of 5 produce **NON-DESIRED** | **STRONG FORK — the candidate SURVIVES GATE 5.** This is not a kill. |
>
> **"Survives GATE 5" is not "is a good task."** A strong fork only means models build different
> things; it says nothing about whether your grader can tell those things apart. frostdb C1
> measured **9 of 10 NON-DESIRED — a genuinely strong fork — and then died at GATE 4 with 0 of 5
> outcome variance**, because every implementation was observationally identical through the
> interface the grader could see. Fork is necessary, not sufficient. GATE 4 decides.
>
> frostdb C1's five implementations were all the card's own *wrong-path* shape. That is the
> second row. It was recorded as "10/10 desired" and killed.
>
> **④ Every GATE 5 kill gets an adversarial audit before it is final** (§KILL AUDIT below).


**Never score fork strength by argument. Argued fork strength has been wrong 11 times out of 11** — candidates scoring **24–33/35** all measured **Fork 1** when probed. franz-go argued its way to a good fork score and returned **1.0**. `STATUS: LIVE`

```bash
for i in 1 2 3 4 5; do
  timeout 600 script -qec "metacode run --yolo --format text --dir <clone> \
    'Describe in 3 sentences how you would implement <the capability>. Approach only, no code.'" \
    /dev/null > /tmp/<repo>-run/prior-$i.out
done
```

| Result | Reading |
|---|---|
| ≥4/5 take the SAME path and it is **NOT** the desired one | **strong fork** — build it |
| ≥4/5 take the desired path | **no fork.** It will one-shot. Do not build |
| roughly even split | weak fork — some trials pass by luck; expect a noisy pass-rate |

1. **Probe the step that STATES THE CONSTRAINT — usually step 2, never only step 1.** A 30/35 candidate was scored on a step-1 probe and inherited that score: step 1 genuinely held at Fork 5 (**0/3** desired) while **step 2 measured 5/5 desired**, and the prescribed re-cut — capability without strategy — still gave **3/3**. **8 of 8 overall.** P6's premise is that step 2 states the constraint, so step 2 is where collapse happens.
2. **Probe TWICE with different phrasing.** One run cannot separate "the model prefers this path" from "I led the witness". A rom candidate returned 5/5, then **5/5 again** on a deliberately non-leading variant — that second run made the 10/10 kill trustworthy.
3. **"0 of n volunteered it" measures NOVELTY, not fork and not cascade.** It conflates *un-volunteered* with *un-executable*. bc-java's caller-scoped MLS registry had **0/10 volunteer** the constraint and **10/10 execute it correctly once stated**, including non-obvious slice-propagation plumbing; the rule was used to overturn Codex's "two tasks in a trench coat" verdict and inflate the candidate to 33/35. **Codex was right.** Since the instruction MUST state the step-2 constraint, **probe step 2 WITH the constraint stated; ≥4/5 correct = dead.** `STATUS: LIVE` (corrected 2026-09-18)
4. **Priors are language-specific and they invert.** Rust: **3/3** returned generational slots + free list unprompted; **3/3** returned `Arc` + `Arc::make_mut` + path-copying unprompted — persistence/COW/generational handles are model-PREFERRED there, Fork 1. Ruby: **10/10** replaced a plain argument array with a single-use pending object unprompted, volunteering the unstated contract too (`cancel` in 7 of 10, result memoization in 4). The generalizable error: **the inverted premise is true about the REPO and false about the MODEL.**
5. **Two measured verdicts not to re-litigate.** P6 failed **5 of 13** probed candidates because the "clever" design was already idiomatic — including the highest scorer, p2c picker-state continuity, argued Fork 5 and scored 29/30, with **5 of 5** cold models writing the sophisticated design unprompted. Conversely "standards-pinned behaviour has no fork" is **RETRACTED and false**: RFC 5280 §4.2.1.10 says an implementation "MUST either process the constraint or reject the certificate", writing the fork down for you; a candidate vetoed on that claim re-scored 22–23/30.

## GATE 6 — Tier-0 structural gates

Each is a fail and each is decidable without a build. `STATUS: LIVE (PEER)`

| Filter | Test |
|---|---|
| **Seam test** [R03] | Step-1 gold must **fail** step-2's tests. If step 1 already states what step 2 asserts, there is no second turn |
| **Step-1 observability** [R01] | Step 1 must produce behaviour assertable from outside; grading private state rejects valid alternative designs |
| **Determinism scan** [R09] | No wall clock, concurrency race, benchmark threshold or NP-hard "minimum" in any contract. Verify the card's named injection point exists |
| **Mechanism-naming scan** [R01+R04] | Neither step may name a **file, algorithm, data structure or language construct** — implementation, fails R04. Interface naming is settled by GATE 0: a surviving candidate needs no new name, so there is nothing to pin |
| **Never grade against a library export** [R05] | If the reference answer is callable from inside the solution — matching a public export's output exactly — the grader leaks the solution |
| **Anti-overcorrection** [N04] | **Under ~20 lines, or composes two shipped functions → discard.** Verification alone selects trivia: absent *and* substantial. Target 80–150 net lines across 2–4 files |
| **Normaliser consistency** [R08] | If graded entries are read through a normaliser (`to_h`, a serializer, an accessor), **every** assertion must go through it; one assertion reaching past it re-narrows the contract |

## GATE 7 — cascade viability

**Always attempt multi-turn first** — worth roughly **3×** a single-turn task, so single-turn is a fallback, never a first choice. The honest question: **could a solver do step 2 without step 1?** If yes it is not a cascade, it is two tasks in a trench coat. Run **both** P6 operational tests before believing any cascade claim — the HEAD counterfactual and the parallel-API test, stated at `→ reference/R6-fork-patterns.md §P6`; measured on casbin, where P6 was narrated in all 8 candidates and **engineered in none**. Record both answers in the HANDOFF. `STATUS: LIVE`

For P6, **step 1 must be the universal first answer.** rom C3 died here: all 10 probes kept step 1's extracted boundary and built the object *around* it, so step 2 changed one `return` line and its grader passed with step 1 deleted entirely. Corollary — P6 concentrates difficulty in step 2 by construction, so **step 1 drifts over the too-easy ceiling**: all 5 bc-java MLS probes got step 1 right unprompted.

Before declaring single-turn, work the ladder: (1) rescue by moving information — **does step 2's grader assert on something only step 1 can produce?** (2) add a constraint making step 1's obvious implementation untenable (P6); (3) let a third step carry the dependency — a 3-step task also buys the single-1.0 exemption a 2-step cannot use; (4) only then single-turn, and record WHY. Legitimate single-turn proofs seen: step 2 is +2 net lines; step 2 is a predicate flip doable inline; the grading-relevant information already exists at HEAD so step 1 creates nothing. Each is a *proof that no dependency exists*, not a judgement that the cascade is weak.

**Carrying capacity is a repo/idea property, not a grader failure.** RustCrypto widened step tests **11 → 24** and **11 → 25**, added an unused-bit sweep, nesting, truncation, malformed lengths, a ~200 KB payload, pointer identity, lifetimes, delegation and idempotency, and went symptom-only in the instructions — and stayed **5/5 and 5/5**, because Avocado reproduced the same ~12-line method on two types effectively verbatim.

## GATE 8 — score the survivors, and read the table correctly

Only candidates past GATE 0–7 reach scoring, and a **different** model scores than proposed. Codex returns the table first, no prose, justifying each score in one line with a concrete repo reference — **an unjustifiable 4 is a 2.** `STATUS: LIVE`

| Axis | 1 | 5 |
|---|---|---|
| **Novelty** | exists on SO/blogs/peer tasks | no public analogue found |
| **Difficulty** | a competent model one-shots it | needs real domain reasoning |
| **Fork strength** | "more edge cases" | two reasonable designs diverge observably |
| **Harness-ability** | timing/network/flaky to assert | deterministic, cheap to grade |
| **Observability** | advantage is only "faster" / internal | the advantage IS a visible contract change |
| **Realism / fit** | invents machinery this repo has no place for | a maintainer would plausibly want it, and the host subsystem already exists |
| **Cascade** | steps are independent chunks | step 2 is impossible without step 1 |
| **Scope** | <20 net lines | 80–150 net lines across 2–4 files |

**Threshold: build only at ≥28/40, and never with Fork strength ≤2, Observability ≤2, or Realism/fit ≤2.** Three veto axes. Score Fork from GATE 5's measurement (≥4/5 wrong path = 5; ≥4/5 desired path = 1, do not build; even split = 3). Observability is a veto because it eliminated half the algorithm catalogue — asymptotically better but behaviourally identical cannot be graded at all. Realism/fit exists because the rubric contradicted the library: a bc-java candidate scored **29** proposing a write-ahead log inside `bcmls`, a protocol codec **with no I/O layer at all**. Score Harness-ability from the GRADING path → `A1-repo-screen.md` §8.

**Read the per-axis scores, never the total — veto axes cannot be outvoted.** A bc-java candidate was dispatched as a multi-turn build off its **30/35 headline**; the same report's step table said in plain text `| C5 ITS snapshots | single-turn | unchanged (not probed) |` — Cascade **2**, never probed, realism flagged two paragraphs later. A full cycle was spent rediscovering a written-down verdict. **A high total with Cascade ≤2 is a single-turn candidate at best.**

**Calibration target, easy to get backwards.** In-band on Avocado is **1–3 of 5 and LOWER IS BETTER**: 1/5 ideal, 3/5 ceiling, 4/5 over it; a step reading 1/5 is a success, leave it alone. **Avocado 0/5 is NOT a failure** — the server says *too hard* only when no model passed (`avocado 0, opus 0, gpt 0`), so read Opus and GPT first; 1–3/5 is a stricter operational target, not the server's validation condition. Corollary: **harder is cheap, easier is expensive.** Decode → `reference/R1-field-authority.md`; is the number real → `reference/R2-signal-integrity.md`.

## NO SURVIVOR — the bounded terminal

`STATUS: LIVE`. **Every one of five reviewers flagged this as blocking**, and every run tonight
had to invent its own stopping rule from its dispatch brief rather than from the playbook. As
written, `no survivor → A2` was an unbounded loop with no exhaustion state.

```
RESURVEY_BUDGET: 2      # A2 rounds per repo, including the first
```

**Write exactly one of these as your `EXIT:` line — the router reads it and nothing else:**

| `EXIT:` | When | Routes to |
|---|---|---|
| `EXIT: SURVIVOR` | ≥1 candidate carrying a MEASURED fork **and** a GATE-4 A3-LOCAL result in band | `B1` |
| `EXIT: NO SURVIVOR — RESURVEY` | budget remains **and** an untried lens/axis exists — name it | `A2`, round n+1 |
| `EXIT: NO SURVIVOR — REPO EXHAUSTED` | budget spent, **or** the kill is repo-scoped | `A1`, next shortlist entry |

**Go straight to `REPO EXHAUSTED`, skipping any remaining budget, when the kill is a property of
the repo rather than of the card.** Measured tonight — each of these retired a whole repo:

- the repo is a **compatibility/reimplementation** library (a reference is importable)
- it **implements a published spec** and what the spec leaves open is only error reporting
- the discriminating property is **not expressible over the interface the grader can see**
  (GATE 1 pre-filter 4) — an adversarial audit confirmed no re-cut helps
- **upstream churn** in the target subsystem is high enough that premises expire

A resurvey against a repo-scoped kill hits the same wall with different words. Say so and move on.

### The kill ledger — mandatory on any NO SURVIVOR

Write `<run>/kill-ledger.md`, one row per candidate: `card | gate | fact-or-reading | evidence
line | reversible-if`. `reversible-if` names the rule or measurement that would have to change.
`GATE 0` changed once tonight and nothing recorded which kills it invalidated; two kills turned
out to rest on a broken probe and were only caught because a reviewer re-read them by hand.

## KILL AUDIT — no GATE 5 kill is final until this runs

`STATUS: LIVE`. On 2026-09-22 four repos were declared dead. Reviewers later found **two of the
four kills invalid**, both from the same defect: the probe never stated the card's constraint.
The reviewers caught it — after the runs had ended and the repos were written off. Make it a
gate, not a postmortem. It is cheap: the kill is already written up.

**Dispatch Codex with one instruction: argue this candidate is ALIVE.** Give it the card, the
probe prompts, the raw probe outputs, and the kill write-up. It must answer all six:

| # | Question | The case it catches |
|---|---|---|
| 1 | Does each probe prompt state the card's `CONSTRAINT`? | frostdb C1, santuario C3 |
| 2 | Does the assertion actually **observe** the discriminating behaviour, or a proxy? | frostdb's never observed serialization completion |
| 3 | Was the DESIRED/NON-DESIRED mapping applied in the declared direction? | frostdb scored a strong fork as a kill |
| 4 | Was GATE 4 run in its A3-LOCAL form, or waived? | waived on every run tonight |
| 5 | Would a **different constraint on the same surface** survive? | the surface may be live even if this card is not |
| 6 | Is the kill a **fact** (merged PR, importable reference, already-true premise) or a **convergence reading**? | facts stand; readings need 1–3 re-checked |

**A kill that rests only on a convergence reading, with any of 1–4 unmet, is NOT a kill.** Fix
the instrument and re-measure. Record the audit verdict in the handoff next to the kill.

**Steelman before you kill.** One sentence: the strongest version of this candidate, and whether
a different constraint on the same surface survives. If you cannot write it, you have not
understood the candidate well enough to reject it.

## THE GATE CHECKLIST

Per candidate card, in order. Tick with evidence; waive with a reason. A card failing any line is **killed and reported**, not repaired here.

| # | Step | Proof |
|---|---|---|
| 1 | Read `HANDOFF A2`; list the cards and their residual risks | card paths + one-line premise each |
| 2 | **GATE 0** namability | the written-out graded assertion, the token inventory, IN-BASE/COINED per token with its `grep` |
| 3 | **GATE 1** three pre-filters + fork-collapse test | two implementation families named; a grader sketch with no data-structure name; step 1's signature vs step 2's requirement; the two sentences side by side |
| 4 | **GATE 1** constraint classification | step-2 constraint quoted and labelled cost or behavioural |
| 5 | **GATE 2** hollow premise | the code path read (`file:line`) **and** the executed reproduction at `base_commit`, with output |
| 6 | **GATE 3** disclosure | 4–6 queries with `total_count`; `--comments` output per touched issue; roadmap/feature sweep if a feature; candidate-symbol peer sweep per `A1` §3 |
| 7 | **GATE 4** outcome-variance probe | 5 impl outputs, each graded against your assertion; the n/5 figure |
| 8 | **GATE 5** fork probe, ×2 phrasings, on the constraint-stating step | 10 prior outputs, the path each took, n/5 per phrasing |
| 9 | **GATE 6** Tier-0 | one line per filter with its verdict |
| 10 | **GATE 7** cascade | HEAD-counterfactual answer, parallel-API answer, ladder rung if it falls back to single-turn |
| 11 | **GATE 8** score | the 8-axis table from a model that did not propose the card, each score justified |
| 12 | Read per-axis, not the total | the three veto-axis values stated explicitly |
| 13 | Rank survivors / declare no survivor | one line per card: survived, or the killing gate with its evidence |
| 14 | Emit the HANDOFF | block below, `CHECKLIST: n of m` filled in |

```
HANDOFF A3
  EXIT:      <survivor(s) with the MEASURED fork figure and the measured outcome-variance figure —
             or "no survivor" with the killing gate per card. EXIT: NOT MET if neither is established>
  CHECKLIST: <n of m ticked; every waived line with its reason>
  ARTIFACTS: <probe outputs, the gate table, the score table, the kill log>
  FACTS:     per survivor — base_commit sha; the existing public entry point the graded assertion runs
             through and the proof every asserted token is IN-BASE; the outcome-variance n/5 and the
             exact assertion used to grade it; which assertion cluster carries the difficulty; the
             fork probe n/5 per phrasing and which step was probed; the three veto-axis scores; the
             cascade evidence (HEAD counterfactual, parallel-API); the step-2 constraint sentence,
             classified behavioural
  OPEN:      anything unmeasured and why. Any contract-prose question — Owner: Avocado/Vidit,
             never this act's owners (→ 00-ROUTER.md §5).
  NEXT:      B-build/B1-scaffold.md — or back to A-source/A2-idea-generate.md if no survivor
```

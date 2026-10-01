# A3 — IDEA GATE

| | |
|---|---|
| **Owner** | Claude (verification, probes, novelty sweeps) + Codex (scoring, step breakdown). Neither may write contract prose — `→ 00-ROUTER.md` §5 |
| **Input** | the candidate cards from `HANDOFF A2` |
| **Output** | survivors, ranked — or an evidenced **"no survivor"** |
| **Exit** | **≥1 survivor that clears every FACTUAL veto and carries a credible branch count ≥3**, or an honest "no survivor" naming the gate that killed each card. A fork reading is recorded, never decisive. |

You measure claims; you do not generate replacements. A candidate that dies here goes back to `A2`, it is not repaired in place. Claude-as-analyst was the wave-1 error source (repo pre-screen wrong on 2 of 4, a false "standards-pinned has no fork" rule, a dedup method returning 0 on a repo with 11 peer tasks); Claude-as-verifier held up across four spot-checks with zero inflated. **A well-evidenced kill is a good outcome** — three of four A/B repos returned zero survivors and those were the correct answers.

## 0a. POSTURE — this act exists to disqualify, not to predict

`STATUS: LIVE`, 2026-09-23. **Changed deliberately after two nights of ~17 kills and zero tasks.**

This act used to try to predict which candidates would land in band. It cannot, and neither can
anything else we own:

- **55.9%** of all tasks land in band (n=23,524). **5.8%** come back 5/5, and even those are
  accepted **45.5%** of the time. 0/5 is accepted **81.2%**.
- Nothing about a contract predicts its band — a step avocado solves 5/5 and one it solves 0/5
  have statistically identical prompts across 1,585 step observations.
- Even a perfectly tuned task at true p=0.40 lands in band only **83.5%** of the time.

**We were rejecting ~95% of candidates to avoid a 5.8% outcome.** That trade is backwards.

So the job here is to **disqualify what is genuinely dead** — recall-solvable, already fixed,
ungradeable, unnamable — and then get out of the way. Everything that survives goes to `B`.

**The server is a better instrument than any local proxy.** `GATE 4`'s local n=5 said in-band on
`connect-go`; the server said 5/5. We built `C1`–`C6` to repair tasks from real trial data and have
never once reached them, because everything died here. A 5/5 return is a `C3` hardening round on a
task that exists, with real evidence attached — strictly better than a line in the kill ledger.

**Bias toward building.** When a candidate clears the factual vetoes and you are unsure, build it.

**What you are aiming at is the quality ladder** (`00-ROUTER.md` §3b). The floor is **L1** — every
validation passing except calibration, plus an agentic review of `GOOD`. Calibration is the rung
above it. So a candidate that will plainly grade cleanly and review well is worth more than one
that argues better on paper, and the gates here exist to stop you building something that cannot
reach L1 — not to predict which rung it lands on.

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

**Vetoes vs recorded numbers.** Only the FACTUAL gates kill. The fork-proxy gates are measured,
recorded in the handoff, and do not decide — see GATE 5.

| Gate | Kills | Cost | Run at | status |
|---|---|---|---|---|
| **0** | grader needs a name absent at `base_commit` | free | 1st | **VETO** |
| **1** | pre-filter 4 (difference unobservable through the grader's interface) | free | 2nd | **VETO** — pre-filters 1–3 are recorded only |
| **2** | the premise is already true at HEAD | one file read — **a BUILD in compiled languages** | 3rd | **VETO** |
| **3** | the cause or remedy is public | a few searches | 4th | **VETO** |
| **4** | no outcome variance | 5 calls | **7th** | recorded — local n=5 mispredicted the server once |
| **5** | the model already prefers the desired path | 10 calls | **8th** | **RECORDED ONLY — no longer a veto** |
| **6** | ungradeable / nondeterministic / hangs / trivial seam | free | **5th** | **VETO** |
| **7** | the cascade is decorative | free | **6th** | recorded — restructure, do not kill |
| **8** | scoring and ranking — **survivors only** | a Codex pass | last | advisory |

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
   that works at all. Against that, the old corpus figure of 1 passed / 13 is REFUTED — at n=647 it is **52.1%**. The odds are bad; they are not zero.

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

> ### ⚠ THE POSTURE BELOW IS CONTRADICTED BY OUR OWN ACCEPTED TASKS. `STATUS: LIVE`, 2026-09-30.
>
> This gate says coining a token makes a candidate almost-never-buildable, and steers toward
> *"existing behaviour becomes correct, observable or safe"* — a defect framing. **Two of our
> three accepted multi-turn tasks coin an API and name it in the contract.**
>
> `django-model-utils` step 1: *"Watched relation names are supplied with
> `FieldTracker(related=[...])` ... e.g. `FieldTracker(related=['author'])`"* — a coined keyword
> argument, named, with a literal usage example.
>
> `open62541` step 1 puts the whole signature in a fenced block:
> `UA_StatusCode UA_EXPORT UA_NumericRange_print(const UA_NumericRange *range, UA_String *out);`
>
> Both accepted. And the org's highest-throughput author states the same policy outright:
> *exact public API names, signatures, return shapes and exception types are required contract
> details, not implementation details* — across a portfolio that is 47 of 49 `extend_behavior`.
>
> **Re-read the gate's own evidence.** The failure it cites is
> *silent-contract-plus-pinning-test* — tests pin a token the contract does **not** name. The
> remedy for that is to **name the token**. This gate instead banned the category that produces
> coined tokens at all, which is a larger claim than the evidence supports and it is the reason
> our ideation became defect-only.
>
> **Working rule until Vidit rules otherwise:** coining a token is not a veto. It is an
> obligation — `B2` names every coined token in the contract, `B3` proves the grader accepts
> nothing broader. That is the existing override, and it should be the default path rather than
> a debt. What stays vetoed is the real failure: a token the tests pin and the contract is
> silent about.
>
> This is not an argument reopening a measured rule — it is two of our own accepted tasks doing
> the thing the gate forbids. Record the next coined-token candidate's outcome either way.

Two consequences the gate as originally written accepted: it makes most `expose_interface` tasks unwritable (**52.1% at n=647 — ordinary**, so this trade is NOT obviously worth taking — prefer candidates where existing behaviour becomes correct, observable or safe); and it **subsumes the coined-observability auto-reject** (`→ A2-idea-generate.md §6`), since a ledger whose invented field names carry the contract fails at step 3 every time. What the contract may still state later is `B2`'s business, not this gate's.

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

> ### Disclosure is not one thing. Split it by WHAT is disclosed.
>
> `STATUS: LIVE`, 2026-09-23. A *diagnosed but unfixed* bug — the `semantic_bugs` shape — is **by
> definition** an open issue with a public thread. Read literally, GATE 3 kills every SEARCH
> candidate that exists, which made the SEARCH mandate self-contradictory.
>
> | what the public thread contains | verdict |
> |---|---|
> | the **symptom** — a user reporting wrong output, a failing case, a confusing behaviour | **allowed.** The symptom is what your contract states anyway. |
> | the **cause** — a comment or PR naming the faulty line, the mechanism, or the metadata the fix needs | **KILL.** The search is over before the solver starts. |
> | the **remedy** — a merged or open PR implementing it | **KILL**, unconditionally. |
>
> Apply the strict reading when in doubt, and record which reading you used. Every kill made under
> this split on 2026-09-23 survives *both* readings, so the split has not yet been load-bearing —
> but it is what makes the SEARCH lane coherent.
>
> **Measure the supply before you survey.** Two `gh api` calls give the fraction of open bug issues
> that are still broken at base *and* carry no public cause or remedy:
>
> | repo | undisclosed bug supply |
> |---|---|
> | **concourse/concourse** | **12 of 17 — 71%** |
> | cloudnative-pg | 49 of 75 |
> | crossplane | 13 of 29 |
> | kustomize | 19 of 42 — and 8 of the 12 still-broken bugs already carry a PR or root-cause comment |
>
> A repo whose tracker is already mined is a dead SEARCH lane however healthy its issue count looks.

> **Run these four FIRST. Each one killed a candidate on 2026-09-22 that had already cleared
> earlier gates.** `STATUS: LIVE`
>
> ```bash
>   # 1. FUNCTION-scoped history. The file-scoped form returns noise and hides this.
>   git log -L :<func>:<path> --oneline | head -40
>   #    ^ VERIFY THE BINDING. Measured 2026-09-23: the regex form
>   #      `-L '/func.*Name/,...'` silently bound to a 5-line TYPE DECLARATION and
>   #      reported 2 commits for an 11-commit file. That miss is why a run killed a
>   #      candidate on the wrong grounds and never saw merged PR #5892.
>   #      Sanity-check: the span it printed should be the function body, and the
>   #      count should be plausible against `git log --oneline -- <path> | wc -l`.
>   #      Cross-check with `git log -S '<a literal from the function>' --oneline`.
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

> ### CONFLICT — UNRESOLVED: "merged PR touching the surface" vs the disclosure split. Owner: human.
>
> `STATUS: LIVE`, 2026-09-30. The hard-kill list below and the disclosure split above give
> **opposite answers** on the same candidate, and until this run nothing had forced the question.
>
> Measured on `belaban/JGroups`. `TPConfig.setBundler` stops the incumbent bundler *before* the
> candidate's `start()` can throw, so a failed candidate leaves a stopped bundler installed and
> the transport's data plane dead. Reproduced by execution, not grep. The function carries two
> public PRs in 18 months — `#807` (CLOSED, landed as `5658b5e7f`) and `#860` (CLOSED, one comment
> *"Applied"*, landed as `f190fddab`, **whose diff is byte-equal to the current HEAD body**).
>
> | reading | verdict | basis |
> |---|---|---|
> | the hard-kill list: *"any merged public PR touching the surface"* | **KILL** | an applied closed PR is a merged PR in substance, and it touches the exact function |
> | the disclosure split: symptom allowed / **cause** kills / **remedy** kills | **NOT a kill** | both commit bodies were read in full. `5658b5e7f`: *"allows setting the bundler instance … Previously it had to be set by class name or it would be overwritten during init."* `f190fddab`: *"allows setting the bundler instance on TP before it is initialized/channel is created."* Neither mentions preparation failure, rollback, a stopped incumbent, or destruction. They **introduced and refactored the hazardous shape without publishing its cause or remedy.** |
>
> An adversarial audit briefed to argue the candidate ALIVE reached the same split independently
> and said so in those words.
>
> **Operationally until a human resolves it: apply the strict reading, and record BOTH.** The
> split is the newer LIVE rule and exists precisely because the blanket form *"kills every SEARCH
> candidate that exists"* — but the blanket form is what is written in the kill list, and this
> act's standing instruction is to apply the strict reading when in doubt. Whichever you use,
> write both verdicts into the handoff with the commit bodies quoted, so the decision is
> reviewable rather than a judgement call buried in a kill line.

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
>    **The affordability problem, and the one legal relaxation.** `STATUS: LIVE`, raised by two
>    runs. For a **net-new-capability** card the hand-written DESIRED implementation *is the task* —
>    demanding it before `A3` clears makes the gate cost more than the build, which is why it was
>    waived on every prior run rather than run badly.
>
>    For net-new cards only, substitute a **DESIRED stand-in**: not a full implementation, but the
>    smallest patch that makes the sketch pass, written against one class from the contract-domain
>    enumeration rather than all of them. The base and negative-control validations stay mandatory
>    and unrelaxed — they are cheap, and the negative control is the one that catches a blind
>    sketch. Record in the handoff that you used a stand-in and which class it covered.
>
>    This relaxation does **not** extend to bug-fix or existing-behaviour cards. There the golden
>    is small and a real DESIRED implementation is affordable, so write it.
>
>    ### ⚠ THE COLD PROBE REPRODUCES OPUS, NOT AVOCADO
>
>    `STATUS: LIVE`, measured 2026-09-24 on `concourse`. This is why GATE 4 keeps mispredicting.
>
>    The probe predicted **avocado 3/5**; the server returned **avocado 5/5**. But the probe was
>    not wrong about the *problem* — it named the two discriminating branches correctly, and those
>    are exactly the two **opus** lost on (`opus 0/5`). Read that again: **the n=5 cold
>    implementations behaved like opus, not like avocado.**
>
>    The behavioural split was clean and total:
>
>    | | opus (0/5) | avocado (5/5) |
>    |---|---|---|
>    | edited `atc/exec/step.go` to widen the interface | **5 of 5** | **0 of 5** |
>    | modified a restored upstream `_test.go` | **5 of 5** | **0 of 5** |
>    | approach | asked the injected state to mint a scope → nil deref on a bare fake | self-contained wrapper with nil guards |
>
>    **So a local n=5 measures the difficulty of your task for whatever model generated the
>    implementations — and that is not the model the gate scores.** A 3/5 local reading is not a
>    prediction of the avocado band; it is a statement about the probe generator.
>
>    Two consequences:
>
>    1. **Never report a GATE 4 number as a predicted avocado band.** Report it as "n of 5 cold
>       implementations failed", and say which generator produced them.
>    2. This is the third independent reason **branch count beats GATE 4** (`B3` §④) — branch count
>       is a property of the graded set and does not depend on who wrote the code you tested it on.
>
>    All three are required. On frostdb the negative control was decisive: the old buffered
>    implementation showed "sink b reached the end of its copy, 2,739,919 bytes, while sink a
>    had consumed nothing."

> 4. Generate n=5 cold implementations from `CONSTRAINT` alone and run the sketch against them.
> 5. Want **1–3 of 5**. 0/5 or 5/5 kills the candidate — *and 5/5 after step 3 passed is a real
>    kill, unlike a GATE 5 convergence reading.*
>
>    ### ⚠ THE PROBE MUST STATE EVERY CLAUSE THE SKETCH GRADES. A "STATED DELTA" IS A KILL.
>
>    `STATUS: LIVE`, measured 2026-09-30 on `mina-sshd`, n=10 paired implementations.
>
>    Step 4 says "from `CONSTRAINT` alone", and a card author who leaves the discriminating clause
>    out of `CONSTRAINT` gets an **in-band reading for a task that will come back 5/5.** That is
>    not a hypothetical:
>
>    | the discriminating clause | probe result |
>    |---|---|
>    | **unstated** (graded, not said) | **2 of 5 pass — in band** |
>    | **stated**, same clause, same sketch, same generator | **5 of 5 pass** |
>
>    The clause was "a member that can carry a failure must end the close carrying the close
>    failure". Unstated, five implementations split 3/2 on capability precedence entirely
>    unprompted. Stated, all five got it. `instruction.md` **must** state it — a silent spec with a
>    pinning test is the configuration that produced `BAD_GRADING_WRONG` on 4 of 4 peer tasks — so
>    the in-band reading was measuring a contract that can never be shipped.
>
>    **So:**
>
>    - The probe prompt must contain **every clause the sketch asserts on**, worded as
>      `instruction.md` will word it. Diff the two before you run, and paste the diff.
>    - When a candidate reads in band, **re-run it once with every graded clause stated.** The
>      delta is the diagnostic, not the first number.
>    - **A clause that discriminates only while unstated is not a fork. It kills the SURFACE, not
>      just the card** — no re-cut of that surface recovers it, because every re-cut has to state
>      the thing that was doing the work.
>    - This is the same mechanism as `reference/R6-fork-patterns.md` §P6's retracted
>      "cascade probe" rule (0/10 volunteered, 10/10 executed once told). That paragraph is about
>      cascades; this one is about the primary gate, and the gate never inherited it.
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
| **SEARCH** — must FIND the defect/invariant/call site before acting | finding is stochastic | `semantic_bugs` **49.6%, n=268**; `expose_interface` **52.1%, n=647** |
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

> ### DECIDED 2026-09-23 — this gate no longer kills. Record the number and move on.
>
> `STATUS: LIVE`. Three independent lines said it does not predict outcome, and it had cost ~17
> candidates across two nights for zero built tasks:
>
> 1. **Population, n=23,524** — nothing about a contract predicts its band; a step avocado solves
>    5/5 and one it solves 0/5 have statistically identical prompts (n=1,585 step observations).
> 2. **Trial forensics, 51 failing trials across 19 arms** — every failure is a QUALITY failure:
>    a missing member of an enumerable set, a missed interaction, a placement error. DESIGN
>    divergence does not appear as a primary label.
> 3. **One candidate dissected** — *"its variance carrier was QUALITY (completeness of a reset),
>    not DESIGN — and the fork axis only measures DESIGN, so that premise shape cannot clear
>    GATE 5 by construction."* The gate is not mismeasuring QUALITY premises; it is blind to them,
>    and will reject every one it is shown.
>
> **The one case where fork-1 correctly predicted 5/5 (`connect-go`) also had branch count ~1**, so
> `B3`'s branch count caught it too. Branch count is right where this gate is right, and right
> where this gate is structurally blind. It dominates.
>
> **So: run the probe, record the number in the handoff, and do not kill on it.** The number still
> earns its keep as paired data — if fork and branch count ever disagree on a task that reaches the
> server, that is the observation which would reopen this.
>
> **What decides instead:** `B-build/B3-grader.md` §④ BRANCH COUNT ≥3, and two steps with step 1
> carrying real difficulty (`A2` §3b).

## GATE 6 — Tier-0 structural gates

Each is a fail and each is decidable without a build. `STATUS: LIVE (PEER)`

| Filter | Test |
|---|---|
| **Seam test** [R03] | Step-1 gold must **fail** step-2's tests. If step 1 already states what step 2 asserts, there is no second turn |
| **Step-1 observability** [R01] | Step 1 must produce behaviour assertable from outside; grading private state rejects valid alternative designs |
| **Determinism scan** [R09] | No wall clock, concurrency race, benchmark threshold or NP-hard "minimum" in any contract. Verify the card's named injection point exists |
| **Mechanism-naming scan** [R01+R04] | Neither step may name a **file, algorithm, data structure or language construct** — implementation, fails R04. Interface naming is settled by GATE 0: a surviving candidate needs no new name, so there is nothing to pin |
| **Never grade against a library export** [R05] | If the reference answer is callable from inside the solution — matching a public export's output exactly — the grader leaks the solution |
| **Anti-overcorrection** [N04] | **Under ~20 lines, or composes two shipped functions → discard.** Verification alone selects trivia: absent *and* substantial. Target 80–150 net lines across 2–4 files — **and apply it PER STEP.** A card with a substantial step 1 and a step 2 that is one guard, one forwarded call or one interface method that does not exist at `base_commit` is a single-turn candidate, not a multi-turn one. Measured 2026-09-30: this row, applied per step, was the binding kill on an entire repo — every remaining defect in the target domain was individually worth fixing and individually too small to be half a task. → `A2` §6a sizes it at survey time so it does not cost a full gate pass |
| **Normaliser consistency** [R08] | If graded entries are read through a normaliser (`to_h`, a serializer, an accessor), **every** assertion must go through it; one assertion reaching past it re-narrows the contract |

> **A wrong answer that HANGS is ungradeable, and this gate had no row for it.**
> `STATUS: LIVE`, 2026-09-23. A candidate was killed here because the plausible wrong
> implementation does not return a wrong *value* — it **deadlocks**. A grader can assert on a
> wrong value; a hang produces a timeout, which reads as infrastructure, not as a failed
> assertion, and it burns the trial's whole budget. Add the question: *what does the plausible
> wrong implementation DO — return something wrong, or fail to return?* If the latter, kill it.

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

**Threshold: build only at ≥28/40, and never with Observability ≤2 or Realism/fit ≤2.**

> ### The Fork veto is CONDITIONAL on GATE 4, and GATE 4 wins. `STATUS: LIVE`
>
> This act called GATE 4 **PRIMARY** and GATE 5 **SECONDARY**, then gave the secondary gate an
> absolute veto over the primary one and never said which won. A run hit the contradiction
> head-on and had to improvise; that was a defect, not its error.
>
> ### FALSIFIED ON ITS FIRST TEST — 2026-09-23. Treat the veto as ABSOLUTE again.
>
> `connect-go-trailing-metadata-parity` was built on this exception and **failed**:
> `GATE 5` measured fork 1 and Codex's `GATE 8` said *"Would I build it? No."*;
> `GATE 4` A3-LOCAL measured **3 of 5, in band**, so under the rule below it was built.
> The server returned **`avocado 1|1` — 5 of 5 on step 1, over the ceiling** — plus
> `BAD_GRADING_WEAK`. **Codex was right and the exception was wrong.**
>
> The single paired observation we have says a local `GATE 4` 3/5 does **not** predict the
> server's band on a fork-1 candidate. n=1, but it is the only paired data point, and it went
> against the rule. So:
>
> ### ⚠ THIS GATE AND `ledger/RULES.md` GIVE OPPOSITE ANSWERS. `Owner: human`, 2026-09-30.
>
> `RULES.md` records **S-004 "fork ≤2 is an absolute veto" as SUPERSEDED by R-005**
> (branch count ≥3), on three independent lines — population, 51-trial forensics, one
> dissection — and notes the veto **cost ~17 candidates**. This gate still states the veto as
> live. Both are `STATUS: LIVE` in their own file.
>
> Neither has been flipped, deliberately. The reopening condition below demands *paired
> local-vs-server data on ≥3 fork-1 candidates, not another argument*, and `RULES.md`'s
> supersession is argument-plus-forensics, not paired data. `S-005` exists because this exact
> rule was already flipped twice by reasoning and was wrong both times.
>
> **Until Vidit rules:** run **both**. Kill on fork ≤2 *and* record what branch count says. If
> they disagree, that disagreement is the paired datum the reopening condition is asking for —
> write it to `ledger/RUNS.md` rather than picking a side. A second run has now hit this
> head-on; the cost of leaving it is real candidates.
>
> **Fork ≤2 is an absolute veto. Do not build.** The text below is retained only so the
> reasoning is legible and so a future paired measurement can reopen it deliberately rather
> than by someone re-deriving the same argument from scratch.
>
> To reopen it you need **paired local-vs-server data on ≥3 fork-1 candidates**, not another
> argument. Record any such pair in `ledger/RUNS.md`.
>
> ~~Fork strength ≤2 is a veto ONLY when GATE 4 was not measured in band.~~ `STATUS: SUPERSEDED`
>
> | Fork (GATE 5) | Outcome variance (GATE 4 A3-LOCAL) | Verdict |
> |---|---|---|
> | any | **not measured / waived** | Fork ≤2 **vetoes**. The proxy is all you have. |
> | ≤2 | **1–3 of 5, validated three ways** | **BUILD.** Record it as a quality-variance task and name the discriminator. |
> | ≥4 | 0/5 or 5/5 | **DEAD** — a strong fork does not rescue zero outcome variance (frostdb C1: 9/10 fork, 0/5 outcome). |
>
> **Why.** The fork veto is a *proxy* for "this will one-shot and come back 5/5". GATE 4 measures
> that property **directly, on real patches** rather than on three-sentence plans. When the proxy
> and the direct measurement disagree, the measurement wins — that is what PRIMARY means.
>
> This act's own variance taxonomy already permits it: of SEARCH, QUALITY and DESIGN, **QUALITY —
> "the artifact exists either way; the standard varies"** — is a legitimate carrier. A fork-1
> candidate where 2 of 5 competent implementations miss a required behaviour is a *quality*-variance
> task, not a broken one. The Fork axis only measures DESIGN divergence.
>
> **Two obligations when you build on this exception:**
> 1. **Name the discriminator in one sentence** — the specific behaviour the failing implementations
>    missed. If you cannot name it, you have not measured outcome variance, you have measured noise.
> 2. **Record it in the handoff as a fork-1 build**, so that if the server returns 4/5 or 5/5 the
>    repair is `C3` hardening and nobody re-litigates the decision.

Remaining veto axes: Score Fork from GATE 5's measurement (≥4/5 wrong path = 5; ≥4/5 desired path = 1, do not build; even split = 3). Observability is a veto because it eliminated half the algorithm catalogue — asymptotically better but behaviourally identical cannot be graded at all. Realism/fit exists because the rubric contradicted the library: a bc-java candidate scored **29** proposing a write-ahead log inside `bcmls`, a protocol codec **with no I/O layer at all**. Score Harness-ability from the GRADING path → `A1-repo-screen.md` §8.

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

> ### ⚠ A Q5 "ALIVE" ANSWER IS ITSELF A PROBE RESULT AND MUST BE RE-MEASURED WITH THE CLAUSE STATED
>
> `STATUS: LIVE`, measured 2026-09-30 on `authelia/authelia` `internal/authorization`.
>
> The audit is asked to find *"a different constraint on the same surface"*, so it goes looking
> for divergence among the five implementations — and the easiest divergence to find is always
> on something the probe **did not state**, because that is precisely where the implementations
> were free. Nothing in this section told it, or its reader, to re-measure.
>
> Measured: a card read **5/5** on eight stated clauses. The audit returned **ALIVE**, citing a
> genuine **2/5** split on the per-rule report (`!results[0].MatchQuery`, `!results[0].IsMatch()`,
> `results[1].Skipped` — two of five passing). The split was real and was reproduced
> independently by a differential probe. **The clause was unstated.** Stating it and re-running
> n=5 returned **5/5**.
>
> That is exactly the `GATE 4` mina-sshd mechanism, arriving through the audit instead of
> through the card author. **So:**
>
> - A Q5 answer of ALIVE is a **hypothesis**, never a resurrection. It names a candidate clause.
> - Before the card re-enters, **state that clause as `instruction.md` would state it and re-run
>   GATE 4.** The second number decides; the audit's number never does.
> - If the audit's divergence is on a surface the probe prompt did not mention at all, expect
>   collapse — and if it collapses, the finding is upgraded: the **surface** is dead, not the card.
> - Brief the auditor with this paragraph, so its Q5 answer arrives labelled as a hypothesis.
>
> Without this, the audit converts a correct kill into a build. One run was one dispatch away
> from scaffolding on a card that had measured 5/5 twice.

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

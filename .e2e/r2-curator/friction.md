# friction.md — r2-curator (engineer half)

Appended as I go. One entry per place the playbook was unclear, missing, wrong,
self-contradictory, or slower than it should have been.

---

## F1 — `A2-idea-generate.md` §8 line 1 says "Read `HANDOFF A1`". There is no `HANDOFF A1`.

**File:** `A-source/A2-idea-generate.md:272`
> `| 1 | Read HANDOFF A1 | LOC, subsystem count, HEAD sha and the named existing entry point copied into your run notes. Do not re-measure |`

I start at `A2` by instruction, and `A1` was run by a different agent in a different session
that produced `runs/shortlist-proto.md`, not a `HANDOFF A1` block. The shortlist entry has LOC,
subsystem count and the grading path, but **not the HEAD sha** — which `A2`'s own FACTS block
(`A2:292`) requires and which `A3`'s GATE 0 needs to classify tokens IN-BASE vs COINED.

I had to clone and derive it myself (`88dee99a85921bd0f20955e1d7efbaf896fc17f3`). Cheap here
(~40 s) but it is a real gap: the playbook assumes `A1`'s output format and the actual upstream
artefact is a different format. Either `A1` should be specified to emit the HANDOFF block into
the shortlist, or `A2` step 1 should say "read `HANDOFF A1` **or the shortlist entry**, and
derive HEAD yourself if absent".

**Cost:** ~2 min.

---

## F2 — Java/Maven recipe is NOT in the playbook. It is in another pair's friction log.

**File:** nowhere in `~/swebench-playbook/`. The working recipe lives in
`.e2e/pair-santuario/friction.md:12-61`.

`A1-repo-screen.md` owns "harness timing" and `B4-solution-env.md` owns the Dockerfile, but
neither carries the host-specific facts that make a Java build work here:

- GCS mirror `https://maven-central.storage-download.googleapis.com/maven2` as `<mirrorOf>central</mirrorOf>`
- `--network=host` mandatory on `docker run`, not only `docker build`
- mirror **and** both fwdproxy stanzas must be in the **same** `settings.xml`, because
  `~/.m2/settings.xml` on this host ships proxies and no mirror

I only knew this because my dispatch brief quoted it. A pair that read only the playbook would
have rediscovered it, and the santuario log says that costs ~25 min. This belongs in
`reference/R3-landmines.md` (it is exactly a packaging trap) with a per-language section.

Verified working on curator, cold, this run: `BUILD SUCCESS`, all 13 modules, artifacts pulled
through `gcs-central`. Curator additionally needs `rm .mvn/extensions.xml` (Develocity extension
is unresolvable) — that one IS in the shortlist entry.

**Cost:** 0 min for me, ~25 min for anyone without the brief.

---

## F3 — `A3` GATE 3 fires far too late for a repo whose open issues are imported JIRA tickets.

**File:** `A-source/A3-idea-gate.md:116-141` (GATE 3 sits after GATE 0/1/2).

Gate order is justified in `A3:14` as an economy argument — free gates first. That economy
assumes disclosure checking is expensive. On `apache/curator` it is nearly free and it is the
gate that actually bites, because the repo's 121 open issues are **bulk-imported Apache JIRA
tickets**, each carrying a full root-cause diagnosis and frequently a proposed patch in the
comments.

Measured this run: my strongest self-generated candidate (`ServiceDiscoveryImpl.reRegisterServices()`
aborting the whole fan-out on the first per-instance failure, and running on the
`ConnectionStateManager` event thread) was killed outright by **open issue #840 / CURATOR-320**,
whose body states the diagnosis verbatim and whose comments contain a **posted diff** introducing
`reRegisterExecutor` / `reRegisterFuture` / `reRegisterRetryCount` — i.e. exactly the remedy — with
the maintainer replying "can you please create a PR with your change?".

One `gh api repos/apache/curator/issues?state=open` call (2 s, 121 rows) would have pre-empted
~25 min of my reading. **Recommendation:** add to `A2` §8 as a step between 5 and 6 — "dump the
full open-issue title list once, per repo, before writing any card" — so that ideation is steered
away from disclosed areas rather than gated after the fact. The current order pays full ideation
cost on candidates that were dead before they were written.

**Cost:** ~25 min.

---

## F4 — The round-2 dispatch brief and the repo evidence disagree about what "121 open issues" means.

Not a playbook-file defect, but a live mis-cue worth recording.

My brief says: *"Also note 121 open issues is a real defect supply — unlike round 1's frostdb,
which had 8 and yielded nothing."* `A1-repo-screen.md` likewise treats issue density as a
positive screening signal.

On this repo the sign is **inverted**. The 121 issues are not a supply of un-diagnosed defects;
they are a supply of *publicly diagnosed* ones, many with patches inline. High issue density on a
JIRA-imported Apache repo is a **disclosure hazard**, not a defect supply. Any candidate drawn
from the same subsystem as an open ticket is dead at GATE 3 regardless of whether I found it
independently.

`A1`'s issue-density criterion should distinguish "open issues" from "open issues with
maintainer-grade diagnoses attached", because they point in opposite directions.

**Cost:** it shaped where I looked first, so folded into F3's 25 min.

---
## F5 — `B2-contract.md` is missing two rules the source pipeline had (told to me, logged as instructed)

**File:** `B-build/B2-contract.md`.

My dispatch brief states that `B2` lacks **"step 2's spec must be self-contained"** and
**"no 'deferred to step 2' language in step 1"**, and instructs me to apply both when briefing
Avocado and to log the gap. I confirm the gap by inspection: neither rule appears in `B2`.

I never reached `B2` — no card survived `A3` — so I applied neither. Logging it so the finding is
not lost with my run, and noting that the instruction to "apply both when you brief Avocado" is
unreachable for any pair that dies in `A`. If these two rules matter (and the second one especially
sounds like it prevents a real cascade defect), they belong in `B2` as text, not in a per-run brief.

**Cost:** 0 min. Recorded for completeness.

---

## F6 — `A3` GATE 5 rule 3 decides my case, but its stated rationale does not cover it

**File:** `A-source/A3-idea-gate.md:202`.

> **"0 of n volunteered it" measures NOVELTY, not fork and not cascade.** … Since the instruction
> MUST state the step-2 constraint, **probe step 2 WITH the constraint stated; ≥4/5 correct = dead.**

My two phrasings disagreed, sharply and reproducibly:

| phrasing | result |
|---|---|
| constraint stated | **5/5 produced the intended design** |
| constraint withheld | **5/5 produced a design that regresses behaviour holding at HEAD**, 2/5 knowingly |

The rule resolves this — the constraint-stated number decides, so the candidate is dead — and I
followed it. But the rule's *justification* is "the instruction MUST state the step-2 constraint",
and that premise is false for the shape I hit. My second requirement was **not a new requirement**:
it is behaviour that holds at `base_commit` (I measured it, `REPRO-I`) and would live in
`pass_to_pass`. Tasks pin existing behaviour in `p2p` without the instruction enumerating it, all
the time — that is not the "silent spec + pinning test" configuration `GATE 0` forbids, which is
about *`fail_to_pass`* pinning an unstated new symbol.

So there is a genuine third case the rule does not name, and an agent reading it literally can
reach the right verdict for a reason that does not apply, or — worse — talk itself past the rule
on the grounds that the premise fails. I nearly did the latter. What actually settled it for me was
an argument the playbook does **not** contain:

> If the contract states the second requirement → 5/5. If it withholds it and the grader pins it →
> 0/5. One sentence moves the task between the two extremes with **no gradient**. That is `A3`
> GATE 4's own "5/5 → 0/5 with nothing in between" deterministic-task signature, arriving *before*
> the build instead of after it.

**Suggested addition to GATE 5**, phrased as a test rather than a rule: *when the two phrasings
disagree, do not pick a number — ask what the task reads at each extreme. If the honest answer is
5/5 one way and 0/5 the other, the candidate is bimodal on a prompt sentence and there is no
gradient to calibrate into.* That is a stronger and more general kill than the volunteered/executed
distinction, and it would have reached the same verdict without relying on a premise that was false
here.

**Cost:** ~15 min of genuinely uncertain reasoning, which is the expensive kind.

---

## F7 — `A3`'s gate ORDER made me pay for GATE 2 on a candidate GATE 5 killed

**File:** `A-source/A3-idea-gate.md:14-26` (the gate-order table and its economy argument).

The order is 0 → 1 → 2 → 3 → 4 → 5, justified as free-gates-first. I followed it: GATE 2 on C1
meant writing a 140-line JUnit reproduction harness, building it in Docker and reading the output.
Roughly 12 minutes. GATE 5 then killed the candidate in 7 minutes of wall time using 10 calls and
**no Docker at all**.

The stated cost model says GATE 4 is "5 calls, no Docker" and GATE 5 is "10 calls" while GATE 2 is
"one file read". That undercounts GATE 2 badly: the gate's own text is emphatic that **grep is not
reproduction** — *"Execute at `base_commit` … bug-shaped: run it and see the failure"* — and
executing at `base_commit` on a compiled language means a build. On Java that is minutes, not a
file read. The cost column is written for interpreted languages.

The gates also answer questions of very different value. GATE 2 asks *is the premise real* — and
mine was, spectacularly. GATE 5 asks *is it worth building* — and it was not. Asking the cheap
disqualifying question after the expensive confirming one is backwards whenever the expensive one
requires a toolchain.

**Suggested fix:** make the cost column language-conditional, and state that on any compiled
language GATE 5 (10 calls, no build) should run **before** GATE 2 (which needs a build). My own
numbers this run: GATE 5 ≈ 7 min and killed both candidates; GATE 2 ≈ 12 min and killed neither.

**Cost:** ~12 min, wholly recoverable by reordering.

---

## F8 — `A2` §2's surface→card ratio and the ≥8 dispatch target are in tension, and §8 line 12 makes you report against the wrong one

**File:** `A-source/A2-idea-generate.md:60` vs `A2:7` and `A2:283`.

`A2:7` sets the dispatch target at **≥8 cards**. `A2:60` says to expect **15–20 surfaces to collapse
to 2–4 real candidates** and that "that ratio is the point, not a loss". Those cannot both be met
below ~60k LOC, and `A2:60` says so — *"the ≥8 dispatch target is reachable only on a 60k+ LOC
repo"*. Curator is 53k, i.e. under the line by 12%.

So the honest outcome on this repo is structurally an under-count, and §8 line 12 ("Confirm the
count honestly — cards written vs the ≥8 target") frames it as a shortfall to be explained. It is
not a shortfall; it is the documented expected value for a repo of this size. I produced 24 surfaces
(two surveys × 12) and 2 cards, which is *better* than the stated 15–20 → 2–4 ratio on the surface
side and inside it on the card side.

Minor, but it creates real pressure to backfill at precisely the moment the playbook most wants you
not to (`A2:60`, "**Never backfill** — both source pipelines agree on this and both were burned by
ignoring it"). I did not backfill. Suggest line 12 read "cards written vs the §2 band **for this
repo's LOC**", with the ≥8 figure marked as the 60k+ case.

**Cost:** ~3 min of deciding whether to pad. Zero, if the line is reworded.

---

## F9 — Near-miss on the IRON-CLAD RULE, recorded because the brief asked for it

`PAIR-COMMON.md` asks me to log a near-miss if I catch myself about to route prose into
`instruction.md`. One, and it is worth having on record because of *where* it came from.

Writing card C1, I drafted the two conflicting requirements as two crisp sentences (R-a and R-b in
`artifacts/cards.md`). They are good sentences. They are exactly the sentences a contract would
use, and `A2` §4 requires "the tension — the two things that conflict — in one sentence" as a
**mandatory card field**. So the act-file *requires* me to produce something that is one
copy-paste from being contract prose.

I did not route them anywhere — no card content went to Codex, `mc.sh` was only given probe
prompts, and nothing was written to any `instruction.md` path (none exists; no task dir was
created). But the structural point stands: **`A2`'s mandatory "tension" and "Interface Contract"
fields put a non-Avocado runner one paste away from a violation by design**, and the only thing
between the two is the runner's discipline. `A2:17-19` anticipates this — "cards **stop** at
observable contracts plus the grader API surface" — but a *tension sentence* is neither an
observable contract nor a grader API surface; it is prose about the requirement. That field is on
the wrong side of the line it draws.

Suggest `A2` §4 say the tension field must be written as a **contrast of two observable
behaviours** (which is checkable) rather than as a requirement sentence.

**Cost:** 0 min. The discipline held; the design pressure is the finding.

---

## Waste log

**`WASTE:` ~25 min reading `curator-x-discovery`'s registration path** before dumping the open-issue
list. Killed by #840 in one call once I ran it. Entirely recoverable by F3's suggested reordering.

**`WASTE:` ~12 min on the GATE 2 Docker reproduction** for a candidate GATE 5 then killed for free.
See F7. I would run it again in the same order only on an interpreted language.

**`NOT WASTE, though it looks like it:` the second, non-leading probe.** It cost 5 calls and did
not change the verdict. It is the single most informative measurement in the run — it is what
showed that this repo has **no SEARCH variance** (5/5 found the defect from a bare symptom), which
is a transferable fact about the repo that no `A1` criterion captures and that would have predicted
the whole outcome. `A3` GATE 5 rule 2 requires the second phrasing; on this evidence it should be
promoted from "makes the kill trustworthy" to "measures the repo, not just the candidate".

---

## F10 — the playbook was rewritten UNDER me, mid-act, and my reviewer judged me against the new text

**Files:** `A-source/A3-idea-gate.md` (287 lines when I read it → **399** now), `tools/probe-lint.py`
(did not exist when I probed).

Timeline, from `git log` and `stat`:

| time | event |
|---|---|
| ~16:40 | I read `A3-idea-gate.md`. 287 lines. No GATE 4 "A3-LOCAL" form. No `CONSTRAINT:`/`DESIRED:`/`NON-DESIRED:` requirement. No KILL AUDIT section. No mention of a probe linter. |
| 16:52–17:00 | I ran 15 GATE 5 probes against the rules as I had read them. |
| 17:01 | `tools/probe-lint.py` created. |
| 17:01 | commit `e744c14` — *"A3: fix the instrument that produced two invalid kills"* — rewrites GATE 4 and GATE 5 and adds the KILL AUDIT. |
| ~17:05 | I wrote `handoffs/02-A3.md` declaring a kill, still against the old text. |
| ~17:10 | Reviewer FAILs the act, citing `A3-idea-gate.md:179-199`, `:241-255`, `:286-288` and `tools/probe-lint.py:19-25` — **none of which existed when I executed the act.** |

Every individual finding in that review is *correct against the current file*. I have complied
with all of them rather than argue the timing, and the new rules improved my result materially
(see F11). But three things follow and none are in the playbook:

1. **`00-ROUTER.md` §8 says "No act begins without the prior HANDOFF in hand."** There is no
   corresponding rule pinning the *act-file version* an act executes against. An act-file is as
   much an input as a handoff. Suggest: the HANDOFF block record the act-file's git sha, and a
   reviewer compare against that sha, not against HEAD.
2. **A mid-run rewrite silently invalidates work already done**, and the executor has no signal.
   Nothing told me `A3` had changed; I found out from the review. A one-line note in the run
   directory, or a `reviewer-relay.sh` message, would have cost nothing.
3. **This is a real risk to the comparison being run tonight.** Several pairs are executing the
   same playbook concurrently and are being scored against each other. If `A3` changed at 17:01,
   pairs that reached `A3` before and after that moment ran **different protocols**. Any
   cross-pair comparison of `A3` outcomes is confounded unless the act-file sha is recorded.

**Cost:** ~20 min of rework, all of it worth doing. The finding is the process gap, not the rework.

---

## F11 — the new `probe-lint.py` invalidated BOTH of my GATE 5 probes, and it was right to

Recording this as a positive result, because it is the clearest evidence tonight that the patched
instrument works.

I had declared card C1 dead on a GATE 5 reading of 5/5-desired. Running the now-mandatory lint
against my own prompts:

```
FAIL  probe-A1.txt: states only 47% of the CONSTRAINT's content words.
FAIL  probe-A1.txt: names 3 DESIRED-design words the constraint does not: ['name', 'port', 'while']
        You are leading the witness; a 5/5 here proves nothing.
FAIL  probe-A2.txt: states only 28% of the CONSTRAINT's content words.
```

Both prompts fail, for the two distinct reasons the tool was built to catch. My "leading" probe
named the design words; my "non-leading" probe withheld half the constraint. **Neither verdict
counts**, so the kill I wrote up at 17:05 was unestablished — exactly as the reviewer said, and
exactly the frostdb/santuario failure the tool documents.

Two observations for the playbook:

- **The lint is cheap and it should run before the probe, not after the kill.** It took 0.3 s and
  it retired a conclusion I had spent ~25 minutes reaching and writing up. `A3` already says
  "lint every probe prompt before it counts"; what is missing is a line in the **checklist** (line
  8) making the lint an explicit, ticked, evidence-bearing step rather than prose inside the gate.
- **Writing a prompt that passes the lint is genuinely constraining, and that is the point.** My
  replacement prompts (`probe-B1.txt`, `probe-B2.txt`) quote the `CONSTRAINT` verbatim and then
  vary only the surrounding frame — maintainer-design-note vs incident-action-item. That is the
  only shape I found that gets ≥60% constraint coverage, zero design leakage, and two materially
  different phrasings at once. **Suggest the playbook just say that**: quote the constraint
  verbatim in both prompts and vary the frame around it. It would have saved me two failed drafts.

---

## F12 — GATE 4 A3-LOCAL is the best thing in the rewritten act, and it reversed my method

`A3-idea-gate.md:173-199`.

The old GATE 4 was unrunnable at `A3` (it needs a contract from `B2` and a grader from `B3`), so
every run waived it and fell through to GATE 5 — which the file itself calls the weakest
instrument. I did exactly that at 17:05.

The A3-LOCAL form is runnable and it is decisively better. What it cost me: one scratch JUnit file
(4 assertions), one base-validation run, five worktrees, five cold implementations, five test runs.
About 35 minutes wall, most of it parallel. What it bought:

- a **validated** discriminator — the sketch was proven to fail at `base_commit` *before* being
  used, so a 5/5 afterwards means something a convergence reading never can;
- five real implementations I can diff, rather than five descriptions of intent;
- the actual answer, which agreed with my retracted GATE 5 reading but for the first time on
  evidence that survives the lint.

**One gap in the A3-LOCAL text, worth fixing.** Step 3 says "the current code must FAIL it. An
assertion that already passes measures nothing." That is right for the sketch *as a whole*, but my
sketch deliberately contains assertions that **pass** at base — T3 is the DESIRED-vs-NON-DESIRED
discriminator and it *must* pass at base, because the NON-DESIRED design is precisely the one that
regresses it. A literal reading of step 3 would have made me delete the only assertion that
separates the two designs.

Suggest: *"the sketch as a whole must fail at `base_commit`. Individual assertions may pass there —
an assertion that distinguishes DESIRED from NON-DESIRED by catching a regression will pass at base
by construction, and deleting it destroys the discriminator."*

**Cost:** ~10 min of hesitation over whether T3 was legal. Zero, if the text says this.

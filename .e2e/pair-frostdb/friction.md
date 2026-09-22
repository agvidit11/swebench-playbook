# friction.md — pair-frostdb

Appended as I go. One entry per place the playbook was unclear, missing, wrong,
self-contradictory, or slower than it should have been.

---

## F1 — `B2-contract.md` is missing two rules the source pipeline had
**File:** `B-build/B2-contract.md` (whole file)
**Reported by:** the common brief, confirmed as a known gap before I started.
The two missing rules are: **"step 2's spec must be self-contained"** and
**"no 'deferred to step 2' language in step 1"**. I will apply both when I brief
Avocado and will note in the B2 handoff that they came from the brief, not the
act-file.
**Time cost:** none yet (pre-warned). Would have been a full repair round if not.

---

## F2 — `instruction-lint.py` shipped stale relative to the D1 naming rule
**File:** `~/.claude/skills/swebench-mt/instruction-lint.py`; consumed by
`B-build/B2-contract.md` whose EXIT is "instruction-lint clean".
The old script enforced an *absolute* never-name rule and hard-FAILed on any
symbol absent at `base_commit`. Under D1 a new name that the graded tests pin
MUST be named in the contract — so B2's exit condition was **unreachable** for
any task whose grader pins a new symbol. That is a playbook-level defect: an act
file's exit condition was gated on a tool that contradicted the rule the act
file states.
Fixed in place by the coordinator (three-way check, both directions). Note it
only runs the leak half until `tests/config.json` has a `test_patch` — so it
must be re-run after B3, which `B2` does not currently tell you.
**Time cost:** zero for me (fixed before I reached B2), but it would have cost a
full round.

---

## F3 — `A2` §2 gives two surface-count rules that disagree, and the tiebreak
is stated in a direction that does not cover my case
**File:** `A-source/A2-idea-generate.md:51-58`
The LOC band (45,247 → 15k–60k) says **10–12 surfaces**. The cross-check says
"roughly 2–3 surfaces per major subsystem", and frostdb has 8 subsystems with
real LOC (query 9,166 · pqarrow 5,175 · root 4,527 · dynparquet 2,724 · index
1,133 · internal 1,086 · wal 694 · parts 459) → **16–24**. The act says "if LOC
and subsystem count disagree badly, trust the subsystem count", but its worked
example is the *opposite* direction (200k LOC in three packages → fewer
surfaces). It does not say what to do when the subsystem count is *higher* than
the LOC band. I asked for 14–16 and wrote the derivation down.
**Time cost:** ~5 min of re-reading.

---

## F4 — the playbook has no act between "read the shortlist" and `A2`, so the
`A1` HANDOFF that `A2` step 1 requires does not exist
**File:** `A-source/A2-idea-generate.md:272` ("Read `HANDOFF A1`") and
`00-ROUTER.md:22` (S1 = "Repo picked, no candidate cards").
My assignment starts me at `A2` with a *shortlist log*, not an `A1` HANDOFF
block. The log carries most of the same facts (LOC, subsystems, dedup,
AI-authorship, timings) but not in HANDOFF shape, and it does not carry a HEAD
sha — I had to derive that from the clone myself
(`9e5cfe0171adff531d30a9df3e111686996f4a9f`). A2 step 1 also says "Do not
re-measure", which conflicts with `A2` §3.2's instruction to re-verify quoted
admissions against current HEAD, and with the brief's "do not accept any
pre-screen". I re-verified the one surface the shortlist named
(`index/lsm.go:401`) and the timings, and treated everything else as claims.
**Time cost:** ~10 min.

---

## F5 — `A2` names MetaCode as owner but gives no card-authoring dispatch, only a survey one
**File:** `A-source/A2-idea-generate.md:5` (Owner), `:108-114` (tooling), `:265-284` (checklist)
The act's owner is MetaCode and Claude "never generates ideas or surfaces". But
the checklist runs `survey.txt → run the survey → merge → write one card per
survivor → self-audit each card`, and only the *survey* has a documented
dispatch pattern. Steps 8-11 (merge, auto-reject, card, self-audit) are
generative and therefore also MetaCode's, yet nothing tells you to dispatch them
— read naively, Claude writes the cards, which violates §5's spirit even though
§5 only hard-blocks `instruction.md`. I dispatched a second `mc.sh` pass for the
cards. That is the right call but it is mine, not the playbook's.
**Fix:** A2 should specify two dispatches — survey, then cards — with the card
brief's required fields, and say that the merge/auto-reject/self-audit stages
belong to the same owner as the survey.
**Time cost:** ~15 min deciding, ~12 min of extra dispatch wall-clock.

## F6 — `EARLIER:` the hollow-premise clause is in the survey prompt but there is
no *verification* step before cards are written
**File:** `A-source/A2-idea-generate.md:77-86` (the shift-left clause) and
checklist step 10.
The clause worked partially: both surveys cited `file:line` for every surface.
It still did not stop a hollow premise. MetaCode's S2 claimed `avg` had "no
execution behind it" and cited `chooseAggregationFunction`'s `default:` branch
**correctly** — the citation is true, the conclusion is false, because
`resolveAggregation` (`query/logicalplan/builder.go:205-234`) desugars
`AggFuncAvg` one layer *above* the cited line. A `file:line` citation proves the
line exists; it does not prove the layer above does not already handle the case.
The cheap check that would have caught it: **run the repo's own end-to-end
fixtures for the behaviour before writing the card** — `logictest/testdata/exec/
aggregate/aggregate:47` is a passing `avg(...)` fixture sitting in the tree.
**Where it should live:** a new A2 checklist line between 9 and 10: *"for every
surviving premise, grep the repo's own test/fixture corpus for the behaviour you
claim is absent; a passing fixture is a kill."* That is 30 seconds per card and
it killed one of four merged candidates here.
**Time cost:** ~20 min (I found it by hand after the survey; the card pass then
had to be re-briefed).

## F7 — `EARLIER:` nothing in A2 checks whether a proposed step 1 already exists at `base_commit`
**File:** `A-source/A2-idea-generate.md:174-196` (auto-rejects)
§6 rejects "step 1 = recall-only" and "step 1 whose requirements include
behaviour and returns are unchanged", but neither is phrased as the mechanical
check that catches it: *is the code this step asks for already in the tree at
`base_commit`?* MetaCode's S8/M3 proposed a step 1 that builds the sampler's
alphabetical field sort, which is verbatim at
`query/physicalplan/sampler.go:244-254`. A one-line grep kills it.
**Where it should live:** same new checklist line as F6 — "for every step 1,
`grep` for the construct it asks you to add; if it is already there the card is
dead." Costs seconds, killed a second of four merged candidates.

## F8 — `REPEAT:` I re-derived HEAD, LOC-per-subsystem, build time and test time
that the shortlist either did not carry or carried in the wrong shape
**File:** `A-source/A2-idea-generate.md:272` ("Read `HANDOFF A1`… Do not
re-measure") vs. reality.
The shortlist log has LOC totals and two test timings but no HEAD sha, no
per-subsystem LOC breakdown, and no warm-build figure. A2 §2 needs the
per-subsystem count to derive the surface ask, so I measured it anyway. I also
spot-checked `go build` and `go test ./index/...` because the brief says not to
accept a pre-screen.
**Fix:** the `A1` HANDOFF's `FACTS:` line should be *required* to carry HEAD sha
+ per-subsystem non-test LOC, because A2 §2 consumes exactly those.
**Time cost:** ~8 min.

## F9 — `WASTE:` running a second independent survey cost ~11 min of wall-clock and
changed the outcome, so it was NOT waste — but the playbook does not sanction it
**File:** `A-source/A2-idea-generate.md:5` ("Codex may run the wide survey")
Read literally this is an either/or. I ran both. It paid: Codex independently
reached the same multi-sink candidate (which is why I rank it first — two
independent surveys converging is evidence the single-survey path cannot
produce), and Codex avoided the `avg` hollow premise that MetaCode fell into.
Logging it because the playbook currently makes this look like duplicated work
when it is actually the cheapest cross-check available at this stage — both
dispatches run in parallel and neither blocks the other.
**Recommendation:** make the second survey standard, explicitly as a
cross-check, and add a "where the two surveys disagree" step to the merge.

## F10 — `PINPOINT:` no act-file owns "this premise is hollow", so R8 cannot route it
**File:** `reference/R8-finding-to-file.md` is described in `00-ROUTER.md:232`
as "tracing a finding to the file that owns it", but a hollow premise is found
*before* any artifact exists. There is no artifact to route to and no act-file
whose repair path is "kill the card". A2 §3.3 describes the prevention but
nothing describes the remediation, so the honest move (delete the candidate,
record the evidence) is left to judgment.
**Fix:** A2 §6 should end with an explicit disposition for a premise that fails
verification: `record the quote that killed it in the card-pass rejection list;
never elaborate it; never re-survey the same surface`.

---

## F11 — `EARLIER:` GATE 1's fork-collapse test would have killed both cards for
free, before ~50 minutes of probing
**File:** `A-source/A3-idea-gate.md:66-68`
The test is three lines: *write the contract sentence, write the
observable-consequence sentence, if they are the same sentence the fork is zero.*
Applied to C1 and C2 it is instantly true for both, and the 10/10 + 10/10 + 5/5
probes only confirmed it. **But the test lives at `A3`**, after the cards are
written, and `A2` never asks for the two sentences side by side even though `A2`
§4 already demands the observable and the contract as separate card fields.
**Where it should live:** `A2` §4 should require the two sentences adjacent on
the card, and §7's self-audit should carry a row for them. Both cards already
contained the material; nobody was asked to put it next to itself.
**Time cost:** ~50 min of probe wall-clock that changed no decision — though it
did convert an argued kill into a measured one, which the run wanted.

## F12 — `PINPOINT:` GATE 3 says "a shipped test = the direction is public" but
routes you to `<clone>/src/test`, which does not exist in most repos
**File:** `A-source/A3-idea-gate.md:95` —
`grep -rln "<behaviour keyword>" <clone>/src/test | head`
That path is Java/Maven-shaped. In frostdb the decisive artifact was
`logictest/testdata/plan/aggregate/aggregate` — a **checked-in prose-annotated
expectation fixture**, not a test file, in a directory the suggested path would
never reach. It contained (a) a maintainer TODO declining the exact widening
C2 proposed, and (b) proof that `OrderedAggregate` never plans anywhere in the
suite. I found it only because PR #307's body pointed at it by name.
**Fix:** the grep should be language-agnostic and should include fixture/golden
directories: `grep -rln "<keyword>" <clone> --include='*test*' --include='*testdata*'`,
plus an explicit instruction to follow any "see the X test for details" pointer
in a PR body.

## F13 — `EARLIER:` the card's size estimate ran 2-3× high and nothing checks it
until after a build
**Files:** `A2` §4 "Size estimate", `A3` GATE 6 anti-overcorrection [N04]
C1's card estimated 110-190 net lines across 2 files. The five real
implementations came in at **39-67 net lines in 1 file** — under the 80-150
floor, which is itself a GATE 6 fail. The estimate was made by reading code; the
measurement fell out of the GATE-4 probe for free.
**Where it should live:** GATE 4 already produces real patches. `A3` should say
"read the net-line count off the GATE-4 implementations and re-run N04 against
the measured number, not the card's estimate." One line, no extra cost.

## F14 — `WASTE:` GATE 2's "execute, don't grep" is right, but `A3` gives no
recipe and the obvious route dirties the clone
**File:** `A-source/A3-idea-gate.md:81`
"Grep is not reproduction. Execute at `base_commit`" is the correct rule and it
paid for itself twice here. But the act gives a `grep` one-liner and no
execution recipe, so each agent invents one. Mine was: write
`zz_<scope>_test.go` into the clone, run `go test -run …`, delete it, then
assert `git status --porcelain` is empty. That worked and is worth writing down,
because the naive alternative — editing an existing test file — leaves the clone
dirty and silently poisons every later measurement taken from it.
**Fix:** `A3` GATE 2 should carry the throwaway-probe-file recipe and the
mandatory `git status --porcelain` check after.

## F15 — `REPEAT:` I built the same "does it parse and how many rows" helper
twice, once for GATE 2 and once for GATE 4
Small, but structural: GATE 2 wants an executed reproduction and GATE 4 wants a
graded assertion, and for any candidate they exercise the *same* entry point with
the *same* fixtures. `A3` treats them as unrelated gates.
**Fix:** GATE 2 should say "write the reproduction as the first assertion of your
GATE-4 harness"; the reproduction then doubles as the base-commit validation
GATE 4 needs anyway (mine: A1/A2/A3 fail at base, A4 passes). One artifact, two
gates, and it forces the f2p/p2p baseline diff to exist early.

## F16 — the two-survey cross-check earned its keep a second time
Extending F9 with the A3 result: MetaCode's survey produced the hollow `avg`
premise, Codex's did not. Codex's survey produced the optimizer-injection
candidate that died on "no caller", MetaCode's did not. **Both surveys
independently produced the multi-sink candidate**, which is why it was ranked
first — and it was also the one that turned out to be a measured 5/5. So
convergence between two independent surveys is NOT evidence of quality; here it
was evidence that the candidate is *obvious*, which is the same property that
makes a model one-shot it.
**That inversion is worth a rule:** when two independent surveys converge on the
same candidate, treat it as a **fork-strength warning**, not a confidence
signal — and probe that candidate first. I did rank it first and probe it first,
but for the opposite reason, and I got the right answer by luck of ordering.

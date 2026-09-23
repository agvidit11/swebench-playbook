# friction.md — r2-connectgo

One entry per place the playbook was unclear, missing, wrong, self-contradictory, or slower
than it should have been. Appended as I go.

---

## F1 — `A2-idea-generate.md:272` demands a `HANDOFF A1` that structurally cannot exist

**Where:** `A-source/A2-idea-generate.md` §8 checklist line 1, and the `Input` row of the header
table (line 6).

Both make `HANDOFF A1` a hard input: *"Read `HANDOFF A1` | LOC, subsystem count, HEAD sha and the
named existing entry point copied into your run notes. **Do not re-measure**"*. My brief starts me
at `A2` with the screening delivered as a **prose shortlist** (`shortlist-proto.md`), which is not
a HANDOFF block and does not carry three of the five named fields — it has LOC and a subsystem
list, but **no HEAD sha** and **no named existing entry point**. So "do not re-measure" is
unsatisfiable on its face: I had to clone and run `git log -1` to get a base sha before I could
write a single card field.

**Cost:** ~4 minutes, and a judgement call about how much re-measuring is allowed that the
playbook should have made for me.

**Fix:** `A1` should emit the HANDOFF block to a file the way every other act does, or `A2` should
say what to do when its input is a screening report rather than a HANDOFF. A one-line "if you
were handed a shortlist instead, re-derive HEAD sha and the entry point; everything else is
authoritative" would close it.

---

## F2 — `A2` §2 contradicts its own `Output` row on the card count

**Where:** `A2-idea-generate.md:8` (`Output | candidate cards — dispatch target **≥8**`) versus
`A2-idea-generate.md:60` (*"the ≥8 dispatch target is reachable only on a 60k+ LOC repo with many
subsystems... On a smaller repo, report the real number and the derivation"*).

connect-go is 28,882 non-test LOC, so §2 says 10–12 *surfaces* collapsing to *2–4 candidates*,
while the header row asks for ≥8 cards. The reconciliation is in §2 but the header is what an
agent copies into its plan. Checklist line 12 then asks me to "confirm the count honestly... vs
the ≥8 target", which re-anchors on the number §2 just told me is unreachable.

**Cost:** low in time, non-trivial in pressure-to-backfill — which is the exact behaviour §60
forbids in the next sentence.

**Fix:** make the `Output` row conditional: `≥8 on a 60k+ repo; otherwise per §2`.

---

## F3 — `B2-contract.md` is missing two rules the source pipeline had (flagged in my brief, confirmed)

`B2` lacks **"step 2's spec must be self-contained"** and **"no 'deferred to step 2' language in
step 1"**. I will apply both when briefing Avocado. Logged here per the common brief's
instruction; see F-numbered entries below for anything I hit myself.

---

## F4 — `A3` GATE 4 and GATE 5 cost far more wall-clock than the "~6 minutes per candidate" budget

**Where:** `A3-idea-gate.md:14` — *"Budget **~6 minutes per candidate** through GATE 0–3"* — then
GATE 4 asks for **5** `mc.sh` dispatches and GATE 5 for **10** `metacode run` calls, per
candidate. A single `mc.sh` survey dispatch on this repo has already been running for >8 minutes
(`timeout 1700` is the ceiling the helper itself sets). 15 serial calls at even 3 minutes each is
45 minutes per candidate, which is an order of magnitude past the stated budget and cannot be
reconciled with "get to a probed survivor fast".

The act never says the probes may be run **concurrently**, and §6 of the router lists "ideation,
fork probes, novelty sweeps" as parallel-safe — so the permission exists, but it is in a
different file from the instruction that needs it.

**Fix:** state the concurrency allowance inside GATE 4/5, and give a realistic wall-clock figure
(the 6-minute budget is for GATE 0–3 only, which the text does say, but the reader arrives at
GATE 4 with "6 minutes" in their head).

---

## F5 — `A3` contradicts itself on which gate decides: GATE 4 is declared PRIMARY, GATE 8's fork veto overrides it anyway

**Where:** `A-source/A3-idea-gate.md:143-145` versus `:245`.

`:143` — *"**GATE 4 — the outcome-variance probe (PRIMARY)**"*, `:145` — *"Outcome variance is the
target, not design divergence... A task can have two genuinely different valid designs and have
both pass every time."* `:182` — *"GATE 5 — the model-prior fork probe (**SECONDARY**, design)"*.

Then `:245` — *"**Threshold: build only at ≥28/40, and never with Fork strength ≤2**... Score Fork
from GATE 5's measurement (≥4/5 desired path = 1, do not build)."*

So the SECONDARY gate carries an absolute veto over the PRIMARY one, and the act never says which
wins. This is not hypothetical — it is exactly the state my survivor is in:

- GATE 4, measured: **3 of 5** cold implementations pass the graded assertion. `A3`'s own table:
  *"1–3/5 pass → in band. This is the target."*
- GATE 5 phrasing A, measured: **5 of 5** propose the intended design. `A3`'s own table:
  *"≥4/5 take the desired path → no fork. It will one-shot. Do not build."*
- GATE 8, scored by Codex reading both numbers: **34/40, Fork 1, "Would I build it? No."**

Both numbers are real and they disagree, because they measure different things: whether a model can
*describe* the fix, and whether a model can *land* it. On this candidate the description is easy and
the landing is not — two of the five wrote a plausible, building, upstream-suite-passing patch that
still missed a required behaviour.

**Cost:** ~25 minutes of deciding, and it is the single highest-stakes ambiguity in the act.

**Fix:** state the precedence in one sentence. My read of the evidence, offered rather than
asserted: the fork veto is a *proxy* for "it will one-shot", and GATE 4 measures that property
directly, so a measured in-band GATE 4 should retire the proxy. If the intended precedence is the
other way, `:143`'s "PRIMARY" should be deleted, because it is currently the wrong signpost.

**What I did:** proceeded, and recorded the veto and the override in `handoffs/02-A3-ADDENDUM.md`
rather than burying it. Reviewer can overrule; nothing downstream depends on the choice being right.

---

## F6 — `B1` §2's landmine table is out of date against the scaffold it describes, in both directions

**Where:** `B1-scaffold.md:123-147`.

I ran `codimango task init --type swebench-multi` today and diffed the result against all 21 rows.
The scaffold has moved:

- **Rows 2, 4, 12, 18, 21 are already fixed upstream.** The shipped `tests/test.sh` accepts both
  `fail_to_pass` and `FAIL_TO_PASS` *and hard-errors when they disagree*, parses
  `before_repo_set_cmd`'s multi-line form correctly in Python rather than taking the last line in
  bash, derives the reward from parsed results with a fail-closed prologue and an explicit comment
  saying not to use `$?`, and ships **no canary at all** (`grep -ril 'canary\|BENCHMARK DATA SHOULD
  NEVER'` over the fresh tree returns nothing). Rows 1 and 10 are also gone — there is no `tests/`
  regex in `parser.py` any more, and the gold-checkout block is present.
- **But `preflight.sh` still flags row 21** — *"reward may derive from exit status in
  …/tests/test.sh"* — on the **stock, unmodified scaffold**, because `cleanup_and_reward()`
  reads `local exit_code=$?`. The scaffold's own comment explains at length why that read is a
  backstop and not the reward. So the checker and the template now disagree out of the box, and
  a new author cannot tell whether they are looking at a real finding.

**Cost:** ~20 minutes reading a table against a template that had already moved.

**Fix:** re-derive §2 against the current `task init` output and date-stamp it; and either teach
`preflight.sh` to recognise the stock `cleanup_and_reward` shape or drop row 21's check.

---

## F7 — the `team-aai` Bash guard blocks read-only commands on a computed filename

**Where:** the `team-aai` provenance guard, triggered while I was inspecting the scaffold.

`find . -name 'instr*.md' -exec wc -c {} \;` — the exact command `B1-scaffold.md:213` tells me to
run as proof for checklist line 1b — was refused with *"this Bash command writes to a computed
filename (command substitution or glob) inside a guarded task's spec directory"*. It writes nothing;
`wc -c` reads. The guard pattern-matches on the glob, not on the verb.

**Cost:** small, but it makes a checklist line unrunnable as written, which is the worst kind of
friction because the honest response is to tick it with a substitute and the tempting one is to tick
it anyway.

**Fix:** `B1` should give a guard-safe proof command (`stat -c '%s %n' <task>/steps/*/instruction.md`
works and I used it), or the guard should exempt read-only verbs.

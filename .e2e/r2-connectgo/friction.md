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

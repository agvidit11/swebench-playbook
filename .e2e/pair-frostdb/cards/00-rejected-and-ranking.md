# A2 — candidates NOT carded, and the ranking

## Candidates NOT carded (one line each)

- **MC-M1 (ordered multi-agg + avg):** dead — hollow premise per correction 1 (`avg` desugared at `builder.go:205-234`, execution fixtures pass; step 2 rests on "no avg execution").
- **MC-M2 (sort+merge type-widening + nulls):** dead — mechanical-edit volume (per-type switch cases in two files) with coexisting parallel APIs; fails both P6 operational tests, no genuine tension.
- **MC-M3 (sampler order + index fix):** dead — step 1 already in tree (`sampler.go:244-254`, auto-reject) and the remainder (S12 positional-index fix) is sub-20-line, under the floor per correction 3.
- **MC-M4:** **carded as C1** (merged with Codex-M4, same candidate; better analysis taken from each).
- **Codex-M1 (optimizer injection → isolation):** dead — no motivating caller (hypothetical embedders = "a nicer API") compounded by recall-only functional-options step 1.
- **Codex-M2:** **carded as C2** (rescoped to ordered-path-only per correction 2, SQL path corrected to `sqlparse/visitor.go`, step 2 narrowed to single-agg to fit the envelope).
- **Codex-M3 (proto node + enum parity):** dead — step 1 is the one-line `engine.go:140` fix (sub-20-line auto-reject per correction 6); cascade collapses, S6 alone is single-turn.
- **Codex-M4:** **merged into C1** (same multi-sink candidate as MC-M4).
- **Codex-M5 (PreviewRecord → continuity):** dead — step 1 as specified is satisfied by trivial `return b.NewRecord()` delegation so nothing stops avocado outright (breaks the required per-arm profile), and any rescope that fixes the profile pushes into arrow-builder ownership surgery with no caller beyond write-path convenience.
- **Codex-M6 (nested ingestion → nested merge):** dead — 550–1000 net lines (3–6× the envelope) with step 1 (native Arrow structs + schema-v2 groups across nullable/repeated parents) harder than step 2, inverting measurement.

## Ranked list + honest read

1. **C1 (streaming multi-sink persist)** — strongest: live refusal contradicting its own doc comment, in-envelope size, barrier observable with no valid-alternative leakage, stdlib recall punished by contract.
2. **C2 (computed operands → order-preserving projection)** — buildable with careful grader scoping; carries the flagged R09 size residual and a preservation-predicate over/under-fit risk (R03 deferred).

**Honest read:** yes, this repo yields at least one buildable multi-turn task — C1 is a genuine revert-and-redo with a verified fork, a concrete rotation/migration caller, and a deterministic barrier seam. C2 is a real second, contingent on grading the planner carve-out in both directions (J1+J2). An honest zero was available; the evidence did not support it.

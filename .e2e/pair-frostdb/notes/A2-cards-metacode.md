MetaCode at Meta (https://fburl.com/metacode)
Using AI Gateway (Meta Model API upstream)
[metacode] using AI inference gateway (Model API): https://metacode-modelapi.ai-gateway.fbinfra.net/v1
Warning: Failed to mount .arcrc: Mount failed '/tmp/phabricator_cats/metacode_agvidit/1235111/arcrc' to '/home/agvidit/.arcrc': ENOENT: No such file or directory
[93mWARNING: 11 skill(s) in /home/agvidit/.claude/ not available for MetaCode.[0m
MetaCode reads skills from ~/.agents/skills/ and .metacode/skills/, not from .claude/.
Run `metacode migrate-from-claude` to copy them to ~/.agents/skills/, or `agent-market skill <name> install --agent metacode`, or open MetaCode TUI and run `/legacy-skills` to see the list.

Writing candidate cards — first reading both surface surveys in full.
I've got the main surfaces — now pulling the remaining sections to complete the merge map.
Both surveys read. Now verifying HEAD citations read-only for the survivors before writing cards.
Tension mechanism verified hands-on. One last check — the SQL-side pre-projection that motivates the M2 step-1 design.
I have verified every HEAD citation below read-only against the clone at `/tmp/frostdb-run/frostdb`. Composing the cards now — printed to stdout, no disk writes.

# CARD PASS — polarsignals/frostdb @ 9e5cfe0171adff531d30a9df3e111686996f4a9f

Both surveys read in full (`survey-mc.out`, 544 lines; `survey-codex.md`, 373 lines). All six hand-verified corrections accepted as overriding. Key re-verifications I performed myself in this pass: `store.go:30-62` refusal + single-sink `io.Pipe` streaming; `db.go:348-350` doc-comment contradiction + `db.go:187-192` appendable sinks + `db.go:382-387` `DataSink` interface; `query/exprpb/engine.go:140` discarded builder return vs `b = b.Project(exprs...)` at `:118`; `query/physicalplan/aggregate.go:33-36` brancz TODO + `:54-59` ordered-only refusal; `query/physicalplan/physicalplan.go:315-316,349-364,525-531` (the Projection/ordering interaction); `query/physicalplan/planordering.go:42-50` invalidation state machine; `sqlparse/visitor.go:86-91,129-130` (repo-root path — the Codex survey's `query/sqlparse/` path is stale, content confirmed live); `internal/records/record_builder.go:251-313,547-549` + `table.go:237-245` drain-on-`NewRecord` semantics.

---

## C1 — Streaming multi-sink persist (merged: MC-M4 + Codex-M4, same candidate)

1. **Composition** — C-axis: **AXIS 19, closed extension point behind a refusal guard** (the storage-boundary refusal). A-shape: **P6 revert-and-redo, buffer-then-constrain** (step 1 builds a materialize-everything fan-out; step 2's single-pass concurrency constraint forces removal of step 1's buffer).

2. **Step requirements, invariants, tension.**
   - **Step 1.** `TableBlock.Persist` delivers the block to *every* configured sink. May serialize once to bytes and upload per sink sequentially; may serialize per sink. Invariant **I1**: each of N sinks holds a parseable `data.parquet` with the expected row count. Invariant **I2**: a failing sink surfaces an error and triggers per-sink `Delete` cleanup of partial uploads (the single-sink `Delete`-on-error at `store.go:53-55` generalized).
   - **Step 2.** Constrain to a **single coordinated serialization stream**: one `Serialize` pass feeds N concurrent `Upload`s; both uploads must be in-flight simultaneously (observable via a start barrier in fake sinks); per-sink errors aggregated without losing the healthy sink's block. The step-1 buffer must go. Invariant **J1**: both `Upload` calls cross an explicit start barrier before `Serialize` completes, and each stream parses to the full row count. Invariant **J2**: mid-stream failure of one sink yields an error mentioning that sink while the healthy sink's block stays intact.
   - **Tension in one sentence:** one `io.Reader` is single-shot while N independent sinks exert independent backpressure and fail independently, so sharing a single serialization pass conflicts with per-sink failure isolation.
   - **Cost-clause accounting (compound constraint: "bounded memory" AND "partial failure rolls back"):** the **bounded-memory/concurrency half does all the work** — it is what invalidates step 1's buffer-then-loop (a buffered loop can never have sink 2's `Upload` in flight before sink 1 finishes). The failure-rollback half alone does *not* invalidate step 1 (buffered fan-out + per-sink `Delete` already satisfies it); drop the concurrency half and step 1 survives intact, so the concurrency half is the load-bearing fork and the failure half is secondary hardening. P6 genuinely engaged via the first half.

3. **HEAD citation + nearest presence.**
   - HEAD refuses, `store.go:35-38`:
     > `for i, sink := range t.table.db.sinks { if i > 0 { return fmt.Errorf("multiple sinks not supported") }`
   - while the struct comment promises the opposite, `db.go:348-350`:
     > `// The database supports multiple data sources and sinks.` / `sources []DataSource` / `sinks []DataSink`
   - and the sinks are publicly appendable, `db.go:187-192` (`WithWriteOnlyStorage` → `s.sinks = append(s.sinks, ds)`).
   - **Nearest presence** (verbatim, the case it fails to cover): the single-sink path at `store.go:39-49` already streams — `r, w := io.Pipe()` / `go func() { defer w.Close(); err = t.Serialize(w) }()` / `sink.Upload(ctx, fileName, r)` — covering one-shot streaming to one sink; it fails to cover fan-out (one serialization → N uploads with independent failure domains).

4. **Motivating caller.** Block rotation (`table.go:436 writeBlock`, `:572 RotateBlock`) calls `Persist` per rotated block. The concrete operational need is **dual-write migration and second-bucket backup during rotation** (local FS + object store, or primary + replica bucket): today configuring the second sink via the public `WithWriteOnlyStorage` option is a hard error at persist time, so any operator wanting mirrored durability must fork the persist path out-of-tree. Scale requirement is per-block fan-out (one stream shared by N uploads), not per-row. "A nicer API" this is not — the configuration surface already exists and the refusal breaks it.

5. **Interface Contract.** No new exported symbols; the contract is behavioral through existing entry points:

   | Symbol | Kind | Shape | Reachability | Alternatives |
   |---|---|---|---|---|
   | `TableBlock.Persist` | method | existing `func (t *TableBlock) Persist() error`, N-sink behavior | IN-BASE (`store.go:30`) | n/a (existing API, behavior-graded) |
   | `DataSink.Upload/Delete` fakes | test-local | in-memory buckets + start-barrier + fail-injection | STATED (test harness constructs them; not repo symbols) | any fake implementing `db.go:382-387` accepted |
   | `WithWriteOnlyStorage` | option | existing multi-append | IN-BASE (`db.go:187`) | n/a |

   A symbol neither STATED nor IN-BASE: none — that is the point; the task adds behavior, not vocabulary.

6. **Observable Schema.** N/A — the deliverable is upload behavior on existing sinks, not a collection of records. Byte-identical output across sinks is explicitly **not** required (re-serialization is a valid step-1 shape); graded observable is parseability + row counts + barrier concurrency + failure semantics. (No test-only reset hook needed; fakes are constructed per test. No design smell.)

7. **Named wrong shapes + why plausible.**
   - *Step-1-shaped wrong answer to step 2:* **serialize-per-sink loop** (call the existing pipe/`Serialize` body N times). Plausible because it is the smallest diff to the existing loop and passes every row-count assertion; it fails J1 (uploads never concurrent from one pass) and wastes N× serialization CPU against rotation.
   - *Recalled wrong answer:* **naive `io.MultiWriter` fan-out.** Plausible because the stdlib names exactly this ("fan-out writer") and the single-sink path already uses `io.Pipe`; a capable model reaches for it first. It fails J2 (first failing/slow writer aborts or stalls all sinks; no per-sink error aggregation) and the barrier case. Neither is a strawman: the first is the survey-predicted cold implementation in both surveys; the second is what the three-word recall test below actually retrieves.

8. **Determinism seam.** In-memory fake `DataSink`s with an explicit channel start-barrier and mid-stream fail-injection. Concurrency is required (that is the graded point) but wall-clock timing and real network are not: barrier release is test-driven, serialization output is fixed blocks. No flakiness by construction.

9. **Predicted per-arm rates.**
   - Step 1: avocado **3/5**, opus **4/5**, gpt **4/5**. *What stops avocado outright:* step 1 is not just guard-removal — I2's per-sink `Delete`-on-error must be threaded through the existing pipe-goroutine error capture (`store.go:40-57`, where `err` crosses a goroutine boundary and upload-error vs serialize-error take different paths); the cheap loop drops the cleanup or conflates the two error paths, failing the fail-sinkB-assert-A-intact guard case.
   - Step 2: avocado **1/5**, opus **3/5**, gpt **2/5** (mixed, as required). Steps are in the right order: step 2 (single-shot-reader fan-out with independent failure domains) is strictly the harder step; step 1's successes bound step 2's effective n without inversion.

10. **Step-1 guard cases owned by step 2.** I1 is guarded by step-2 `f2p.barrier_concurrent_full_rows` (both uploads in flight pre-completion, each parsing to full counts — fails if fan-out drops/duplicates bytes, i.e. I1 regresses). I2 is guarded by step-2 `f2p.midstream_failure_isolation` (sinkB fails halfway → error names B, sinkA intact, no leaked partial on B — fails if error/cleanup discipline regresses). Step-1 `f2p` IDs live only in step 1's `pass_to_pass`; they are never copied into step 2's `pass_to_pass`.

11. **Inter-step file overlap.** Step 1: `store.go` (+ storage tests). Step 2: `store.go` again — **incremental on step 1** (replaces step-1's loop/buffer with coordinated fan-out on the same `Persist` path; no second API alongside, since `RotateBlock`/`writeBlock` call one path). Tests cumulative from base.

12. **Size estimate.** 1–2 files (`store.go` + tests), **110–190 net lines honestly** (both surveys converge here): ~40–70 for step 1 (loop + per-sink cleanup), ~70–120 for step 2 (tee/barrier fan-out + error aggregation). Primitives reused: `io.Pipe`, `errgroup` (already imported at `store.go:18`), `DataSink.Upload/Delete`, in-memory `objstore.Bucket` fakes. Upper edge of the 80–150 envelope, honestly reported.

13. **Rubric self-audit.**

    | Item | Verdict | Evidence (one line) |
    |---|---|---|
    | R01 (premise live) | PASS | refusal quote `store.go:35-38` + contradicting promise `db.go:348-350`; nearly failed by mistaking the existing `io.Pipe` streaming (`:39-49`) for fan-out coverage |
    | R02 (observable behavioral) | PASS | barrier-concurrency + parseable-row-counts, no byte-identity; nearly failed by asserting identical bytes, which would punish valid re-serialization |
    | R04 (fork genuine) | PASS | sequential loop vs coordinated fan-out both writable, differ on J1 — not speed-only |
    | R05 (no coined schema) | PASS | zero new symbols; contract reuses `Persist`/`Upload`/`Delete` in library terms |
    | R06 (caller concrete) | PASS | dual-write rotation backup via existing `WithWriteOnlyStorage`, not "nicer API" |
    | R07 (determinism) | PASS | fake-sink channel barrier, no clock/network |
    | R08 (grader distribution) | PASS | observable accepts re-serialization (step 1) and any fan-out topology meeting the barrier; nearly failed by pinning `io.MultiWriter` as the mechanism |
    | R09 (size envelope) | PASS | 110–190, upper edge but inside tolerance; primitives reused, honestly counted |
    | R11 (inter-step cascade) | PASS | J1 unpassable with step-1 buffer (HEAD counterfactual + parallel-`PersistFanout` rejected: rotation calls one path) |
    | N01 (three-word recall) | PASS | recall retrieves `io.MultiWriter`, which the contract punishes (J2) — recall is the trap, not the key |
    | N02 (existing vocabulary) | PASS | 7/7 nouns IN-BASE with file:line; only descriptive "fan-out", never a symbol |
    | N03 (peer-shape collision) | **FAIL (residual risk)** | "fan-out writer" is a common task shape in *other* repos; corpus is clean for this repo (containment note 4) but shape-collision on the observable is flagged, not cleared |
    | N04 (cost-clause trap) | PASS | concurrency half named load-bearing, failure half secondary, drop-test stated in card |
    | R03 / R10 / R12 / R13 | deferred | R03 to grader review (barrier-case flakiness audit); R10 to mining gate (peer-shape screen); R12/R13 to task-spec stage |

---

## C2 — Computed aggregate operands → order-preserving pre-projection (rescoped Codex-M2; MC-S11/Codex-S3 + ordered-path scope)

*Rescoping notes (honest): Codex-M2 as surveyed bundles two capabilities in step 2 (computed operands **and** multi-aggregation) at 300–500 lines with an `Explain`-shape invariant. Per correction 2 the multi-agg refusal is ordered-path-only, and per the size envelope I scope step 2 to a **single** computed aggregate staying on the ordered path. The `query/sqlparse/` path cited in the Codex survey is stale; the content is live at repo-root `sqlparse/visitor.go` (verified above).*

1. **Composition** — C-axis: **AXIS 19 (refused computation: the brancz TODO) colliding with the plan-ordering state machine**. A-shape: **P6 build-then-constrain** (step 1 materializes operand arrays the naive way; step 2's ordering-preservation constraint forces rework of exactly that mechanism — verified below, not asserted).

2. **Step requirements, invariants, tension.**
   - **Step 1.** Direct-builder aggregations over computed operands execute correctly: `ScanTable(...).Aggregate([]*AggregationFunction{Sum(Col("value").Add(Col("timestamp")))}, ...)` through `Execute` returns row-wise-expression sums. Either mechanism allowed (pre-`Projection` node mirroring the SQL visitor, or in-`Aggregate` operand evaluation). Invariant **I1**: every aggregate consumes the row-wise value of its expression. Invariant **I2** (regression guard): bare-column aggregates unchanged.
   - **Step 2.** The same computed-operand query over an ordered table with ordered aggregations enabled must still plan `OrderedAggregate` (not silently fall back to hash), with values matching the hash path; **and** the planner carve-out must be narrow: tested with an *explicitly inserted* row-preserving `Project` node in the builder chain (so neither step-1 fork gets it for free), while an order-destroying shape still falls back. Invariant **J1**: `Scan→Project(row-preserving)→Aggregate` plans ordered + values correct. Invariant **J2**: a genuinely order-breaking plan still does not plan ordered.
   - **Tension in one sentence:** the projection that fixes step 1's values is precisely what kills step 2's ordered path, because the physical planner treats *any* `Projection` visit as ordering-invalidating.
   - **Tension verified at HEAD (not asserted):** every plan visit calls `oInfo.newNode()` (`physicalplan.go:315-316`); the `case plan.Projection != nil:` branch (`:349-364`) never calls `nodeMaintainsOrdering()`; per the state machine (`planordering.go:42-50`, double `newNode()` → `planOrderingInfoStateInvalidated`) the subsequent `Aggregation` visit finds ordering dead, so `shouldPlanOrderedAggregate` bails at `:529-531` (`if !oInfo.orderingMaintained() { return false, nil }`). A step-1 pre-projection therefore *necessarily* demotes step 2 to hash — the cascade is mechanical, and step 2 must teach the planner to distinguish row-preserving projections without opening the door to order-destroying ones.

3. **HEAD citation + nearest presence.**
   - HEAD admits incorrectness, `query/physicalplan/aggregate.go:33-36`:
     > `// TODO(brancz): This is not correct, it doesn't handle aggregations correctly of previously projected columns like `sum(value + timestamp)`.`
   - the ordered-path scope (correction 2): refusal is ordered-only, `aggregate.go:54-59` (`"OrderedAggregate does not support multiple aggregations"`) above the hash path at `:71-78` (`NewHashAggregate(... aggregations ...)` takes the slice); planner bail at `physicalplan.go:525-528` (`if len(agg.AggExprs) > 1 ... return false, nil`).
   - **Nearest presence** (verbatim, uncovered case): the SQL adapter already performs the repair HEAD's Go path lacks, `sqlparse/visitor.go:86-91`:
     > `// This is the expression that will be aggregated so we // need to ensure that it is in the pre-projection.` + `preProjections = append(preProjections, agg.Expr)` (wired at `:129-130`: `v.builder = v.builder.Project(preProjections...)` then `.Aggregate(aggregations, groups)`). Covers SQL-lowered queries; fails to cover direct Go `Builder.Aggregate` calls with computed operands.

4. **Motivating caller.** **Compatibility obligation + streaming bound.** The SQL layer accepts `SELECT sum(value+timestamp) ...` and lowers it through pre-projections, but the Go builder — the primary programmatic facade — silently miscomputes the same expression (brancz TODO). Any Parca-style consumer issuing arithmetic aggregates over duration-ordered tables either gets wrong values (Go path) or loses the ordered streaming bound the moment a projection intervenes (planner demotion). Both halves are needed for one correct, streaming answer.

5. **Interface Contract.** No new symbols; behavioral through existing entry points:

   | Symbol | Kind | Shape | Reachability | Alternatives |
   |---|---|---|---|---|
   | `Builder.Aggregate` / `Builder.Project` | methods | existing builder chain incl. explicit `Project` in step-2 tests | IN-BASE (`logicalplan/builder.go`, `sqlparse/visitor.go:129-130` usage) | n/a (existing API) |
   | `Execute` / `Explain` | methods | values + plan-shape observable | IN-BASE (`query/engine.go`) | n/a |
   | `OrderedAggregate` plan shape | behavior | `Draw()`/`Explain` shows ordered node (step 2 only) | IN-BASE (`ordered_aggregate.go:144-161` `Draw`) | any plan rendering naming the ordered operator accepted |

6. **Observable Schema.** N/A — deliverable is aggregate values + plan selection, not a record collection. No test-only hooks; determinism via fixed inputs (see 8).

7. **Named wrong shapes + why plausible.**
   - *Step-1 wrong shape:* extend the `DynamicColumn`-matching loop (`aggregate.go:37-52`) to also match raw computed exprs against physical field names. Plausible because the TODO sits on that loop and the loop is where names resolve; it silently aggregates the wrong array for `value+timestamp` (no field carries that name) while passing all bare-column tests.
   - *Step-2 wrong shape:* **unconditional pre-projection + hash fallback** (copy the SQL visitor pattern verbatim, accept the demotion). Plausible because the shipped visitor *demonstrates exactly this design* and every value assertion passes — only the `Explain` plan-shape case and the streaming bound fail. A second plausible step-2 failure: blanket `nodeMaintainsOrdering()` in the `Projection` case (one line, passes J1, fails J2 by keeping ordering across order-destroying projections). Neither is a strawman: each is the minimal diff its own file layout suggests.

8. **Determinism seam.** Fixed input records in table order + explicit ordered-aggregations exec option (`WithOrderedAggregations`, `physicalplan.go:273` region) + `WithOverrideInput` single-partition input. Ordering is the graded dimension, so the seam is pinned input order; no clock, no goroutines, no randomness.

9. **Predicted per-arm rates.**
   - Step 1: avocado **2/5**, opus **4/5**, gpt **3/5**. *What stops avocado outright:* the column-matching machinery (`MatchColumn` at `aggregate.go:350-352`) rewards the local loop-extension patch, which compiles green and passes bare-column suites while silently mis-aggregating computed exprs — a partial-credit trap that requires understanding expression evaluation routing, not pattern extension, to escape.
   - Step 2: avocado **1/5**, opus **3/5**, gpt **2/5**. Steps correctly ordered: step 2 (state-machine carve-out with a both-directions discriminator, J1+J2) is conceptually harder than step 1 despite fewer lines; step-1 successes bound step 2's n without inversion. The explicit-`Project` test shape closes the fork-B free pass (in-aggregate evaluation preserves ordering only when no plan node intervenes; the test inserts one).

10. **Step-1 guard cases owned by step 2.** I1 (row-wise computed values) is guarded by step-2 `f2p.ordered_computed_values_match_hash` (ordered-plan values equal hash-plan values on the same data — fails if step-1 evaluation regresses under the ordered operator). I2 (bare-column behavior) is guarded by step-2 `f2p.bare_column_still_ordered` (bare-column ordered plans unchanged by the planner carve-out) plus `f2p.order_breaking_still_hash` (J2: over-broad carving caught). Step-1 `f2p` IDs stay in step 1's `pass_to_pass` only.

11. **Inter-step file overlap.** Step 1: `query/logicalplan/builder.go` and/or `query/physicalplan/aggregate.go` (+ tests). Step 2: `query/physicalplan/physicalplan.go` (`Projection` case) + `planordering.go` (**cumulative from base** for the planner half, incremental on step 1's tests for the value half). Disjoint primary files per step except shared test coverage — no fake incrementalism.

12. **Size estimate.** 3–4 files, **~150–220 net lines honestly**: step 1 ~100–150 (operand materialization/evaluation + column binding), step 2 ~40–70 (order-preservation predicate for projections + planner wiring). Modestly above the 80–150 envelope's top; the excess is the J2 discriminator, which is load-bearing, not padding.

13. **Rubric self-audit.**

    | Item | Verdict | Evidence (one line) |
    |---|---|---|
    | R01 (premise live) | PASS | brancz TODO quoted verbatim `aggregate.go:33-36`; nearly failed by citing the stale `query/sqlparse/` path instead of repo-root `sqlparse/visitor.go` |
    | R02 (observable behavioral) | PASS | `Execute` values + `Explain` plan shape through existing entry points; nearly failed by asserting values only, which hash-fallback also satisfies |
    | R04 (fork genuine) | PASS | pre-projection vs in-aggregate evaluation both writable, diverge on ordering (verified state machine), not perf-only |
    | R05 (no coined schema) | PASS | 8/8 nouns IN-BASE with file:line; zero coined record/field names |
    | R06 (caller concrete) | PASS | SQL↔Go builder parity obligation + ordered-table streaming bound, not aesthetics |
    | R07 (determinism) | PASS | pinned input order + explicit ordered-aggs option; ordering premise gets its seam |
    | R08 (grader distribution) | PASS | contract states the ordered plan-shape requirement upfront so hash-correct solutions are out-of-contract, not failed-correct; nearly failed by leaving plan shape implicit while grading it |
    | R09 (size envelope) | **FAIL (residual risk)** | honest 150–220 exceeds the 150 top; excess is the J2 anti-overfit discriminator, kept deliberately — grader cost scales with it |
    | R11 (inter-step cascade) | PASS | verified invalidation chain (`:315-316` + `:349-364` + `planordering.go:42-50` + `:529-531`); step-2 test inserts its own `Project`, closing the fork-B free pass |
    | N01 (three-word recall) | PASS | recall retrieves "pre-projection" from the visitor, but the recalled shape fails J1 (demotion) — recall is the trap; the carve-out has no ≤3-word name |
    | N02 (existing vocabulary) | PASS | restated entirely in `Projection`/`nodeMaintainsOrdering`/`OrderedAggregate` terms |
    | N03 (peer-shape collision) | PASS | ordered-aggregation task shapes exist elsewhere, but this observable (computed-operand × ordering state machine) is FrostDB-specific مکانیک; corpus clean for this repo |
    | N04 (cost-clause trap) | PASS | single constraint (ordering preservation), no compound cost clause to split |
    | R03 / R10 / R12 / R13 | deferred | R03 to grader review (over/under-fit of the preservation predicate); R10 to mining gate; R12/R13 to spec stage |

---

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

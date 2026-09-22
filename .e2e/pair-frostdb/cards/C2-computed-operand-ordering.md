# Card C2 — Computed aggregate operands -> order-preserving pre-projection

Repo: polarsignals/frostdb @ 9e5cfe0171adff531d30a9df3e111686996f4a9f
Author: MetaCode (Avocado) — A2 card pass, brief at /tmp/frostdb-run/cards.txt

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


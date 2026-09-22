MetaCode at Meta (https://fburl.com/metacode)
Using AI Gateway (Meta Model API upstream)
[metacode] using AI inference gateway (Model API): https://metacode-modelapi.ai-gateway.fbinfra.net/v1
Warning: Failed to mount .arcrc: Mount failed '/tmp/phabricator_cats/metacode_agvidit/4097032/arcrc' to '/home/agvidit/.arcrc': ENOENT: No such file or directory
[93mWARNING: 11 skill(s) in /home/agvidit/.claude/ not available for MetaCode.[0m
MetaCode reads skills from ~/.agents/skills/ and .metacode/skills/, not from .claude/.
Run `metacode migrate-from-claude` to copy them to ~/.agents/skills/, or `agent-market skill <name> install --agent metacode`, or open MetaCode TUI and run `/legacy-skills` to see the list.

Surveying FrostDB surfaces — verifying admissions and mapping extension points.
Verifying the ten in-code admissions against HEAD before drafting surfaces.
Admissions partially verified — now checking the remaining refusal guards and planner TODOs.
I've confirmed the refusal guards are live — now gathering final context to complete the surface list.
I've confirmed the refusal guards are live — now gathering final context to complete the surface list.
Ordered aggregate and related files identified — now reading the final batch of entry points.
# SURFACE SURVEY — polarsignals/frostdb @ `9e5cfe0171adff531d30a9df3e111686996f4a9f`

Method: read-only. All line citations verified against HEAD in this session. No builds/tests run. No tree writes.
Admission re-verification summary is embedded per-surface (field 3/4). The brief says "do not re-measure" for LOC/harness; I did not.

Admission verdicts (re-verified):

- `aggregate.go:54-58` refusal guard — **STILL TRUE**.
- `aggregate.go:33-36` projected-column TODO — **STILL TRUE**.
- `merge.go:22` WARNING ascending-only — **PARTIALLY STALE**: value comparison at `merge.go:100-108` DOES consult `Direction.comparison()`; null-ordering at `merge.go:91-98` does NOT consult direction. So descending values work, descending null placement does not.
- `binaryscalarexpr.go:113` list panic — **STILL TRUE**.
- `sampler.go:262` disparate-schema TODO — **STILL TRUE**, and there is a real index bug beside it (see S12).
- `dynparquet/schema.go:1552` flat-schema-only — **STILL TRUE**.
- `record_builder.go:37` + `table.go:171` nested-columns refusal — **STILL TRUE**.
- `store.go:37` multiple-sinks refusal — **STILL TRUE**.
- `lsm.go:470` sentinel O(1) TODO — **STILL TRUE**.
- `optimize.go:181`, `planordering.go:66`, `arrow.go:723` TODOs — **STILL TRUE** (read in session).

---

## S1 — Ordered multi-aggregation behind a refusal guard

Subsystem/files: `query/` — `query/physicalplan/aggregate.go:54-70`, `query/physicalplan/physicalplan.go:518-556`, `query/physicalplan/ordered_aggregate.go:24-134`.

Axis: **AXIS 19** (closed extension point at plan boundary).

HEAD TODAY: HEAD refuses. `query/physicalplan/aggregate.go:54-58`:
> `if len(aggregations) > 1 { return nil, fmt.Errorf("OrderedAggregate does not support multiple aggregations, found %d", len(aggregations),)` 
immediately above `query/physicalplan/aggregate.go:63-65`:
> `// TODO(asubiotto): Multiple aggregation functions are not yet supported. The planning code should already have planned a hash aggregation in this case.`
The behaviour described (one ordered pass computing ≥2 aggregations) is **not implemented**. The planner colludes: `query/physicalplan/physicalplan.go:525-527`:
> `if len(agg.AggExprs) > 1 { // More than one aggregation is not yet supported. return false, nil }`
so the ordered path is never even attempted for multi-agg.

Nearest presence (verbatim neighbour + uncovered case): `query/physicalplan/ordered_aggregate.go:106-112` `func NewOrderedAggregate(pool, tracer, aggregation Aggregation, groupByColumnMatchers, finalStage)` takes exactly **one** `Aggregation`; `query/physicalplan/aggregate.go:71-78` `NewHashAggregate(... aggregations ...)` takes a slice. Neighbour covers multi-agg only via hash; fails to cover the ordered (streaming, group-boundary) case.

Fork: A = N parallel `OrderedAggregate` instances sharing one input scan, each with its own `curGroup`/builders, merged at `Finish`. B = one `OrderedAggregate` holding `[]Aggregation`, one shared group-boundary detector, vectorized agg-result builders. Cold model predicts **A** (reuses the existing single-agg struct verbatim). `FORK: strong` — both are genuinely writable; A doubles buffering and risks divergent partial-order-set bookkeeping.

Observable: through existing `Engine.Scan` / `Query` with `SELECT sum(x), max(x) ... GROUP BY ordered_col` on an ordered table; assert per-group values of **both** result columns. A-vs-B differ observably only under partial ordering / multi-record inputs (A can emit divergent ordered-set merges) and in `Draw()` string shape; not speed-only. Gradeable.

Existing-vocabulary check (6 nouns): `OrderedAggregate` IN-BASE (`ordered_aggregate.go:43`); `Aggregation` IN-BASE (`aggregate.go:104`); `GroupExprs` IN-BASE (`logicalplan/expr.go`, `Aggregation` struct); `Finish` IN-BASE (`ordered_aggregate.go:411`); `Callback` IN-BASE (`ordered_aggregate.go:163`); `multi-aggregation-set` COINED. Ratio 5/6 IN-BASE.

P6 answers: (1) HEAD counterfactual — delete step 1 (multi-agg semantics), could step 2's grader (shared single-pass boundary detection) still pass? **No**: without multi-agg there is nothing to share a boundary across; grader has no observable. Cascade is real. (2) Parallel-API test — can step 2 be satisfied by adding a second API alongside A? **No**: the planner selects exactly one physical path per aggregation node (`shouldPlanOrderedAggregate` true/false); leaving N replicated instances intact while adding a fused operator forks the plan shape and doubles the ordered-stream buffering that step 2's constraint forbids. **P6 PASS** (this is P6 candidate #1; see merge M1).

Determinism seam: `NO SEAM` needed for values (ordered input, no clock); group-boundary determinism rides on the existing single-goroutine `Callback`/`Finish` contract. No wall-clock/concurrency/network.

Size: 2–3 files (`aggregate.go`, `ordered_aggregate.go`, `physicalplan.go`), ~120–200 net lines honestly (multi-builder Finish merge is the bulk).

Motivating caller: any `GROUP BY ts, sum(bytes), max(bytes)` telemetry query on a duration-ordered FrostDB table (the Parca/parquet-tool use case in-repo at `cmd/parquet-tool`); today it silently falls back to hash aggregation and loses the streaming bound.

---

## S2 — `Avg` is an enum value with no execution behind it

Subsystem/files: `query/` — `query/logicalplan/expr.go:718-750`, `query/physicalplan/aggregate.go:81-101,955-971`, `query/exprpb/proto.go:190-201,566-577`.

Axis: **AXIS 19**.

HEAD TODAY: HEAD parses/names `avg` but refuses to execute it. `query/logicalplan/expr.go:726` declares `AggFuncAvg`; `query/physicalplan/aggregate.go:85-100` `chooseAggregationFunction` switches `Sum/Min/Max/Count/Unique/And` and `default: return nil, fmt.Errorf("unsupported aggregation function: %s", ...)`. `Avg` falls into default. Behaviour (avg execution) **not implemented**. Note `resultNameWithConcreteColumn` at `aggregate.go:983-984` already maps `AggFuncAvg`, so the naming half is written and the execution half is refused — classic AXIS 19 shape.

Nearest presence: `func Avg(expr Expr) *AggregationFunction` at `expr.go:794` (constructor exists) plus `validate.go:278` accepting `AggFuncAvg` as valid. Covers validation/naming; fails to cover `Aggregate()`/`runAggregation()` execution (including final-stage count/sum recombination).

Fork: A = rewrite avg as `sum/count` pair in the logical planner (desugar before physical planning). B = native `AvgAggregation` physical operator carrying (sum,count) state per group with final-stage merge. Cold model predicts **A** (least code, uses existing `Sum`/`Count`). `FORK: strong`.

Observable: `SELECT avg(x) ... GROUP BY y` through `Engine.Query`, asserting per-group averages including empty-group NULL and final-stage (multi-source `Synchronizer`) merges. A-vs-B differ on result-column naming (`avg(x)` vs `sum/count` internals leaking), NULL semantics, and overflow behaviour. Gradeable.

Vocabulary (5): `Avg` IN-BASE (`expr.go:794`); `AggFunc` IN-BASE (`expr.go:718`); `runAggregation` IN-BASE (`aggregate.go:955`); `finalStage` IN-BASE (`aggregate.go:124`); `average-state` COINED. 4/5.

P6 answers: (1) delete step 1 (avg works at all)? Step 2 grader (e.g. NULL/merge-correct avg) passes trivially on error paths — **no cascade if step 2 is just "correct avg"**. As a standalone surface it is build-then-use, not P6. (2) parallel API? Yes — a desugared path can coexist with a native path. **P6 FAIL**; keep as single-turn capability surface.

Determinism seam: NO SEAM (pure arithmetic over ordered/hash groups).

Size: 2–3 files, ~80–130 lines.

Motivating caller: SQL surface — `sqlparse/visitor.go:209` already lowers SQL `AVG` to `logicalplan.Avg`; any SQL `SELECT AVG(...)` query is the caller and today errors at execution.

---

## S3 — List comparisons panic in the scalar-expression dispatch

Subsystem/files: `query/` — `query/physicalplan/binaryscalarexpr.go:84-117`.

Axis: **AXIS 19**.

HEAD TODAY: explicit panic guard. `query/physicalplan/binaryscalarexpr.go:112-114`:
> `switch leftType.(type) { case *arrow.ListType: panic("TODO: list comparisons unimplemented") }`
Behaviour (filter on a list column) **not implemented** — it panics rather than returning an error.

Nearest presence: the two lines above it, `query/physicalplan/binaryscalarexpr.go:97-109` handling `*array.Dictionary` for `OpEq/OpNotEq` and erroring `unsupported operator` otherwise; plus `ArrayScalarContains` at `:234` handling Binary/String. Neighbour covers scalar-vs-flat-column; fails to cover repeated/list columns.

Fork: A = deep element-wise list comparison (per-row `ListSlice` compare). B = reject lists with a typed `ErrUnsupported...` error propagated through `Eval` instead of panic (no new semantics, just a safe refusal). Cold model predicts **B-ish but keeps panic** — actually cold model most likely writes A badly (compares offsets, not values). `FORK: weak` (B is arguably just hygiene) — kept per instructions.

Observable: `Table.Scan` / engine filter `WHERE list_col = <scalar>` or `Eval` on a record with a `ListType` column; assert: returns typed error (B) vs row bitmap (A) vs panic (HEAD). Gradeable via `require.NotPanics` + error assertion.

Vocabulary (5): `BinaryScalarExpr` IN-BASE (`:35`); `Eval` IN-BASE (`:41`); `Bitmap` IN-BASE; `OpEq` IN-BASE (`logicalplan`); `list-comparison` COINED. 4/5.

P6: (1) deleting step 1 (safe refusal), step 2 grader (element semantics) still fails at HEAD — but it fails by panic either way, so no cascade. **FAIL**. (2) parallel API trivially possible. Not P6.

Determinism seam: NO SEAM.

Size: 1–2 files, ~40–80 lines.

Motivating caller: parquet-tool `find` on repeated columns; today a user filter on a list column crashes the process instead of erroring.

---

## S4 — `MergeRecords` type-switch panics on unlisted Arrow types

Subsystem/files: `pqarrow/` — `pqarrow/arrowutils/merge.go:116-172`.

Axis: **AXIS 19**.

HEAD TODAY: closed dispatch. `pqarrow/arrowutils/merge.go:169-170`:
> `default: panic(fmt.Sprintf("unsupported type for record merging %T", arr1))`
with only Binary/String/Int64/Int32/Uint64/Dictionary-binary covered at `:120-168`. Float64, Bool, Timestamp, Duration, List, Struct **panic**. Behaviour (merge on those types) **not implemented**.

Nearest presence: `pqarrow/arrowutils/sort.go:442-497` `newMultiColSorter`, which covers *more* types (Float64, Timestamp, dictionary-string/binary/fixed-size-binary) but errors instead of panicking. Neighbour proves the comparison primitives exist; merge fails to wire them.

Fork: A = extend the `compare` switch case-by-case (float64, bool, timestamp...). B = route merge comparison through the shared `comparator`/`orderedSorter` abstraction used by sort (deduplicate). Cold model predicts **A** (copy-paste cases). `FORK: strong` (B is a real refactor fork).

Observable: `MergeRecords(mem, records-with-float64-col, orderByCols, limit)` — A/B return ordered record; HEAD panics. Gradeable.

Vocabulary (4): `MergeRecords` IN-BASE (`merge.go:23`); `SortingColumn` IN-BASE (`sort.go:42`); `cursorHeap` IN-BASE (`merge.go:75`); `float-merge` COINED. 3/4.

P6: (1) no cascade alone. (2) parallel API possible (new function). Not P6.

Determinism seam: NO SEAM (pure order); determinism via fixed input records.

Size: 1–2 files, ~80–150 lines.

Motivating caller: `LIMIT`-with-`ORDER BY float_col` queries merging per-source records (`pqarrow` merge is on the distributed-query path); float metrics are the common case.

---

## S5 — `SortRecord` refuses types its sibling already compares

Subsystem/files: `pqarrow/` — `pqarrow/arrowutils/sort.go:442-497`, `groupranges.go:199-202`, `pqarrow/arrow.go:1091-1119`.

Axis: **AXIS 19**.

HEAD TODAY: explicit refusal. `pqarrow/arrowutils/sort.go:494-496`:
> `default: ms.Release(); return nil, fmt.Errorf("unsupported column type for sorting %T for column %s", e, r.Schema().Field(col.Index).Name)`
Bool, Float32, Duration, List, Struct, RunEndEncoded error out. Behaviour **not implemented** for those types.

Nearest presence: same-file dictionary coverage at `:464-493` and `Take*` helpers at `:141-364` (`TakeDictColumn`, `TakeListColumn`, `TakeStructColumn`) proving the engine can already materialise those columns. Covers take; fails to cover order-compare.

Fork: A = add per-type cases to `newMultiColSorter`. B = generic `cmp.Ordered`-based fallback plus null-placement reuse. Cold model predicts **A**. `FORK: weak` (B is A with generics; both add cases) — kept.

Observable: `SortRecord(record-with-bool-col, ...)` returns sorted indices vs error. Gradeable.

Vocabulary (4): `SortRecord` IN-BASE (`:54`); `SortingColumn` IN-BASE; `Direction` IN-BASE (`:23`); `bool-sort-key` COINED. 3/4.

P6: FAIL (same reasoning as S4). Narrow-then-widen merge partner with S4 (see M2).

Determinism seam: NO SEAM; stable-sort question is S8-adjacent but this surface asserts only correctness of order, ties broken arbitrarily and asserted as sets.

Size: 1 file, ~60–100 lines.

Motivating caller: `ORDER BY` over boolean/status or duration columns from SQL (`sqlparse`); parity with the merge path.

---

## S6 — Dictionary scalar filter supports only `=` / `!=`

Subsystem/files: `query/` — `query/physicalplan/binaryscalarexpr.go:99-109`, `query/expr/binaryscalarexpr.go`.

Axis: **AXIS 19**.

HEAD TODAY: guard refuses ordering predicates on dictionaries. `query/physicalplan/binaryscalarexpr.go:100-108`:
> `case *array.Dictionary: switch operator { case logicalplan.OpEq: return DictionaryArrayScalarEqual(...); case logicalplan.OpNotEq: return DictionaryArrayScalarNotEqual(...); default: return nil, fmt.Errorf("unsupported operator: %v", operator) }`
Range/regex/contains on dictionary columns **not implemented** (equality only).

Nearest presence: `DictionaryArrayScalarContains` at `:271` — the contains implementation for dictionaries **already exists** but is reachable only via `OpContains/OpNotContains` at `:90-91`, not via `<,<=,>,>=`. Neighbour proves dictionary iteration exists; fails to cover ordered comparison.

Fork: A = decode-per-row and compare against scalar (simple, allocates). B = binary-search the dictionary values once, map predicate to index-range, then bitmap over codes (no per-row decode). Cold model predicts **A**. `FORK: strong`.

Observable: filter `dict_col > "m"` through `BinaryScalarOperation`/`Table.Scan`; assert bitmap. A-vs-B identical results (speed-only difference) → per instructions, if graded on bitmap alone both pass; the discriminating observable must be allocation/span behaviour — I mark the A-vs-B *performance* facet `UNGRADEABLE`, but the surface itself (HEAD errors → works) is gradeable as a capability. Kept as capability, fork labelled strong-but-perf-only.

Vocabulary (5): `DictionaryArrayScalarEqual` IN-BASE (`:194`); `OpGt` IN-BASE; `Bitmap` IN-BASE; `ArrayRef` IN-BASE (`:18`); `range-on-dictionary` COINED. 4/5.

P6: FAIL (additive capability).

Determinism seam: NO SEAM.

Size: 1–2 files, ~80–120 lines.

Motivating caller: label-column range filters (`service > "m"`) on dictionary-encoded parquet columns — the dominant FrostDB label shape.

---

## S7 — LSM `Scan` consumes without a neutral preview (observer non-interference)

Subsystem/files: `index/` — `index/lsm.go:395-454` (`Iterate`, `Scan`).

Axis: **AXIS 10**.

HEAD TODAY: every inspection path hands out retained references or runs the filter. `index/lsm.go:401`:
> `func (l *LSM) Scan(ctx context.Context, _ string, _ *dynparquet.Schema, filter logicalplan.Expr, tx uint64, callback func(context.Context, any) error) error`
and inside, `lsm.go:420-425` (`r.Retain(); callback(ctx, r)`) and `lsm.go:444-445` (`node.part.Retain(); callback(ctx, &releaseableRowGroup{...})`). There is no `Peek`/`Inspect`/`Estimate`/`Explain` — the verified hand-noted neighbour `index.LSM.Scan` is the *only* way to learn what a scan would touch. Stating "no preview exists" from this neighbour: the file's method set is `Size, LevelSize, Snapshot, Add, InsertPart, String, Prefixes, Iterate, Scan, findLevel, findNode, EnsureCompaction, Rotate, merge, compact` — no neutral inspector. Behaviour (preview) **not implemented**.

Nearest presence: `func (l *LSM) Size() int64` at `lsm.go:241` and `LevelSize` at `:250` — global byte counters; plus `Iterate` at `:395` exposing raw `*Node`s under RLock. Covers coarse accounting / raw access; fails to cover per-scan, filter-aware, snapshot-neutral estimation (which parts/row-groups at `tx` would match, without retaining or invoking `callback`).

Fork: A = `Estimate(ctx, filter, tx) (parts, rowGroups, bytes)` that evaluates `booleanFilter.Eval` but never retains/calls back. B = `Inspect(ctx, filter, tx, func(part TX, size, level))` visitor with the same traversal but a different callback shape. Cold model predicts **B** (visitor mirrors `Scan`). `FORK: weak` (same traversal, different signature) — kept.

Observable: call `Estimate`/`Inspect` then call `Scan` with identical `(filter, tx)`; assert (i) preview counts equal actual matched parts/row-groups, (ii) a subsequent `Scan` returns identical rows as a `Scan` with no preceding preview (non-interference: no double-retain, no skipped parts, refcounts balanced — assert via `Size()` stability and row equality). Gradeable through existing `LSM` + `Scan`.

Vocabulary (6): `LSM` IN-BASE (`lsm.go:43`); `Scan` IN-BASE (`:401`); `tx` IN-BASE (param); `filter` as `logicalplan.Expr` IN-BASE; `callback` IN-BASE; `estimate` COINED. 5/6.

P6: FAIL (pure addition; preview alongside Scan is the textbook parallel API).

Determinism seam: explicit `tx uint64` is the seam — pin `tx`, single-threaded, no clock. No wall-clock/network/concurrency needed.

Size: 1 file, ~80–120 lines.

Motivating caller: query planner / `AggFuncPushDown` + UI `EXPLAIN` path: needs row-group shortlist cardinality before committing to a full scan; today the only way to know is to run it.

---

## S8 — Sampler unified-schema build uses a total alphabetical sort (canonical order) [P6 #1, step 1]

Subsystem/files: `query/` — `query/physicalplan/sampler.go:228-289` (`materialize`).

Axis: **AXIS 13**.

HEAD TODAY: total sort. `query/physicalplan/sampler.go:244-254`:
> `// Sort the fields alphabetically` + `slices.SortFunc(fields, func(i, j arrow.Field) int { ... })`
Behaviour (deterministic unified schema) **is implemented** — kept anyway per instructions; the surface is about *which* canonical order.

Nearest presence: the dedup loop just above at `sampler.go:234-242` collecting `fields` in reservoir-encounter order (`added` map guards first-seen). Neighbour preserves encounter order right up until the sort discards it; fails to cover stability among dynamically-discovered (mutually incomparable) columns.

Fork: A (HEAD/step 1) = alphabetical total sort at materialize. B = first-seen (encounter) order for all fields, or: sorted known-schema prefix + first-seen dynamic suffix. Cold model writes **A cold** (alphabetical is the idiomatic "deterministic schema" answer in Go). `FORK: strong` for step 1 as the thing-to-tear-out. P6 precondition holds: A is eager/unconditional/materialise-everything (builds the whole unified record eagerly at the size limit).

Observable: reservoir over records with disjoint dynamic columns (e.g. record1 has `zeta`, record2 has `alpha`), force `materialize` via small `sizeLimit`, assert output schema field order through `Finish`→`next.Callback` records. A yields `[alpha, zeta]`; B yields `[zeta, alpha]` (encounter order). Gradeable through existing `NewReservoirSampler` + `Callback`/`Finish`.

Vocabulary (5): `ReservoirSampler` IN-BASE (`:18`); `materialize` IN-BASE (`:229`); `Finish` IN-BASE (`:201`); `RecordBuilder` (arrow) IN-BASE-via-import; `encounter-order` COINED. 4/5.

P6 answers: (1) HEAD counterfactual — delete step 1 (the materialize-with-unified-schema artifact entirely): could step 2's grader (order constraint on the unified record) still pass? **No** — without step 1 there is no unified record at all; downstream `Finish` emits per-slice records and the order assertion is vacuous. Cascade real. (2) Parallel-API — add `MaterializeEncounterOrdered` alongside? **No**: `Finish` consumes `s.reservoir` in place; two coexisting orderings fork the record schema handed to `next.Callback` and every downstream operator (`HashAggregate` matches by field name, `Take` by index). The constraint must rework the one path. **P6 PASS**.

Determinism seam: deterministic with fixed `size`/`sizeLimit` and single-goroutine `Callback` sequence; randomness in `sample()` is out of scope if the test fills then materializes without replacement sampling (or seeds `rand`). No clock/network.

Size: 1 file, ~40–70 lines for the order change (step 2); step 1 (if built fresh) ~80–120.

Motivating caller: downstream column-index-sensitive consumers (`Take`, `writeColumnToArray`, parquet writers) and snapshot-stable schema evolution: encounter order is append-stable across ingests while alphabetical renames positions on every new label.

---

## S9 — `MergeRecords` null placement ignores direction (half of the WARNING is still true)

Subsystem/files: `pqarrow/` — `pqarrow/arrowutils/merge.go:22,84-114`, `pqarrow/arrowutils/sort.go:553-584`.

Axis: **AXIS 13**.

HEAD TODAY: split behaviour. `pqarrow/arrowutils/merge.go:22`:
> `// WARNING: Only ascending ordering is currently supported.`
Verification: value path at `merge.go:100-108` DOES consult direction (`return cmp == h.orderByCols[idx].Direction.comparison()`), so ascending-only is **stale for values**. Null path at `merge.go:91-98`:
> `if cmp, ok := nullComparison(...); ok { if h.orderByCols[idx].NullsFirst { return cmp == -1 }; if !h.orderByCols[idx].NullsFirst { return cmp == 1 } }`
does NOT consult `Direction` — descending+`NullsFirst` misplaces nulls. So the warning is **partially true** (true for the null-ordering half). Compare the correct sibling `sort.go:553-584` `multiColSorter.compare`, which folds `nullsFirst` and `directions` together.

Nearest presence: `sort.go:536-551` `Less` + `compare` handling both direction and nulls; merge's `Less` handles direction only for non-null. Covers in-memory sort; fails to cover cross-record merge.

Fork: A = thread `Direction` into the null branch (`nullsFirst XOR descending`). B = reuse one shared `nullPlacement(direction, nullsFirst)` helper between sort and merge. Cold model predicts **A** (local edit). `FORK: weak` — kept.

Observable: `MergeRecords` with `SortingColumn{Direction: Descending, NullsFirst: true/false}` over records with nulls in the key; assert null row positions vs `SortRecord` on the concatenated equivalent. Gradeable.

Vocabulary (5): `MergeRecords` IN-BASE; `SortingColumn` IN-BASE; `Direction` IN-BASE; `NullsFirst` IN-BASE (`sort.go:45`); `null-placement` COINED. 4/5.

P6: FAIL alone (bug fix, single step). Pairs with S4/S5 as narrow-then-widen (M2).

Determinism seam: NO SEAM (fixed inputs, no clock).

Size: 1 file, ~15–40 lines.

Motivating caller: `ORDER BY x DESC NULLS FIRST/LAST` with `LIMIT` over multiple sources — merge is the distributed-limit path; wrong null placement returns wrong limited rows.

---

## S10 — Ordered aggregate silently assumes its input ordering (observe-then-enforce hook)

Subsystem/files: `query/` — `query/physicalplan/ordered_aggregate.go:163-411`, `query/physicalplan/planordering.go:17-63`.

Axis: **AXIS 10** (observer) with AXIS 19 flavour; I file it under AXIS 10.

HEAD TODAY: no verification, no explanation. `OrderedAggregate.Callback` at `:163` ingests records and tracks `curGroup`/`groupBuilders` with no ordering assertion; `planOrderingInfo.orderingMaintained()` at `planordering.go:61-63` is a planner-side boolean, never re-checked at runtime. A mis-planned (unordered) input produces silently wrong aggregates. No `Explain`/`ValidateOrdering` exists.

Nearest presence: `Draw()` at `ordered_aggregate.go:144-161` (`"OrderedAggregate (%s by %s)"`) — a static label, not a runtime check; and `getNonCoveringOrdering` at `planordering.go:115-117`. Covers naming the expectation; fails to cover verifying it per record without consuming/altering results.

Fork: A = per-`Callback` cheap boundary check (first row vs `curGroup`, error on regression). B = standalone `ExplainOrdering(record) bool` inspector the engine calls before/after without touching operator state. Cold model predicts **A** (inline `if`). `FORK: weak` — kept.

Observable: feed an unordered record to `OrderedAggregate` via `Callback`; assert typed error (A) / false-from-inspector (B) vs silent wrong sums (HEAD). Then feed ordered input and assert results identical with the check enabled (non-interference). Gradeable via existing `NewOrderedAggregate`.

Vocabulary (5): `OrderedAggregate` IN-BASE; `Callback` IN-BASE; `curGroup` IN-BASE (`:66`); `Draw` IN-BASE; `ordering-check` COINED. 4/5.

P6: FAIL (additive guard).

Determinism seam: NO SEAM; single-goroutine callbacks.

Size: 1–2 files, ~60–100 lines.

Motivating caller: the planner's `filterCoverIdx`/partial-order logic (`planordering.go:82-113`) is subtle; a runtime guard turns silent corruption into a plannable error, unblocking `orderedAggregations` being enabled by default.

---

## S11 — Projected-column aggregation is admitted wrong (brancz TODO)

Subsystem/files: `query/` — `query/physicalplan/aggregate.go:33-36`, `query/physicalplan/project.go`, `query/logicalplan/expr.go`.

Axis: **UNLENSED CONTROL #1**.

HEAD TODAY: admitted incorrect. `query/physicalplan/aggregate.go:33-36`:
> `// TODO(brancz): This is not correct, it doesn't handle aggregations correctly of previously projected columns like sum(value + timestamp). Need to understand why we need to handle dynamic columns here differently and not just use the aggregation funciton's expression.`
Behaviour (correct `sum(expr)` over projections) **not implemented**; still true at HEAD (the loop at `:37-52` matches only `DynamicColumn` and stores `expr.Expr` raw).

Nearest presence: `HashAggregate.Callback` column matching at `aggregate.go:337-360` (`col.expr.MatchColumn(field.Name)`) — works when the agg expr is a bare column; fails when it is `value + timestamp` or any computed projection (matches the wrong field or none, silently aggregating the wrong array).

Fork: A = evaluate the scalar/projected expression per record into a temp array, then aggregate the temp. B = rewrite the plan to insert a `Project` node before the aggregate so the aggregate always sees a materialised column. Cold model predicts **A** (local temp in Callback). `FORK: strong`.

Observable: `SELECT sum(value + timestamp)` (or logical plan `Sum(BinaryExpr(...))`) through engine; assert per-group sums vs hand-computed. HEAD returns wrong values or `aggregate field(s) not found`. Gradeable.

Vocabulary (5): `HashAggregate` IN-BASE; `Callback` IN-BASE; `Aggregation` IN-BASE; `DynamicColumn` IN-BASE; `projection-eval` COINED. 4/5.

P6: (1) no cascade alone. (2) parallel API possible. Not P6. (Bug-fix shape: counts toward the ≤1/3 bug budget.)

Determinism seam: NO SEAM.

Size: 2–3 files, ~100–160 lines.

Motivating caller: SQL arithmetic aggregates — `SELECT sum(a+b)` is elementary SQL; the SQL layer (`sqlparse`) can already parse the expression, execution silently miscomputes it.

---

## S12 — Sampler `materialize` indexes the wrong record's columns (disparate-schema TODO + index bug)

Subsystem/files: `query/` — `query/physicalplan/sampler.go:228-289`.

Axis: **UNLENSED CONTROL #2**.

HEAD TODAY: TODO plus wrong index. `query/physicalplan/sampler.go:262`:
> `for i, f := range bldr.Fields() { // TODO handle disparate schemas`
and inside, `:264-270`: the miss branch appends null (fine), but the hit branch does `builder.AppendValue(f, r.ref.Column(i), int(r.i))` — `i` is the **unified-builder** index, not the position of `schema.Field(i).Name` inside `r.ref`'s own schema. With disparate schemas the wrong column (or an out-of-range column) is sampled. Behaviour (correct disparate-schema materialize) **not implemented**; still true at HEAD.

Nearest presence: the `added`/dedup schema-union loop at `:231-242` correctly unions by **name** (`schema.HasField(...)`); the copy loop below switches to **positional** `Column(i)`. Neighbour proves name-based lookup was understood; the copy fails to use it.

Fork: A = per-row `FieldIndices(name)` lookup in the source record. B = precompute per-reservoir-entry index-remap arrays once, then copy positionally. Cold model predicts **A** (direct lookup). `FORK: weak` (perf-only difference) — kept; the graded fix is identical.

Observable: two records with different column sets sharing one name with different positions (e.g. rec1 `(a,b)`, rec2 `(b,a)` or disjoint `(a,x)`/`(b,x)`), small `sizeLimit` to force `materialize`, assert sampled values per column name through `Finish`. HEAD swaps/misattributes values. Gradeable.

Vocabulary (5): `materialize` IN-BASE; `reservoir` IN-BASE (`:31`); `RecordBuilder` IN-BASE-via-import; `Schema` IN-BASE; `remap` COINED. 4/5.

P6: FAIL alone (bug fix). Composes with S8 (same function, see M3).

Determinism seam: single-goroutine `Callback` order is the seam; pin record order, no clock.

Size: 1 file, ~30–60 lines.

Motivating caller: dynamic-label sampling (the sampler exists for profiles with per-row label sets); disparate schemas are its normal input, not an edge case.

---

## S13 — Sentinel lookup is O(n) per insert (admitted, not compaction)

Subsystem/files: `index/` — `index/lsm.go:470-482`, `index/list.go` (`Node`, `Sentinel`).

Axis: **UNLENSED CONTROL #3**.

HEAD TODAY: admitted linear. `index/lsm.go:470`:
> `// TODO: this should be changed to just retain the sentinel nodes in the lsm struct to do an O(1) lookup.`
`findLevel` at `:471-482` iterates the whole part list per call; `InsertPart` at `:357-379` calls `findLevel`. Behaviour (O(1) level access) **not implemented**; still true. (Not compaction/level-accounting framing — excluded is the *picking/sizing* framing; this is a data-structure lookup. `index/` remains live per the brief.)

Nearest presence: `lsm.partList.Sentinel(...)` construction at `lsm.go:155-157` and `NewList(L0)` at `:131` — sentinels are created once and stable; `findNode` at `:485-496` is the same linear pattern. Covers stability (safe to retain pointers); fails to cover retaining them.

Fork: A = `sentinels [N]*Node` array on `LSM`, populated at construction. B = `map[SentinelType]*Node`. Cold model predicts **B** (Go-idiomatic map). `FORK: weak` — kept (perf-only; mark `UNGRADEABLE` on speed, gradeable only on behavioural equivalence + pointer stability across inserts/compactions).

Observable: behavioural equivalence only (`InsertPart`/`Scan`/`String` identical, `findLevel` unexported so assert through `InsertPart` + `LevelSize` + `String`). Speed-only difference → the *fork choice* is UNGRADEABLE as a race; the surface is a refactor, not a task by itself. Honestly parked (see merge table: `parked-single-turn` at best, likely dropped).

Vocabulary (4): `LSM` IN-BASE; `SentinelType` IN-BASE; `InsertPart` IN-BASE; `sentinel-cache` COINED. 3/4.

P6: FAIL. (Also a Go-prior risk: maps/slices are idiomatic; no cascade.)

Determinism seam: NO SEAM (single-threaded construction; lock discipline unchanged).

Size: 1–2 files, ~30–50 lines.

Motivating caller: `NO CALLER` for graded behaviour (no observable change by design). Operational motive only (recovery inserts N parts × O(N) walk). I keep it as the required unlensed control and mark it accordingly.

---

## S14 — Single-sink refusal in `Persist` (multi-destination fan-out)

Subsystem/files: repo-root — `store.go:29-62`, `db.go` (`sinks`), `table.go` (`writeBlock`, `RotateBlock`).

Axis: **AXIS 19**.

HEAD TODAY: explicit refusal. `store.go:35-38`:
> `for i, sink := range t.table.db.sinks { if i > 0 { return fmt.Errorf("multiple sinks not supported") }`
Multi-sink persist **not implemented**; still true at HEAD. Note the loop already iterates `sinks` — the plural field exists, the writer does not.

Nearest presence: `DefaultObjstoreBucket` (`store.go:65-71`) implementing the sink interface, plus `t.Serialize(w)` at `:43` proving serialisation is sink-agnostic. Covers one sink; fails to cover fan-out (one serialisation → N uploads, partial-failure semantics).

Fork: A = serialize once to bytes, upload to each sink sequentially (simple, 2× memory). B = `io.Pipe`/`io.MultiWriter` fan-out streaming to N sinks in one pass with per-sink error aggregation. Cold model predicts **A** (read-all-then-loop). `FORK: strong`.

Observable: configure `db.sinks = [sinkA, sinkB]`, `Persist()` a block, assert both sinks hold `data.parquet` with identical bytes; then fail sinkB and assert error contract (A-vs-B differ on atomicity/cleanup: `Delete` on error exists at `:53-55` for one sink; multi-sink needs per-sink cleanup). Gradeable without network (in-memory `objstore.Bucket` fakes).

Vocabulary (5): `Persist` IN-BASE (`store.go:30`); `sinks` IN-BASE (`db.go`); `Serialize` IN-BASE; `Upload` IN-BASE-via-interface; `fan-out` COINED. 4/5.

P6 answers: (1) delete step 1 (second sink works)? Step 2 grader (failure-atomicity across sinks) vacuous without two sinks. Real cascade only if step 2's constraint (bounded memory / streaming, no full buffering) forces removal of A's buffer — that is a genuine revert-and-redo: A buffers the whole block, B streams. (2) parallel API? A second `PersistFanout` alongside `Persist` is possible, but the block-rotation caller (`RotateBlock`/`writeBlock`) calls one path — leaving both means two serialisations per rotation, violating the streaming constraint. **P6 PASS** (P6 candidate #2; see M3). P6 precondition holds: A is materialise-everything (buffer whole block).

Determinism seam: in-memory bucket fakes; inject failing-sink stub. No wall-clock; concurrency only inside B (errgroup), testable single-threaded via sequential variant. No real network.

Size: 1–2 files, ~80–140 lines.

Motivating caller: dual-write migrations (local FS + object store) and backup-to-second-bucket during rotation; today the second sink is a hard error.

---

## S15 — `AggFuncPushDown` dies on any intermediate node (planner TODO)

Subsystem/files: `query/` — `query/logicalplan/optimize.go:159-193`, `query/expr/filter.go`, `pqarrow/arrow.go:723` region.

Axis: **AXIS 19** (planner avoids the physical optimisation because the case is refused).

HEAD TODAY: bail-out. `query/logicalplan/optimize.go:184-187`:
> `default: // If we find anything other than a table scan after a global aggregation, bail out by setting the filterExpr to nil.`
plus `query/logicalplan/optimize.go:181`:
> `// TODO(asubiotto): Should we make this less specific?`
So `max(x)` pushes only through the exact shape `Aggregation→TableScan`; `Aggregation→Filter→TableScan`, `→Project→`, `→Sort→` silently lose the pushdown. Behaviour (pushdown through projections/filters) **not implemented**; still true.

Nearest presence: the carried case at `:175-178` (`plan.TableScan != nil → plan.TableScan.Filter = filterExpr`) and `TestAggFuncPushDown` at `optimize_test.go:198` covering the single-hop shape. Covers one hop; fails to cover pass-through nodes that preserve the agg's column.

Fork: A = allowlist of pass-through node types (Project with identity mapping, Filter, Sort, Limit) that forward `filterExpr`. B = general dataflow analysis: propagate iff all `ColumnsUsedExprs` of intermediate nodes are subset-preserving for the agg column. Cold model predicts **A** (case list). `FORK: strong`.

Observable: build logical plans `Max→Project→Scan` / `Max→Filter→Scan`, run `(&AggFuncPushDown{}).Optimize`, assert `TableScan.Filter` is set (B/A) vs nil (HEAD). Gradeable as a pure planner unit test — no engine, no I/O.

Vocabulary (5): `AggFuncPushDown` IN-BASE (`:166`); `Optimize` IN-BASE (`:168`); `TableScan` IN-BASE; `Filter` IN-BASE; `pass-through` COINED. 4/5.

P6: FAIL (additive widening; parallel planner rule could coexist).

Determinism seam: NO SEAM (pure plan rewrite).

Size: 1–2 files, ~60–100 lines.

Motivating caller: `SELECT max(duration)` with a `WHERE`/`SELECT`-project wrapper — the max-memoized row-group skipping described in the optimizer's own doc comment (`:162-165`) never fires for real SQL shapes.

---

### Shape audit (required mix)

- Count: 15 surfaces. Net-new capability (not defect fix): S1, S2, S4, S5, S6, S7, S10, S14, S15 = 9/15 (≥1/3 ✓).
- Bug-fix ("HEAD has a bug"): S9, S11, S12 = 3/15 (≤1/3 ✓). S13 is a refactor, S3/S8 are capability/order-change.
- Genuine P6 passing both tests: S8, S14 (2 ✓).
- UNLENSED controls: S11, S12, S13 (3 ✓). The unlensed ones are not the best — S1/S2/S8/S14 carry the strongest extension-point receipts — but S11/S12 are the most *gradeable* bugs in the survey (admitted + wrong results, not just missing code).

---

## MERGE PASS

| Surface | Disposition | Reason |
|---|---|---|
| S1 ordered multi-agg | **merged → M1** (step 1) | needs a second aggregation semantic to share the ordered path with; pairs with S2 |
| S2 avg execution | **merged → M1** (step 2) | the concrete second function that forces S1's single-`Aggregation` struct open; narrow (one agg) → widen (avg through the new vector path) |
| S3 list panic | dropped | safe-refusal hygiene; no partner needs it; single-turn at best |
| S4 merge types | **merged → M2** (step 1) | establishes the shared-comparison seam on the merge path |
| S5 sort types | **merged → M2** (step 2) | widens the same seam to the sort path; tension is dedup-vs-duplication |
| S6 dict ranges | parked-single-turn | strong capability but no related surface shares its bitmap mechanism; no tension partner |
| S7 LSM preview | parked-single-turn | good AXIS 10 single-turn (preview + non-interference assertions); no partner |
| S8 sampler order | **merged → M3** (step 1) | builds the materialize artifact that S12's fix and the order constraint both require |
| S9 merge nulls×direction | **merged → M2** (step 3, optional) | enforces direction-aware nulls on top of M2's unified comparator |
| S10 ordered-guard | parked-single-turn | good observe-then-enforce single; no cascade tension |
| S11 projected-col agg | parked-single-turn | best standalone bug-fix task; self-contained, no partner |
| S12 disparate-schema index | **merged → M3** (step 2) | cannot be correctly fixed without S8's unified-schema artifact; build-then-use inside a P6 shell |
| S13 sentinel cache | dropped | UNGRADEABLE fork (speed-only), NO CALLER; keeping it would fab­ricate a task |
| S14 multi-sink | merged → M4 (alternate P6) | genuine P6 but shares no files with M1–M3; kept as standby, not primary |
| S15 pushdown widen | parked-single-turn | clean planner unit-task; no partner |

### M1 — Ordered multi-aggregation carrying `avg` (S1 + S2; build-then-use / narrow-then-widen)

- Step 1 requirement: plan and execute ≥2 aggregations (`sum`, `max`) in one `OrderedAggregate` pass over ordered input; `shouldPlanOrderedAggregate` no longer bails on `len(AggExprs)>1`, and the refusal error at `aggregate.go:56-58` is gone.
- Step 2 requirement: `avg` executes through the same fused ordered path (including final-stage merge), with NULL/empty-group semantics.
- Compositional invariant per step: S1 — one shared group-boundary stream yields N per-group result columns; S2 — the N-column contract extends to a function whose state is a pair.
- **Tension in one sentence:** step 1 fuses N independent aggregations into one boundary detector to avoid N passes, while step 2's `avg` cannot be fused as an independent value stream at all and forces the fused carrier to hold composite (sum,count) state with different final-stage recombination.
- Interface Contract (symbols not already in base):

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| `OrderedAggregate.Aggregations []Aggregation` (field; replaces singular `aggregationFunction`/`columnToAggregate`) | field | `[]Aggregation` on existing struct | STATED (graded via `NewOrderedAggregate` variadic/slice constructor or `Draw()` showing N names) | PINNED to constructor shape chosen by task; synonyms not accepted for the field name but `Draw()` text is accepted as the observable instead |
| `NewOrderedAggregateMulti` or slice-taking `NewOrderedAggregate` | func | `func(pool, tracer, []Aggregation, []Expr, bool) *OrderedAggregate` | STATED | accepted synonyms: `NewOrderedMultiAggregate` |
| `Avg` ordered final-stage recombination (sum-of-sums / sum-of-counts) | behaviour | observable via result values only, no new symbol | IN-BASE values (`avg(x)` name already at `expr.go:794`) | n/a |

- Named wrong shape: **N side-by-side single-agg operators + `avg` desugared to `sum/count` in the planner** — because `NewOrderedAggregate` takes one `Aggregation` today and `Sum`/`Count` already execute, the laziest correct-looking diff replicates the struct and rewrites the expression, which passes single-record tests but diverges on partial-order multi-set merges and leaks `sum/count` column names.
- Why it would: the shipped primitive (`NewOrderedAggregate` singular) and the adjacent Go idiom (fan-out slice of operators sharing `next`) both point at replication; the requirement's "one pass" reading is easy to misread as "one scan feeding N operators".
- Inter-step file overlap: step 1 touches `aggregate.go`, `ordered_aggregate.go`, `physicalplan.go`; step 2 touches `ordered_aggregate.go` (state carriers), `aggregate.go` (`chooseAggregationFunction`/`runAggregation`) incrementally on step 1, cumulative from base otherwise.
- What step 2 cannot compute without step 1's artifact: the `avg` final-stage merge over ordered sets needs the fused multi-column ordered-set bookkeeping (`groupResults`/`aggregationResults` per set); without step 1 there is no multi-set ordered carrier to attach composite state to — in one sentence: no fused boundary detector, nowhere to hang (sum,count) pairs across ordered sets.

### M2 — One comparison seam for sort + merge, then direction-aware nulls (S4 + S5 + S9; narrow-then-widen + observe-then-enforce)

- Step 1 requirement: `MergeRecords` handles the widened scalar type set (float64/bool/timestamp at minimum) with ascending + both null placements correct.
- Step 2 requirement: `SortRecord` handles the same widened set, with merge-vs-sort agreement on identical inputs (cross-oracle test).
- Step 3 (optional) requirement: descending + `NullsFirst` combinations agree between merge and sort (fixes S9).
- Invariants: S1 — merge order equals sort order on the widened types; S2 — the widened comparison lives in one shared helper, not two switches; S3 — null placement is a pure function of `(direction, nullsFirst)`.
- **Tension:** step 1–2 push toward one shared comparator to kill two parallel switches, while step 3's null-direction interaction cannot be shared by value-comparison reuse alone and forces the shared helper's signature to change (null handling moves inside it).
- Interface Contract:

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| `CompareOrdered(colA, colB any, dir, nullsFirst)` or equivalent unexported helper used by both paths | func | pure comparison helper | STATED (graded behaviourally via `MergeRecords`/`SortRecord` agreement, not by name) | any name accepted; graded via behaviour |
| (no new exported API required) | — | widened accepted input types to existing `MergeRecords`/`SortRecord` | IN-BASE entry points | n/a |

- Named wrong shape: **copy-paste the new cases into both switches independently** — because each switch is self-contained and compiles green per-type, the model duplicates float/bool/timestamp logic twice and fixes nulls only in merge, leaving sort-vs-merge disagreement on the next type.
- Why: the shipped layout (two private switches in different files) rewards local case-addition; the Go idiom "handle the type where you see it" reads naturally here.
- Overlap: step 1 `merge.go`; step 2 `sort.go` + shared helper (cumulative); step 3 both `Less` functions (incremental on the helper).
- What step 2 cannot compute without step 1: the cross-oracle agreement test needs merge's widened behaviour as the reference — without step 1, "agree with merge" is agreement with a panic.

### M3 — Deterministic sampler materialization (S8 + S12; P6 shell around build-then-use)

- Step 1 requirement: `materialize` builds the unified schema and record (HEAD's eager artifact), with a stated, tested column order.
- Step 2 requirement: disparate schemas materialize correctly (name-based copy, S12 fix) **and** the order obeys the step-2 constraint (encounter-order / stability among incomparable columns), replacing step 1's alphabetical total sort.
- Invariants: S1 — one unified record preserves every sampled value; S2 — same values, canonical order preserving first-seen stability.
- **Tension:** step 1 needs *some* total order to emit a record at all (alphabetical is simplest), while step 2's stability-among-incomparables constraint forbids any total sort and forces removal of the `slices.SortFunc` step 1 just added.
- Interface Contract: no new symbols required — graded through existing `NewReservoirSampler`/`Callback`/`Finish` record schemas and values. (Deliberately zero-contract: the discrimination is order + correctness of values.)
- Named wrong shape: **keep the alphabetical sort and fix only the column index** — because the TODO comment sits on the copy loop (`sampler.go:262`) and not on the sort, the natural minimal diff repairs `Column(i)`→name lookup while leaving `SortFunc` intact, passing value tests but failing order-stability tests.
- Why: the shipped comment directs attention to the loop body; alphabetical determinism "looks correct" and matches Go map-canonicalization idiom (`sort keys for determinism`).
- Overlap: both steps touch only `sampler.go` (step 2 incremental on step 1).
- What step 2 cannot compute without step 1: the order-stability assertion needs the unified materialized record; without step 1's union-and-merge there is no multi-schema record whose column order is even defined.

### M4 (standby P6) — Streaming multi-sink persist (S14 alone as two-step P6)

- Step 1: buffer-once fan-out to N sinks (works, materialises whole block). Step 2 constraint: bounded-memory streaming (no full-block buffering) with per-sink error aggregation and cleanup — must remove the buffer. Tension: one serialisation shared by N uploads vs N independent failure domains. Wrong shape: serialize-per-sink loop (N serialisations, N× CPU, races with rotation). Step 2 cannot compute its memory bound without step 1's aforementioned buffer as the thing to remove. Kept as standby because it shares no files with M1–M3 and would be a fourth cascade, not a merge.

### Honesty statement

No premise was discarded for lack of evidence — every admission above was re-verified with a verbatim quote and a still-true/stale verdict (the merge WARNING is the only stale-half one, and I showed exactly which half). Dropped: S3 (hygiene), S13 (ungradeable, no caller). Parked single-turns (S6, S7, S10, S11, S15) are, in my judgment, individually stronger *tasks* than M2's widening steps — if this repo yields cascades, M1 and M3 are the real ones; M2 is honest narrow-then-widen glue. Zero-cascade would have been reported if S8/S14 had failed their operational tests; they pass, so I report 3 (+1 standby) merged candidates.

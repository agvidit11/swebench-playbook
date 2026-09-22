# SURFACE SURVEY — `polarsignals/frostdb` @ `9e5cfe0171adff531d30a9df3e111686996f4a9f`

Read-only survey; no files were changed and no build/test commands were run.

## Summary

- Surfaces: **16**
- Net-new capabilities/contracts: **11**
- HEAD defects: **5**
- UNLENSED controls: **3**
- Genuine P6 candidates passing both operational tests: **3**
- Strongest merged candidates: optimizer isolation, computed ordered aggregation, protobuf aggregation parity, multi-sink streaming, nested generic ingestion.

The `swebench-mt` playbook influenced the rejection of performance-only and edge-case-only ideas in favor of observable structural forks.

## Surface list

### S1. Injectable optimizers with repeatable observation

1. **Subsystem / files:** query planning; `query/engine.go`, `query/logicalplan/optimize.go`, `query/logicalplan/logicalplan.go`.
2. **Axis:** AXIS 19 + AXIS 10. Net-new capability. Genuine P6.
3. **HEAD TODAY:** `DefaultOptimizers` returns a fixed list at `query/logicalplan/optimize.go:9-19`, and every build unconditionally runs that list at `query/engine.go:184-186`. `LocalEngine` options only expose tracing and physical-plan options at `query/engine.go:34-46`. Public optimizer injection and isolation are not implemented.
4. **Nearest presence:** `"type Optimizer interface { Optimize(plan *LogicalPlan) *LogicalPlan }"` at `query/logicalplan/optimize.go:5-7`; the extension interface exists, but there is no engine option accepting implementations.
5. **Fork — FORK: strong:** A stores injected optimizers and runs them directly on the builder’s shared plan. B clones the logical plan for every `Explain`/`Execute`, then optimizes the clone. A is the predicted cold implementation because `Builder.Build` returns `b.plan` directly at `query/logicalplan/builder.go:257-265`.
6. **Observable:** inject a mutating optimizer through a proposed `WithOptimizers`, call `Explain` twice and then `Execute`, and assert that the added plan node appears exactly once each time and execution is unchanged. Existing entry points: `NewEngine`, `Explain`, `Execute`.
7. **Existing vocabulary:** `Optimizer` IN-BASE (`optimize.go:5`), `LogicalPlan` IN-BASE (`logicalplan.go:15`), `LocalQueryBuilder` IN-BASE (`engine.go:66`), `Explain` IN-BASE (`engine.go:170`), `Execute` IN-BASE (`engine.go:158`), `WithOptimizers` COINED. Ratio **5/6 IN-BASE**.
8. **P6:** HEAD counterfactual: **NO**—without injection the mutating optimizer cannot reach the grader. Parallel-API test: **NO**—the same injected option and existing `Explain`/`Execute` calls must remain reusable. Passes P6.
9. **Determinism seam:** no time or concurrency; a deterministic counting/mutating optimizer.
10. **Size:** 3 files, about 110–170 net lines.
11. **Motivating caller:** embedders already have the public `Optimizer` abstraction but cannot install domain-specific rules or safely inspect their effects.

### S2. Multiple functions in `OrderedAggregate`

1. **Subsystem / files:** physical query execution; `query/physicalplan/aggregate.go`, `ordered_aggregate.go`, `physicalplan.go`.
2. **Axis:** AXIS 19. Net-new capability.
3. **HEAD TODAY:** `Aggregate` returns `"OrderedAggregate does not support multiple aggregations, found %d"` at `query/physicalplan/aggregate.go:54-58`; the planner avoids that branch at `query/physicalplan/physicalplan.go:525-527`. The capability is not implemented.
4. **Nearest presence:** `"Multiple aggregation functions are not yet supported. The planning code should already have planned a hash aggregation in this case."` at `query/physicalplan/aggregate.go:63-65`. `HashAggregate` already stores `aggregations []Aggregation` at `aggregate.go:149`.
5. **Fork — FORK: strong:** widen `OrderedAggregate` to maintain independent carry/result state per aggregation, or plan several ordered aggregators and zip their keyed outputs. A model is more likely to widen the operator because the hash implementation supplies the adjacent slice-based design.
6. **Observable:** through `LocalQueryBuilder.Aggregate`, `WithOrderedAggregations`, `Explain`, and `Execute`, assert one ordered plan and correct `sum`/`max`/`count` columns across record boundaries and dynamic groups.
7. **Existing vocabulary:** `OrderedAggregate` IN-BASE (`ordered_aggregate.go:24`), `Aggregation` IN-BASE (`aggregate.go:103`), `WithOrderedAggregations` IN-BASE (`physicalplan.go:273`), `Explain` IN-BASE (`engine.go:170`), `Execute` IN-BASE (`engine.go:158`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**—multiple aggregation support can be implemented directly. Parallel API: **YES**—a second multi-aggregate operator could coexist. Not P6 alone.
9. **Determinism seam:** single physical input via `WithOverrideInput`, or fixed record callbacks.
10. **Size:** 3–4 files, about 300–500 net lines.
11. **Motivating caller:** `Avg` expands to `sum` plus `count` at `query/logicalplan/builder.go:205-234`, so ordered execution currently cannot serve a built-in aggregation.

### S3. Computed operands in the core aggregation builder

1. **Subsystem / files:** logical/physical query planning; `query/logicalplan/builder.go`, `query/physicalplan/aggregate.go`, `project.go`.
2. **Axis:** AXIS 19. **HEAD bug.**
3. **HEAD TODAY:** the admission remains true: `"This is not correct, it doesn't handle aggregations correctly of previously projected columns like sum(value + timestamp)."` at `query/physicalplan/aggregate.go:33-36`. Hash aggregation matches `col.expr.MatchColumn(field.Name)` at `aggregate.go:350-352`, so a raw computed expression has no physical field to match. It is not fully implemented.
4. **Nearest presence:** the SQL front end already inserts aggregate operand pre-projections: `"we need to ensure that it is in the pre-projection"` at `sqlparse/visitor.go:87-95`. Direct Go builder calls do not receive that repair.
5. **Fork — FORK: strong:** insert a projection node naming every computed aggregate operand, or evaluate each operand inside the aggregate callback using the existing projection machinery. A model likely inserts a projection because the SQL visitor demonstrates that design.
6. **Observable:** `ScanTable(...).Aggregate([]*AggregationFunction{Sum(Col("value").Add(Col("timestamp")))}, ...)` must execute through `LocalQueryBuilder.Execute` and return the row-wise-expression sum.
7. **Existing vocabulary:** `Builder.Aggregate` IN-BASE (`builder.go:152`), `BinaryExpr` IN-BASE (`expr.go:105`), `Sum` IN-BASE (`expr.go:752`), `Projection` IN-BASE (`project.go:865`), `Execute` IN-BASE (`engine.go:158`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**—the behavior is independently fixable. Parallel API: **YES**—a separate computed-aggregate path could coexist. Not P6 alone.
9. **Determinism seam:** fixed input records; no time or concurrency.
10. **Size:** 3 files, about 100–180 net lines.
11. **Motivating caller:** direct Go query builders should have parity with the SQL adapter, which already accepts the expression.

### S4. Row-wise list comparison semantics

1. **Subsystem / files:** physical filtering; `query/physicalplan/binaryscalarexpr.go`, `filter.go`.
2. **Axis:** AXIS 19. Net-new capability.
3. **HEAD TODAY:** `BinaryScalarOperation` dispatches on the array type and executes `panic("TODO: list comparisons unimplemented")` for `*arrow.ListType` at `query/physicalplan/binaryscalarexpr.go:97-116`. It is not implemented.
4. **Nearest presence:** non-list values fall through to `ArrayScalarCompute` at `binaryscalarexpr.go:116-124`; repeated columns are already advertised as Arrow LIST at `internal/records/record_builder.go:84-91`.
5. **Fork — FORK: strong:** compare each row’s list recursively with explicit null semantics, or construct a repeated scalar array and invoke Arrow compute kernels. The Arrow-kernel route is the predicted cold implementation because it is the existing scalar path.
6. **Observable:** call the existing `BinaryScalarOperation` or `Filter` with nullable list rows and list scalars; assert `OpEq`/`OpNotEq` bitmap membership, including null list, null element, empty list, and equal contents.
7. **Existing vocabulary:** `BinaryScalarOperation` IN-BASE (`binaryscalarexpr.go:84`), `ListType` IN-BASE (`binaryscalarexpr.go:112`), `OpEq` IN-BASE (`expr.go:17`), `OpNotEq` IN-BASE (`expr.go:18`), `Bitmap` IN-BASE (`filter.go:35`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a list-specific comparator could sit beside the current path. Not P6.
9. **Determinism seam:** none needed.
10. **Size:** 2–3 files, about 100–180 net lines.
11. **Motivating caller:** `records.Build` already produces repeated/list columns, but those columns cannot participate in ordinary equality filters.

### S5. Protobuf reachability for `IsNullExpr`

1. **Subsystem / files:** protobuf query boundary; `proto/frostdb/storage/v1alpha1/storage.proto`, generated storage code, `query/exprpb/proto.go`.
2. **Axis:** AXIS 19. Net-new capability.
3. **HEAD TODAY:** logical `IsNullExpr` exists at `query/logicalplan/expr.go:801-878`, and physical projection exists at `query/physicalplan/project.go:558-600`; the protobuf expression switch has no corresponding case and returns `"unsupported expression type: %T"` at `query/exprpb/proto.go:249-269`. The end-to-end capability is not implemented.
4. **Nearest presence:** the proto says its expression `oneof` exists `"to maintain forward compatibility"` at `proto/frostdb/storage/v1alpha1/storage.proto:117-142`, and the adjacent `IfExpr` is wired both directions at `query/exprpb/proto.go:116-136` and `273-297`. It fails to cover `IsNullExpr`.
5. **Fork — FORK: weak:** add an explicit protobuf `IsNullExpr` oneof, or encode it as equality with a null literal. A model likely adds the explicit oneof because the logical node already has distinct semantics.
6. **Observable:** `ExprToProto(IsNull(Col("x")))`, `ExprFromProto`, then `ProtoEngine.Execute`; assert round-trip expression equality and null/non-null output.
7. **Existing vocabulary:** `logicalplan.IsNullExpr` IN-BASE (`expr.go:807`), `ExprToProto` IN-BASE (`proto.go:244`), `ExprFromProto` IN-BASE (`proto.go:36`), `ProtoEngine` IN-BASE (`engine.go:17`), protobuf `IsNullExpr` COINED. Ratio **4/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a separate encoding helper could coexist. Not P6.
9. **Determinism seam:** none needed.
10. **Size:** 4–5 files including generated code, about 180–320 net lines.
11. **Motivating caller:** remote/protobuf query clients cannot express a logical and physically implemented null projection.

### S6. Complete protobuf aggregation-function dispatch

1. **Subsystem / files:** protobuf query conversion; `query/exprpb/proto.go`, `proto/frostdb/storage/v1alpha1/storage.proto`.
2. **Axis:** AXIS 19. Net-new capability.
3. **HEAD TODAY:** the wire enum defines `TYPE_AVG`, `TYPE_UNIQUE`, and `TYPE_AND` at `storage.proto:289-294`, but both conversion switches only accept sum/min/max/count at `query/exprpb/proto.go:190-201` and `566-577`. The enum’s advertised capability is unreachable.
4. **Nearest presence:** `logicalplan` already defines and names `AggFuncAvg`, `AggFuncUnique`, and `AggFuncAnd` at `query/logicalplan/expr.go:718-746`; the protobuf converters fail to cover those existing cases.
5. **Fork — FORK: weak:** map all existing enum values directly, or lower `AVG` to sum/count during conversion while mapping unique/and directly. Direct mapping is the predicted cold implementation.
6. **Observable:** round-trip all seven aggregation enum values through `AggregationFunctionToProto` and `ExprFromProto`, then execute AVG/UNIQUE/AND through `ProtoEngine`.
7. **Existing vocabulary:** `AggFuncAvg`, `AggFuncUnique`, `AggFuncAnd` IN-BASE (`expr.go:726-728`); `TYPE_AVG`, `TYPE_UNIQUE`, `TYPE_AND` IN-BASE (`storage.proto:289-294`). Ratio **6/6**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, separate conversion functions could be added. Not P6 alone.
9. **Determinism seam:** fixed records; no time or concurrency.
10. **Size:** 2 files, about 25–60 net lines.
11. **Motivating caller:** the protobuf schema already promises the functions, and the local builder already implements them.

### S7. Protobuf aggregation node is discarded

1. **Subsystem / files:** protobuf plan construction; `query/exprpb/engine.go`, `engine_test.go`.
2. **Axis:** **UNLENSED control. HEAD bug.**
3. **HEAD TODAY:** aggregation parsing calls `b.Aggregate(aggExprs, groupExprs)` without assigning the returned builder at `query/exprpb/engine.go:125-140`. `Builder.Aggregate` returns a new builder at `query/logicalplan/builder.go:175-203`; therefore the node is dropped. Not implemented correctly.
4. **Nearest presence:** every adjacent plan case assigns the result, for example `"b = b.Project(exprs...)"` at `query/exprpb/engine.go:113-118`. Aggregation alone fails to do so.
5. **Fork — FORK: weak:** assign `b = b.Aggregate(...)`, or redesign `logicalplan.Builder` methods to mutate receivers. The one-line assignment is the obvious cold implementation.
6. **Observable:** `ProtoEngine.FromProto` on scan→aggregation must expose `LogicalPlan.Aggregation`; `Explain` must show an aggregate and `Execute` must return aggregate values.
7. **Existing vocabulary:** `ProtoEngine` IN-BASE (`engine.go:17`), `FromProto` IN-BASE (`engine.go:64`), `PlanNode` IN-BASE (`engine.go:64`), `Builder.Aggregate` IN-BASE (`builder.go:152`), `LogicalPlan.Aggregation` IN-BASE (`logicalplan.go:26`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, an alternate proto builder could coexist. Not P6 alone.
9. **Determinism seam:** fixed fake `TableReader`; no concurrency required.
10. **Size:** 2 files, about 10–35 net lines.
11. **Motivating caller:** every protobuf client submitting an aggregation currently gets the underlying scan instead.

### S8. Reservoir materialization across disparate schemas

1. **Subsystem / files:** sampling; `query/physicalplan/sampler.go`, `sampler_test.go`.
2. **Axis:** AXIS 19. **HEAD bug.**
3. **HEAD TODAY:** the reservoir explicitly permits records that `"may vary in schema due to dynamic columns"` at `sampler.go:30-31`, but materialization says `// TODO handle disparate schemas` and reads `r.ref.Column(i)` using the merged-schema index at `sampler.go:261-270`. The behavior is not fully implemented.
4. **Nearest presence:** materialization already creates a union schema and appends nulls for absent names at `sampler.go:230-265`; it fails when an existing field occupies a different source index.
5. **Fork — FORK: strong:** resolve every merged field with `FieldIndices(name)` per source record, or first normalize sampled records with `EnsureSameSchema` and then append. Reusing `EnsureSameSchema` is the predicted cold implementation.
6. **Observable:** force materialization with records whose fields are missing and reordered; through `NewReservoirSampler`, `Callback`, and `Finish`, assert each sampled value remains under its original field name and absent values become null.
7. **Existing vocabulary:** `ReservoirSampler` IN-BASE (`sampler.go:73`), `Callback` IN-BASE (`sampler.go:104`), `Finish` IN-BASE (`sampler.go:201`), `EnsureSameSchema` IN-BASE (`arrowutils/schema.go:15`), `DynamicColumn` IN-BASE (`logicalplan/expr.go`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a separate normalizer could coexist. Not P6.
9. **Determinism seam:** bypass random selection by constructing the package-local reservoir and invoking existing `materialize`; alternatively assert only name/value association, independent of which rows were selected.
10. **Size:** 2 files, about 70–120 net lines.
11. **Motivating caller:** sampling explicitly accepts dynamic schemas, and memory-pressure materialization is the path intended to keep such sampling bounded.

### S9. One-pass persistence to multiple sinks

1. **Subsystem / files:** storage plumbing; `store.go`, `db.go`, `db_test.go`.
2. **Axis:** AXIS 19. Net-new capability. Genuine P6.
3. **HEAD TODAY:** options append every sink at `db.go:187-190`, but `TableBlock.Persist` returns `"multiple sinks not supported"` on the second sink at `store.go:35-38`. The public configuration path is reachable but refused.
4. **Nearest presence:** `"The database supports multiple data sources and sinks."` at `db.go:348-350`; one sink already receives a streamed `io.Pipe` at `store.go:39-49`. The missing case is fan-out to more than one sink.
5. **Fork — FORK: strong:** A removes the guard and serializes/uploads once per sink sequentially. B serializes once and streams with coordinated fan-out/backpressure to all sinks. A is the predicted cold implementation because it is the smallest change to the existing loop.
6. **Observable:** configure two existing `DataSink`s through repeated `WithWriteOnlyStorage`, invoke `TableBlock.Persist`, and assert both uploads begin at the synchronization barrier and each stream parses to the expected row count. No byte-for-byte comparison.
7. **Existing vocabulary:** `DataSink` IN-BASE (`db.go:382`), `WithWriteOnlyStorage` IN-BASE (`db.go:187`), `TableBlock.Persist` IN-BASE (`store.go:30`), `Upload` IN-BASE (`db.go:385`). Ratio **4/4**.
8. **P6:** HEAD counterfactual: **NO**—HEAD refuses the second sink. Parallel-API test: **NO**—the existing `Persist` path configured by existing options is graded. Passes P6.
9. **Determinism seam:** explicit channel barrier inside fake sinks; concurrency is required, real network and wall-clock timing are not.
10. **Size:** 2–3 files, about 110–190 net lines.
11. **Motivating caller:** repeated storage options already construct multiple sinks, and mirrored object-store persistence is a concrete durability/compatibility use case.

### S10. Non-consuming record-builder preview

1. **Subsystem / files:** generic record ingestion; `internal/records/record_builder.go`, `record_builder_test.go`.
2. **Axis:** AXIS 10. Net-new capability. Genuine P6.
3. **HEAD TODAY:** `Build[T]` provides `Append` and `NewRecord` at `record_builder.go:251-267`; `NewRecord` calls each field’s `NewArray` at `record_builder.go:268-282`, which drains/reset builders. No non-consuming preview is implemented.
4. **Nearest presence:** the lower-level builder documents `"NewRecord creates a new record from the memory buffers and resets the RecordBuilder"` at `pqarrow/builder/recordbuilder.go:67-73`. It fails the preview-without-consuming case.
5. **Fork — FORK: strong:** A implements `PreviewRecord` by delegating to `NewRecord`. B snapshots current arrays while preserving builder state and reference ownership. A is the predicted cold implementation because `NewRecord` is the only adjacent record-producing primitive.
6. **Observable:** append rows, call proposed `PreviewRecord`, append another row, then call existing `NewRecord`; assert the preview has the original rows, the final record has all rows, and releasing either record does not alter the other.
7. **Existing vocabulary:** `Build` IN-BASE (`record_builder.go:92`), `Append` IN-BASE (`record_builder.go:251`), `NewRecord` IN-BASE (`record_builder.go:267`), `PreviewRecord` COINED. Ratio **3/4**.
8. **P6:** HEAD counterfactual: **NO**—the step-2 lifecycle test cannot compile without the preview artifact. Parallel-API test: **NO**—the contract pins the same `PreviewRecord` method. Passes P6.
9. **Determinism seam:** none needed.
10. **Size:** 2 files, about 80–140 net lines.
11. **Motivating caller:** the `GenericTable.Write` path immediately drains the builder into `InsertRecord` at `table.go:236-245`; validation or inspection of the exact staged Arrow batch currently cannot happen without consuming it.

### S11. Native nested structs in generic ingestion

1. **Subsystem / files:** generic records/table schema; `internal/records/record_builder.go`, `table.go`, `dynparquet/schema.go`.
2. **Axis:** AXIS 19. Net-new capability.
3. **HEAD TODAY:** the admission is current: `"Nested Columns are not supported"` at `internal/records/record_builder.go:35-38` and `table.go:169-172`; an unrecognized struct kind panics at `record_builder.go:179-212`. Not implemented.
4. **Nearest presence:** schema v2 explicitly models nested `Group` nodes at `proto/frostdb/schema/v1alpha2/schema.proto:68-96`, and `ParquetSchemaFromV2Definition` recursively builds groups at `dynparquet/schema.go:209-240`. Generic reflection does not reach it.
5. **Fork — FORK: strong:** flatten nested fields into dotted v1 columns, or recursively build Arrow structs and schema-v2 groups preserving nullable/repeated parents. A model likely chooses recursive native structs after finding schema v2, though the dynamic-column dotted convention makes flattening credible.
6. **Observable:** existing `NewGenericTable[T]` and `Write` accept a struct containing nullable nested structs; querying/projecting the nested path returns parent-null, child-null, and populated-child cases distinctly.
7. **Existing vocabulary:** `Build` IN-BASE (`record_builder.go:92`), `GenericTable` IN-BASE (`table.go:226`), `NewGenericTable` IN-BASE (`table.go:247`), `SchemaV2` IN-BASE (`table.go:143-146`), `Group` IN-BASE (`schema.proto:87`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a separate nested builder could coexist. Not P6.
9. **Determinism seam:** none needed.
10. **Size:** 3–5 files, about 300–550 net lines.
11. **Motivating caller:** the repository already carries a nested-schema wire format and Arrow/Parquet struct conversion, but the primary typed ingestion facade cannot produce it.

### S12. Nested superset row-group reconciliation

1. **Subsystem / files:** dynamic Parquet schema merging; `dynparquet/schema.go`, `schema_test.go`, possibly `nil_chunk.go`.
2. **Axis:** AXIS 19. Net-new capability.
3. **HEAD TODAY:** the admission is current: `DynamicRowGroupMergeAdapter.ColumnChunks` says `"This only works because we currently only support flat schemas."` at `dynparquet/schema.go:1548-1553`; mapping is performed only over root names at `schema.go:1497-1520`. Nested reconciliation is not implemented.
4. **Nearest presence:** `nodeFromDefinition` recursively converts schema-v2 groups at `schema.go:218-240`, while `NewDynamicRowGroupMergeAdapter` already fills absent flat fields with `NewNilColumnChunk` at `schema.go:1548-1565`. Missing nested children and definition/repetition levels are not covered.
5. **Fork — FORK: strong:** flatten leaf paths and remap leaf column ordinals, or recursively align group nodes while generating null pages with correct definition/repetition levels. The leaf-path approach is the predicted cold implementation because the current adapter is column-chunk indexed.
6. **Observable:** merge two existing `DynamicRowGroup`s whose common parent group has different child subsets; read through `Rows()` and assert sibling values remain attached while missing children are null.
7. **Existing vocabulary:** `DynamicRowGroupMergeAdapter` IN-BASE (`schema.go:1523`), `ColumnChunks` IN-BASE (`schema.go:1551`), `DynamicRowGroup` IN-BASE (`schema.go:787`), `NewNilColumnChunk` IN-BASE (`nil_chunk.go:19`), `Rows` IN-BASE (`schema.go:1586`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a nested adapter could coexist with the flat implementation. Not P6 alone.
9. **Determinism seam:** none needed.
10. **Size:** 2–3 files, about 250–450 net lines.
11. **Motivating caller:** schema-v2 tables can already describe nested groups, but row groups with evolved nested children cannot be safely combined.

### S13. Borrowed-input ownership for `EnsureSameSchema`

1. **Subsystem / files:** Arrow schema reconciliation; `pqarrow/arrowutils/schema.go`, `schema_test.go`.
2. **Axis:** **UNLENSED control.** New ownership contract; HEAD documentation is ambiguous, so this is not counted as a defect.
3. **HEAD TODAY:** replaced input records are collected and explicitly released at `pqarrow/arrowutils/schema.go:54-92`. The function’s documentation at `schema.go:11-14` says only that it ensures equal schemas and does not disclose ownership transfer. Borrowed-input behavior is not implemented.
4. **Nearest presence:** unchanged records are returned directly at `schema.go:57-61`; only records requiring replacement are released. Thus ownership differs based on schema equality.
5. **Fork — FORK: strong:** transfer ownership of replaced inputs as today, or borrow all inputs and make callers release input and output records independently. A model modifying the existing function likely preserves transfer semantics unless ownership is explicitly constrained.
6. **Observable:** pass tracking implementations of `arrow.Record` to existing `EnsureSameSchema`; assert no input `Release` occurred before return and that input records remain readable after independently releasing aligned outputs.
7. **Existing vocabulary:** `EnsureSameSchema` IN-BASE (`schema.go:15`), `arrow.Record` IN-BASE in its signature (`schema.go:15`), `Release` IN-BASE usage (`schema.go:90-92`), `mergedRecords` IN-BASE (`schema.go:54`). Ratio **4/4**.
8. **P6:** HEAD counterfactual: **YES**—the ownership contract can be changed directly. Parallel API: **YES**—a borrowed variant could coexist, so this is not P6.
9. **Determinism seam:** reference-count tracking; no concurrency.
10. **Size:** 2 files, about 25–60 net lines.
11. **Motivating caller:** callers composing schema alignment with later merge/inspection need to reuse inputs without conditional ownership rules.

### S14. Partial-order-preserving heterogeneous schema union

1. **Subsystem / files:** Arrow schema reconciliation; `pqarrow/arrowutils/schema.go`, `schema_test.go`.
2. **Axis:** AXIS 13. New ordering contract.
3. **HEAD TODAY:** `EnsureSameSchema` gathers fields into a map, alphabetically sorts every name, and constructs the merged schema at `pqarrow/arrowutils/schema.go:32-52`. Stable preservation of existing field order is not implemented.
4. **Nearest presence:** source fields are encountered in record order at `schema.go:33-39`, but that order is discarded by `sort.Strings(columnNames)` at `schema.go:46`. It fails to preserve the first schema’s relative order among unrelated fields.
5. **Fork — FORK: strong:** total lexical order, as today, or retain the first schema’s field sequence and append first-seen new fields while respecting any shared prefix. The current total sort is the predicted cold implementation.
6. **Observable:** call existing `EnsureSameSchema` with schemas `[key,z,a]` and `[key,m,z]`; assert `[key,z,a,m]`, correct null placement, and unchanged values rather than total lexical order.
7. **Existing vocabulary:** `EnsureSameSchema` IN-BASE (`schema.go:15`), `Schema` IN-BASE (`schema.go:20`), `Field` IN-BASE (`schema.go:32`), `mergedFields` IN-BASE (`schema.go:48`). Ratio **4/4**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **NO** if the existing function’s contract is pinned, but the counterfactual still makes this non-P6.
9. **Determinism seam:** explicit input record order.
10. **Size:** 2 files, about 50–90 net lines.
11. **Motivating caller:** projection and record consumers use positional Arrow fields; schema evolution should not reorder every pre-existing payload column merely because a new field appeared.

### S15. Direction and null placement through ordered synchronization

1. **Subsystem / files:** physical planner and ordered fan-in; `query/physicalplan/physicalplan.go`, `planordering.go`, `ordered_synchronizer.go`, `pqarrow/arrowutils/merge.go`.
2. **Axis:** AXIS 19 + AXIS 13. **HEAD bug.**
3. **HEAD TODAY:** `MergeRecords` correctly consults `Direction.comparison()` at `merge.go:100-108`, but the planner passes only group expressions to `NewOrderedSynchronizer` at `physicalplan.go:438-443`; synchronization rebuilds every descriptor as zero-valued ascending with `arrowutils.SortingColumn{Index: i}` at `ordered_synchronizer.go:198-201`. Descending/null placement is not propagated.
4. **Nearest presence:** `dynparquet.SortingColumn` already exposes `Descending()` and `NullsFirst()` at `dynparquet/schema.go:38-52`; `planOrderingInfo` stores only `[]ColumnDefinition` at `planordering.go:26-38`, losing those attributes.
5. **Fork — FORK: weak:** carry concrete sorting descriptors through planning, or infer direction/null placement from incoming batches. A model likely extends planner metadata and constructor arguments.
6. **Observable:** feed two synchronized inputs ordered descending with nulls first/last, using existing `NewOrderedSynchronizer`; assert globally ordered callback values and stable non-key schema fields.
7. **Existing vocabulary:** `OrderedSynchronizer` IN-BASE (`ordered_synchronizer.go:24`), `SortingColumn` IN-BASE (`sort.go:41`), `Direction` IN-BASE (`sort.go:23`), `NullsFirst` IN-BASE (`sort.go:45`), `MergeRecords` IN-BASE (`merge.go:23`). Ratio **5/5**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a directional constructor could coexist. Not P6.
9. **Determinism seam:** fixed two-input goroutines coordinated by channels/barriers; no wall-clock ordering.
10. **Size:** 3–4 files, about 110–190 net lines.
11. **Motivating caller:** schemas explicitly support descending and null placement, while ordered aggregation relies on synchronized streams respecting those declarations.

### S16. Correct sorting metadata from generic records

1. **Subsystem / files:** generic record construction; `internal/records/record_builder.go`, `record_builder_test.go`.
2. **Axis:** **UNLENSED control. HEAD bug.**
3. **HEAD TODAY:** `NewRecord` sorts `b.sort` by declared sort rank, then records `Index: idx` where `idx` is the rank within that sorted slice at `internal/records/record_builder.go:290-303`. This is wrong when unsorted fields precede sorted fields or declared sort priority differs from physical field order.
4. **Nearest presence:** physical fields are emitted separately in struct/declaration order at `record_builder.go:267-281`. That loop has the real output positions, but those positions are not retained in `b.sort`.
5. **Fork — FORK: strong:** record physical offsets while fields expand, or construct the record first and resolve each sorting field name through its schema. Name lookup is the predicted cold implementation because dynamic fields can expand one logical field into several columns.
6. **Observable:** build a struct with an unsorted leading field and sort tags whose priorities differ from declaration order; pass returned `Record.SortingColumns` to existing `SortRecord` and assert ordering by the tagged columns.
7. **Existing vocabulary:** `Record.SortingColumns` IN-BASE (`record_builder.go:24-27`), `Build.NewRecord` IN-BASE (`record_builder.go:267`), `SortingColumn.Index` IN-BASE (`sort.go:41-45`), `SortRecord` IN-BASE (`sort.go:54`). Ratio **4/4**.
8. **P6:** HEAD counterfactual: **YES**. Parallel API: **YES**, a metadata-repair helper could coexist. Not P6.
9. **Determinism seam:** fixed input rows.
10. **Size:** 2 files, about 40–90 net lines.
11. **Motivating caller:** `Record.SortingColumns` is explicitly returned for consumption by `SortRecord`; incorrect positional metadata makes that advertised composition sort by unrelated fields.

## Admission audit

| Admission | HEAD verification |
|---|---|
| Ordered aggregate rejects multiple functions | **True.** Guard at `query/physicalplan/aggregate.go:54-58`; planner avoids it at `physicalplan.go:525-527`. Covered by S2. |
| Computed aggregate operands are incorrect | **Partly true.** Core Go builder remains incorrect at `aggregate.go:33-36`; SQL compensates with pre-projections at `sqlparse/visitor.go:87-95`. Covered by S3. |
| `MergeRecords` ascending-only warning | **Stale.** Warning remains at `pqarrow/arrowutils/merge.go:22`, but values consult direction at `merge.go:100-108`. Null placement at `merge.go:91-97` is intentionally absolute through `NullsFirst`, not direction-relative. Direction is instead lost by `OrderedSynchronizer`; covered by S15. |
| List comparisons unimplemented | **True.** Panic at `query/physicalplan/binaryscalarexpr.go:111-114`. Covered by S4. |
| Sampler disparate schemas | **True.** TODO and positional misread at `query/physicalplan/sampler.go:261-270`. Covered by S8. |
| Merge adapter works only for flat schemas | **True.** `dynparquet/schema.go:1552`. Covered by S12. |
| Generic nested columns unsupported | **True.** `internal/records/record_builder.go:37` and `table.go:171`. Covered by S11. |
| Multiple sinks unsupported | **True.** `store.go:35-38`, despite appendable sink options. Covered by S9. |
| LSM sentinel lookup should be O(1) | **True but rejected.** `index/lsm.go:470-481`; the observable difference is speed only, so it is UNGRADEABLE under the brief. |
| `AggFuncPushDown` should be less specific | **Still true but rejected.** `query/logicalplan/optimize.go:179-187`; changing it principally alters scan pruning and the existing implementation memoizes maxima, hitting the performance/memoization exclusions. |
| `preExprVisitorFunc` replacement | **Still present but rejected.** `query/physicalplan/planordering.go:65-79`; it is cleanup with no useful external observable. |
| Page-level dictionary-only optimization | **Still true but rejected.** `pqarrow/arrow.go:718-765`; result semantics are unchanged, making it performance-only and UNGRADEABLE. |

## Merge pass

### Surface mapping

| Surface | Disposition | Reason |
|---|---|---|
| S1 | M1 | A closed optimizer extension point naturally composes with non-interfering `Explain`. |
| S2 | M2 | Multiple ordered aggregation consumes the computed-column artifact from S3. |
| S3 | M2 | Pre-projection creates the operands needed by the ordered stage. |
| S4 | parked-single-turn | List semantics are self-contained; no honest second surface depends on them. |
| S5 | parked-single-turn | Protobuf `IsNullExpr` parity is useful but independent of the aggregation chain. |
| S6 | M3 | Complete aggregation enum conversion becomes observable through the repaired proto plan. |
| S7 | M3 | The fixed aggregation node is required for end-to-end execution of S6. |
| S8 | parked-single-turn | It could reuse schema reconciliation, but a solver could implement local name lookup; the cascade would be fake. |
| S9 | M4 | Sequential multi-sink support followed by one-pass coordinated fan-out is a genuine P6. |
| S10 | M5 | Consuming preview followed by non-consuming continuity is a genuine P6. |
| S11 | M6 | Produces native nested records consumed by the schema-evolution step. |
| S12 | M6 | Widens nested ingestion to heterogeneous nested row groups. |
| S13 | parked-single-turn | Ownership can be corrected independently; forcing another feature to call this helper would grade implementation style. |
| S14 | parked-single-turn | Combining it with S15 fails the HEAD counterfactual because synchronization can reconcile fields internally. |
| S15 | parked-single-turn | Direction propagation is independently fixable. |
| S16 | parked-single-turn | A focused metadata defect with no honest dependent second stage. |

## M1. Custom optimizer injection → observer isolation

- **Step 1 requirement:** install custom `logicalplan.Optimizer`s in `LocalEngine`; invariant: configured optimizers participate exactly once in a physical build.
- **Step 2 requirement:** repeated `Explain` and later `Execute` do not retain mutations from earlier builds; invariant: each operation starts from the same logical plan.
- **Tension:** mutable, in-place optimizers conflict with a reusable query builder observed repeatedly.

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| `WithOptimizers` | function | `func(...logicalplan.Optimizer) query.Option` | STATED | PINNED |

- **Named wrong shape:** mutate-shared-plan registration. A capable model will store the optimizer slice and extend the existing `buildPhysical` loop, because `Builder.Build` returns the original plan pointer and all default optimizers mutate in place.
- **Inter-step overlap:** step 1 touches `query/engine.go` and tests; step 2 revisits `engine.go` and adds plan cloning in `query/logicalplan`. Incremental on step 1.
- **Step-2 dependency:** without the injected optimizer artifact, the grader cannot induce or observe repeated optimizer mutation.
- **P6:** passes both operational tests.

## M2. Computed aggregate operands → multiple ordered execution

- **Step 1 requirement:** direct builder aggregations materialize/evaluate computed operands correctly; invariant: every aggregate consumes the row-wise value of its expression.
- **Step 2 requirement:** several computed aggregates remain eligible for ordered execution; invariant: `Explain` selects one ordered aggregate and results match hash aggregation.
- **Tension:** an eager projection supplies named operand arrays but currently invalidates the ordering information required to select `OrderedAggregate`.

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| — | — | No new test-touched symbols | IN-BASE | — |

- **Named wrong shape:** unconditional pre-projection followed by hash fallback. A model will copy the SQL visitor’s shipped pre-projection pattern, while the physical planner treats `Projection` as order-invalidating because that branch does not call `nodeMaintainsOrdering`.
- **Inter-step overlap:** step 1 touches `logicalplan/builder.go`, `aggregate.go`, and tests; step 2 touches `physicalplan.go`, `planordering.go`, `ordered_aggregate.go`, and overlapping tests. Cumulative from step 1.
- **Step-2 dependency:** ordered aggregation cannot bind computed operands until step 1 provides their physical arrays and names.

## M3. Protobuf aggregation node → full enum parity

- **Step 1 requirement:** retain the value returned by `Builder.Aggregate`; invariant: a protobuf aggregation produces a logical aggregation node.
- **Step 2 requirement:** AVG, UNIQUE, and AND round-trip and execute through that node; invariant: every already-defined wire enum maps to its corresponding logical function.
- **Tension:** complete enum conversion is useless when the value-style builder call silently discards the entire aggregation node.

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| — | — | All enum values and conversion entry points already exist | IN-BASE | — |

- **Named wrong shape:** converter-only completion. A capable model will add the three missing switch arms because the proto enum advertises them, but may miss the ignored builder return in another file.
- **Inter-step overlap:** step 1 touches `query/exprpb/engine.go` and its tests; step 2 touches `query/exprpb/proto.go` plus the same end-to-end tests. Incremental.
- **Step-2 dependency:** `ProtoEngine` cannot execute a newly converted aggregation function without step 1’s retained aggregation plan node.

## M4. Multiple sinks → one-pass coordinated streaming

- **Step 1 requirement:** `Persist` accepts every configured sink; invariant: each sink receives a parseable block containing the expected rows.
- **Step 2 requirement:** serialization is a single coordinated stream whose sinks may consume concurrently; invariant: both uploads cross an explicit start barrier before completion and all observe a complete Parquet stream.
- **Tension:** an `io.Reader` is one-shot, while independent sinks apply backpressure and can fail at different points.

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| — | — | `Persist`, `DataSink`, and storage options already exist | IN-BASE | — |

- **Named wrong shape:** sequential reserialization loop. A model will remove the guard and repeat the existing pipe/`Serialize` body for each sink, because that is the smallest local change.
- **Inter-step overlap:** both steps modify `store.go` and storage tests; step 2 replaces the step-1 loop rather than merely adding another API.
- **Step-2 dependency:** concurrent fan-out cannot be exercised until the existing `Persist` path reaches more than one configured sink.
- **P6:** passes both operational tests.

## M5. Record preview → non-consuming continuity

- **Step 1 requirement:** expose the currently staged `Build[T]` rows as a record; invariant: preview values and schema equal the staged batch.
- **Step 2 requirement:** preview, release, append, and `NewRecord` preserve the original and new rows; invariant: observation neither drains nor aliases later builder state.
- **Tension:** the only shipped record-producing primitive transfers builder buffers and resets them.

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| `PreviewRecord` | method | `func (*Build[T]) PreviewRecord() *Record` | STATED | PINNED |

- **Named wrong shape:** `return b.NewRecord()`. A capable model will delegate to the adjacent method because it already constructs exactly the required return type.
- **Inter-step overlap:** both steps modify `internal/records/record_builder.go` and its tests; step 2 must replace or substantially rework step 1.
- **Step-2 dependency:** continuity across preview cannot be evaluated without the preview artifact created in step 1.
- **P6:** passes both operational tests.

## M6. Native nested ingestion → nested schema evolution

- **Step 1 requirement:** generic nested structs produce native Arrow struct arrays and schema-v2 groups; invariant: parent and child nullability survive `GenericTable.Write` and query projection.
- **Step 2 requirement:** row groups with differing child subsets merge under the same parent; invariant: shared children retain values and absent children become correctly leveled nulls.
- **Tension:** flattening makes step 1 easy but loses the group structure and definition/repetition levels required by step 2.

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| — | — | Existing `NewGenericTable`, `Write`, schema-v2 `Group`, and merge APIs are sufficient | IN-BASE | — |

- **Named wrong shape:** dotted-name flattening into schema v1. A model may follow the repository’s dynamic-column convention, where logical fields such as `labels` become physical names such as `labels.pod`.
- **Inter-step overlap:** step 1 touches `internal/records/record_builder.go`, `table.go`, and tests; step 2 touches `dynparquet/schema.go`, `nil_chunk.go`, and nested integration tests. Cumulative from base with integration overlap in tests.
- **Step-2 dependency:** the evolved-row-group grader cannot obtain native nested records through the generic ingestion path without step 1’s group-valued record and schema artifact.

## Final assessment

M1, M2, M3, and M4 have the strongest observable structural forks. M5 is a clean P6 but has a narrower operational caller. M6 is substantial and likely exceeds the target patch size.

The UNLENSED controls found real defects and one ownership ambiguity, but none is stronger as a multi-turn surface than the best lens-derived candidates.
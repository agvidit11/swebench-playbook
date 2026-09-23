# Card C1 — Streaming multi-sink persist

Repo: polarsignals/frostdb @ 9e5cfe0171adff531d30a9df3e111686996f4a9f
Author: MetaCode (Avocado) — A2 card pass, brief at /tmp/frostdb-run/cards.txt
Source surveys: /tmp/frostdb-run/survey-mc.out (MetaCode), /tmp/frostdb-run/survey-codex.md (Codex gpt-5.6-sol)

---

## DECLARED PROBE DIRECTION — frozen 2026-09-22, redo run, BEFORE any probe was dispatched

> **Authorship of this block, stated explicitly.** Everything ABOVE this line is the
> original A2 card and is MetaCode's (`Author:` line 4 refers to that text only).
> **This block was written by Claude** in the redo run. It is A3 measurement scaffolding,
> not card content, and it does not carry MetaCode's attribution. Flagged by the reviewer
> on `00-A3-interim.md`; the fix is this note, since the fields cannot be removed —
> `probe-lint.py` refuses to run without them and A2's card schema does not emit them
> (logged as a playbook defect in `friction.md` F8).

These three fields are required by `A3 GATE 5 pre-check ①` and by `tools/probe-lint.py`.
They are derived from §2 step 2 of this card (`J1`, "the step-1 buffer must go") and from
§7's named wrong shapes. They were written before a single probe ran in the redo run, and
they are not revised afterwards. They are A3 measurement scaffolding and are NOT contract
prose — `instruction.md` is Avocado's / the human's to write from scratch at `B2`
(`00-ROUTER.md` §5).

CONSTRAINT: When a database has more than one data sink configured, persisting a table
block must deliver that block to every configured sink. Turning the block into its
uploadable form must happen exactly once per persist call and must not be repeated for
each sink. No sink may reach the end of the block until every other sink has begun
consuming it: while any sink has consumed nothing, no other sink may observe the end of
its copy, and the persist call must still be in progress. If a sink fails partway
through, the persist call must return an error that identifies that sink, the failing
sink's partial object must be removed through that same sink, and every healthy sink must
still end up holding the complete block.

DESIRED: A single production of the block whose bytes reach the sinks while it is still
being produced, so that consumption by the sinks drives production and the whole block is
never held at once; a stalled sink therefore holds back the others, and a failing sink is
detached and cleaned up while production continues feeding the healthy ones.

NON-DESIRED: Produce the whole block into an in-memory byte slice or a temporary file
first and then hand every sink an independent reader over that finished copy, uploading
concurrently; or run the existing single-sink path once per sink; or a plain fan-out
writer that couples one sink's failure or stall into the others' data loss.

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


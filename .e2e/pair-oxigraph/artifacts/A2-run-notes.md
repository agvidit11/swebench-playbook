# A2 run notes — oxigraph/oxigraph

## Step 1 — HANDOFF A1 facts (copied from `/home/agvidit/swebench/runs/shortlist-data.md`, NOT re-measured)

| field | value |
|---|---|
| repo | `oxigraph/oxigraph` |
| clone | `/tmp/shortlist-data/clones/oxigraph` |
| HEAD sha | `450d2fe0ea8b9aa457ad41dbf542582d1d443150` (2026-09-22 21:29:50 +0200, "SPARQL: Fix a wrong IF type inference") |
| licence | Apache-2.0 OR MIT |
| non-test LOC | 97,270 Rust (whole workspace) |
| subsystems | 14 crates (13 under `lib/`) |
| open issues | 130 (+24 PRs), 394 lifetime |
| remote branches | 27, all dependabot, zero agentic |
| AI authorship | **0 / 1000 commits** |
| peer tasks | **0** on oxigraph internals (pyoxigraph appears only as a *grading oracle* in 4 tbench tasks) |
| inline issue refs | 7 across 97k LOC |
| grading path | `docker run rust:1-slim`; `cargo build -p spareval -p sparopt -p spargebra -p oxrdf` = **47 s cold**; `cargo test -p spareval --no-run` = **4.5 s**. RocksDB (`oxrocksdb-sys`) NOT needed for query-engine crates |
| named existing entry points | `Store::{snapshot,start_transaction,quads_for_pattern,bulk_loader,load_from_reader,validate,clear_graph,remove_named_graph,backup}`; `spareval::QueryEvaluator::explain()` → `QueryExplanation` (JSON plan tree + per-node stats); `compute_statistics()`, `without_optimizations()`; `sparopt::Optimizer::optimize_query_expression()` |

Per-crate LOC measured locally only to *split the survey ask by subsystem* (A2 §2 allows
subsystem passes); this is not re-screening:

```
13700 lib/oxigraph/     (pulls oxrocksdb-sys -> EXCLUDED from grading path)
10268 lib/spargebra/
10008 lib/spareval/
 9848 lib/oxttl/
 7438 lib/oxjsonld/
 7346 lib/oxrdf/
 6969 lib/oxsdatatypes/
 5243 lib/sparesults/
 3542 lib/sparopt/
 3018 lib/oxrdfxml/
 2452 lib/sparql-smith/
 2317 lib/oxrdfio/
 1079 lib/spargeo/
```

## Step 2 — authorship lane

Runner for the survey dispatch: **Avocado / MetaCode via `~/.claude/skills/swebench-mt/mc.sh`**
(A2's declared owner). Claude (me) does not generate surfaces or ideas and does not write
contract prose. Cards stop at observable contracts + grader API surface; the
`Interface Contract` table is the deliverable in place of prose. (`00-ROUTER.md` §5)

## Step 3 — the composed lens

Checked `ledger/RUNS.md` + `reference/R6-fork-patterns.md` instantiation tables for prior use:

| A-shape | prior instantiations | available? |
|---|---|---|
| P1 silent per-item failure | **3** (spire, go-zero, graphiti) | **CLOSED — at ceiling** |
| P2 live visibility during iteration | 1 (ruby-rdf/sparql) | **AVOID — same domain (a SPARQL engine). Self-collision: "the same pattern in the same subsystem across two repos IS a peer collision"** |
| P3 ownership/lifetime lent-vs-materialised | 1 (open62541) | open, but Rust prior inverts (ownership cluster = Fork 1) |
| P4 snapshot vs view | 1 (franz-go) | open |
| P5 state across masking boundary | 1 (net-imap) | open |
| P6 revert-and-redo | 2 (rom-rb ×2, neither built) | **OPEN — under ceiling** |
| P7/P8/P9 | 0 | unproven |

**P2 is disqualified for this repo before the survey runs.** R6's shipped P2 instantiation is
`ruby-rdf/sparql` — a SPARQL engine, the exact same subsystem. A "live visibility during
iteration" card on oxigraph's evaluator would be P2 instantiated twice in one domain, which
R6 §"SELF-COLLISION IS THE REAL RISK" calls a peer collision regardless of repo. This also
puts a caution on any card that grades `QueryExplanation` mid-iteration counters.

- **Layer C, primary axis: AXIS 19 — closed extension points at a protocol boundary.**
  `R5-search-axes.md` AXIS 19. Strongest single measured axis (found 3 of 4 survivors' hosts
  in the bc-java v2 run). Greps: an enum used as a wire code point; dispatch throwing
  `unknown`; a registry map with **no public writer**; a commented-out registration API.
  Precondition confirmed present in this repo before choosing it: `spareval` has three
  extension seams (`ServiceHandler`, `CustomFunctionRegistry`, `QueryableDataset`) and
  `error.rs:25/41` carry `"The function {0} is not supported"` /
  `"The service {0} is not supported"` dispatch-throwing-unknown sites.
- **Layer C, secondary axis: AXIS 10 — observer noninterference.** Chosen because
  `R5` §"WHICH AXES SURVIVE LANGUAGE IDIOM" says axes whose wrong path is a **pipeline**
  choice survive a strong language idiom, while **data-structure**-choice axes erode — and the
  brief's standing Rust risk is exactly a data-structure prior. Axis 10's wrong path
  ("implement observation by invoking the real consuming operation and buffering its result;
  or rerun lazy work to reconstruct an explanation") is a pipeline choice.
- **Layer A, primary shape: P6 revert-and-redo**, preferring R6's documented free source for
  the step-2 constraint — **"THE SECOND FORMAT IS THE CONSTRAINT"**. oxigraph is a
  multi-format, multi-backend library (Turtle/TriG/N-Triples/N-Quads/RDF-XML/JSON-LD;
  in-memory `Dataset` vs RocksDB `Store`; local vs `SERVICE` dataset), so the second
  format/backend is already present and the caller need is self-evident. This is R6's
  answer to P6's KNOWN WEAKNESS (agents invent operational callers, which scores worst on
  realism).
- **Layer A, secondary shape: P8 error classification and recoverability** (unproven, zero
  instantiations). R6: *"Explicitly permitted by specs ... Good for standards-heavy repos,
  which we are short of."* oxigraph is standards-heavy, and the corrected form of the
  retracted "standards-pinned has no fork" rule is to check whether the clause **names an
  alternative** — SPARQL 1.1 §SERVICE SILENT and the extension-function clauses do exactly that.
- **Layer B: OMITTED — `R7-algo-catalogue.md` is QUARANTINED.** Not sourced from.

### Two repo-specific constraints written into the survey ask

1. **Rust per-language prior (measured, `R6` Part B).** persistence, COW, generational
   handles, `Arc::make_mut`, path-copying are **model-PREFERRED in Rust** -> Fork ~1. Any
   surface whose divergence is one of those is a dead surface here. Named as a ban in the ask.
2. **SPARQL 1.1 / XSD / Turtle are published W3C specs.** Anything whose correct behaviour
   is recoverable from the spec text is recall-solvable. The survey must mark each surface
   SPEC-PINNED / SPEC-SILENT / SPEC-NAMES-AN-ALTERNATIVE with the clause. The
   implementation-defined territory in a SPARQL engine is: query **planning/optimisation**
   (the spec says nothing about join order, filter pushdown or cardinality), the **explain /
   statistics** surface, **extension-point plumbing**, and **error taxonomy above the
   `SILENT` line**.

## Step 4 — surface-count derivation (A2 §2), written down BEFORE the ask

- Non-test LOC = 97,270 -> band **60k–150k -> ask for 15–20**.
- Subsystem cross-check: 13 crates, but `lib/oxigraph` (13.7k) is excluded from the grading
  path (RocksDB) and `sparql-smith`/`spargeo`/`lints` are marginal. The crates reachable in
  the measured 47 s / 4.5 s harness path are 8:
  `spareval, sparopt, spargebra, oxrdf, sparesults, oxsdatatypes, oxttl, oxrdfio` = **~55k LOC**.
- At 2–3 surfaces per major subsystem that is 16–24; the LOC band says 15–20. A2 says trust
  the subsystem count when they disagree — they do not disagree badly here.
- **Ask = 18 surfaces**, run as two subsystem passes (query engine: spareval/sparopt/spargebra;
  data/serialisation: oxrdf/oxsdatatypes/sparesults/oxttl/oxrdfio).
- Expected collapse (A2 §2): 15–20 surfaces -> **2–4 real candidates**. So the ≥8 card
  dispatch target is **not** reachable honestly on this repo and I will report the real
  number rather than backfill.

## Step 5 — the repo's own admissions

`/tmp/oxigraph-run/admissions.txt` — 70 hits over the 8 grading-path crates.
Command run (from the clone root):

```
grep -rnE "TODO|FIXME|not supported|unsupported|not implemented|NotImplemented|for now|we do not|we don't|cannot be|is ignored|silently" \
  lib/spareval/src lib/sparopt/src lib/spargebra/src lib/oxrdf/src lib/sparesults/src \
  lib/oxsdatatypes/src lib/oxttl/src lib/oxrdfio/src
```

Per crate: spareval 20, sparopt 15, oxttl 12, spargebra 10, sparesults 7, oxrdfio 3,
oxsdatatypes 2, oxrdf 1.

The eight strongest (fed verbatim into `survey.txt`; each to be re-verified against HEAD by
the surveyor, per A2 §3.2):

| # | site | verbatim admission |
|---|---|---|
| A1 | `lib/sparopt/src/optimizer.rs:1072` | `// We don't do join reordering inside of SERVICE calls, we don't know about cardinalities` |
| A2 | `lib/sparopt/src/optimizer.rs:548` | `// TODO: we can be smart and push some filters` |
| A3 | `lib/sparopt/src/optimizer.rs:466` | `// TODO: handle the case where the filter overrides an expression variable (should not happen in SPARQL but allowed in the algebra)` |
| A4 | `lib/sparopt/src/optimizer.rs:1261` | `// TODO: we should be smart and count as shared variables FILTER(?a = ?b)` |
| A5 | `lib/spareval/src/eval.rs:44` | `// TODO: make expression raise error when relevant (storage I/O)` |
| A6 | `lib/spareval/src/lib.rs:374` | `"EXISTS is not supported by the SPARQL expression evaluator"` |
| A7 | `lib/sparopt/src/type_inference.rs:319` | `VariableType::LITERAL \| VariableType::UNDEF // TODO: add xsd: cast functions` |
| A8 | `lib/oxrdfio/src/format.rs:61,108` | `// TODO: more combinations` (format/profile detection) |

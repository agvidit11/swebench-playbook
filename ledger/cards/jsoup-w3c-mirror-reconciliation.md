# jsoup-w3c-mirror-reconciliation

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `jhy/jsoup` @ `088614f4a1454232a1f03c63b7f80742f1f2a854`
- Seam: `org.jsoup.helper.W3CDom`
- Composition: semantic identity distinct from serialization × snapshot versus live view
- Trap: natural order loses information
- Routing: `MEASURE` with a chained three-step Lane-P probe
- A4: `ADJACENT`; no peer covers W3CDom correspondence, reverse application, or reconciliation

## A1 receipt

MIT; active 2026-10-01; 30,161 non-test Java LOC across eight principal packages; no agent artifacts or attributed commits; five open issues; warmed offline W3CDom suite 4.77s.

## User problem and base proof

I transform jsoup documents with W3C APIs such as XPath and XSLT. `W3CDom` creates a disconnected copy, so rebuilding after transformation loses held node references, user data, and source provenance. I need an opt-in conversion session that safely carries W3C changes back into the original document.

At base, moving/editing a W3C `<p>` and inserting `<em>` left the jsoup source unchanged. A W3C-to-source backlink existed, but no reverse lookup or apply API existed.

## Obligations

CONSTRAINT: The Mirror API retains identity-based links both ways. Application preserves surviving jsoup identity, refreshes inserted/removed links, and is repeatable. With two-sided edits, non-conflicting changes merge while conflicts throw `IllegalStateException` before source mutation.

DESIRED: An identity-aware session with a stable baseline, in-place reconciliation, refreshed correspondence, and preflighted atomic conflicts.

NON-DESIRED: Serialize/reparse; positional/value matching; unconditional W3C-wins; progressive mutation; stale mappings.

## Steps

1. `W3CDom.mirror(Document) -> W3CDom.Mirror` exposes both documents and nullable identity lookups in both directions, distinguishing equal siblings and surviving W3C reparenting.
2. `Mirror.apply()` reflects W3C-only moves, order, attributes, node data, insertions and deletions in place, reuses surviving nodes, refreshes links/baseline, and is idempotent.
3. Atomic two-sided reconciliation preserves one-sided/equal edits, rejects divergent scalar or competing child-sequence edits, leaves source/mappings/baseline untouched on conflict, and advances the baseline on success.

Pinned public symbols: `mirror`, public static final `Mirror`, `document`, `sourceDocument`, `sourceNode`, `w3cNode`, `apply`. Existing `SourceProperty` remains compatible.

Wrong branches: serialize/reparse; position-based reconciliation; W3C-wins; progressive apply; one-shot backlinks. Later steps own mapping refresh, surviving `==` identity, user data/source ranges, idempotence, and conflict atomicity.

Pure in-memory grading. Estimated production deltas: 80–130, 110–170, 80–140 lines; Step 2 should be narrowed below 150 during probe/build if needed.

Rating: P1 4, P2 4, P3 2, P4 3, P5 4, P6 2, P7 2 = **21/28 MEASURE**. Step 1 may use the non-final exemption; Steps 2/3 are predicted 2–3/5 and 1–3/5.


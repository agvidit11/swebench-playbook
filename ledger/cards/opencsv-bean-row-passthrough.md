# opencsv-bean-row-passthrough

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: canonical SourceForge `https://git.code.sf.net/p/opencsv/source` @ `68dedc22bf6377a057109b2f55791fa353cfa872` (`featureBug270`, maintainer-authored 2026-07-04)
- Seam: immutable accepted bean row -> source/mapping association -> ownership-aware write-back
- Trap: natural order loses information; independent filtering makes positional reconstruction lie
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `CLEAR`; no OpenCSV task or exact bean/edit/passthrough peer found

## User problem and base evidence

Vendors add columns that our Java bean does not own. When we parse their CSV, correct fields we do own, and write it back, OpenCSV keeps the header but blanks the vendor data. Preserve those unowned cell values on accepted rows while current bean values still control columns owned by the existing mapping strategy.

At base, parsing `Alice,"vendor, keeps this",A-1`, editing Alice to Alicia, and writing produced `Alicia,,A-1`. `CsvToBean.stream()` returns only beans; its processing path clones the source row but enqueues only `T`; filters and verifiers independently discard rows. `AbstractMappingStrategy.setFieldValue()` ignores columns without a mapped field, and `transmuteBean()` renders both an unmapped cell and an intentionally emptied mapped value as `""`.

A natural raw-row/bean zip substitute desynchronized after filtering and associated Bob with Alice's `secret-A`. A non-empty-cell overlay substitute resurrected a mapped value the caller intentionally cleared.

## Steps

1. Add immutable `CsvBeanRow<T>` carrying the bean, source header, source cells, and mapped-column membership, with defensive snapshots.
2. Add `List<CsvBeanRow<T>> CsvToBean.parseRows()`, preserving the exact accepted source row through existing filters, verifiers, exception handling, converters, and mapping strategy.
3. Add `void StatefulBeanToCsv.writeRows(Iterable<CsvBeanRow<T>> rows)`, emitting the source schema and merging current mapped bean values with preserved unmapped cells through the existing CSV writer.

CONSTRAINT: preserve source and column-ownership evidence at the accepted-row boundary, then use that evidence to recompose output.

NON-DESIRED: reread-and-zip raw rows to beans; preserve rejected-row cells; overwrite all cells from `transmuteBean()`; infer mapped ownership from non-empty output; mutate held row/header/cell snapshots; bypass current writer quoting/escaping.

Independent branches include filter/verifier/conversion rejection alignment, mapped-empty versus unmapped-empty authority, multivalued mappings owning multiple header positions, defensive snapshots, and writer quoting. Step 3 is a distinct write/recomposition operation that depends on the artifact and association from Steps 1–2. No single-turn fallback.

Activity recheck: the pinned commit is a stable five-commit public branch in the canonical repo; changes are documentation/parser-performance tests, target production code matches master, target failures reproduce, and the full offline suite passes.

Evidence: `/root/scout_opencsv` handoff and focused gate audit.

Rating: P1 4, P2 3, P3 3, P4 3, P5 4, P6 4, P7 3 = **24/28 MEASURE**.

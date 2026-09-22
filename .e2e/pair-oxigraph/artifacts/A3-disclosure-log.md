# A3 GATE 3 — disclosure log (re-run with total_count, after reviewer finding)

Date: 2026-09-22. Repo oxigraph/oxigraph. base_commit 450d2fe0ea8b9aa457ad41dbf542582d1d443150

## A. `gh api search/issues` with total_count

### query: `repo:oxigraph/oxigraph SILENT`
total_count: 21
  #1889 [closed] Keyless MINUS silently discards dataset read errors
  #1878 [closed] CONSTRUCT silently drops triples when term externalization fails
  #1928 [open] RDF/XML: attribute-value normalization not applied (newline in attribute kept as \n)
  #1938 [closed] SPARQL UPDATE LOAD: make sure the operation is atomic even when SILENT is set and that we insert the named graph even if the graph is empty
  #1647 [open] [oxjsonld] Handling unexpandable keys
  #1631 [open] Some federated queries with Wikidata seem to fail
  #1839 [closed] oxigraph.exe serve --location "D:\oxigraph-data" , can not start
  #1862 [closed] Specifying multiple RDF Datasets in URL-encoded POST request fails with 0.5.8 (and later)

### query: `repo:oxigraph/oxigraph SERVICE SILENT`
total_count: 6
  #1631 [open] Some federated queries with Wikidata seem to fail
  #1839 [closed] oxigraph.exe serve --location "D:\oxigraph-data" , can not start
  #1881 [closed] SPARQL XML parser trims literal boundary whitespace
  #1608 [closed] RocksDB wrapper panics with TryFromIntError on macOS when ulimit -n is unlimited
  #13 [closed] Custom functions
  #8 [closed] SERVICE clauses

### query: `repo:oxigraph/oxigraph MOVE graph`
total_count: 25
  #1957 [closed] Add Store::snapshot, a pinned read view that takes no lock
  #1688 [open] [Feature Request] Web-based UI for Oxigraph using Salvo
  #279 [open] Not everything is being deleted
  #1517 [open] Feature Request: Integrated Web UI for SPARQL Queries and Result Visualization
  #1560 [open] [Proposal] Full Geometry support, with geospatial indexing and GeoSPARQL 1.1 implementation
  #882 [open] Implement Sophia traits
  #498 [open] Could Oxigraph define a Default Base IRI?
  #88 [open] Oxigraph server - authentication support

### query: `repo:oxigraph/oxigraph COPY graph`
total_count: 9
  #658 [open] New high-level `Graph`/`Dataset` API
  #1957 [closed] Add Store::snapshot, a pinned read view that takes no lock
  #1737 [open] SHACL 1.2 Rules
  #1884 [closed] Slow query because a join with an unmistakable shared variable gets `keys = ` (empty) inside a `UNION`
  #1385 [closed] Update ruff requirement from ~=0.11.0 to ~=0.12.8 in /python
  #922 [closed] Custom TypeScript types for better RDF/JS compatibility
  #865 [closed] Rewrites the in-memory storage
  #639 [closed] Python "warning: unnecessary qualification"

### query: `repo:oxigraph/oxigraph custom function`
total_count: 45
  #1624 [open] Issue with custom functions in `SERVICE` call 
  #1852 [open] [parser] Expose Parser Implementation Details
  #554 [open] Add support for custom datatypes (inherited from base datatypes)
  #1849 [closed] Add QueryEvaluator::custom_(aggregate_)functions and make use of it to generate service descriptions
  #48 [open] Add full text search support to Oxigraph
  #640 [open] "'stdbool.h' file not found" by oxrocksdb-sys/build.rs during cargo build
  #1682 [open] Staged parallel execution in the current SPARQL evaluator
  #1746 [closed] Customize the max buffer size for parsing

### query: `repo:oxigraph/oxigraph custom aggregate`
total_count: 7
  #1849 [closed] Add QueryEvaluator::custom_(aggregate_)functions and make use of it to generate service descriptions
  #1682 [open] Staged parallel execution in the current SPARQL evaluator
  #1786 [closed] feat(dotnet): production-ready .NET bindings — Store, SPARQL 1.1, RDF I/O, async API, 280 tests, full docs
  #1366 [closed] Adds custom aggregate functions
  #1153 [closed] Support custom aggregation functions
  #1286 [closed] Migration from RDF-star to RDF 1.2
  #8 [closed] SERVICE clauses

### query: `repo:oxigraph/oxigraph EXISTS`
total_count: 46
  #885 [open] Poor performance on FILTER NOT EXISTS
  #1936 [closed] SPARQL: EXISTS: fixes error propagation
  #1885 [closed] sparopt: rewrite EXISTS on cartesian products and unions
  #1905 [open] [sparopt] `GRAPH` around non-BGP/path inners (and nested `GRAPH`) drops the outer graph binding.
  #1894 [open] Slow queries due to a variable-length path inside a sequence path
  #1871 [open] ORDER BY materialises its entire input unbounded; --timeout-s does not abort evaluation
  #1527 [open] New query evaluator using DataFusion
  #1899 [closed] Fix Graph Store POST creation status

### query: `repo:oxigraph/oxigraph explain plan`
total_count: 9
  #1871 [open] ORDER BY materialises its entire input unbounded; --timeout-s does not abort evaluation
  #1951 [open] Join reordering inside generated `Lateral` ignores outer bindings in `UNION` and filtered groups
  #215 [open] Oxigraph servers hangs with FILTER function in sparql
  #926 [open] Another strangely slow query
  #1710 [closed] Do not panic when explaining plan not convertable to SPARQL
  #1733 [closed] bugfix/optimizer: fix quadratic scaling of OPTIONAL in a JOIN on FK
  #217 [closed] Provide a way to display the query plan
  #470 [closed] Fix missing GSPO index compaction

### query: `repo:oxigraph/oxigraph atomic update`
total_count: 16
  #1896 [closed] Make Graph Store PUT replacements atomic
  #1047 [open] [Feature Request] RDF4J-compliant HTTP REST API
  #1938 [closed] SPARQL UPDATE LOAD: make sure the operation is atomic even when SILENT is set and that we insert the named graph even if the graph is empty
  #1864 [closed] Add --fail-on-named-graphs to load
  #1802 [closed] Inexplicably slow DELETE INSERT WHERE
  #1781 [closed] Update regex requirement from <2026.2.0 to <2026.6.0 in /python
  #1810 [closed] Bump the pip group in /python with 2 updates
  #1696 [closed] Disk-backed storage: `StrHash` lookup failure on a transactional batch of two same-resource updates

## B. Remote-branch sweep — the shortlist's "27 branches, all dependabot" is FALSE
```
total remote branches: 26
dependabot:            3
NON-dependabot:
  0.5
  comment-dataset-view
  context-loading
  custom-aggregations
  dealloc
  encoder
  fusion
  jsonld-scoped-context
  lateral
  lateral-opt
  logos
  main
  path-opt
  pyo3-wheels
  python-zig
  rocksdb
  rocksdb-lto
  rules
  spargebra-context
  sparql-exist
  speedb
  wip-text-counting
  zlib
```

## C. `--comments` on the open issues that touch a surviving surface
### #1624 (OPEN) — Issue with custom functions in SERVICE call  [surface S01/S03]
```
author:	Tpt
association:	collaborator
edited:	false
status:	none
--
This is very weird. Some questions:
1. Are you sure you are using the same Oxigraph version in both environment? If you don't update the docker images, `latest` might still point to an older version in one of the environments.
2. What is the SPARQL endpoint targetted by the `SERVICE` call?
3. May you point me to the github job that failed? It might help me understand things a bit better.
--
author:	vemonet
association:	contributor
edited:	false
status:	none
--
1. My bad, I just did a `docker pull` on the macos and I am now getting the same error, I must had a older version of oxigraph already pulled from some months ago, I can see these errors have been added ~3 months ago

```rust
    #[error("The custom function {0} is not supported")]
    UnsupportedCustomFunction(NamedNode),
```

So I guess the issue is mainly that this error with custom function not being defined should not be triggered inside a `SERVICE` block

2. It's an endpoint based on RDFLib: https://github.com/vemonet/rdflib-endpoint
3. Failing job: https://github.com/vemonet/rdflib-endpoint/actions/runs/21952568303/job/63407198144
--
author:	Tpt
association:	collaborator
edited:	true
status:	none
--
I have found the root cause:
- the query evaluator was building an evaluator for SERVICE clause content to retrieve which variables are bound.
- I recently modified Oxigraph to return a nice error when a custom function is not supported instead of just having its return value be always not defined.

#1634 fixes the issue by using a more direct method to retrieve SERVICE clause output variables
--
```
### #1951 (OPEN) — Join reordering inside generated Lateral ignores outer bindings  [surface S04/S09]
```
```

## D. Feature/roadmap sweep (A3 GATE 3 feature-side arm)
```
open 'enhancement'-labelled: 72
  #1926 Add query timeout to Python API
  #1875 spareval: consider supporting memory consumption bounds
  #1874 HTTP server: cancel SPARQL queries when the client disconnect
  #1873 spareval: Implement "TopK" optimization
  #1852 [parser] Expose Parser Implementation Details
  #1829 sparesults: additive positional row API for `SELECT` result serialization
  #1819 Add cross calendar comparison supports
  #1737 SHACL 1.2 Rules
  #1687 rdf 1.2 (rdf-star) meta queries very slow
  #1682 Staged parallel execution in the current SPARQL evaluator
  #1652 [Feature Request] Support gzipped formats in the python Store.load() function
  #1647 [oxjsonld] Handling unexpandable keys
roadmap-in-title: 0
AGENTS.md
```

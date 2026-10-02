# PROBES — every card's Avocado probe result, append-only

Lane P writes one row per probe. This is how we learn which trap classes and repos actually split
Avocado — read it before choosing the next card.

| date | machine | card | repo | trap class | contract words | Avocado n/5 | failures (stated / unstated / infra) | verdict |
|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | devvm6971 | gobgp step 2 divergent route | osrg/gobgp | natural order loses information | ~230 | 3/5 | 2 stated (reduce-first dropped an entry) | in band |
| 2026-10-01 | devvm6971 | gobgp step 3 divergent paths (v1) | osrg/gobgp | permissive helper | 297 | 3/3 reached | — | too easy → re-authored for route-target legality |
| 2026-10-02 | devvm6971 | go-zero goctl compatibility (single-turn) | zeromicro/go-zero | equivalence over a large domain | ~600 | 0/5 | 3 stated, 2 timeouts | being converted to 3-step |
| 2026-10-02 | devvm6971 | adaptix-typeddict-union-dump-selection s2 (ambiguity reject) | reagento/adaptix | equivalence over a large domain | 325 | 5/5 | 0 genuine (load-back row = base bug, info) | too easy → drop |
| 2026-10-02 | devvm6971 | adaptix-typeddict-union-dump-selection s1 (dump case selection) | reagento/adaptix | permissive helper | 242 | 4/5 real (1/5 graded) | 1 stated (stale __required_keys__); 3 = contract named buggy Literal loader as authority | contract defect; card dropped on s2 |
| 2026-10-02 | devvm6971 | phprrule-rset-split-reschedule s2 (rescheduleFrom) | rlanvin/php-rrule | permissive helper | 378 | 5/5 | 0 (1 infra hang, code complete) | too easy → drop |
| 2026-10-02 | devvm6971 | phprrule-rset-split-reschedule s1 (splitAt) | rlanvin/php-rrule | natural order loses information | 312 | 5/5 | 0 | too easy → drop. LESSON: trap is self-checkable by running the library's own iterator; Avocado verifies and escapes |
| 2026-10-02 | devvm6971 | geojson-antimeridian-bbox s2 (compute_bbox) | georust/geojson | natural order loses information | 311 | 5/5 | 0 | too easy |
| 2026-10-02 | devvm6971 | geojson-antimeridian-bbox s2b (amend: removed approach hint) | georust/geojson | natural order loses information | 329 | 5/5 | 0 | too easy → drop |
| 2026-10-02 | devvm6971 | geojson-antimeridian-bbox s1 (collection union) | georust/geojson | natural order loses information | 240 | 5/5 | 0 | too easy; "antimeridian bbox" recalled as largest-gap |
| 2026-10-02 | devvm6971 | config-rs-writable-layer-delta s2 (layer_between) | rust-cli/config-rs | natural order loses information | 294 | 1/5 | 3 stated (array shrink under upper index override copies upper value), 1 unstated (absent=no-opinion not restated) | IN BAND (fragile, rides on one case) → ACTIVE single-turn |
| 2026-10-02 | devvm6971 | config-rs-writable-layer-delta s1 (changes_since) | rust-cli/config-rs | equivalence over a large domain | 302 | 5/5 | 0 | too easy → folded |
| 2026-10-02 | devvm6971 | unyt-pint-bridge s2 (import + round trip) | yt-project/unyt | natural order loses information | 257 | 0/5 | 5 stated (define_unit symbol collisions come back base-expanded; 4/5 didn't revisit step-1 base-expanded export); probe defects: coincidental import matches, wrong preserve baseline; oracle used attribute side-channel | bimodal → one amend (single-turn merged) |
| 2026-10-02 | devvm6971 | unyt-pint-bridge s1 (export identity) | yt-project/unyt | permissive helper | 264 | 5/5 | 0 | too easy; table-patch trap never fired |
| 2026-10-02 | devvm6971 | commonmark-java link-retarget s1 (inline) | commonmark/commonmark-java | permissive helper (source spans) | 301 | 1/5 strict, 2/5 lenient | 3 stated (span drift after \| in table cells), 1-2 implied-unstated (unescaped \| breaks table) | IN BAND → ACTIVE single-turn |
| 2026-10-02 | devvm6971 | commonmark-java link-retarget s2 (reference defs) | commonmark/commonmark-java | natural order loses information | 342 | 5/5 (+16-case amend 5/5) | 0 | too easy → dropped |
| 2026-10-02 | devvm6971 | comfytable-cell-style (single-turn) | Nukesor/comfy-table | permissive/strict helper | 306 | 4/5 effective (3/5 strict) | 1 stated (22 leaves dim), 1 unstated build break (--all-features non_exhaustive match) | too easy → drop; Avocado handles reset spellings broadly |
| 2026-10-02 | devvm6971 | unyt-pint-bridge merged single-turn (amend) | yt-project/unyt | permissive helper + natural order | 261 | 0/5 | all stated (hbar->dirac_constant 5/5, mcd 4/5, define_unit collisions); same cliffs every impl | park — fixing = naming cases |

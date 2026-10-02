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

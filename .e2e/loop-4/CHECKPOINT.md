# CHECKPOINT — loop-4

**Lane:** concurrency primitives, schedulers, async runtimes, resource lifecycle, job/workflow
engines, caching and eviction.
**Run dir:** `/home/agvidit/swebench-playbook/.e2e/loop-4/`
**Clones:** `/home/agvidit/swebench-playbook/.e2e/loop-4/clones/<name>`
**Task-scoped /tmp prefix:** `/tmp/loop4-*` — never generic names.
**Docker lock:** `flock /tmp/swebench-docker.lock <cmd>` — NOT held.

## Current position
ACT `A1` — repo screen, from scratch (no prior shortlist for this territory).

## Fixed environment facts (measured 2026-09-22)
- host: go1.26.5, java 1.8.0_502, mvn 3.6.3, docker 29.7.2, 166 cores, 223G RAM.
  **no ruby, no cargo on host** → Ruby/Rust repos need containers.
- `/tmp/llc` HEAD `d8472c4c` 2026-09-02 — **20 days stale**; a zero local hit is UNKNOWN.
  `/tmp/llc/tmp/tasks` = 15,985 author dirs.
- Maven direct central 429s → GCS mirror `https://maven-central.storage-download.googleapis.com/maven2`,
  `docker build --network=host`.

## Claimed by other pairs — do not touch
- loop-1: data stores / storage engines (frostdb, oxigraph, immudb retired)
- loop-2: protocols / networking / RPC (santuario, curator, connect-go retired)
- loop-3: build systems / compilers / linters (prism, lego retired)

## Retired tonight (whole-session) — do not re-source
polarsignals/frostdb, oxigraph/oxigraph, codenotary/immudb, apache/santuario,
apache/curator, connectrpc/connect-go, ruby/prism, go-acme/lego.

## Lane saturation warnings (from dispatch)
- caffeine 17 peers, qdrant 28, roaring 25. Phrase away from `idempoten*` (4,899 corpus hits),
  `round-trip` (3,081), `converge` (2,065), `invalidat*` (1,946).
- Already killed on peers by the find-repos shortlist and IN MY LANE:
  `hibiken/asynq` (≥10), `quartz-scheduler/quartz` (≥8), `resilience4j` (≥7),
  `spring-batch` (≥7), `golang-migrate` (≥8).
- Target shape: `semantic_bugs` (7 passed / 7), never `expose_interface` (1 / 13).

## Done
- Read PAIR-COMMON.md, LOOP-BRIEF.md, 00-ROUTER.md, A1.
- Read `/home/agvidit/swebench-playbook/.e2e/find-repos/artifacts/shortlist.md` as a CLAIM
  (36 repos screened, 4 survivors). `concourse/concourse` is in my lane and is one of its
  survivors — treated as a claim, re-screened first-hand, not accepted.

## Next concrete commands
1. Read peer repo pools (jayzong / aaitemp) for lane hits.
2. G1 live peer sweeps (`gh search code --owner codimango "<repo>"`, spaced) over the
   candidate set; local corpus sweeps in parallel.

## In flight
none

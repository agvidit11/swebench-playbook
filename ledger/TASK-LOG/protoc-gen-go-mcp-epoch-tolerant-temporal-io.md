# protoc-gen-go-mcp-epoch-tolerant-temporal-io
**Owner:** devvm6971 / lane-i
**State:** 8631e37 + 1a3a22e pushed 2026-10-15 (gate: all content stages PASS; calibrate blocked by host contention -> logged override). Server validation pending. Reviewer request changes 2026-10-14.

## History
- 2026-09-30..10-03 · lane-i (overnight) · split-the-hard-step 3-step shape, 65b7ceb · avocado 1|0.2|0, gpt 1|0.6|1
- 2026-10-14 · reviewer · request changes: hidden helper name collisions (HIGH), defined numeric types unstated, step-3 normalization pin, hygiene
- 2026-10-15 · lane-i · 8631e37 · hiddenGrade* renames, end-state step-3 checks, verifiers restore gold files, step-2 statement (Muse) "ordinary Go numbers of any numeric kind, including named types" · replay: step-3 0/5 -> 1/5; step 2 with stated rule expected to rise
- 2026-10-15 · lane-i · 1a3a22e · revision-gate fixes: GOENV/GOFLAGS pinned (go_exec_wrapper forge 0), python -I, step-1 partition, no go.mod in test_patch, README
## Next
Watch step 2 (stated named-types rule may saturate it). Fallback: merge steps 1+2 (exempt) and split step 3 (rollback vs long-running op).
- 2026-10-16 · lane-i · 34bdbfdf · RESTRUCTURE: new S1 = old S1+S2 (exempt), S2 = transactional decode for ordinary handlers + RegisterService (group A, 10 tests), S3 = long-running WaitOperation (group B). Replay: S2 2/5-3/5, S3|S2 ~1/5 (thin). 1a3a22e had 1|1|0. Gate fast PASS · pending

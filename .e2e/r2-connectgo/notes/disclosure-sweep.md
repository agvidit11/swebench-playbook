# GATE 3 pre-sweep — connectrpc/connect-go disclosed zones (run BEFORE the merge stage)

Repo: `connectrpc/connect-go`, clone `/tmp/connectgo-run/connect-go`, HEAD
`2168d015cc8fbe59e023ec58e3ed99c78c5364c6` (2026-09-22).

Structural note found while sweeping: the whole `connecthttp/` package is **new** — it was
created by `842cb19 Proposal v2 (#951)`. `git log -- connecthttp/` returns only 5 commits.
So the protocol layer has almost no post-refactor history, which cuts both ways: little public
PR exposure on the new file paths, but the v2 proposal thread (#951) is a large public design
document that discusses the protocol layer at length.

## Open issues, all 17, read for direction disclosure

`gh issue list --repo connectrpc/connect-go --state open --limit 40`

| # | title | verdict for ideation |
|---|---|---|
| 983 | Flaky test `TestClientDisconnect/http2/handler_writes` returns `Unknown` instead of `Canceled` | **BURNED** — maintainer `emcfarlane` replies "we want to try tighten this error case if possible so a `Canceled` may be propagated correctly". Client-disconnect-mid-write error classification is a disclosed direction. Also a flaky test: keep `TestClientDisconnect` out of `pass_to_pass`. |
| 907 | `sendMaxBytes` incorrectly applied to EndStream control frames in streaming RPCs | **BURNED** — PR #908 open with the remedy. |
| 828 | Need to be able to handle low-level marshalling errors | **BURNED** — `emcfarlane` posts the v2 remedy verbatim, with code, in the thread (context-aware codec decorator). Codec-marshal-failure observability is disclosed. |
| 823 | Ability to close server side of BidiStream from separate goroutine | **BURNED** for bidi half-close concurrency. |
| 781 | Consider exposing `connectCodeToHTTP` | **BURNED** for the Connect-code↔HTTP-status mapping surface. |
| 774 | unary response has zero messages due to `io.EOF` for all `io.EOF` errors | **BURNED** — `jhump` writes the remedy: "When the EOF is the former, we should wrap it with an RPC 'unavailable' error instead of incorrectly interpreting it as a cardinality violation". Unary EOF-vs-cardinality classification is disclosed. |
| 620 | Unenforced discard limits | **BURNED** — two maintainers debate the remedy for `discardLimit` vs `WithReadMaxBytes` interaction, *including a reproduction that loops over connect / grpc / grpcweb clients*. This is exactly the "over-limit message detectable only after decompression" surface the shortlist suggested. Dead. |
| 604 | Options for safely handling slow clients | **BURNED** for write-side backpressure / slow-consumer policy. |
| 879 | Separate handle of streaming timeout settings | **BURNED** for per-stream vs per-call timeout policy. |
| 924, 816, 793, 694, 672, 665, 451, 356 | registration API, `rpc.system` in `WithRecover`, protojson options, exporting memhttp, streaming-request retry, observability foundations, generics aliases, Go-release TODOs | not in the lens; noted for completeness |

## Recent merged PRs on the protocol layer (hard-kill zone, §7.1)

```
2168d01 Set Connect-Timeout-Ms when less than a millisecond remains (#984)
fd2bdcb Modernize use of errors.As and new (#986)
6b72ead Reject a negative Connect-Timeout-Ms instead of expiring the context (#982)
a807df5 Fix WithCompressors with no arguments to disable compression (#978)
842cb19 Proposal v2 (#951)
```

- **Connect-Timeout-Ms encoding/rounding/validation is burned twice over** (#982, #984, both in
  the last handful of commits). Do not ideate on timeout header encoding.
- **`WithCompressors` with no arguments** is burned (#978).
- Closed-but-relevant: **#892 "Fix CallInfo header/trailer propagation on error responses"** and
  **#964 "Fix dropped headers on errStreamingClientConn"** — header/trailer propagation on the
  error path is a merged public fix. Treat as burned.

## Peer-task dedup on this repo

- `gh api repos/codimango/swe-bench-pro-ritesh33/git/trees/main?recursive=1` →
  `ritesh33_connectrpc__connect-go-e299aa6-v1`, **single-turn**, on v1 @ `e299aa6`.
  Graded file: `tests/gold/duplex_http_call_test.go`.
  Its `instruction.md`, read in full:
  > "There's a crash that shows up when multiple streaming RPCs are running concurrently. The
  > internal pipe used to pass request body data along isn't created upfront — it gets set up
  > lazily the first time someone tries to send data through it. The problem is that another
  > goroutine can race in and try to close the write side of that pipe before it's ever been
  > created. Since it doesn't exist yet, you get a nil pointer panic."
  **Verified subject: the lazy request-body pipe lifecycle in `duplex_http_call.go`.** Burned
  zone = pipe creation/close ordering in that one file. It does NOT touch the protocol layer,
  error classification, trailers, framing or compression. Shortlist's "if it sits in
  `protocol_grpc.go`, drop to rank 4" condition is **not** triggered.
- Corpus sweep `grep -rl "connectrpc\|connect-go" /tmp/llc/tmp/tasks` (15,985 task files) → 3 hits:
  `swe-bench-pro-noelleli/spark-connect-go-add-df-support.md` (Apache Spark, homograph),
  `swe-bench-pro-gauravgupta1/repeated-query-params.md` (**connectrpc.com/vanguard**, a different
  repo — REST↔RPC transcoding of repeated query params), `swe-bench-aai-labs-ollo/…` (incidental).
  **Zero peer tasks on connect-go itself beyond the ritesh33 one.**

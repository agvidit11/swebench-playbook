# Card C13 — response trailing metadata must mean the same thing on all three wires

Repo `connectrpc/connect-go`, module `connectrpc.com/connect/v2`, base
`2168d015cc8fbe59e023ec58e3ed99c78c5364c6`.

## Composition

- **C-axis:** R5 axis **6 — failure-atomic callback mutation**, composed with R5 **AXIS 19 —
  closed extension points at a protocol boundary**. The injected fault is a piece of the
  handler's *own* optional metadata that the chosen wire format cannot carry; the boundary is the
  one `Close(err)` call site behind which three wire encodings live.
- **A-shape:** R6 **P6 revert-and-redo**, in its `THE SECOND FORMAT IS THE CONSTRAINT` form
  (`R6-fork-patterns.md:321-328`). Step 1 fixes the protocol where the fault is fatal; step 2
  requires the same handler to behave identically on the other two, where the natural step-1
  shape (repair it inside the protocol writer that failed) cannot reach.

## Step 1 — requirement

A streaming handler that attaches response trailing metadata and then finishes by returning an
error must have that error's code and message reach the client **on every protocol the server
speaks**, whatever bytes the trailer value contains, and whether or not the handler had already
sent messages. Messages already sent must still be received.

- **Compositional invariant:** the RPC's primary outcome is independent of the serialisability of
  its optional metadata.
- **The tension:** the terminal frame carries *both* the status and the metadata, so a failure
  while encoding the metadata is, mechanically, a failure to deliver the status — you cannot
  report "I could not encode your trailer" through the channel that just failed.

## Step 2 — requirement

For one and the same handler, the set of response trailers a client observes must be identical on
every protocol, and identical whether or not the handler sent a message before finishing. An entry
that cannot be represented on all three must be absent on all three; one that all three can carry
must arrive byte-identical, with repeated values in the order the handler added them.

- **Compositional invariant:** what the caller observes is a function of the handler, not of the
  wire format the caller happened to pick.
- **The tension:** *fidelity* (deliver exactly what the handler set — Connect can, because its
  trailers live in a JSON body where the HTTP field grammar does not apply) versus *portability*
  (one handler, three protocols, one observable contract). Satisfying fidelity per-protocol is
  what HEAD does and it is why the same handler yields six different results.

## HEAD citation and nearest presence

| what HEAD does | where |
|---|---|
| Connect streaming serialises the trailer map into the end-of-stream JSON message, so arbitrary bytes pass through untouched | `connecthttp/protocol_connect.go:849` → `MarshalEndStream` at `:872`, `connectEndStreamMessage` at `:1301` |
| gRPC writes trailers through `http.TrailerPrefix`; `net/http` silently discards any field value it considers illegal | `connecthttp/protocol_grpc.go:594-599` |
| gRPC-Web, **if nothing has been written yet and there are no custom headers**, merges trailers into the HTTP *header* block | `connecthttp/protocol_grpc.go:566-571` |
| gRPC-Web otherwise writes them into a body envelope with `http.Header.Write`, and **a write failure becomes the RPC's result** | `connecthttp/protocol_grpc.go:576` → `MarshalWebTrailers` at `:608`, the fatal line at `:619-621` |
| gRPC detail marshalling failure also replaces the handler's code and message | `connecthttp/protocol_grpc.go:966-971` |

**Nearest presence, verbatim** — the closest thing that already exists to the claimed absence:

```go
	if err := trailer.Write(raw); err != nil {
		return connect.Errorf(connect.CodeInternal, "format trailers: %s", err).WithCause(err)
	}
```
`connecthttp/protocol_grpc.go:619-621`. This *is* a failure path for an unencodable trailer — it
exists and it is reached. What it fails to cover is that its return value is the value of
`Close(err)`, so the handler's own `err` is discarded: the library notices the problem and then
reports it *instead of* the RPC's result rather than *alongside* it. There is no equivalent site
at all on the Connect path (nothing checks) or on the gRPC path (`net/http` swallows it below us).

A second nearest presence, for the uniformity half:

```go
	// gRPC always sends the error's code, message, details, and metadata as
	// trailing metadata. The Connect protocol doesn't do this, so we don't want
	// to mutate the trailers map that the user sees.
```
`connecthttp/protocol_grpc.go:557-559`. The comment shows the authors already reasoned about the
two protocols disagreeing about the trailer map — and resolved it by *copying* the map per
protocol, which is exactly what lets the three diverge.

## MEASURED, at base_commit — the whole point of the card

Handler sets one response trailer `Probe-Key`, then returns `connect.NewError(CodeAborted,
"handler boom")`. One handler, one `connecthttp.Mount`, three client transports.

| trailer value | sent a message first? | Connect | gRPC | gRPC-Web |
|---|---|---|---|---|
| `"a\x00b"` | no  | `aborted`, value **verbatim** | `aborted`, value **dropped** | `aborted`, value **dropped** |
| `"a\x00b"` | yes | `aborted`, value **verbatim** | `aborted`, value **dropped** | **`internal` — the handler's status is destroyed** |
| `"a\r\nb"` | no  | `aborted`, verbatim (CRLF intact) | `aborted`, dropped | `aborted`, dropped |
| `"a\r\nb"` | yes | `aborted`, verbatim | `aborted`, dropped | `aborted`, **rewritten to `"a  b"`** |
| `"  padded  "` | either | verbatim | verbatim | **trimmed to `"padded"`** |
| `"plain"` | either | exact | exact | exact |

Six outcomes for one line of handler code, and one of them loses the handler's result. The
`\x00`/send-first cell and the `\x00`/no-send cell differ **within the same protocol**, purely
because the trailers-only fast path at `protocol_grpc.go:566` was eligible in one and not the
other.

Reproduction is in `.e2e/r2-connectgo/artifacts/probe-outputs.md`; the grading assertion used
throughout is `/tmp/connectgo-run/grader_test.go`, and at base it fails **23 subtests of 88**.

## Motivating caller

connect-go's single selling point is that one `http.Handler` serves Connect, gRPC and gRPC-Web at
once — the README and the v2 proposal both lead with it. A service that attaches a request-id or a
billing counter as trailing metadata, and is called by a Go gRPC client, a browser gRPC-Web client
and a curl-able Connect client, gets three different answers today, and the browser client is the
one that can lose the error entirely. This is not a hypothetical caller: `protocol_grpc.go:591-593`
already says *"Breaking this logic breaks Envoy's gRPC-Web translation."*

## Interface Contract

**Every symbol the graded tests touch already exists at `base_commit`. Nothing is coined.**

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| `connect.CallInfo.ResponseTrailer()` | method | `*connect.Header` | IN-BASE (`connect.go:742`) | n/a |
| `connect.Header.Add/Set/Get/Values` | methods | `string`, `[]string` | IN-BASE (`connect.go:607-632`) | n/a |
| `connect.CallInfoForServerContext` | func | `(*CallInfo, bool)` | IN-BASE (`connect.go:1095`) | n/a |
| `connect.NewClientContext` | func | `(context.Context, *CallInfo)` | IN-BASE (`connect.go:1075`) | n/a |
| `connect.NewError` / `connect.CodeAborted` / `connect.CodeOf` / `(*Error).Message` | func/const/method | — | IN-BASE (`connect.go:966`, `:818`, `:1103`, `:991`) | n/a |
| `connecthttp.Mount` / `NewTransport` / `WithGRPC` / `WithGRPCWeb` | funcs | — | IN-BASE (`connecthttp.go:240`, `:193`, `option.go:34`, `:41`) | n/a |
| `pingv1connect.RegisterPingServiceHandler` / `NewPingServiceClient` | generated | — | IN-BASE | n/a |
| `memhttptest.NewServer` | func | — | IN-BASE | n/a |

There is no new exported API in either step. The contract is stated entirely as behaviour through
`connect.CallInfo`.

## Observable Schema

**Not applicable — the deliverable is not a collection of records.** The observable is the value
of an accessor that already exists (`CallInfo.ResponseTrailer().Values(k)`) and an error code from
an accessor that already exists (`connect.CodeOf`). The container, element, field names, value
domain and lifetime are all fixed by `net/http.Header` and `connect.Header`, which ship at base.
This is the "minimal existing-vocabulary signal" row of `A2` §6, not the "newly coined record" row.

## Named wrong-shape per step, and why a capable model writes it

**Step 1 wrong shape — "make `MarshalWebTrailers` non-fatal."** Catch the `trailer.Write` error at
`protocol_grpc.go:619`, drop the offending entries, retry, and return nil. *Why a capable model
writes it:* the failure is reported from exactly that line, the stack ends there, and the fix is
four lines. It is the smallest change that makes the failing observation pass. It is observably
wrong for step 2: it never runs on the trailers-only branch two screens above it
(`protocol_grpc.go:566-571`), never runs for Connect, and never runs for unary Connect, so the
same handler still yields three different trailer sets.

**Step 2 wrong shape A — "fail the call."** Validate centrally and, on an illegal value, end the
RPC with `CodeInternal` on every protocol. *Why a capable model writes it:* **measured — 5 of 5
cold models chose exactly this** when asked to make the behaviour predictable without being told
which way (`/tmp/connectgo-run/forkB-*.out`). It is the loud, defensible, fail-fast answer. It is
observably wrong under step 1's invariant, which it silently repeals: the handler's `aborted` is
destroyed on *all three* protocols instead of one.

**Step 2 wrong shape B — "validate with `httpguts.ValidHeaderFieldValue` and stop."** *Why:* it is
the canonical Go predicate and it is what `net/http` itself uses, so it looks authoritative.
It is observably wrong for `"  padded  "`: that value is a perfectly legal HTTP field value and
still does not survive gRPC-Web's in-body trailer block, because the block is parsed back with
`textproto`, which strips surrounding whitespace. A solver that keys on legality rather than on
round-trip identity passes every `\x00`/`\r\n` case and fails the whitespace ones.

## Determinism seam [R09]

No wall clock, no concurrency, no network. The fault is injected as **data** — a byte in a trailer
value — which is the most deterministic injection point available. The transport is
`internal/memhttp/memhttptest`, an in-memory `http.Server` already used by the repo's own suite.
Every assertion is a comparison of two strings or a `connect.Code`. `go test ./connecthttp/ -run
TestGrade` completes in **0.18 s**.

## Predicted per-arm rate, per step

| step | avocado | opus | gpt | reasoning |
|---|---|---|---|---|
| 1 | 2–3 / 5 | 4 / 5 | 4 / 5 | one protocol, one named failure line; the search is bounded. Risk: **too easy** — this is P6's documented step-1 drift. Loaded deliberately by requiring the no-send case and the already-delivered-messages case as well. |
| 2 | 1–2 / 5 | 2–3 / 5 | 2–3 / 5 | five write paths plus the whitespace case; the measured model prior (5/5) is the *opposite* resolution |

**What stops avocado passing step 1 outright?** Honest answer: possibly nothing. Step 1's failure
line is named in the error message the test prints. This is the card's main calibration risk and
it is recorded as such, not argued away.

## Step-1 guard cases owned by step 2

Step 2's `fail_to_pass` must include, as its own cases (not as step 1's IDs in `pass_to_pass`):

- `grpcweb / value "a\x00b" / sent a message first` → code is `aborted`, message is `handler boom`
  — i.e. step 1's invariant re-asserted inside step 2's suite, because the natural step-2 shape
  ("fail the call with internal") regresses precisely this.
- `grpcweb / value "a\x00b" / sent a message first` → **one** message was still received.

## Inter-step file overlap

| step | files | relation |
|---|---|---|
| 1 | `connecthttp/protocol_grpc.go` | — |
| 2 | `connecthttp/header.go`, `connecthttp/server_stream.go`, `connecthttp/protocol_connect.go`, `connecthttp/protocol_grpc.go` | **incremental on step 1**, and it must *remove* step 1's local repair from `protocol_grpc.go` |

Overlap is deliberate and is the P6 signature: step 2 rewrites the file step 1 edited. The
scaffold must make step 2 a delta, not a rebuild from base.

## Size estimate

80–140 net lines across 3–4 files. One predicate (round-trip representability), one application
point in the shared handler path, and the removal of three per-protocol behaviours. Primitives
reused: `toHTTPHeader`/`mergeHeaders`/`protocolHeaders` in `header.go`, `handlerStream.flushTrailer`
in `server_stream.go`.

## Self-audit — 13 card-stage items, 4 deferred

| item | verdict | evidence |
|---|---|---|
| R01 unstated requirement | **PASS** | The thing that nearly failed it: the **container-and-order** of repeated trailer values. I had to add "with repeated values in the order the handler added them" to step 2 explicitly, because a solver that rebuilds the map through a `map[string]string` would pass every single-value case and fail nothing I had written. Now pinned in the contract and asserted in `TestGradeC`. |
| R02 unreachable symbol | **PASS** | The thing that nearly failed it: I first wrote the observable as "the handler is told its trailer was dropped", which needs a symbol that does not exist. Rewritten as "the client observes the same set", which uses `CallInfo.ResponseTrailer()` only. Every token in the Interface Contract is IN-BASE; the stated ratio is 0 coined of 14. |
| R04 mechanism naming | **PASS** | Neither step names a file, function, algorithm or data structure. Both steps are stated as "what the client observes". |
| R05 grade against a library export | **PASS** | The reference answer is not callable from inside the solution. `httpguts.ValidHeaderFieldValue` is the obvious library predicate and it is **deliberately not sufficient** — the whitespace case defeats it — so importing the library export produces a *failing* solution, which is the inverse of the R05 risk. |
| R06 "only X / never Y" adversarial case | **PASS** | Step 2 says "must be absent on all three". The adversarial case is `"plain"` and the 4-value repeated list in `TestGradeC`, which prove the solver did not simply drop everything. Both are in the graded set. |
| R07 realism | **PASS** | Trailing metadata across a multi-protocol mux is the library's own advertised use; the repo already worries about Envoy's gRPC-Web translation at `protocol_grpc.go:591-593`. |
| R08 pinned spec vs tolerant tests | **FAIL → repaired, and a residual remains** | First draft said only "identical across protocols" while the tests asserted *absent*. Two defensible readings — absent-everywhere, or normalise-everywhere-and-deliver — and the tests only accepted one. Repaired by pinning "must be absent" in the step-2 requirement. **Residual risk: a solver who trims `"  padded  "` to `"padded"` on all three protocols has satisfied "identical" and will still fail.** Owner: `B2`, which must carry the word "absent" verbatim. |
| R09 determinism | **PASS** | No clock, no goroutine ordering, no network. 0.18 s. |
| R11 | **PASS** | Both steps assert through the same public entry point the repo's own tests use. |
| N01 | **PASS** | Substantial: 5 divergent write paths, not a one-line guard. |
| N02 | **PASS** | Not a mechanical-volume edit. |
| N03 | **PASS** | Grounded in a measured defect, not an invented feature. |
| N04 anti-overcorrection | **PASS** | 80–140 net lines, not "under 20 or two shipped functions composed". |
| R03 | deferred → `A3` GATE 4 rollouts |
| R10 | deferred → `B3` |
| R12 | deferred → `B3` |
| R13 | deferred → `B5`/server |

### Three-word recall test

*"Validate trailer bytes"* is three words and names a **wrong** answer (wrong shape B). The correct
answer — round-trip identity through three different serialisations, one of which is a JSON
object, one an HTTP trailer block and one a `textproto`-parsed body frame — has no three-word name.
The 10 cold probes support this: all ten named a location, none named the whitespace case.

### Existing-vocabulary test

Nouns in the observable contract: *response trailer, value, key, code, message, protocol, message
count*. **All seven are already in the library's vocabulary.** Zero coined.

### Named residual risks (required non-PASS content)

1. **R08 residual above** — "identical" admits normalise-everywhere; the contract must say "absent".
2. **Step 1 may be too easy.** Recorded, not argued away. If the server says "too easy" on step 1,
   the cheap direction is to fold step 1 into step 2 and re-cut a harder step 1.
3. **Design fork measured at 1.** 5 of 5 cold models, given step 2's constraint, proposed the
   intended location and mechanism (`forkA-*.out`). The candidate's difficulty is therefore SEARCH
   and QUALITY, not DESIGN. `A3` GATE 4 is the gate that decides whether that is enough.

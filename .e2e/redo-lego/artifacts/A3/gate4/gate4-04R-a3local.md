# GATE 4 — A3-LOCAL outcome-variance probe, candidate 4R. **PRIMARY gate, never run on this repo before.**

The prior run recorded this line as *"NOT RUN — not runnable in this act"* and both its GATE-5
kills inherited that caveat. It is runnable. This is the measurement.

## Procedure, per `A3 GATE 4` A3-LOCAL, steps 1–5

**1. CONSTRAINT taken verbatim from the card.** `/tmp/redo-lego-g4/build-prompt.txt` quotes the
card's `CONSTRAINT:` block unchanged and adds only mechanical rules (change the repo in place, no
new exported identifier, existing tests must pass, **do not touch any `_test.go`**, work offline).
The contract was not improved.

**2. Five throwaway assertions, in a scratch file** (`/tmp/redo-lego-g4/sketch_test.go`), never
under `<task>/tests/`. Each observes the discriminating behaviour, not a proxy:

| id | what it observes |
|---|---|
| S1 | tlsalpn01 — a connection the challenge server **accepted** (TLS handshake completed) is dead after `CleanUp` returned nil |
| S2 | tlsalpn01 — a teardown that could not be performed is **not** reported as success |
| S3 | http01 — `CleanUp` always finishes; it never blocks on a signal already consumed |
| S4 | http01 — a connection accepted before teardown is dead after `CleanUp` returned nil |
| S5 | sanity / p2p — the ordinary path still returns nil and releases the address, both servers |

**3. Validated at `base_commit` BEFORE use** — `/tmp/redo-lego-repro` @ `58468399`:

```
S1 after CleanUp: alive=true  --- FAIL: TestS1_TLSALPN_AcceptedConnDeadAfterCleanUp
S2 second CleanUp err=<nil>   --- FAIL: TestS2_TLSALPN_FailedTeardownReported
                              --- FAIL: TestS3_HTTP01_CleanUpAlwaysFinishes   (blocked 4.00s)
S4 after CleanUp: alive=true  --- FAIL: TestS4_HTTP01_AcceptedConnDeadAfterCleanUp
S5 tlsalpn01/http01 clean     --- PASS: TestS5_OrdinaryTeardownStillClean
```

Four discriminating assertions fail at base; the sanity assertion passes. The sketch measures
something.

> **Instrument defect found and fixed mid-gate, recorded because it would have inverted the
> result.** The first `roundTrip` helper read a fixed 64-byte window. An HTTP response is longer
> than that, so the *second* call read the tail of the *first* response out of the socket buffer
> and reported a dead connection as alive. Under that reader, S1 "failed" on all five
> implementations — a result I would have reported as outcome variance. The helper now consumes a
> complete response via `http.ReadResponse`, and S1 was re-validated as still failing at
> `base_commit` before regrading. This is the same class of error as frostdb's assertion never
> observing serialization completion, caught because GATE 4 step 3 forces a base-commit check.

**4. Five cold implementations from CONSTRAINT alone**, five separate clones at `base_commit`,
`mc.sh` / MetaCode, no other input. Every one of them produced a real change:

| impl | files | net lines | upstream `go test ./challenge/...` | `_test.go` touched |
|---|---|---|---|---|
| 1 | 2 | +127 / −57 | all ok | none |
| 2 | 2 | +116 / −16 | all ok | none |
| 3 | 2 | +108 / −12 | all ok | none |
| 4 | 2 | +122 / −29 | — | none |
| 5 | 2 | +101 / −22 | — | none |

Note the scope: 89–127 net lines across 2 files, i.e. squarely inside GATE 6's 80–150 target band.
This is not a trivia candidate being one-shot; it is a correctly-sized one being one-shot.

**5. Result.**

| assertion | impl-1 | impl-2 | impl-3 | impl-4 | impl-5 | n/5 |
|---|---|---|---|---|---|---|
| S1 tlsalpn01 conn dead | PASS | PASS | PASS | PASS | PASS | **5/5** |
| S2 failed teardown reported | FAIL | FAIL | FAIL | FAIL | FAIL | **0/5** |
| S3 http01 never blocks | PASS | PASS | PASS | PASS | PASS | **5/5** |
| S4 http01 conn dead | PASS | PASS | PASS | PASS | PASS | **5/5** |
| S5 sanity | PASS | PASS | PASS | PASS | PASS | **5/5** |

- **Full sketch (S1–S5): 0 of 5.**
- **Sound sketch (S1, S3, S4, S5): 5 of 5.**

## Which number is the honest one — and why it is not goalpost-moving

The 0/5 is **entirely S2**, and S2 is a confirmed false negative. A3 requires this check
explicitly: *"0/5 pass → too hard, or the grader is wrong — check for a false negative first."*

S2 demands that a *second* `CleanUp` return an error. Three independent pieces of evidence say that
demand is wrong, and the first of them predates every measurement:

1. **Pre-registered.** `card-04R…md` §"Residual risks, named", risk 1, written and saved before the
   first probe ran: *"The repeat-CleanUp assertion could false-negative an implementation that
   makes teardown idempotent and returns nil on the second call … the single most likely source of
   a wrong 0/5."*
2. **10 of 10 GATE-5 probes** independently argued for idempotent teardown; four said so in as many
   words (*"treat nil state as success"*, *"repeated CleanUp calls are idempotent"*).
3. It is what `io.Closer` semantics and the rest of this repo already do.

So the reportable figure is **5 of 5 on the sound assertions**, and A3's table gives that one
reading: *"5/5 pass your grader → too easy — no outcome variance. Do not build."*

## Verdict — GATE 4 A3-LOCAL: **KILL**

Five cold implementations, given nothing but the constraint sentence, each independently found a
four-site defect family spanning two packages — including the inverted `errors.Is`, the discarded
`Close()` return, the drained-channel hang, and the never-shut-down `http.Server` — wrote
~110 net lines apiece, kept the upstream suite green, and satisfied every sound assertion. There is
no outcome variance here to grade.

This kill is **not** a convergence reading. It is an executed measurement of outcome, on the gate
A3 calls PRIMARY, with the assertion validated at `base_commit` first — the exact instrument whose
absence qualified both of the prior run's GATE-5 kills.

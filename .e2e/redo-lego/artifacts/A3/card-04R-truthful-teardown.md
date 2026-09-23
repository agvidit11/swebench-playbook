# CARD 4R — "Teardown must tell the truth"

Re-cut of run-20260922T221320Z cascade 4 ("one port, many challenges"), which died on `GATE 5`
alone. The prior cut was built around the **code shape** (per-domain SNI map) and its probe prompt
handed that shape to the model verbatim. This cut is built around the **observable consequence of
the inverted `errors.Is`**: `CleanUp` reports a teardown it did not perform.

## DECLARATION BLOCK — fixed before any probe was run (probe-lint.py reads this)

CONSTRAINT: A nil result from a challenge server's CleanUp must mean the challenge server really is gone: nothing it accepted before teardown may still be usable afterwards, and its address must be free. If the challenge server could not be shut down, CleanUp must give back an error describing that failure instead of reporting success. CleanUp must always finish promptly; it must never block waiting for something that will never happen.

DESIRED: Teardown stops the thing that is actually serving, not merely the socket it accepts on, and whatever stopping it produced is handed back unchanged; a repeat teardown reports the same truth rather than being silently smoothed over, and never waits on a signal that has been consumed.

NON-DESIRED: Accountability is bolted on somewhere other than the teardown entry point itself, so the entry point keeps handing back success for a teardown that failed; or only the socket is unbound, more carefully, so connections previously accepted survive; or the hang is papered over with a deadline on the signal instead of by knowing whether anything is up; or the fix lands on one of the two challenge servers and not the other.

SHAPE: semantic_bugs

---

- repo `go-acme/lego` · base `58468399a23fbdf4cb3a366e6d81925c1f97b4fe`
- surfaces `challenge/tlsalpn01/tls_alpn_challenge_server.go`,
  `challenge/tlsalpn01/tls_alpn_challenge.go`,
  `challenge/http01/http_challenge_server.go`, `challenge/http01/http_challenge.go`
- shape `semantic_bugs` (real accidental upstream defect, not a feature)

---

## The defect, and why it is a family and not one line

`38f23c8c` *chore: update linter (#1278)* mechanically rewrote a negative comparison into a
positive `errors.Is`:

```
-	if err := s.listener.Close(); err != nil && err != http.ErrServerClosed {
+	if err := s.listener.Close(); err != nil && errors.Is(err, http.ErrServerClosed) {
```

`net.Listener.Close()` **cannot** return `http.ErrServerClosed` — that sentinel is produced by
`http.Server.Serve`, never by a listener. So the branch is dead and
`tlsalpn01.ProviderServer.CleanUp` returns `nil` unconditionally. Its error return is decoration.

The same "teardown reports success it did not achieve" property is violated three more ways on the
sibling surface, which is what lifts this above `GATE 6` anti-overcorrection:

| # | site | violation | subtlety |
|---|---|---|---|
| V1 | `tlsalpn01/..._server.go:121` | inverted predicate; every close failure discarded | **high** — reads as correct error handling |
| V2 | `http01/..._server.go:110` | `s.listener.Close()` return dropped on the floor | low |
| V3 | `http01/..._server.go:106-112` | second `CleanUp` blocks forever on the drained `s.done` | **high** |
| V4 | both | the `http.Server` is a local in `Present`/`serve` and is never shut down — only the socket is closed, so connections it already accepted survive teardown | **high** |

V4 is why a nil `CleanUp` does not mean "gone" even when nothing failed.

---

## CONSTRAINT

> A `nil` result from a challenge server's `CleanUp` must mean the challenge server really is gone:
> nothing it accepted before teardown may still be usable afterwards, and its address must be free.
> If the challenge server could not be shut down, `CleanUp` must give back an error describing that
> failure instead of reporting success. `CleanUp` must always finish promptly; it must never block
> waiting for something that will never happen.

Classification: **behavioural**, not a cost clause. It names no file, algorithm, data structure or
language construct.

## DESIRED

> Teardown stops the thing that is actually serving, not merely the socket it accepts on, and
> whatever stopping it produced is handed back unchanged. A second teardown reports the same truth
> rather than being silently smoothed over, and never waits on a signal that has already been
> consumed.

## NON-DESIRED

> Accountability is bolted on somewhere other than the teardown entry point itself — the caller
> captures and joins the teardown result, or it is merely logged more loudly — while the entry point
> keeps handing back success for a teardown that failed. Or: only the socket is closed (more
> carefully, with a nil-guard or a `sync.Once`), so connections already accepted survive. Or: the
> hang is papered over with a timeout/`select` on the signal instead of by knowing whether anything
> is up. Or: the fix lands on one of the two challenge servers and not the other.

---

## Step decomposition (P6)

**Step 1 — `challenge/tlsalpn01`.** Make TLS-ALPN-01 teardown mean what it says: own the serving
component so it can be stopped rather than merely unbound, hand back the real outcome, and finish
promptly on a repeat call.

**Step 2 — `challenge/http01` parity plus the solver.** The HTTP-01 challenge server must honour the
same contract, and `Solve` in both packages must stop reporting a solved challenge when the
challenge server it started could not be torn down — while a validation failure must remain the
error the caller sees.

**Artifact dependency (HEAD counterfactual).** At `base_commit` `CleanUp` can never produce a
non-nil result, so step 2's requirement is vacuous: there is nothing for `Solve` to propagate. Step
2's grader drives a real `ProviderServer` end to end, so it fails with step 1 absent **and** fails
with step 1 present but step 2 absent (`Solve` still only logs). Seam test [R03] holds in both
directions.

## GATE 0 — token inventory

Every asserted token exists at `base_commit`; **zero new exported symbols required**.

| token | grep count | verdict |
|---|---|---|
| `ProviderServer` | 29 | IN-BASE |
| `Present` | 899 | IN-BASE |
| `CleanUp` | 879 | IN-BASE |
| `Solve` | 34 | IN-BASE |
| `NewProviderServerWithOptions` | 6 | IN-BASE |
| `NewChallenge` | 12 | IN-BASE |
| `GetAddress` | 8 | IN-BASE |
| `Options` | many | IN-BASE |

Assertions are on *behaviour* (is the address bindable, is the connection dead, is the result
non-nil, did the call finish inside a deadline) — no error type, field or helper name is pinned.

## Residual risks, named

1. The repeat-`CleanUp` assertion could false-negative an implementation that makes teardown
   idempotent and returns nil on the second call. The CONSTRAINT is worded to forbid that
   ("could not be shut down … instead of reporting success"), but it is the single most likely
   source of a wrong 0/5. **This is what GATE 4 A3-LOCAL measures.**
2. The `http01` failed-re-`Present` path (`s.listener, err = lc.Listen(...)` nils the field on
   error, orphaning the bound socket) is a *data race* at base — it panics nondeterministically.
   **Excluded from the graded set** under `GATE 6` [R09]. Kept as motivating evidence only.
3. Fork strength on the *design* axis is expected to be low; this is a `semantic_bugs` candidate
   whose variance source is SEARCH, per `A3 GATE 4` (`semantic_bugs` 7 passed / 7 vs
   `expose_interface` 1 / 13).

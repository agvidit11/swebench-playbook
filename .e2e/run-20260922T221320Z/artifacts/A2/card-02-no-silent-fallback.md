Writing your multi-turn card — first inspecting the live source to pin line numbers.
Building your CASCADE-2 card from the live tree — now verifying the remaining call sites.
Search backend unavailable — switching to local inspection for the remaining details.
# CASCADE 2 — "No-Silent-Fallback Selection" (SWE-bench-Pro multi-turn card, go-acme/lego @ HEAD, module `github.com/go-acme/lego/v5`)

## Composition
- **Search axis:** chain-selection strictness × fetcher-exhaustion (how hard `preferredChain` binds, how many alternate URLs get tried before giving up).
- **Fork shape instantiated:** stacked augment `c1 + c3`, named **observe-then-exhaust**: (c1) make preferred-chain selection observable + full-bundle, stacked under (c3) exhaust-all-candidates fallback with typed terminal error. ch1 (renewal/policy plumbing) explicitly **DROPPED** to hold ≤150 net lines.

## Step 1 requirements — Observable, full-bundle selection (c1)
1. `hasPreferredChain` must match `preferredChain` against **every certificate in the issuer bundle**, not leaf/top only (check each parsed cert's `Issuer.CommonName`, and accept `Subject.CommonName` as synonym where the bundle's top self-signed root carries the name in Subject).
2. `checkResponse` must **not** Warn-and-default on miss: when `preferredChain != ""` and no alternate matches, it must return `(false, error)` whose message contains the requested `preferredChain` value, leaving `certRes.Certificate/IssuerCertificate/CertURL/CertStableURL` on the default chain so existing callers keep a usable cert but can now detect the miss via the existing `(bool, error)` return.
3. Match case must preserve current observable effect: on hit, `CertURL`/`CertStableURL` point at the matched alternate link and `Certificate`/`IssuerCertificate` hold the matched chain (existing `Test_checkResponse_alternate` stays green).
- **Compositional invariant S1:** no new record/ledger type; the outcome is visible only through **already-existing** `checkResponse` return values and `Resource` fields, so S2 can reuse the same seam without a migration.

## Step 2 requirements — Exhaust-all-candidates fallback (c3)
1. `GetOCSP` single-cert path must iterate **ALL** `IssuingCertificateURL` entries (fetch issuer) until one parses as X.509, instead of `[0]`-only; only after exhaustion return a terminal error whose text contains `no issuing certificate URL` or the last URL + `issuing certificate`.
2. OCSP POST path must iterate **ALL** `OCSPServer` entries until one returns a parseable `ocsp.Response`; transport failure / bad status / parse failure on candidate *i* must advance to *i+1*, not abort.
3. Honour caller preference with existing vocabulary only: candidates tried in slice order (the order the CA/caller put in the cert extensions); terminal error text must contain the `preferredChain`-style requested name where applicable and the last-tried URL, so "which candidate was tried" is readable from the error + `httptest` hit counts. No new struct.
- **Compositional invariant S2:** S1's miss-error is never swallowed by S2's loops — exhaustion errors wrap/chain and remain `errors.As`-compatible with plain `error` string matching (`Contains`), so S1 guard cases still fail if S1 regresses.

## THE TENSION
Availability (always hand back *some* certificate/OCSP bytes) conflicts with honouring an explicit caller preference (`preferredChain` / ordered URLs must mean something observable, not silent default).

## HEAD citation (what HEAD does TODAY)
- `certificate/certificates.go:558` — single-cert issuer fetch has no fallback:
> `// TODO: build fallback. If this fails, check the remaining array entries.`
— fails to cover: entries `[1:]` of `IssuingCertificateURL` when `[0]` is dead/slow/corrupt.
- `certificate/certificates.go:563` — fetches only first issuer URL:
> `req, errC := http.NewRequestWithContext(ctx, http.MethodGet, issuedCert.IssuingCertificateURL[0], nil)`
— fails to cover: any second/third mirror; one dead mirror kills `GetOCSP`.
- `certificate/certificates.go:597` — POSTs only first OCSP responder:
> `req, err := http.NewRequestWithContext(ctx, http.MethodPost, issuedCert.OCSPServer[0], bytes.NewReader(ocspReq))`
— fails to cover: `OCSPServer[1:]` when `[0]` returns 500/garbage/times out.
- `certificate/certificates.go:664` — leaf/top-only chain test:
> `if topCert.Issuer.CommonName == preferredChain {`
with context `topCert := certs[len(certs)-1]` (`:662`) — fails to cover: preferred name appearing on an intermediate elsewhere in the bundle, or on Subject of a self-signed root.
- `certificate/certificates.go:499` — Warn-and-default makes miss undetectable:
> `log.Warn("lego has been configured to prefer certificate chains with issuer, but no chain from the CA matched this issuer. Using the default certificate chain instead.",`
followed by `:503 return true, nil` — fails to cover: any caller that needs to distinguish "preferred chain served" from "default served" (returns success either way).

## Motivating caller
ACME fleet operator (e.g. lego-based cert-manager for a CDN edge with cross-signed ISRG `DST Root CA X3` → `ISRG Root X1` migration): must pin `ObtainRequest.PreferredChain` per-DC for old-Android compatibility, and must staple OCSP at scale where individual `IssuingCertificateURL`/`OCSPServer` hosts flap. Today a typo'd chain silently serves the wrong root (outage for pinned clients) and one dead OCSP mirror fails stapling for the whole fleet; operator needs a detectable miss + try-every-mirror before failing, offline-testable in CI.

## Existing-vocabulary test (mandatory)
Observable contract nouns: `preferredChain` — already in lego (`ObtainRequest.PreferredChain`, `Resource.PreferredChain`); `CertURL`/`CertStableURL`/`Certificate`/`IssuerCertificate` — already in lego (`Resource` fields); `IssuingCertificateURL`/`OCSPServer` — already in lego (`x509.Certificate` fields read at `:559,:563,:597`); `error`/`bool` return — already in lego (`checkResponse(...) (bool, error)`); `HTTPClient` — already in lego (`api.Core.HTTPClient`). Coined by me: **none** (zero new exported nouns).
**How step 1 avoids an invented ledger in one line:** step 1 reports match/miss through the existing `(bool, error)` return plus the existing `Resource.CertURL/CertStableURL` values and error text, never a new `Attempt/Result/Report` record.

## Interface Contract (graded tests touch)
| Symbol | Kind | Shape | Reachability (STATED or IN-BASE) | Alternatives (PINNED or accepted synonyms) |
|---|---|---|---|---|
| *(no new symbols — contract is pinned-empty)* | — | graded tests call only IN-BASE `(*Certifier).checkResponse`, `(*Certifier).GetOCSP`, unexported `hasPreferredChain` via same-package tests, `api.New`/`tester.MockACMEServer`, `httptest.Server` | IN-BASE | PINNED: any solution adding an exported symbol still passes iff existing-entry-point assertions hold; tests use `ErrorContains` (not `Equal`) for messages and `Contains` for URLs, so synonym spellings of the terminal errors are accepted if they contain the pinned substrings `preferredChain` value + `no issuing certificate URL`/`OCSP` + last URL |
- Legal configuration: **pinned spec (existing entry points only) + narrow tests** on those entry points. No vague-spec/narrow-test gap because there is no new name to guess.

## Observable Schema
No collection deliverable by design (avoids invented-ledger auto-reject) — all answers N/A with reason:
Container: N/A (single `Resource` mutated in place + `(bool, error)`; no slice/map/type-with-method added). Element: N/A (no struct/interface added). Exact field/method names: N/A (reuse `Resource.Certificate/IssuerCertificate/CertURL/CertStableURL`, `ObtainRequest.PreferredChain`). Value domain/spelling: error text MUST contain the requested chain string verbatim + (step 2) the last-tried URL verbatim; `CertURL` on miss stays the default `order.Certificate` link. Option names: N/A. Lifetime/persistence: N/A (no persisted state; per-call return only). Test-only lifecycle hook: none (design-smell fixed by using real `httptest.Server` + `core.HTTPClient` injection). Two-defensible-answers test: passes vacuously — a competent Go engineer cannot pick a different symbol because the prose names only symbols that already exist in lego.

## Named wrong-shape
**Wrong-shape W1: `type ChainSelectionReport struct { Matched bool; Attempts []Attempt; ... }` returned alongside `Resource`.** Plausible because: the cascade prose says "whether the requested chain was actually matched, and which candidate was tried," which reads like a ledger; the adjacent Go idiom is a result-struct with a slice of attempts; and lego already ships record types (`Resource`, `ObtainRequest`) so a capable model reaches for one more struct — this is exactly the newly-coined-schema auto-reject the card is engineered to forbid.

## Determinism seam (no sleeps, offline)
Injection point: `api.Core.HTTPClient` (`acme/api/api.go:32,71`) — tests set `core.HTTPClient` to a client whose `Transport` routes to `httptest.Server`s (first issuer/OCSP URL = failing server returning 500/garbage or closing, second = good server serving DER issuer bytes / valid OCSP response built with `golang.org/x/crypto/ocsp`). Chain-selection tests use the existing `tester.MockACMEServer` + `servermock.RawStringResponse` harness (as in `Test_checkResponse_alternate`) with `Link: rel="alternate"` chains. No clock, no sleep, no external network; ordering asserted via per-server hit counters.

## Predicted per-arm pass rate per step
- Step 1: avocado ≤3/5 (typically 2/5), opus ≥3/5 (typically 4/5), gpt ≥3/5 (typically 3–4/5).
- Step 2: avocado ≤3/5 (typically 1–2/5).
**WHAT STOPS AVOCADO PASSING STEP 1 OUTRIGHT:** avocado reliably widens the loop but keeps the Warn-and-default tail (`return true, nil` after `log.Warn`) or compares only `Subject.CommonName` / only the leaf, so the new miss-error assertion (`ErrorContains(preferredChain)` + `valid==false`) fails on 2+ of 5 arms while opus/gpt follow the "return error on miss" instruction — hence step 1 stays the *easier* step and ordering is measurement-correct (step 2's multi-URL transport/parse-exhaustion loop is strictly harder).

## Step-1 guard cases owned by step 2
- S1-invariant "miss returns error containing chain name" → guarded by S2 `TestCheckResponse_MissError_Preserved_AfterFallbackChange` (fail_to_pass in step 2; fails if Warn-and-default regresses).
- S1-invariant "full-bundle match (intermediate/Subject synonym)" → guarded by S2 `TestHasPreferredChain_FullBundle_IntermediateMatch` (fails if reverted to `certs[len-1]`-only).
- S1-invariant "hit still populates matched CertURL/CertStableURL" → guarded by S2 `TestCheckResponse_Hit_StillSelectsAlternate` (fails if S2 loop breaks alternate selection). NEVER put any step-1 fail_to_pass id into step-2 pass_to_pass; these are step-2 fail_to_pass guards.

## Inter-step file overlap
- Step 1 touches: `certificate/certificates.go` (hunks: `hasPreferredChain` + `checkResponse` miss path).
- Step 2 touches: `certificate/certificates.go` (hunks: `GetOCSP` issuer-fetch loop + OCSP POST loop + terminal errors). **INCREMENTAL on step 1** (step-2 base = step-1 output; step-1 hunks frozen, step-2 adds adjacent hunks in same file + graded `_test` file). ch1 dropped so no third file.

## Size estimate
Files: 2 (1 prod: `certificate/certificates.go`; 1 graded-test harness reusing `certificate/certificates_test.go` + `internal/tester/servermock`). Net prod lines: ~100–120 (S1 ~30: bundle loop + miss error; S2 ~70–90: two exhaustion loops + error accumulation). Primitives reused: `certcrypto.ParsePEMBundle`, `api.Core.HTTPClient.Do`, `http.NewRequestWithContext`, `ocsp.CreateRequest/ParseResponse`, `tester.MockACMEServer`, `httptest.Server`, `certcrypto/testdata/*.pem`-style bundles. Fits 80–150 net-line target; ch1 dropped rather than exceed 150.

## Rubric self-audit
| ID | Verdict | Evidence (one line) |
|---|---|---|
| R01 (task is measurable) | PASS | assertions pin `ErrorContains(chain)` + `CertURL` + httptest hit-counts; nearly failed by leaving "which candidate was tried" as prose — pinned it to error-text-substring + hit counters. |
| R02 (feasible ≤150 lines offline) | PASS | ~110 net lines reusing `MockACMEServer/httptest`; nearly failed by keeping ch1 renewal plumbing — dropped ch1 to fit budget. |
| R04 (no invented schema) | PASS | zero new exported nouns; existing-vocabulary table marks every noun already-in-lego. |
| R05 (deterministic/offline) | PASS | seam is `core.HTTPClient` + `httptest.Server`; no sleeps/network. |
| R06 (wrong-shape discriminates) | PASS | W1 ledger-struct names the shipped `Resource` primitive + result-slice idiom that leads there. |
| R07 (tension stated) | PASS | one-sentence availability-vs-preference conflict above. |
| R08 (step ordering correct) | PASS | S2 exhaustion strictly harder than S1 loop+widen; nearly failed by making S1's Subject-synonym subtlety the hard part — kept S1 mechanical so avocado-gap sits where predicted. |
| R09 (guards/overlap sane) | PASS | three S2 fail_to_pass guards named; incremental overlap declared; no S1 ids in S2 P2P. |
| R11 (HEAD-grounded) | PASS | five `certificates.go` line cites with verbatim quotes + uncovered-case each. |
| N01 (no network) | PASS | all grading via `MockACMEServer`/`httptest` + local PEM bundles. |
| N02 (real caller/scale) | PASS | CDN cross-sign pinning + OCSP-mirror flapping at fleet scale, not "nice API". |
| N03 (residual risk named) | **FAIL (residual risk)** | risk: Subject-vs-Issuer synonym on self-signed roots varies by CA bundle — tests accept either via `Contains`, but a real CA emitting the name in neither field still misses; accepted to stay within vocab/line budget. |
| N04 (alternatives pinned/tolerant) | PASS | contract table Alternatives column pinned-empty + `ErrorContains` tolerance stated. |
| Deferred | — | R03→decided at task-render (exact test ids); R10→decided at calibration (cut scores); R12→decided at review (duplicate check); R13→decided at merge (line-count audit). |

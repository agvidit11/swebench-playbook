Merging 18 surfaces into strict cascades — verifying the seams first.
Confirmed the repo layout — now sampling the candidate seams.
## MERGE TABLE
| id | verdict | reason |
| cc1 | -> 1 | Founds key-algorithm cascade: silent PEM default is the naive base for a shared key→artifact model |
| aa3 | -> 1 | Widens same key-type invariant to JWS alg selection; opaque empty-alg failure needs shared model |
| cc3 | -> 1 | Widens same invariant to temp-cert issuance (RSA-only defaults); third consumer of shared model |
| c1 | -> 2 | Founds fallback cascade: index-[0]-only fetch with live TODO is the naive base |
| c3 | -> 2 | Same silent-fallback shape (leaf-only match + Warn-then-default); joint observe-then-enforce with c1 |
| ch1 | -> 2 | Same shape cross-package (pinned sort + first-solver); widens selection-policy invariant |
| cc2 | DROPPED | Fix under ~20 lines (append ExtraExtensions); paired c4 step is "now use what you built" |
| aa1 | DROPPED | Pure expose_interface (tunable backoff); three-word recall (exponential backoff) |
| aa2 | DROPPED | Fix under ~20 lines (add switch cases); volume of mapping entries, no cascade tension |
| aa4 | DROPPED | Pure expose_interface (export maxBodySize/option); already-reached seam |
| c2 | PARKED-SINGLE-TURN | Crisp single: RFC 8555 reason constants + range check; no partner needing shared artifact |
| c4 | DROPPED | Step 2 computable from data already reached (domains/SAN/MustStaple flow through ObtainRequest); mechanical guard + field copy |
| ch2 | DROPPED | Pure expose_interface (register PersistentProvider); 1-passed/13-failed shape |
| ch3 | PARKED-SINGLE-TURN | Crisp single: per-challenge listener map + propagated close errors; concurrency fix needs no cascade |
| ch4 | DROPPED | Contract not observable behaviour (are unknown tags ignored or rejected?); spec cannot state it without coining tags |
| C1 | DROPPED | Step 1 = split/extract 450-case switch; difficulty is volume of mechanical edits + global registry state |
| C2 | DROPPED | Pure expose_interface (inject baseURL/timeout/transport); step 2 computable at its own seam |
| C3 | PARKED-SINGLE-TURN | Crisp single: typed-nil 2xx + nil/nil non-2xx fix with httptest fixtures; no cascade partner |

## AUTO-REJECTS
- cc2+c4 pairing: step 2 extends the same function step 1 wrote ("now use what you built") — reject.
- aa1: expose_interface (make backoff pluggable) + THREE-WORD RECALL TEST ("exponential backoff") — reject.
- aa2 alone: fix under ~20 lines, difficulty is volume of mapping entries — reject.
- aa4: expose_interface (export/override 1MiB limit); step 2 computable from data already reached at get() — reject.
- c4 alone: step 2 computable from data already reached (ObtainRequest already carries MustStaple/Email); empty-guard is mechanical — reject.
- ch2: expose_interface ("make DNSPersist01 pluggable"), 1-passed/13-failed shape — reject.
- ch4: contract not observable behaviour (unknown-tag equality has no agreed verb) — reject.
- C1: step 1 = split/extract/move a 450-case class; difficulty is volume of mechanical edits; natural impl is process-global mutable registry — reject.
- C2: expose_interface (inject URL/timeout/transport); EXISTING-VOCABULARY passes but no dilemma, just threading args — reject.
- cc2 alone: composing two already-shipped functions (append Extension + forward flag), fix under ~20 lines — reject.

## CASCADES
**1. Every-Key-Type (cc1 + aa3 + cc3)** — Step 1: introduce one tested key-kind→PEM/JWS mapping (RSA/ECDSA-P256-P384/Ed25519 + explicit unsupported-key error) and fix PEMBlock/PEMEncode to use it instead of silent nil. Step 2: enforce the mapping in JWS signer selection (correct RS256/ES256/ES384/EdDSA, typed error on unknown curve/key) and in temp/DER cert issuance (no RSA-only/KeyEncipherment-only defaults). THE TENSION: interop (accept every key ParsePEMPrivateKey accepts) conflicts with strictness (every unsupported key must fail loudly, never empty alg/nil block). Not P6 (step 1 survives intact; steps are narrow-then-widen + build-then-use). Step 2 CANNOT compute correct EdDSA-vs-reject without step 1's key-kind verdict, since signer sees only crypto.Signer and PEM round-trip is lossy. Biggest risk: Ed25519 JWS/TLS fixture variance across go-jose/x509 versions makes grading brittle.
**2. No-Silent-Fallback Selection (c1 + c3 + ch1)** — Step 1: expose selection outcome as data (OCSP candidate tried, chain top-issuer vs preferredChain match over full bundle not leaf-only, solver ordered-candidate list) instead of Warn-and-default. Step 2: enforce fallback policy with failure injection: iterate all IssuingCertificateURL/OCSPServer entries and all server-offered challenges/preferred chains, returning a typed not-found/unreachable error only after exhaustion. THE TENSION: availability (always return some cert/solver) conflicts with honoring explicit caller preference (preferredChain/order must mean something). Not P6 (step 1's report artifact survives; step 2 consumes it — observe-then-enforce). Step 2 CANNOT compute "preferred was missed vs. preferred was honored" without step 1's recorded match outcome, since default bundle/solver bytes look identical either way. Biggest risk: scope creep to 3 seams exceeds 150 lines unless solver ordering is pinned to fixtures.

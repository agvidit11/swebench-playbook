# STAGE 2 — Candidate cards: apache/santuario-xml-security-java @ 497d3fb4

Read-only on the clone: `git rev-parse HEAD` → `497d3fb4c8b5654a9951a3de4682c6ed48038173`,
`git status --short` clean before and after. Survey read in full
(`/tmp/santuario-pair/notes/survey.out`, 449 lines, 16 surfaces S1–S16).
A handful of citations re-verified at HEAD this round with read-only
`sed`/`find` (Manifest.java loop, VerifiedReference, KeyResolver.java path
`keys/keyresolver/`, XMLCipher TODOs, Transforms check, Reference MD5 guard,
X509Data stub, test-tree layout). No `instruction.md`, no solver prose —
the Interface Contract tables below are the deliverable in place of prose.

**Yield: 3 cards (C1, C2, C3).** 16 surfaces → 3 candidates; the rest are
mapped in the Merge Table as DROPPED or PARKED-SINGLE-TURN. Zero was on the
table; three merges survived every gate below with evidence, so three are
written. A fourth (budget cluster S6+S7+S8) was the largest merge considered
and is killed in the log with its rule named.

Threat-model routing (global, per THREAT_MODEL.md §5a/§13): none of the three
cards claims a §8 forgery/bypass with secure validation on. All three operate
strictly inside the on-posture, leave key *trust* (§3/§9) and XSW *coverage*
(§9/§10) to the caller, and touch only diagnostics/reporting/retry structure —
so none routes to VALID (that is expected: these are capability/hardening
tasks, not vuln reports) and none is a KNOWN-NON-FINDING.

---

## C1. Attributed per-reference verification ledger (classify at the Reference seam, consume at the Manifest seam)

1. **TITLE + surfaces + merge shape.** "Complete, attributed per-reference
   verification ledger" — merges **S1** (tri-state reporting) + **S2**
   (nested-Manifest short-circuit guard). Merge shape: **build-then-use**
   across two seams (NOT revert-and-redo: nothing built in step 1 is removed
   in step 2; step 2 *consumes* step 1's artifact through a different method
   in a different file).
2. **COMPOSITION: lens + divergence shape.** Lens-1 (boolean/`null` collapse:
   `Reference.verify()`'s `boolean` at `Reference.java:785-800` collapses
   "digest wrong" and "input unresolvable", the latter escaping instead as a
   thrown `ReferenceNotInitializedException` from
   `getContentsBeforeTransformation`/`calculateDigest`,
   `Reference.java:430-444` / `735-736`). Divergence shape:
   **same-loop / two-seam split** — step 1 classifies *inside* the
   per-reference evaluation (`Reference.java`), step 2 changes *aggregation*
   (`Manifest.java` loop). This re-cut exists specifically to satisfy the
   auto-reject on same-function step 2: the naive S1+S2 merge (step 1 rewrites
   the `Manifest.verifyReferences` loop, step 2 edits the same loop for the
   nested guard) is killed in the log; C1 cuts the other way.
3. **STEPS + invariants + tensions.**
   - **Step 1 — classify at the Reference seam.** Requirement: the
     per-reference evaluation must distinguish, through a pinned carrier,
     "reference resolved and digest mismatched" from "reference input could
     not be resolved at all", without changing the existing `boolean verify()`
     contract for current callers. Compositional invariant: *every path out of
     per-reference evaluation carries its reason* (boolean-false ⇒ resolved
     but bad; attributed-failure ⇒ unresolvable). THE TENSION: the existing
     `boolean verify()` signature must keep working for its current callers
     (no signature change that breaks `Manifest.java:339`'s call site)
     **versus** the new reason, which cannot travel through a boolean and
     therefore needs a second channel that every existing throw-site must
     adopt consistently.
   - **Step 2 — consume at the Manifest seam.** Requirement:
     `Manifest.verifyReferences` must (a) never abort the loop on an
     unresolvable reference (record the attributed entry, continue with the
     remaining references), (b) evaluate nested Manifests independently of
     earlier-reference outcomes (remove the `verify &&` gate at
     `Manifest.java:347` so a digest-bad ref #2 no longer suppresses the
     nested Manifest at ref #3), and (c) return `false` (not throw
     `MissingResourceFailureException`) when the only failures are
     per-reference. Compositional invariant: *the ledger is complete and
     position-aligned* — `getVerificationResults().size()` equals the number
     of `Reference` elements, and overall-false no longer depends on loop
     position. THE TENSION: completeness for the diagnostic consumer (WSS4J
     needs every entry to say what failed) **versus** the existing
     fail-fast/throw contract that current callers catch
     (`MissingResourceFailureException` from `Manifest.java:406-408`).
   - **Step 2 CANNOT compute without step 1's artifact** (one sentence):
     without step 1's attributed-failure channel at the Reference seam, step
     2's loop cannot tell "this throw means record-and-continue" from "this
     throw means abort" and collapses back to today's catch-and-rethrow.
   - No step 3.
4. **HEAD CITATION + NEAREST-PRESENCE quote.** `Manifest.java:347`
   (`if (verify && followManifests && currentRef.typeIsReferenceToManifest())`)
   and `Manifest.java:403-408` (`catch (ReferenceNotInitializedException ex)
   … throw new MissingResourceFailureException(…)`). NEAREST-PRESENCE
   verbatim: `public List<VerifiedReference> getVerificationResults()` with
   `VerifiedReference(boolean valid, String uri, List<VerifiedReference>
   manifestReferences)` (`VerifiedReference.java:39-47`) — "the closest
   existing thing to the absence claimed. It fails to cover the unresolvable
   case: `VerifiedReference` has only `valid` (boolean), no
   UNKNOWN/UNRESOLVABLE state, and the throw path means no entry is ever
   recorded for references after (or including) the unresolvable one."
5. **MOTIVATING CALLER.** **WSS4J** (WS-Security on CXF): on inbound SOAP with
   4+ signed parts where one `Reference` points at a detached attachment that
   failed to arrive, today's `checkSignatureValue` throws
   `MissingResourceFailureException` and WSS4J logs a single opaque abort —
   operators cannot tell "attachment missing in transit" (retry the fetch)
   from "digest mismatch" (reject the message). A complete attributed ledger
   is what the WSS4J `SAMLTokenValidator`/signature-validation error path
   needs to classify the fault without re-running verification. Scale:
   gateways validating thousands of multi-reference messages/s cannot afford
   verify-then-re-verify-to-diagnose. Compatibility: existing boolean/throw
   callers keep compiling and behaving (step 1 preserves `verify()`; step 2
   changes only the unresolvable path from throw to false-plus-ledger — the
   overall verdict stays non-true).
6. **INTERFACE CONTRACT TABLE.** Graded tests touch existing names plus the
   minimal coined carrier:
   | Symbol | Kind | Shape | Reachability | Alternatives |
   |---|---|---|---|---|
   | `Manifest.verifyReferences` | method | existing signature, new no-abort/no-suppress behaviour | IN-BASE | PINNED (behaviour pinned, not renamed) |
   | `Manifest.getVerificationResults` | method | existing, completeness pinned (`size == #refs`) | IN-BASE | PINNED |
   | `VerifiedReference.isValid` | method | existing | IN-BASE | PINNED |
   | `VerifiedReference.getUri` | method | existing | IN-BASE | PINNED |
   | `VerifiedReference.getManifestReferences` | method | existing, non-empty-when-followed pinned | IN-BASE | PINNED |
   | `Reference.verify` | method | existing boolean contract preserved | IN-BASE | PINNED |
   | `MissingResourceFailureException` | type | existing; step-2 tests assert it is NOT thrown for per-reference unresolvable | IN-BASE | PINNED |
   | `XMLSecurityException.getMsgID` | method | existing (`signature.tooManyReferences` untouched) | IN-BASE | PINNED |
   | *unresolvable-status carrier* (e.g. a status accessor on the reference
     result or a pinned `ReferenceNotInitializedException` subtype/wrapping
     rule) | method-or-type | **the one coined token**: carries
     resolved-but-bad vs unresolvable per reference | STATED (contract names
     the exact accessor/type and its values) | PINNED (exact name + values
     pinned; no synonyms — a synonym would be a second coined token) |
   **COINED-TOKEN COUNT: 1** (the step-1 attribution carrier; everything else
   is existing vocabulary: `Manifest`, `verifyReferences`,
   `getVerificationResults`, `VerifiedReference.isValid`, `getUri`,
   `getManifestReferences`, `XMLSecurityException`, `getMsgID`,
   `signature.tooManyReferences`, `org.apache.xml.security.maxReferences`
   untouched). Step 1 alone coins it; step 2 coins nothing further.
7. **NAMED WRONG SHAPE + why plausible.** *Two-phase pre-resolution*: the
   solver adds a pre-pass that resolves every reference's input before the
   verify loop, then verifies — satisfying completeness while doubling
   dereference work and changing which `ResourceResolver` side effects happen
   before any digest is checked. Plausible because `getContentsBefore
   Transformation` (`Reference.java:430-444`) already exists as a separable
   public step, the existing code reads resolve-then-verify in that order, and
   a solver that thinks "classify first, loop second" reaches for it
   naturally; it also preserves the `verify &&` guard byte-for-byte, so a
   solver minimising diff prefers it. It is wrong (fails the nested-guard
   graded case and any resolver-side-effect ordering case) yet contract-legal
   — a real discriminator, not a strawman.
8. **DETERMINISM SEAM.** Hand-built DOM: 4-reference `SignedInfo` (ref #2
   digest-bad, ref #3 Manifest-typed with a resolvable nested manifest, ref #4
   bogus same-document fragment URI for the unresolvable path) +
   `ResourceResolver` registration to force unresolvable deterministically.
   No clock, no threads, no network, no randomness.
9. **PREDICTED PER-ARM RATE.** Step 1: 2/5 (finding *every* unresolvable
   throw-site inside Reference evaluation and routing them through one carrier
   without breaking the boolean call site is SEARCH-heavy). Step 2: 2/5
   (removing two intertwined behaviours — abort-throw AND `verify &&` gate —
   while keeping overall-verdict and message-key behaviour requires touching
   the loop without breaking the cap checks at `Manifest.java:321-325`).
10. **INTER-STEP FILE OVERLAP.** Step 1: `Reference.java` (+ coined carrier
    lives here or beside it). Step 2: `Manifest.java` (+ `VerifiedReference.java`
    only if the carrier needs a field there — preferably not). Overlap:
    **barely-overlapping by construction** (different files, step 1 writes the
    producer seam, step 2 the consumer seam). Step 2 is CUMULATIVE from base +
    step 1's carrier (it imports the carrier; it does not re-edit
    `Reference.java`). No delta-patch fragility.
11. **SIZE.** 3 files (`Reference.java`, `Manifest.java`,
    `VerifiedReference.java` untouched-or-trivial), ~90–130 net lines. In band.
12. **TEST COST.** Lives near
    `test/dom/signature/SignatureReferenceTest.java` (existing per-reference
    DOM tests) and `XmlSecTest.java`; graded set = hand-built DOM docs, no
    network, no StAX harness. Cheap: one class runs in well under a second of
    test time inside the ~14 s `mvn -Dtest=X` invocation.
13. **SELF-AUDIT.**
    | Item | Verdict | Evidence (one line) |
    |---|---|---|
    | R01 interface stated | PASS | Nearly failed: the carrier could have been left as "some status" —
      instead the table pins exactly one coined accessor/type with PINNED
      alternatives (no synonyms). |
    | R02 symbols reachable | PASS | Nearly failed: step-1 carrier is STATED not IN-BASE — rescued only
      because the contract names it exactly and step 2 coins nothing. |
    | R04 no mechanism naming | PASS | Steps say "classify/consume/record", never catch-table/exception-type
      implementation; the wrong-shape section holds the mechanism talk. |
    | R05 not gradeable vs library export | N-A | No third-party export involved; grading is against repo's own behaviour. |
    | R06 adversarial "only/never/must-not" | PASS | "never abort" graded by doc with unresolvable ref FIRST followed by
      verifiable refs (entries for later refs must exist); "must not suppress"
      graded by digest-bad ref before Manifest-typed ref (nested list
      non-empty). |
    | R07 realism | PASS | WSS4J inbound-fault classification is a real operational need, not a
      "nice API" (named caller + retry-vs-reject decision). |
    | R08 spec-precision vs test-narrowness | **FAIL (residual)** | The ledger's *ordering* guarantee
      (position-aligned vs append-in-resolution-order) is load-bearing for the
      graded size assertion but only implied by "complete"; a solver emitting
      in resolution order passes size yet breaks positional reading. Named
      residual risk: contract should pin index alignment explicitly. |
    | R09 determinism | PASS | Bogus-fragment-URI + registered-resolver injection; no clock/threads/net. |
    | R11 scope | PASS | 90–130 lines / 3 files, in band; StAX parity explicitly excluded. |
    | N01-N04 novelty/anti-overcorrection | PASS | LOCAL-POLICY (xmldsig-core §5.2 silent on reporting); no REC behaviour
      pinned; key-trust/coverage left to caller per §9. |
    **Residual risk carried:** R08 ordering under-specification (above).

    **Fork-strength answers (C1).** Two implementation families: (a)
    in-loop catch-and-record through the coined carrier; (b) two-phase
    pre-resolution pass then verify (the named wrong shape — still satisfies
    the ledger-completeness sentence while differing observably on
    resolver-side-effect order and nested-guard behaviour). CONTRACT sentence:
    "every Reference element yields one attributed ledger entry and the
    operation returns false rather than throwing for per-reference
    unresolvable." OBSERVABLE-CONSEQUENCE sentence: "a WSS4J-style caller can
    distinguish retry-the-fetch from reject-the-message without re-running
    verification." Different sentences (the second is about the caller's
    downstream decision, not the ledger shape) — fork nonzero. Step-2
    constraint is **BEHAVIOURAL** ("must not stop at the first unresolvable;
    must not suppress nested evaluation after a failure") — not a cost clause.
    Variance source is **SEARCH** (every unresolvable throw-site + the guard +
    cap checks must all be found). What stops a strong model passing step 1
    outright: the carrier must be adopted at *all* unresolvable sites
    (`430-444`, `735-736`, nested-manifest construction at `362-365`) while
    the boolean `verify()` call site keeps working — a partial adoption passes
    the solver's own happy-path test but fails graded adversarial docs.
    CASCADE: head-counterfactual — delete step 1, step 2's grader (attributed
    entries, no throw) cannot pass on `null`-only Reference seam. Parallel-API
    — step 2 pins changed behaviour of the *existing* `verifyReferences`
    (no-throw + completeness), not a new method; a second API alongside
    leaves the existing throw in place and fails. Both hold.

---

## C2. Decrypt-failure classification with bounded EncryptedKey retry over preserved references

1. **TITLE + surfaces + merge shape.** "Classified decrypt errors + lossless
   retry inputs" — merges **S11** (decrypt error classification) + **S14**
   (encryption xs:any / `referenceInformation` round-trip loss). Merge shape:
   **observe-then-enforce**: step 1 captures what the model drops (extension
   content through parse→model→serialize), step 2 enforces a policy whose
   inputs *are* what step 1 captured.
2. **COMPOSITION: lens + divergence shape.** Lens-2 (terminal-vs-recoverable
   classification at the decrypt boundary) fed by a control admission (the
   three `XMLCipher.java` TODOs). Divergence shape: **capture-then-constrain
   in one subsystem, different functions** — step 1 writes the model/marshal
   functions (`newEncryptionProperty`/`newEncryptionMethod`/
   `ReferenceImpl.toElement` region), step 2 writes the decrypt-execution
   functions (`decryptData`/`doFinal` family + `EncryptedKey` retry loop).
   Same file (`XMLCipher.java`), deliberately different functions — flagged
   yellow under field 10, step 2 ships as a delta patch.
3. **STEPS + invariants + tensions.**
   - **Step 1 — lossless extension capture.** Requirement: schema-legal
     extension content (`##other` children on `EncryptionMethod` at
     `XMLCipher.java:2517-2518`, `anyAttribute`+`##other` on
     `EncryptionProperty` at `2556-2560`, `referenceInformation` through
     `ReferenceImpl.toElement` at `3645-3647`) must survive
     parse→model→serialize round-trip and be readable through a pinned
     accessor. Compositional invariant: *round-trip fidelity* —
     `toElement(parse(doc))` preserves extension bytes. THE TENSION: the
     inner-class model objects are typed/closed (known-field getters) **versus**
     the schema, which is open (`##other`/`anyAttribute` explicitly allowed) —
     the accessor must expose untyped content without promoting it into the
     typed contract.
   - **Step 2 — classified failure + bounded retry.** Requirement: decrypt
     failures are classified (terminal: corrupt `CipherData`/unsupported
     algorithm — stop; recoverable: wrong key for this `EncryptedKey` — try
     the next `EncryptedKey`/`DataReference` preserved by step 1), and retry
     is bounded by the number of key references actually present (no new
     unbounded loop over attacker-listed keys — the amplification guard).
     Compositional invariant: *the retry set is exactly the preserved set* —
     step 2 attempts precisely the references step 1 retained, in document
     order, stopping at the first terminal failure. THE TENSION: robustness
     for the multi-recipient caller (try next key) **versus** the CPU-amplifi
     cation risk of attacker-controlled retry lists (each attempt is expensive
     crypto), resolved by binding the bound to present-and-preserved inputs.
   - **Step 2 CANNOT compute without step 1's artifact** (one sentence):
     without step 1's preserved `referenceInformation`/extension references,
     step 2's retry loop has no faithful key-reference set to iterate — it
     would retry over the same lossy inputs today's code drops, so the graded
     second-key-succeeds case cannot pass.
   - No step 3.
4. **HEAD CITATION + NEAREST-PRESENCE quote.** `XMLCipher.java:3645-3647`
   (`// TODO: Need to martial referenceInformation … <any namespace="##other"
   …/>`), `2517-2518`, `2556-2560` (same-TODO family). NEAREST-PRESENCE
   verbatim: "`KeyReference`/`DataReference.toElement()`
   (`XMLCipher.java:3635-3650`) fails to round-trip `referenceInformation`
   (TODO at 3645), so even the retry inputs are lossy" — and the
   `XMLEncryptionException` throws across `XMLCipher` are "closest to
   classification; fail to cover retryability (caller cannot tell 'wrong key,
   try next `EncryptedKey`' from 'corrupt `CipherData`, stop')."
5. **MOTIVATING CALLER.** **Apache CXF / WSS4J multi-recipient decryption**:
   a WS-Security gateway holding two recipient certs receives a message with
   two `EncryptedKey` elements; today a wrong-first-key surfaces as an
   undifferentiated `XMLEncryptionException` and the gateway 500s instead of
   trying the second key — while a corrupt-`CipherData` message *should*
   500 fast rather than burn CPU across every listed key. Compatibility:
   single-key callers see identical behaviour (retry set of size 1 = today's
   path); only the exception taxonomy gains structure, no signature changes
   on `decryptData`.
6. **INTERFACE CONTRACT TABLE.**
   | Symbol | Kind | Shape | Reachability | Alternatives |
   |---|---|---|---|---|
   | `XMLCipher.decryptData` / `doFinal` family | methods | existing signatures; classified-failure + retry behaviour pinned | IN-BASE | PINNED |
   | `EncryptedData`, `EncryptedKey`, `CipherData`, `KeyInfo`,
     `XMLEncryptionException` | types | existing | IN-BASE | PINNED |
   | `ReferenceList`, `DataReference`, `KeyReference` | types | existing; fidelity pinned via round-trip | IN-BASE | PINNED |
   | *preserved-extension accessor* (one method returning the retained
     `##other`/attribute content as inert DOM) | method | **coined token 1** |
     STATED | PINNED (exact name/shape pinned; accepted synonym: NONE — widening
     here would coin a second token) |
   | *recoverable-vs-terminal signal* on the decrypt failure (pinned as
     either a `getMsgID` value set or a single boolean query — contract picks
     exactly one) | method-or-value | **coined token 2** | STATED | PINNED
     (the contract pins ONE of the two shapes; the other is then forbidden,
     keeping the count at 2) |
   **COINED-TOKEN COUNT: 2** (one capture accessor, one classification
   signal). The retry bound itself coins nothing (bound = count of preserved
   references, computed from step-1 data). No invented ledger/census/record
   type — the observable effect flows through the existing `decryptData`
   entry point.
7. **NAMED WRONG SHAPE + why plausible.** *Retry-everything*: the solver
   classifies nothing and instead wraps `decryptData` in a loop that tries
   every `EncryptedKey` for *every* failure kind (including corrupt
   `CipherData` and unsupported algorithms), satisfying "second key succeeds"
   while violating the terminal-stop cases. Plausible because the existing
   code already iterates key references without classifying (`toElement`
   region shows iteration-shaped code), "just try the next one" is the
   natural robustness reflex, and the amplification danger is invisible in
   unit tests with two keys. It is contract-legal (same entry point, same
   success case) yet fails graded must-not-retry cases — a genuine
   discriminator. (If this sentence could not be written it would be a
   strawman; it can, so it stays.)
8. **DETERMINISM SEAM.** Hand-built `EncryptedData` DOMs with test keys:
   two-`EncryptedKey` doc (first key wrong, second right), corrupt-
   `CipherData` doc, unsupported-algorithm doc. `RetrievalMethod` resolvers
   excluded. No clock/threads/network/randomness.
9. **PREDICTED PER-ARM RATE.** Step 1: 3/5 (inner-class surgery in a
   3709-line file; the three TODO sites must all be found — SEARCH, but the
   survey hands the line numbers to the task author, not the solver; the
   solver must still find them). Step 2: 2/5 (every `XMLEncryptionException`
   throw-site on the decrypt path must be triaged terminal-vs-recoverable;
   over-broad "recoverable" passes the retry case and fails the
   must-not-retry cases).
10. **INTER-STEP FILE OVERLAP.** Step 1: `XMLCipher.java` inner-model region
    (`newEncryptionMethod` ~2517, `newEncryptionProperty` ~2556,
    `ReferenceImpl.toElement` ~3635-3650). Step 2: `XMLCipher.java`
    decrypt-execution region (`decryptData`/`doFinal` family). **Heavy overlap
    (same file) — yellow flag acknowledged**: step 2 ships as a DELTA patch on
    step 1's tree (CUMULATIVE), and the graded step-2 cases re-run step-1
    fidelity cases as pass-to-pass. Tiebreak vs C1/C3 noted in ranking.
11. **SIZE.** 1 file (+ tests), ~100–150 net lines. Top of band, honest.
12. **TEST COST.** Lives near `test/dom/encryption/` (`EncryptContentTest.java`,
    `BaltimoreEncTest.java` family); graded set = small DOM round-trips +
    decrypt attempts with test keys. Cheap, same ~14 s invocation profile.
13. **SELF-AUDIT.**
    | Item | Verdict | Evidence |
    |---|---|---|
    | R01 interface stated | PASS | Nearly failed: the classification signal could have been "some
      taxonomy" — instead the contract forces exactly one of two shapes and
      forbids the other. |
    | R02 symbols reachable | **FAIL (accepted)** | The two coined tokens are STATED-only;
      graded tests cannot reach them without the contract text — this is the
      legal three-way branch (absent+pinned+named) but it pays the
      transcription cost the brief warns about. Evidence: count is 2, not 0,
      and Alternatives is PINNED-shut to stop synonym drift. |
    | R04 no mechanism naming | PASS | "classified failure / bounded retry" with no named technique; the
      retry loop shape lives only in the wrong-shape section. |
    | R05 not gradeable vs library export | N-A | Own-behaviour grading. |
    | R06 adversarial "only/never/must-not" | PASS | "must not retry corrupt CipherData /
      unsupported algorithm" each gets an adversarial graded case asserting
      fast terminal failure AND attempt-count == 1. |
    | R07 realism | PASS | CXF/WSS4J multi-recipient gateway is named with the concrete
      500-vs-retry decision; not an abstract nice API. |
    | R08 spec-precision vs test-narrowness | PASS | Nearly failed: xmlenc-core leaves
      error handling to implementations, tempting a broad taxonomy — the card
      narrows to exactly two classes + count-bound, matched to the graded set. |
    | R09 determinism | PASS | Test keys + excluded remote resolvers; attempt-count asserted, never
      wall-clock. |
    | R11 scope | PASS | 100–150 lines, 1 file; bound reuses preserved-set count (no new knob). |
    | N01-N04 novelty/anti-overcorrection | **RESIDUAL RISK (not PASS)** | §9 fence:
      classification must stop at retryability and claim NO padding-oracle /
      ordering hardening (threat-model Q8 caller layer); a solver that
      "hardens" decrypt ordering overreaches the model. Named and fenced. |
    **Residual risks carried:** R02 transcription cost (2 coined tokens);
    N-item oracle-proximity fence.

    **Fork-strength answers (C2).** Two families: (a) reason-code/boolean on
    the existing `XMLEncryptionException`; (b) distinct exception subtypes per
    class. CONTRACT: "decrypt exposes whether a failure is retryable and, when
    it is, attempts exactly the preserved key references in order."
    OBSERVABLE-CONSEQUENCE: "a two-recipient gateway delivers the message on
    second-key success and 500s fast on corrupt ciphertext without burning CPU
    across the key list." Different sentences (retry discipline + cost bound
    vs delivery outcome). Step-2 constraint is **BEHAVIOURAL** ("must attempt
    the next preserved key after a recoverable failure; must stop after a
    terminal one") — no cost clause names a technique. Variance is **SEARCH**
    (every decrypt-path throw-site triaged). What stops 5/5 on step 1: three
    TODO sites in disjoint regions of a 3709-line file must ALL be made
    faithful — two-of-three passes the solver's own round-trip but fails the
    graded third. CASCADE: head-counterfactual — delete step 1, the graded
    second-key case fails (references lossy, nothing faithful to retry).
    Parallel-API — step 2 pins retry/stop behaviour of existing `decryptData`,
    not a new method; an additive API leaves existing-callers' behaviour
    unchanged and fails.

---

## C3. Key-resolver decline-vs-failure attribution with fail-fast consumption

1. **TITLE + surfaces + merge shape.** "Resolver-chain failure attribution"
   — merges **S4** (KeyResolver decline-vs-fail) with its own consumption
   policy (S5's give-up theme deliberately NOT merged — see kill log).
   Merge shape: **observe-then-enforce within one subsystem**: step 1 builds
   the decline/fail reporting channel (observe), step 2 consumes it with a
   fail-fast chain policy (enforce). Single-surface-deepened card.
2. **COMPOSITION: lens + divergence shape.** Lens-1 (chain accumulates
   `null`s; `null` means "not mine" and "mine but bad" identically across
   100+ `return null` sites; terminal generic
   `KeyResolverException("utils.resolver.noClass")` at `KeyResolver.java:101-106`
   / `123-139`). Divergence shape: **channel-then-policy split across two
   types** — step 1 writes the SPI return channel (`KeyResolverSpi` and
   implementations), step 2 writes the chain loop (`KeyResolver`
   `getX509Certificate`/`getPublicKey`).
3. **STEPS + invariants + tensions.**
   - **Step 1 — attributed reporting channel.** Requirement: each
     `KeyResolverSpi` outcome must be observable as declined (not applicable)
     vs failed (applicable, material rejected), plus an ordered per-resolver
     ledger for the terminal failure, without changing the existing
     first-non-null success path. Compositional invariant: *no silent
     conflation* — every resolver that ran contributes exactly one attributed
     outcome. THE TENSION: dozens of `return null` sites must be triaged
     individually (decline vs fail is a per-site judgment) **versus** the
     existing SPI signature, which funnels both through `null` and cannot
     carry the distinction without a second channel.
   - **Step 2 — fail-fast consumption + attributed terminal.** Requirement:
     the chain loop stops consulting further resolvers after an attributed
     *failure* (declines continue the scan), and the terminal exception
     carries the ordered ledger; under secure validation this additionally
     avoids handing attacker `KeyInfo` bytes to every remaining resolver
     (notably dereferencing ones). Compositional invariant: *resolvers after
     an attributed failure never run* (graded via the ledger, not via mocks).
     THE TENSION: robustness-through-exhaustion (today's try-everything,
     which maximises interop across resolver implementations) **versus**
     fail-fast containment (stop feeding attacker material down the chain
     once a competent resolver has rejected it).
   - **Step 2 CANNOT compute without step 1's artifact** (one sentence):
     the loop today observes only `null`, so a fail-fast-on-failure rule is
     inexpressible until step 1's channel tells failure apart from decline.
   - No step 3.
4. **HEAD CITATION + NEAREST-PRESENCE quote.** `KeyResolver.java:83-106`
   (loop + terminal throw; verified this round: `LOG "check resolvability by
   class…"; cert = resolver.engineLookupResolveX509Certificate(…); if (cert
   != null) return cert;` then `throw new KeyResolverException(
   "utils.resolver.noClass", exArgs)`). NEAREST-PRESENCE verbatim: the
   terminal `throw new KeyResolverException("utils.resolver.noClass", exArgs)`
   (`KeyResolver.java:106`) — "the closest thing to a terminal report; fails
   to cover *which* resolvers ran and *why each* declined/failed", with
   `KeyResolverSpi.engineLookupAndResolvePublicKey` default `return null`
   (`KeyResolverSpi.java:90`) baking the collapse in.
5. **MOTIVATING CALLER.** **WSS4J/CXF operations**: inbound messages with
   attacker-controlled `KeyInfo` currently produce "noClass" with zero
   attribution — gateway operators cannot tell "register another resolver /
   caller-config problem" (all declined) from "the claiming resolver rejected
   the key material" (attacker-material problem), and today's
   try-everything loop hands the same hostile bytes to remote-dereferencing
   resolvers after a local one already said bad. **Java SAML stacks**
   (Shibboleth/OpenSAML-adjacent deployments on Santuario) hit the same wall
   triaging federation-key failures. Compatibility: success path byte-identical
   (first-non-null still wins); only total-failure behaviour gains structure.
   Threat-model fence: diagnostics ONLY — must not become key *trust*
   (§3/§9); no unknown-element-as-key promotion (the S12 trap, killed below).
6. **INTERFACE CONTRACT TABLE.**
   | Symbol | Kind | Shape | Reachability | Alternatives |
   |---|---|---|---|---|
   | `KeyResolver.getX509Certificate` / `getPublicKey` | methods | existing
     signatures; fail-fast + attributed-terminal behaviour pinned | IN-BASE | PINNED |
   | `KeyResolverSpi` + existing impls (`X509CertificateResolver`,
     `RSAKeyValueResolver`, `RetrievalMethodResolver`) | types | existing;
     outcomes attributed | IN-BASE | PINNED |
   | `KeyResolverException` (+ `utils.resolver.noClass` key) | type/key |
     existing; terminal now carries ledger | IN-BASE | PINNED |
   | *decline-vs-failure channel* (one status value / carrier through which an
     SPI reports failed-not-declined) | value-or-type | **coined token 1** |
     STATED | PINNED (exact shape pinned; the alternative channel shape is
     forbidden, not accepted) |
   | *ordered per-resolver ledger accessor on the terminal failure* | method |
     **coined token 2** | STATED | PINNED |
   **COINED-TOKEN COUNT: 2** (channel + ledger accessor). No status *object*
   with field-names-as-task — the ledger reuses resolver class names +
   channel values only.
7. **NAMED WRONG SHAPE + why plausible.** *Log-only attribution*: the solver
   adds per-resolver decline/fail `LOG.debug` lines (the file already logs
   "check resolvability by class") and changes nothing observable — satisfying
   a careless reading ("report which resolvers ran") while the terminal stays
   generic and the chain still tries everything. Plausible because the seam
   already logs there, logging is the lowest-diff "observability" reflex, and
   graded tests that only assert success-path behaviour would still pass. It
   fails the ledger-carrying terminal and the never-ran-after-failure cases —
   a real discriminator. (Strawman test passed: the shipped `LOG` idiom is the
   lure, stated explicitly.)
8. **DETERMINISM SEAM.** Registered test resolvers (decline-stub,
   fail-stub, success-stub in fixed order) + hand-built `KeyInfo` DOMs;
   remote resolvers (`RetrievalMethodResolver` network paths) unregistered in
   tests. No clock/threads/network/randomness.
9. **PREDICTED PER-ARM RATE.** Step 1: 2/5 (per-site null triage across
   implementations; misclassifying one fail as decline breaks fail-fast
   grading). Step 2: 3/5 (loop rewrite is small — risk it drifts EASY; what
   saves it is the secure-validation no-further-dereference case, which
   requires understanding which resolvers touch remote input).
10. **INTER-STEP FILE OVERLAP.** Step 1: `KeyResolverSpi.java` + one-to-three
    impl files (`keys/keyresolver/implementations/`). Step 2:
    `KeyResolver.java` loop (`getX509Certificate`/`getPublicKey`). Same
    subsystem, **adjacent files, different functions** — legal under the
    same-function rule (step 2 does not extend any function step 1 wrote) but
    flagged: step 2 is a DELTA patch on step 1's tree (CUMULATIVE), and
    step-1 ledger cases re-run as pass-to-pass inside step 2.
11. **SIZE.** 3–4 files (`KeyResolver.java`, `KeyResolverSpi.java`, 1–2
    impls), ~80–130 net lines. In band.
12. **TEST COST.** Near `test/dom/signature/KeyValueTest.java` /
    `X509DataTest.java` (KeyInfo-path DOM tests) with stub resolvers; no
    network. Cheap.
13. **SELF-AUDIT.**
    | Item | Verdict | Evidence |
    |---|---|---|
    | R01 interface stated | PASS | Nearly failed: "ledger" left open would be
      transcription-bait — instead the table pins ledger = ordered
      (resolver, channel-value) pairs only, no new record type. |
    | R02 symbols reachable | PASS | Same tension as C2 (STATED-only tokens) but
      count held at 2 with PINNED-shut alternatives; IN-BASE success path
      carries most grading. |
    | R04 no mechanism naming | PASS | "channel / fail-fast" with no prescribed
      mechanism; log-only and sentinel-exception both left open as shapes. |
    | R05 not gradeable vs library export | N-A | Own behaviour. |
    | R06 adversarial "only/never/must-not" | **FAIL (residual)** | "resolvers after
      an attributed failure NEVER run" is graded via ledger absence — but a
      resolver with no observable ledger footprint could run silently and pass.
      Named residual: tests must use footprint-leaving stubs, which the card
      states but cannot enforce on solver implementations. |
    | R07 realism | PASS | WSS4J/SAML key-failure triage named with the
      register-vs-reject operator decision. |
    | R08 spec-precision vs test-narrowness | PASS | xmldsig-core §4.4/§6 leave chain
      design to the library; graded set pins exactly decline-continue /
      fail-stop / ledger-carry, nothing broader. |
    | R09 determinism | PASS | Stub-resolver ordering; network resolvers excluded. |
    | R11 scope | PASS | 80–130 lines; global `resolverList` ordering untouched (no new
      process-global mutable state — read-only traversal only). |
    | N01-N04 novelty/anti-overcorrection | PASS | Fenced off §9 trust (diagnostics
      only; unknown elements never promoted to keys — the killed S12-merge
      trap, named). |
    **Residual risk carried:** R06 silent-runner gap (above) + weakest cascade
    of the three (step 2's redaction/no-dereference value depends on resolver
    inventory the task may have to stipulate).

    **Fork-strength answers (C3).** Two families: (a) sentinel/distinct
    return channel consumed by the loop; (b) exception-carried failure with
    decline staying `null`. CONTRACT: "the chain distinguishes decline from
    failure and stops after failure with an attributed terminal."
    OBSERVABLE-CONSEQUENCE: "an operator holding only the terminal exception
    knows whether to register another resolver or reject the key material —
    without re-running resolution." Different sentences (chain discipline vs
    operator decision). Step-2 constraint is **BEHAVIOURAL** ("must not consult
    resolvers after an attributed failure"). Variance is **SEARCH** (which of
    the 100+ `null`s are fails). What stops 5/5 on step 1: per-site triage —
    any single misclassified site flips a graded doc's outcome. CASCADE:
    head-counterfactual holds (no channel → fail-fast inexpressible);
    parallel-API holds (pins existing `getPublicKey`/`getX509Certificate`
    behaviour, not a new method). Honest flag: this cascade is the weakest of
    the three — step 2's policy is small enough that its difficulty leans on
    step 1's triage being exactly right.

---

## MERGE TABLE (all 16 surfaces)

| Surface | Disposition | Reason / card |
|---|---|---|
| S1 per-reference tri-state | MERGED → C1 (step-2 ledger half; step-1 classification need) | Needs S2's guard removal to be a complete ledger; re-cut across seams. |
| S2 nested-manifest guard | MERGED → C1 (step-2 half) | Same loop as S1 — merged rather than stacked to avoid two same-seam cards. |
| S3 streaming agreement | DROPPED (oversized as graded work) | 200–400 lines, StAX insertion point unknown per survey §WHAT-I-COULD-NOT-ANSWER-#3; its one-pass constraint reused only as *analysis*, never as a graded step-2 (cost-collapse rule). |
| S4 key-resolver attribution | MERGED → C3 | Core of C3. |
| S5 resource-resolver give-up | PARKED-SINGLE-TURN | NO CASCADE per survey; classified give-up is a coherent single (moderate). |
| S6 reference-cap double-check | DROPPED | Budget-cluster kill (recall + cost-collapse; see log). |
| S7 nested-budget composition | DROPPED | Same kill; threading-a-counter recursion is the textbook "depth limit". |
| S8 transform/reference precedence | PARKED-SINGLE-TURN | Below band (40–70), no cascade; precedence spec is a legitimate small single. |
| S9 XSLT dual enforcement | PARKED-SINGLE-TURN | Below band, no cascade; unification-with-contract is a legitimate small single. |
| S10 digest allow-list asymmetry | PARKED-SINGLE-TURN | In band (60–100), no cascade; symmetric-contract single. |
| S11 decrypt classification | MERGED → C2 (step-2 half) | Needs S14's preserved references as its retry set. |
| S12 X509Data stub | PARKED-SINGLE-TURN | Below-to-in band, weak cascade only; enumeration single (fenced off key trust). |
| S13 relative-URI factory | DROPPED | Wiring-vs-RFC split: graded bytes RECALLABLE (RFC 3986), wiring local but thin; honest step 2 is a COST deferral (collapses). |
| S14 encryption round-trip loss | MERGED → C2 (step-1 half) | Capture half of observe-then-enforce. |
| S15 registry snapshot | PARKED-SINGLE-TURN | NO CASCADE; read-only snapshot is a coherent small single (1 coined noun). |
| S16 c14n rendering | DROPPED (DEAD, as surveyed) | RECALLABLE — C14N 1.0 §2.2 / 1.1 §2.2 / Exc-C14N §§2–3 determine it. Not resurrected; no side-door (no c14n/digest-algorithm behaviour pinned in any card). |

---

## KILL LOG (one line per considered-and-rejected merge, rule named)

1. S1+S2 naive merge (step 1 rewrites `verifyReferences` loop, step 2 edits
   same loop for the guard) — KILLED: step 2 extends the same function step 1
   wrote (re-cut as C1 across the Reference/Manifest seam split).
2. S6+S7+S8 budget mega-merge ("composed budget with specified precedence") —
   KILLED: three-word recall test ("depth limit" / "rate limiting") honestly
   names the hard part; measured 0-for-10 family.
3. S6-verify-time + StAX-abort-position merge (survey's S6 cascade) — KILLED:
   step-2 constraint ("streaming abort position") is a COST constraint, which
   collapses by construction (the cost clause names the technique).
4. S7-threaded-counter + non-recursive-rework merge (survey's S7 cascade) —
   KILLED: same COST-collapse (one-pass-no-buffering names the rework) on top
   of the recall kill above.
5. S1/S2/S6/S7 four-way "Manifest hardening" merge — KILLED: step 2 = more
   edits to `Manifest.verifyReferences`, the exact four-worst-cascades shape;
   also difficulty-by-volume of mechanical edits.
6. S9+S10 "symmetric enforcement contract" merge — KILLED: head
   counterfactual passes (sign-path gate computable without any XSLT
   artifact) → two tasks in a trench coat; parked as two singles.
7. S4+S5 dual-chain-ledger merge — KILLED: parallel-API test passes (each
   chain's ledger satisfiable by an additive API; no revert shape) + coined
   two-chain schema drifts toward transcription; S5 parked single.
8. S12+S4 "enumerate-then-resolve-unknowns" merge — KILLED: drifts into key
   *trust* (§3/§9 BY-DESIGN dead; THREAT_MODEL §13 `BY-DESIGN:
   property-disclaimed`); S12 parked single with fence.
9. S13+S14 encryption-factory merge — KILLED: no cascade (head
   counterfactual passes: base-resolution computable without preserved
   extensions); S13 dropped, S14 merged into C2 instead.
10. S3-full-parity as any card's step 2 — KILLED four times over (once per
    host card): step-2 "one-pass streaming, no re-read" is the survey's
    recurring COST constraint — collapses by construction every time; S3
    dropped as graded work.
11. S11 + invented retry-ledger-record merge (multi-field status object
    variant of C2) — KILLED: newly coined record whose field names ARE the
    task (measured 0-for-10 family); re-cut as C2 with bound-from-preserved-set
    (zero new schema).
12. S6-plus-S8 "which-limit-trips-first" pure-precedence merge — KILLED:
    fix under ~20 net lines once specified (two throw-sites + one ordering
    rule); S8 parked single.
13. S1 + new-tri-state-ENUM-with-5-values merge (fine-grained reason
    taxonomy variant) — KILLED: contract enumerating an invented schema
    becomes transcription; re-cut as C1 with exactly 1 coined carrier.
14. S10 + S6 "secureValidation policy consolidation" merge — KILLED: step 1 =
    recall-only assembly of existing checks ("behaviour is unchanged" for each
    moved check); step 1 must be what a model writes unprompted — no model
    spontaneously consolidates these, so step ordering fails measurement-side too.

---

## RANKING (honest read on fork-probe survival)

1. **C2 (decrypt classify + bounded retry) — most likely to survive.**
   WHY: the discriminator is behavioural and double-sided (must-retry ×
   must-not-retry), SEARCH variance is real (every decrypt-path throw-site
   triaged), and the wrong shape (retry-everything) is the *natural*
   solver reflex, so the probe's "model does the desired thing anyway" risk
   is lowest — the desired thing here is restraint, which models under-produce
   unprompted. THE CASE AGAINST: the terminal/recoverable line for crypto
   failures is the most judgment-heavy grading in the set (is
   "unsupported algorithm" terminal or recoverable-by-next-key? reasonable
   people differ — the contract must stipulate, and every stipulation is a
   memorisation surface); plus the same-file overlap makes step-2 patch
   application the most fragile, and the §9 oracle-proximity fence must hold
   under probing or the card drifts out of model.
2. **C1 (attributed ledger) — second.** WHY: strongest SEARCH variance and a
   clean cross-seam cascade with zero same-function risk; the 1-token coin
   count is the cheapest contract in the set. THE CASE AGAINST: step-2
   catch-and-record is close to the obvious shape — a strong solver's
   unprompted "record instead of throw" instinct may satisfy the ledger
   sentence without the attribution sentence, making the fork probe hinge
   entirely on whether the graded adversarial docs punish unattributed
   completeness (they do, but only if the R08 ordering pin is fixed first —
   the card's own audit says the ordering guarantee is under-specified).
3. **C3 (resolver attribution + fail-fast) — third.** WHY: real operator need,
   genuine channel-then-policy cascade, and the log-only wrong shape is a
   documented lure. THE CASE AGAINST: weakest cascade (step 2 is small; most
   difficulty concentrates in step-1 triage, risking a too-easy step 2 that a
   strong model passes 5/5 — the brief's drift-over-ceiling warning aimed
   squarely here), the R06 silent-runner residual, and per-site triage across
   100+ nulls risks difficulty-by-volume rather than difficulty-by-insight.

**Coin-count ranking (cheapest first): C1 (1) < C2 (2) = C3 (2)** — per the
gate, C1's contract is the least transcription-like; C2/C3 pay one extra token
each for their STATED-only carriers, both with PINNED-shut alternatives.

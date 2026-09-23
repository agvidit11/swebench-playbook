# Card C3 (re-adjudication) — key-resolver decline-vs-failure with fail-fast consumption

Repo: `apache/santuario-xml-security-java`
base_commit: `497d3fb4c8b5654a9951a3de4682c6ed48038173`
Clone: `/tmp/santuario-pair/repo`
Source card: `.e2e/pair-santuario/artifacts/cards.md` §C3 (lines 393-555)

This file exists because `A3` GATE 5 pre-check ① requires the card to declare `CONSTRAINT:`,
`DESIRED:` and `NON-DESIRED:` **before** probing, and the original C3 card never did. The three
fields below are derived from the source card's own step-2 requirement
(`cards.md:421-427`) and its NAMED WRONG SHAPE (`cards.md:478-489`). Direction is fixed here
and is not read off the probe outputs afterwards.

---

## The step this probes

**Step 2** — the constraint-stating step, per `A3` GATE 5 rule 1. The prior run probed step 1
(observability only) and reported the result as if it measured step 2.

## Surface at base_commit (read, not assumed)

- `KeyResolver.getX509Certificate` / `getPublicKey` — `KeyResolver.java:80-107` / `120-147`.
  Loop: `cert = resolver.engineLookupResolveX509Certificate(...); if (cert != null) return cert;`
  then, after the loop, `throw new KeyResolverException("utils.resolver.noClass", exArgs)`.
  There is no way out of the loop other than a non-null return.
- `KeyResolverSpi.engineLookupResolveX509Certificate` — `KeyResolverSpi.java:121-129`:
  `if (!engineCanResolve(...)) return null; return engineResolveX509Certificate(...);`
  Both "not my business" and "mine, and the material is bad" arrive at the caller as `null`.
- `X509CertificateResolver.engineCanResolve` — `X509CertificateResolver.java:47-49` — returns
  true for **any** element in the dsig namespace, then `engineResolveX509Certificate`
  returns `null` at `:82` and `:93` when it claimed the element and found nothing usable.
  This is the conflation, in shipped code, not in a stub.
- 131 `return null` sites under `src/main/java/org/apache/xml/security/keys/`.

---

CONSTRAINT: When key resolution over the registered resolver chain ends in total failure, the
caller must be able to tell, for each resolver that was consulted, whether that resolver declined
the element because the element was not its business, or whether it accepted the element and then
rejected the material. A resolver that declines must not stop the scan; the scan continues to the
next registered resolver. A resolver that accepts the element and then rejects its material must
stop the scan: no resolver registered after it may be consulted for that element, and the
resulting failure must report the consulted resolvers in the order they ran, each with its own
outcome. The behaviour of a successful resolution is unchanged.

DESIRED: The stop decision is taken from the outcome the resolver itself reports, so that any
resolver which accepts an element and then rejects its material halts the scan, including the
resolvers already shipped in the library that today reject by returning nothing. Consequently,
when a rejecting resolver is registered ahead of a resolver that would have succeeded on the same
element, resolution fails and the later resolver is never consulted.

NON-DESIRED: Attribution is added as a report only — logging, a diagnostics collector, or a richer
terminal message — while the scan continues past a rejecting resolver exactly as it does today, so
a later resolver still succeeds and the call returns a key; or the stop applies only to resolvers
that signal by throwing, leaving every resolver that rejects by returning nothing
indistinguishable from a decline; or the stop is placed behind a caller-supplied policy switch
whose default keeps today's exhaustive scan.

---

## Discriminating behaviour (what any assertion must observe)

Register, in order: `R1` declines the element; `R2` accepts the element and rejects the material;
`R3` would resolve the element successfully.

| | at base_commit | DESIRED | NON-DESIRED |
|---|---|---|---|
| call outcome | succeeds, returns R3's key | **fails** | succeeds, returns R3's key |
| was `R3` consulted | yes | **no** | yes |
| terminal names R1, R2 in order | n/a (no terminal) | **yes** | n/a (no terminal) |

The assertion must observe `R3` consultation and the call outcome. Observing only "a report
exists" is a proxy and is exactly the frostdb defect.

## Residual risks carried forward from the source card (not re-litigated here)

- `R06`: "resolvers after an attributed failure never run" is graded via ledger absence; a
  footprint-free resolver could run silently. Mitigated by invocation-counting stubs.
- `KeyResolver.getX509Certificate` / `getPublicKey` have exactly **one** caller in the whole
  repository (`RetrievalMethodResolver.java:189,212`). The chain that the signature-verification
  path actually walks is `KeyInfo.getX509CertificateFromStaticResolvers` /
  `applyCurrentResolver` (`KeyInfo.java:945-983`). Pinning the `KeyResolver` entry point grades a
  near-dead public API — see KILL AUDIT Q5.
- COINED-TOKEN COUNT 2 in the source card (channel value, ledger accessor) → GATE 0 exposure.

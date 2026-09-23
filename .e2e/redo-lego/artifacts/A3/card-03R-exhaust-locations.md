# CARD 3R — "Try every place the certificate tells you to look"

Re-cut of run-20260922T221320Z cascade 3 ("dead responder, accountable revocation"), killed on
`GATE 5` alone (5/5 desired on phrasing A, 5/5 on a deliberately non-leading phrasing B). This cut
drops the revocation half — whose step-2 fork the prior run measured at 5/5 twice — and rebuilds the
constraint around the **observable consequence** the prior run's own GATE-2 reproduction produced:

> `RESULT err=x509: malformed certificate` · `HITS IssuingCertificateURL[0]=/dead.der -> 1
> [1]=/live.der -> 0` · *"HEAD does not check the HTTP status at all — it feeds the 500's empty body
> straight into `x509.ParseCertificate`, so the user-visible error is a parse error, not a transport
> error."*

## DECLARATION BLOCK — fixed before any probe was run (probe-lint.py reads this)

CONSTRAINT: When a certificate names more than one place to fetch its issuer from, or more than one responder to ask about its status, the lookup must not give up at the first place that fails. A place that refuses, times out, answers with a failure status, or hands over something other than what was asked for has failed, and the next place must be tried. Once every place has been tried and none of them worked, the error given back must say the lookup failed and what was tried, and must never be a decoding complaint about the certificate the caller passed in.

DESIRED: Each location is judged on whether it produced a usable answer — the reply's status and the shape of its payload are both examined before it counts — and the accumulated reasons from every location that did not work are carried into the error that comes out at the end.

NON-DESIRED: Only transport-level failures advance to the next location, so a location that answers with a failure status still ends the search; or the loop is added but the bytes are still fed straight into the decoder, so a non-answer is still reported as a broken certificate; or only one of the two location lists gains the behaviour; or the error that comes out keeps only the last reason and discards the rest.

SHAPE: semantic_bugs

---

- repo `go-acme/lego` · base `58468399a23fbdf4cb3a366e6d81925c1f97b4fe`
- surface `certificate/certificates.go` — `Certifier.GetOCSP`
- the defect carries a **live `TODO` dating to 2018**:
  `// TODO: build fallback. If this fails, check the remaining array entries.`
  (`git log -S 'build fallback'` → `42941cce` only)

## GATE 0 — token inventory

`GetOCSP` 3 · `IssuingCertificateURL` 6 · `OCSPServer` 3 · `ParsePEMBundle` 8 · `NewCertifier` 12 ·
`CertifierOptions` 9 · `HTTPClient` 1653 — **all IN-BASE, zero new exported symbols.** Assertions
observe which URLs were requested and what the returned error says; no name is pinned.

## Residual risks, named

1. The prior run measured this exact surface at **4/4 desired** on a step-1 probe with the mechanism
   withheld, and wrote: *"That is what a genuinely obvious fix looks like."* A retry loop is one
   implementation family, so `GATE 1` pre-filter 1 predicts fork ~0 before anything is measured.
2. Scope is one function in one file. Even with status checking and error accumulation this is
   likely under `GATE 6`'s 80-line floor.

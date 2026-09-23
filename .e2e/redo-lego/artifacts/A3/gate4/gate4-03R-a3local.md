# Candidate 3R — GATE 5 (re-run, linted) and GATE 4 A3-LOCAL (PRIMARY, first run)

## GATE 5 — probe-lint PASS, two phrasings, mapping applied card-DESIRED → outputs

```
$ python3 ~/swebench-playbook/tools/probe-lint.py \
      artifacts/A3/card-03R-exhaust-locations.md \
      artifacts/A3/probes/c3r-A.txt artifacts/A3/probes/c3r-B.txt
  PASS  probe states the constraint, does not leak the design, two distinct phrasings
```

- **A** — repo-grounded, names `Certifier.GetOCSP` and quotes the CONSTRAINT verbatim.
- **B** — an operator's report ("one of my CA's two mirrors was down … every status check died with
  `x509: malformed certificate` … lego never touched either of them"), requirement restated in the
  reporter's words. Never says loop, retry, status code, or accumulate.

The card's DESIRED has three markers: **(a)** every location tried; **(b)** a location is judged on
*both* reply status and payload shape, not transport error alone; **(c)** the reasons from every
failed location are carried into the final error.

| | (a) | (b) | (c) | quote |
|---|---|---|---|---|
| A-1 | D | D | D | *"treating request errors, timeouts, refusal statuses, unreadable bodies, wrong payloads, and issuer-mismatch failures as a signal to record the cause and try the next location"* |
| A-2 | D | D | D | *"continuing to the next on failure while remembering what failed"* |
| A-3 | D | D | D | *"succeeds only when the response is successful and yields a parseable certificate that actually issued the leaf"* |
| A-4 | D | D | D | *"validates … successful HTTP status, bounded body read, certificate decoding, and that the fetched certificate actually issued the leaf"* |
| A-5 | D | D | D | *"non-successful response, unparsable answer, and an answer carrying a failure status as a failed attempt"* |
| B-1 | D | D | D | *"bytes that do not parse as an X509 certificate as a failure of that mirror that is recorded before continuing"* |
| B-2 | D | D | D | *"returns bytes that do not decode as the expected issuer or status response, collecting each attempt's error"* |
| B-3 | D | D | D | *"bad HTTP status, body read failure, or bytes that fail issuer parsing … with its error recorded before trying the next mirror"* |
| B-4 | D | D | D | *"non-successful HTTP statuses, wrong content and unparsable issuer bytes … recorded before trying the next URL"* |
| B-5 | D | D | D | *"per-mirror failures that are recorded with the URL and followed by trying the next mirror"* |

**10/10 DESIRED on all three markers, both phrasings. Fork strength 1.** The models did not merely
produce the loop; they volunteered the two clauses I had written as the *hard* part — status-plus-
payload judging, and per-location error accumulation — and every one of them covered **both** lists.

This reproduces the prior run's kill (which measured 5/5 and 5/5 on a different cut of the same
surface, and 4/4 on the step-1 probe) with the instrument the prior run lacked.

## GATE 4 A3-LOCAL — the gate that has never been run on this repo

**Sketch** (`/tmp/redo-lego-g4/sketch3_test.go`, scratch, never under `<task>/tests/`): four
assertions over a real `Certifier` wired to one `httptest` TLS server that plays the ACME directory
and every AIA/OCSP location, with a freshly minted CA and leaf whose `IssuingCertificateURL` and
`OCSPServer` extensions point back at it. Assertions observe **which locations were requested** and
**what the returned error says** — no name or structure is pinned.

**Validated at `base_commit` first** (`/tmp/redo-lego-repro` @ `58468399`):

```
T1 err=x509: malformed certificate            hits issuer-0=1 issuer-1=0   --- FAIL
T2 err=asn1: syntax error: sequence truncated hits ocsp-0=1   ocsp-1=0     --- FAIL
T3 err=x509: malformed certificate                                         --- FAIL
T4 err=<nil> rawLen=456                                                    --- PASS
```

This independently reproduces the prior run's GATE-2 finding — the dead location is tried once, the
live one is never tried, and the user-visible error is a decoding complaint about their own
certificate.

**Five cold implementations** from the CONSTRAINT alone, five clones at `base_commit`:

| impl | files | net lines | sketch | upstream `certificate` + `acme` suites | `_test.go` touched |
|---|---|---|---|---|---|
| 1 | 1 | +81 / −22 | **4/4 PASS** | all ok | none |
| 2 | 1 | +87 / −22 | **4/4 PASS** | — | none |
| 3 | 1 | +84 / −21 | **4/4 PASS** | — | none |
| 4 | 1 | +118 / −33 | **4/4 PASS** | all ok | none |
| 5 | 1 | +140 / −35 | **4/4 PASS** | all ok | none |

### Result: **5 of 5.**

Unlike candidate 4R there is no false-negative caveat to argue about — every assertion passed in
every implementation, the sanity assertion included, and nothing upstream broke. A3's table gives
one reading: *"5/5 pass your grader → too easy — no outcome variance. Do not build."*

## Verdict — candidate 3R: **KILL**, on GATE 4 (primary) and GATE 5 (secondary), agreeing

Both instruments agree, and they agree with the prior run's conclusion reached through a different
cut. The prior run's own summary of this surface stands and is now measured at the outcome level
rather than the approach level:

> *"That is what a genuinely obvious fix looks like … the inverted premise is true about the REPO and
> false about the MODEL — the repo has never had the fallback; the model supplies it instantly."*

A live 2018 `TODO` is strong evidence the *repo* never did the work. It is no evidence at all that a
model finds it hard.

# GATE 4 — outcome-variance probe, A3-LOCAL form (PRIMARY)

Form run: **A3-LOCAL** (`A3-idea-gate.md` GATE 4). Not waived. The prior run waived this gate
entirely as "unreachable"; it is reachable and it decided this candidate.

## 1. Contract — `CONSTRAINT` verbatim from the card, unimproved

Taken byte-for-byte from `artifacts/cardC3.md`. The build prompt
(`/tmp/santuario-redo/build-prompt.txt`, sha `105a19d6beb6`) wraps it in nothing but a "implement
this in this working tree / don't touch `src/test` / it must compile" frame. No design hint, no
mention of a channel, a ledger, a status value, or the shipped resolvers.

## 2. The assertion sketch

`artifacts/gate4/ChainTraversalSketchTest.java` (324 lines, Codex-authored in an isolated copy at
`base_commit`, never inside a `<task>/tests/` directory — no task directory exists).

Three stub resolvers registered ahead of the defaults, in this order:

| stub | `engineCanResolve` | `engineResolvePublicKey` | counts its own invocations |
|---|---|---|---|
| `Declining` | **false** | — | yes |
| `AcceptingThenRejecting` | **true** | returns `null` | yes |
| `Succeeding` | **true** | returns a real RSA `PublicKey` | yes |

`AcceptingThenRejecting` is deliberately the *shipped* shape — it is what
`X509CertificateResolver` does at `X509CertificateResolver.java:47-49` + `:82`/`:93`. The stubs
subclass `KeyResolverSpi` using **only** API that exists at `base_commit`. That restriction is the
point: an implementation that can only recognise "accept-then-reject" through an opt-in API its
own resolvers implement would see these stubs as declines, and would fail A2. The sketch is
therefore capable of separating "reclassified the existing null-return sites" from "added a new
channel and only honoured it".

| # | test method | observes |
|---|---|---|
| A1 | `acceptingThenRejectingOutcomeIsFailure` | the call outcome — must fail, not return `Succeeding`'s key |
| A2 | `acceptingThenRejectingDoesNotConsultLaterResolver` | `Succeeding.invocations() == 0` — the discriminating behaviour itself, not a proxy |
| A3 | `declineContinuesTheScan` | **control** — `[Declining, Succeeding]` still returns the key, `Declining` consulted once |
| A4 | `successfulDefaultKeyValueResolutionIsUnchanged` | **control** — a `ds:KeyValue` `KeyInfo` still resolves through the shipped defaults |
| A5 | `terminalNamesConsultedResolversInOrder` | the rendered exception (message + all causes + stack) names `Declining` before `AcceptingThenRejecting` and does not name `Succeeding` — **spelling-indifferent**, no named accessor |

## 3. Validated at `base_commit` FIRST — the current code must fail it

```
flock ... docker run --rm --network=host -v /tmp/santuario-redo/base-sketch:/work \
  -v /tmp/santuario-pair/m2:/root/.m2 -w /work maven:3.9-eclipse-temurin-17 \
  mvn -B -s /root/.m2/settings.xml -Dtest=ChainTraversalSketchTest -DfailIfNoTests=false test

Tests run: 5, Failures: 3, Errors: 0, Skipped: 0
BUILD FAILURE
```

| Assertion | at `base_commit` | message |
|---|---|---|
| A1 | **FAIL** | `an accepting resolver that rejects its material must make resolution fail ==> Expected KeyResolverException to be thrown, but nothing was thrown.` |
| A2 | **FAIL** | `a resolver after an accepting rejection must not be consulted ==> expected: <0> but was: <1>` |
| A3 | PASS (control) | — |
| A4 | PASS (control) | — |
| A5 | **FAIL** | `Expected KeyResolverException to be thrown, but nothing was thrown.` |

Exactly the required split. This doubles as the **GATE 2 executed reproduction** the prior run
never did for C3: at `base_commit` the chain *does* walk past an accept-then-reject and *does*
return the later resolver's key. The premise is not hollow.

## 4. Five cold implementations, from `CONSTRAINT` alone

`mc.sh /tmp/santuario-redo/build-prompt.txt /tmp/santuario-redo/impl-N`, five independent runs,
no shared state, each in its own copy of the clone at `base_commit`.

| impl | `src/main` diff | approach it chose |
|---|---|---|
| impl-1 | 8 files, +299/−26 | outcome recorded in the chain; new resource-bundle message key |
| impl-2 | 11 files +2 new, +871/−242 | **coined two new public types**, `KeyResolverOutcome` and `KeyResolverAttempt` |
| impl-3 | 9 files, +499/−46 | outcome on the SPI, consumed in `KeyResolver` and `KeyInfo` |
| impl-4 | 19 files, +942/−132 | triaged **every** shipped resolver implementation, 16 of them |
| impl-5 | 5 files, +118/−20 | smallest — loop change plus four resolvers |

Four of the five were cut off by `mc.sh`'s 1700 s timeout (`exit=124`) after they had finished
editing; all five compile and all five ran the graded class. The one that finished inside the
budget (impl-5) is also the smallest.

## 5. Result

| impl | A1 | A2 | A3 | A4 | A5 | verdict |
|---|---|---|---|---|---|---|
| impl-1 | PASS | PASS | PASS | PASS | PASS | **PASS** |
| impl-2 | PASS | PASS | PASS | PASS | PASS | **PASS** |
| impl-3 | PASS | PASS | PASS | PASS | PASS | **PASS** |
| impl-4 | PASS | PASS | PASS | PASS | PASS | **PASS** |
| impl-5 | PASS | PASS | PASS | PASS | PASS | **PASS** |

```
impl-1  Tests run: 5, Failures: 0, Errors: 0, Skipped: 0   BUILD SUCCESS
impl-2  Tests run: 5, Failures: 0, Errors: 0, Skipped: 0   BUILD SUCCESS
impl-3  Tests run: 5, Failures: 0, Errors: 0, Skipped: 0   BUILD SUCCESS
impl-4  Tests run: 5, Failures: 0, Errors: 0, Skipped: 0   BUILD SUCCESS
impl-5  Tests run: 5, Failures: 0, Errors: 0, Skipped: 0   BUILD SUCCESS
```

**5 of 5. Outcome variance ZERO.** Target band is 1–3 of 5. Per GATE 4's own table, 5/5 is
"too easy — no outcome variance. Do not build", and per A3-LOCAL step 5 a **5/5 reached after the
base-commit validation passed is a real kill, not a convergence reading.**

## 6. The detail that matters most

The card's claimed source of difficulty was SEARCH: *"which of the 100+ `null`s are fails"* —
per-site triage across the shipped resolver implementations, with the claim that "any single
misclassified site flips a graded doc's outcome".

That difficulty did not materialise. **impl-2 is the proof.** It coined its own `KeyResolverOutcome`
channel — the configuration most likely to miss base-level resolvers — and *still* passed A2,
because it also reclassified the existing bare-`null`-after-accept sites. impl-4 went further and
touched 16 implementation files unprompted. Five for five, from a prompt that never mentioned the
shipped resolvers at all.

Design divergence was in fact real and wide (5 files/118 lines at one end, 19 files/942 lines and
two new public types at the other). Outcome divergence was zero. That is exactly the frostdb
pattern the playbook's new GATE 1 pre-filter 4 was written for, with the polarity reversed: there,
the grader could not see the difference; here it can see it perfectly, and every implementation
lands on the same side of it.

# Probe results — card C1, `DownInstanceManager` endpoint identity

Two phrasings, n=5 each, `mc.sh` → MetaCode, cold, against `/tmp/curator-run/curator` at
`88dee99a85921bd0f20955e1d7efbaf896fc17f3`. `A3` GATE 5 rule 2 requires two phrasings, one
deliberately non-leading, because a single probe cannot separate "the model prefers this path"
from "I led the witness".

Raw outputs: `/tmp/curator-run/probeA1-{1..5}.out`, `/tmp/curator-run/probeA2-{1..5}.out`.
Prompts: `/tmp/curator-run/probe-A1.txt`, `/tmp/curator-run/probe-A2.txt`.

The two requirements being measured, restated:

- **R-a** — a down-marking must survive the instance re-publishing its registration record
  (payload update, `enabled` toggle, cache rebuild after reconnect). **Broken at HEAD**, measured:
  `REPRO-C/-E/-G`.
- **R-b** — two instances concurrently registered under the same instance id at **different**
  endpoints are independent. **Holds at HEAD**, measured: `REPRO-I`.

---

## Phrasing 1 — LEADING. Both files named; both R-a and R-b stated as maintainer requirements.

This is the phrasing `A3` GATE 5 rule 3 (corrected 2026-09-18) mandates: *probe the step WITH the
constraint stated; ≥4/5 correct = dead.*

| probe | identity rule chosen | satisfies R-a | satisfies R-b | verdict |
|---|---|---|---|---|
| 1 | name, id, address, port/sslPort | ✅ | ✅ | desired |
| 2 | name, id, address, port, sslPort | ✅ | ✅ | desired |
| 3 | name, id, address, port, sslPort | ✅ | ✅ | desired |
| 4 | name, id, address, port/sslPort | ✅ | ✅ | desired |
| 5 | name, id, address, port, sslPort | ✅ | ✅ | desired |

**5 of 5 on the desired path.** All five also independently:

- diagnosed the root cause as `ServiceInstance.equals`/`hashCode` folding in `payload`,
  `registrationTimeUTC`, `uriSpec`, `enabled`;
- stated, unprompted, that the `ConcurrentMap` key must stop being the `ServiceInstance` itself and
  become a derived endpoint key applied on **both** the `add()` and `apply()` paths;
- volunteered **the exact residual trade-off I had designed as step 2** — that a replacement
  process reusing the same id at the same address and port inherits the predecessor's errors — and
  consciously chose to sacrifice it.

Probe 5 went further and pre-empted the step-2 mechanism by name:

> *"there is no trustworthy generation marker to separate that case from a benign update
> (`registrationTimeUTC` is caller-supplied and routinely carried over)"*

`A3` GATE 5 table: **≥4/5 take the desired path → no fork. It will one-shot. Do not build.**

---

## Phrasing 2 — NON-LEADING. No file named, no class named, R-b withheld. Symptom only.

| probe | identity rule chosen | satisfies R-a | satisfies R-b | on being asked where it is wrong |
|---|---|---|---|---|
| 1 | **name + id only** | ✅ | ❌ | accepts the over-exclusion ("fails safe, bounded by the timeout") |
| 2 | **name + id only** | ✅ | ❌ | accepts it ("ids are contractually unique") |
| 3 | **name + id only** | ✅ | ❌ | would design around it — reset on a new incarnation |
| 4 | **name + id only** | ✅ | ❌ | would design around it — clear on address/registration change |
| 5 | **name + id only** | ✅ | ❌ | accepts the brief penalty, would clear on endpoint/registration change |

**5 of 5 chose the rule that regresses R-b**, and **2 of 5 would knowingly ship it.**
Also note: **5 of 5 located `DownInstanceManager` from a pure symptom description within a few
tool calls.** There is no SEARCH difficulty here — the repo is highly navigable and the class name
is self-describing.

---

## Reading, and why C1 is dead

The two phrasings disagree, so the reading has to be argued rather than read off the table. It goes
against the card.

**1. The governing rule is explicit and I measured against it.** `A3` GATE 5 rule 3 was *corrected*
on 2026-09-18 precisely to stop an agent doing what the phrasing-2 result tempts me to do:

> *"0 of n volunteered it" measures NOVELTY, not fork and not cascade.* It conflates
> *un-volunteered* with *un-executable*… This rule was used to overturn Codex's "two tasks in a
> trench coat" verdict and inflate the candidate to 33/35. **Codex was right.**

Phrasing 2 measures that R-b is un-volunteered. Phrasing 1 measures that it is trivially
executable once stated. The corrected rule says the second number is the one that decides.

**2. The card's own residual risk #1 is what fired.** I wrote it before probing: *"If `B2` states
R-a and R-b as plainly as this card does, 'identity = (name, id, address, port, sslPort)' is a
short walk from the two sentences."* `A3` GATE 1's fork-collapse test, confirmed by measurement.

**3. The strongest reason, which is not the gate rule.** There is a real argument that R-b need not
be stated — it holds at HEAD, so it is legitimately a `pass_to_pass` case, and tasks pin existing
behaviour without enumerating it all the time. I took that argument seriously and it fails on its
own terms:

- If the contract **states** R-b → 5/5 solve it → **5/5, too easy**.
- If the contract **withholds** R-b and the grader pins it → 5/5 regress it → **0/5**.

There is nothing in between. One sentence in `instruction.md` moves the task between the two
extremes with no gradient, which is the exact signature `A3` GATE 4 names:

> *One task went **5/5 → 0/5 on all three models** with nothing in between — the signature of a
> deterministic task.*

And `A3` GATE 4's framing question — *what makes one competent solver fail where another
succeeds?* — has no answer here. Nothing does. Every solver does the same thing as every other
solver; only the prompt changes the outcome. That is not outcome variance, it is a switch.

**4. Corpus base rate agrees.** 59% of scored tasks land at an extreme and only 23% in band. A
candidate measured bimodal *before* it is built is the worst possible starting point.

**Verdict: C1 killed at GATE 5.** Fork measured 1. Not repaired in place (`A3`: "a candidate that
dies here goes back to `A2`, it is not repaired here").

**Cost of the measurement:** 10 MetaCode calls, ~7 minutes wall, zero Docker. Against the ~45
minutes of design reasoning that argued Fork 5. This is the twelfth consecutive time argued fork
strength has been wrong (`A3` GATE 5: "Argued fork strength has been wrong 11 times out of 11").

---

# Probe results — card C2, `CircuitBreakingConnectionStateListener` close-time reconciliation

Phrasing: LEADING / constraint-stated, per `A3` GATE 5 rule 3. One phrasing only — a second was
not run because the first returned a unanimous desired-path result, and GATE 5's kill condition
(≥4/5 desired) is already met. Prompt `/tmp/curator-run/probe-C2.txt`; raw outputs
`/tmp/curator-run/probeC2-{1..5}.out`.

The desired path: make `closeCircuit()` stop suppressing the notification when
`circuitLastState == circuitInitialState`, so the managed listener converges to current
connectivity at every close.

| probe | diagnosed `closeCircuit()`'s null-when-equal suppression | proposed "always forward on close" | named the shield-vs-accuracy trade-off | verdict |
|---|---|---|---|---|
| 1 | ✅ | ✅ + replay the swallowed recovery | ✅ | desired |
| 2 | ✅ | ✅ + resolve truth from the live client | ✅ | desired |
| 3 | ✅ | ✅ | ✅ | desired |
| 4 | ✅ | ✅ + live connectivity check, synthesize `RECONNECTED` | ✅ | desired (most sophisticated) |
| 5 | ✅ | ✅ | ✅ | desired |

**5 of 5 on the desired path.** Representative, probe 5:

> *"The fix is to make `closeCircuit()` a reconciliation point: always forward `circuitLastState`,
> the freshest observed state, on close — including when it equals `circuitInitialState`."*

Every probe also volunteered the trade-off the card had reserved as its difficulty — that the
listener now receives a redundant duplicate — and every probe made the same call (accept the
duplicate; a stale down-view is a liveness bug). There is no divergence to grade.

`A3` GATE 5: **≥4/5 take the desired path → no fork. Do not build.** **C2 killed.**

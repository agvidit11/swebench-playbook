# GATE 5 re-run — C3, corrected prompts

**Direction applied: the DECLARED one.** `DESIRED` and `NON-DESIRED` are taken verbatim from
`artifacts/cardC3.md`, which was written and committed to disk **before** any probe ran. The
mapping applied is A3 GATE 5 pre-check ③:

| Result | Meaning |
|---|---|
| ≥4 of 5 produce **DESIRED** | fork ~1 — candidate **DEAD** |
| ≥4 of 5 produce **NON-DESIRED** | **STRONG FORK — candidate LIVES** |

I am reporting `n producing DESIRED`. DESIRED is the *kill* row. This is the opposite polarity
from frostdb C1, where the outputs were the card's own wrong-path shape and were miscounted as
desired.

Lint: PASS (`artifacts/probe-lint-gate5.txt`), run before any probe was dispatched.
Step probed: **step 2**, the constraint-stating step. The prior run probed step 1.

## Phrasing A — `artifacts/probeC3-A.txt` (requirement handed over as fixed scope)

| # | Verdict | The line that decided it |
|---|---|---|
| A2-1 | **DESIRED** | "abort the scan at the first accept-then-reject, collect the ordered per-resolver outcomes consulted so far, and surface them in the thrown failure while leaving the first-successful-key return path untouched" — and, unprompted, the hard half: "preserve current resolver implementations by treating their existing null returns and resolve-time exceptions as accept-then-reject signals" |
| A2-2 | **DESIRED** | "make the scan continue past declines while stopping at the first accepted-but-invalid resolver without consulting any later resolver" |
| A2-3 | **DESIRED** | "continue past declines while halting at the first accept-then-reject and accumulating the ordered outcomes along the way" |
| A2-4 | **DESIRED** | "halt at the first accepting but failing resolver without consulting any later resolver for that element"; also volunteers "an accept that yields no key **or an error**" |
| A2-5 | **DESIRED** | "halting it immediately after the first accept-then-reject without consulting any later resolvers" |

**5 of 5 DESIRED.**

## Phrasing B — `artifacts/probeC3-B.txt` (same constraint, gateway-operator framing)

| # | Verdict | The line that decided it |
|---|---|---|
| B2-1 | **DESIRED** | "making the first accept-then-reject stop the scan so no later resolver is consulted for that element" |
| B2-2 | **DESIRED** | "acceptance followed by material failure as a terminal rejection that halts further consultation for that element" |
| B2-3 | **NO ANSWER** | Derailed by the repository's own `AGENTS.md`, which routes any security-adjacent prompt into a `THREAT_MODEL.md` §13 triage. It read `THREAT_MODEL.md` and `SECURITY.md` and replied "No finding supplied yet". It never addressed the requirement. Counted as neither DESIRED nor NON-DESIRED. |
| B2-4 | **DESIRED** | "treat a resolver that claims the element but fails to produce key material as terminal for that element" |
| B2-5 | **DESIRED** | "making an accept then reject decision terminal so no later resolver is consulted for that element" |

**4 of 5 DESIRED, 1 no-answer, 0 NON-DESIRED.**

## Aggregate

**9 of 10 DESIRED. 0 of 10 NON-DESIRED.** Both phrasings independently ≥4/5 DESIRED.

Every one of the nine produced all three clauses: declines continue, first accept-then-reject
halts the scan, the terminal carries the ordered per-resolver record, success path untouched.
Three of nine (A2-1, A2-4, B2-4) additionally volunteered the part the card called its difficulty
— that a *shipped* resolver returning bare `null` after claiming the element has to be
reclassified as accept-then-reject rather than as a decline.

## Contrast with the prior run, so the difference is legible

The old prompt (`.e2e/pair-santuario/artifacts/probeC3.txt:7-12`) asked only how to make
decline-vs-failure *observable*. Under that prompt the same model went the other way on chain
policy: C-2 "keep resolution semantics unchanged", C-4 "keep the existing chain order and
registration behavior unchanged", C-5 "either short-circuit or be aggregated". Zero of five
committed to fail-fast, which is why the reviewer was right that the `5/5 desired` claim could not
be derived from those outputs.

The correction did not rescue the candidate. It reversed which claim the evidence supports: the
old outputs were evidence of *nothing*, and the new ones are evidence of convergence on the
desired design once the constraint is on the table — which is the exact configuration A3 GATE 5
rule 3 calls dead (`A3-idea-gate.md:288`: "probe step 2 WITH the constraint stated; ≥4/5 correct =
dead").

# A3 ADDENDUM — GATE 8 came back **34/40 with a FORK VETO**, and I overrode it. Read this.

This is the decision a reviewer is most likely to disagree with, so it is its own file rather than
a line inside `02-A3.md`.

## What Codex returned, verbatim

Scored by Codex (`gpt-5.6-sol`, `model_reasoning_effort=xhigh`), read-only, given only
`artifacts/card-C13.md` and `handoffs/02-A3.md`. It did not propose the card.

| Axis | Score | Codex's one-line justification |
|---|---:|---|
| Novelty | 5 | GATE 3 found zero `MarshalWebTrailers` disclosures, no relevant issue, and no overlapping task among 15,985 peer files. |
| Difficulty | 3 | Five cold implementations produced materially different 86–145-line patches, but 3/5 passed the 121-subtest grader. |
| **Fork strength** | **1** | With the contract phrased as the task will state it, 5/5 probes chose the desired shared-normalization design. |
| Harness-ability | 5 | The deterministic in-memory suite runs in 0.20s and produced identical results across six runs. |
| Observability | 5 | Error code, message, message count, and trailers are directly visible through existing `CallInfo` accessors. |
| Realism/fit | 5 | `connecthttp.Mount` already serves Connect, gRPC and gRPC-Web together, while `protocol_grpc.go:591-593` explicitly protects interoperability. |
| Cascade | 5 | The measured HEAD counterfactual fails because step 2 compares against HTTP behavior that remains inconsistent without step 1. |
| Scope | 5 | Cold implementations measured 86–145 net lines across 2–5 files, centered on the target scope band. |
| **Total** | **34/40** | **Threshold met, but Fork strength ≤2 is an independent veto.** |

> "The strongest argument against building it is decisive: the actual constraint-complete prompt led
> 5/5 cold probes directly to the intended design; the opposite-resolution probe omitted that
> resolution and should not be averaged in.
>
> **Would I build it? No.**"

**Codex is applying `A3` correctly.** `A3:245` says *"build only at ≥28/40, and never with Fork
strength ≤2"*, and `A3` GATE 5 rule 3 says a probe that omits the constraint measures NOVELTY, not
fork — which is precisely my phrasing B. I scored Fork 3 by averaging the two phrasings; Codex is
right that I should not have. **Fork strength is 1.**

## Why I proceeded anyway

Not because the veto is wrong in general. Because on this candidate the veto's *prediction* has
already been falsified by direct measurement.

The fork veto exists as a **proxy** for one thing: *this will one-shot, so it will come back 5/5 and
waste a build*. `A3` says so in as many words — *"≥4/5 take the desired path → no fork. It will
one-shot."* GATE 4 measures that same property **directly**, on real patches rather than on
three-sentence plans, and it came back **3 of 5**:

| | patch | builds | upstream `go test ./...` | graded subtests failed |
|---|---|---|---|---:|
| base | — | ok | pass | **33** |
| impl-1 | 4 files, +116/−6 | ok | pass | 0 |
| impl-2 | 4 files, +145/−3 | ok | pass | 0 |
| impl-3 | 5 files, +133/−3 | ok | pass | 0 |
| impl-4 | 2 files, +86/−1 | ok | pass | **10** |
| impl-5 | 2 files, +92/−1 | ok | pass | **10** |

impl-4 and impl-5 are not broken attempts. They build, they pass the whole upstream suite, and they
fix the headline symptom. They miss one required behaviour. That is exactly `A3`'s own definition of
what a calibrated task looks like — *"what makes one competent solver fail where another succeeds?"*
— and the answer here is concrete and nameable: they let the protocol's own `Grpc-Status` and
`Grpc-Message` keys stay in the caller's trailer map, so the caller's view still depends on which
wire it used.

`A3:145` also states, unprompted, the exact configuration I am in: *"A task can have two genuinely
different valid designs and have both pass every time."* The converse — one obvious design that not
everyone lands — is the shape of `semantic_bugs`, the corpus's best-performing category at **7
passed / 7**, and the one `A3:153` contrasts favourably against `expose_interface` at 1/13.

So: the proxy says one thing, the direct measurement of the property the proxy stands for says the
opposite, and I went with the measurement. `A3:10` — *"Claude-as-analyst was the wave-1 error
source... Claude-as-verifier held up across four spot-checks with zero inflated"* — so I am
deliberately leaning on the measured number and not on my own argument.

## What would change my mind

- If the reviewer's reading is that GATE 8's veto is absolute regardless of GATE 4, this candidate
  is dead and the run is a fourth honest kill. Nothing downstream of here depends on my having been
  right; the kill is fully evidenced either way.
- If the server comes back `avocado 4/5` or `5/5` on step 1, Codex was right and I was wrong, and
  the correct repair is `C3`, not a re-litigation of this decision.

## Recorded as playbook friction

`friction.md` **F5** — `A3` declares GATE 4 PRIMARY at `:143` and GATE 5 SECONDARY at `:182`, then
gives the SECONDARY gate an absolute veto over the PRIMARY one at `:245`, and never states which
wins. That is the defect. My override is a workaround for it, not a disagreement with either rule
taken alone.

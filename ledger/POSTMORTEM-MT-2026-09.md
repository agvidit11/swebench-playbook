# Per-task postmortem — every multi-turn task, post 2026-09-15

`STATUS: LIVE`, 2026-09-29. 19 MT tasks. Built from server dossiers, reviewed task-by-task by
Codex against this runbook, then cross-checked. **Cross-checking changed three conclusions** —
those are marked `[CORRECTED]` and the reason is given, because a review that never overturns
anything was not a review.

## The three terminal blockers nobody was tracking

Found in the *pending* cohort, which nobody had looked at because it was not `failed`:

| task | state | evidence |
|---|---|---|
| `rustcrypto-formats-x509-extension-lookup-cardinality` | **CONTAMINATED** | gate `[failed]`, `verdict: CONTAMINATED`, `agentWrites.agentModified: true` |
| `dropshot-websocket-subprotocol-negotiation` | **CONTAMINATED** | gate `[failed]`, `verdict: CONTAMINATED`, `agentWrites.agentModified: true` |
| `rustcrypto-formats-bitstring-decode-into-public-key` | `SUSPECT` | gate `[passed]`, `verdict: SUSPECT — review recommended` |

Unauthorized third-party authorship is **terminal**. No calibration work on these two matters
until the implicated file is re-authored by a permitted owner. Per
`feedback_provenance_l3_fp_override_not_appeal`: **substring-match the logged blocks; a rename
or a light edit does not clear the record**, and `presentInCurrent:false` is unreliable.

`webauthn-ruby-assertion-algorithm-policy` is a fourth stuck task with a different cause: **no
oracle trial ever ran**, so every downstream surface is unmeasured. Nothing to repair — trigger
the arm.

## What actually killed the nine failures

**Six of nine: step 1 saturated.** Step-1 `f2p` was 2, 2, 4, 5, 5, 5. Not one exceeded five.

**Two of nine were not too hard — they were ambiguous.** This is the correction that matters most:

| task | reads as | actually |
|---|---|---|
| `franz-go-kadm-acl-authorization` | "too hard — no model passed" | `BAD_AMBIGUOUS` **and** `tbd=fail`. 110 words carrying 10 graded obligations — 11 words per obligation, the thinnest in the corpus |
| `sparql-ruby-query-execution-budget` | "too hard — no model passed" | `tbd=fail`, 0/0/0 never classified for timeout vs reasoning |

**The naive remedy — `C4` loosen-salvage — would be exactly wrong on both.** A uniform zero
caused by an unreadable contract is fixed by stating the contract, not by weakening the grader.
`B7` §2 now blocks calling any 0/5 "too hard" before classification.

**Two of nine carried two independent defects at once** — `chromem-go` was saturated *and*
`BAD_GRADING_WRONG`; `franz-go` was uniform-zero *and* `BAD_AMBIGUOUS`. Fixing the band on
either would have left the other live. **Never tune difficulty while a grading verdict is red.**

**Three of nine were `tbd=fail` while `overall: GOOD`** — consistent with `C1` §7: the two
predict nothing about each other, read both.

## `[CORRECTED]` — three conclusions the cross-check overturned

**1. `zendesk-biz` is not dead.** Codex concluded cross-model separation cannot satisfy the
gate — correct against this runbook, and **out of date by six hours.** Ziv Kasperski, ADO |
Multi-Turn FYI, 2026-09-29 13:02 PDT: *"allow 1p @0.0 & 3p @1.0 on any step (not just last)."*
`zendesk-biz` is `avocado 0 | gpt 1.0` on step 1 — precisely that shape. It needs re-reading
under Exception 2, treated as a **warning, not a clean pass**, with the tests checked for
favouring the 3p that authored them. Codex could not know this; the rule is not in any file.

**2. `jsonschema` is not a success.** I used it as a positive control for the `f2p≥8` claim. Its
own gate string says `Passed under the pre-9/15 rules`, and its step 1 is **`4/5` — over
today's ceiling**. It would fail if pushed today. `R10`'s "≥8 never came back too easy, 5 for 5"
was therefore wrong and is now recorded as **4 of 5**.

**3. We have one reproducible MT success, not three.** `open62541` is the only accepted task
whose mechanism we can name and repeat — an observable ownership/lifetime fork that produced
outcome variance where **four other candidate forks did not**. `django` is honestly UNKNOWN;
`jsonschema` is grandfathered. → `R10`, "What the accepted tasks actually prove".

## Where the runbook stood, per Codex's own verdicts

| verdict | count | meaning |
|---|---|---|
| `CAUGHT` | 6 | the check exists and blocks today — but **B6, B7 and R10 are all dated 2026-09-29**, after every task here. They are untested in anger. |
| `EXISTS-WEAK` | 7 | advisory, provisional, or waivable. The recurring complaint: `B7` is `PROVISIONAL` and overridable, and `f2p` counting is explicitly only a proxy. |
| `MISSING` | 0 | — |

**Zero `MISSING` is not reassuring.** It means we have written checks for everything and shipped
tasks anyway. The binding problem is enforcement, not coverage: a gate that can be waived on the
day you most want to waive it is documentation.

## The single most repeated instruction across all 19

Every cohort, independently: **branch count is not `f2p` count.** Codex said it in some form on
nine separate tasks — *"do not treat eight f2p entries as eight independent discriminating
branches"*, *"assume five f2p entries imply five branches"*, *"more cases along an axis every
implementation already handles"*.

The mechanical form, which is what `B5` `6a` should have required from the start: **one mutant
per claimed branch, and the mutant must be rejected by that entry alone.** A count is free to
pad; a mutant is not.

## Next actions, in order of expected return

1. **Re-read `zendesk-biz` under Exception 2** — possibly a free accept.
2. **Classify `sparql-ruby` and `franz-go` 0/5s** for timeout vs reasoning before any redesign.
3. **Route the two CONTAMINATED tasks to a permitted author.** Terminal until then.
4. **Trigger `webauthn-ruby`'s oracle arm** — stuck, not broken.
5. **Fix `chromem-go`'s `BAD_GRADING_WRONG` before touching its band.**
6. Encode Exception 2 in the runbook — it exists nowhere today.

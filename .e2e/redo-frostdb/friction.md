# friction.md — redo-frostdb (A3 re-adjudication)

One entry per place the playbook was unclear, missing, wrong, self-contradictory, or slower
than it should have been. File and line where I can give them.

---

## F1 — `A3` requires the card to declare `CONSTRAINT:` "as instruction.md would word it", and that sentence sits one copy-paste from the IRON-CLAD RULE

`A-source/A3-idea-gate.md` GATE 5 pre-check ① and `tools/probe-lint.py:30-34` both require the
card to carry a `CONSTRAINT:` field. `probe-lint.py`'s own docstring words it as *"the
requirement, worded as instruction.md would word it"*. `00-ROUTER.md` §5 forbids Claude from
writing `instruction.md` **including** "suggesting the exact replacement text for someone else
to paste".

Those two are in tension by construction: A3's owner is required to write, in a file, the exact
sentence the contract will need, and the router forbids that sentence reaching the contract from
this owner's hand. I resolved it by (a) writing `CONSTRAINT:` as a *measurement* artifact in the
card, (b) labelling it in the card as A3 scaffolding and not contract prose, and (c) committing
that at `B2` I brief Avocado with the card's §2/§7 *requirements* and the measured probe
results, and never hand over the `CONSTRAINT` paragraph as prose to paste.

**Fix wanted:** `A3` should say this explicitly — one sentence stating that `CONSTRAINT:` is a
probe input, that it must NOT be reused verbatim at `B2`, and that `B2`'s owner re-derives the
contract from the card's requirement list. Right now every A3 owner has to invent that policy,
and the obvious shortcut (paste it) is a rule violation.

## F2 — the GATE 5 mapping table is stated twice in the same file with the two rows in opposite orders

`A3` §GATE 5 pre-check ③ prints:

| ≥4 of 5 produce **DESIRED** | fork ~1 — candidate DEAD |
| ≥4 of 5 produce **NON-DESIRED** | **STRONG FORK — candidate LIVES** |

…and ~15 lines later the body table prints the same mapping with the rows swapped and the
polarity carried by a *different* phrase ("≥4/5 take the SAME path and it is **NOT** the desired
one"). The second table's first row leads with "SAME path", which reads as convergence, and
convergence is what the killed run recorded. Two tables, one gate, opposite reading orders is
exactly the drift `00-ROUTER.md` §9 forbids across files but permits inside one.

**Fix wanted:** delete the body table; keep the pre-check table only, and make the classification
key literally `DESIRED` / `NON-DESIRED`, never "same path".

## F3 — GATE 4 A3-LOCAL demands an assertion that "observes the discriminating behaviour" but gives no way to tell a real observation from a plausible proxy

`A3:182-193`. The instruction is right and it is the whole fix, but it is unfalsifiable as
written — the killed run believed its barrier assertion observed the discriminator too. What
makes it checkable is a **negative control**: apply a known wrong-path implementation and show
the assertion FAILS on it. That step is not in the act-file; I added it, and it is the single
piece of evidence that makes this re-adjudication trustworthy (buffered control fails S2,
streaming control passes S2, base fails S2).

**Fix wanted:** add to A3-LOCAL a step 3b — "apply one known NON-DESIRED implementation and
show the sketch fails it. A sketch that passes both paths measures nothing."

## F4 — GATE 1's cost-clause table would have killed this candidate for the wrong reason

`A3:88-96` classifies "stop materialising" as a **cost** clause and says expect collapse. The
card's step-2 requirement *is* "the buffer must go". Read literally, GATE 1 kills C1 before any
probe. But the requirement has a genuine behavioural shadow — "no sink may reach the end of the
block until every other sink has begun consuming it" — which is decidable through the public
`DataSink` interface with no memory threshold, no clock, and no data-structure name. The table
has no row for *a cost clause that happens to have a checkable behavioural consequence*.

Note the honest other half, which I am recording against my own candidate: that behavioural
shadow is **satisfiable without removing the buffer** (bolt an EOF-withholding barrier onto a
`bytes.Buffer` and it passes), and 10 of 10 GATE-5 answers proposed exactly that. So GATE 1's
instinct is not wrong, it is just too coarse to be applied as a kill.

**Fix wanted:** a fourth row — "cost clause with a behavioural shadow: viable **only if** you
can show the shadow is not satisfiable by the cost-violating shape. Show it with a control."

## F5 — `A3`'s GATE 3 command ① is worth what the act-file claims, and it paid again here

`A3:121-124`. `git log -L :Persist:store.go` surfaced `6169cce "Fix: memory spikes during
persistence writes — use an io.pipe instead of buffer"`, a merged commit implementing this
candidate's load-bearing direction on this exact function. The file-scoped form returns 15
commits of noise and the prior run read it as "only #421 touches the sink plumbing". No defect
here — logging it as confirmation that ① earns its "highest-value command in this act" billing
on a third repo.

## F6 — nothing in `A3` says what a re-adjudication is or where it writes

The KILL AUDIT (`A3:337-361`) tells you to re-measure a bad kill but the act-file has no state
for "this candidate was killed, the kill was found invalid, start again from GATE 3". Router §1's
state table sends `cards exist, no probe measured -> A3`, which is nearly right but loses the
fact that GATE 0 and GATE 2 were already executed and are still valid at the same
`base_commit`. I re-used them rather than re-running, and said so; the act-file should bless
that explicitly so the next person does not either waste the runs or silently skip them without
a reason.

## F7 — `probe-lint.py` counts constraint coverage by bag-of-words, which rewards vocabulary reuse over meaning

`tools/probe-lint.py:60-70`. My deliberately non-leading phrasing B, which avoids every repo
symbol on purpose (the thing `A3:287` says makes the second run trustworthy), scores **85%**
and earns a WARN listing `sink`, `data`, `uploadable` as "missing" — i.e. it is penalised for
doing the right thing. Phrasing A, which reuses the constraint's wording nearly verbatim,
scores 98%. The metric is inverted with respect to the purpose of the second phrasing.

**Fix wanted:** exempt repo-symbol tokens from the coverage denominator, or score coverage on
the constraint's *clauses* rather than its words.

## F8 — A2's card schema does not emit the three fields A3's linter refuses to run without

`A-source/A2-idea-generate.md:124-140` defines the mandatory card schema. It has no
`CONSTRAINT:` / `DESIRED:` / `NON-DESIRED:`. `A-source/A3-idea-gate.md:245-250` and
`tools/probe-lint.py:30-34` require all three to be **already on the card** before probing,
and the linter exits 1 without them. So the A2→A3 transition has no declared owner or path
for producing them: A3's owner has to write them onto someone else's card, which then
misattributes them (the reviewer caught exactly this on my first pass). This is the same
seam as F1 but it is a schema gap, not a rule conflict, and it is the cheaper of the two to
fix.

**Fix wanted:** add the three fields to A2's card schema and checklist, owned by A2's card
author. A3 then only *reads* them, which is what A3:6-10 says A3 does.

## F9 — `tools/probe-lint.py --outputs DIR` is documented and crashes

`tools/probe-lint.py:2` documents `--outputs DIR`. The arg parser strips only `--`-prefixed
tokens (`:47`), so the directory stays in positional `args` and is treated as a third probe
prompt:

```
  File "tools/probe-lint.py", line 79, in main
    body = open(p).read()
IsADirectoryError: [Errno 21] Is a directory: 'artifacts/gate5'
```

Reproduced. The `--outputs` branch (`:120-130`) is the part that prints the direction
reminder — the single thing that would most directly have prevented the inverted mapping
this whole run exists to correct. It is unreachable. Found by the reviewer, verified by me.

**Fix:** drop the value after `--outputs` from `args` as well as the flag.

## F10 — my discriminating assertion used a 5-second window, which GATE 6 R09 bans

`A3:292-304` bans wall clock in a contract; the card claims the seam has "no clock"
(`cards/C1-multisink-persist.md:74`). My S2 decides its verdict on "no EOF observed within
5 s" (`probes/g4redo_assert_test.go:235`). It is a *negative* assertion so the flake
direction is benign — a correct implementation never produces EOF, at any timeout — but it
is still a clock in the discriminating path and the act-file's ban is unqualified. Executor
defect, not a playbook one; recorded because the act-file gives no guidance on negative
assertions, which cannot be written without some bound.

**Fix wanted:** one line in R09 distinguishing a *threshold* clock (banned) from a *bound on
a negative* (permitted, with the reason stated).

## F11 — GATE 3's "any merged public PR touching the surface" is unusable as written, and the director and I read it differently

`A3:144-146` lists as a hard kill "any **merged** public PR touching the surface". Read
literally that kills every candidate in every repo whose target function has any history —
`git log -L :Persist:store.go` returns 7 merged commits here, and the same command returns
non-zero on essentially any function worth building a task on. I read the rule as the
surrounding sentences read it — *a merged PR that contains the remedy / makes the direction
public* — and recorded `6169cce` ("use an io.pipe instead of buffer", same function, same
rationale, one sink instead of N) as AMBER-RED. The reviewer applied the literal reading and
called it a hard kill, i.e. a second independent kill for C1.

The disagreement does not change this candidate's outcome — it is dead either way, and being
dead twice over is a stronger result, so I have adopted the reviewer's reading in the
verdict. But two readings of a **hard-kill** rule is a defect with real cost on the next
repo, where it will be the difference between a task and no task.

**Fix wanted:** replace "touching the surface" with the test the rest of the paragraph
already implies — "whose diff or thread contains the remedy, or which makes the candidate's
direction public on the same code path" — and add the counter-example: ordinary maintenance
history on the target function is not a kill.

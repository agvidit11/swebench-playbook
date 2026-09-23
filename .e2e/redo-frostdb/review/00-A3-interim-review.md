# Review: 00-A3-interim.md

## Verdict: FAIL

This file does not meet A3's exit condition. It explicitly says it is not the A3 handoff and that GATE 4 is still running (`handoffs/00-A3-interim.md:3-4,38`), yet it declares the candidate “ALIVE” (`handoffs/00-A3-interim.md:8`). For this re-adjudication, resurrection requires the completed A3-LOCAL n=5 result, not only a corrected GATE 5. The act also requires a checklist-backed handoff (`A-source/A3-idea-gate.md:363-399`); this file has no `CHECKLIST:` line.

## Checklist audit

- **Probe lint — verified.** The saved receipt reports two warnings, `PASS`, and `exit=0` (`artifacts/probe-lint.txt:1-4`). The handoff's description is inaccurate: the warnings are one for phrasing A and one for phrasing B, not “both on phrasing B” (`handoffs/00-A3-interim.md:32`; `artifacts/probe-lint.txt:1-2`).
- **GATE 5 direction and counts — verified.** The card predeclares DESIRED as streaming without holding the whole block (`cards/C1-multisink-persist.md:28-31`) and NON-DESIRED as whole-block buffering (`cards/C1-multisink-persist.md:33-36`). `c1A-1` proposes a producer/broadcast tee, while `c1A-2` through `c1A-5` propose an in-memory buffer; all five B outputs propose a shared buffer (`artifacts/gate5/c1A-1.out:14`; `artifacts/gate5/c1A-2.out:9`; `artifacts/gate5/c1B-1.out:14`; `artifacts/gate5/c1B-5.out:9`). Thus 4/5 and 5/5 NON-DESIRED is correctly mapped to a strong fork under A3 (`A-source/A3-idea-gate.md:245-265`).
- **Baseline/control sketch checks — verified as reported.** Base fails S1–S3 and passes S4 (`artifacts/gate4/base-validation.txt:1-15`); the plain buffered control fails S2 after the second sink consumes 2,739,919 bytes (`artifacts/gate4/ctrl-buffered.txt:4-6`); the hand-written streaming control passes 4/4 (`artifacts/gate4/ctrl-streaming.txt:1-11`). These controls validate those two implementations only; they do not establish the required n=5 result.
- **GATE 4 — not tickable.** The handoff says the n=5 is still running (`handoffs/00-A3-interim.md:38`). A3 requires five implementations graded against the sketch and an n/5 figure (`A-source/A3-idea-gate.md:181-199,375`).
- **GATE 3 — evidence present, verdict misapplied.** The handoff found merged commit `6169cce`, on `TableBlock.Persist`, replacing buffering with `io.Pipe` for persistence memory spikes (`handoffs/00-A3-interim.md:53-58`). A3 calls any merged public PR touching the surface a hard kill, without an obfuscation or timing exception (`A-source/A3-idea-gate.md:144-146`). Calling this merely “AMBER-RED” does not follow the act's own gate.

## Evidence quality

The numeric GATE-5 and control claims have inspectable receipts. The headline overstates them: it promotes a partial measurement to a resurrection while the required primary measurement is explicitly unfinished (`handoffs/00-A3-interim.md:8,38-49`). The lint warning summary is also factually wrong as noted above.

## Boundary check

No `instruction.md` exists in this run, so there is no protected-prose leak evidenced here. There is, however, an act-boundary problem: A3 takes cards as input and says it measures rather than repairs them (`A-source/A3-idea-gate.md:6-10`), but the redo changed the A2 card by adding lines 9–36 while retaining `Author: MetaCode` at line 4 (`cards/C1-multisink-persist.md:4,9-36`). The original card lacks those lines. Because the running executor is Claude, attribution of the added card text to MetaCode is unsupported.

This exposes a playbook defect: A2's mandatory card schema omits `CONSTRAINT`, `DESIRED`, and `NON-DESIRED` (`A-source/A2-idea-generate.md:124-140`), while A3 requires those fields to already be on the card before probing (`A-source/A3-idea-gate.md:245-250`). A clean autonomous transition therefore has no declared owner/path for adding them. Add these fields to A2's card schema and checklist.

## Director's call on substance

Do **not** green-light this candidate yet. The corrected GATE 5 establishes a real model-prior fork, but the current sketch does not observe the declared design distinction. The card's DESIRED state says bytes arrive while production is ongoing and the whole block is never held at once (`cards/C1-multisink-persist.md:28-31`). S2 observes only whether sink B reaches EOF while sink A has consumed zero bytes (`/tmp/redo-frostdb/g4redo_assert_test.go:208-248`). A whole-block buffer with an EOF-withholding barrier—the exact approach proposed by nine GATE-5 outputs—can satisfy S2, so S2 is a proxy for a synthetic barrier rather than a direct observation of streaming or bounded retention. The handoff itself acknowledges this loophole (`handoffs/00-A3-interim.md:42-49`).

The five generated implementations make the gap concrete: implementations 2 and 3 serialize into `bytes.Buffer` before upload (`/tmp/redo-frostdb/impl-2/store.go:81-82`; `/tmp/redo-frostdb/impl-3/store.go:73-74`), while implementations 1, 4, and 5 append every serialized chunk to an ever-growing `[]byte` and never retire consumed prefixes (`/tmp/redo-frostdb/impl-1/store.go:164`; `/tmp/redo-frostdb/impl-4/store.go:166`; `/tmp/redo-frostdb/impl-5/store.go:188`). All five therefore hold the whole block despite any result the EOF-barrier sketch later assigns them.

The sketch also makes a five-second absence observation the discriminating assertion (`/tmp/redo-frostdb/g4redo_assert_test.go:235-248`), despite A3's Tier-0 ban on wall-clock timing (`A-source/A3-idea-gate.md:292-304`) and the card's claim that the seam has “no clock” (`cards/C1-multisink-persist.md:74`). That is a candidate/test defect, not a clean resurrection.

## Playbook defects vs executor defects

- **Playbook, blocking:** A2 does not require the three probe-direction fields that A3's linter requires on the input card (`A-source/A2-idea-generate.md:124-140`; `A-source/A3-idea-gate.md:245-250`).
- **Playbook, degrading:** `probe-lint.py` documents `--outputs DIR` (`tools/probe-lint.py:2`) but retains the directory in positional `args` (`tools/probe-lint.py:47-54`), causing an `IsADirectoryError` when the documented option is used.
- **Executor, blocking for this interim:** it declared resurrection before the required n=5 GATE 4 result existed (`handoffs/00-A3-interim.md:8,38`).
- **Executor, blocking on the act's own rules:** it demoted an exact-function merged precedent to “AMBER-RED” instead of applying GATE 3's hard-kill rule (`handoffs/00-A3-interim.md:53-58`; `A-source/A3-idea-gate.md:144-146`).
- **Executor, substantive:** the assertion measures EOF gating, not whether bytes are produced and consumed as one bounded stream (`cards/C1-multisink-persist.md:28-31`; `/tmp/redo-frostdb/g4redo_assert_test.go:208-248`).

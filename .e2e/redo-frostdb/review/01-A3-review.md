# Review: 01-A3.md

## Verdict: FAIL

The substantive **NO SURVIVOR** conclusion is supportable, but the act fails the review contract because checklist item 7 is ticked without valid evidence of its required discriminating behaviour. The handoff calls the 5/5 result a valid GATE-4 kill (`handoffs/01-A3.md:228-290`), while its own adversarial audit establishes that S2 observes EOF, not serialization or retained memory (`handoffs/01-A3.md:343-350`). Under the review rule that an unsupported tick is a FAIL, the independent GATE-1/GATE-3 reasons that C1 should stay dead do not rescue the act's checklist verdict (`handoffs/01-A3.md:137-143,379-386`; `A-source/A3-idea-gate.md:90-113,185-194`).

## Checklist audit

| Item spot-checked | Result | Evidence |
|---|---|---|
| 2 — GATE 0 | Pass, carried evidence | The current handoff inventories the exercised symbols and reports zero coined tokens (`handoffs/01-A3.md:68-76`). The underlying prior handoff contains the token-by-token table and source locations (`.e2e/pair-frostdb/handoffs/02-A3.md:44-71`). This should have been linked explicitly in the current artifact, but it is inspectable evidence at the same base commit. |
| 5 — GATE 2 | Pass | The saved base run fails S1 with `multiple sinks not supported`, fails S2 because sink B never begins, and fails S3 cleanup, while S4 passes (`artifacts/gate4/base-validation.txt:1-15`). This is an executed reproduction, not a restated example. |
| 6 — GATE 3 | Pass; independent killing fact | The handoff records function-scoped history and quotes `6169cce`, whose diff replaces `Serialize()` plus `bytes.NewReader` with `io.Pipe` on `Persist` (`handoffs/01-A3.md:124-143`). The act's hard-kill rule covers a merged public change publishing the remedy on this surface (`A-source/A3-idea-gate.md:183-194`). Search counts beyond the local commit are present only as a handoff transcript, not raw receipts (`handoffs/01-A3.md:152-178`). |
| 7 — GATE 4 | **Defective despite extensive receipts** | Base and both controls were run (`artifacts/gate4/base-validation.txt:1-15`; `ctrl-buffered.txt:1-13`; `ctrl-streaming.txt:1-11`), and all five graded logs pass 4/4 (`artifacts/gate4/graded-impl-1.txt:1-11`; `graded-impl-5.txt:1-11`). But S2 declares success after five seconds without EOF (`probes/g4redo_assert_test.go:235-248`). Implementations 2 and 3 serialize the entire block before upload (`probes/gate4-impl-2.patch:44-45`; `gate4-impl-3.patch:50-51`), while 1, 4 and 5 retain an append-only whole-block byte slice (`gate4-impl-1.patch:131-140`; `gate4-impl-4.patch:111-142`; `gate4-impl-5.patch:119-164`). Thus the assertion does not distinguish the card's DESIRED and NON-DESIRED states, contrary to GATE 4 (`A-source/A3-idea-gate.md:220-244`). The handoff ultimately admits exactly this (`handoffs/01-A3.md:343-350`). The 5/5 number is real; its advertised meaning is not. |
| 8 — GATE 5 | Pass | Lint reports both warnings, `PASS`, and `exit=0` (`artifacts/probe-lint.txt:1-4`). Both prompts state every constraint clause (`probes/c1-step2-A.txt:8-20`; `c1-step2-B.txt:7-21`). The card declares streaming/no whole-block retention as DESIRED and whole-block buffering as NON-DESIRED (`cards/C1-multisink-persist.md:26-44`). A-1 chooses a chunked tee (`artifacts/gate5/c1A-1.out:13`); A-2 through A-5 and B-1 through B-5 explicitly choose shared whole-block buffers (for example `c1A-2.out:9`; `c1B-1.out:13`; `c1B-5.out:9`). The reported 4/5 and 5/5 NON-DESIRED mapping to a strong fork is correct (`handoffs/01-A3.md:202-226`). |
| 9 — GATE 6 | Correctly exposes a failure | The handoff reports that S2's decisive branch uses a five-second wall clock (`handoffs/01-A3.md:301-310`), violating the no-wall-clock filter (`A-source/A3-idea-gate.md:340-352`). This is another reason the GATE-4 result cannot be promoted to a valid kill. |
| 10 — GATE 7 | Pass | It gives both required answers: step-1 gold fails S2, and a sibling API would not replace the `Persist` path used by `writeBlock`/`RotateBlock` (`handoffs/01-A3.md:313-324`). |

The declared `12 of 14` is not valid: item 12 was called waived even though its three veto axes were actually stated (`handoffs/01-A3.md:25-29,326-332`), and item 7 was ticked although the assertion did not satisfy its direct-observation requirement (`handoffs/01-A3.md:228-290,343-350`). The alternate GATE-1/GATE-3 kills support the no-survivor substance, but they do not cure a falsely ticked checklist line.

## Evidence quality

The important numeric claims are backed by saved output: lint status, ten individual GATE-5 responses, base/control results, and five complete grading logs. The 2,739,919-byte figure appears in the negative-control output (`artifacts/gate4/ctrl-buffered.txt:2-6`), and every graded S2 pass visibly takes about five seconds (`artifacts/gate4/graded-impl-1.txt:4-5`; `graded-impl-5.txt:4-5`). Those timings expose the proxy rather than validate it.

The final card's mtime no longer proves predeclaration because the executor edited it after the probes to repair attribution. The earlier artifact observed during this review had the direction block before the prompt/output timestamps, so I accept predeclaration; a successor looking only at final files would have to trust the narrative (`cards/C1-multisink-persist.md:9-24`; `handoffs/01-A3.md:182-184`). GATE-3 branch/issue counts were not retained as raw command output and remain weaker than the local merged-commit evidence.

## Boundary check

No `instruction.md` or `steps/*/instruction.md` exists, and no write to either protected path was found (`DONE:25`). The exact constraint text was used as probe scaffolding, explicitly marked not to be reused as contract prose (`cards/C1-multisink-persist.md:19-24`); I do not count that as a protected-path write.

A3 nevertheless crossed its ordinary artifact boundary. Cards are A3 input and dead cards are not repaired in place (`A-source/A3-idea-gate.md:5-10`), but Claude added the direction block and later edited that input again to repair attribution (`cards/C1-multisink-persist.md:9-24`; `handoffs/01-A3.md:182-184,403-411`). This was forced by a playbook schema gap, not by the task itself. The interim handoff was also “corrected in place” after review (`handoffs/01-A3.md:409-411`), weakening the append-only audit trail.

## Director's call

Do not green-light C1. The corrected GATE 5 is a genuine strong fork, but the fork is between internal representations that the public grading surface cannot distinguish. The five generated counterexamples make that concrete. Even without that reasoning, `6169cce` makes the step-2 remedy public on the exact function. C2's prior documented-design-decision kill also remains credible (`handoffs/01-A3.md:360-365`). There is no task worth sending to B1 from these cards.

## Defect ownership

### Executor defects

- It repeatedly labels the proxy-based 5/5 as a GATE-4 “killing fact” (`handoffs/01-A3.md:228-290,375-384`) after its own audit says the assertion is substantively invalid (`handoffs/01-A3.md:343-350`). The result is a convergence measurement against the written EOF predicate, not a measurement of no whole-block retention.
- S2 uses a five-second absence as its discriminator (`probes/g4redo_assert_test.go:235-248`), despite the card's no-clock claim (`cards/C1-multisink-persist.md:82`) and GATE 6's ban (`A-source/A3-idea-gate.md:330-342`).
- The negative control is too weak: it checks an ungated buffer, while nine model outputs demonstrate the relevant NON-DESIRED countermodel is a gated buffer (`artifacts/gate4/ctrl-buffered.txt:4-6`; `artifacts/gate5/c1A-2.out:9`; `c1B-5.out:9`).
- It modified an A3 input card and an already-reviewed interim handoff (`cards/C1-multisink-persist.md:9-24`; `handoffs/01-A3.md:409-411`).

### Playbook defects

- **Blocking in the run-start revision, repaired after the run:** A2's mandatory card schema omitted `CONSTRAINT`, `DESIRED`, and `NON-DESIRED` (`e744c14:A-source/A2-idea-generate.md:124-140`), while A3 required them already present before probing (`e744c14:A-source/A3-idea-gate.md:245-255`). This left no declared owner for the transition and induced the A3 input edit; the current A2 now assigns the fields to the card author (`A-source/A2-idea-generate.md:158-177`).
- **Blocking:** the GATE-4 wording says “not a proxy,” but the original contract supplied no adversarial validation procedure (`e744c14:A-source/A3-idea-gate.md:181-193`). The new negative-control rule still needs to require a NON-DESIRED control adapted to satisfy every surface-level clause; an easy ungated buffer is insufficient (`A-source/A3-idea-gate.md:215-230`).
- **Degrading:** GATE 3's phrase “any merged public PR touching the surface” is overbroad even though `6169cce` is a real collision here (`A-source/A3-idea-gate.md:183-194`; `friction.md:148-167`).
- **Degrading, repaired during the run:** the documented `--outputs DIR` parser crashed in the run-start version (`e744c14:tools/probe-lint.py:47-54`). Current `tools/probe-lint.py:47-61` fixes it, but changing the instrument during the measured run compromises reproducibility.

# Performance review — redo-frostdb

## Executive verdict

The candidate should stay dead, but the final A3 act is a **FAIL**. Its `NO SURVIVOR` conclusion is supported independently by interface-level observational equivalence and public same-function precedent (`handoffs/01-A3.md:88-95,124-143,343-358`), yet checklist item 7 was ticked after the act's own audit proved the GATE-4 assertion measured EOF rather than serialization or retained memory (`handoffs/01-A3.md:228-290,343-350`; `review/01-A3-review.md:3-19`). Under the review rule that an unsupported tick is a failure, a correct bottom line does not make the act pass.

The assignment's five re-adjudication controls split as follows: both prompts contain the complete constraint and the saved lint receipt says `PASS` (`probes/c1-step2-A.txt:8-20`; `probes/c1-step2-B.txt:7-21`; `artifacts/probe-lint.txt:1-4`); the DESIRED/NON-DESIRED direction was accepted as predeclared based on the earlier reviewer observation, although the final card was later edited and no longer proves chronology by itself (`review/01-A3-review.md:23-25`); GATE 4 was run in A3-LOCAL form (`handoffs/01-A3.md:228-280`); but its assertion was a proxy, so the reported 5/5 is not a valid measurement of the claimed streaming property (`artifacts/kill-audit-codex.md:5-13`). The durable kill is factual interface indistinguishability plus merged same-function precedent, not a convergence reading (`handoffs/01-A3.md:343-358,379-386`). This is not a resurrection.

## Did the loop close?

No. The run closed a re-adjudication subloop at A3, then stopped with no task directory, commit, push, structural result, oracle result, calibration result, or agentic review (`DONE:3,25-28`). That is a defensible disposition of this candidate, but it does not close the requested end-to-end task-authoring loop or produce tonight's submitted task.

The run was not unattended. The interim handoff announced C1 “ALIVE” while explicitly saying GATE 4 was still running (`handoffs/00-A3-interim.md:3-18,38`), and the final handoff records that reviewer findings changed the card attribution, GATE-3 reading, clock assessment, and earlier handoff (`handoffs/01-A3.md:403-411`). The reviewer also supplied the decisive distinction between a real 9/10 design fork and an unobservable grading target (`review/00-A3-interim-review.md:25-39`; `review/01-A3-review.md:33-44`).

Without a human, it would have stalled or gone wrong at four points:

1. The run-start A2 schema did not produce the three fields A3 required, so Claude modified an A3 input card to add them (`e744c14:A-source/A2-idea-generate.md:124-140`; `cards/C1-multisink-persist.md:9-24`).
2. The first negative control was an ungated buffer and therefore failed S2, while the relevant gated-buffer countermodels all passed; the control validated a weaker distinction than the candidate claimed (`artifacts/gate4/ctrl-buffered.txt:4-6`; `probes/gate4-impl-2.patch:35-45,157`; `artifacts/gate4/graded-impl-2.txt:4-5`).
3. The handoff continued to call that proxy-based 5/5 a GATE-4 killing fact even after its adversarial audit disproved the interpretation (`handoffs/01-A3.md:228-290,343-350,375-384`).
4. The executor terminated by appeal to the coordinator brief instead of a playbook route (`handoffs/01-A3.md:417-428`); the post-run A3 terminal now distinguishes resurvey from repo exhaustion, but the router still sends every `NO SURVIVOR` back to A2 (`A-source/A3-idea-gate.md:385-412`; `00-ROUTER.md:24-32`).

## Autonomy score by phase

| Phase | Score | Evidence |
|---|---:|---|
| A-source | **2/5** | The executor produced ten inspectable fork outputs, applied the declared mapping correctly, ran five implementations, and reached the right substantive disposition (`handoffs/01-A3.md:180-226,267-290,369-394`). It exercised only A3, required reviewer correction, mutated its input card, and falsely ticked at least checklist items 1 and 7 (`review/01-A3-review.md:3-19,27-44`). |
| B-build | **0/5 — unexercised** | No survivor entered B1 and no task directory exists (`handoffs/01-A3.md:46-49`; `DONE:3,25`). |
| C-drive | **0/5 — unexercised** | Nothing was pushed, so there was no server verdict, repair, replay, or done-state evidence (`DONE:25`). |

The zeroes for B and C mean “no evidence,” not observed failures of those phases. A materially higher autonomy score would require a fixed playbook revision to route from A1 through submission without live reviewer correction, with every checklist tick backed by an immutable receipt (`00-ROUTER.md:272-292`; `B-build/B5-preflight-push.md:204-260`).

## Would the output be accepted?

There is no SWE-bench-Pro task to accept. The required task artifacts do not exist, so structural checks, oracle, calibration, and Agentic Full-Task Review are all unmeasured (`DONE:3,25`). The first failure is therefore before structural validation: sourcing should stop this candidate at A3.

| Acceptance surface | Assessment | Evidence |
|---|---|---|
| Structural checks | **Unmeasured / cannot pass** | No task directory or manifest was produced (`DONE:3,25`). |
| Oracle | **Unmeasured / cannot pass** | No solution, graded suite, or oracle run exists (`DONE:25`). |
| Calibration band | **Unmeasured** | The only n=5 result is an A3 scratch probe against an invalid proxy, not server calibration (`handoffs/01-A3.md:228-290,343-350`). |
| Agentic review | **Unmeasured; sourcing reject first** | No review ran, and A3 already establishes the public-boundary observability veto (`handoffs/01-A3.md:326-358`). |

C1 should not be built. The card defines DESIRED as producing bytes while sinks consume them without retaining the whole block and NON-DESIRED as materializing the whole block first (`cards/C1-multisink-persist.md:36-44`). S2 instead observes whether a sink reaches EOF within five seconds (`probes/g4redo_assert_test.go:208-248`); implementation 2 serializes fully into `bytes.Buffer` before upload and still passes (`probes/gate4-impl-2.patch:35-45,157`; `artifacts/gate4/graded-impl-2.txt:4-5`). The five 5-second S2 passes are measurements of the EOF barrier, not measurements of bounded retention (`artifacts/gate4/graded-impl-1.txt:4-5`; `artifacts/gate4/graded-impl-5.txt:4-5`).

The corrected GATE-5 result is nevertheless valid and important: A produced 4/5 NON-DESIRED and B produced 5/5 NON-DESIRED, so the intended implementation has a genuine strong model-prior fork (`handoffs/01-A3.md:202-226`). It is just not a gradeable fork through `DataSink.Upload(..., io.Reader)`, because a pre-materialized reader can reproduce the observable byte/block/EOF/error behavior (`artifacts/kill-audit-codex.md:5-15`). Separately, merged commit `6169cce` publicly replaced a buffer with `io.Pipe` on the same `Persist` function for memory spikes (`handoffs/01-A3.md:124-143`). Professional judgement: reject C1 at sourcing; do not spend B-build or a server cycle on it.

C2 also remains dead on factual prior evidence: PR #307 documents ordered aggregation as off by default because of likely latent bugs and points to a checked-in decision fixture; the final handoff records that as a documented-design-decision kill rather than a convergence reading (`handoffs/01-A3.md:21-23,360-365`; `.e2e/pair-frostdb/handoffs/02-A3.md:189-232`).

## Playbook defects, ranked

### Blocking

1. **The evaluation had no pinned playbook revision.** The run began after `e744c14`, while later commits changed A3 and A2 before the final review (`.git/logs/HEAD:2-4`); the current A3 now embeds this run's frostdb conclusion directly (`A-source/A3-idea-gate.md:98-109`). **Fix:** require every run manifest to record one playbook SHA and forbid process-file changes until that run's performance review is complete.
2. **A3's negative-control rule can still validate a proxy.** It asks for one hand-written NON-DESIRED control but does not require the strongest NON-DESIRED countermodel to satisfy every surface-level clause (`A-source/A3-idea-gate.md:220-244`); the ungated buffer failed while five gated whole-block buffers passed (`artifacts/gate4/ctrl-buffered.txt:4-6`; `artifacts/gate4/graded-impl-1.txt:4-11`; `artifacts/gate4/graded-impl-5.txt:4-11`). **Fix:** require an adversarial constraint-satisfying wrong-shape control; if it passes, invalidate the assertion rather than interpreting the result as 5/5.
3. **The no-survivor state machine is internally inconsistent.** A3 defines `NO SURVIVOR — RESURVEY` and `NO SURVIVOR — REPO EXHAUSTED` with different destinations (`A-source/A3-idea-gate.md:385-412`), but the router matches either as generic `NO SURVIVOR` and routes to A2, while A3's own handoff template also always says A2 (`00-ROUTER.md:24-32`; `A-source/A3-idea-gate.md:468-482`). **Fix:** make the router parse the two exact exit values and make the handoff's `NEXT` agree.
4. **Probe chronology is asserted, not durably proved.** The linter checks that fields exist but records neither input hashes nor a pre-execution receipt (`tools/probe-lint.py:69-80,121-141`); after the card and receipt were edited, only the predecessor review preserved the claim that direction predated outputs (`review/01-A3-review.md:23-25`). **Fix:** write an immutable pre-probe manifest containing card/prompt hashes, declared direction, UTC time, and lint exit before any model call.

### Degrading

5. **The A3 checklist does not encode the stronger GATE-4 proof.** The prose requires base, negative-control, and positive-control validation (`A-source/A3-idea-gate.md:220-240`), but checklist item 7 asks only for five graded implementations and n/5 (`A-source/A3-idea-gate.md:451-460`). **Fix:** put all three control receipts and the direct-observation verdict in checklist item 7.
6. **The mandatory kill ledger is absent from the checklist and handoff schema.** A3 requires `<run>/kill-ledger.md` (`A-source/A3-idea-gate.md:414-419`), but neither checklist item 13 nor `ARTIFACTS` names it explicitly (`A-source/A3-idea-gate.md:463-473`). **Fix:** add a dedicated checklist line and handoff field for the ledger.
7. **GATE 3's merged-history kill is overbroad.** “Any merged public PR touching the surface” also catches ordinary maintenance, although this run's `6169cce` does publish the relevant buffer-to-pipe direction (`A-source/A3-idea-gate.md:183-194`; `friction.md:148-167`). **Fix:** require the diff or discussion to disclose the candidate's remedy, direction, or invariant on that path.
8. **`probe-lint.py` measures lexical overlap, not semantic clause coverage.** It warns on the deliberately rephrased B prompt despite all four clauses being present (`tools/probe-lint.py:82-108`; `probes/c1-step2-B.txt:7-21`; `artifacts/probe-lint.txt:1-4`). **Fix:** lint explicit clause IDs or a structured constraint manifest instead of content-word overlap.
9. **Conformance checking is structural but not semantic.** The checker verifies headers, handoffs, links, ownership phrases, duplicate sentences, status markers, and router references, but not exit-value routing or prose-to-checklist agreement (`check-playbook.py:41-159`); those are exactly the contradictions in defects 3, 5, and 6. **Fix:** add machine-readable act metadata and validate router destinations, exit enums, checklist obligations, and handoff fields against it.
10. **The precedence ledger is empty.** Its own discipline requires live and superseded rules with run anchors, but both tables contain no entries (`ledger/RULES.md:16-37`). **Fix:** populate it from the current `STATUS` rules and make an empty live-rule table fail conformance.

The run-start A2→A3 producer/consumer gap was blocking but is now repaired: `e744c14` required A3's three direction fields without placing them in A2's card schema (`e744c14:A-source/A2-idea-generate.md:124-140`; `e744c14:A-source/A3-idea-gate.md:245-255`), whereas current A2 now owns them explicitly (`A-source/A2-idea-generate.md:158-177`). The original `--outputs` parser defect was likewise repaired in current code (`tools/probe-lint.py:46-65`), but both repairs landed after this run's measurement and reinforce defect 1 (`.git/logs/HEAD:2-4`).

## What a human still has to do

1. Keep C1 retired and do not send it to B1; its desired distinction is not observable at the available public boundary (`artifacts/kill-audit-codex.md:11-15`; `handoffs/01-A3.md:379-386`).
2. Decide whether to pursue one of the thirteen parked single-turn frostdb surfaces or move to the next A1 repo; no multi-turn survivor remains here (`handoffs/01-A3.md:412-426`).
3. Pin the next run to a playbook SHA and repair the current router/A3 terminal mismatch before relying on unattended continuation (`.git/logs/HEAD:2-4`; `00-ROUTER.md:24-32`; `A-source/A3-idea-gate.md:395-412`).
4. Require the authorized A2 owner to create future direction fields, and keep Claude/Codex from turning probe scaffolding into reusable instruction prose (`A-source/A2-idea-generate.md:158-177`; `00-ROUTER.md:168-180`).
5. For the next candidate, independently validate the strongest constraint-satisfying wrong shape before accepting a GATE-4 assertion (`A-source/A3-idea-gate.md:220-244`; `review/01-A3-review.md:14-19`).
6. Once a genuine survivor exists, execute B1 through B5 and then C1 through done; none of those acceptance surfaces was exercised here (`00-ROUTER.md:55-68`; `DONE:3,25`).

## Verdict

**Neither.** This was a reviewer-dependent A3 re-adjudication that reached the right candidate disposition, not a complete autonomous task-authoring loop and not an end-to-end supervised submission (`handoffs/01-A3.md:403-428`; `DONE:3,25`).

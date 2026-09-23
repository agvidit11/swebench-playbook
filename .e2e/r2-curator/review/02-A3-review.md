# Review 02 — A3 idea gate

## Verdict: FAIL

The professional conclusion may be right—neither candidate is ready to build—but A3 did not establish its declared exit with the evidence its own gate requires. The handoff says both cards were killed “on MEASUREMENT” (`handoffs/02-A3.md:3-7`), while explicitly waiving the primary outcome-variance measurement as “subsumed” by Gate 5 (`handoffs/02-A3.md:31`). That is the exact shortcut A3 forbids: Gate 4 is “not optional and it is not the same as GATE 5,” and a Gate-5-only kill is allowed only after Gate 4 A3-LOCAL ran and was inconclusive (`A-source/A3-idea-gate.md:179-199`).

## Checklist audit

- **#7 fails, and its waiver is invalid.** No five implementations were generated and no throwaway assertion was run against them (`handoffs/02-A3.md:31`, `handoffs/02-A3.md:81-83`). Gate 5 records approach choices; it cannot prove that five implementations would pass the behavioural grader “by construction.” A3 requires actual implementations and an observed `n/5` (`A-source/A3-idea-gate.md:181-193`).
- **#8 fails despite being ticked.** The handoff labels the line “×2 phrasings” and ticks it (`handoffs/02-A3.md:32`), but the C2 artifact says only one phrasing was run (`artifacts/probe-results.md:119-124`). A3 requires two phrasings (`A-source/A3-idea-gate.md:286-288`). C1's purported second phrasing also withholds R-b (`artifacts/probe-results.md:53-61`), although the rule requires probing the constraint-stating step *with the constraint stated* (`A-source/A3-idea-gate.md:286-288`).
- **The mandatory pre-probe lint fails.** Running the prescribed command against C1's card and its two prompts returns exit 1: the card has no literal `CONSTRAINT:`, `DESIRED:`, or `NON-DESIRED:` declarations. Those declarations and a passing lint are mandatory before a Gate-5 probe counts (`A-source/A3-idea-gate.md:241-255`; `tools/probe-lint.py:19-25`). The handoff neither reports the lint failure nor waives it.
- **#2 fails despite being ticked for both cards.** Gate 0 requires the exact assertion in code and a per-token grep classification (`A-source/A3-idea-gate.md:34-39`). C1 supplies an interface inventory but no written-out assertion or preserved grep output (`artifacts/cards.md:173-188`); C2 is expressly a partial, unpromoted card with no Interface Contract at all (`artifacts/cards.md:294-297`). The handoff nevertheless claims both passed (`handoffs/02-A3.md:26`).
- **#5 is not a valid all-card tick.** The handoff admits C2's premise was not executed (`handoffs/02-A3.md:29`, `handoffs/02-A3.md:83`), although Gate 2 precedes Gate 5 and requires an executed reproduction at base (`A-source/A3-idea-gate.md:104-114`). A later Gate-5 result cannot waive an earlier ordered gate.
- **#6 lacks the required evidence for C2.** The handoff gives two C2-ish identifier counts but no preserved query output and no 4–6-query sweep (`handoffs/02-A3.md:30`). A3 requires 4–6 searches per premise, each recorded with `total_count`, plus comment output for touched issues (`A-source/A3-idea-gate.md:146-159`). `open-issues.txt` is only a 121-row title list, not that evidence (`handoffs/02-A3.md:14`).

These are falsely ticked lines, so the review rule makes the act a FAIL rather than “pass with defects.”

## Evidence quality

The Gate-5 counts themselves are real but narrower than claimed. C1 has ten raw approach outputs: the constraint-stated prompt yields 5/5 endpoint keys (`artifacts/probe-results.md:26-49`), while the symptom-only prompt yields 5/5 id-only keys (`artifacts/probe-results.md:53-66`). C2 has five raw approach outputs and all five discuss always forwarding at close (`artifacts/probe-results.md:130-145`). Those are measured model priors, not the required Gate-4 implementation outcomes.

The handoff overstates the artifact as “15 probe outputs, both phrasings” (`handoffs/02-A3.md:9`): “both phrasings” is true only for C1, and C1's second prompt changes the contract by withholding R-b (`/tmp/curator-run/probe-A2.txt:19-22`). C2's prompt itself tells the model to discuss `closeCircuit()` and the equal-opening/closing-state case (`/tmp/curator-run/probe-C2.txt:20-24`), so unanimous diagnosis is unsurprising.

C1's base reproduction is genuine: its saved output shows metadata changes readmit a marked-down instance while a distinct endpoint remains unaffected (`artifacts/cards.md:112-135`). C2 has no corresponding premise reproduction (`handoffs/02-A3.md:29`).

C2 also appears hollow on direct inspection. An opening disconnected state is forwarded immediately (`/tmp/curator-run/curator/curator-framework/src/main/java/org/apache/curator/framework/state/CircuitBreakingConnectionStateListener.java:139-150`). If the last swallowed state is connected, `checkCloseCircuit()` closes and `closeCircuit()` forwards it because it differs from the disconnected opening state (`/tmp/curator-run/curator/curator-framework/src/main/java/org/apache/curator/framework/state/CircuitBreakingConnectionStateListener.java:164-191`), which the shipped reconnect test observes (`/tmp/curator-run/curator/curator-framework/src/test/java/org/apache/curator/framework/state/TestCircuitBreakingConnectionStateListener.java:121-129`). If the last state equals the initial disconnected state, forwarding that duplicate does not make a currently connected client appear connected. The proposed “always forward” edit therefore does not establish C2's promised invariant; this is precisely why Gate 2 required execution.

## Boundary and provenance

No `instruction.md` or step instruction exists, and the handoff assigns any future contract prose to Avocado/Vidit (`handoffs/02-A3.md:84-85`), so I found no iron-clad instruction-ownership leak.

A3 did cross its own input boundary for C2. A2 says C2 is “not promoted, not probed,” has partial fields, and is not offered as a survivor (`artifacts/cards.md:294-297`); A3 may measure candidate cards but may not generate or repair replacements (`A-source/A3-idea-gate.md:6-10`). It should have rejected the malformed input or sent it back to A2, not promoted it into a Gate-5 kill (`artifacts/probe-results.md:119-147`).

## Director's call

The engineer did genuinely explore the Round-2 space: C1 combines a reproduced failure under record mutation with two conflicting identity requirements (`artifacts/cards.md:112-148`). This is not another `expose_interface` card; its tested vocabulary is existing API (`artifacts/cards.md:173-188`).

I still would not green-light C1. The constraint-stated approach probe is 5/5 on the desired endpoint-key design (`artifacts/probe-results.md:26-49`), and the handoff itself concedes the claimed P6 cascade fails the parallel-API test (`handoffs/02-A3.md:34`). That is strong evidence of an easy, non-cascading task, but it is not a substitute for Gate 4. C2 is weaker: it began as a partial fallback (`artifacts/cards.md:294-297`), its prompt nearly names the code edit (`/tmp/curator-run/probe-C2.txt:20-24`), and its premise was never executed (`handoffs/02-A3.md:29`).

Thus “do not build either yet” is sound; “both cards killed by conforming measurement” is not.

## Playbook defects vs executor defects

**Playbook defect:** A2's mandatory card schema does not require the exact `CONSTRAINT:`, `DESIRED:`, and `NON-DESIRED:` fields (`A-source/A2-idea-generate.md:124-140`), while A3 makes those exact fields mandatory and its linter rejects their absence (`A-source/A3-idea-gate.md:241-255`; `tools/probe-lint.py:19-25`). Fix: add the three literal fields to A2's card schema and checklist.

**Executor defects:** it overrode the explicit Gate-4 prohibition; counted one C2 phrasing as satisfying a two-phrasing tick; ran probes whose mandatory lint fails; claimed Gate 0 for an incomplete C2 card; ticked Gate 2 without executing C2; and promoted a partial A2 fallback inside a measure-only act (`handoffs/02-A3.md:26-33`, `artifacts/cards.md:294-297`).

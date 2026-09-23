# Review 01 — A2 idea generation

## Verdict: FAIL

The run explored the required Round-2 space and produced one substantive candidate, but the act did not meet its own ownership and exit contract. The handoff ticks the authorship line while naming Claude as the runner (`handoffs/01-A2.md:24`), whereas A2 assigns this act to MetaCode, allows Codex only for the wide survey, and says “Claude never generates ideas or surfaces” (`A-source/A2-idea-generate.md:5`). The resulting artifact is explicitly labelled “Runner: Claude” (`artifacts/cards.md:3`) and contains the re-cut, step decomposition, and candidate judgement (`artifacts/cards.md:67`, `artifacts/cards.md:137`, `artifacts/cards.md:150`), not merely orchestration.

The reported exit is also internally false. It says “2 cards written” (`handoffs/01-A2.md:3`), but C2 says it is partial, unpromoted, and unprobed (`artifacts/cards.md:294-297`) and lacks the mandatory Interface Contract and self-audit (`handoffs/01-A2.md:62-63`). A2 requires every card to carry the mandatory fields and self-audit (`A-source/A2-idea-generate.md:124-140`, `A-source/A2-idea-generate.md:281-282`). There is one complete card plus one fallback note, not two conforming cards.

## Checklist audit

- **#2 fails despite being ticked.** The evidence proves the wrong owner authored the candidate artifact (`handoffs/01-A2.md:24`; `artifacts/cards.md:3-6`) against A2’s owner boundary (`A-source/A2-idea-generate.md:5`). This alone triggers FAIL under the review rule for a falsely ticked line.
- **#4 passes.** The artifact derives 10–12 surfaces from 53,038 LOC and 13 modules (`artifacts/cards.md:8-9`), and the actual ask requests 10–12 (`/tmp/curator-run/survey.txt:6-9`).
- **#6 passes.** The actual ask names failure-atomicity and P6 (`/tmp/curator-run/survey.txt:11-15`), requires a concrete injected fault and invariant (`/tmp/curator-run/survey.txt:72-76`), requires a same-area tension (`/tmp/curator-run/survey.txt:78-81`), and demands two revert-and-redo surfaces (`/tmp/curator-run/survey.txt:97-106`).
- **#7 passes.** Both actual survey outputs contain 12 `## SURFACE` headings; their reported sizes are 55,030 and 36,937 bytes (`handoffs/01-A2.md:10-11`), comfortably above A2’s 600-byte failure floor (`A-source/A2-idea-generate.md:278`).
- **#8 passes.** The merge table accounts for both surveys’ surfaces and gives a disposition for each (`artifacts/cards.md:30-55`).
- **#10/#11 fail as represented in the exit count.** C1 has the required contract and audit (`artifacts/cards.md:173-192`, `artifacts/cards.md:257-290`); C2 expressly does not (`artifacts/cards.md:294-297`).
- **#5 is only partly auditable.** The handoff gives counts and citations (`handoffs/01-A2.md:27`), and an independent source scan reproduced 1 hit in `framework/state`, 0 in `x-discovery`, and 4 in `recipes/cache`; however, the required saved raw grep output is absent from `ARTIFACTS` (`handoffs/01-A2.md:8-13`) despite A2 requiring “output saved” (`A-source/A2-idea-generate.md:276`).

## Evidence quality

The strongest measurements are real. The cold build log reports `BUILD SUCCESS` and total time `01:08 min` (`/tmp/curator-run/build-cold.log:3995-3999`). The scratch reproduction really ran four tests and reports `Failures: 0` with 0.07 seconds of test execution (`/tmp/curator-run/repro1.log:68-78`). The issue dump is 121 lines, matching the handoff’s count (`handoffs/01-A2.md:12`).

One claim is premature: the A2 handoff says its argued rate has already been superseded by A3 measurement and points to `handoffs/02-A3.md` (`handoffs/01-A2.md:54-55`), but that handoff did not exist when A2 landed. A2 itself says its cards are claims and gates must not run here (`A-source/A2-idea-generate.md:10-12`). The card nevertheless embeds an A3 GATE-2 executed reproduction (`artifacts/cards.md:112-136`) and kills surfaces using A3 gates 2, 3, and 6 (`artifacts/cards.md:35-53`). This mixes act boundaries and makes the handoff temporally non-self-contained.

## Boundary and provenance

No instruction file exists in this run, and the artifact explicitly disclaims contract prose (`artifacts/cards.md:3-6`), so I found no iron-clad `instruction.md` leak in A2. The separate A2 ownership boundary was violated as described above. The scratch clone is also left modified—`.mvn/extensions.xml` deleted and `ZZRepro.java` untracked—while the artifact promises the repro is “deleted before any commit” (`artifacts/cards.md:114-115`); that future cleanup is not evidence at A2 exit.

## Director’s call

This is materially better ideation than Round 1. C1 is not `expose_interface`: all eight graded symbols are existing public API (`artifacts/cards.md:173-188`), and it combines an injected-fault premise with a real same-step conflict (`artifacts/cards.md:69-71`, `artifacts/cards.md:137-148`). Curator is worth this probe because the base defect was executed, not merely inferred (`artifacts/cards.md:112-135`).

I would **not green-light C1 yet**. Its own audit says the contract may directly imply the endpoint-key answer (`artifacts/cards.md:279-286`). More importantly, the claimed P6 “tear-out” is not established: the card says step 1’s key must be replaced because step 2 needs registration time (`artifacts/cards.md:163-168`), but a plausible implementation can retain the endpoint key and add incarnation metadata to its value. A3 must test that actual family, not only repeat the card’s proposed dichotomy.

The live five-answer step-1 probe already points toward saturation: each output independently identifies whole-object equality and proposes stable id/endpoint identity (`/tmp/curator-run/probeA1-1.out:13`, `/tmp/curator-run/probeA1-2.out:14`, `/tmp/curator-run/probeA1-3.out:12`, `/tmp/curator-run/probeA1-4.out:13`, `/tmp/curator-run/probeA1-5.out:14`). That is A3 evidence, not a defect in A2, but it makes the candidate’s trajectory weak.

## Playbook defects vs executor defects

**Playbook defect:** the router permits “repo chosen but no cards” to enter S1/A2 (`00-ROUTER.md:20-28`), while A2 requires a prior `HANDOFF A1` (`A-source/A2-idea-generate.md:6`, `A-source/A2-idea-generate.md:272`). The executor’s partial waiver (`handoffs/01-A2.md:23`) is a reasonable recovery from that contradiction. Fix: define an explicit imported-shortlist input schema for A2, including HEAD SHA and the A1 facts.

**Playbook defect:** A2’s prose says not to run gates (`A-source/A2-idea-generate.md:10-12`), but its merge workflow asks the same actor to apply auto-rejects (`A-source/A2-idea-generate.md:279-280`). Fix: distinguish A2-local auto-reject filters from A3 gates and prohibit A3-labelled claims before handoff.

**Executor defects:** Claude authored/re-cut the card despite the owner rule; a partial fallback was counted as a conforming card; the required admission-search output was not persisted; and A3 evidence was performed/claimed inside A2 before the A2 handoff (`handoffs/01-A2.md:24`, `handoffs/01-A2.md:3`, `handoffs/01-A2.md:27`, `artifacts/cards.md:112-136`).

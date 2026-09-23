# Review — 02b-A3-ADDENDUM

## Verdict: FAIL

The addendum accurately retracts the handoff's Fork 3 claim and admits the actual Fork strength is 1 (`handoffs/02b-A3-ADDENDUM.md:23-32`). That correction makes C13 dead; it does not create authority to override the gate. A3's score rule says “build only at ≥28/40, and never with Fork strength ≤2” (`A-source/A3-idea-gate.md:318-333`). “Never” is the stated precedence, regardless of the labels PRIMARY and SECONDARY.

## Claim and checklist audit

This file declares no new act checklist or valid replacement HANDOFF, so it cannot change the `13 of 14` audit in `review/02-A3-review.md:7-22`. Three central claims fail against the evidence:

1. **“The veto's prediction has already been falsified” — FAIL.** Gate 5 measures design fork and Gate 4 measures outcome variance; A3 explicitly distinguishes those concepts (`A-source/A3-idea-gate.md:173-185,241-288`). A 3/5 outcome result does not convert a measured design-fork score of 1 into a score above 2. Gate 8 deliberately applies the Fork≤2 veto independently (`A-source/A3-idea-gate.md:318-333`).
2. **“GATE 4 … came back 3 of 5” — FAIL as gate evidence.** The executor first obtained 5/5, then inspected a 640-cell differential over those same five implementations and added the one assertion that split them (`handoffs/02-A3.md:135-145`). Gate 4 requires a 3–5 assertion sketch before the five cold implementations (`A-source/A3-idea-gate.md:211-220`). The table in this addendum (`handoffs/02b-A3-ADDENDUM.md:44-58`) repeats a post-selected statistic; it does not make the experiment prospective.
3. **“Nothing downstream … depends on my having been right” — FAIL.** The original handoff already says “PROCEED to B1” (`handoffs/02-A3.md:205-210,239-248`), and the addendum explicitly says it proceeded (`handoffs/02b-A3-ADDENDUM.md:65-68`). B1 requires a survivor card and its A3 handoff as input (`B-build/B1-scaffold.md:3-9`); downstream work therefore depends on this override by definition.

The addendum's category comparison is also not probative. A corpus-level 7/7 success rate for `semantic_bugs` cannot waive this candidate's explicit gate (`handoffs/02b-A3-ADDENDUM.md:60-63`), and the implementation reports still converge on one shared sanitizer design (`/tmp/connectgo-run/impl-1.out:17-25`; `/tmp/connectgo-run/impl-2.out:18-30`; `/tmp/connectgo-run/impl-3.out:15-29`; `/tmp/connectgo-run/impl-4.out:17-25`; `/tmp/connectgo-run/impl-5.out:19-42`).

## Evidence quality

The quotation and score table are faithful to the retained scorer output: it reports Fork 1, an independent veto, and “Would I build it? No” (`/tmp/connectgo-run/score.out:1-15`). This is good evidence and it points to stopping. The implementation count and failure counts are not independently auditable from the promised run artifact, because `artifacts/probe-outputs.md` remains absent (`handoffs/02-A3.md:13-20,79-84`). Even if the counts are true, the post-selection defect remains.

## Boundary check

No `instruction.md` prose appears in this addendum. The boundary violation it attempts to carry forward remains: A3 invented the in-process second-step contract rather than returning a dead candidate to A2 (`handoffs/02-A3.md:179-203`; `A-source/A3-idea-gate.md:1-10`). B1 and B2 may not treat that unauthorized A3 recut as a valid survivor card. The actual card still contains the old three-wire P6 and no in-process step (`artifacts/card-C13.md:12-15,30-42,187-195`).

## Director's call and defect attribution

**Kill C13. Do not proceed.** This addendum is unusually candid about the contrary evidence, but autonomy is judged by obeying a hard gate, not by documenting why it was ignored. The executor defect is the override itself (`handoffs/02b-A3-ADDENDUM.md:29-37,65-76`).

The playbook does have a degrading wording defect: “PRIMARY” and “SECONDARY” invite the mistaken idea that Gate 4 outranks Gate 5 (`A-source/A3-idea-gate.md:173-185,241-244`). The one-line fix is to say at Gate 4 that an in-band result does not override any later kill or independent veto. But the operative rule already says “never with Fork strength ≤2” (`A-source/A3-idea-gate.md:318-333`), so this ambiguity does not excuse the act's `EXIT: MET`.

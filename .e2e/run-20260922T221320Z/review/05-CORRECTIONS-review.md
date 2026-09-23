# Review 05 — corrections after reviewer audit

## Verdict: FAIL

The correction record accepts the earlier findings and repairs the headline `HANDOFF` blocks, but it does not make the underlying records internally consistent. It says A1 was amended to `13 of 16` and A2 to `9 of 13` (`handoffs/05-CORRECTIONS.md:25-27,44-47`), while the detailed A1 and A2 checklist tables still label the disputed rows `DONE` and retain their old `16 of 16` / `13 of 13` headings (`handoffs/01-A1.md:348-370`; `handoffs/02-A2.md:287-305`). A corrective handoff whose own claimed amendments leave contradictory canonical evidence does not meet its stated purpose.

This file is also not a router-conforming act handoff: it declares no act owner, input, output, exit condition, checklist count, artifacts, facts, open items, or next act. The router requires the six-field block for every act handoff (`00-ROUTER.md:266-286`). If this is intentionally an audit amendment rather than an act, the playbook has no amendment protocol; that is itself a traceability defect.

## Checklist audit

`05-CORRECTIONS.md` declares no checklist, so there is no `n of m` claim to validate. I instead spot-checked four of its concrete amendment claims.

1. **A1 headline correction — supported.** The A1 handoff now says `EXIT: NOT MET` and `CHECKLIST: 13 of 16 ticked`, exactly as the correction record claims (`handoffs/01-A1.md:12-31`; `handoffs/05-CORRECTIONS.md:14-27`).
2. **A1 detailed correction — not supported.** The same A1 file still titles its detailed section `16 of 16 addressed`, marks line 14 `DONE for lego`, and only afterward supplies a contradictory “CORRECTED TALLY” (`handoffs/01-A1.md:348-370`). The amendment did not remove the unsupported tick.
3. **A2 headline correction — supported.** The A2 handoff now says `EXIT: NOT MET` and `CHECKLIST: 9 of 13 ticked`, with lines 3, 9, 10 and 11 named as failures (`handoffs/02-A2.md:12-26`; `handoffs/05-CORRECTIONS.md:44-83`).
4. **A2 detailed correction — not supported.** The same A2 file still titles its checklist `13 of 13`, marks all four disputed lines `DONE`, and says `Waived: 0` (`handoffs/02-A2.md:287-305`). Its surface table also still totals 17 while claiming all 18 are accounted for: 3 card-1 + 2 card-2 + 3 parked + 9 dropped (`handoffs/02-A2.md:174-183`). The correction accurately identifies `ch1` as the eighteenth, dropped-late item (`handoffs/05-CORRECTIONS.md:85-89`), but that disposition was not reconciled into the canonical table or its `n` column.

## Evidence quality

The strongest correction claims are grounded and candid. The A1 durable copies exist, and each is byte-identical to its cited `/tmp` source; the correction names their durable paths (`handoffs/05-CORRECTIONS.md:35-40`). The accepted Card 2 findings also quote concrete source ranges and explain why the two steps are independent and why the first observable is not externally reachable (`handoffs/05-CORRECTIONS.md:91-107`). Those findings reinforce the no-survivor result.

Evidence preservation is nevertheless weak because prior handoffs were edited in place after their reviews. The correction explicitly says it amended both records (`handoffs/05-CORRECTIONS.md:25-27,44-47`), but the router defines only emission of a handoff, not versioning or post-review mutation (`00-ROUTER.md:273-286`). Line-cited reviews can therefore point at content that no longer represents what they reviewed.

## Boundary and ownership

The correction stayed within run bookkeeping and copied shortlist artifacts into the run. No task directory or protected instruction file exists; the run stopped before B1 (`CHECKPOINT.md:12-17`). I found no direct or indirect `instruction.md` write.

The boundary defect is procedural: `05-CORRECTIONS.md` is presented as a handoff but corresponds to no declared act, and it mutates earlier evidence instead of appending a complete, authoritative replacement. The playbook does not assign an owner or output schema for reviewer-driven corrections (`00-ROUTER.md:266-286`).

## Director's call

The substantive decision remains correct: do not build any of the four candidates. The correction adds two independent reasons Card 2 was already dead before its A3 history kill (`handoffs/05-CORRECTIONS.md:91-107`), while the final checkpoint records four candidates and four kills (`CHECKPOINT.md:29-36`). The correction improves honesty but does not rehabilitate A1, either A2 round, or A3's unsupported checklist claims.

## Defect attribution

Executor defects:

- Amended only the summary blocks and left contradictory detailed checklists in both canonical handoffs (`handoffs/01-A1.md:348-374`; `handoffs/02-A2.md:287-305`).
- Claimed A2's final 18-surface accounting was corrected without updating the table whose numeric rows still total 17 (`handoffs/02-A2.md:174-183`; `handoffs/05-CORRECTIONS.md:85-89`).
- Used a non-standard handoff with none of the router's mandatory fields (`handoffs/05-CORRECTIONS.md:1-10`; `00-ROUTER.md:273-286`).

Playbook defects:

- The router has no append-only correction/amendment protocol, so post-review edits can invalidate line-cited evidence without producing a new authoritative version (`00-ROUTER.md:266-286`; `handoffs/05-CORRECTIONS.md:25-27,44-47`). Fix: forbid in-place handoff edits after review and require a versioned amendment that supersedes named fields while preserving the original.
- The handoff contract is not machine-enforced. The playbook checker validates act-file templates, links and ownership prose, but does not validate run handoffs or checklist arithmetic (`check-playbook.py:41-59,154-172`). Fix: add run-handoff schema validation, including allowed exit states and consistency between the summary count and detailed rows.

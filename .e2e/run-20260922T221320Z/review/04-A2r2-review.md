# Review 04 — A2 idea generate, round 2

## Verdict: FAIL

This retrospective handoff does not meet A2's exit. A2 requires actual candidate cards, each axis-composed and carrying the full self-audit (`A-source/A2-idea-generate.md:5-10,244-263`). The handoff instead says the “cards” were deliberately abbreviated and waives the self-audit, while declaring `EXIT: MET` (`handoffs/04-A2r2.md:18-30,97-112`). An exit requirement cannot be waived, and a ticked “one card per survivor” line with no card artifact is a hard failure.

## Checklist audit

The handoff reports all 13 lines accounted, with five inherited and one waived (`handoffs/04-A2r2.md:23-24,97-112`). I checked six lines.

1. **Lines 1–5 — not safely inheritable as a block.** The repo, base SHA, lens and admissions are unchanged, so lines 1–3 and 5 can reasonably reuse round-1 evidence. But line 4's surface accounting was already incomplete: the final round-1 disposition totals 17, with `ch1` lost between the merge table and cards (`review/02-A2-review.md:11-17`). Calling all five inherited without addressing that known defect carries bad state into the new act.
2. **Line 6 — supported.** The 5 KB brief exists durably at `artifacts/A3/p-remerge.txt`, and the MetaCode output describes the requested function-history work (`handoffs/04-A2r2.md:35-52`; `artifacts/A3/remerge.out:14-47`). Filing an A2 input under A3 is confusing but does not erase the evidence.
3. **Line 7 — supported only as dispatch completion.** `remerge.out` contains the literal `## CASCADES` section and two proposed cascades (`artifacts/A3/remerge.out:49-53`). This shows the survey returned content; it does not validate that content.
4. **Line 9 — false.** The handoff records only C3's rejection for coined exported names (`handoffs/04-A2r2.md:105-106`). It does not apply the auto-rejects to the two candidates it calls survivors. Cascade 3 is the exact decorative “step 2 = now use what you built in step 1” shape: at HEAD, `RevokeWithReason` can parse its bundle, select the non-CA certificate and validate the reason without `GetOCSP` or its proposed helper (`artifacts/A3/remerge.out:51`; `/tmp/e2e-lane-GO/lego/certificate/certificates.go:511-528`; `A-source/A2-idea-generate.md:182-186`).
5. **Line 10 — false.** A2 requires one numbered card per survivor with every §4 field (`A-source/A2-idea-generate.md:281-282`). The handoff admits that it produced only “220-word cascade sketches, not full §4 cards,” and lists no card paths (`handoffs/04-A2r2.md:25-27,107`). Calling this `DONE (abbreviated)` is an unsupported tick, not a permitted alternate form.
6. **Line 11 — invalid waiver.** The self-audit is part of A2's explicit exit, not optional work (`A-source/A2-idea-generate.md:5-8,244-263`). A named biggest risk is only one requirement inside that audit; it does not replace the 13 card-stage rubric rows and four deferred items (`handoffs/04-A2r2.md:107-108`). Therefore `EXIT: MET` is false even if the waiver is stated.

The handoff was also emitted after A3 round 2 had already completed: it calls itself a supplementary record for an act that ran “between” the two halves of the preceding handoff (`handoffs/04-A2r2.md:1-7`). The router says no act begins without the prior handoff and that every act emits its handoff before routing onward (`00-ROUTER.md:241-261`). Retroactive documentation cannot provide A3 with a validated input at the time A3 ran.

## Evidence quality

The source-history evidence is useful and appears genuine. The output records histories for six functions and shows the linter commit's inverted `errors.Is` predicate (`handoffs/04-A2r2.md:76-93`; `artifacts/A3/remerge.out:14-47`). The existing reason constants are also real, and the quoted base functions exist (`handoffs/04-A2r2.md:79-83`).

What is missing is more important: there are no full cards, no per-card interface-contract tables, no predicted per-arm rates, no proper self-audits, and no complete final surface merge table. Those are the evidence A2's handoff contract requires (`A-source/A2-idea-generate.md:286-298`). The two cascade descriptions are proposals, not measured task-quality evidence.

## Boundary and ownership

MetaCode produced `remerge.out`, consistent with A2 ownership (`artifacts/A3/remerge.out:1-13`; `A-source/A2-idea-generate.md:5-7`). No `instruction.md` or `steps/*/instruction.md` exists in the run, and I found no direct or indirect protected-file write. The problem is act sequencing and missing artifacts, not instruction authorship.

A2's output belongs in A2 cards and an A2 handoff before A3 starts. Here the input brief and output are filed under `artifacts/A3`, and the handoff was written after `03-A3.md` (`handoffs/04-A2r2.md:1-7,25-27`). That crosses the declared act boundary and makes the claimed A2→A3 chain non-auditable in real time.

## Director's call

I would not green-light either round-2 proposal.

- Cascade 3 is not a cascade: its revocation half is independently implementable at HEAD, and joining the two fixes through a new private helper manufactures code reuse rather than a requirement dependency (`artifacts/A3/remerge.out:51`; `/tmp/e2e-lane-GO/lego/certificate/certificates.go:511-528`). It should have failed A2's auto-reject before reaching A3.
- Cascade 4 is substantively plausible and has a real dependency, but the exact SNI-map/shared-listener/keyed-cleanup design was produced by all five probes (`handoffs/03-A3.md:204-217`). With no implementation-based outcome measurement, there is no basis to believe it would land in band (`handoffs/03-A3.md:221-240`).

## Defect attribution

Executor defects:

- Declared A2's exit met while explicitly omitting the required full cards and self-audits (`handoffs/04-A2r2.md:18-30,97-112`; `A-source/A2-idea-generate.md:5-8`).
- Marked checklist line 9 done without applying the build-then-use auto-reject to cascade 3 (`handoffs/04-A2r2.md:58-65,105-106`; `A-source/A2-idea-generate.md:182-186`).
- Emitted the A2 handoff retroactively after the downstream A3 handoff, contrary to the router's handoff ordering (`handoffs/04-A2r2.md:1-7`; `00-ROUTER.md:248-261`).
- Inherited round-1 surface accounting despite the already-documented missing surface (`handoffs/04-A2r2.md:101-102`; `review/02-A2-review.md:14`).

Playbook defects:

- A3 sends dead candidates “back to A2” but neither act defines a re-entry protocol: which A2 checks may be inherited, whether new full cards are mandatory, or how handoff numbering preserves temporal order (`A-source/A3-idea-gate.md:5-10,284-286`; `A-source/A2-idea-generate.md:265-298`). Fix: define a round-specific A2 re-entry checklist and require its handoff before A3 resumes.
- The loop has no termination rule for repo exhaustion (`friction.md:397-411`). Fix: bound A2↔A3 rounds and require a complete surface-disposition record before returning to A1.

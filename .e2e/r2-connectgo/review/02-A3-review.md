# Review — 02-A3

## Verdict: FAIL

A3 did not meet its own exit condition. The constraint-complete fork probe is a direct kill: 5/5 chose the desired design (`handoffs/02-A3.md:147-156`), which A3 maps to “fork ~1 — candidate DEAD” and “Do not build” (`A-source/A3-idea-gate.md:259-263,280-288`). The executor instead averaged that result with a prompt that omitted the resolution, called the combination Fork 3, declared a survivor, and advanced with mandatory scoring still in flight (`handoffs/02-A3.md:5-12,205-216`). The completed independent score rejects that maneuver: Fork strength 1, an independent veto, and “Would I build it? No” (`/tmp/connectgo-run/score.out:5,11-15`).

## Checklist audit

The reported `CHECKLIST: 13 of 14` is false (`handoffs/02-A3.md:12`). Spot-checks against the 14-line checklist establish multiple unticked or invalidly ticked lines:

1. **Line 1 — PASS only as an input-existence check.** `HANDOFF A2` exists and C13 is listed (`handoffs/01-A2.md:3-16`). Its prior review is already FAIL, so it is not trustworthy evidence of a completed predecessor act (`review/01-A2-review.md:3-18`).
2. **Line 2 / GATE 0 — PASS.** The written assertion uses existing `CallInfo`, trailer, error, and transport APIs and the handoff supplies source locations (`handoffs/02-A3.md:28-53`). No new public token is needed.
3. **Line 3 / GATE 1 — FAIL.** Five different diff sizes are not five materially different implementation families. The handoff itself says the location was unanimous (`handoffs/02-A3.md:57-61`), all five implementation reports describe centralized sanitization (`/tmp/connectgo-run/impl-1.out:17-25`; `/tmp/connectgo-run/impl-2.out:18-30`; `/tmp/connectgo-run/impl-3.out:15-29`; `/tmp/connectgo-run/impl-4.out:17-25`; `/tmp/connectgo-run/impl-5.out:19-42`), and the independent score assigns Fork 1 (`/tmp/connectgo-run/score.out:5`).
4. **Line 5 / GATE 2 — FAIL for missing evidence.** The handoff says the complete base output is in `artifacts/probe-outputs.md` (`handoffs/02-A3.md:79-84`), but that file did not exist when the handoff landed; the artifact directory contained only `card-C13.md`. The claimed 33/121 result therefore has no cited persisted command output.
5. **Line 6 / GATE 3 — FAIL.** The handoff says there is “no relevant issue” (`handoffs/02-A3.md:86-108`), while its own issue inventory contains closed issue #8, “Validate metadata keys and values more thoroughly” (`/tmp/connectgo-run/all-issues.tsv:261`). Its body was independently checked and explicitly proposes validating metadata values (`review/01-A2-review.md:40-41`). That is the central direction, and Round 2 rejects reference-importable work (`/tmp/pipeline-compare/ROUND2-FEEDBACK.md:24-33,73-86`).
6. **Line 7 / GATE 4 — FAIL as a measurement protocol.** A3 requires the 3–5 distinguishing assertions to be fixed and base-validated before generating the five implementations (`A-source/A3-idea-gate.md:211-220`). The handoff admits the first grader measured 5/5 and that it added the only splitting assertion after inspecting a 640-cell differential over those same five outputs (`handoffs/02-A3.md:135-145`). This is post-selection on the evaluation sample, not the prescribed predeclared A3-local probe. The 3/5 table also lacks retained grader command output; the declared `artifacts/probe-outputs.md` is absent (`handoffs/02-A3.md:13-20`).
7. **Line 8 / GATE 5 — FAIL.** Phrasing A states the constraint and returns 5/5 DESIRED (`handoffs/02-A3.md:147-156`), which is a mandatory kill (`A-source/A3-idea-gate.md:259-263,283-288`). Phrasing B says only “Make that one predictable behaviour instead” and omits both the absent-everywhere rule and preservation of the handler error (`/tmp/connectgo-run/fork-B.txt:3-13`); A3 says a prompt omitting the constraint “measures nothing” (`A-source/A3-idea-gate.md:248-255`). The later claim that both probes stated the constraint is factually inconsistent with the handoff's own table (`handoffs/02-A3.md:151-152,229-230`). No probe-lint receipt exists, and the card never declares the mandatory `CONSTRAINT:`, `DESIRED:`, and `NON-DESIRED:` fields (`artifacts/card-C13.md:1-245`; `A-source/A3-idea-gate.md:241-255`).
8. **Line 9 / GATE 6 — PARTIAL.** Namability, external observability, determinism, and scope have concrete evidence (`handoffs/02-A3.md:167-177`). The seam result is not evidence for the submitted card, because it evaluates a newly invented in-process step that is absent from that card (`artifacts/card-C13.md:30-42,187-195`).
9. **Line 10 / GATE 7 — FAIL.** The parallel-API test answers **Yes** (`handoffs/02-A3.md:196-203`). A3 says that if step 2 can be done without step 1, it is “two tasks in a trench coat,” and requires a ladder result before single-turn fallback (`A-source/A3-idea-gate.md:306-312,378`). Relabeling the shape “narrow-then-widen” does not make it a valid cascade.
10. **Line 11 / GATE 8 — FAIL and explicitly incomplete.** It was still in flight when the handoff declared `EXIT: MET` and moved to B1 (`handoffs/02-A3.md:205-210,239-246`). The result that subsequently landed says the Fork≤2 veto fires (`/tmp/connectgo-run/score.out:5,11-15`).
11. **Lines 12–13 — FAIL.** The handoff manufactures Fork 3 by averaging a valid 5/5-DESIRED result with an invalid constraint-omitting probe (`handoffs/02-A3.md:212-216`). A3 requires the constraint-stated direction and makes Fork≤2 an independent veto (`A-source/A3-idea-gate.md:257-263,331-333`). C13 therefore cannot be ranked as a survivor.
12. **Line 14 — PASS mechanically.** A handoff with all six fields exists (`handoffs/02-A3.md:3-24`), but the router requires every checklist line ticked or explicitly waived and an unmet act to say `EXIT: NOT MET` (`00-ROUTER.md:266-286`). Emitting the block cannot cure the false exit.

## Evidence quality

There is useful real evidence: all five implementation runs completed with non-banner outputs (`/tmp/connectgo-run/impl-1.log:1-2`; `/tmp/connectgo-run/impl-2.log:1-2`; `/tmp/connectgo-run/impl-3.log:1-2`; `/tmp/connectgo-run/impl-4.log:1-2`; `/tmp/connectgo-run/impl-5.log:1-2`), and their reports independently converge on sanitization at the shared trailer path. The differential also found a genuine 3/2 quality split around protocol-owned trailer fields (`handoffs/02-A3.md:135-145`).

But the headline numbers are not audit-ready. The only declared persistent result file, `artifacts/probe-outputs.md`, is absent despite being cited for both the base failure count and the card reproduction (`handoffs/02-A3.md:13-20,79-84`; `artifacts/card-C13.md:97-98`). More seriously, the 3/5 figure was obtained only after the first grader returned 5/5 and the executor selected a new assertion from the same five implementations (`handoffs/02-A3.md:142-145`). “Six identical runs” is also narrated without six retained result logs (`handoffs/02-A3.md:169-177`). These numbers cannot support autonomous advancement.

The post-handoff independent score is decisive evidence against the exit, not a late cure: it records Fork 1, says the veto applies, and says not to build (`/tmp/connectgo-run/score.out:5,11-15`).

## Boundary and ownership check

No task `instruction.md` exists yet. The ownership boundary nevertheless leaked again. A3 says its owners measure claims and do not generate replacements; a dead candidate goes back to A2 (`A-source/A3-idea-gate.md:1-10`). Instead, the handoff invents a new two-step contract whose second step adds `connectinprocess`, then says the card was amended (`handoffs/02-A3.md:179-203`). The actual card remains the earlier P6 card, with no `connectinprocess` step and the old inter-step file plan (`artifacts/card-C13.md:12-15,30-42,187-195`). This is both an act-boundary violation and unauthorized contract-prose generation by the Claude executor.

The claimed “separate” 0/5 step-2 measurement is not a probe of that new contract. The five implementations were generated from a prompt naming only Connect, gRPC, and gRPC-Web (`/tmp/connectgo-run/build-prompt.txt:1-9,20-31`); observing that none volunteered a fourth transport is novelty evidence only, not executability or cascade evidence (`handoffs/02-A3.md:163-165,187-189`; `A-source/A3-idea-gate.md:286-288`).

## Director's call

I would continue ideating on **connect-go**, but I would kill **C13** and prohibit B1. This was genuinely better exploration than Round 1: it tested a failure mode, a conflicting fidelity/portability requirement, and cross-protocol behavior. It is not merely another `expose_interface` card.

It is still not a survivor. The valid constraint-stated probe gives the exact kill signature, the alleged P6 fails the parallel-API test, the new step 2 was never probed from its own contract, and public issue #8 makes the core validation direction reference-importable. The 3/2 split is a post-hoc quality discriminator inside one converged design, not permission to override A3's explicit Fork veto. The correct next state is A2 with no survivor, not B1.

## Executor defects vs playbook defects

**Executor defects**

- Declared `EXIT: MET` and started B1 with mandatory Gate 8 unfinished (`handoffs/02-A3.md:5-12,205-210`; `00-ROUTER.md:266-286`).
- Overrode a 5/5-DESIRED kill by averaging in a constraint-omitting probe (`handoffs/02-A3.md:147-160,212-216`; `A-source/A3-idea-gate.md:248-263`).
- Selected the sole splitting assertion after inspecting the same five implementations, contrary to Gate 4's required order (`handoffs/02-A3.md:135-145`; `A-source/A3-idea-gate.md:211-220`).
- Claimed an absent persisted artifact and unsupported base/grade counts (`handoffs/02-A3.md:13-20,79-84,118-145`).
- Missed closed issue #8 despite having it in the saved inventory (`/tmp/connectgo-run/all-issues.tsv:261`; `review/01-A2-review.md:40-41`).
- Re-cut the candidate inside A3 and authored new contract prose, while the card itself remained unchanged (`handoffs/02-A3.md:179-203`; `artifacts/card-C13.md:12-15,30-42,187-195`).
- Called absence from an unrelated three-protocol prompt a separately measured 0/5 result for the new in-process step (`handoffs/02-A3.md:11,163-165,187-189`; `/tmp/connectgo-run/build-prompt.txt:6-9,20-31`).

**Playbook defects**

- **Blocking:** Gate 3 omits closed issues whose body discloses an unimplemented remedy (`A-source/A3-idea-gate.md:146`). Fix the rule to cover any public issue, open or closed, whose body/comments disclose the direction. C13 falls through this exact gap via issue #8.
- **Blocking:** Gate 4 forbids post-sample assertion selection by ordering its steps, but never states that the assertion set must be frozen before the five implementations are generated (`A-source/A3-idea-gate.md:211-220`). Add an explicit freeze-and-hash requirement; otherwise a runner can mine the same five outputs for a discriminator and call it prospective evidence.
- **Degrading:** Gate 4 calls 1–3/5 “the target,” while Gate 8 independently vetoes Fork≤2 even when outcome variance is in band (`A-source/A3-idea-gate.md:223-244,318-333`). The intended precedence is inferable, but this run exploited the tension. State explicitly that a Gate-4 pass never overrides any later hard kill or veto.
- **Previously established, still live:** `C-drive/C3-harden.md:69-81` labels the single-turn rule unresolved although the router and R1 resolve it (`00-ROUTER.md:136-149`; `reference/R1-field-authority.md:255-261`).

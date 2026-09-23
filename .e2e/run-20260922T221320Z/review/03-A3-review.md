# Review 03 — A3 idea gate

## Verdict: FAIL

A3 reached an allowed substantive outcome—an evidenced **no survivor**—but its declared `11 of 14` checklist is not supported. In particular, checklist line 8 is marked done even though candidate 4 received only one phrasing, directly contrary to Gate 5's mandatory two-phrasing rule (`handoffs/03-A3.md:17-18,181-217,275-295`; `A-source/A3-idea-gate.md:182-202`). Checklist lines 5 and 6 are also marked done for an aggregate four-candidate run without the per-candidate executions and disclosure queries their proof columns require. Under the review rule, a tick without evidence makes this act fail.

## Checklist audit

I checked seven lines against the durable A3 artifacts, the pinned source, and the act's own required proof.

1. **Line 2, Gate 0 — substantially supported.** Independent source counts reproduce the three zero-hit coined names for Every-Key-Type and representative IN-BASE counts: `PEMBlock=3`, `GetOCSP=2`, `RevokeWithReason=5`, `CRLReasonKeyCompromise=1`, and `ProviderServer=29` (`handoffs/03-A3.md:49-77,171-179`). The proposed round-2 interfaces also use existing public entry points (`artifacts/A3/remerge.out:49-53`). The handoff does not paste the exact assertion code demanded by Gate 0 step 1, but the rejection of Card 1 on three assertion-pinned coined tokens is independently credible.
2. **Line 5, Gate 2 — unsupported as ticked.** The table says `DONE (card 2 / c1)` and the handoff gives one executed reproduction for the OCSP fallback (`handoffs/03-A3.md:87-100,283`). The checklist is explicitly “per candidate card, in order” and requires both a source path and executed reproduction (`A-source/A3-idea-gate.md:251-263`). No executed base reproduction is supplied for round-2 `RevokeWithReason` or `ProviderServer`; source inspection is not execution, and A3 itself says “Grep is not reproduction” (`A-source/A3-idea-gate.md:104-114`). Those candidates were subsequently run through Gate 5, so this is not a valid cheaper-gate waiver.
3. **Line 6, Gate 3 — unsupported as ticked.** Six query totals and the decisive history are supplied for round-1 Card 2 (`handoffs/03-A3.md:102-146`), and `remerge.out` contains useful function histories for the round-2 surfaces (`artifacts/A3/remerge.out:14-47`). But Gate 3 requires 4–6 disclosure queries **per candidate**, with totals and issue comments (`A-source/A3-idea-gate.md:116-141,262`). No such query set is shown for round-2 candidates 3 or 4, despite the checklist's unqualified `DONE` claim (`handoffs/03-A3.md:284`).
4. **Line 7, Gate 4 — honestly not run.** The executor does not mislabel the design prompts as implementation outcomes; it explicitly records that no cold implementation was built or graded (`handoffs/03-A3.md:221-240,285`). That candour is good evidence hygiene, but it leaves the act without any measured outcome variance. Gate 4 requires five cold implementations and actual assertions, not three-sentence plans (`A-source/A3-idea-gate.md:143-180,263`).
5. **Line 8, Gate 5 — false as a completed checklist line.** Candidate 3 has two five-response phrasings, and all ten archived outputs select leaf-by-content plus a reason allowlist (`artifacts/A3/probes/c1-A.txt:1-10`; `artifacts/A3/probes/c1-B.txt:1-6`; `handoffs/03-A3.md:187-202`). Candidate 4 has only `c2-A`; the artifact list itself names only four briefs, and the handoff admits only one candidate-4 phrasing (`handoffs/03-A3.md:19-21,187-193`). Gate 5 says “Probe TWICE with different phrasing” (`A-source/A3-idea-gate.md:200-202`), while the checklist proof invents an exception—“Second phrasing run on the candidate it decided”—that the act does not contain (`handoffs/03-A3.md:286`). This unsupported tick independently requires FAIL.
6. **Line 10, Gate 7 — only partial, and one claimed dependency is false.** Candidate 4 has a real dependency: keyed cleanup needs the registry created in step 1 (`artifacts/A3/remerge.out:53`). Candidate 3 does not. At base, `RevokeWithReason` already parses the complete PEM bundle and has each certificate's `IsCA` field; it can select the leaf and validate the reason without `GetOCSP`, an issuer fetch, or a new shared helper (`/tmp/e2e-lane-GO/lego/certificate/certificates.go:511-528`). The claim that step 2 “CANNOT compute” the revocation bytes without step 1's `(leaf, issuer)` artifact is therefore an engineered code-sharing dependency, not a requirement dependency (`artifacts/A3/remerge.out:51`; `A-source/A3-idea-gate.md:220-228`).
7. **Lines 13–14 — supported.** The handoff provides a one-line killing gate for all four candidates and routes away from B1 (`handoffs/03-A3.md:40-47,291-292`). `NO SURVIVOR` is a valid A3 exit form (`A-source/A3-idea-gate.md:5-10`).

The reported total is itself hard to reconcile: the table contains ten unqualified `DONE` rows, one `PARTIAL`, two waived/N/A rows, and one `NOT RUN`, yet calls that “11 ticked” (`handoffs/03-A3.md:275-295`). Counting a partial line as ticked does not make its missing evidence exist.

## Evidence quality

The strongest evidence is real. I reproduced the function history: commit `1d24006e` is titled `fix: preferred chain only match root name (#1334)` and replaces the all-certificates loop with the top-certificate check quoted in the handoff (`handoffs/03-A3.md:118-141`). The Gate-0 counts are also reproducible at base. Those two original-card kills are sound.

The round-2 numbers are measurements of **described approaches**, not of working outcomes. Every prompt says “Approach only, no code” (`artifacts/A3/probes/c1-A.txt:10`; `artifacts/A3/probes/c1-B.txt:5-6`; `artifacts/A3/probes/c2-A.txt:10`). The handoff correctly calls them Gate-5 design-divergence measurements and explicitly says outcome variance was not measured (`handoffs/03-A3.md:221-240`). One small accounting error remains: it reports `c1-S1` as 4/4 usable with one progress-only response, but all five archived outputs contain a final three-sentence design. This does not rescue the idea; it makes the convergence stronger.

## Boundary and ownership

No `instruction.md` or `steps/*/instruction.md` exists anywhere under this run, so I found no protected-file write and no direct or indirect instruction-file ownership leak. The candidate text in `remerge.out` was produced by MetaCode, an allowed A2 ideation owner (`artifacts/A3/remerge.out:1-13`; `A-source/A2-idea-generate.md:5-7`).

The act boundary still failed. A3 says it measures claims and “does not generate replacements”; dead candidates go back to A2 (`A-source/A3-idea-gate.md:5-10`). The executor says it went back to A2, but it emitted no second A2 handoff, no round-2 cards with A2's required fields/self-audit, and no A2 checklist. Instead, it folded MetaCode's two new candidates directly into the A3 handoff (`handoffs/03-A3.md:150-179`; `artifacts/A3/remerge.out:49-53`). This is not a protected-file authorship violation, but it bypasses the A2 exit and destroys the audit trail between acts.

## Director's call

I agree with **not building any of the four**.

- Every-Key-Type is recall-shaped and assertion-dependent on coined names (`handoffs/03-A3.md:49-77`).
- No-Silent-Fallback would reverse a deliberate merged change (`handoffs/03-A3.md:118-141`).
- Dead-responder/accountable-revocation is two independent fixes joined by a private helper: revocation can identify a leaf from its already-parsed bundle at HEAD, so the HEAD counterfactual disproves the cascade (`artifacts/A3/remerge.out:51`; `/tmp/e2e-lane-GO/lego/certificate/certificates.go:511-528`).
- One-port/many-challenges is a plausible real bug and a genuine cascade, but all five design probes returned essentially the complete SNI-map/shared-listener/keyed-cleanup design (`handoffs/03-A3.md:204-217`). Without Gate 4, there is no evidence it would land in the calibration band. I would not green-light it on speculation.

The repo remains worth mining, but this survey did not produce a buildable task. The correct next move is a clean A2 round with a different axis or a new A1 candidate, not B1 (`handoffs/03-A3.md:31-35,247-271`).

## Defect attribution

Executor defects:

- Marked Gate 5 complete after running only one phrasing for candidate 4 (`handoffs/03-A3.md:187-193,286`; `A-source/A3-idea-gate.md:200-202`).
- Marked Gates 2 and 3 complete without per-candidate executed reproductions and disclosure-query receipts for both round-2 candidates (`handoffs/03-A3.md:275-286`; `A-source/A3-idea-gate.md:251-264`).
- Claimed candidate 3 has a causal cascade although its second step is implementable against HEAD without step 1 (`artifacts/A3/remerge.out:51`; `/tmp/e2e-lane-GO/lego/certificate/certificates.go:511-528`).
- Re-entered idea generation without a distinct A2 handoff/checklist, despite A3 forbidding in-place replacement (`A-source/A3-idea-gate.md:5-10`; `handoffs/03-A3.md:150-179`).

Playbook defects:

- **Blocking:** Gate 4's required inputs do not exist until B2/B3/B4, although Gate 4 is A3's primary pre-build gate (`A-source/A3-idea-gate.md:143-180`; `friction.md:369-395`). Fix: move the gate after the contract/grader/build, or define an explicitly non-task probe contract and throwaway grader with legal ownership.
- **Blocking:** Gate 3 specifies file-level history, which would have hidden the merged decision that killed Card 2; it also omits the closed-issue-with-merged-remedy case (`A-source/A3-idea-gate.md:116-141`; `friction.md:297-354`). Fix: require function-scoped history and add that disclosure category.
- **Degrading:** A2↔A3 has no round limit or evidence threshold for declaring a repo exhausted (`A-source/A3-idea-gate.md:284-286`; `friction.md:397-411`). Fix: state a bounded number of rounds and the required disposition inventory.
- **Degrading:** The aggregate checklist format makes it easy to mark a gate done after testing only one of several candidates, even though it says “per candidate card” (`A-source/A3-idea-gate.md:251-270`; `handoffs/03-A3.md:275-295`). Fix: require a candidate-by-gate matrix rather than one status per gate.

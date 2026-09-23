# Review — 01-A2

## Verdict: FAIL

A2 did explore the Round-2 space: the brief explicitly requires failure injection, conflicting requirements, and P6 (`/tmp/connectgo-run/survey.txt:20-29,74-85`), and the two survey outputs contain 12 surfaces each. But the act did not meet its own contract. Its sole claimed card did not exist when the handoff was emitted, two card-dependent checklist lines were therefore ticked without evidence, the required A1 input was absent, A3 gates and probes ran inside/before the A2 handoff, and the Claude runner wrote exact contract prose despite declaring “contracts only, no prose.” These are hard autonomy failures, not taste calls.

## Checklist audit

The reported `CHECKLIST: 12 of 13` is false (`handoffs/01-A2.md:8`). The handoff says “line 3 partially waived,” while its own table marks line 1 partially waived (`handoffs/01-A2.md:23-25`). More importantly:

1. **Line 1 — FAIL.** The handoff admits that no `HANDOFF A1` exists and substitutes an external prose shortlist (`handoffs/01-A2.md:23`). A2 requires “one screened repo + its HANDOFF A1” (`A-source/A2-idea-generate.md:5-8`), and the router says no act begins without the prior handoff (`00-ROUTER.md:273-286`). This mandatory input is not waivable merely because most facts can be re-derived.
2. **Line 4 — PASS, with evidence.** The source shortlist reports 28,882 non-test LOC and the subsystem inventory (`/home/agvidit/swebench/runs/shortlist-proto.md:97-114`); the brief records the 10–12 band, six-subsystem cross-check, and asks for exactly 12 (`/tmp/connectgo-run/survey.txt:7-15`).
3. **Line 6 — PASS on document contents, FAIL on ownership.** The brief contains the lens and P6 shape (`/tmp/connectgo-run/survey.txt:20-29`), an unlensed-control allowance (`/tmp/connectgo-run/survey.txt:17-18`), the citation rule (`/tmp/connectgo-run/survey.txt:64-72`), the required failure/conflict/revert distribution (`/tmp/connectgo-run/survey.txt:74-85`), admissions (`/tmp/connectgo-run/survey.txt:99-112`), and containment (`/tmp/connectgo-run/survey.txt:134-138`). However, it also supplies six repo-specific candidate surfaces (`/tmp/connectgo-run/survey.txt:31-50`) even though the runner identifies itself as Claude (`handoffs/01-A2.md:24`) and A2 says “Claude never generates ideas or surfaces” (`A-source/A2-idea-generate.md:5`).
4. **Line 7 — PASS.** The recorded sizes match the files: 46,677 bytes and 33,494 bytes (`handoffs/01-A2.md:9-11`), and each output has exactly 12 `### S<n>` headings. The survey SHA prefix also matches the measured SHA-256 `cd24cd7c605b...` (`handoffs/01-A2.md:9`).
5. **Lines 8–9 — FAIL as act-boundary violations.** The handoff does contain a 24-row merge table and kill log (`handoffs/01-A2.md:37-76`), but it reports A3-style measurements and GATE-3 kills—e.g. a 36-cell probe (`handoffs/01-A2.md:43`) and probe 6 (`handoffs/01-A2.md:58`). A2 explicitly says every card is an unverified claim and “Do not run gates here” (`A-source/A2-idea-generate.md:10-12`). A3 also began before this handoff existed, contrary to `00-ROUTER.md:285-286`.
6. **Lines 10–11 — FAIL, no evidence.** At 2026-09-23T00:04:55Z, `find .e2e/r2-connectgo/artifacts -type f` returned no files and `.e2e/r2-connectgo/artifacts/card-C13.md` did not exist. Yet the handoff names that file (`handoffs/01-A2.md:13,32`) and claims its self-audit is present (`handoffs/01-A2.md:33`). A ticked line with no artifact is a failure.
7. **Line 12 — defective evidence.** “1 candidate card + 2 parked” (`handoffs/01-A2.md:5-7`) does not reconcile with the table, which identifies only X3 as parked (`handoffs/01-A2.md:57,75,89`). The public-disclosure subtotal is also labelled 9 but lists 10 surfaces (`handoffs/01-A2.md:70`).
8. **Line 13 — PASS.** The handoff exists and contains all six required fields (`handoffs/01-A2.md:3-16`). That does not cure the false completion claims.

## Evidence quality

The survey byte counts, SHA prefix, HEAD SHA, LOC, and 12+12 heading counts are grounded in actual files (`handoffs/01-A2.md:9-13,26,29`; `/tmp/connectgo-run/survey.txt:7-15`). The claimed 36/36 uniform probe has no retained output or listed artifact (`handoffs/01-A2.md:43`), so it is not independently auditable. The missing card makes every claim about C13’s fields and self-audit unevidenced. The count accounting is internally inconsistent as noted above.

## Boundary and ownership check

No `instruction.md` exists in the run yet. Nevertheless, the protected prose boundary has already leaked. The handoff identifies the runner as Claude and promises “contracts only, no prose” (`handoffs/01-A2.md:24`), but before the handoff it created `/tmp/connectgo-run/build-prompt.txt`, a ready-to-use solver contract with a “What must be true” section, three normative requirements, and constraints (`/tmp/connectgo-run/build-prompt.txt:4-39`). Its timestamp is 2026-09-22 16:59:50 -0700; the handoff timestamp is 17:03:28. This is exact contract prose from an unauthorized author, irrespective of whether it has yet been copied into `instruction.md`. A2’s boundary forbids Claude/Codex both from writing `instruction.md` and from supplying prose for someone else to paste (`A-source/A2-idea-generate.md:14-19`). The statement “Nothing in this handoff or the card is instruction text” (`handoffs/01-A2.md:90`) omits this material artifact.

The act also exceeded its declared output by executing A3 verification and launching five implementation samples plus two five-sample fork probes before emitting A2. That breaks the serial handoff protocol (`00-ROUTER.md:273-286`) and makes the live review checkpoint ineffective.

## Director's call

I would green-light **the repository for continued ideation**, but not this candidate yet. Connect-go has genuine shared-code protocol seams, and this run did what Round 1 failed to do: it explicitly searched failure injection and conflicting requirements rather than returning another `expose_interface` card (`/tmp/connectgo-run/survey.txt:20-29,74-85`). The C13 premise—preserve the handler’s primary error while enforcing cross-protocol trailer legality—has real tension and is externally observable through existing APIs (`handoffs/01-A2.md:61`).

I would not green-light C13 from A2 because the card and self-audit are absent, the candidate has already been shaped into detailed contract prose, and its intended “intersection all protocols can carry” behavior may collapse to a centralized filter. A3 must establish a real fork and outcome variance from completed samples, not infer them from the interesting bug.

### Post-handoff verification of C13

The card appeared at 2026-09-23T00:10:57Z, more than seven minutes after the handoff, so it does not retroactively make the handoff's completion claim true. It also contains two independent kill signals:

- The card itself records that **5 of 5** constraint-stated models chose the intended location and mechanism and calls the design fork “measured at 1” (`artifacts/card-C13.md:238-245`). A3 maps ≥4/5 DESIRED to “fork ~1 — candidate DEAD” (`A-source/A3-idea-gate.md:259-263`).
- The saved all-issues inventory contains closed issue **#8, “Validate metadata keys and values more thoroughly”** (`/tmp/connectgo-run/all-issues.tsv:261`). A direct `gh issue view 8 --repo connectrpc/connect-go --comments` at 2026-09-23T00:15Z returned: “HTTP and gRPC restrict the characters allowable in headers. We should extend `IsReservedHeader` to validate more thoroughly (and add a corresponding check for the header value).” That is the candidate's central validation direction, publicly proposed. It makes C13 reference-importable under the Round-2 standard, yet the A2 disclosure/kill pass claimed X7 survived (`handoffs/01-A2.md:61`) without examining this obvious title from its own issue inventory. A3's literal hard-kill list covers merged PRs, closed-unmerged PRs, and open issues (`A-source/A3-idea-gate.md:116-133`) but omits closed issues with unimplemented proposed remedies; that loophole is itself a blocking playbook defect.

## Executor defects vs playbook defects

**Executor defects**

- Began A2 without its required A1 handoff (`handoffs/01-A2.md:23`; `A-source/A2-idea-generate.md:6`; `00-ROUTER.md:285-286`).
- Emitted a 12/13 claim with the sole card missing and its self-audit unverifiable (`handoffs/01-A2.md:8,13,32-33`).
- Ran A3 gates/probes inside and before A2 completion (`handoffs/01-A2.md:43,58`; `A-source/A2-idea-generate.md:10-12`).
- Claude seeded concrete surfaces and wrote exact contract prose (`handoffs/01-A2.md:24`; `/tmp/connectgo-run/survey.txt:31-50`; `/tmp/connectgo-run/build-prompt.txt:4-39`).
- Reported irreconcilable counts (`handoffs/01-A2.md:5-7,57,70,75,89`).

**Playbook defects**

- A2 tells the runner to ask for 10–12 surfaces in this LOC band but describes an “honest” expected yield of 2–4 elsewhere; the handoff’s friction report correctly identifies the count semantics as easy to confuse. The immediate failure here is still executor-side: A2’s header says exit quality, not raw count (`A-source/A2-idea-generate.md:7-12`).
- A3's disclosure gate omits closed issues even when their body specifies the exact unimplemented remedy (`A-source/A3-idea-gate.md:116-133`). C13 demonstrates the consequence: issue #8 contains the central validation direction but falls through the literal enumeration. Add “any public issue, open or closed, whose body/comments disclose the direction.”
- `C-drive/C3-harden.md:69-81` still labels the single-turn calibration rule unresolved although the router and authority reference resolve it (`00-ROUTER.md:136-149`; `reference/R1-field-authority.md:255-261`). This is degrading, not causal here.

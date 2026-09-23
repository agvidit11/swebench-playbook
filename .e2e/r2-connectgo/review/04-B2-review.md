# Review — 04-B2

## Verdict: FAIL

B2's own exit requires `instruction-lint.py` clean or an allowed §6 override (`B-build/B2-contract.md:3-10`). The handoff instead reports `SKIP … no resolvable base_commit` and defers the gate to B3 (`handoffs/04-B2.md:3-7,52-56,106-111`). That is neither clean nor a §6 symbol override. The prescribed run independently reproduces the same `SKIP`, because B1 leaves all config `base_commit` values as placeholders until B3. B2 therefore cannot claim `EXIT: MET`.

## Checklist audit

The reported `13 of 14 ticked` is false or, at minimum, arithmetically misleading: line 11 is deferred and line 14 is inapplicable (`handoffs/04-B2.md:5-7`). Direct checks:

1. **Line 1 — FAIL against the actual card.** The handoff says the card and Interface Contract were read (`handoffs/04-B2.md:43`), but the authored step 2 is an in-process parity contract absent from `card-C13.md`, whose P6 describes two passes over the three HTTP wire protocols and never names `connectinprocess` (`artifacts/card-C13.md:12-15,30-42,187-195`). The new step came from Claude's A3 recut (`handoffs/02-A3.md:179-203`), not the survivor card B2 requires (`B-build/B2-contract.md:3-10`).
2. **Lines 2–3 — PASS with a boundary concern below.** The retained prompt is 10,617 bytes and the wrapper receipt is real: `mc.sh: exit=0 bytes=1221` (`handoffs/04-B2.md:44-45`; `/tmp/connectgo-run/contract.log:1-2`). The dispatch output is above the banner threshold and records the two writes (`/tmp/connectgo-run/contract.out:9-14`).
3. **Line 4 — PASS, but its evidence is numerically false.** Both instructions exist and contain substantive prose. Actual `wc -w` is **322** for step 1 and **281** for step 2, exactly as MetaCode's retained output reports (`/tmp/connectgo-run/contract.out:13-14`), not 272 and 250 as claimed twice in the handoff (`handoffs/04-B2.md:5-6,46,52`). Both remain below 350.
4. **Lines 5–8 — mostly PASS on the resulting prose.** Both steps state observable mismatches, use no repo identifier, path, heading, list, or code block, and do not prescribe one implementation location (`/home/agvidit/swe-bench-pro-agvidit/connect-go-trailing-metadata-parity/steps/1_wire_parity/instruction.md:1-3`; `/home/agvidit/swe-bench-pro-agvidit/connect-go-trailing-metadata-parity/steps/2_inprocess_parity/instruction.md:1-3`). Clause 2 is vacuous only if the future grader truly introduces no new exact symbol; B2 cannot yet verify that without the test patch.
5. **Line 9 — FAIL for its stated evidence.** Five differently-sized diffs do not show that two competent engineers chose different designs. The five implementation reports all use the shared trailer-sanitization design (`/tmp/connectgo-run/impl-1.out:17-25`; `/tmp/connectgo-run/impl-2.out:18-30`; `/tmp/connectgo-run/impl-3.out:15-29`; `/tmp/connectgo-run/impl-4.out:17-25`; `/tmp/connectgo-run/impl-5.out:19-42`). The two failures also did **not** “satisfy the prose”: leaving protocol-owned keys in the caller map violates the explicit no-extra-entry requirement (`handoffs/04-B2.md:51,98-100`; `handoffs/02b-A3-ADDENDUM.md:53-58`).
6. **Line 10 — PASS for mechanical form, with a counting defect.** Both files are two prose paragraphs, have no formatting markup, and are below 350 words. The handoff compresses multiple independently testable outcomes—status, message, sent messages, absence, byte preservation, repeated order, extra-key exclusion, wire non-regression, and no new public names—into “three requirements” (`handoffs/04-B2.md:52`). The 2–4 requirement limit is not objectively met merely by grouping them into sentences (`B-build/B2-contract.md:148-169,277-278`).
7. **Line 11 — FAIL.** The linter result is `SKIP`, not clean (`handoffs/04-B2.md:52-53`). §6 permits overrides only for a new symbol that the grader pins and A3 admitted (`B-build/B2-contract.md:203-216`); the handoff says there is no such symbol and anticipates no override (`handoffs/04-B2.md:106-111`).
8. **Line 12 — PASS on self-containment/order.** Step 1 has no forward reference; step 2 explains its own observable mismatch without referring to a prior instruction (`handoffs/04-B2.md:54`). This is a useful check, but it does not validate the unauthorized upstream recut.
9. **Line 13 — PASS.** B1 recorded both files at zero bytes, B1 handed off at 17:40:56, and MetaCode wrote them at 17:41:04 and 17:41:10. The retained MetaCode transcript confirms those writes (`handoffs/03-B1.md:23-25`; `/tmp/connectgo-run/contract.out:9-14`). No Claude/Codex write to either instruction path is evidenced.
10. **Line 14 — valid waiver.** This is a first write (`handoffs/04-B2.md:56`). It should be counted as waived, not as a tick.

## Evidence quality

The author, file sizes, prompt size, wrapper exit, and current prose are backed by retained artifacts. The reported word counts are not: the handoff says 272/250 while both `wc -w` and MetaCode's own output say 322/281 (`handoffs/04-B2.md:5-6,46,52`; `/tmp/connectgo-run/contract.out:13-14`). The boundary-test evidence is also misstated: implementations 4 and 5 failed a behavior the prose explicitly requires, not an unstated grader preference (`handoffs/04-B2.md:51,98-100`).

The lint skip exposes a blocking playbook sequencing defect rather than merely an executor inconvenience. `instruction-lint.py` reads the SHA only from `steps/*/tests/config.json` or top-level `tests/config.json`; it returns `SKIP` when none is 40-hex (`/home/agvidit/.claude/skills/swebench-mt/instruction-lint.py:31-42,92-110`). B1 deliberately leaves those Codex-owned configs as placeholders (`handoffs/03-B1.md:55-76`), yet B2 requires a clean lint before B3 (`B-build/B2-contract.md:3-10,203-216`).

## Boundary check

The final files were written by MetaCode, not Claude or Codex. That part of the iron-clad rule is satisfied.

There are two separate boundary problems. First, Claude supplied the substantive in-process contract that A3 invented instead of returning the dead card to A2 (`handoffs/02-A3.md:179-203`; `handoffs/04-B2.md:81-89`). Second, the brief gets uncomfortably close to indirect prose authorship: it supplies reusable wording formulas and directs that a particular word be said explicitly (`/tmp/connectgo-run/contract-brief.txt:35-52,107-124`). MetaCode did compose the final paragraphs, so I do not classify the files as third-party-authored; I do classify this as a defect in the claimed “rules and card only” boundary (`handoffs/04-B2.md:25-37,44`).

B3 was also dispatched before this B2 handoff existed: `/tmp/connectgo-run/b3-brief.md` is timestamped 17:47:15, while `handoffs/04-B2.md` is timestamped 17:49:02. The handoff admits it was “already dispatched” (`handoffs/04-B2.md:14`). This violates the router's serial handoff rule (`00-ROUTER.md:266-286`).

## Director's call and defect attribution

The prose is readable and unusually explicit about the observable contract. It is likely easy for exactly that reason, consistent with the valid 5/5 design probe. It should not proceed to B3 because C13 is dead and B2 did not meet its lint exit.

**Executor defects:** advanced from a non-survivor; claimed a skipped lint as a met exit; reported false word counts; treated one converged design with quality omissions as design divergence; began B3 before handoff (`handoffs/04-B2.md:3-14,43-56`).

**Playbook defects:** B2's exit is structurally impossible in the normal fresh-scaffold order because its linter requires the B3-owned config SHA (`B-build/B2-contract.md:3-10,203-216`; `/home/agvidit/.claude/skills/swebench-mt/instruction-lint.py:31-42,98-110`). One-line fix: make the B2 run explicitly name/read B1's pinned SHA, or formally define the pre-B3 name-leak run as provisional and reserve `PASS` for B3 line 20b. Also add the missing explicit MT rules—step 2 self-contained and step 1 with no forward reference—to B2 itself (`handoffs/04-B2.md:58-63`; `B-build/B2-contract.md:281-286`).

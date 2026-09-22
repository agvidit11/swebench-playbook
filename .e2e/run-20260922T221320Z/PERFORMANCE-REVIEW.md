# Performance review — run-20260922T221320Z

## Did the loop close?

No. At cutoff, one handoff existed, `DONE` was absent, and no durable artifact had been placed under the run's `artifacts/` directory (`review/monitor-receipt.md:3-5`). A1 explicitly failed its exit and nevertheless selected A2 as next (`handoffs/01-A1.md:12-16,42,367-377`). The first unattended stall was A1 G10: Docker was held by another session, leaving the required container receipts unavailable (`handoffs/01-A1.md:33-34,306-335`). Without a human/coordinator, the act either waits for that external resource or illegally weakens G10 to native timing.

The run was also supervised before reaching B: a coordinator changed `instruction-lint.py` in place after discovering that it disagreed with D1 (`friction.md:50-76`). That is direct evidence the published loop could not run against a frozen, self-consistent toolchain.

## Autonomy by phase

| Phase | Score | Evidence |
|---|---:|---|
| A-source | **1/5** | A1 did broad, evidence-rich screening, but did not satisfy G10/exit, produced an invalid checklist summary, and advanced anyway (`review/01-A1-review.md:3-18`). A2/A3 were not reviewed. |
| B-build | **0/5 — not demonstrated** | No B handoff or task artifact existed at cutoff (`review/monitor-receipt.md:3-5`). The coordinator had already needed to repair a B2 lint dependency (`friction.md:50-76`). |
| C-drive | **0/5 — not demonstrated** | No task was built or pushed, so no server verdict or C handoff existed (`review/monitor-receipt.md:3-5`). |

## Would the output be accepted?

No task output exists, so it cannot clear structure, oracle, calibration, or agentic review (`review/monitor-receipt.md:3-5`). The selected repository is worth surveying, but that is only an A1 result. If A2 begins immediately, the first process failure is upstream of structural validation: A1's prerequisite was not met (`handoffs/01-A1.md:12-16`; `00-ROUTER.md:215-216`).

## Playbook defects, ranked

### Blocking

1. **A1 parallelism contradicts its own shared-index and Docker work.** The router fans A1 out while declaring shared indexes and Docker serial-only (`00-ROUTER.md:158-175`); A1 makes the shared pull per-lane and G10 containerized (`A-source/A1-repo-screen.md:247-266`). Fix: split coordinator prework and serial G10 into explicit acts/stages.
2. **B2's external lint gate is unversioned and now disagrees with the checked-in description.** B2 says the script implements the pre-D1 rule (`B-build/B2-contract.md:203-216`), while the coordinator changed it mid-run and discovered it now needs post-B3 data (`friction.md:50-75`). Fix: version the tool with the playbook and add the post-B3 rerun to B3's checklist.
3. **The router does not enforce its own `EXIT: NOT MET` stop mechanically.** It states the rule (`00-ROUTER.md:215-216`), yet the executor could emit `PARTIAL` and proceed (`handoffs/01-A1.md:12-16,42`). Fix: add a handoff validator that rejects unknown exit states and blocks `NEXT` when exit is unmet.

### Degrading

1. **The conformance checker scans generated `.e2e` reports.** Its walker excludes only `.git` (`check-playbook.py:18-23`), and the live scan count changed as other runs wrote Markdown (`review/monitor-receipt.md:6`). Fix: restrict it to the router/act/reference/ledger source set or exclude `.e2e`.
2. **Corpus freshness is hard-coded.** A1 says 16 days while the receipt is 20 days and `git pull` cannot refresh the upstream (`A-source/A1-repo-screen.md:43-48`; `friction.md:17-30`). Fix: compute and report age; treat hits inside the stale window as unknown.
3. **Lane results lack a mandatory coordinator recheck.** The coordinator found two hits after the lane reported zero (`friction.md:78-100`). Fix: require coordinator reruns of G1/G2 for the selected repo.
4. **Artifacts are not durable by default.** A1 points to three `/tmp` shortlists while the run's `artifacts/` remains empty (`handoffs/01-A1.md:24-27`; `review/monitor-receipt.md:5`). Fix: copy final act evidence into the run artifact directory before handoff.

## What a human still has to do

1. Stop A2 until A1 is completed or explicitly re-scoped; the current handoff admits the exit miss (`handoffs/01-A1.md:12-16,42`).
2. Obtain serial container measurements for enough candidates to reach three valid survivors, or formally change G10; the queued commands are already recorded (`handoffs/01-A1.md:306-335`).
3. Decide whether lego's active-pool race is acceptable (`handoffs/01-A1.md:35-39`).
4. Freeze/version the playbook and its external scripts before resuming; the lint changed mid-run (`friction.md:50-76`).
5. Resolve the licence conflict only if a non-permissive candidate is revived; MIT lego does not bind it (`handoffs/01-A1.md:29-32`).

## Verdict

**Neither.** This was not a complete autonomous loop, and it did not reach a stable supervised build loop. It completed useful screening work, but stopped with A1's exit unmet, required coordinator intervention, and advanced contrary to the router (`handoffs/01-A1.md:12-16,42`; `friction.md:50-76`).

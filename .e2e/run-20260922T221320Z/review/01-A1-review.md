# Review 01 — A1 repo screen

## Verdict: FAIL

A1 did not meet its own exit. The handoff says only one repo passed its interpretation of every gate and labels the exit `PARTIAL` (`handoffs/01-A1.md:12-22`), while A1 requires at least three fully gated repos or an evidenced dead lane (`A-source/A1-repo-screen.md:5-8`). More strictly, lego's G10 was native, not the checklist's required throwaway-container run (`handoffs/01-A1.md:17-22`; `A-source/A1-repo-screen.md:266`), so zero repos have the prescribed G10 proof. The router requires `EXIT: NOT MET` and forbids improvising forward (`00-ROUTER.md:215-216`), but the handoff routes to A2 (`handoffs/01-A1.md:42,377`).

## Checklist audit

The headline `16 of 16 addressed` is not a valid `n of m ticked` report: it simultaneously records two waivers and one partial item (`handoffs/01-A1.md:23,339-361`). Line 14 is incomplete, and “addressed” is not the completion criterion in the router (`00-ROUTER.md:198-201`).

Independent spot-checks:

1. Checklist 1 is supported: `/tmp/llc` was at `d8472c4c54ec0dcf9f2a951f1ab77b840f1aa308`, dated 2026-09-02, matching the receipt (`handoffs/01-A1.md:68-76`).
2. Checklist 6/11 is supported: the clone was at `58468399a23fbdf4cb3a366e6d81925c1f97b4fe`; recomputation produced 111,352 non-test Go LOC and 262 subsystems, matching `handoffs/01-A1.md:132-137,348,353`.
3. Checklist 14's native measurement is real: I reran the claimed subset with `GOPROXY=off`; it passed in 11.28 seconds, consistent with `handoffs/01-A1.md:147-173`. It still does not satisfy the prescribed container proof (`A-source/A1-repo-screen.md:266`).
4. Checklist 15 is materially supported: the three `/tmp` shortlists exist and contain survivor/reject tables; the GO file alone has 103 lines and records three provisional survivors plus eight rejects (`/tmp/e2e-lane-GO/shortlist.md:12-90`). The durable run `artifacts/` directory is nevertheless empty (`review/monitor-receipt.md:4-7`).

## Evidence quality

The core lego measurements are genuine, not copied examples: the HEAD, license, size, module path, and offline test output were independently reproducible (`handoffs/01-A1.md:130-174`). The handoff also corrected a lane's false “0 direct” peer count by reading two real consumer-task hits (`handoffs/01-A1.md:188-208`), which is good evidence discipline.

The consolidation is internally inconsistent. It calls seven repos G10-deferred (`handoffs/01-A1.md:12-16,261-271`), but the OPEN list names five (`handoffs/01-A1.md:33-34`), and the checklist later distinguishes three deferred plus two not queued (`handoffs/01-A1.md:356`). Spire and smallstep have native timings but disappear from that accounting (`handoffs/01-A1.md:265-266`). These inconsistencies do not change the FAIL, but they make the survivor count non-auditable.

## Boundary and ownership

No evidence shows Claude, Codex, a script, or a patch writing any `instruction.md`; A1 did not produce contract prose. The act stayed on screening and run bookkeeping. Its shortlist artifacts live in ephemeral `/tmp` rather than the run's `artifacts/`, weakening restartability but not violating A1's declared output (`A-source/A1-repo-screen.md:7`; `handoffs/01-A1.md:24-27`).

## Director's call

I would green-light `go-acme/lego` for one A2 survey, not as a pre-approved task. It has a useful size, broad existing API, real fixtures, and a fast offline subset (`handoffs/01-A1.md:132-145`). The carried exclusions are substantive: HTTP-01 issuance, DNS propagation, order lifecycle, and account/TOS plumbing already have adjacent peer coverage (`handoffs/01-A1.md:241-259`). Its appearance in multiple active candidate pools is a real race risk (`handoffs/01-A1.md:35-39`). A2 must find a different invariant and A3 must re-prove novelty.

## Defect attribution

Executor defects:

- Advanced to A2 after an unmet exit and used `PARTIAL` instead of the mandated `NOT MET` (`handoffs/01-A1.md:12-16,42`; `00-ROUTER.md:215-216`).
- Reported `16 of 16 addressed` despite an explicitly partial G10 line (`handoffs/01-A1.md:23,356-361`).
- Counted a native run as G10 despite the checklist requiring a throwaway container (`handoffs/01-A1.md:17-22`; `A-source/A1-repo-screen.md:266`).

Playbook defects:

- A1 is fanned out in parallel while shared-index work is serial-only (`00-ROUTER.md:158-175`), yet checklist steps 1–2 are per lane (`A-source/A1-repo-screen.md:247-254`).
- A1's exit gate requires container work (`A-source/A1-repo-screen.md:195-208,266`) while the router makes all Docker work serial-only (`00-ROUTER.md:158-160`). The executor had to invent a split (`friction.md:32-42`).
- The corpus freshness claim is time-stamped prose, not a computed proof (`A-source/A1-repo-screen.md:43-48`); the actual corpus was 20 days stale (`friction.md:17-30`).
- A1 warns against pre-screens but does not explicitly require the coordinator to re-audit a lane's returned shortlist; doing so found two missed hits (`friction.md:78-100`).

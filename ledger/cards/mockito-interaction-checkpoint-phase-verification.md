# mockito-interaction-checkpoint-phase-verification

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `mockito/mockito` @ `116a4d6231dc35f90543060af41dcde00fe4e2ae`
- Seam: immutable interaction checkpoint -> since-checkpoint verification -> guarded selective cleanup
- Trap: shallow state across a masking boundary + natural order loses information
- Routing: `MEASURE`, three chained steps
- A4: `ADJACENT`; listener, timeout, deep-stub, and mock-copy peers excluded

## User problem and base evidence

I have a long test with shared setup calls and several phases. `clearInvocations()` deletes setup evidence another assertion still needs. Saving `getInvocations()` is not a reliable checkpoint either: later verification changes the held invocation objects. I need to freeze what mocks have seen, check only calls after that point—including order across mocks—and retire that phase only when every later call is accounted for, without touching older history.

At base, a held invocation changed `isVerified` from false to true after later verification; `clearInvocations()` reduced history from one entry to zero. The registered-invocation implementation copies the list but shares mutable invocation objects and clears the entire list.

## Steps

1. Add `Mockito.checkpoint(Object... mocks)` returning a public, read-only point-in-time artifact whose call order and ignored/verified/stub state do not change after later calls, verification, or clearing. Capture has no mock-side effects.
2. Use the checkpoint as authority for ordinary and in-order verification limited to later calls. Successful scoped verification marks only matched later calls; older calls remain visible to existing APIs.
3. Guarded multi-mock cleanup removes post-checkpoint calls only when every such call is verified/ignored. Any remaining call is reported and nothing is removed anywhere. Older calls always remain.

CONSTRAINT: immutable boundary, phase-scoped verification, then atomic selective retirement.

NON-DESIRED: shallow list copy; per-mock instead of global order; clear-all; deletion while scanning; one mock cleared before another fails.

Probe through chained real parent trees. Step 1 is the sole likely exemption. Require Step 2 and final Step 3 to retain independent difficulty; no single-turn fallback.

Full evidence: `/tmp/mockito-lane-i-20261005-qcfzsF/REPORT.md`.

Rating: P1 4, P2 2, P3 1, P4 2, P5 4, P6 2, P7 3 = **18/28 MEASURE**.

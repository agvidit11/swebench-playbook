# open62541-1 / open62541-2 — round 3 (allocation-failure discipline), PARKED

## Lever
The accepted open62541 task's step-2 discriminator was injected-allocation-failure discipline via a
link-time malloc/calloc/realloc/free interposer in the graded tests (fail the Nth allocation, count
live allocations). Both of our open62541 contracts already STATE "allocation failure returns
BADOUTOFMEMORY, output NULL/false, no partial object" — but no sketch had ever injected a failure.

## open62541-1 (filter normal form -> subsumes) — raw logs, 34 checks
Source: /tmp/pairb/g4/open62541-1/cold-{1..5}.v3-test.log (report never written, see blocker)

| impl | result | failure | class |
|---|---|---|---|
| cold-1, cold-4, cold-5 | 34/34 | — | — |
| cold-2 | 2 errors | SIGSEGV inside step-1 OOM sweep (stated: OOM -> BADOUTOFMEMORY) | R |
| cold-3 | 1 failure | step-2 leak at allocation ordinal 3 (leak-freedom NOT stated in words) | needs stating |

Fault injection confirmed ONE fair branch on a card that read 5/5 on 30 algorithm assertions.
Step 1 => 4/5, still over the ceiling. Not push-ready.
Also fixed in the desired seed during round 3: two OOM cleanup leaks (SimpleAttributeOperand copy,
clause append / intersection clone) — the oracle itself was wrong under fault injection.

## open62541-2 (binary shape -> accepts)
Codex died before grading any implementation.

## BLOCKER (tooling, not a card fact)
Both round-3 Codex sessions were terminated by OpenAI's filter:
"This content was flagged for possible cybersecurity risk" — almost certainly the libc
malloc/free interposer (`extern void *__libc_malloc` + overriding `malloc`). So the accepted task's
strongest discriminator cannot currently be built by Codex. Options for the coordinator: author
the interposer via Muse (1P) instead, use open62541's own allocator hooks (UA_mallocSingleton /
UA_EXPORT allocator pointers) if they exist at base rather than overriding libc symbols, or a
Trusted-Access Codex account.

## Next if resumed
1. Re-try the OOM sweep via open62541's own allocator indirection (no libc override) — may pass
   the filter.
2. State leak-freedom explicitly (it is a natural C ownership clause) and re-measure fresh.
3. Add a step-1 constraint of the control's kind (a stated constraint that fights the natural edit
   site) — e.g. existing encoder/decoder files must remain byte-identical — and measure.

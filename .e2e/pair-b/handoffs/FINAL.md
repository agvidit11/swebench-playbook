# PAIR B — FINAL HANDOFF (2026-10-02 ~07:50 UTC)

Shipped: **0**. Push-ready: **0**. Built: **1** (go-zero-goctl-api-contract-compatibility, single-turn,
handed to the main session for tuning at ~07:20 UTC with open B6 findings — see
/tmp/pairb/build-go-zero-goctl/avocado-reread.md).

## Funnel
5 repos -> 108 surfaces (A2 round 1: 86; concourse round 2: 22) -> 13 cards -> 1 KILL (same-seam
peer) + 3 DOWNGRADE + 3 AMEND + 6 MEASURE -> 6 cold-probed -> 1 built (DOWNGRADE to single-turn).

## Every card
| card | kind | evidence |
|---|---|---|
| open62541-2 binary shape -> accepts | MEASURE -> parked | r1 5/5,5/5 · r2 principle-level 5/5,4/5 · r3 OOM: Codex killed by cyber filter |
| open62541-1 filter NF -> subsumes | MEASURE -> parked | r1 5/5,5/5 · r3 OOM (raw logs): 1 fair branch (segfault under OOM), step1 4/5 · r4 killed by cyber filter |
| kustomize-2 changeset -> reconcile | MEASURE -> parked | r1 5/5,5/5 |
| go-zero-1 ApiSpec -> compat | DOWNGRADE -> BUILT | r1 5/5,5/5 · r2 5/5, full 2/5 · build: cold 2/5, local Avocado 0/5 (R3,T2), B6 not clean |
| spire-2 scope -> cursor | MEASURE -> retired | r1 5/5,5/5; only divergence = digest bytes (coined pin) |
| concourse-r2-2 step tree -> diff | MEASURE -> parked | V1 amended (in_parallel order observable) · r1 5/5 · r2 5/5 |
| concourse-r2-1 var-source graph | KILL | same seam as joshbaltar-2/swe-concourse-varsource-chain-order |
| kustomize-1, go-zero-2, spire-3 | AMEND (not spent) | step 2 collapses once stated |
| spire-1, concourse-1, concourse-2 | DOWNGRADE (not spent) | step 2 mechanical given step 1 |

## Findings worth carrying
1. Probe calibrated: accepted open62541 task, real instruction, real tests -> local 1/5 = server 1/5.
2. Fully-stated algorithm contracts saturate fresh Avocado (6/6 cards, incl. LCS, coinductive
   recursive acceptance, K3 union-coverage subsumption).
3. What discriminates (control + go-zero): stated constraints that fight the natural edit site,
   fault-injection quality, and stated equivalences over a large domain (numeric spelling,
   conditional precedence) — not algorithm rules.
4. Principle-level contracts help only when the principle does not NAME the mechanism (go-zero
   step 2 moved 5/5 -> 2/5; concourse stayed 5/5 because naming the wire codec gave everything away).
5. Codex cannot build allocation-failure graders right now: 3 sessions killed by the provider cyber
   filter, with libc override AND with the repo's own allocator hooks.
6. B6 caught an R12 oracle bug, a false negative that failed 5/5 fresh impls, a GOFLAGS forge and an
   init()-forge — none visible to preflight/oracle. Run B6 before trusting any band.

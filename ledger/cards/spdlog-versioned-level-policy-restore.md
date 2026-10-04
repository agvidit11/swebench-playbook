# spdlog-versioned-level-policy-restore

- Date/machine: 2026-10-04 / devvm23237
- Repo/base: `gabime/spdlog` @ `d6c93f38a08b4ea0f8ffcfd7f7857307d5d5c3fa`
- Seam: registry global/named logger-level policy and config loading
- Composition: complete versioned policy snapshot/apply -> revision-guarded restore
- Trap: natural order loses information
- Routing: `MEASURE`, two chained steps
- A4: `ADJACENT`; no policy-snapshot/versioned-rollback peer

## User problem and base evidence

I temporarily raise logging while diagnosing an incident, but another operator may change levels while that override is active. Today I can only write the old values back afterward, which silently overwrites the newer policy. The registry also retains named rules for loggers that do not exist yet, so inspecting current logger levels is incomplete. I need a complete versioned policy snapshot and a safe restore that refuses to overwrite intervening changes.

At base, applying `warn`, temporary `trace`, newer `err`, then naïvely restoring `warn` loses the newer setting. Loading `future=debug,info` and then setting the global level to `warn` leaves an existing logger at `warn` while a subsequently initialized `future` logger receives latent `debug`.

CONSTRAINT: the policy artifact covers the global default, named late-bound rules, current loggers, and a monotonic policy revision. Restore succeeds only against the expected revision; any intervening registry-level mutation makes it return false without changing state.

NON-DESIRED: snapshot only instantiated logger objects; unconditional restore; revision changes for ordinary log emission; silently discard future-logger rules; compare only effective levels.

## Steps

1. Add complete versioned registry level-policy snapshot/apply behavior that preserves global and named future-logger rules, updates existing loggers, and governs later initialization.
2. Add revision-guarded restoration using the Step-1 artifact. `set_level`, config loading, or policy application between capture and restore causes an atomic false/no-change outcome.

Step 2 is a distinct conditional mutation over Step 1's complete state artifact, not another report. Existing exact public naming remains a probe question; no internal representation is pinned.

Harness: focused header-only probes compile offline in 4–6s; full primary test runs in 5.5s. Exclude individual AI-touched branches/seams. Full survey evidence is in the `/root/scout_spdlog` handoff.

Rating: P1 4, P2 2, P3 1, P4 4, P5 4, P6 3, P7 3 = **21/28 MEASURE**.

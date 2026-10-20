# MT recipe v2: replicate the Oct 5–10 run (8 server passes in ~5 days)

## What the winning run did (measured)
Passes: jsonc, reversion, FieldTracker, OTIO, jedi, vobject, auditlog, isogit, then polyfactory, picocli, dogpile, MST, wtforms, store_model, node-config, polymorphic.
1. **Domain first:** library *state/identity bookkeeping under a sequence of edits*. Seen: undo/history, source-preserving edits, recurring series, timeline nest/unnest, refactorings, stash/apply, config reload/layering, cache invalidation scopes, generic specialization, value provenance, patch logs, form row identity, dirty tracking.
2. **One authority sentence**, in lay voice: "same as the existing path X" / "same as a fresh rebuild/reload". No case lists.
3. **≥3 independent fault lines per non-exempt step**, reproduced at base by Codex (each line ≈0.8 pass alone; three ≈0.2–0.5).
4. **3 steps that build on each other** (S1 exempt can be easy; S2 extends S1's code; S3 depends on S2's).
5. **Push fast, then fix from the server**: recover the 15 server trees, add or drop licensed lines by per-tree union, re-push. Most passed in 1–3 rounds. The server is the measurement; local runs only screen.

## What to keep from the later lessons (these caused revisions, not failures)
- Carry-forward: later steps re-run earlier steps' tests as p2p. Lowercase config keys only.
- Unforgeable grader: trusted interpreter copy + manifest, unprivileged runner, answers unreadable during grading.
- Gold check: one independent Codex mutation/state-history pass before push.
- Licensed lines: each line traces to an instruction sentence; no line chosen *because* trees failed it; reserve uniformly failed lines instead of deleting rules.
- Coupling documented in README/BUILD-NOTES. README real-rates after the pass.
- Count completed trials only (exclude provider errors).

## What to DROP (it slowed everything after Oct 15)
- Heavy cold probes at k=5 that kill 90% of cards before build. Replace with a **light screen**: k=3 headless on S2 only, rejecting just a clear 3/3 saturation. Let the server decide the rest.
- 15–20 local fix rounds before the first push. Cap at 3 rounds, then push.
- Chasing the local gate.py calibrate on the exempt step (needs Vidit's standing override rule).
- Code-transform/semantics domains that need Codex to write forge/attack controls. They trip the Codex cyber filter. Bookkeeping libraries don't need exotic forges.

## Cadence target
2–3 builds in parallel, each card → push in ≤1 day. Fix rounds from server trees as results land. Goal: 1–2 server passes per day.

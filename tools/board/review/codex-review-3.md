# Round 3 review

1. **PASS** — The claim design now covers atomic online acquisition, reconciliation, explicit-OID CAS operations, ref heartbeats, expiry grace, namespace fallback/probing, hashed refs, GC/audit, bounded refs, and offline advisory semantics.
2. **PASS** — The spool has durable `O_APPEND` + `flock` producers, one sync worker, post-push acknowledgement, dedupe, bounded foreground sync, and last-known-good behavior.
3. **PASS** — Config/profile/plugin foundations are in build step 1, and the Codimango adapter contract is complete.
4. **REVISE** — Notes are removed from the v1 command surface and unsupported funnel stages are deferred, but `archived (dirs no longer listed)` still infers an authoritative Codimango status from absence. This is unsafe when `totalExact=false`.

The `sqlrank` addition is consistent: it is optional, returns a fixed schema, preserves freshness, has an import fallback, and leaves rendering/report output in core.

## Verdict

**REVISE.** In DESIGN.md, replace:

`- **Funnel (v1, exact sources only):** built (task dirs in git) → submitted → accepted, archived (dirs no longer listed) and tasks per repo (config.json repo).`

with:

`- **Funnel (v1, exact sources only):** built (task dirs in git) → submitted / accepted / archived (Codimango status), and tasks per repo (config.json repo).`

Keep the following two sentences deferring repos screened / idea cards / retire reasons to v1.1 unchanged.

# Round 2 review

## 1. Disposition of the top 10 changes

| # | Status | Why |
|---|---|---|
| 1 | **ADDRESSED** | Authority, disagreement findings, freshness, stale-cache banners, strict mode, and fail-closed mutations are explicit. |
| 2 | **PARTLY** | A create-only remote ref fixes the simultaneous-create race, but the expiry/renew/steal protocol and GitHub namespace capability are not yet specified safely. |
| 3 | **PARTLY** | Hooks are local, bounded, rate-limited, and fail-open, but durable concurrent spool writes and single-worker sync/checkpoint semantics are still unstated. |
| 4 | **ADDRESSED** | The versioned, idempotent schema now covers writer ordering, aliases, corrections, provenance, size limits, and quarantine. |
| 5 | **ADDRESSED** | The action-first groups, width profiles, stable pipe mode, explicit words, and accessible legend resolve the UI concern. |
| 6 | **PARTLY** | Cache, health, timeout/error fixtures, and one adapter are implied, but the adapter contract still needs checked exit status, atomic last-known-good writes, and bounded foreground behavior. |
| 7 | **ADDRESSED** | `presubmit.py` remains read-only behind a wrapper that preserves output/exit status and records only after completion. |
| 8 | **ADDRESSED** | Flow/coverage/reporting lead; retained contribution stats have the fixed private, non-causal, minimum-sample, opt-in-export safeguards. |
| 9 | **PARTLY** | Portable config and extension boundaries are designed well, but section 12 introduces them after code that already depends on them. |
| 10 | **PARTLY** | Backfill, automatic NLP, and contribution analysis moved out of v1 and the failure matrix is strong; notes remain contradictory and v1 still needs tighter implementation contracts below. |

## 2. Atomic claim refs

**Is create-only push atomic on GitHub?** Conditionally, yes. If GitHub accepts that namespace and the client sends an ordinary, non-forced update from zero to `refs/claims/<id>`, receive-pack serializes the ref update: of two concurrent creates, one succeeds and the other gets a stale/non-fast-forward rejection. A prior `ls-remote` is not the lock; only the push result is.

That does not yet make the design a complete lease protocol:

- **Namespace/support:** GitHub reliably exposes branch/tag refs, but arbitrary namespaces may be hidden or rejected and are not fetched by a normal clone. Add an integration probe against the exact repository for create, read, renew, and delete. If `refs/claims/*` is unsupported, use `refs/heads/workboard-claims/<hash>` and verify its ruleset behavior.
- **Ref names:** Do not embed raw task names. Use a fixed-length hash of the canonical entity ID; store the original ID in the claim object. This avoids invalid ref characters and `foo` versus `foo/bar` file/directory collisions.
- **Permissions/push rules:** Repository write access generally permits direct manipulation, while branch protections may not cover custom refs; a rule may also reject deletion or updates. This protects cooperating clients from races, not from another writer issuing a plain force/delete. `doctor` must report the capability/rules result, and the design must not call this an authorization boundary.
- **Ambiguous push outcome:** SSH can disconnect after GitHub accepted a push. Give every acquisition a unique `claim_id` and unique commit OID, then query the exact remote ref after any uncertain result. Own OID means acquired; another OID means lost; absent means retryable. Never report success from local state alone.
- **Lease semantics:** Use the explicit form `--force-with-lease=refs/claims/<id>:<observed_oid>` for release, renewal, and steal. Never use bare `--force-with-lease`, because custom refs have no dependable remote-tracking ref. Include a unique nonce to avoid accidental ABA reuse.
- **Heartbeat/steal:** The liveness heartbeat must CAS-update the claim ref itself to a new descendant commit. A ledger-only heartbeat leaves a TOCTOU hole: a renewal can occur while a thief still replaces the unchanged ref. Steal must create a descendant of the exact expired tip and update with the explicit expected OID; a concurrent renewal or steal then loses cleanly.
- **Expiry/clock:** A commit timestamp is client-controlled, not GitHub receipt time. Require clock-health checks and, before steal, observe the same tip unchanged for a monotonic grace period of at least two heartbeat intervals, then CAS it. Refuse steal when claim-source or clock health is bad.
- **Force/delete:** Descendant renew/steal updates can remain fast-forward even while carrying an explicit lease. Deletion still needs delete permission. Rules forbidding force/deletion must be detected before claims are enabled.
- **GC/audit:** A live ref keeps its commit reachable; after release GitHub may eventually collect it. The ledger must retain claim/release/steal audit facts, and reconciliation must tolerate a ref change occurring before its ledger event. Never depend on a deleted claim commit for history.
- **Many refs:** Keep refs only for live claims, delete them on release/DONE, query exact refs where possible, and set a supported-live-claim bound. Listing an unbounded namespace on every hook/command will not scale.
- **Offline:** There is no exclusive offline acquisition. An offline auto-claim is `PENDING/ADVISORY`, must not be shown as owned, and may lose when synced. Hooks remain fail-open and cannot prevent two offline sessions starting the same unclaimed task. Therefore describe the feature as **atomic online acquisition with best-effort cached enforcement**, not a safety lock.

Also define “healthy/fresh claim” for hook blocking as a successful claim-ref refresh within a configured short TTL, a valid ref payload, healthy clock, and a non-expired ref heartbeat. Ledger freshness alone is insufficient.

## 3. Remaining v1 build blockers

1. **Specify durable local serialization.** All hook producers append under `O_APPEND` + `flock` with line/queue limits; one per-host sync lock assigns `seq`, rotates/checkpoints the spool, and acknowledges records only after the ledger push succeeds. Retries may duplicate events but must not lose them; `event_id` dedupes them. Bound foreground sync and retain the last-known-good cache on timeout.
2. **Move foundations earlier.** Minimal config loading/validation, profile selection, and plugin API/registry must be in step 1; only the interactive `config init` wizard may remain step 6. Otherwise early adapters and hooks will hard-code the values section 11 forbids.
3. **Pin the Codimango adapter contract.** One argv-based subprocess call per refresh, timeout, checked return code, captured stderr, envelope/schema validation, atomic cache replacement, and preservation of the prior good cache. Renderers and hooks never fetch directly.
4. **Resolve scope contradictions.** Section 12 says notes are v1.1, so remove `note add/resolve` from the v1 command surface or explicitly mark them unavailable. Build only stats whose authoritative input and timestamp/cohort definitions exist; defer unsupported funnel stages rather than estimating them silently.

## 4. Verdict

**REVISE.** Sign-off after these exact edits:

1. Replace “Atomic across servers” with “atomic online acquisition” and add the create/reconcile, explicit-OID release/renew/steal, ref-heartbeat, expiry-grace, namespace probe/fallback, hashed-name, GC, bounded-ref, and offline semantics above.
2. Add the durable spool/single-sync-worker contract.
3. Move minimal config/profile/plugin foundations to build step 1 and pin the Codimango adapter contract.
4. Remove notes and source-less funnel metrics from v1, or define their v1 authoritative inputs.

The fixed product decisions are safe with the safeguards already stated; none needs revisiting.

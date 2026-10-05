# dropwizard-metrics-membership-snapshot-reconcile

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `dropwizard/metrics` @ `f0e769316b4e9f252f70fc063721d88b86a587b3`
- Seam: frozen flattened membership -> identity-sensitive delta -> conditional in-place reconciliation
- Trap: natural order loses authority; replacing the registry breaks held consumers
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `CLEAR`; no Dropwizard Metrics reconciliation task or disclosed remedy found

## User problem and base evidence

Our service loads metrics from optional plugins. The plugins own long-lived counters, meters, and gauges, but plugin membership changes on configuration reload. Calling `registerAll` again can collide halfway through or leave removed metrics behind. Replacing the shared registry is unsafe because reporters and application components retain the original object. I need to freeze what is published, compare it with the next nested metric set, and update that same shared registry only if the frozen starting point is still current.

At base, `getMetrics()` is immutable but live rather than a membership snapshot. `registerAll` inserts earlier entries before a later collision and leaves partial stale membership. Replacing a `SharedMetricRegistries` entry changes registry identity while a reporter holding the old object keeps reporting stale state. Focused offline core tests pass 74/74 in 5.60 seconds.

## Steps

1. Add an immutable, recursively flattened membership snapshot of a `MetricSet` or registry. It freezes names and metric object identities, not changing counter/gauge values; later source or child-registry membership changes cannot alter it.
2. Compare two snapshots and deterministically classify added, removed, replaced, and unchanged names. Same name plus same metric object is unchanged; a different object is replacement.
3. Apply the delta to the existing registry only when its scoped membership still matches the baseline. A stale delta fails before mutation or listener events. Success preserves unchanged identities/state, emits one typed event per actual change, leaves unrelated names untouched, and remains visible through an already-held reporter and shared-registry reread.

CONSTRAINT: derive publication from frozen membership and reject stale input before altering the held shared registry.

NON-DESIRED: live-map snapshots; additive `registerAll`; clear-and-reregister; type-only equality; mutation before stale validation; swapping the registry object; diffing before nested expansion.

Independent branches include recursive expansion, registry-as-child membership, object identity versus name/type equality, unchanged state retention, stale-baseline preflight, listener cardinality, unrelated-name scoping, and held-reporter identity. Step 3 is a distinct mutation/publication operation consuming Step 2's artifact. No single-turn fallback.

Relevant seams: `MetricRegistry.java:101-171,359-390,533-541,595-607`; `SharedMetricRegistries.java:24-50,99-105`; `ScheduledReporter.java:275-285`.

Evidence: `/root/scout_dropwizard_metrics` handoff.

Rating: P1 4, P2 4, P3 2, P4 3, P5 4, P6 3, P7 3 = **23/28 MEASURE**.

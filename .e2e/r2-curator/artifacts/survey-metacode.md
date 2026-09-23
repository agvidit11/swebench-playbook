MetaCode at Meta (https://fburl.com/metacode)
Using AI Gateway (Meta Model API upstream)
[metacode] using AI inference gateway (Model API): https://metacode-modelapi.ai-gateway.fbinfra.net/v1
Warning: Failed to mount .arcrc: Mount failed '/tmp/phabricator_cats/metacode_agvidit/2577579/arcrc' to '/home/agvidit/.arcrc': ENOENT: No such file or directory
[93mWARNING: 11 skill(s) in /home/agvidit/.claude/ not available for MetaCode.[0m
MetaCode reads skills from ~/.agents/skills/ and .metacode/skills/, not from .claude/.
Run `metacode migrate-from-claude` to copy them to ~/.agents/skills/, or `agent-market skill <name> install --agent metacode`, or open MetaCode TUI and run `/legacy-skills` to see the list.

Surveying Curator for failure-atomicity — verifying HEAD admissions and mapping recovery seams.
Those four admissions look thin — now digging into the actual recovery seams for real surfaces.
The broad grep came back empty on escaping — switching to direct file reads.
Discovery re-registration and queue seams are mapped — now checking barriers, transactions, and namespace handling.
Evidence gathering is nearly complete — pulling final line citations.
## Admissions check (before the surfaces)

**A1 — `curator-framework/.../state/ConnectionStateManager.java:264`.** Still true at HEAD. In context (`processEvents()`, lines 259–267) it concedes a real race, not a style nit:

```
// CURATOR-525 - there is a race whereby LOST is sometimes set after the connection has been
// repaired
// this "hack" fixes it by forcing the state to "RECONNECTED"
log.warn("ConnectionState is LOST but isConnected() is true. Forcing RECONNECTED.");
addStateChange(ConnectionState.RECONNECTED);
```

What it concedes: `currentConnectionState == LOST` and `isConnected() == true` can hold simultaneously, so the manager re-posts RECONNECTED after LOST. It does not concede anything about *listener-visible ordering* (can a listener see LOST then RECONNECTED with no suspension between? can it see RECONNECTED twice?) — that ordering contract is what Surfaces 1–2 mine.

**A2 — `curator-recipes/.../cache/NodeCache.java:169` ("bare TODO").** Still true at HEAD, but concedes almost nothing. In context (`close()`, lines 163–176) the TODO sits above nulling out two fields for GC:

```
// TODO
// From PathChildrenCache
// This seems to enable even more GC - I'm not sure why yet - it
// has something to do with Guava's cache and circular references
connectionStateListener = null;
watcher = null;
```

Verdict: a GC-hygiene mystery, not a behavioural gap. Not surfaced (would violate the ~20-line/auto-reject rule anyway).

**A3 — `curator-recipes/.../cache/TreeCache.java:375`.** Still true at HEAD, and slightly more interesting than it looks. In context (`processResult` CHILDREN case, lines 372–383):

```
// TODO consider doing update of cversion, pzxid, numChildren only
if (isLive(oldChildData) && oldChildData.getStat().getMzxid() == newStat.getMzxid()) {
```

What it concedes: on a CHILDREN event whose `mzxid` is unchanged, the code replaces the whole `ChildData`/stat rather than merging child-version fields — so a concurrent GET_DATA update can be obscured (the comment on lines 377–378 admits the hazard). Touches Surface 6's territory but at single-node granularity. Kept as evidence inside Surface 6, not its own surface (fix is ~5 lines).

**A4 — `curator-recipes/.../cache/PathChildrenCache.java:396` ("bare TODO").** Still true at HEAD, same GC-nulling mystery as A2 (`close()`, lines 396–401). Not a surface.

**Further grep I ran myself** over `state/`, `cache/`, `nodes/`, `atomic/`, `queue/`, `shared/`, `barriers/`, `x-discovery details/`, `imps/` for `TODO|FIXME|HACK|XXX|hack|workaround`: the only additional hits are the two already above (`ConnectionStateManager.java:264`, `TreeCache.java:607` "TODO: consider making public" on a helper). So there is no hidden fifth admission in the lens modules; the four given admissions are exhaustive there.

---

## SURFACE 1 — ConnectionStateManager bounded-queue event drop under flap storm

**HEAD citation.** `curator-framework/src/main/java/org/apache/curator/framework/state/ConnectionStateManager.java:59` declares `private final BlockingQueue<ConnectionState> eventQueue = new ArrayBlockingQueue<>(QUEUE_SIZE);` with `QUEUE_SIZE` defaulted at lines 43–55; `postState()` at lines 226–235 does:

```java
while (!eventQueue.offer(state)) {
    eventQueue.poll();
    log.warn("ConnectionStateManager queue full - dropping events to make room");
}
```

and the single consumer `processEvents()` (lines 237–275) delivers by `eventQueue.poll(pollMaxMs, ...)`. Behaviour TODAY: under a rapid SUSPENDED→RECONNECTED→SUSPENDED→LOST flap, intermediate states are **silently discarded oldest-first** and listeners observe a subsequence, never the full sequence. This is ALREADY-IMPLEMENTED (the drop policy is deliberate); what is missing is any contract about *which* subsequence survives (e.g. is the terminal LOST always delivered? is a RECONNECTED ever delivered after the LOST it precedes?).

**Nearest presence.** Verbatim closest thing, `addStateChange()` lines 177–199, dedupes only *consecutive duplicates* (`if (previousState == newConnectionState) return false;`) — it fails to cover non-consecutive loss: SUSPENDED, RECONNECTED, SUSPENDED, LOST with a full queue can deliver e.g. SUSPENDED then LOST, or LOST alone, with no rule stated.

**The fork, as two concrete implementations.** Family A: *priority-preserving drop* — when full, drop the oldest *reconnectable* state but never drop LOST (terminal states pin the queue). Family B: *coalescing drop* — when full, merge into the latest state per equivalence class (any run of SUSPENDED/RECONNECTED collapses, LOST always appended). They DIVERGE OBSERVABLY: inject SUSPENDED, RECONNECTED, SUSPENDED, LOST into a queue of capacity 1. Family A delivers [SUSPENDED, LOST]; Family B delivers [LOST] only — a listener counting RECONNECTED callbacks sees 0 vs 1, and a recipe that recreates ephemeral nodes on RECONNECTED (e.g. `PersistentNode`'s listener) does or does not attempt a doomed create.

**Fault and invariant.** Fault: a network flap producing 4+ state transitions faster than `processEvents()` drains (queue saturates). Invariant: **after the flap settles, every registered listener observes the terminal state exactly once and never observes a state sequence that moves backwards (RECONNECTED delivered after LOST).**

**Tension.** "Deliver every transition so recipes can clean up each episode" vs "never let the event thread fall unboundedly behind a noisy connection" — full fidelity requires an unbounded queue; boundedness requires loss, and the current code chooses loss with no ordering rule.

**Determinism seam.** Deterministic without sleeps: `ConnectionStateManager` is drivable by hand — call `setToSuspended()` / `addStateChange(...)` directly from the test thread with a small `QUEUE_SIZE` (system property read at lines 43–55) and record listener callbacks on a same-thread `ListenerContainer`; no `TestingServer` needed for the queue mechanics, `TestingServer` restart only for end-to-end.

**Vocabulary check.** `ConnectionState` (ALREADY-IN-REPO, `state/ConnectionState.java`), `SUSPENDED`/`LOST`/`RECONNECTED` (ALREADY-IN-REPO, same enum), `eventQueue` / `QUEUE_SIZE` (ALREADY-IN-REPO, grep `QUEUE_SIZE` in `ConnectionStateManager.java`), `postState` (ALREADY-IN-REPO, line 226). COINED-BY-YOU: "flap storm", "terminal state" (used descriptively only; contract is stated in enum constants).

**Size.** ~80–120 net lines across 2–3 files (queue policy + a `ConnectionStateManager` unit test + docs on the enum); inside the band.

---

## SURFACE 2 — LOST-after-repair "hack" double-delivery ordering

**HEAD citation.** `curator-framework/.../state/ConnectionStateManager.java:259–267` (quoted under A1 above): when `currentConnectionState == LOST` but `isConnected()` is true, the manager calls `addStateChange(RECONNECTED)` — posting RECONNECTED *after* LOST was already queued/delivered. And `addStateChange()` lines 182–186 only suppresses *consecutive* duplicates, so a listener can observe `... LOST, RECONNECTED` where the RECONNECTED is synthesized, or `RECONNECTED, LOST, RECONNECTED` across CURATOR-525 interleavings. ALREADY-IMPLEMENTED as a repair heuristic; the listener-visible ordering contract ("LOST is terminal until the next SUSPENDED", or "synthesized RECONNECTED is marked") is missing.

**Nearest presence.** Verbatim, `setCurrentConnectionState()` lines 312–314 (`startOfSuspendedEpoch` bookkeeping) plus the hack itself — they cover the *manager's internal* convergence back to RECONNECTED but fail to cover what the *listener* may already have done with the LOST (e.g. a recipe that deleted its ephemeral node on LOST now recreates it on the synthesized RECONNECTED, while a second recipe that saw only RECONNECTED never cleaned up — the two diverge with no reconciling event).

**The fork, as two concrete implementations.** Family A: *suppress-and-mark* — when the hack fires, deliver a `RECONNECTED` flagged as synthesized (or suppress it if LOST was already delivered and no new suspension occurred). Family B: *episode numbering* — every SUSPENDED opens an episode id; LOST and RECONNECTED carry it, and a synthesized RECONNECTED reuses the LOST's episode so listeners can tell "recovery from the loss you already saw" from "a new incident". DIVERGE OBSERVABLY: drive LOST-delivered then hack-fires. Family A: listener sees no second RECONNECTED (or one marked synthetic). Family B: listener sees RECONNECTED with the same episode id as the LOST. A counting listener distinguishes them.

**Fault and invariant.** Fault: session-timeout injection (`checkSessionExpiration()` lines 277–298, `injectSessionExpiration`) racing a concurrent reconnect, the CURATOR-525 window. Invariant: **no listener ever observes RECONNECTED as the immediate successor of a LOST it already consumed unless a new SUSPENDED/LOST episode began in between.**

**Tension.** "Converge the manager's internal state to the truth (`isConnected()`) immediately" vs "never rewrite history the listeners already acted on" — the hack optimizes the former and ignores the latter.

**Determinism seam.** Deterministic: the repo already scaffolds exactly this race — `CuratorFrameworkImpl.debugCheckBackgroundRetryLatch / debugCheckBackgroundRetryReadyLatch` with the comment `// scaffolding to test CURATOR-525` (`CuratorFrameworkImpl.java:713–744`). Drive `addStateChange(LOST)`, stub `isConnected()==true`, assert listener sequence; no sleeps.

**Vocabulary check.** `ConnectionState.LOST / RECONNECTED / SUSPENDED` (ALREADY-IN-REPO), `addStateChange` (ALREADY-IN-REPO, line 177), `isConnected` (ALREADY-IN-REPO, line 222), CURATOR-525 (ALREADY-IN-REPO, line 262 comment). COINED-BY-YOU: "episode", "synthesized" (descriptive; the contract can be written with enum constants plus a boolean already present in `ConnectionState.isConnected()`).

**Size.** ~80–130 net lines across 2–4 files (manager + listener contract + test); inside the band.

---

## SURFACE 3 — CircuitBreakingConnectionStateListener coalescing: what the managed listener sees

**HEAD citation.** `curator-framework/.../state/CircuitBreakingConnectionStateListener.java:152–162` (`handleOpenStateChange`): while the circuit is open every state except the *first* SUSPENDED→LOST transition is swallowed (`circuitLastState = newState` recorded but not forwarded), and `closeCircuit()` lines 188–192 forwards at most one state — and **nothing at all** when `circuitLastState == circuitInitialState` (`stateToSend` is null). So TODAY a flap of SUSPENDED, RECONNECTED, SUSPENDED, RECONNECTED inside one open-circuit window produces exactly one downstream callback (the opening SUSPENDED) plus possibly one closing state — the two interim RECONNECTEDs vanish. ALREADY-IMPLEMENTED; missing is the contract saying which swallowed transitions a recipe may assume *did not happen* (can it assume its ephemeral node still exists because it never saw RECONNECTED? it cannot — the reconnection was real).

**Nearest presence.** Verbatim javadoc lines 47–57: "While the delay is active, the circuit breaker will store state changes but will not forward them … When the delay elapses, if the connection has been restored, the circuit closes and forwards the new state" — covers *forwarding the last state* but fails to cover the `stateToSend == null` case (line 189: connection flapped and returned to the opening state, so the managed listener sees SUSPENDED…silence, and cannot distinguish "outage ongoing" from "outage came and went").

**The fork, as two concrete implementations.** Family A: *edge-reporting close* — on close always emit the last state even if equal to the initial one (listener sees SUSPENDED…SUSPENDED meaning "one full flap episode elapsed"). Family B: *episode-summary close* — on close emit a single RECONNECTED iff the connection is currently up regardless of stored states (listener sees SUSPENDED…RECONNECTED, i.e. "you are connected now, reconcile"). DIVERGE OBSERVABLY: open on SUSPENDED, flap to RECONNECTED and back to SUSPENDED, let retries exhaust. Family A delivers a second SUSPENDED; Family B delivers RECONNECTED-or-nothing depending on current truth — a recipe that recreates state on RECONNECTED behaves differently.

**Fault and invariant.** Fault: connection flapping faster than the circuit-breaker `RetryPolicy` delay (`CircuitBreaker.tryToRetry`, `CircuitBreaker.java:72–88`, driven by `RetryPolicy.allowRetry` at line 80). Invariant: **when the circuit closes, the managed listener's last observed state correctly classifies the current connectivity (connected vs not) — it never believes it is disconnected when the client is connected.**

**Tension.** "Shield recipes from noisy herding" (javadoc lines 29–35) vs "never let a recipe's view of connectivity go stale behind the shield" — every swallowed RECONNECTED is load saved and truth lost simultaneously.

**Determinism seam.** Fully deterministic: `CircuitBreakingConnectionStateListener` has a package-visible constructor taking a `CircuitBreaker` (`lines 113–119`), and `CircuitBreaker.build(retryPolicy, service)` (line 43–45) accepts an injectable `ScheduledExecutorService` — use a same-thread/manual scheduler, drive `stateChanged()` by hand, no ZK server at all.

**Vocabulary check.** `ConnectionState.{SUSPENDED,LOST,RECONNECTED}` + `isConnected()` (ALREADY-IN-REPO), `CircuitBreaker.{tryToOpen,tryToRetry,isOpen,getRetryCount}` (ALREADY-IN-REPO, `state/CircuitBreaker.java:49–88`), `circuitLostHasBeenSent / circuitLastState / circuitInitialState` (ALREADY-IN-REPO, lines 83–87). COINED-BY-YOU: "flap episode" (descriptive only).

**Size.** ~60–100 net lines (listener + test); lower edge of band — pair with Surface 2 if a larger task is needed.

---

## SURFACE 4 — **REVERT-AND-REDO** — ServiceDiscovery re-registration across N ephemeral nodes is not atomic

**HEAD citation.** `curator-x-discovery/src/main/java/org/apache/curator/x/discovery/details/ServiceDiscoveryImpl.java:402–408`:

```java
private void reRegisterServices() throws Exception {
    for (final Entry<T> entry : services.values()) {
        synchronized (entry) {
            internalRegisterService(entry.service);
        }
    }
}
```

with per-service `internalRegisterService()` at lines 206–233 doing create-catch-NodeExists-delete-then-recreate with `MAX_TRIES = 2`, invoked from the reconnect listener at lines 70–83 (`RECONNECTED`/`CONNECTED` → `reRegisterServices()`, exceptions only logged). Behaviour TODAY: re-registration is a sequential loop over N services with per-entry locking and **no cross-service atomicity** — if the session expires (or `start()`'s caller gives up, cf. `start()` lines ~138–146 catching `KeeperException` with "will try again later") midway, services 1..k are re-registered and k+1..N are not, and nothing records k. ALREADY-IMPLEMENTED as best-effort loop; the atomicity/reconciliation contract is missing.

**Nearest presence.** Verbatim, `updateService()` (~lines 190–204): takes `synchronized (entry)`, sets `entry.service = service`, serializes and `setData().forPath(...)` — covers single-service consistency but fails to cover the multi-service case: a concurrent `updateService` for service B racing `reRegisterServices()` can serialize-then-re-register in either order, leaving ZK holding B-old with the in-memory entry holding B-new and no version check (plain `setData`, no `withVersion`).

**The fork, as two concrete implementations.** The naive first implementation (which is HEAD): *eager re-register-all on every RECONNECTED*, sequentially, exceptions logged-and-continued. It is killed by the second requirement: **re-registration must converge to exactly the in-memory set with no ghost resurrection** — because the same loop also runs at `start()`, and `unregisterService()` (lines 244–247: `services.remove()` then delete) racing a reconnect can have its delete undone by a concurrent re-register pass that already snapshotted the entry (unregister removes from the map but the loop holds a stale `Entry` reference). The redo, Family B: *diff-and-version re-registration* — snapshot entry versions, re-register only entries whose version predates the disconnect, skip entries removed during the pass, and verify each create with a post-read. DIVERGE OBSERVABLY: register A and B, start a reconnect pass, concurrently unregister B. Naive: B's ephemeral node exists in ZK after the pass (ghost resurrected). Redo: B stays absent. A `checkExists` after the race distinguishes them deterministically.

**Fault and invariant.** Fault: session expiry / RECONNECTED arriving between service k and k+1 of N, or `unregisterService(B)` interleaving with the re-register loop. Invariant: **after re-registration settles, the set of ephemeral instance nodes in ZK equals exactly the set of currently registered services — no partial prefix, no resurrected unregistered instance.**

**Tension.** "Re-register fast and eagerly so discovery downtime is minimal" vs "never resurrect an instance its owner just withdrew" — speed wants snapshot-and-blast; correctness wants version-checked diffing.

**Determinism seam.** Deterministic: `internalRegisterService` is `@VisibleForTesting`-adjacent protected (line 206), `getRegisteredService` is `@VisibleForTesting` (line 397), `Entry` lock is per-service so a test can hold one entry's monitor to stall the loop mid-pass while another thread unregisters; `TestingServer` kill/restart supplies the RECONNECTED. No sleeps required — coordinate with latches on the entry monitor.

**Vocabulary check.** `registerService / unregisterService / updateService / reRegisterServices / internalRegisterService` (ALREADY-IN-REPO, grep `RegisterService` in `ServiceDiscoveryImpl.java`), `Entry.service / Entry.cache` (ALREADY-IN-REPO, lines 85–93), `RECONNECTED / CONNECTED` (ALREADY-IN-REPO, line 72), `CreateMode.EPHEMERAL / DYNAMIC_SEQUENTIAL` (ALREADY-IN-REPO, lines 213–224). COINED-BY-YOU: "ghost resurrection" (descriptive label for `checkExists == non-null after unregister`; contract uses existing methods).

**Size.** ~100–150 net lines across 2–4 files (versioned entries + re-register diff + test); inside the band.

---

## SURFACE 5 — DownInstanceManager: which errors count, and wall-clock purge under concurrency

**HEAD citation.** `curator-x-discovery/src/main/java/org/apache/curator/x/discovery/details/DownInstanceManager.java:46–61`:

```java
void add(ServiceInstance<?> instance) { purge(); ... useStatus.errorCount.incrementAndGet(); }
public boolean apply(ServiceInstance<T> instance) { purge();
    Status status = statuses.get(instance);
    return (status == null) || (status.errorCount.get() < downInstancePolicy.getErrorThreshold());
}
```

with time-based `purge()` at lines 63–82 (entries older than `downInstancePolicy.getTimeoutMs()` removed, purge itself throttled to half-timeout). Behaviour TODAY: **every** `ServiceProviderImpl.noteError()` (line 130–131: `downInstanceManager.add(instance)` unconditionally) counts equally toward `getErrorThreshold()` — a connection-loss failure of the *caller* and a genuine failure of the *instance* are indistinguishable — and `Status.startMs` is fixed at first-error time, so a steady trickle of errors just under threshold never marks down while a burst does, with purge timing driven by `System.currentTimeMillis()`. ALREADY-IMPLEMENTED as a counting filter; the error-classification contract (which failures are the instance's fault) is missing.

**Nearest presence.** Verbatim closest, `ServiceProviderImpl.getInstance()` lines 125–131 returning `providerStrategy.getInstance(instanceProvider)` where `instanceProvider` is filtered by `localFilters` including the `downInstanceManager` (lines 78–80) — covers *excluding* downed instances but fails to cover *attribution*: `noteError` takes only the instance, not the exception, so the filter can never learn whether the error was retryable-transport vs instance-death.

**The fork, as two concrete implementations.** Family A: *classified noteError* — `noteError(instance, throwable)` counts only non-retryable codes (BADVERSION/NODEEXISTS-class server rejections) and ignores transport codes (CONNECTIONLOSS/SESSIONEXPIRED/OPERATIONTIMEOUT), reusing the repo's existing retryability notion (`CuratorFrameworkImpl.processBackgroundOperation` lines 517–518: `getRetryPolicy().allowRetry(KeeperException.create(code))`). Family B: *decaying score* — keep unclassified counting but replace the fixed-window `startMs`/purge with per-error timestamps and a sliding window, so a trickle eventually clears and a burst still trips. DIVERGE OBSERVABLY: 5 CONNECTIONLOSS errors then a healthy call, threshold 5. Family A: instance never marked down (`apply` true throughout). Family B (or HEAD): instance marked down until timeout purge. `apply()` before/after distinguishes them.

**Fault and invariant.** Fault: caller's connection drops mid-`getInstance`-then-use (all N in-flight calls fail with CONNECTIONLOSS, none the instance's fault) while `purge()`'s wall-clock throttle (line 66: skip if within half-timeout) delays clearing. Invariant: **transport-caused errors alone never cause a healthy instance to be excluded once connectivity is restored.**

**Tension.** "Shed failing instances fast to protect tail latency" vs "never confuse your own network outage with their outage" — fast shedding wants every error counted; correct attribution wants most errors discounted during a flap.

**Determinism seam.** Deterministic, no server: `DownInstanceManager` is a pure in-memory class (`ConcurrentMap` + `AtomicInteger`/`AtomicLong`); drive `add`/`apply` by hand with a `DownInstancePolicy(errorThreshold, timeoutMs)`. Only the purge uses wall clock — injectable by using tiny timeouts plus a same-thread executor, or expose `startMs`; a `Thread.sleep` is needed *only* for the purge-timing half, the classification half is sleep-free.

**Vocabulary check.** `DownInstanceManager.add/apply/purge` (ALREADY-IN-REPO, lines 46–82), `DownInstancePolicy.getErrorThreshold/getTimeoutMs` (ALREADY-IN-REPO, `x/discovery/DownInstancePolicy.java`), `ServiceProviderImpl.noteError/getInstance` (ALREADY-IN-REPO, lines 125–131), `InstanceFilter.apply` (ALREADY-IN-REPO, line 56). COINED-BY-YOU: none — contract uses `apply()` return values and `KeeperException.Code` constants.

**Size.** ~80–130 net lines (classification + test); inside the band. (Note: this is error *classification*, not "exponential backoff" — the rejected three-word item is the retry timing, which this surface does not touch.)

---

## SURFACE 6 — CuratorCache rebuild: double-query races and phantom delete/create pairs (NET-NEW capability)

**HEAD citation.** `curator-recipes/.../cache/CuratorCacheImpl.java:137–149`:

```java
private void rebuild() {
    ...
    nodeChanged(path);   // rebuild from the root first
    // rebuild remaining nodes - note: this may cause some nodes to be queried twice
    // (though versions checks will minimize that). If someone can think of a better
    // way let us know
    storage.stream().map(ChildData::getPath).filter(p -> !p.equals(path)).forEach(this::nodeChanged);
}
```

with `processEvent()` lines 151–170 mapping watch events to `nodeChanged`/`removeStorage`, and storage a `StandardCuratorCacheStorage` ConcurrentHashMap (`StandardCuratorCacheStorage.java:37–64`: bare `put`/`remove`/`clear`, no generation). Behaviour TODAY (ALREADY-IMPLEMENTED as eager best-effort): during a reconnect-triggered `rebuild()` (wired via `persistentWatcher.getResetListenable().addListener(this::rebuild)` line 87, and `PersistentWatcher`'s reset fires on every `isConnected()` state, `PersistentWatcher.java:53–56`), each path is re-queried independently while live watch events concurrently `put`/`remove` — so a listener can observe REMOVE then CREATE for a node that never disappeared (rebuild's `removeStorage` racing a concurrent `nodeChanged` put), or miss an update that lands between the root query and its own path's query.

**Nearest presence.** Verbatim, `OutstandingOps` (`cache/OutstandingOps.java:25–49`): an `AtomicLong` counter with a one-shot `completionProc` (fires `initialized`) — covers *counting in-flight ops to gate the initial `initialized` event* but fails to cover *generation fencing of rebuild vs live events*: it counts but does not tag, so a live event from generation N applied during rebuild N+1 is indistinguishable from a rebuild result.

**The fork, as two concrete implementations.** Family A: *generation-fenced rebuild* — bump a generation counter at rebuild start; tag every `nodeChanged` result with the generation that issued it; apply only results from the latest generation, dropping stale rebuild reads. Family B: *quiesce-then-diff* — pause application of live events during rebuild (buffer them), take a full snapshot, then apply the buffered live events in order on top. DIVERGE OBSERVABLY: reconnect while path /a is being updated rapidly. Family A: listener sees at most one CREATE/CHANGED per actual version, stale rebuild reads silently dropped (fewer events, possible to skip an intermediate value). Family B: listener sees the snapshot value followed by every buffered live event in order (more events, strictly ordered). An event-counting listener distinguishes them.

**Fault and invariant.** Fault: session reconnect (PersistentWatcher reset storm) racing sustained writes to a cached subtree. Invariant: **after the rebuild settles, the storage contents equal the server state at some single point in time, and no listener ever observes a REMOVE followed by a CREATE for a path whose node was never deleted.**

**Tension.** "Make the cache converge fast with independent parallel re-reads" vs "never show a listener a state that never existed" — per-path concurrency minimizes time-to-converge and maximizes phantom interleavings; fencing/diffing costs a machinery the current code explicitly wished for ("If someone can think of a better way let us know").

**Determinism seam.** Deterministic: `CuratorCacheImpl.storage()` is `@VisibleForTesting` (line 133), `nodeChanged`/`removeStorage`/`rebuild` are private but reachable via `PersistentWatcher.getResetListenable()` manual firing plus `TestingServer` data changes; drive reset + direct `processEvent` calls on one thread to force the interleave without sleeps. (This is also where TreeCache A3's `mzxid` concern generalizes: `CuratorCacheImpl.checkChildrenChanged` lines 172–179 already compares `cversion` — cite it as the per-node precedent.)

**Vocabulary check.** `CuratorCacheImpl.rebuild/nodeChanged/removeStorage/processEvent` (ALREADY-IN-REPO, lines 137–170), `OutstandingOps` increment/decrement (ALREADY-IN-REPO), `PersistentWatcher.getResetListenable` (ALREADY-IN-REPO, `watch/PersistentWatcher.java:136`), `StandardCuratorCacheStorage.put/remove` (ALREADY-IN-REPO), `ChildData.getPath` (ALREADY-IN-REPO). COINED-BY-YOU: "generation" (standard concurrency term; contract statable as "results tagged with issuing rebuild count").

**Size.** ~100–150 net lines across 2–4 files (generation fence in `CuratorCacheImpl` + storage tagging + test); inside the band. NET-NEW: the observable is listener-event atomicity under reconnect, not a new API.

---

## SURFACE 7 — PathChildrenCache RECONNECTED: refresh results vs RECONNECTED event ordering (NET-NEW capability)

**HEAD citation.** `curator-recipes/.../cache/PathChildrenCache.java:630–658` (`handleStateChange`):

```java
case CONNECTED:
case RECONNECTED: {
    try {
        offerOperation(new RefreshOperation(this, RefreshMode.FORCE_GET_DATA_AND_STAT));
        offerOperation(new EventOperation(this, new PathChildrenCacheEvent(...CONNECTION_RECONNECTED, null)));
```

Behaviour TODAY (ALREADY-IMPLEMENTED): on reconnect the cache enqueues a full `RefreshOperation` and *then* a `CONNECTION_RECONNECTED` event into the same single-threaded `offerOperation` queue — so ordering looks safe, but `RefreshOperation` fans out async `getDataAndStat` background reads per child (`processChildren`/`getDataAndStat`), and the RECONNECTED event only waits for the *refresh to be issued*, not for the *per-child reads to complete*. A listener that repopulates downstream state on RECONNECTED therefore races the refresh's own CHILD_ADDED/CHILD_UPDATED events. Contrast `TreeCache.handleStateChange` (`TreeCache.java:760–790`): RECONNECTED calls `root.wasReconnected()` *then* publishes — same eager shape, same gap.

**Nearest presence.** Verbatim, `rebuild()` lines 341–360 with `rebuildTestExchanger` (line 120, `volatile Exchanger<Object> rebuildTestExchanger`): covers *testing full-rebuild interleavings* but fails to cover the *reconnect path*: `handleStateChange` does not call `rebuild()` at all, it offers the lighter `RefreshOperation`, so the exchanger-tested barrier semantics do not apply where the fault actually hits.

**The fork, as two concrete implementations.** Family A: *barrier event* — make CONNECTION_RECONNECTED a barrier that is delivered only after all per-child reads issued by the preceding refresh complete (join on the refresh's outstanding gets, reusing the `OutstandingOps` counting idea from `cache/OutstandingOps.java`). Family B: *refresh-suppressed reconnect* — deliver RECONNECTED immediately but tag it "stale-view": listeners must treat post-reconnect child events as authoritative and the RECONNECTED itself as advisory. DIVERGE OBSERVABLY: reconnect with 3 changed children. Family A: listener sees 3 CHILD_UPDATED then RECONNECTED. Family B: listener sees RECONNECTED first, then 3 CHILD_UPDATED. Any order-logging listener distinguishes them.

**Fault and invariant.** Fault: RECONNECTED arriving while M children changed during the outage; per-child async re-reads still in flight when the RECONNECTED event fires. Invariant: **a listener that snapshots `getCurrentData()` upon CONNECTION_RECONNECTED never observes a view older than the refresh that the same reconnection triggered.**

**Tension.** "Tell listeners immediately that the connection is back so they can resume work" vs "don't let them act on a view the refresh hasn't finished repairing" — immediacy vs currency, same event.

**Determinism seam.** Deterministic: `rebuildTestExchanger` (line 120) is exactly the injection seam for pausing the refresh mid-flight — hold the exchanger, fire RECONNECTED, record listener order, release; plus `ConnectionStateListener` drivable by hand (`connectionStateListener`, lines 124–125). No sleeps.

**Vocabulary check.** `handleStateChange / RefreshOperation / EventOperation / RefreshMode.FORCE_GET_DATA_AND_STAT / PathChildrenCacheEvent.Type.CONNECTION_RECONNECTED` (ALREADY-IN-REPO, lines 630–658 + `cache/RefreshOperation.java` + `cache/EventOperation.java`), `offerOperation` (ALREADY-IN-REPO), `rebuildTestExchanger` (ALREADY-IN-REPO, line 120). COINED-BY-YOU: "barrier event" (descriptive; implementable as an `Operation` subclass, an existing type).

**Size.** ~80–140 net lines across 2–3 files (barrier op + `handleStateChange` + test); inside the band. NET-NEW: the observable is event-ordering under reconnect, not a new API.

---

## SURFACE 8 — **REVERT-AND-REDO** — DistributedQueue consumer-error handling: REQUEUE transaction vs eager delete (plus QueueSharder split-brain growth)

**HEAD citation.** `curator-recipes/.../queue/DistributedQueue.java:578–605` (`processNormally`): reads item bytes, then **deletes the item node first** (`client.delete().withVersion(...).forPath(itemPath)` line 588) and only *then* calls `processMessageBytes` (line 592) — if the consumer throws and `errorMode == REQUEUE`, the bytes survive only in memory; a crash between delete and requeue loses the message. The lock-path variant `processWithLockSafety` (lines 608–651) does it the other way: hold ephemeral lock node, process, then single ZK `inTransaction()` delete+recreate (lines 624–632) — atomic but twice the znodes per message. And `processMessageBytes` (lines 547–576) iterates a `MultiItem` batch breaking at the first failure with `REQUEUE`, discarding position. `ErrorMode` itself (`queue/ErrorMode.java:27–37`) is just `{REQUEUE, DELETE}`. ALREADY-IMPLEMENTED as two inconsistent strategies in one class; the uniform exactly-once-redelivery contract is missing.

**Nearest presence.** Verbatim, lines 596–602: `catch (NodeExists|NoNode|BadVersionException ignore) { // another process got it }` — covers *competing consumers* but fails to cover *this consumer crashing after delete-before-process*: the "another process got it" assumption is wrong when *no* process has it anymore.

**The fork, as two concrete implementations.** The naive first implementation (which is HEAD's `processNormally`): *eager delete-then-process, requeue from memory*. It is killed by the second requirement: **a message whose consumer throws must survive the consumer's own crash** (QueueSafety's `lockPath` + `QueueBuilder.lockPath` promise implies at-least-once; delete-first silently downgrades it to at-most-once whenever the process dies in the gap). The redo: *process-then-atomic-move* for all paths — unify on the transaction shape (delete original + create requeue copy in one `commit()`), extended to `MultiItem` partial progress (requeue the *unconsumed suffix*, not the whole batch). DIVERGE OBSERVABLY: batch item [m1-ok, m2-throws] with REQUEUE, then kill the consumer process between handling and requeue. Naive: m2 lost (deleted first, requeue never happened) — or with the lock variant, m1 redelivered although consumed. Redo: m1 gone, m2 present exactly once. Queue contents after the fault distinguish them. (Same file's `QueueSharder.checkThreshold` lines 220–256 adds a second facet: N independent `DistributedQueue` shards each grow/shrink on `getNumChildren` thresholds with only `leaderLatch.hasLeadership()` gating creation — two leaders across a partition both add shards; the naive "each shard decides locally" is killed by the same convergence requirement.)

**Fault and invariant.** Fault: consumer throws on item k of a batch (REQUEUE mode) and the process crashes before the requeue write lands; or connection SUSPENDED between the delete and the requeue-create. Invariant: **every queued message is delivered at least once and no successfully consumed message is ever redelivered after a consumer-side fault.**

**Tension.** "Delete first so a poison message can never block the head" vs "keep the message until the consumer succeeds so nothing is lost" — head-of-line progress vs at-least-once, decided per exception with a two-value enum.

**Determinism seam.** Deterministic: `processWithLockSafety` is `@VisibleForTesting` (line 608), `makeRequeueItemPath` is protected (line 653), `ErrorMode` settable via `setErrorMode` (line 220); drive with a throwing `QueueConsumer` against `TestingServer`, kill/restart between delete and requeue via executor control. No sleeps.

**Vocabulary check.** `ErrorMode.REQUEUE/DELETE` (ALREADY-IN-REPO), `processNormally / processWithLockSafety / processMessageBytes / ProcessMessageBytesCode.REQUEUE` (ALREADY-IN-REPO, lines 542–651), `QueueSafety.getLockPath` (ALREADY-IN-REPO), `MultiItem.nextItem` (ALREADY-IN-REPO, `queue/MultiItem.java`), `inTransaction().delete().and().create().commit()` (ALREADY-IN-REPO, lines 624–632). COINED-BY-YOU: none.

**Size.** ~100–150 net lines across 2–4 files (unified consume path + suffix requeue + test); inside the band.

---

## SURFACE 9 — DistributedAtomicValue: connection loss inside create-vs-set is unclassifiable (NET-NEW capability)

**HEAD citation.** `curator-recipes/.../atomic/DistributedAtomicValue.java:266–287` (`tryOnce`):

```java
if (createIt) { client.create().creatingParentContainersIfNeeded().forPath(path, newValue); }
else { client.setData().withVersion(stat.getVersion()).forPath(path, newValue); }
...
} catch (KeeperException.NodeExistsException | KeeperException.BadVersionException | KeeperException.NoNodeException e) {
    // do Retry
}
```

with the retry drivers `tryOptimistic` (lines 245–264) and `tryWithMutex` (lines 214–243) looping on `retryPolicy.allowRetry(...)`. Behaviour TODAY (ALREADY-IMPLEMENTED as optimistic-concurrency-with-retry): only *contention* codes retry; a `CONNECTIONLOSS`/`SESSIONEXPIRED` thrown by the blocking `create`/`setData` propagates out of `tryOnce` to the caller — but the write may or may not have applied server-side, and `MutableAtomicValue.preValue/postValue/succeeded` record nothing about the ambiguity. A caller that retries gets at-most-once reporting with at-least-once effects: the increment may apply twice.

**Nearest presence.** Verbatim closest, `getCurrentValue()` lines 203–212: catches `NoNodeException` to set `createIt = true` — covers *absence observed before the write* but fails to cover *absence-vs-presence ambiguity after a transport failure*: on retry the read may now see the value the failed write itself created, and `makeValue.makeFrom(preValue)` will apply the function twice to two different bases.

**The fork, as two concrete implementations.** Family A: *idempotent-makeValue with read-verify* — after any transport failure inside `tryOnce`, re-read and compare against the attempted `newValue` bytes; if equal, report success without re-applying (requires `MakeValue.makeFrom` results to be recognizable — works for `DistributedAtomicLong`-style increments only via fencing). Family B: *applied-or-unknown report* — never auto-retry a transport failure inside the create/set; return `succeeded=false` with a new `AtomicStats` state recording "effect unknown", leaving retry policy to the caller who owns idempotence. DIVERGE OBSERVABLY: increment 5→6, CONNECTIONLOSS thrown after server applied it, caller retries once. Family A: final value 6, `succeeded=true`. Family B: final value 6, first call reports unknown, caller decides. Final value equal but the *reported* outcome and second-call behaviour differ — observable through `AtomicValue.succeeded()` + read-back.

**Fault and invariant.** Fault: CONNECTIONLOSS/SESSIONEXPIRED between the server applying `create`/`setData` and the client receiving the reply (the classic ambiguous-failure window), inside either the optimistic or the mutex-promoted path. Invariant: **after any transport failure, the reported outcome never claims "not applied" when the value was applied, and no automatic retry ever applies a non-idempotent increment twice.**

**Tension.** "Hide transport failures behind the retry policy so callers see clean success/failure" vs "never lie about an effect you cannot verify" — the current code retries contention (safe: version-guarded) but punts transport (unsafe to retry, unsafe to report), satisfying neither fully.

**Determinism seam.** Deterministic: single-threaded `TestingServer` + a `RetryPolicy` with `allowRetry` counting; force the window with a sorter: the blocking client calls go through `RetryLoop`, and connection loss is injectable via `TestingServer.kill()`/`restart()` between `getCurrentValue` and the write by controlling the `MakeValue` callback (it runs inline between read and write — block it on a latch, kill the server, release). Assert on `AtomicValue.succeeded()` + `postValue` + server-side read. No sleeps.

**Vocabulary check.** `DistributedAtomicValue.tryOnce/tryOptimistic/tryWithMutex` (ALREADY-IN-REPO, lines 214–287), `MakeValue.makeFrom` (ALREADY-IN-REPO, `atomic/MakeValue.java`), `MutableAtomicValue.preValue/postValue/succeeded` (ALREADY-IN-REPO), `AtomicStats.incrementOptimisticTries/incrementPromotedTries` (ALREADY-IN-REPO), `PromotedToLock.getRetryPolicy/getMaxLockTime` (ALREADY-IN-REPO). (PromotedToLock's internal `InterProcessMutex` is used only as the existing promotion mechanism, not as the subject — this surface's noun is the atomic value's retry classification.) COINED-BY-YOU: "applied-or-unknown" (descriptive; statable via existing `succeeded` + `preValue/postValue`).

**Size.** ~80–140 net lines across 2–3 files (`DistributedAtomicValue` + stats/reporting + test); inside the band. NET-NEW: the observable is report-accuracy under ambiguous failure, not a new API.

---

## SURFACE 10 — SharedValue concurrent watch + reconnect re-read: monotonicity and single notification (NET-NEW capability)

**HEAD citation.** `curator-recipes/.../shared/SharedValue.java:208–220` (`updateValue`):

```java
while (true) {
    VersionedValue<byte[]> current = currentValue.get();
    if (current.getZxid() >= zxid) { return; }   // zxid-gated: stale writes dropped
    if (currentValue.compareAndSet(current, new VersionedValue<>(zxid, version, bytes))) { return; }
}
```

fed by two concurrent writers: the watch path `SharedValueCuratorWatcher.process` → `readValueAndNotifyListenersInBackground` (lines 63–71, background re-read + `upadateAndNotifyListenerCallback` lines 267–275 which calls `updateValue` then `notifyListeners` unconditionally on OK) and the reconnect path `connectionStateListener` lines 74–87 (`newState.isConnected()` → same background re-read). Behaviour TODAY (ALREADY-IMPLEMENTED monotonicity of *stored* value): the `zxid` gate keeps storage monotone, but *notification* is un-gated — two racing re-reads for versions 7 and 8 can each pass the gate in order yet each fire `valueHasChanged`, and a reconnect re-read racing a watch re-read can notify twice for one version or notify 7-after-8 if the callbacks interleave (callback for 7 runs after 8's `updateValue` but `notifyListeners` reads `getValue()` fresh at line ~278 — actually masking under-notification with *wrong-version* notification: listener called for 7's completion but handed 8's bytes, or called twice with 8's bytes). `trySetValue(previous, newValue)` lines 183–205 adds the stale-`previous` fail-fast (`previous.getZxid() != current.getZxid()` → false) that a mid-flight notification can spuriously trip.

**Nearest presence.** Verbatim, lines 189–191: `if (previous.getZxid() != current.getZxid() || !Arrays.equals(...)) return false;` — covers *caller's snapshot staleness* but fails to cover *self-inflicted staleness*: the client's own `currentValue` may have advanced via a racing re-read between the caller's `getVersionedValue()` and `trySetValue`, failing a compare that the server would have accepted (server checks `version`, client pre-checks `zxid`+bytes).

**The fork, as two concrete implementations.** Family A: *version-fenced notify* — capture the zxid read alongside the data and notify only if it is still current at callback time (drop the callback otherwise: at-most-one notification per version). Family B: *coalesced notify* — collapse concurrent in-flight re-reads into one (single-flight) and notify once with the max version observed. DIVERGE OBSERVABLY: versions 7, 8 land while a reconnect re-read is in flight (3 reads outstanding). Family A: up to 3 callbacks but each handed the bytes matching its version (or dropped if stale) — listener sees monotone (7,8) or (8). Family B: exactly 1 callback with 8's bytes. Callback count + argument bytes distinguish them.

**Fault and invariant.** Fault: third-party writes versions 7→8 during a SUSPENDED→RECONNECTED flap, so the watch re-read and the reconnect re-read (lines 76–86) are concurrently in flight with the watcher's own re-registration. Invariant: **listeners observe versions in non-decreasing order with each notification carrying the bytes of the version it announces, and each version notified at most once.**

**Tension.** "Re-read eagerly on every signal (watch event AND reconnect) so the view is never stale" vs "notify exactly once per version so listeners can act on each delivery" — two triggers, one unsynchronized callback, and the zxid gate protects storage but not the listener.

**Determinism seam.** Deterministic: the `@VisibleForTesting` constructor (lines 109–118) injects the `CuratorWatcher`, so drive `process(event)` by hand twice with controlled re-read completion (latch inside a wrapped client or merely sequence two `updateValue`-adjacent callbacks); `updateValue` is private but observable via `getVersionedValue()` + listener call log. `TestingServer` restart for the reconnect half. No sleeps.

**Vocabulary check.** `SharedValue.updateValue/readValueAndNotifyListenersInBackground/notifyListeners/trySetValue/getVersionedValue` (ALREADY-IN-REPO, lines 74–87, 183–297), `VersionedValue.getZxid/getVersion` (ALREADY-IN-REPO), `SharedValueListener.valueHasChanged/stateChanged` (ALREADY-IN-REPO), `ConnectionState.isConnected` (ALREADY-IN-REPO). COINED-BY-YOU: "single-flight" (standard term; implementable with existing `AtomicReference`).

**Size.** ~80–130 net lines across 2 files (`SharedValue` + test); inside the band. NET-NEW: the observable is notification-ordering under concurrent re-reads, not a new API.

---

## SURFACE 11 — CONTROL — NamespaceImpl lazy namespace-root creation races itself (unlensed)

**HEAD citation.** `curator-framework/src/main/java/org/apache/curator/framework/imps/NamespaceImpl.java:64–84` (`fixForNamespace`):

```java
String fixForNamespace(String path, boolean isSequential) {
    if (ensurePathNeeded.get()) {
        try {
            ...
            RetryLoop.callWithRetry(zookeeperClient, ... ZKPaths.mkdirs(... ZKPaths.makePath("/", namespace) ...) ...);
            ensurePathNeeded.set(false);
```

Behaviour TODAY: the namespace root is created lazily on first namespaced call, guarded only by a plain `AtomicBoolean` checked-then-set *after* the mkdirs completes — two threads entering concurrently both see `true`, both run `mkdirs`, and any failure in one (e.g. the other's in-flight parent creation) is swallowed by `client.logError("Ensure path threw exception", e)` while `ensurePathNeeded` stays `true` for the next call. Idempotent in outcome (`mkdirs` tolerates NodeExists) but the error is logged as if real and the "ensured" flag never records *which* outcome occurred. ALREADY-IMPLEMENTED as benign-race-tolerant; the exactly-once-attempt / error-fidelity contract is missing. (Ignoring the lens entirely: this is about path translation and startup idempotence, no connection loss involved.)

**Nearest presence.** Verbatim, `unfixForNamespace` lines 54–62 (namespace prefix stripping with the `"/"` edge case) — covers *translating results back* but fails to cover *translating attempts forward exactly once*: strip is pure, ensure is effectful-and-raced, and only the pure half is disciplined.

**The fork, as two concrete implementations.** Family A: *compareAndSet guard* — `ensurePathNeeded.compareAndSet(true, false)` *before* mkdirs; losers skip mkdirs entirely (one attempt total, failures propagate to the single attempter). Family B: *failure-sticky flag* — keep concurrent attempts but only clear the flag on success; on failure keep it set *and* rethrow to the caller instead of `logError`-and-continue. DIVERGE OBSERVABLY: namespace root creation fails once (e.g. auth error) with two threads racing. Family A: one mkdirs attempt, one exception, second thread proceeds to the data op (which fails on its own). Family B: two mkdirs attempts, both callers get the exception. Attempt counts + who observes the error distinguish them.

**Fault and invariant.** Fault: none injected (control — no flap); concurrent first-use of a namespaced client plus one failing `mkdirs`. Invariant: **a failed namespace-root creation is reported to the caller that attempted it and never surfaces as a spurious error on a later, unrelated operation.**

**Tension.** "Make first use Just Work without a startup step" vs "don't hide infrastructure failures inside a path-translation helper" — laziness wants silent ensure; diagnosability wants loud failure. No lens tension claimed beyond that.

**Determinism seam.** Deterministic: construct `NamespaceImpl` directly with a mock/TestingServer client, invoke `fixForNamespace` from N threads on a barrier; fail mkdirs via ACL or a failing `AclProvider`. No timing.

**Vocabulary check.** `NamespaceImpl.fixForNamespace/unfixForNamespace/getNamespace` (ALREADY-IN-REPO, lines 50–84), `ensurePathNeeded` (ALREADY-IN-REPO), `ZKPaths.mkdirs/fixForNamespace` (ALREADY-IN-REPO), `RetryLoop.callWithRetry` (ALREADY-IN-REPO). COINED-BY-YOU: none.

**Size.** ~40–80 net lines (guard + test); below the band's middle but a legitimate control — pair with Surface 12 for a full task.

---

## SURFACE 12 — CONTROL — PersistentTtlNode touch schedule silently loses to TTL expiry under pause (unlensed)

**HEAD citation.** `curator-recipes/src/main/java/org/apache/curator/framework/recipes/nodes/PersistentTtlNode.java:201–219` (`touch`):

```java
void touch() {
    try {
        try { client.setData().forPath(childPath); }
        catch (KeeperException.NoNodeException e) {
            client.create().orSetData().withTtl(ttlMs).withMode(CreateMode.PERSISTENT_WITH_TTL).forPath(childPath);
        }
    } catch (KeeperException.NoNodeException ignore) { // ignore
    } catch (Exception e) { ... log.debug("Could not touch child node", e); }
}
```

scheduled at `ttlMs / touchScheduleFactor` (`start()` line 227), where the child's TTL is `ttlMs` (line 208). Behaviour TODAY: the safety margin is exactly one factor (default `touchScheduleFactor` — check constructor defaults, typically small); any scheduling pause (long GC, executor stall, or a SUSPENDED period where `setData` throwsRetryable and is debug-logged-and-dropped) longer than `ttlMs - ttlMs/factor` lets the TTL node expire server-side, the parent loses its last child, and (by the class javadoc lines 46–48) the parent is deleted — **the "persistent" node silently un-persists with only a debug log**. ALREADY-IMPLEMENTED as best-effort touch; the survival-margin contract is missing. (Unlensed: this is wall-clock scheduling arithmetic, not failure-atomicity classification.)

**Nearest presence.** Verbatim, the javadoc lines 46–48: "a method of having the parent node deleted if the TTL expires. i.e. if the process [dies] … will be deleted" — covers *intentional* expiry-on-death but fails to cover *accidental* expiry-while-alive: the same deletion mechanism fires when the toucher is merely paused, and nothing distinguishes the two cases afterward.

**The fork, as two concrete implementations.** Family A: *expiry-aware touch* — before each `setData`, `checkExists` the child; if absent (expired while alive), recreate parent chain + child and report a `TOUCH_RESURRECTED` state to `PersistentNodeListener` (an existing listener type, `nodes/PersistentNodeListener.java`). Family B: *deadline scheduler* — schedule touches by absolute deadline (`ttlMs/factor` before expiry computed from the last successful touch's wall time) rather than fixed rate, skipping catch-up bursts after a pause but guaranteeing at most one TTL window is ever risked. DIVERGE OBSERVABLY: stall the executor for 1.5×TTL then resume. Family A: child exists again + one resurrection notification. Family B: child may be gone with no resurrection (parent legitimately expired) but no unbounded catch-up touch storm. Post-pause `checkExists` + touch-count distinguish them. FORK ZERO risk acknowledged if only one family is deemed material — but both are implementable by a competent engineer from the existing `touch()` + `CloseableScheduledExecutorService` (`getCloseableScheduledExecutorService`, ~line 270), so both are named.

**Fault and invariant.** Fault: executor pause / GC stall / SUSPENDED window exceeding the touch margin (no network fault needed — `Thread.sleep` on the scheduler thread suffices). Invariant: **a live `PersistentTtlNode` whose process never died never loses its node to TTL expiry, or else reports the loss through its existing listener rather than a debug log.**

**Tension.** "Touch cheaply and quietly in the background" vs "never confuse 'I was paused' with 'I died'" — the TTL mechanism deliberately equates the two, and the recipe inherits that equation without recording which one happened. No manufactured tension beyond this one.

**Determinism seam.** Mixed: `touch()` is `@VisibleForTesting` package-visible (line 202) and the executor injectable (`CloseableScheduledExecutorService`), so the touch-vs-expiry race is drivable deterministically (call `touch()` manually, delete the child out-of-band, call `touch()` again and assert resurrection-or-report). Only the *realistic pause duration* needs wall clock; assert the post-pause state, not the timing — no `Thread.sleep` threshold in the assertion itself.

**Vocabulary check.** `PersistentTtlNode.touch/touchScheduleFactor/ttlMs/childPath/DEFAULT_CHILD_NODE_NAME` (ALREADY-IN-REPO, lines 59–70, 123–141, 201–227), `CreateMode.PERSISTENT_WITH_TTL / withTtl` (ALREADY-IN-REPO, lines 206–210), `PersistentNodeListener` (ALREADY-IN-REPO, `nodes/PersistentNodeListener.java`), `CloseableScheduledExecutorService` (ALREADY-IN-REPO). COINED-BY-YOU: "touch margin" (descriptive; contract statable in `ttlMs` and `touchScheduleFactor`).

**Size.** ~80–130 net lines across 2–3 files (touch path + listener signal + test); inside the band.

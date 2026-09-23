## SURFACE 1 — Suppress stale `LOST` after recovery [NET-NEW CAPABILITY, REVERT-AND-REDO]

### 1. HEAD citation

`CuratorFrameworkImpl.validateConnection()` unconditionally converts a delayed `Expired` result into `LOST` at `curator-framework/src/main/java/org/apache/curator/framework/imps/CuratorFrameworkImpl.java:677`. `ConnectionStateManager` later repairs a contradictory state by adding another `RECONNECTED` at `curator-framework/src/main/java/org/apache/curator/framework/state/ConnectionStateManager.java:260`.

The existing test expects `RECONNECTED`, then stale `LOST`, then compensating `RECONNECTED` at `curator-framework/src/test/java/org/apache/curator/framework/imps/TestFrameworkEdges.java:112`, `:117`, and `:119`.

The stronger behavior—never exposing the stale `LOST`—is **not fully implemented** at HEAD.

### 2. Nearest presence

The admission remains verbatim at `ConnectionStateManager.java:262`:

> `// CURATOR-525 - there is a race whereby LOST is sometimes set after the connection has been`  
> `// repaired`  
> `// this "hack" fixes it by forcing the state to "RECONNECTED"`

It concedes that recovery is compensating after listeners may already have observed the false state.

### 3. Fork

- **Connection-generation fencing:** increment a generation on each repaired connection, tag retry-derived failures with their originating generation, and discard a `LOST` from an older generation.
- **Queue-side reconciliation:** before dispatching a negative event, compare it with the current transport state and collapse the pending `LOST` plus corrective `RECONNECTED` into the connected state.

They diverge during rapid genuine flaps: generation fencing preserves distinct current-generation transitions, while queue reconciliation may coalesce them.

Naive first implementation: eagerly publish `LOST` and repair it with another `RECONNECTED`, as HEAD does. The second requirement—listeners must never act on a loss known to be stale—makes compensation untenable because listener side effects cannot be recalled.

### 4. Fault and invariant

**Fault:** a background retry reports `SESSIONEXPIRED` after the underlying client has already reconnected.

**Invariant:** Once recovery for a connection generation has been delivered, no failure originating in an older generation may subsequently be delivered as `ConnectionState.LOST`.

### 5. Tension

Promptly reporting genuine session loss conflicts with suppressing delayed errors without hiding a real second failure.

### 6. Determinism seam

Deterministic with concurrency but no real network or wall-clock threshold: `debugCheckBackgroundRetryReadyLatch`, `debugCheckBackgroundRetryLatch`, and `injectedCode` exist at `CuratorFrameworkImpl.java:711`, and the current test drives them around a `TestingServer` restart.

### 7. Vocabulary check

- `ConnectionState`, `LOST`, `RECONNECTED`, `ConnectionStateListener`, `SESSIONEXPIRED` — **ALREADY-IN-REPO** (`rg -n 'ConnectionState|LOST|RECONNECTED|SESSIONEXPIRED' curator-framework/src`).
- `connection generation`, `stale failure` — **COINED-BY-YOU** (`rg -ni 'connection.?generation|stale failure' curator-framework/src` has no matching contract).

### 8. Size

Roughly 110–150 net lines across 3 files: manager/framework plumbing plus race tests. In target band.

## SURFACE 2 — Preserve negative-state epochs when the listener queue overflows [NET-NEW CAPABILITY]

### 1. HEAD citation

`ConnectionStateManager` uses a fixed `ArrayBlockingQueue` of default size 25 at `curator-framework/src/main/java/org/apache/curator/framework/state/ConnectionStateManager.java:43` and `:59`. It updates `currentConnectionState` before enqueueing at `ConnectionStateManager.java:182`, then discards arbitrary oldest events when full at `:231`.

Thus the final current state is normally retained, but the behavior “each accepted negative epoch remains observable before its recovery” is **not fully implemented**.

### 2. Nearest presence

`ConnectionStateManager.java:231` says verbatim:

> `while (!eventQueue.offer(state)) {`  
> `    eventQueue.poll();`  
> `    log.warn("ConnectionStateManager queue full - dropping events to make room");`  
> `}`

This covers bounded memory but not preservation of semantically important loss/recovery pairs.

### 3. Fork

- **Producer backpressure:** block `addStateChange()` until the listener thread has queue capacity, retaining every accepted transition.
- **State-aware compaction:** keep the producer nonblocking but compact redundant states while retaining at least one negative and one recovery event per connection epoch.

They diverge observably in callback count and whether a slow listener can delay the ZooKeeper event-producing thread.

### 4. Fault and invariant

**Fault:** a listener is held on a latch while more than 25 alternating `SUSPENDED`/`RECONNECTED` transitions are posted.

**Invariant:** Every accepted negative connection epoch must be observed as negative before its corresponding connected state, even when the event queue reaches capacity.

### 5. Tension

Delivering every meaningful transition conflicts with never blocking the thread that reports connection changes.

### 6. Determinism seam

No real network or wall clock is needed: instantiate `ConnectionStateManager`, block a `ConnectionStateListener` with a `CountDownLatch`, and call public `addStateChange()` directly; `ConnectionStateManagerSize` at `ConnectionStateManager.java:47` can reduce the queue before class initialization.

### 7. Vocabulary check

- `ConnectionStateManager`, `eventQueue`, `ConnectionStateListener`, `SUSPENDED`, `RECONNECTED` — **ALREADY-IN-REPO** (`rg -n 'eventQueue|ConnectionStateListener|SUSPENDED|RECONNECTED' curator-framework/src/main/java/org/apache/curator/framework/state`).
- `negative connection epoch`, `state-aware compaction` — **COINED-BY-YOU** (`rg -ni 'negative connection epoch|state-aware compaction' curator-framework/src` finds none).

### 8. Size

About 90–130 net lines across 2 files, primarily queue policy and deterministic tests. In target band.

## SURFACE 3 — Exactly-once terminal callbacks for queued operations during client close [ALREADY-IMPLEMENTED]

### 1. HEAD citation

`CuratorFrameworkImpl.close()` changes state under `closeLock`, shuts down executors, clears delay state, atomically drains queued operations, and calls `closeOperation()` at `curator-framework/src/main/java/org/apache/curator/framework/imps/CuratorFrameworkImpl.java:347`, `:379`, and `:398`. `closeOperation()` synchronously sends a callback with `SESSIONEXPIRED` at `CuratorFrameworkImpl.java:587`.

Tests cover every background builder and assert one completion at `curator-framework/src/test/java/org/apache/curator/framework/imps/TestFramework.java:918` and `:949`.

For operations still in Curator’s pending/retry queue, this behavior is **already fully implemented**.

### 2. Nearest presence

The close-path rationale at `CuratorFrameworkImpl.java:395` is:

> `// Operations are forbidden to queue after closing, but there are still other concurrent mutations,`  
> `// say, un-sleeping and not fully terminated background thread. So we have to drain the queue atomically`  
> `// to avoid duplicated close.`

This is the closest implementation of the complete invariant rather than a missing case.

### 3. Fork

- **Synthetic terminal completion:** HEAD’s implementation drains pending operations and invokes each callback once with its original event type and `SESSIONEXPIRED`.
- **Silent cancellation:** close removes queued work and relies solely on the global `CLOSING` event, never invoking per-operation callbacks.

They diverge observably in whether callers waiting on a background callback complete or remain unresolved.

### 4. Fault and invariant

**Fault:** `close()` races with N background operations sleeping for retry in `backgroundOperations`.

**Invariant:** Every callback-bearing operation drained by close receives exactly one terminal callback with its original `CuratorEventType` and `SESSIONEXPIRED`.

### 5. Tension

Completing every callback can make `close()` run arbitrary user callback code, while silent cancellation permits faster and more isolated teardown.

### 6. Determinism seam

Concurrency is required, but neither a real network nor a wall-clock threshold is inherently required: `CuratorFrameworkImpl.DebugBackgroundListener` and the test’s `CountingCompletableFuture` provide latch/count seams. The current integration helper at `TestFramework.java:933` still includes `Thread.sleep` and server restarts, so the existing suite is partly timing-based.

### 7. Vocabulary check

- `backgroundOperations`, `OperationAndData`, `CuratorEventType`, `CLOSING`, `SESSIONEXPIRED`, `BackgroundCallback` — **ALREADY-IN-REPO** (`rg -n 'backgroundOperations|OperationAndData|CLOSING|SESSIONEXPIRED|BackgroundCallback' curator-framework/src`).
- `terminal callback` — **COINED-BY-YOU** (`rg -ni 'terminal callback' curator-framework/src` finds none).

### 8. Size

Implementation is already present. Strengthening or isolating the contract would be roughly 80–120 net test lines across 1–2 files, with little or no production change.

## SURFACE 4 — Sequential service registration survives reconnect without duplicates [NET-NEW CAPABILITY, REVERT-AND-REDO]

### 1. HEAD citation

`registerService()` installs an `Entry` in `services` before remote creation at `curator-x-discovery/src/main/java/org/apache/curator/x/discovery/details/ServiceDiscoveryImpl.java:178`. `DYNAMIC_SEQUENTIAL` selects `EPHEMERAL_SEQUENTIAL` at `ServiceDiscoveryImpl.java:219`, but the returned concrete path is discarded at `:226`. Reconnect invokes the same creation again at `:402`, while unregister deletes the unsuffixed `pathForInstance(...)` at `:453`.

Consequently, reconnect within the same session can add another sequential child, and unregister does not know the actual suffixed child path. Duplicate-free sequential registration is **not fully implemented**.

### 2. Nearest presence

The nearest recovery logic is verbatim at `ServiceDiscoveryImpl.java:72`:

> `if ((newState == ConnectionState.RECONNECTED) || (newState == ConnectionState.CONNECTED)) {`  
> `    try {`  
> `        log.debug("Re-registering due to reconnection");`  
> `        reRegisterServices();`

It restores registration intent, but does not reconcile the concrete sequential znode created by the prior attempt.

### 3. Fork

- **Remember the actual path:** store the path returned by sequential create in `Entry`; on reconnect check that exact path and recreate only after it is gone; unregister deletes the stored path.
- **Reconcile by service ID:** scan service children, deserialize each `ServiceInstance`, delete duplicates matching the local ID, and create only when none remains.

They diverge observably after a flap: the first preserves the existing znode name while its session survives; the second may choose or replace a canonical survivor and emit extra cache events.

Naive first implementation: add `EPHEMERAL_SEQUENTIAL` to the creation-mode switch while retaining ID-derived paths everywhere else, as HEAD does. The requirement that reconnect and unregister address the same concrete registration invalidates that representation and requires redesigning `Entry`, not extending the switch.

### 4. Fault and invariant

**Fault:** the client reaches `RECONNECTED` without session expiry, or loses the response after the server accepts an `EPHEMERAL_SEQUENTIAL` create.

**Invariant:** After recovery exactly one child deserializing to the locally registered service ID exists, and after `unregisterService()` no such child exists.

### 5. Tension

Forcing delete/recreate makes watchers reliably notice updates, while preserving a surviving sequential node avoids duplicate identities and unnecessary churn.

### 6. Determinism seam

Use `TestingServer`, a protected `internalRegisterService()` override, and the semaphore pattern already present at `curator-x-discovery/src/test/java/org/apache/curator/x/discovery/details/TestServiceDiscovery.java:65`. Concurrency is involved; no real network or fixed sleep is necessary if registration and connection-state latches are used.

### 7. Vocabulary check

- `ServiceDiscoveryImpl`, `Entry`, `ServiceInstance`, `DYNAMIC_SEQUENTIAL`, `RECONNECTED`, `registerService`, `unregisterService` — **ALREADY-IN-REPO** (`rg -n 'DYNAMIC_SEQUENTIAL|reRegisterServices|unregisterService|class Entry' curator-x-discovery/src`).
- `canonical survivor`, `concrete registration path` — **COINED-BY-YOU** (`rg -ni 'canonical survivor|concrete registration path' curator-x-discovery/src` finds none).

### 8. Size

Approximately 120–170 net lines across 3–4 files. Near the target, though the scan-and-reconcile implementation could exceed it.

## SURFACE 5 — CuratorCache initialization cannot be stranded by synchronous submission failure [NET-NEW CAPABILITY]

### 1. HEAD citation

`CuratorCacheImpl.nodeChanged()` increments `OutstandingOps` before scheduling `getData()` at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache/CuratorCacheImpl.java:220`. If builder validation or submission throws, the catch at `:226` only calls the exception handler. `OutstandingOps` invokes `initialized()` only when a decrement reaches zero at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache/OutstandingOps.java:40`.

The documented behavior says `initialized()` is called when initial nodes finish loading at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache/CuratorCacheListener.java:58`. Avoiding a permanently stranded count is **not fully implemented**.

### 2. Nearest presence

The closest existing cleanup is:

> `outstandingOps.increment();`  
> `client.getData().inBackground(callback).forPath(fromPath);`  
> `} catch (Exception e) {`  
> `    handleException(e);`  
> `}`

from `CuratorCacheImpl.java:220`. It reports the exception but fails to settle the incremented operation.

### 3. Fork

- **Always settle submission:** decrement in the synchronous failure path, allowing `initialized()` once all successfully submitted and failed initial operations settle.
- **Abort and restart the generation:** mark the current initial rebuild failed, discard its count, and permit a later `PersistentWatcher` reset to create a fresh `OutstandingOps` generation; emit `initialized()` only for a successful generation.

They diverge observably because the first may report initialization after an incomplete load, while the second withholds it until recovery succeeds.

### 4. Fault and invariant

**Fault:** schema validation throws synchronously after `outstandingOps.increment()` but before `getData().forPath()` queues its callback.

**Invariant:** A synchronous submission failure must not leave the cache permanently one outstanding operation away from either initialization or a recoverable new initialization attempt.

### 5. Tension

Callers must not wait forever, but `initialized()` must not falsely certify an incomplete cache.

### 6. Determinism seam

Deterministic without real network timing: configure a `SchemaSet` whose `watched` allowance rejects the cache’s un-watched `getData()` at `GetDataBuilderImpl.java:279`, use `withExceptionHandler()`, and observe `initialized()` with latches. A `TestingServer` is sufficient for watcher registration.

### 7. Vocabulary check

- `CuratorCache`, `OutstandingOps`, `initialized`, `PersistentWatcher`, `SchemaSet`, `withExceptionHandler` — **ALREADY-IN-REPO** (`rg -n 'OutstandingOps|initialized\\(|PersistentWatcher|withExceptionHandler' curator-recipes/src curator-framework/src`).
- `initialization generation`, `settled operation` — **COINED-BY-YOU** (`rg -ni 'initialization generation|settled operation' curator-recipes/src` finds none).

### 8. Size

About 90–140 net lines across 3 files: `CuratorCacheImpl`, `OutstandingOps`, and tests. In target band.

## SURFACE 6 — Merge TreeCache child metadata without regressing node data [NET-NEW CAPABILITY, WEAK]

### 1. HEAD citation

For a `CHILDREN` result, `TreeCache` replaces the cached `Stat` only if its `mzxid` matches the cached data’s `mzxid` at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache/TreeCache.java:373`. When they differ, child metadata such as `cversion`, `pzxid`, and `numChildren` is not incorporated.

The metadata-preserving behavior is **not fully implemented**. `TreeCache` is deprecated, making this surface weak.

The separate admission at `TreeCache.java:607`, `TODO: consider making public.`, concerns visibility of the unhandled-error listenable and does not concede a recovery-semantic gap.

### 2. Nearest presence

The still-current admission at `TreeCache.java:375` is verbatim:

> `// TODO consider doing update of cversion, pzxid, numChildren only`

It specifically concedes that the current all-or-nothing `Stat` replacement loses independently useful child metadata.

### 3. Fork

- **Field-wise merge:** retain the cached data and data-related stat fields while copying only `cversion`, `pzxid`, and `numChildren` from the children response.
- **Coherent reread:** reject the mixed response and issue another `getData()` so the cache installs one complete `Stat` from a later observation.

They diverge in listener latency and request count; field-wise merge updates child metadata immediately, while rereading may lag or starve under continuous mutation.

### 4. Fault and invariant

**Fault:** `GET_DATA` and `CHILDREN` responses for one node complete out of order while another client changes both its data and child set.

**Invariant:** The cached `ChildData` must never regress its newest data/mzxid while still eventually reflecting the newest observed child metadata.

### 5. Tension

Combining fields from separate observations improves freshness but weakens snapshot coherence; rereading preserves whole-stat coherence but adds failure and starvation opportunities.

### 6. Determinism seam

`TreeCache.Builder.setExecutor()` at `TreeCache.java:146` can control event publication, and `TestingServer` can drive data and child mutations. However, there is no existing latch between the two ZooKeeper response callbacks, so exact response reordering currently requires `Thread.sleep`/timing or a new test hook.

### 7. Vocabulary check

- `TreeCache`, `ChildData`, `Stat`, `mzxid`, `cversion`, `pzxid`, `numChildren`, `GET_DATA`, `CHILDREN` — **ALREADY-IN-REPO** (`rg -n 'mzxid|cversion|pzxid|numChildren|GET_DATA|CHILDREN' curator-recipes/src`).
- `field-wise merge`, `whole-stat coherence` — **COINED-BY-YOU** (`rg -ni 'field-wise merge|whole-stat coherence' curator-recipes/src` finds none).

### 8. Size

Roughly 100–160 net lines across 2–3 files. The reread version may exceed the target slightly.

## SURFACE 7 — Legacy caches become quiescent at close [NET-NEW CAPABILITY, WEAK]

### 1. HEAD citation

`NodeCache.close()` sets `CLOSED`, removes watchers, clears listeners, and nulls listener/watcher references at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache/NodeCache.java:163`; however, a queued result still enters `processBackgroundResult()` without checking state at `NodeCache.java:248` and can mutate `data` at `:281`.

`PathChildrenCache` has the stronger late-result guard at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache/PathChildrenCache.java:599`, plus synchronized submission explicitly justified as a close race at `:773`.

Quiescent close across both legacy caches is **not fully implemented**, principally in `NodeCache`. Both classes are deprecated, so this is weak.

### 2. Nearest presence

The `NodeCache.java:169` and `PathChildrenCache.java:396` TODOs remain at HEAD. Their shared text is:

> `// TODO`  
> `// This seems to enable even more GC - I'm not sure why yet - it`  
> `// has something to do with Guava's cache and circular references`

These admissions concern uncertain GC benefits of nulling callback fields, not a proven callback-order guarantee. The closest actual close-race admission is `PathChildrenCache.java:773`:

> `This method is synchronized because it has to check state about whether this instance is still open.`

### 3. Fork

- **Drop-after-close:** add state/generation checks to every callback before it mutates storage or schedules another read.
- **Drain-before-return:** track callbacks already accepted before close, let them finish and deliver their events, then clear listeners and return.

They diverge observably when a change was already in flight: the first drops it and closes quickly; the second delivers it before a potentially slower close returns.

### 4. Fault and invariant

**Fault:** a `GET_DATA` callback is queued, then `close()` completes before that callback runs.

**Invariant:** After `close()` returns, cached `ChildData` must not change, no new ZooKeeper read may be scheduled, and no cache listener may still be executing.

### 5. Tension

Fast nonblocking teardown conflicts with delivering all work accepted before close and waiting for user listener bodies.

### 6. Determinism seam

`NodeCache.rebuildTestExchanger` at `NodeCache.java:223` and replaceable executors in `PathChildrenCache` can coordinate in-flight listener work. Precisely pausing a `NodeCache` callback before its mutation has no current hook, so that half needs `Thread.sleep`/timing or a new latch. No real network is required beyond `TestingServer`; concurrency is required.

### 7. Vocabulary check

- `NodeCache`, `PathChildrenCache`, `ChildData`, `CLOSED`, `removeWatchers`, `rebuildTestExchanger` — **ALREADY-IN-REPO** (`rg -n 'rebuildTestExchanger|removeWatchers|State.CLOSED|ChildData' curator-recipes/src/main/java/org/apache/curator/framework/recipes/cache`).
- `quiescent close`, `callback generation` — **COINED-BY-YOU** (`rg -ni 'quiescent close|callback generation' curator-recipes/src` finds none).

### 8. Size

Approximately 90–140 net lines across 3–4 files. In target band, but deprecation materially lowers value.

## SURFACE 8 — PersistentNode close prevents a late create from becoming visible [NET-NEW CAPABILITY, REVERT-AND-REDO]

### 1. HEAD citation

A create callback arriving after close is handled by `processBackgroundCallbackClosedState()`, which schedules a guaranteed delete at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/nodes/PersistentNode.java:222`. `close()` itself only deletes the currently recorded `nodePath` at `PersistentNode.java:322`.

`createNode()` checks `isActive()` before waiting on `debugCreateNodeLatch`, but does not recheck after the latch at `PersistentNode.java:397`, so a create can be submitted after close and later compensated.

Eventual cleanup is implemented, but the stronger behavior “no node becomes visible after close returns” is **not fully implemented**.

### 2. Nearest presence

The existing compensation is verbatim at `PersistentNode.java:230`:

> `if (path != null) {`  
> `    try {`  
> `        client.delete().guaranteed().inBackground().forPath(path);`  
> `    } catch (Exception e) {`  
> `        log.error("Could not delete node after close", e);`  
> `    }`  
> `}`

It removes the late node eventually but permits a post-close visibility window.

### 3. Fork

- **In-flight barrier:** register each create before submission; close waits for its callback and then synchronously completes deletion before returning.
- **Serialized worker barrier:** route create/recreate/delete through one recipe executor and make close enqueue a final delete barrier and wait for it.

They diverge in where blocking occurs and whether multiple reconnect creates can be coalesced by the worker.

Naive first implementation: let the callback notice `CLOSED` and issue compensating deletion, as HEAD does. A requirement forbidding even transient post-close membership kills that design because compensation necessarily happens after visibility.

### 4. Fault and invariant

**Fault:** `close()` occurs after `createNode()` passed its active-state check but before its background create is submitted or acknowledged.

**Invariant:** Once `close()` returns, the managed znode must never subsequently become externally visible, even transiently.

### 5. Tension

A bounded, responsive close conflicts with waiting through connection recovery long enough to settle an ambiguous create.

### 6. Determinism seam

`debugCreateNodeLatch` at `PersistentNode.java:139`, `TestingServer`, and ZooKeeper’s testable session-expiration hook can stage the race. The latch has no companion “reached latch,” and existing tests use `debugWaitMsForBackgroundBeforeClose`/sleep at `PersistentNode.java:309`, so fully deterministic placement currently needs a small new hook.

### 7. Vocabulary check

- `PersistentNode`, `nodePath`, `backgroundCallback`, `guaranteed`, `debugCreateNodeLatch`, `CLOSED` — **ALREADY-IN-REPO** (`rg -n 'nodePath|backgroundCallback|guaranteed|debugCreateNodeLatch|CLOSED' curator-recipes/src/main/java/org/apache/curator/framework/recipes/nodes/PersistentNode.java`).
- `in-flight barrier`, `post-close visibility window` — **COINED-BY-YOU** (`rg -ni 'in-flight barrier|post-close visibility' curator-recipes/src` finds none).

### 8. Size

About 110–160 net lines across 2–3 files. Near the target; robust close-time timeout handling may push it slightly over.

## SURFACE 9 — One atomic increment cannot be replayed as two increments [NET-NEW CAPABILITY]

### 1. HEAD citation

`DistributedAtomicValue.tryOnce()` reads the current value, computes a new value, and uses ordinary create/set operations at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/atomic/DistributedAtomicValue.java:266`, `:274`, and `:276`. It does not request Curator’s existing idempotent operation handling.

If the server applies the write but the response becomes `CONNECTIONLOSS`, the builder retries with the old version, receives `BADVERSION`, and the recipe may recompute and apply the increment again. At-most-once recipe application is **not fully implemented**.

### 2. Nearest presence

The closest existing recovery mechanism is in `curator-framework/src/main/java/org/apache/curator/framework/imps/SetDataBuilderImpl.java:386`:

> `} catch (KeeperException.BadVersionException e) {`  
> `    if (!idempotent) {`  
> `        throw e;`  
> `    }`

It can classify an acknowledged-lost write as success, but the atomic recipe does not opt into it.

### 3. Fork

- **Builder-level idempotency:** use idempotent create/set with the read version and expected bytes, accepting the existing framework’s read-back classification.
- **Recipe-level conservative reconciliation:** after an ambiguous exception, reread the value/version; report success only for an exact expected transition, otherwise return `succeeded=false` without recomputing the delta.

They diverge if another client overwrites the value before reconciliation: builder-level retry may return to the optimistic loop and apply the delta again, while conservative reconciliation terminates unsuccessfully.

### 4. Fault and invariant

**Fault:** `failNextSetForTesting` converts a successful server `setData` response into `CONNECTIONLOSS`, optionally followed by an intervening writer.

**Invariant:** One call to `increment()` or `add(delta)` must never apply its delta more than once, regardless of whether the recipe can prove that the first write succeeded.

### 5. Tension

Continuing under contention maximizes successful updates, while refusing to replay an ambiguous transition preserves at-most-once application.

### 6. Determinism seam

`SetDataBuilderImpl.failNextSetForTesting` at `SetDataBuilderImpl.java:45` injects connection loss after the server mutation at `:407`; `CreateBuilderImpl.failNextCreateForTesting` provides the analogous initial-create seam. They are package-visible in the framework module, so a recipe-level test needs a small adapter or reflection, but no real network, sleep, or concurrency is required beyond `TestingServer`.

### 7. Vocabulary check

- `DistributedAtomicValue`, `AtomicValue.succeeded`, `tryOnce`, `RetryPolicy`, `idempotent`, `BADVERSION`, `CONNECTIONLOSS` — **ALREADY-IN-REPO** (`rg -n 'tryOnce|succeeded|idempotent|BADVERSION|CONNECTIONLOSS' curator-recipes/src/main/java/org/apache/curator/framework/recipes/atomic curator-framework/src/main/java/org/apache/curator/framework/imps`).
- `ambiguous transition`, `at-most-once application` — **COINED-BY-YOU** (`rg -ni 'ambiguous transition|at-most-once application' .` finds none).

### 8. Size

Roughly 100–150 net lines across 3 files, including cross-module fault tests. In target band.

## SURFACE 10 — Failed background queue puts settle flush accounting [NET-NEW CAPABILITY]

### 1. HEAD citation

`DistributedQueue.internalPut()` increments `putCount` before serialization at `curator-recipes/src/main/java/org/apache/curator/framework/recipes/queue/DistributedQueue.java:347`; a serializer exception therefore leaks the count. In the asynchronous callback, any non-`OK` result returns before decrementing it at `DistributedQueue.java:377`. `flushPuts()` waits while that count is positive at `:240`.

The behavior that every accepted or failed put reaches one accounting terminal state is **not fully implemented**.

### 2. Nearest presence

The closest terminal handling at `DistributedQueue.java:377` is:

> `if (event.getResultCode() != KeeperException.Code.OK.intValue()) {`  
> `    return;`  
> `}`

Only the `OK` path reaches:

> `putCount.decrementAndGet();`  
> `putCount.notifyAll();`

at `DistributedQueue.java:383`, leaving failure and submission-exception paths unsettled.

### 3. Fork

- **Per-put completion token:** create an exactly-once completion object before serialization and settle it from serialization failure, submission failure, every terminal callback, or close; success listeners run only for `OK`.
- **Central close/drain accounting:** retain the shared counter, decrement on terminal callbacks, and have close atomically cancel and settle all registered background puts not yet completed.

They diverge before close: the token design lets `flushPuts()` complete after a failed put, while centralized cancellation may leave it blocked until close.

### 4. Fault and invariant

**Fault:** `QueueSerializer.serialize()` throws after `putCount` increments, or the background create callback returns a terminal non-`OK` result.

**Invariant:** Each put must settle `putCount` exactly once, `flushPuts()` must not remain blocked by a terminally failed put, and no success listener may run for that failure.

### 5. Tension

Flush must account for failed work promptly, but background callbacks may race with close and must not decrement or notify twice.

### 6. Determinism seam

A throwing `QueueSerializer` exercises the synchronous case without network or timing. For the callback case, `internalCreateNode()` is `@VisibleForTesting` at `DistributedQueue.java:401` and is already overridden with a latch in `curator-recipes/src/test/java/org/apache/curator/framework/recipes/queue/TestDistributedQueue.java:640`; a direct executor removes scheduler timing.

### 7. Vocabulary check

- `DistributedQueue`, `QueueSerializer`, `putCount`, `flushPuts`, `QueuePutListener`, `CuratorEvent`, `OK` — **ALREADY-IN-REPO** (`rg -n 'putCount|flushPuts|QueuePutListener|QueueSerializer|Code.OK' curator-recipes/src/main/java/org/apache/curator/framework/recipes/queue`).
- `completion token`, `accounting terminal state` — **COINED-BY-YOU** (`rg -ni 'completion token|accounting terminal' curator-recipes/src` finds none).

### 8. Size

Approximately 90–130 net lines across 2 files when implemented as explicit completion accounting plus tests. In target band.

## SURFACE 11 — CONTROL: JSON service-instance compatibility across versions [ALREADY-IMPLEMENTED]

### 1. HEAD citation

`JsonInstanceSerializer` configures Jackson to ignore unknown properties by default at `curator-x-discovery/src/main/java/org/apache/curator/x/discovery/details/JsonInstanceSerializer.java:69`. In compatibility mode it serializes `OldServiceInstance`, omitting `enabled`, at `JsonInstanceSerializer.java:89`.

Tests verify future unknown fields are accepted at `curator-x-discovery/src/test/java/org/apache/curator/x/discovery/details/TestJsonInstanceSerializerCompatibility.java:142`.

This compatibility behavior is **already fully implemented**.

### 2. Nearest presence

The class documentation states verbatim at `JsonInstanceSerializer.java:41`:

> `the default behavior of JsonInstanceSerializer`  
> `has been changed to NOT serialize the enabled field.`

This directly records the existing compatibility choice and its sacrificed field.

### 3. Fork

- **Down-level writer:** compatibility mode emits the old DTO shape, allowing strict pre-CURATOR-275 readers but losing `enabled`.
- **Tolerant reader:** emit the current `ServiceInstance` shape and require readers to ignore unknown fields.

They diverge when `enabled=false`: the down-level representation reads back as the default `true`, while the current representation preserves `false` but breaks strict old readers.

### 4. Fault and invariant

**Fault:** a new writer serializes an instance with `enabled=false` for a strict pre-CURATOR-275 reader.

**Invariant:** In compatibility mode the old reader must deserialize every legacy field without an unknown-property failure, even though `enabled` is intentionally lost.

### 5. Tension

Backward readability by strict clients conflicts with preserving newly introduced fields.

### 6. Determinism seam

Pure byte-array serialization tests; no network, wall clock, or concurrency is required. The package-visible `failOnUnknownProperties` constructor at `JsonInstanceSerializer.java:69` supplies the strict-reader seam.

### 7. Vocabulary check

- `JsonInstanceSerializer`, `OldServiceInstance`, `ServiceInstance`, `enabled`, `compatibleSerializationMode`, `FAIL_ON_UNKNOWN_PROPERTIES` — **ALREADY-IN-REPO** (`rg -n 'OldServiceInstance|enabled|compatibleSerializationMode|FAIL_ON_UNKNOWN_PROPERTIES' curator-x-discovery/src`).
- No coined vocabulary is needed for the observable contract.

### 8. Size

Already implemented. A compatibility extension or expanded matrix would be roughly 60–100 net lines across 2 files, slightly below the preferred band.

## SURFACE 12 — CONTROL: Deterministic precedence for overlapping schemas [ALREADY-IMPLEMENTED]

### 1. HEAD citation

`SchemaSet` documents exact-path precedence followed by first matching regex in constructor order at `curator-framework/src/main/java/org/apache/curator/framework/schema/SchemaSet.java:100`. Its cache loader iterates `regexSchemas` in that order and returns the first match at `SchemaSet.java:47`; `getSchema()` checks `pathToSchemas` first at `:148`.

That precedence behavior is **already fully implemented**.

### 2. Nearest presence

The current contract is verbatim:

> `Schemas are matched in a well defined order:`  
> `1. Exact match on full path (i.e. non-regex)`  
> `2. Match on the first regex path, searched in the order given to this constructor`

at `SchemaSet.java:100`.

### 3. Fork

- **Ordered first-match:** retain HEAD’s exact-first, then caller-order regex selection.
- **Reject ambiguity:** detect overlapping exact/regex or regex/regex rules during `SchemaSet` construction and reject configurations that could select more than one schema.

They diverge observably for overlapping regexes: the first returns whichever appears first, while the second fails before any operation executes.

### 4. Fault and invariant

**Fault:** a path matches an exact schema and multiple regex schemas with conflicting `Allowance` values.

**Invariant:** Schema selection must be deterministic: the exact schema wins, otherwise the first matching regex in constructor order wins.

### 5. Tension

Ordered overlap supports deliberate fallback rules, while rejecting overlap catches accidental policy ambiguity early.

### 6. Determinism seam

Pure construction and `getSchema()` calls are sufficient; no ZooKeeper server, network, clock, or concurrency is required. Existing ordering coverage begins at `curator-framework/src/test/java/org/apache/curator/framework/schema/TestSchema.java:215`.

### 7. Vocabulary check

- `SchemaSet`, `Schema`, `pathToSchemas`, `regexSchemas`, `Allowance`, `getSchema` — **ALREADY-IN-REPO** (`rg -n 'pathToSchemas|regexSchemas|Allowance|getSchema' curator-framework/src/main/java/org/apache/curator/framework/schema`).
- `overlap ambiguity` — **COINED-BY-YOU** (`rg -ni 'overlap ambiguity' curator-framework/src` finds none).

### 8. Size

Already implemented. Switching to ambiguity rejection with useful diagnostics would be about 80–120 net lines across 2 files.
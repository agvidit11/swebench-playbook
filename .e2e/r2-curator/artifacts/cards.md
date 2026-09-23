# A2 candidate cards — apache/curator @ `88dee99a85921bd0f20955e1d7efbaf896fc17f3`

**Runner: Claude.** Authorship lane declared per `00-ROUTER.md` §5 and `A2` §8 step 2:
**contracts only, no prose.** Nothing in this file is contract text and nothing here is to be
pasted into `instruction.md`. The `Interface Contract` tables are the deliverable in place of
prose; `B2` writes the contract, owned by Avocado.

Surface derivation (`A2` §2): 53,038 non-test LOC → band 15k–60k → **10–12 surfaces**. Subsystem
cross-check: 13 modules, so the LOC band and the subsystem count agree; no adjustment.
**Two independent surveys were run** (MetaCode and Codex, same `survey.txt`, 9,293 bytes,
sha `120c3a0c3306`) precisely so that convergence could be measured — per `ROUND2-FEEDBACK.md`,
convergence is a fork-strength **warning**, not a confidence signal.

- MetaCode returned **12** surfaces (10 lensed + 2 CONTROL): `/tmp/curator-run/survey-mc.out`
- Codex returned **12** surfaces (10 lensed + 2 CONTROL): `/tmp/curator-run/survey-cx.out`

**Convergence measured (the warning signal):** 4 pairs converged —
MC1≈CX2 (ConnectionStateManager bounded queue), MC2≈CX1 (LOST-after-repair hack),
MC4≈CX4 (ServiceDiscovery re-registration), MC9≈CX9 (DistributedAtomicValue ambiguous write).
**All four are down-weighted on that basis alone**, and three of them die on other gates anyway.

Cards written: **2**. Derivation: 24 surfaces → 24 collapsed via the merge table below → 2 cards.
That is inside the expected 15–20-surfaces-to-2–4-candidates ratio (`A2` §2). It is **under** the
≥8 dispatch target and I am **not backfilling** — the reason is `friction.md` F3/F4: this repo's
121 open issues are bulk-imported Apache JIRA tickets carrying full diagnoses and, in several
cases, patches in the comments, so the disclosure gate removes whole subsystems at once.

---

# MERGE TABLE — every surface to a card, or killed with the rule that killed it

| # | Surface | Disposition |
|---|---|---|
| MC1 / CX2 | `ConnectionStateManager` bounded `eventQueue` drops oldest on overflow | **KILLED.** Converged across both surveys (warning). Observable is "which subsequence survives an overflow" = backpressure/drop-policy; corpus saturation on `backpressure` is **380 peer tasks** (`R6` Part B saturation table). Three-word recall test: "drop oldest". |
| MC2 / CX1 | LOST-after-repair "hack" (`ConnectionStateManager:262-267`, CURATOR-525) | **KILLED at GATE 3.** Converged (warning) **and** disclosed: open issue **#740 / CURATOR-220 "LOST state is sometimes not reported to ConnectionStateListener"**, plus the `CURATOR-525` marker is inline in the source at `ConnectionStateManager.java:262`. Inline issue markers measure per-file disclosure density; this line is the densest in the file. |
| MC3 | `CircuitBreakingConnectionStateListener` — what the shielded listener may conclude when the circuit closes | **PARKED as card C2.** Zero disclosure (`CircuitBreaking` → 0 issues, `DownInstancePolicy`-grade clean). Best harness-ability in the repo: `CircuitBreaker.build(retryPolicy, service)` takes an injectable `ScheduledExecutorService`, so **no ZooKeeper server at all**. Held as the fallback if C1 dies at the probe. Residual worry: the noun is "circuit breaker", which is a three-word-recallable mechanism even though the *contract* is about listener state reconciliation, not the breaker. |
| MC4 / CX4 | `ServiceDiscoveryImpl.reRegisterServices()` aborts the fan-out on first failure; runs on the `ConnectionStateManager` event thread | **KILLED at GATE 3 — hard kill.** Open issue **#840 / CURATOR-320** states the diagnosis verbatim ("*Causing the reRegisterServices() method to be run on ConnectionStateManager thread… the RECONNECTED event in the queue will fire and reRegisterServices() will rerun… It deletes and recreates the node. Effectively causing the services to thrash up and down*") and its **comments carry a posted patch** introducing `reRegisterExecutor` / `reRegisterFuture` / `reRegisterRetryCount`, with the maintainer replying "*can you please create a PR with your change?*". Also converged across both surveys. This was **my own strongest independently-derived candidate** and the gate is what killed it. |
| MC4b | `internalRegisterService` delete-then-recreate is non-atomic (instance vanishes if the session dies in the gap) | **KILLED at GATE 3.** Same issue #840 body covers it explicitly. |
| MC4c | `STATIC`/`PERMANENT` registrations should not be re-registered | **KILLED at GATE 3.** Open issue **#615 / CURATOR-94** proposes the exact change with code. |
| MC5 | `DownInstanceManager` error classification — transport errors vs instance errors | **RE-CUT into card C1.** The classification half is dead as posed: `ServiceProvider.noteError(instance)` takes no throwable, so classification requires a new overload = `expose_interface`, corpus rate 1 passed / 13 failed. **But the file was the right place** — see C1, which is about *identity* rather than classification and needs no new public symbol. |
| MC6 | `CuratorCacheImpl.rebuild()` — phantom delete/create and stale-generation reads | **KILLED at GATE 2 (hollow-premise-adjacent) + GATE 3 (shipped test).** The repo ships `TestCuratorCacheConsistency`, which builds a `listenerDataMap` purely from listener events, kills 2 of 5 cluster members mid-run, and then asserts the listener map, the cache storage and actual ZK all agree — i.e. **the repo already asserts the invariant** and `A3` GATE 3 is explicit that a shipped test means the direction is public. Kept as a near-miss: a genuine narrower hole survives (`putStorage` compares only `Stat.getVersion()`, and a node deleted-and-recreated while disconnected returns to version 0, so the change is invisible to listeners; `getCzxid` appears **0 times** in all of `src/main`). Not built because the fix is a single comparison — `N04` anti-overcorrection, under ~20 lines. |
| MC7 | `PathChildrenCache` delivers `CONNECTION_RECONNECTED` before the refresh it triggered completes | **KILLED at GATE 3.** Issue **#816 / CURATOR-296 "Notify cache listeners when re-init completes after reconnect"** is the direction, by title, with a maintainer assignee and `resolution: Fixed`. A closed issue that *names the remedy* is still disclosure. |
| MC8 | `DistributedQueue` `processNormally` deletes before processing; `REQUEUE` loses the message if the consumer crashes in the gap | **KILLED.** Three-word recall test: "at-least-once delivery" / "exactly-once delivery". Also partly disclosed by open **#1122 / CURATOR-605** (`processWithLockSafety` double-delivery on consumer session death). |
| MC9 / CX9 | `DistributedAtomicValue` cannot classify an ambiguous write; `increment()` can apply twice | **KILLED at GATE 6 [R05].** Converged (warning), and fatal: Curator **already ships** the remedy as a public library export — `Idempotentable.idempotent()` on `CreateBuilder`/`SetDataBuilder`, with `IdempotentUtils.matches()` doing the read-back classification (`curator-framework/.../imps/IdempotentUtils.java`). Codex's own card says it: "*It can classify an acknowledged-lost write as success, but the atomic recipe does not opt into it.*" The reference answer is callable from inside the solution. R05 forbids it. |
| MC10 | `SharedValue` notification is not version-fenced; concurrent re-reads over-notify | **KILLED.** `notifyListeners()` re-reads `getValue()` rather than using the callback's own bytes — real, but the fix is moving one expression; `N04`, under ~20 lines. |
| MC11 | CONTROL — `NamespaceImpl` lazy namespace-root creation races itself | **Dropped.** Control surface; no fork, and the race is benign (`NodeExists` is caught). |
| MC12 | CONTROL — `PersistentTtlNode` touch schedule loses to TTL expiry under pause | **Dropped.** Disclosed: open **#1152 / CURATOR-636 "Make PersistentTtlNode initialDelay more configurable"**. Also wall-clock-dependent → `R09`. |
| CX3 | Exactly-once terminal callbacks for queued operations during client close | **Dropped — Codex marked it `ALREADY-IMPLEMENTED` itself.** Honest negative, recorded. |
| CX5 | `CuratorCache` initialization stranded by synchronous submission failure | **KILLED.** `OutstandingOps.increment()` then a throwing submission leaks the count so `initialized()` never fires — real, but single-family (wrap in try/finally) and ~10 lines. `N04`, and GATE 1 pre-filter 1: one implementation family = fork zero. |
| CX6 | Merge TreeCache child metadata without regressing node data | **Dropped — Codex labelled it WEAK itself.** Also disclosed: `TreeCache.java:375` `// TODO consider doing update of cversion, pzxid, numChildren only` is an inline admission that is *also* a published statement of the direction. |
| CX7 | Legacy caches become quiescent at close | **Dropped — Codex labelled it WEAK.** Disclosed: open **#938 / CURATOR-418 "ServiceCacheImpl.close() should be idempotent"** and **#678 / CURATOR-157**. |
| CX8 | `PersistentNode.close()` permits a late create to become transiently visible | **KILLED at GATE 6 [R09].** The invariant ("once `close()` returns the znode must never become visible, even transiently") is genuinely good, but Codex's own determinism field concedes it: "*The latch has no companion 'reached latch', and existing tests use `debugWaitMsForBackgroundBeforeClose`/sleep at `PersistentNode.java:309`, so fully deterministic placement currently needs a small new hook.*" A contract whose assertion needs a new test-only lifecycle hook is an `A2` §5 design smell and an `R09` determinism failure. |
| CX10 | `DistributedQueue.internalPut` leaks `putCount`, so `flushPuts()` can block forever on a failed put | **KILLED at GATE 1 pre-filter 1 + N04.** Genuinely broken and genuinely undisclosed (`flushPuts` → **0** issues, searched). But: `putCount.incrementAndGet()` at `:347` then `ItemSerializer.serialize` throws, and the background callback `return`s on non-`OK` at `:377` without decrementing. Every repair is the same family — settle the counter on all terminal paths. One implementation family = fork zero, and it is ~15 lines. |
| CX11 | CONTROL — JSON service-instance compatibility across versions | **Dropped — Codex marked `ALREADY-IMPLEMENTED`.** |
| CX12 | CONTROL — deterministic precedence for overlapping schemas | **Dropped — Codex marked `ALREADY-IMPLEMENTED`.** |

**Auto-rejects applied by rule (`A2` §6):**
- three-word recall test: MC1 ("drop oldest"), MC8 ("exactly-once delivery"), and it is the
  standing worry against C2 ("circuit breaker").
- existing-vocabulary test: passed by both surviving cards — see each card's Interface Contract,
  where every asserted token is IN-BASE.
- `N04` under ~20 lines: MC6 (narrow form), MC10, CX5, CX10.
- coined-observability auto-reject: no card's deliverable is a ledger/census/manifest/audit record.

---

# CARD C1 — Down-instance exclusion must survive a registration record being re-published

**Composition.** C-axis: *failure-atomic behaviour and error classification under injected fault*
(the `ROUND2-FEEDBACK.md` lever 1, failure-injection contract) × A-shape: **P6 revert-and-redo**,
with **lever 2 (two requirements pulling against each other) inside step 1**.
`R6` instantiation count for P6: 2 recorded (both rom-rb, neither built), so P6 is **not** at its
~3 self-collision ceiling. Domain (service discovery / endpoint health attribution) does not
collide with either rom-rb instantiation (plugin lifecycle, prepared commands).

**Module.** `curator-x-discovery`. Explicitly outside the burned zone — the shortlist's adjacency
warning bans `recipes/locks` and `recipes/leader`, and names `curator-x-discovery` "the
least-mined corner of the repo".

## HEAD citation and nearest presence

`curator-x-discovery/src/main/java/org/apache/curator/x/discovery/details/DownInstanceManager.java:33`

```java
private final ConcurrentMap<ServiceInstance<?>, Status> statuses = Maps.newConcurrentMap();
```

The map is keyed by the **whole `ServiceInstance` object**. `ServiceInstance.equals()` /
`hashCode()` (`ServiceInstance.java`, both methods) compare **all ten fields**: `name`, `id`,
`address`, `port`, `sslPort`, `payload`, `registrationTimeUTC`, `serviceType`, `uriSpec`,
`enabled`. So the identity used for error attribution is the *entire serialized record*, and any
change to any field is a different key.

`add()` at `:46-53` and `apply()` at `:55-61` both look the instance up by that key.
`ServiceProviderImpl.noteError()` at `:130-131` is the only feed: `downInstanceManager.add(instance)`.

**Is it already implemented?** No — and this is not a grep conclusion. See the executed
reproduction below.

**Nearest presence, verbatim.** The closest existing thing to "identity that survives
re-publication" is the whole-record key itself plus the time-based `purge()` at `:63-82`:

```java
long elapsedMs = System.currentTimeMillis() - entry.getValue().startMs;
if (elapsedMs >= downInstancePolicy.getTimeoutMs()) { it.remove(); }
```

That covers *expiring* a down-marking on a timer. It fails to cover *retaining* one across a
record update: the entry is not expired, it is simply never found again, because the lookup key
changed. The distinction matters — the exclusion does not lapse, it is **laundered**.

## GATE 2 — executed reproduction at `base_commit` (not a grep)

Harness `/tmp/curator-run/curator/curator-x-discovery/src/test/java/org/apache/curator/x/discovery/details/ZZRepro.java`
(scratch only, deleted before any commit), run inside `maven:3.9-eclipse-temurin-17`:
`mvn -B -pl curator-x-discovery test -Dtest=ZZRepro` → `Tests run: 4, Failures: 0` (the harness
prints, it does not assert). Observed output:

```
REPRO-A  apply(before) before any error      = true
REPRO-B  apply(before) after noteError       = false
REPRO-C  apply(after)  after noteError       = true      <-- payload update cleared the exclusion
REPRO    before.equals(after)                = false
REPRO    hash(before)==hash(after)           = false
REPRO-D  apply(first)  after noteError       = false
REPRO-E  apply(second) after noteError       = true      <-- registrationTimeUTC change cleared it
REPRO-F  apply(enabled=true)  after error    = false
REPRO-G  apply(enabled=false) after error    = true      <-- enabled flag toggle cleared it
REPRO-H  apply(oldEndpoint) after error      = false
REPRO-I  apply(newEndpoint) after error      = true      <-- distinct endpoint unaffected (correct today)
```

`REPRO-C`, `-E` and `-G` are the defect: same name, same id, same address, same port, and the
instance is back in rotation. `REPRO-I` is the property that today works **by accident** of the
whole-record key, and that the obvious repair destroys.

## Probe declarations — fixed BEFORE any probe, per `A3` GATE 5 pre-check ①

> **NOTE ON TIMING, stated so the record is honest.** These three fields were added at 17:20,
> *after* the first 15 probes had already run. `A3` was rewritten mid-run (commit `e744c14`,
> "A3: fix the instrument that produced two invalid kills") and `tools/probe-lint.py` was created
> at 17:01 — both **after** my probes executed at 16:52–17:00. The direction below is nonetheless
> the one recorded in this card's own "Named wrong shape" section from the start (key by
> `getId()` = the wrong shape), so it is not being read off the outputs. See `friction.md` F10.

CONSTRAINT: When a caller reports a service instance as failing through the service provider, that instance must stay out of the results the provider returns for the configured down-instance window, and must continue to stay out for the rest of that window even if the instance re-publishes its registration record during the window — for example when its owner updates the payload it advertises, when its enabled flag is toggled, or when the service cache rebuilds its record objects after a reconnect. At the same time, two instances that are concurrently registered under the same instance id at different network endpoints are different instances, and reporting errors against one of them must not keep the other one out of the results.

DESIRED: Error attribution is scoped to the network endpoint — the stable tuple of service name, instance id and the address and ports the instance advertises — so that mutable descriptive metadata is excluded from the comparison while a move to a different address or port is treated as a different instance.

NON-DESIRED: Error attribution keyed on the instance id alone, or on name plus id, so that a replacement or sibling at a different address or port inherits the exclusion; or attribution left keyed on the whole record so that any metadata change clears it; or clearing the exclusion whenever the record changes at all.

## The two requirements that pull against each other — this is the difficulty

| | Requirement | What it forbids |
|---|---|---|
| **R-a** | An instance reported as failing stays excluded for the policy window even if its registration record is re-published (payload update, `enabled` toggle, a cache rebuild after reconnect regenerating the POJO). | Keying on the whole record. |
| **R-b** | Two instances that are concurrently registered under the **same instance id** at different endpoints are independent; excluding one must not exclude the other. | Keying on `getId()`. |

**Neither extreme satisfies both.** HEAD sits at one extreme and fails R-a; the universally
obvious repair (key by `getId()`) sits at the other and fails R-b. The task is finding the
identity in between, and R-b is not folklore — Curator's own `ServiceType.DYNAMIC_SEQUENTIAL`
(`ServiceDiscoveryImpl.java:219-221`, `CreateMode.EPHEMERAL_SEQUENTIAL`) exists precisely so that
one id can be live more than once.

## Step breakdown

**Step 1 — identity.** Down-marking survives re-publication of a record (R-a) while distinct
concurrently-live endpoints under one id stay independent (R-b).
*Compositional invariant:* an error report and the filter decision that consumes it agree on
what "the same instance" means, for every field an owner may legitimately change while running.
*Tension:* R-a vs R-b above.

**Step 2 — the revert.** Constraint: *an error reported against a registration that has since
been superseded must not be attributed to the registration that replaced it at the same endpoint.*
A caller can hold an instance across a timeout and report it long after the process behind that
address and port has been replaced.

*Why this reverts rather than extends.* Step 1's only viable artifact is a key that deliberately
**excludes** `registrationTimeUTC`, because including it is exactly what fails R-a. Step 2 needs
that same field to decide whether a late report predates the current registration. The one value
step 1 had to drop is the one step 2 needs, so the single value-equality key cannot be widened —
`Status` (today `startMs` + an `AtomicInteger`) has to carry a registration boundary per endpoint,
and the error has to be stamped with the reporter's view. Step 1's structure is torn out.

*Step-2 tension:* a late report is real evidence the caller was failed, versus a late report must
not punish a process that was not running when the failure happened.

## Interface Contract — every symbol the graded tests touch

| Symbol | Kind | Shape | Reachability | Alternatives |
|---|---|---|---|---|
| `ServiceProvider.noteError(ServiceInstance<T>)` | method | `void` | **IN-BASE** (`ServiceProvider.java`) | PINNED — existing public API |
| `ServiceProvider.getAllInstances()` | method | `Collection<ServiceInstance<T>>` | **IN-BASE** | PINNED |
| `ServiceProvider.getInstance()` | method | `ServiceInstance<T>` | **IN-BASE** | PINNED |
| `ServiceProviderBuilder.downInstancePolicy(DownInstancePolicy)` | builder method | fluent | **IN-BASE** (`ServiceProviderBuilder.java`) | PINNED |
| `DownInstancePolicy(long, TimeUnit, int)` | ctor | — | **IN-BASE** | PINNED |
| `ServiceInstanceBuilder.registrationTimeUTC(long)` | builder method | fluent | **IN-BASE** (`ServiceInstanceBuilder.java`) | PINNED — and this is the determinism seam |
| `ServiceInstance.getId/getAddress/getPort/getPayload` | accessors | — | **IN-BASE** | PINNED |
| `InstanceFilter<T>.apply(ServiceInstance<T>)` | method | `boolean` | **IN-BASE** (`InstanceFilter.java`) | PINNED |

**No COINED token is required by any graded assertion.** GATE 0 therefore passes without an
override — the whole contract is expressible through `ServiceProvider`'s existing public surface.
Nothing new is named, so there is nothing for `B2` to pin and nothing for `B3` to over-narrow.

*Observable Schema (`A2` §5): N/A.* The deliverable is not a collection of records — it is a
`boolean`-valued exclusion decision observed through an existing `Collection` return. Container,
element, field names and value domain are all pre-existing.

## Named wrong shape, and why a capable model writes it

**Wrong shape:** key `statuses` by `instance.getId()`.
**Why a capable model writes it:** it is the minimal edit that makes the reported symptom go away,
`getId()` is the field the Javadoc calls the instance's identity, and `ServiceDiscoveryImpl`
itself keys its own `services` map by exactly that (`ServiceDiscoveryImpl.java:65`,
`ConcurrentMap<String, Entry<T>> services`, written to with `services.put(thisInstance.getId(), …)`
at `:130`). So the repo's own adjacent idiom actively recommends the wrong answer. It fails R-b
and regresses `REPRO-I`, which is measured to hold at HEAD today.

## Motivating caller

A service fleet that publishes mutable metadata on its discovery record — Curator supports this
directly via `ServiceDiscovery.updateService()` and the `payload` field, and
`ServiceDiscoveryImpl.makeNodeCache()` (`:410-443`) exists solely to watch registered instances for
externally-applied changes. Any operator using that feature, plus `DownInstancePolicy`, currently
has a health-exclusion mechanism that a routine metadata update silently resets. The `enabled`
flag (added by CURATOR-275, "Allow service instances to be disabled temporarily") makes it sharper:
disabling and re-enabling an instance also clears its error history.

## Determinism seam [R09]

`ServiceInstanceBuilder.registrationTimeUTC(long)` is a **pre-existing public setter for the only
clock-derived field in the identity**, so every identity assertion is driven by literal values and
needs no clock, no sleep and no scheduler. The wall-clock parts of `DownInstanceManager` — the
`purge()` throttle at `:66` and the `startMs` window — are **deliberately excluded from both
steps**; this card grades identity and attribution, never expiry timing. The existing
`TestDownInstanceManager.testExpiration` uses `Thread.sleep` and is the reason to stay away from
the window. `DownInstanceManager` itself is pure in-memory (`ConcurrentMap` + `AtomicInteger` +
`AtomicLong`), so the unit-level assertions need **no ZooKeeper server**; the end-to-end
`ServiceProvider` assertions use the in-process `TestingServer` the module already depends on.

## Inter-step file overlap

Both steps touch `DownInstanceManager.java`; step 2 also touches `ServiceProviderImpl.java`.
Heavy overlap, which is the P6 signature and a yellow flag, not a disqualifier: it tells `B1`
that **step 2 must be authored as a delta on step 1, not as a second patch from base**.

## Step-1 guard cases owned by step 2

| Step-1 invariant | Step-2 `fail_to_pass` case that would fail if it regressed |
|---|---|
| R-a: payload republication does not clear an exclusion | step 2's late-report test republishes the payload before the late report; if R-a regressed the instance would already be back in rotation and the late-report assertion could not distinguish |
| R-b: same id at two live endpoints stays independent | step 2's supersession test registers a replacement at a *different* endpoint in the same scenario; an id-keyed step 2 fails it |

Step 1's `fail_to_pass` ids are **not** reused as step 2's `pass_to_pass`; step 2 gets its own
cases that exercise the same invariants inside a supersession scenario.

## Size

Step 1 ~40–60 net lines across 1–2 files. Step 2 ~60–90 net lines across 2 files. Combined
**~100–150 net lines across 2–3 files** — in the 80–150 band. Primitives reused: `ConcurrentMap`,
`AtomicInteger`, `InstanceFilter`, `DownInstancePolicy`.

## Predicted per-arm rate

Step 1: avocado 2–3/5 (the R-a/R-b conflict is the whole difficulty and R-b has no symptom unless
you look for it), opus ≥3/5, gpt ≥3/5. Step 2: avocado 1–2/5.
**What stops avocado passing step 1 outright?** R-b. A solver that reads only the reported symptom
writes the id-keyed fix and regresses a `pass_to_pass` case that holds at HEAD.
**This is the number the probe must measure, not the number I argue.** Measured result recorded in
`HANDOFF A3`.

## Self-audit (`A2` §7) — 13 card-stage items, 4 deferred

| Item | Verdict | Evidence |
|---|---|---|
| R01 observable contract | PASS | every assertion runs through `ServiceProvider.getAllInstances()` / `getInstance()`. *What nearly failed it:* I first drafted this around `DownInstanceManager.apply()`, which is package-private — that would have graded internal state. Moved the observable up to `ServiceProvider`. |
| R02 symbols reachable | PASS | Interface Contract table, all rows IN-BASE. *What nearly failed it:* MC5's classification cut needed `noteError(instance, throwable)`, a new public overload. Dropped that cut for exactly this reason. |
| R04 no mechanism naming | PASS | contract states which instances must be excluded; never says "key the map by X". |
| R05 no library-export leak | PASS | no Curator export computes endpoint identity. Contrast MC9, killed here because `Idempotentable.idempotent()` *is* that export. |
| R06 adversarial case for every "never" | PASS | "must not exclude the replacement" → `REPRO-I` is the written adversarial case and it is measured at HEAD. |
| R07 realism | PASS | `updateService()` + `payload` + `enabled` are shipped features; the interaction is between two shipped features. |
| R08 spec/grader width | PASS | spec is open on mechanism, tests assert only the `ServiceProvider`-visible decision. *What nearly failed it:* I considered asserting that the two endpoints get *separate* `Status` objects — a white-box pin. Dropped. |
| R09 determinism | PASS | `registrationTimeUTC(long)` is a pre-existing injectable value; expiry timing deliberately out of scope. |
| R11 scope | PASS | ~100–150 net lines, 2–3 files. |
| N01 | PASS | fault-conditioned behaviour, not a formatting or ergonomics change. |
| N02 | PASS | premise verified by execution, not by grep. |
| N03 | PASS | not an invented observability surface; the observable is an existing `boolean` decision. |
| N04 anti-overcorrection | PASS | above the ~20-line floor, and does not compose two shipped functions. |
| R03 seam | **DEFERRED** → decided by the `A3` GATE 6 seam test and the step-1-gold-against-step-2-tests run in `B3`. |
| R10 | **DEFERRED** → needs a build. |
| R12 | **DEFERRED** → needs a build. |
| R13 | **DEFERRED** → needs rollouts. |

**Non-PASS row / named residual risk (mandatory).** Two, stated honestly:

1. **The contract may be the solution.** If `B2` states R-a and R-b as plainly as this card does,
   "identity = (name, id, address, port, sslPort)" is a short walk from the two sentences. That is
   `A3` GATE 1's fork-collapse test and it is the most likely way this card dies. It is precisely
   what the n=5 probe is for, and the probe is deliberately phrased with **both** requirements
   stated, per `A3` GATE 5 rule 3 (probe step 2 *with* the constraint stated; un-volunteered ≠
   un-executable).
2. **Step 2's supersession constraint has no documented source** — it is the known P6 weakness
   (`R6` §P6, "agents invent operational callers and that is consistently the weakest part of the
   candidate on realism"). The late-report scenario is plausible but I did not find it stated
   anywhere in the repo or its issues, so realism on step 2 is weaker than on step 1.

---

# CARD C2 — Fallback, held unprobed: what a shielded listener may conclude when the circuit closes

Recorded so the run is not single-threaded on C1. **Not promoted, not probed** — it is the
fallback if C1's probe kills it. Fields are therefore partial and it is not offered as a survivor.

**Composition.** Same C-axis; A-shape P8 error classification / recoverability (`R6` "other
candidate patterns", unproven, zero instantiations — so zero self-collision).

**HEAD citation.** `curator-framework/.../state/CircuitBreakingConnectionStateListener.java:188-192`

```java
private synchronized void closeCircuit() {
    ConnectionState stateToSend = (circuitLastState == circuitInitialState) ? null : circuitLastState;
    reset();
    callListener(stateToSend);
}
```

and `handleOpenStateChange` at `:152-162`, which records `circuitLastState = newState` and forwards
nothing while the circuit is open, except the first `SUSPENDED`→`LOST` transition.

**The fault and the invariant.** Fault: the connection flaps faster than the breaker's
`RetryPolicy` delay, so `RECONNECTED` transitions are absorbed. Invariant: when the circuit
closes, the managed listener's last observed state must correctly classify current connectivity —
it must never be left believing it is disconnected while the client is connected.

**Why it is held rather than built.** Two reasons. (a) The noun is "circuit breaker", which fails
the spirit of the three-word recall test even though the contract is about listener state
reconciliation rather than the breaker mechanism. (b) MetaCode's own size estimate is 60–100 net
lines — the lower edge of the band, `N04` risk.

**Why it is worth holding.** Zero disclosure (`CircuitBreaking` → 0 issues; the class is named in
no open or closed issue). And the best harness in the repo by a distance:
`CircuitBreaker.build(retryPolicy, service)` (`CircuitBreaker.java:43-45`) accepts an injectable
`ScheduledExecutorService` and `CircuitBreakingConnectionStateListener` has a package-visible
constructor taking a `CircuitBreaker` (`:113-119`), so the whole surface is drivable by hand with
**no ZooKeeper server and no sleeps** — which matters, because the shortlist measured ZK-backed
tests at ~4 s each with a history of timing flakiness.

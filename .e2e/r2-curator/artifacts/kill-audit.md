# KILL AUDIT — C1 Down-instance endpoint identity

## Verdict

**OVERTURN THE FINAL KILL. C1 is ALIVE FOR RE-MEASUREMENT, not yet an A3 survivor.**

The two GATE 5 probes are invalid. More importantly, the GATE 4 run is not the exact
A3-LOCAL instrument claimed: A3 says to take the card's `CONSTRAINT` verbatim and generate from
that alone, but `build-prompt.txt` adds the exact `noteError` entry point, names
`ServiceProvider`, `ServiceDiscovery`, `DownInstancePolicy`, and `InstanceFilter`, and adds
explanatory emphasis. That materially removes SEARCH work, one of A3's three stated sources of
outcome variance. The 5/5 is strong evidence that the implementation is easy once directed to the
right API, but it is not a compliant 5/5 from the declared contract.

The rest of the claimed instrument largely holds: T3 is a real behavioral discriminator, the five
diffs were classified in the declared direction, the base sketch failed, and every implementation
passed the four-test sketch. A clean rerun using the exact card `CONSTRAINT`, with the throwaway
test absent until all five patches are frozen, would settle the card. If that rerun is 5/5, the
kill stands.

## 1. Do both GATE 5 prompts state the card's CONSTRAINT?

**No. Neither probe counts.** I ran:

```text
python3 /home/agvidit/swebench-playbook/tools/probe-lint.py \
  /home/agvidit/swebench-playbook/.e2e/r2-curator/artifacts/cards.md \
  /tmp/curator-run/probe-A1.txt /tmp/curator-run/probe-A2.txt
```

The real output was:

```text
FAIL  probe-A1.txt: states only 47% of the CONSTRAINT's content words.
Missing: ['advertises', 'concurrently', 'configured', 'continue', 'down',
          'during', 'enabled', 'endpoints', 'even', 'example']
FAIL  probe-A1.txt: names 3 DESIRED-design words the constraint does not:
      ['name', 'port', 'while']
FAIL  probe-A2.txt: states only 28% of the CONSTRAINT's content words.
Missing: ['advertises', 'after', 'cache', 'caller', 'concurrently',
          'configured', 'continue', 'down', 'during', 'enabled']
```

A1 is leading as well as incomplete. A2 is a symptom/novelty probe that withholds R-b, so its 5/5
name+id result cannot be mapped as a constraint-stated GATE 5 result. The reported GATE 5 verdicts
must remain discarded.

## 2. Does ZZGate4 observe the discriminating behavior?

**T3 does, directly.** It registers two concurrent `DYNAMIC_SEQUENTIAL` instances with the same
id and different endpoints, calls `provider.noteError(a)`, and then observes
`provider.getAllInstances()`. It requires exactly endpoint B to remain. That is the public
behavior separating endpoint-scoped attribution from name+id attribution; it is not a private-map
or representation proxy.

I verified this empirically in the permitted scratch worktree
`/tmp/curator-run/audit-id-only`. I replaced the whole-record map key with the card's
NON-DESIRED name+id key:

```java
return Objects.equals(name, that.name) && Objects.equals(id, that.id);
```

I confirmed that the installed test was byte-identical to `/tmp/curator-run/ZZGate4.java`
(both SHA-256 `52535a81e27172d8a3db7279c6bc3c334eabca9b56761a2c1153e90934cab203`), then ran the
brief's two Docker/Maven commands, each under `flock /tmp/swebench-docker.lock`. The compile/install
command exited 0. The test command failed only T3, on all three Surefire attempts:

```text
Tests run: 4, Failures: 1, Errors: 0, Skipped: 0
ZZGate4.t3_sameIdDifferentEndpointStaysIndependent
T3: reporting one endpoint changed the availability of the other; got []
==> expected: <1> but was: <0>
```

Therefore an id-only/name+id implementation cannot pass T3 accidentally.

Two qualifications do not overturn that result:

- T1 directly observes payload republication through provider output and is a valid broken-behavior
  check.
- T2 does **not** establish what its comment claims. It disables and then re-enables the record,
  preserves `registrationTimeUTC`, and finishes with a record equal to the original; base therefore
  passes it. It is not an effective enabled-toggle persistence test. This leaves the sketch
  incomplete for one example in the contract, although inspection of all five diffs confirms their
  keys omit `enabled`.

## 3. Was DESIRED/NON-DESIRED applied in the declared direction?

**Yes.** The declared direction is: endpoint-scoped identity is DESIRED; id-only or name+id is
NON-DESIRED. Each implementation included address and ports in the key, so each took the DESIRED
side. The deciding lines are:

- wt-1: `this.id = instance.getId(); this.address = instance.getAddress(); this.port = instance.getPort(); this.sslPort = instance.getSslPort();`
- wt-2: `this.name = instance.getName(); this.id = instance.getId(); this.address = instance.getAddress();` followed by both port fields.
- wt-3: `this.name = instance.getName(); this.id = instance.getId(); this.address = instance.getAddress();` followed by both port fields.
- wt-4: the same decisive lines as wt-3.
- wt-5: `return new InstanceKey(instance.getName(), instance.getId(), instance.getAddress(), instance.getPort(), instance.getSslPort());`

wt-1 omits service name, contrary to the write-up's claim that all five used the literal five-field
tuple. That is not a direction reversal: `ServiceProviderImpl` creates one
`DownInstanceManager` for a cache already scoped by `serviceName`, so service name is invariant
for ordinary provider-produced instances. Four implementations are literal DESIRED and wt-1 is
behaviorally endpoint-scoped on the graded public path. None is the declared NON-DESIRED id-only
shape.

## 4. Was GATE 4 A3-LOCAL run or waived?

**It was not waived, and the execution logs are genuine, but its input contract was not compliant
with A3-LOCAL step 1.**

The logs substantiate the execution claim:

- Base: `Tests run: 4, Failures: 1`, with T1 failing on run 1 and both Surefire reruns. The only
  recorded failure is T1, so T2/T3/T4 passed.
- wt-1 through wt-5: each says `Tests run: 4, Failures: 0, Errors: 0, Skipped: 0` and
  `BUILD SUCCESS`.

That validates the sketch-at-base and 5/5 execution sequence. It does not validate the claim
"`CONSTRAINT` alone." The card's declaration begins generically:

```text
When a caller reports a service instance as failing through the service provider ...
```

The build prompt changes that to:

```text
When a caller reports a service instance as failing by calling noteError on the service provider ...
```

and later names four exact APIs whose compatibility must be preserved. A3-LOCAL says:
"`Take CONSTRAINT verbatim from the card. That is your contract; do not improve it.`" The prompt
did not do that. Naming `noteError` collapses the search from the symptom to
`ServiceProviderImpl.noteError()` and then directly to `DownInstanceManager.add()`. Since A3
expressly treats SEARCH as the strongest source of outcome variance, this is a material
instrumentation defect, not merely punctuation.

## 5. Would a different constraint on this same surface survive?

**Yes, the surface remains promising, although the replacement candidate is unmeasured and must
return to A2/A3.** The strongest recut is stale-error attribution across supersession:

> If a caller obtained registration generation G1, the same endpoint was subsequently replaced by
> generation G2, and the caller then reports its late failure against G1, G2 must not inherit that
> failure. Ordinary metadata republication within G1 must still preserve G1's down state, and a
> concurrently live same-id endpoint must remain independent.

This is an ordering/state problem rather than the single obvious projection-key answer:

- `ServiceProviderImpl.getInstance()` returns a current object at lines 125–126, while
  `noteError()` later forwards whatever object the caller retained directly to
  `DownInstanceManager.add()` at lines 129–131. There is no check against the cache's current
  generation.
- `ServiceCacheImpl.childEvent()` replaces the current record on add/update at lines 157–188.
- `ServiceInstance.getRegistrationTimeUTC()` and the existing builder setter provide a
  deterministic generation seam; no wall-clock race is required in the grader.

Materially different implementation families exist: keep generation-aware status/history per
endpoint; validate the reported generation against the cache's current record before attribution;
or carry an internal registration/node generation token through the provider path. The observable
test can be a deterministic sequence—obtain G1, publish G2 at the same endpoint, await G2, report
G1 late, and assert G2 remains available.

There is preliminary evidence this cut has difficulty: all five endpoint-key implementations omit
`registrationTimeUTC`, and all five A1 prose outputs explicitly accept sacrificing a same-endpoint
replacement. Thus all five present implementations would fail this recut. That is not yet a
surviving 1–3/5 measurement; it is a reason to send the surface back for a fresh exact-constraint
A3-LOCAL probe.

I also examined the lower-level concurrent purge race in `DownInstanceManager`: a purge can remove
an expired `Status` while another thread increments that detached object, losing the new report.
That is a real concurrency-shaped possibility, but it lacks the deterministic public injection
seam required by GATE 6. The sequential supersession cut above is the stronger candidate.

## 6. Fact or convergence reading?

**The defect is a fact; the kill is a convergence reading.** At base,
`ConcurrentMap<ServiceInstance<?>, Status>` plus full-record equality is present, and the base
reproduction/log demonstrates the payload-republication defect. But no merged public PR,
importable reference implementation, or already-true premise establishes that the task is dead.
Deadness comes only from local model convergence.

The GATE 5 convergence readings are invalid by lint. The GATE 4 reading is much stronger because
its behavioral discriminator is valid and the logs show 5/5, but it was obtained from an
API-directed restatement rather than the verbatim card constraint. Under the KILL AUDIT rule, that
is not a final kill; fix the instrument and re-measure.

## The steelman

The strongest C1 is a generation-aware error-attribution contract across three competing truths:
metadata republication must not forgive a failing live registration, concurrent same-id endpoints
must remain independent, and a late error from a superseded registration must not quarantine its
healthy successor at the same endpoint. Curator already exposes every needed observation through
`ServiceProvider`, cache-driven registration updates, and explicit `registrationTimeUTC`
values, while the implementation must reconcile cached-current state with caller-held historical
state rather than merely choose a better map key. That version has a deterministic public behavior,
multiple reasonable implementation families, and real ordering difficulty—but it still needs a
fresh exact-constraint n=5 measurement before it can be called an A3 survivor.

## Disposition

- **DONE:** all six audit questions; prompt lint; five diff classifications; log audit; empirical
  id-only counterimplementation.
- **NOT DONE:** clean exact-`CONSTRAINT` n=5 rerun. The brief authorized writes only for the
  question-2 scratch implementation, so I did not generate replacement trials.
- **NEXT:** return C1/surface to A2, recut around stale-error supersession if desired, then run
  A3-LOCAL with the exact declaration copied verbatim and no assertion file visible until all five
  implementations are frozen.

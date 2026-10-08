# R7 — ALGO-CATALOGUE  ·  **QUARANTINED**

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

> **STATUS: QUARANTINED — research history only. Do NOT source ideas from this file.**
>
> Gated out of `A-source/A2-idea-generate.md` until re-measured. Reasons, all measured:
>
> 1. **`R6-fork-patterns.md` records that this layer has failed FIVE times**, each death
>    measured rather than argued. Candidates drawn from it scored 30–33/35 on argued fork
>    strength and then executed correctly 10/10 and 6/6 when a frontier model was simply
>    told the constraint.
> 2. **Its own ranking points at the most saturated ground in the corpus.** The "Ranked
>    top 15" below opens with MVCC snapshot isolation (#2), crash-safe COW B-tree (#3) and
>    path-copy persistent tree (#4) — while `R6` measures `snapshot isolation` at **126**
>    peer tasks, `MVCC` **111**, `consistent snapshot` **126**, `copy-on-write` **112**.
>    The head of the ranking is the part a peer author has most likely already built.
> 3. **It contains 73 techniques.** The old `SKILL.md` advertised 46. Any count cited from
>    memory is unreliable; count before quoting.
> 4. Its per-technique pass-band estimates are **unvalidated priors**, not measurements.
>
> **To un-quarantine:** run the `A3` fork probe and the corpus sweep against a sample of
> entries and record the result in `ledger/RUNS.md`. Until then, an idea that arrives via
> this file must still clear every `A3` gate on its own evidence — and historically none has.

---

Assumptions: pass estimates assume the task specifies behavior, not the technique’s name. Deterministic fake storage, virtual clocks, allocator counters, object identity, serialized state, and injected scheduling hooks are gradeable; wall-clock limits are not. Requiring an otherwise-private implementation trace is considered weak.

## Persistence and versioning

### 1. Path-copy persistent tree — immutable versions with structural sharing

**Naive:** Deep-copy the entire tree or mutate it in place.  
**Observable:** Old roots retain old values; nodes outside the updated root-to-leaf path are literally identical objects; allocations are proportional to tree height.  
**Band:** Strong, about 2/5.  
**Homes:** Config stores, immutable ASTs, versioned indexes.  
**Cascade:** S1 adds snapshots; S2 requires unchanged subtree identity and bounded allocations.  
**Risk:** Medium; persistence is canonical, correct deletion and sharing are not.

### 2. Fat-node partial persistence — history stored inside nodes

**Naive:** Clone each version or keep a separate change log that cannot answer historical pointer traversals.  
**Observable:** Historical handles remain readable; ordinary updates allocate no replacement nodes until a fat node fills; versioned fields resolve correctly.  
**Band:** Strong, 1–2/5.  
**Homes:** Temporal graphs, audit indexes, versioned object models.  
**Cascade:** S1 adds historical reads; S2 limits node allocations and requires stable identities.  
**Risk:** Low-medium; less memorized than path copying.

### 3. Confluent persistence — merge independently derived versions

**Naive:** Deep-copy both branches into a new structure or mutate one branch.  
**Observable:** Both inputs remain valid, shared regions remain shared, and the merged version combines changes under defined conflict rules.  
**Band:** Usually too hard, 0–1/5.  
**Homes:** Branching document stores, symbolic DAGs, build graphs.  
**Cascade:** S1 adds branching versions; S2 adds merging while preserving ancestry and sharing.  
**Risk:** Low, but realism is narrow and semantics need exceptional precision.

### 4. Page-level copy-on-write tree — atomic snapshots without overwriting reachable pages

**Naive:** Update pages in place, or rewrite the whole file.  
**Observable:** Earlier root page IDs still decode the old state; only the modified path gets new pages; the root pointer changes last.  
**Band:** Excellent, 1–3/5.  
**Homes:** Embedded databases, filesystem metadata, durable indexes.  
**Cascade:** S1 implements a page-backed tree; S2 adds crash snapshots and forbids writes to reachable old pages.  
**Risk:** Medium; concept is known, pager details are difficult.

### 5. MVCC with snapshot isolation — readers see a stable version while writers proceed

**Naive:** One mutable map protected by a lock, or clone the whole database per transaction.  
**Observable:** A reader retains its start-time view; write-write conflicts are rejected; uncommitted and later committed values remain invisible to it.  
**Band:** Excellent, 1–2/5.  
**Homes:** Databases, metadata catalogs, transactional caches.  
**Cascade:** S1 adds transactions; S2 introduces overlapping deterministic transactions and snapshot/conflict rules.  
**Risk:** Medium-high vocabulary contamination, but edge cases remain difficult.

### 6. Delta chains with checkpoints — reconstruct history from append-only changes

**Naive:** Store every full snapshot or mutate a single current representation.  
**Observable:** Every historical version is reconstructible; commits append rather than rewrite; checkpoints shorten chains without changing version IDs.  
**Band:** Strong, 2/5.  
**Homes:** Document history, schema registries, backup catalogs.  
**Cascade:** S1 records deltas; S2 adds checkpoint compaction while old version reads must remain identical.  
**Risk:** Low-medium.

## Advanced trees

### 7. Link-cut tree — online link, cut, and path aggregates in a dynamic forest

**Naive:** Store adjacency sets and run DFS/BFS for every path query.  
**Observable:** None inherent; both implementations return the same forest answers. Exposing rotations or access counts would be artificial.  
**Band:** Unusable under this selection rule; implementing it would likely be 0/5.  
**Homes:** Dynamic dependency graphs, network topology, game trees.  
**Cascade:** S1 adds links and path queries; S2 adds cuts, but this still does not force link-cut behavior.  
**Risk:** Medium contamination, excessive implementation risk.

### 8. Euler-tour tree — dynamic forest connectivity via sequence operations

**Naive:** Adjacency lists plus traversal after each update.  
**Observable:** None unless the subsystem already exposes the Euler sequence or persistent sequence roots.  
**Band:** Weak/unusable normally; 1/5 with an authentic sequence representation contract.  
**Homes:** Dynamic graph engines, scene hierarchies, topology editors.  
**Cascade:** S1 exposes Euler tours; S2 requires link/cut while preserving unaffected sequence chunks.  
**Risk:** Low-medium.

### 9. Persistent randomized treap — ordered map with split/merge and structural sharing

**Naive:** Copy a sorted array, use a mutable balanced tree, or rebuild after splits.  
**Observable:** Seeded priorities give deterministic shape; split and merge preserve old roots and share untouched subtrees.  
**Band:** Strong, 2–3/5.  
**Homes:** Immutable maps, text interval indexes, versioned schedulers.  
**Cascade:** S1 adds ordered map operations; S2 adds persistent split/merge and identity assertions.  
**Risk:** Medium; treaps are familiar, persistent edge cases less so.

### 10. Finger tree — persistent sequence with cheap operations near either end and measured splits

**Naive:** Copy arrays or implement a basic deque that cannot preserve old versions.  
**Observable:** Old sequences survive edits; interior chunks are shared; splitting by a monoidal measure returns exact boundaries without materializing the sequence.  
**Band:** Borderline hard, 1/5.  
**Homes:** Editors, immutable event streams, parser token buffers.  
**Cascade:** S1 adds persistent deque operations; S2 adds measured split and concatenation with sharing.  
**Risk:** Low; excellent signal if the repo naturally uses functional structures.

### 11. Bε-tree or buffered B-tree — batch writes through internal buffers

**Naive:** Apply every update immediately to a leaf page.  
**Observable:** A fake block device records buffered writes and batched flushes; reads consult buffers; crash recovery cannot lose buffered operations.  
**Band:** Usually too hard, 0–1/5.  
**Homes:** Storage engines, write-heavy indexes, filesystem metadata.  
**Cascade:** S1 builds a paged B-tree; S2 imposes a page-write budget and crash-replay semantics.  
**Risk:** Low contamination, high implementation scope.

### 12. Bw-tree-style delta chains — latch-free logical pages with immutable deltas

**Naive:** Mutate page objects or copy a complete page for every update.  
**Observable:** Readers holding an old chain see a stable state; writers prepend immutable deltas; consolidation atomically replaces the mapping-table entry.  
**Band:** Too hard for most steps, near 0/5.  
**Homes:** Concurrent indexes, in-memory databases, durable page caches.  
**Cascade:** S1 adds immutable page deltas; S2 adds consolidation with simulated concurrent readers.  
**Risk:** Low, but likely outside the calibration band.

### 13. van Emde Boas tree — predecessor/successor over a bounded integer universe

**Naive:** Balanced tree, sorted array, or dictionary scan.  
**Observable:** None unless recursive cluster layout or allocation count is made public; results are identical.  
**Band:** Unusable; likely 1–2/5 if explicitly demanded.  
**Homes:** Packet schedulers, integer indexes, bounded timestamp setsJosh.  
**Cascade:** S1 adds predecessor queries; S2 fixes a bounded universe, but that still does not behaviorally require vEB.  
**Risk:** Medium-high textbook contamination.

## Amortisation and laziness

### 14. Real-time persistent queue — worst-case bounded work using scheduled lazy rotations

**Naive:** Reverse the rear list all at once, or use a mutable deque.  
**Observable:** Old queue versions remain valid; an instrumented thunk evaluator performs a fixed maximum number of forces per operation.  
**Band:** Strong, 1–2/5.  
**Homes:** Functional runtimes, immutable schedulers, stream processors.  
**Cascade:** S1 adds a persistent queue; S2 adds adversarial branching and a per-operation forcing bound.  
**Risk:** Low-medium.

### 15. Lazy propagation in an interval tree — defer bulk updates while preserving aggregates

**Naive:** Touch every covered element or append overlapping updates that reads replay linearly.  
**Observable:** A backing-store spy shows only logarithmically many node reads/writes; serialized lazy tags remain canonical and partial queries compose them correctly.  
**Band:** 2–3/5, but only if the storage-access contract is authentic.  
**Homes:** Analytics indexes, calendars, image tile metadata.  
**Cascade:** S1 adds point queries; S2 adds range updates and a page-access budget.  
**Risk:** High textbook contamination; otherwise low value.

### 16. Incremental hash-table rehashing — migrate a bounded number of buckets per operation

**Naive:** Stop and rebuild the complete table when its load threshold is crossed.  
**Observable:** Each public operation invokes at most a fixed number of migration callbacks; lookups work across both tables; iterators neither duplicate nor omit entries.  
**Band:** Excellent, 1–3/5.  
**Homes:** Caches, registries, language runtimes.  
**Cascade:** S1 implements resizing; S2 adds latency-budget hooks and iteration during migration.  
**Risk:** Low-medium.

### 17. Self-adjusting/incremental computation — recompute only invalidated dependencies

**Naive:** Re-run the whole computation after any input change.  
**Observable:** Evaluation callbacks run only for the affected dependency cone; unchanged result nodes retain identity; dynamic dependencies are added and removed correctly.  
**Band:** Excellent, 1–2/5.  
**Homes:** Build systems, spreadsheets, reactive UIs.  
**Cascade:** S1 adds dependency tracking; S2 adds conditional dependencies and identity/callback-count assertions.  
**Risk:** Low; very good task material.

## Dynamic programming

### 18. Divide-and-conquer DP optimization — exploit monotone optimal split points

**Naive:** Evaluate every predecessor for every state.  
**Observable:** Normally none. A realistic scoring-oracle API can count calls, but otherwise this is only faster.  
**Band:** Weak; 1–3/5 with an oracle-call budget, unusable without one.  
**Homes:** Partitioning engines, segmentation, batch planning.  
**Cascade:** S1 returns optimal cost; S2 supplies costs through a metered callback and requires witnesses.  
**Risk:** High contest-algorithm contamination.

### 19. Knuth–Yao optimization — reduce interval DP using quadrangle inequalities

**Naive:** Cubic enumeration of split positions.  
**Observable:** None unless the split table is part of the result or cost calls are metered.  
**Band:** Weak and often too hard, 0–1/5.  
**Homes:** Optimal merge planners, grammar-like interval optimizers.  
**Cascade:** S1 implements interval optimization; S2 introduces a metered cost oracle and validates monotone split bounds.  
**Risk:** Medium-high; theorem preconditions are easy to mishandle.

### 20. Convex hull trick or Li Chao tree — answer dynamic linear-function minima

**Naive:** Scan every line for every query.  
**Observable:** A persistent Li Chao variant can expose version roots and sharing; otherwise the result is behaviorally identical.  
**Band:** Strong only with persistence, 1–2/5; otherwise unusable.  
**Homes:** Pricing planners, time-series envelopes, optimization libraries.  
**Cascade:** S1 adds line/query operations; S2 adds historical versions and arbitrary insertion order.  
**Risk:** Medium-high canonical contamination.

### 21. SOS/subset DP — compute aggregates over every submask or supermask

**Naive:** Enumerate all submasks independently.  
**Observable:** None for a normal value-returning API; intermediate tables or iteration counts would be contrived.  
**Band:** Unusable despite likely 2–4/5 implementation success.  
**Homes:** Feature-set analytics, permission lattices, combinatorial solvers.  
**Cascade:** No natural behavioral step 2 that forces it.  
**Risk:** High textbook contamination.

### 22. Digit/automaton DP — count constrained huge domains without enumeration

**Naive:** Enumerate integers or generate strings up to the bound.  
**Observable:** A user-supplied automaton can expose state-transition call counts; counts for enormous bounds also make enumeration practically impossible, but timeout alone is not a valid oracle.  
**Band:** 1–3/5 with metered transitions.  
**Homes:** Validation analytics, identifier counting, symbolic query tools.  
**Cascade:** S1 counts under a bound; S2 adds stateful constraints, leading zeros, and a transition-call budget.  
**Risk:** Medium.

## Strings and compressed indexes

### 23. Suffix automaton — compact online index of all substrings

**Naive:** Store every substring, rebuild a suffix array after each append, or repeatedly search the source.  
**Observable:** Appends work chunk-by-chunk without retaining old chunks; state count is at most `2n−1`; distinct-substring counts are available per prefix.  
**Band:** Strong, 1–2/5.  
**Homes:** Log search, streaming text analytics, plagiarism tools.  
**Cascade:** S1 adds substring queries; S2 makes input streaming and bounds retained state.  
**Risk:** Medium-high canonical contamination.

### 24. Suffix array/tree — reusable full-text index

**Naive:** Scan the text per query or sort suffix strings directly.  
**Observable:** If only matches are returned, none. Exposing the suffix array makes the technique explicit and usually easy.  
**Band:** LOW VALUE; 3–5/5 for arrays, too hard for robust suffix trees.  
**Homes:** Search libraries, genomic tools, static archives.  
**Cascade:** S1 exposes index serialization; S2 adds LCP-based queries.  
**Risk:** High.

### 25. Aho–Corasick automaton — multi-pattern matching across a single stream

**Naive:** Run each pattern separately or search each chunk independently.  
**Observable:** Matches crossing chunk boundaries appear once, overlaps are ordered deterministically, and discarded chunks are never reread.  
**Band:** Excellent, 2–3/5.  
**Homes:** Log filters, malware scanners, syntax highlighters.  
**Cascade:** S1 supports multiple patterns; S2 switches to chunked input with reset and dynamic output rules.  
**Risk:** High name recognition, but streaming state and failure outputs remain tricky.

### 26. Palindromic tree/Eertree — linear-size online representation of distinct palindromes

**Naive:** Expand around every center or store every palindrome string.  
**Observable:** Exactly one node per distinct palindrome plus two roots; prefix updates expose longest palindromic suffixes without retaining duplicate strings.  
**Band:** 1–2/5.  
**Homes:** Text analytics, sequence tools, editor diagnostics.  
**Cascade:** S1 reports palindromes; S2 requires online append, suffix links, and bounded node count.  
**Risk:** Low-medium.

### 27. Rolling hash — fast substring equality and search

**Naive:** Compare substrings directly.  
**Observable:** None beneficial: exact APIs must still handle collisions, while accepting collision risk weakens correctness.  
**Band:** Unusable; models often reach for it unprompted.  
**Homes:** Deduplication, editors, search prototypes.  
**Cascade:** A second step demanding adversarial collision correctness usually invalidates, rather than forces, hashing.  
**Risk:** Very high; LOW VALUE.

### 28. Wavelet tree/matrix — rank, select, and quantiles over a compact sequence

**Naive:** Scan ranges or store a sorted index per value.  
**Observable:** A canonical bitvector serialization is compact and queryable without expanding per-value indexes; rank/select paths can be validated.  
**Band:** Strong but hard, 1/5.  
**Homes:** Compressed databases, telemetry indexes, genomic tools.  
**Cascade:** S1 adds range quantiles; S2 requires canonical compact serialization and rank/select.  
**Risk:** Low-medium.

## Sets, maps, and range indexes

### 29. Crit-bit or compressed radix trie — prefix and longest-prefix operations without per-character chains

**Naive:** Dictionary plus full scans, or an uncompressed trie with one node per byte.  
**Observable:** Longest-prefix semantics are direct; canonical compressed-node serialization and node-count bounds distinguish it from the naive trie.  
**Band:** 2/5.  
**Homes:** Routers, URL indexes, command completion.  
**Cascade:** S1 adds prefix lookup; S2 adds binary keys, longest-prefix matching, and compact serialization.  
**Risk:** Low-medium.

### 30. Adaptive radix tree — node representation changes with fan-out

**Naive:** One hash map per trie node or a fixed 256-slot child array.  
**Observable:** Serialized Node4/16/48/256 transitions, prefix compression, and shrink/grow thresholds are deterministic.  
**Band:** Usually too hard, 0–1/5.  
**Homes:** In-memory databases, routing tables, key-value stores.  
**Cascade:** S1 implements a radix index; S2 imposes canonical node morphing and deletion compaction.  
**Risk:** Low.

### 31. Cuckoo hashing — fixed candidate buckets with relocation

**Naive:** Chaining or linear probing.  
**Observable:** With fixed hashes and seed, table layout, relocation sequence, stash contents, and lookup probe bound are deterministic.  
**Band:** 1–2/5.  
**Homes:** Packet filters, compact maps, embedded stores.  
**Cascade:** S1 adds fixed-capacity hashing; S2 adds bounded probes, deletion, and deterministic resizing.  
**Risk:** Medium.

### 32. Robin Hood hashing with backward-shift deletion — stabilize probe distances

**Naive:** Plain linear probing with tombstones.  
**Observable:** Exact table serialization and probe-distance invariant; deletion leaves no tombstone and preserves early-termination lookup.  
**Band:** 2–3/5.  
**Homes:** Language runtimes, game engines, compact caches.  
**Cascade:** S1 adds open addressing; S2 requires deterministic serialization and tombstone-free deletion.  
**Risk:** Medium-high but still useful.

### 33. Hopscotch hashing — keep entries within a fixed neighborhood

**Naive:** Linear probing or chaining.  
**Observable:** Neighborhood bitmaps and relocation invariants are inspectable; every successful lookup probes within the configured neighborhood.  
**Band:** Too hard, around 0–1/5.  
**Homes:** Concurrent maps, packet-processing tables.  
**Cascade:** S1 adds bounded-neighborhood lookup; S2 adds relocation and deletion under adversarial hashes.  
**Risk:** Low, but niche.

### 34. Seeded skip list — ordered probabilistic map with reproducible structure

**Naive:** Sorted array or binary search tree.  
**Observable:** A fixed RNG produces a golden level structure; iterators can remain valid under a documented mutation policy. Without structure exposure, there is no advantage to grade.  
**Band:** 2–4/5; often too easy.  
**Homes:** Memtables, ordered registries, concurrent indexes.  
**Cascade:** S1 adds ordered operations; S2 adds seeded serialization or lock-free traversal.  
**Risk:** High canonical contamination; LOW VALUE unless integrated deeply.

### 35. Order-statistic/interval tree — augmented tree for rank, selection, or overlap queries

**Naive:** Sort or scan on every query.  
**Observable:** Normally none. It becomes viable when persistent roots must share nodes, or a lazy cursor may fetch only enough backing records to produce requested matches.  
**Band:** 2–3/5 under those added constraints.  
**Homes:** Schedulers, editors, spatial timelines.  
**Cascade:** S1 adds queries; S2 adds persistence or pull-based cursor semantics.  
**Risk:** High for basic augmentation, medium for deletion and persistence.

## Probabilistic summaries

### 36. Bloom filter — compact membership with no false negatives

**Naive:** Exact set or a single-hash bitmap.  
**Observable:** Fixed-size canonical bytes, merge-by-OR, guaranteed retention of inserted keys, and explicitly permitted false positives.  
**Band:** Often too easy, 3–5/5.  
**Homes:** Caches, storage read avoidance, synchronization protocols.  
**Cascade:** S1 adds membership hints; S2 adds serialization, merging, and stable hashing.  
**Risk:** Very high; LOW VALUE unless compatibility details are subtle.

### 37. Counting Bloom/cuckoo filter — compact membership with deletion

**Naive:** Clear Bloom bits on delete, producing false negatives, or retain a full exact set.  
**Observable:** Deleting one colliding key does not erase another; counters saturate safely; fixed-size state survives round-trip serialization.  
**Band:** Strong, 1–3/5.  
**Homes:** Cache admission, duplicate suppression, storage indexes.  
**Cascade:** S1 adds a Bloom filter; S2 introduces deletions, duplicates, and counter overflow.  
**Risk:** Medium.

### 38. Count-Min Sketch — mergeable one-sided frequency estimates

**Naive:** Exact frequency map or a single collision-prone counter array.  
**Observable:** Fixed memory regardless of distinct keys; estimates never undercount; independent summaries merge cellwise and match a single combined stream.  
**Band:** 2–4/5, sometimes too easy.  
**Homes:** Telemetry, abuse detection, cache admission.  
**Cascade:** S1 counts events; S2 imposes bounded state and distributed merging.  
**Risk:** High canonical contamination.

### 39. HyperLogLog — mergeable cardinality estimate with fixed state

**Naive:** Store every distinct item or average raw hash buckets incorrectly.  
**Observable:** Fixed register count, registerwise-max merge, stable binary format, and deterministic estimate for fixed hashes.  
**Band:** 1–3/5, especially with small/large-range corrections.  
**Homes:** Analytics, observability, distributed databases.  
**Cascade:** S1 estimates cardinality; S2 adds cross-shard merge and compatibility fixtures.  
**Risk:** High concept contamination, medium implementation difficulty.

### 40. t-digest — mergeable approximate quantiles concentrated in the tails

**Naive:** Retain and sort all samples or use fixed-width histograms.  
**Observable:** Centroid count remains bounded; weighted samples merge; deterministic fixtures validate tail quantiles and serialization.  
**Band:** 1/5 or too hard because variants are underspecified.  
**Homes:** Metrics, latency analytics, monitoring.  
**Cascade:** S1 adds quantiles; S2 adds weighted distributed merges and centroid bounds.  
**Risk:** Medium; only viable if the exact variant is fully specified.

### 41. Reservoir sampling or priority sampling — uniform fixed-size sample of a stream

**Naive:** Materialize the stream, sample only the prefix, or repeatedly replace slots with the wrong probability.  
**Observable:** Exactly `k` items retained; fixed RNG yields golden samples; merging priority reservoirs matches sampling the combined stream.  
**Band:** 2–3/5.  
**Homes:** Telemetry, debugging capture, data ingestion.  
**Cascade:** S1 samples one stream; S2 adds weighted or mergeable sampling.  
**Risk:** High for basic Algorithm R, medium for mergeable variants.

## Graph algorithms

### 42. Union-find with rollback — reversible connectivity snapshots

**Naive:** Use path compression with no undo, clone the entire DSU, or recompute connectivity.  
**Observable:** Snapshot tokens restore exact parent/size state; nested rollbacks work; history grows only with successful mutations.  
**Band:** Excellent, 1–3/5.  
**Homes:** Constraint solvers, graph editors, speculative planners.  
**Cascade:** S1 adds union/find; S2 adds snapshots and rollback, making path compression hazardous.  
**Risk:** Medium; the no-path-compression detail catches strong models.

### 43. Offline dynamic connectivity — answer add/remove/query histories via segment time and rollback DSU

**Naive:** Rebuild connectivity after each deletion.  
**Observable:** Answers alone do not force the technique. An authentic rollback-state API or operation-log bound is needed.  
**Band:** Weak by itself; 1/5 when layered onto entry 42.  
**Homes:** Network history, temporal permissions, dependency analytics.  
**Cascade:** S1 adds rollback DSU; S2 accepts a complete operation timeline with deletions.  
**Risk:** Medium-high contest contamination.

### 44. 2-SAT via implication graph and SCC — assignment or contradiction certificate

**Naive:** Brute-force assignments or generic backtracking.  
**Observable:** A returned implication-cycle contradiction certificate is useful behavior, but it still does not uniquely require SCC.  
**Band:** Usually too easy, 3–5/5.  
**Homes:** Feature configuration, dependency resolution, policy validation.  
**Cascade:** S1 finds assignments; S2 requires deterministic unsatisfiable certificates.  
**Risk:** Very high; LOW VALUE.

### 45. Matching/flow with primal-dual certificates — solution plus checkable optimality proof

**Naive:** Greedy matching or an incomplete augmenting-path implementation.  
**Observable:** Matching, residual graph, min-cut, or dual potentials form independently checkable certificates; this grades correctness, not asymptotic choice.  
**Band:** 1–3/5 for min-cost flow, 3–5/5 for ordinary max flow.  
**Homes:** Schedulers, assignment engines, routing planners.  
**Cascade:** S1 returns a feasible assignment; S2 adds capacities/costs and certificates.  
**Risk:** High canonical contamination, but edge cases retain value.

### 46. Incremental topological ordering — maintain order and reject cycle-forming edges atomically

**Naive:** Recompute a complete topological sort after every insertion, often changing unrelated order.  
**Observable:** Accepted insertions minimally reorder the affected interval; rejected edges leave graph and order byte-for-byte unchanged; stable tie order persists.  
**Band:** Excellent, 1–2/5.  
**Homes:** Build graphs, workflow engines, package managers.  
**Cascade:** S1 validates a DAG; S2 adds incremental edges with stable-order and atomic-rejection requirements.  
**Risk:** Low-medium.

## Concurrency and memory reclamation

These are best tested with deterministic interleaving hooks or modeled atomics, not real race timing.

### 47. Hazard pointers — reclaim retired nodes only after no reader protects them

**Naive:** Free immediately after unlink, leak forever, or use a global lock.  
**Observable:** A deterministic allocator records that protected retired nodes remain live and are reclaimed after hazards clear; address reuse cannot cause ABA.  
**Band:** Hard, 0–1/5.  
**Homes:** Lock-free queues, concurrent maps, runtime internals.  
**Cascade:** S1 adds lock-free removal; S2 adds forced interleavings and allocator reuse.  
**Risk:** Medium terminology contamination, very high implementation difficulty.

### 48. Epoch-based reclamation — batch frees after all preexisting readers quiesce

**Naive:** Reference-count every access, free immediately, or never free.  
**Observable:** Retired objects remain readable by old epochs, then are reclaimed after every relevant participant advances; stalled readers delay reclamation.  
**Band:** 1–2/5 with a simulated epoch manager.  
**Homes:** Databases, concurrent indexes, networking runtimes.  
**Cascade:** S1 adds reader guards; S2 adds nested guards, stalled participants, and exact reclamation logs.  
**Risk:** Low-medium.

### 49. Read-copy-update — lock-light reads over immutable published versions

**Naive:** Mutate shared objects under a mutex or clone without a grace-period protocol.  
**Observable:** A reader guard sees one stable version; writers publish atomically; removed versions are reclaimed only after the grace period.  
**Band:** Excellent in a modeled environment, 1–2/5.  
**Homes:** Routing tables, configuration registries, kernel-like indexes.  
**Cascade:** S1 adds atomic publication; S2 holds an old reader across updates and checks delayed reclamation.  
**Risk:** Medium.

### 50. Arena/slab allocation — bounded upstream allocations and bulk lifetime control

**Naive:** Allocate every node independently and recursively free it.  
**Observable:** Upstream allocation calls stay flat across many small objects; reset invalidates all arena-owned handles together; freelist reuse follows defined rules.  
**Band:** 2–3/5.  
**Homes:** Parsers, request servers, game engines.  
**Cascade:** S1 introduces allocator injection; S2 imposes slab growth, alignment, reset, and reuse requirements.  
**Risk:** Low-medium.

### 51. Generational slot map — stable handles that reject stale references

**Naive:** Return array indexes or raw pointers that silently alias reused slots.  
**Observable:** Removing and reusing a slot changes its generation; every stale handle fails while unrelated handles remain valid.  
**Band:** Strong, 2–3/5.  
**Homes:** ECS/game engines, async registries, resource managers.  
**Cascade:** S1 adds integer handles; S2 adds deletion/reuse and stale-handle safety.  
**Risk:** Low; highly realistic and cleanly observable.

### 52. Seqlock — optimistic readers detect concurrent writes and retry

**Naive:** Read fields independently, allowing torn snapshots, or lock every read.  
**Observable:** Injected hooks force a write between field reads; the reader retries on odd/changed sequence and never returns a mixed snapshot.  
**Band:** 2/5 in a deterministic simulation.  
**Homes:** Metrics, clocks, shared configuration.  
**Cascade:** S1 adds multi-field snapshots; S2 injects writes at each read boundary.  
**Risk:** Medium.

## Storage and systems techniques

### 53. Write-ahead logging — replay committed work and discard partial transactions

**Naive:** Mutate data pages first or treat every log record as committed.  
**Observable:** Crash injection at every write boundary yields the specified recovered state; checksums reject torn tails; replay is idempotent.  
**Band:** Excellent, 1–3/5.  
**Homes:** Databases, package managers, metadata stores.  
**Cascade:** S1 adds persistence; S2 adds transaction markers, crash points, truncation, and replay.  
**Risk:** Medium-high concept familiarity, low edge-case contamination.

### 54. Log-structured merge tree — immutable runs, tombstones, and level compaction

**Naive:** Rewrite one sorted file per mutation or keep an unbounded append log.  
**Observable:** Flushes create immutable ordered runs; reads reconcile newest values and tombstones; deterministic compaction produces specified files and removes obsolete versions only when safe.  
**Band:** 1–2/5.  
**Homes:** Embedded databases, telemetry stores, search indexes.  
**Cascade:** S1 adds memtable flushes; S2 adds overlapping levels, snapshots, tombstones, and compaction.  
**Risk:** Medium.

### 55. Crash-safe copy-on-write B-tree — publish a new root after durable child pages

**Naive:** Overwrite pages in place or update the root before its descendants.  
**Observable:** Every crash prefix exposes either the old or new tree, never a hybrid; old root handles remain readable; page-write order is testable.  
**Band:** Excellent, 1–2/5.  
**Homes:** Embedded databases, filesystem catalogs, durable caches.  
**Cascade:** S1 adds page persistence; S2 injects crashes after each page write and retains snapshots.  
**Risk:** Medium.

### 56. Transactional compaction — rewrite logs without changing logical history

**Naive:** Delete old segments while copying or install partially written output.  
**Observable:** Readers see a consistent manifest; crashes preserve either old or new segments; retries are idempotent; files become deletable only after readers release them.  
**Band:** Excellent, 1–2/5.  
**Homes:** LSM stores, event logs, backup systems.  
**Cascade:** S1 adds compaction; S2 adds crash points, live readers, and retry cleanup.  
**Risk:** Low-medium.

### 57. Pull-based backpressure with bounded queues — prevent unbounded producer materialization

**Naive:** Read the whole source eagerly or enqueue without a limit.  
**Observable:** A source spy proves no more than the requested window is pulled; cancellation stops reads and releases buffers; result order remains defined.  
**Band:** 2–3/5.  
**Homes:** Stream processors, HTTP clients, database cursors.  
**Cascade:** S1 returns streamed results; S2 adds bounded prefetch, cancellation, and fan-in ordering.  
**Risk:** Low, though basic implementations may be too easy.

### 58. External merge/spillable aggregation — process data larger than the memory budget

**Naive:** Materialize and sort/group everything in RAM.  
**Observable:** An injected storage layer records bounded in-memory runs, lazy k-way reads, deterministic output, and cleanup of temporary runs after errors.  
**Band:** 1–3/5.  
**Homes:** Query engines, log processors, build tools.  
**Cascade:** S1 sorts or groups iterables; S2 supplies one-shot inputs, memory accounting, spills, and failure injection.  
**Risk:** Low-medium.

## Numeric and geometry

### 59. Kahan/Neumaier compensated summation — preserve small contributions in floating-point totals

**Naive:** Ordinary left-to-right addition.  
**Observable:** Adversarial sequences produce materially different numeric answers; chunked merge semantics can also be specified.  
**Band:** Often too easy, 3–5/5 for Kahan; 2–3/5 for mergeable compensated accumulators.  
**Homes:** Metrics, scientific libraries, finance.  
**Cascade:** S1 adds streaming sums; S2 adds adversarial magnitudes and partition merging.  
**Risk:** High canonical contamination.

### 60. Exact/adaptive geometric predicates — correct orientation and intersection near degeneracy

**Naive:** Direct floating-point determinant with an arbitrary epsilon.  
**Observable:** Nearly collinear, huge-coordinate, and exactly degenerate cases receive mathematically correct signs and stable topology.  
**Band:** Excellent, 1–2/5.  
**Homes:** GIS, CAD, mesh tools.  
**Cascade:** S1 adds ordinary intersections; S2 introduces adversarial coordinates and requires exact classification.  
**Risk:** Medium; exact expansion arithmetic is rarely implemented cold.

### 61. Interval arithmetic with outward rounding — guarantee enclosure of the true result

**Naive:** Compute endpoint expressions with ordinary rounding or attach a heuristic epsilon.  
**Observable:** Every mathematically possible value remains enclosed; undefined operations split or widen intervals according to policy; containment survives composition.  
**Band:** 1–2/5.  
**Homes:** Solvers, validation libraries, scientific computing.  
**Cascade:** S1 adds interval operations; S2 adds transcendental functions, infinities, and enclosure fixtures.  
**Risk:** Low-medium.

### 62. Sweep-line geometry — ordered events and active-set neighbor tests

**Naive:** Compare every pair of segments.  
**Observable:** Usually none; both can return identical intersections. Degeneracy rules test correctness but do not force the sweep.  
**Band:** Unusable unless the event stream itself is a public incremental API.  
**Homes:** GIS, layout engines, collision tools.  
**Cascade:** S1 exposes ordered events; S2 supports online event consumption and exact predicates.  
**Risk:** High textbook contamination.

## Scheduling and eviction

These are unusually useful because hit/miss, victim, and dispatch traces are naturally observable.

### 63. ARC — adapt between recency and frequency using ghost lists

**Naive:** LRU or a fixed recency/frequency split.  
**Observable:** Exact victim choices, ghost hits, and adaptation of target `p` are visible on deterministic request traces.  
**Band:** 1–3/5.  
**Homes:** Page caches, object caches, storage engines.  
**Cascade:** S1 adds LRU; S2 introduces scan-resistant and frequency-heavy traces requiring adaptive ghost history.  
**Risk:** Medium-high; ARC is known but frequently implemented incorrectly.

### 64. CLOCK-Pro — approximate adaptive replacement with clock hands and hot/cold/test pages

**Naive:** One-bit CLOCK or LRU.  
**Observable:** Hand movement, resident/test transitions, and victims are deterministic for a specified variant.  
**Band:** Often too hard, 0–1/5.  
**Homes:** Buffer pools, OS-like page caches.  
**Cascade:** S1 adds CLOCK; S2 adds hot/cold adaptation and nonresident test entries.  
**Risk:** Low-medium, but variant ambiguity must be eliminated.

### 65. S3-FIFO — scan-resistant eviction using small, main, and ghost FIFOs

**Naive:** LRU or one FIFO.  
**Observable:** Exact queue transitions, promotions, ghost admissions, and victims follow from a trace; scans do not evict established hot entries as readily.  
**Band:** Excellent, 1–3/5.  
**Homes:** storage caches, CDN metadata, query caches.  
**Cascade:** S1 adds FIFO/LRU eviction; S2 adds scan resistance with fixed queue ratios and ghost behavior.  
**Risk:** Low; particularly promising.

### 66. TinyLFU admission — compare estimated frequency before admitting an item

**Naive:** Admit every miss and evict the current victim.  
**Observable:** Given fixed hashes and aging schedule, admissions, rejections, sketch counters, and victims are deterministic.  
**Band:** 1–3/5.  
**Homes:** Web caches, database caches, artifact caches.  
**Cascade:** S1 adds ordinary eviction; S2 adds admission filtering, bounded sketch state, and aging.  
**Risk:** Medium.

### 67. Deficit round robin — byte-fair service across differently sized jobs

**Naive:** Round-robin one request per queue, which is unfair when costs differ.  
**Observable:** Exact dispatch order and accumulated deficits under virtual costs; empty queues do not bank unlimited credit if policy forbids it.  
**Band:** Excellent, 1–3/5.  
**Homes:** Network schedulers, worker pools, rate-limited APIs.  
**Cascade:** S1 adds round robin; S2 introduces weighted queues and variable-sized work.  
**Risk:** Low-medium.

### 68. Hierarchical timing wheel — bucket timers across multiple time scales

**Naive:** Scan all timers each tick or heap-schedule every timer.  
**Observable:** With a virtual clock, bucket placement, cascades, cancellation, wraparound, and same-deadline firing order are deterministic.  
**Band:** Excellent, 1–2/5.  
**Homes:** Runtimes, networking stacks, job schedulers.  
**Cascade:** S1 adds timers; S2 adds huge horizons, periodic timers, cancellation during callbacks, and wraparound.  
**Risk:** Low-medium.

## Additional high-yield families

### 69. Incremental parsing with subtree reuse — reparse only the edit’s affected region

**Naive:** Parse the entire document after every edit.  
**Observable:** Unchanged syntax subtrees retain object identity; diagnostics outside the damage region remain stable; lexer/parser callback counts stay local.  
**Band:** Excellent but hard, 1–2/5.  
**Homes:** IDEs, formatters, language servers.  
**Cascade:** S1 builds a parser; S2 adds text edits and requires identity-preserving incremental repair.  
**Risk:** Low.

### 70. Observed-remove set/map CRDT — deterministic convergence under concurrent edits

**Naive:** Last-write-wins timestamps or ordinary set union, mishandling concurrent add/remove.  
**Observable:** Replicas converge regardless of merge order; concurrent add/remove follows specified semantics; merging is associative, commutative, and idempotent.  
**Band:** Strong, 1–3/5.  
**Homes:** Collaborative apps, offline sync, replicated metadata.  
**Cascade:** S1 adds replica merge; S2 introduces concurrent removal, tombstone compaction, and duplicate delivery.  
**Risk:** Medium.

### 71. Merkle DAG with hash-consing — content-addressed identity and structural deduplication

**Naive:** Assign random IDs, duplicate equal subobjects, or hash only the root payload.  
**Observable:** Equal structures have equal IDs; unchanged descendants retain IDs after edits; duplicate nodes occupy one stored object; corruption is detectable.  
**Band:** 2–3/5.  
**Homes:** Build systems, package stores, backup tools.  
**Cascade:** S1 adds content hashes; S2 adds DAG deduplication, partial updates, and verification.  
**Risk:** Medium-high concept familiarity.

### 72. Rope/piece table with persistent edits — cheap large-text edits and undo

**Naive:** Copy the complete string for every edit or retain full snapshots.  
**Observable:** Old document handles remain readable; untouched pieces/chunks retain identity; undo changes only roots; iterators stream chunks without flattening.  
**Band:** Excellent, 1–3/5.  
**Homes:** Editors, diff tools, source transformations.  
**Cascade:** S1 adds text editing; S2 adds undo snapshots, streaming, and structural-sharing assertions.  
**Risk:** Medium.

### 73. Rendezvous/consistent hashing — minimize remapping when membership changes

**Naive:** `hash(key) % node_count`, which remaps nearly every key when a node is added.  
**Observable:** Exact mappings are deterministic; after membership change, keys move only to/from the changed node; weighted distributions follow declared scores.  
**Band:** Strong, 2–3/5.  
**Homes:** Sharded caches, worker assignment, replicated storage.  
**Cascade:** S1 maps keys to workers; S2 adds membership churn, weights, and replicas while asserting movement sets.  
**Risk:** Medium; weighted and replicated variants are less memorized.

## Ranked top 15

| Rank | Technique | Why it is especially valuable |
|---:|---|---|
| 1 | Write-ahead logging | Crash-prefix recovery is exceptionally observable, realistic, composable across steps, and full of non-memorized edge cases. |
| 2 | MVCC snapshot isolation | Stable reader views and deterministic conflict behavior directly defeat the mutable-map prior. |
| 3 | Crash-safe COW B-tree | Old roots, page identity, and write ordering expose both persistence and durability without timing tests. |
| 4 | Path-copy persistent tree | Structural sharing and allocation bounds give unusually clean, language-level assertions. |
| 5 | Union-find with rollback | Snapshot restoration naturally invalidates the model’s reflexive use of path compression. |
| 6 | Incremental rehashing | A fixed migration budget plus two-table correctness makes the amortization externally testable. |
| 7 | Transactional compaction | Manifest atomicity, reader lifetimes, crashes, and retries create a rich two-step task. |
| 8 | RCU | Old-reader stability and grace-period reclamation are observable under deterministic scheduling. |
| 9 | Incremental parsing | Subtree identity and localized callback counts strongly distinguish true incremental behavior. |
| 10 | S3-FIFO | Exact traces are easy to grade, the policy is realistic, and contamination is lower than ARC/LRU. |
| 11 | Deficit round robin | Variable-cost dispatch order makes fairness behavioral rather than merely asymptotic. |
| 12 | Hierarchical timing wheel | Virtual-time traces expose cascading, wraparound, ordering, and cancellation semantics. |
| 13 | Streaming Aho–Corasick | Chunk-boundary matches and bounded retention force stateful streaming behavior. |
| 14 | Exact geometric predicates | Adversarial coordinates create unmistakable correctness differences from epsilon-based code. |
| 15 | Rendezvous/consistent hashing | The precise set of remapped keys makes stability under membership churn directly gradeable. |

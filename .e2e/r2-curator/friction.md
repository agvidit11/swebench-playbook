# friction.md — r2-curator (engineer half)

Appended as I go. One entry per place the playbook was unclear, missing, wrong,
self-contradictory, or slower than it should have been.

---

## F1 — `A2-idea-generate.md` §8 line 1 says "Read `HANDOFF A1`". There is no `HANDOFF A1`.

**File:** `A-source/A2-idea-generate.md:272`
> `| 1 | Read HANDOFF A1 | LOC, subsystem count, HEAD sha and the named existing entry point copied into your run notes. Do not re-measure |`

I start at `A2` by instruction, and `A1` was run by a different agent in a different session
that produced `runs/shortlist-proto.md`, not a `HANDOFF A1` block. The shortlist entry has LOC,
subsystem count and the grading path, but **not the HEAD sha** — which `A2`'s own FACTS block
(`A2:292`) requires and which `A3`'s GATE 0 needs to classify tokens IN-BASE vs COINED.

I had to clone and derive it myself (`88dee99a85921bd0f20955e1d7efbaf896fc17f3`). Cheap here
(~40 s) but it is a real gap: the playbook assumes `A1`'s output format and the actual upstream
artefact is a different format. Either `A1` should be specified to emit the HANDOFF block into
the shortlist, or `A2` step 1 should say "read `HANDOFF A1` **or the shortlist entry**, and
derive HEAD yourself if absent".

**Cost:** ~2 min.

---

## F2 — Java/Maven recipe is NOT in the playbook. It is in another pair's friction log.

**File:** nowhere in `~/swebench-playbook/`. The working recipe lives in
`.e2e/pair-santuario/friction.md:12-61`.

`A1-repo-screen.md` owns "harness timing" and `B4-solution-env.md` owns the Dockerfile, but
neither carries the host-specific facts that make a Java build work here:

- GCS mirror `https://maven-central.storage-download.googleapis.com/maven2` as `<mirrorOf>central</mirrorOf>`
- `--network=host` mandatory on `docker run`, not only `docker build`
- mirror **and** both fwdproxy stanzas must be in the **same** `settings.xml`, because
  `~/.m2/settings.xml` on this host ships proxies and no mirror

I only knew this because my dispatch brief quoted it. A pair that read only the playbook would
have rediscovered it, and the santuario log says that costs ~25 min. This belongs in
`reference/R3-landmines.md` (it is exactly a packaging trap) with a per-language section.

Verified working on curator, cold, this run: `BUILD SUCCESS`, all 13 modules, artifacts pulled
through `gcs-central`. Curator additionally needs `rm .mvn/extensions.xml` (Develocity extension
is unresolvable) — that one IS in the shortlist entry.

**Cost:** 0 min for me, ~25 min for anyone without the brief.

---

## F3 — `A3` GATE 3 fires far too late for a repo whose open issues are imported JIRA tickets.

**File:** `A-source/A3-idea-gate.md:116-141` (GATE 3 sits after GATE 0/1/2).

Gate order is justified in `A3:14` as an economy argument — free gates first. That economy
assumes disclosure checking is expensive. On `apache/curator` it is nearly free and it is the
gate that actually bites, because the repo's 121 open issues are **bulk-imported Apache JIRA
tickets**, each carrying a full root-cause diagnosis and frequently a proposed patch in the
comments.

Measured this run: my strongest self-generated candidate (`ServiceDiscoveryImpl.reRegisterServices()`
aborting the whole fan-out on the first per-instance failure, and running on the
`ConnectionStateManager` event thread) was killed outright by **open issue #840 / CURATOR-320**,
whose body states the diagnosis verbatim and whose comments contain a **posted diff** introducing
`reRegisterExecutor` / `reRegisterFuture` / `reRegisterRetryCount` — i.e. exactly the remedy — with
the maintainer replying "can you please create a PR with your change?".

One `gh api repos/apache/curator/issues?state=open` call (2 s, 121 rows) would have pre-empted
~25 min of my reading. **Recommendation:** add to `A2` §8 as a step between 5 and 6 — "dump the
full open-issue title list once, per repo, before writing any card" — so that ideation is steered
away from disclosed areas rather than gated after the fact. The current order pays full ideation
cost on candidates that were dead before they were written.

**Cost:** ~25 min.

---

## F4 — The round-2 dispatch brief and the repo evidence disagree about what "121 open issues" means.

Not a playbook-file defect, but a live mis-cue worth recording.

My brief says: *"Also note 121 open issues is a real defect supply — unlike round 1's frostdb,
which had 8 and yielded nothing."* `A1-repo-screen.md` likewise treats issue density as a
positive screening signal.

On this repo the sign is **inverted**. The 121 issues are not a supply of un-diagnosed defects;
they are a supply of *publicly diagnosed* ones, many with patches inline. High issue density on a
JIRA-imported Apache repo is a **disclosure hazard**, not a defect supply. Any candidate drawn
from the same subsystem as an open ticket is dead at GATE 3 regardless of whether I found it
independently.

`A1`'s issue-density criterion should distinguish "open issues" from "open issues with
maintainer-grade diagnoses attached", because they point in opposite directions.

**Cost:** it shaped where I looked first, so folded into F3's 25 min.

---

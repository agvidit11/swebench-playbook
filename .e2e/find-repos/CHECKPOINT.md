# CHECKPOINT — run `find-repos`

**Last updated:** run COMPLETE. `A1` exited **EXIT MET — 4 survivors**. Nothing committed,
nothing pushed.

## Where I am

- **Final state:** `A1` complete, with the four category gates from the brief applied as
  additional hard gates. `A2` was **not** entered — that is one dispatch per surviving repo
  and belongs to the next act.
- **Run dir:** `/home/agvidit/swebench-playbook/.e2e/find-repos/`
- **Not `PUSH-READY`.** No task directory exists anywhere. No `git commit`, no `git push`,
  no write outside the run dir and `/tmp/a1cat/`.

## The result in one line

36 repos screened; **4 survive every A1 gate *and* all four category gates**, each with a
containerised, offline, deterministic graded path under 10 seconds:
**`concourse/concourse` · `crossplane/crossplane` · `cloudnative-pg/cloudnative-pg` ·
`kubernetes-sigs/kustomize`**.

## Fixed facts (do not re-derive — `A2` consumes these)

| repo | clone | HEAD | LOC / SUB | licence | real open issues | graded path (container) |
|---|---|---|---|---|---|---|
| `concourse/concourse` | `/tmp/a1cat/clones/concourse` | `a3484bc8cc3655a59583527667708d6b8fdd8e50` | 207,716 / 193 | Apache-2.0 | 70 | 5s (`atc/exec`, `atc/scheduler`, `atc/engine`) |
| `crossplane/crossplane` | `/tmp/a1cat/clones/crossplane` | `bbd1a68178e591bde2265872a15d436116e030b8` | 54,516 / ~36 | Apache-2.0 | 115 | 7s (`internal/controller/apiextensions/...`) |
| `cloudnative-pg/cloudnative-pg` | `/tmp/a1cat/clones/cloudnative-pg` | `a6afa71c8e3a5bbcfb36fd8eaa3986c12f1f3405` | 110,380 / 42 | Apache-2.0 | 229 | 8s (`pkg/specs`, `pkg/postgres`, `pkg/reconciler`) |
| `kubernetes-sigs/kustomize` | `/tmp/a1cat/clones/kustomize` | `078ab6cf8e87a87a4dea4c81a8c3f4519e97dec5` | 56,029 / 176 | Apache-2.0 | 131 | 0.4s (`internal/accumulator`, `filters`, `krusty/localizer`) |

All four: `golang:1.27`, `--network=host`, `build_timeout_sec: 1800`, no Maven mirror, no
system libs, no database. `GOTOOLCHAIN=local` set; `GOWORK=off` required on kustomize only.

**All 15 clones are clean** — `for n in */; do git -C $n status --porcelain | wc -l; done`
returns 0 for every one (atlantis, cayenne, cloudnative-pg, commons-pool, concourse,
crossplane, guacamole-client, jackrabbit-oak, jdbi, kustomize, postgres-operator, rustup,
syncope, velero, wal-g). Nothing in this run wrote into a clone; every container run mounted
the clone `:ro` and copied it in.

## Carried exclusions for `A2` — fenced surfaces, NOT repo kills

1. **concourse** — `fly validate-pipeline` and cross-pipeline cycle detection
   (`atc/configvalidate`): `ananyaa/concourse-circular-dependency-check`.
   Also **do not** target `atc/scheduler/algorithm` — its suite needs a live Postgres.
   Also avoid `atc/api` (18 commits/90d) and `atc/creds` (21) — maintainer-hot.
2. **kustomize** — (a) builtin generator plugins / `api/internal/generators` /
   `api/resmap`: `pratyusha-mandapati/generate_resourceQuota_files`; (b) `patches` +
   `target.annotationSelector` selection and application:
   `evyatarh/kustomize-annotationselector`; (c) `patchesJson6902` — RFC 6902 is a published
   spec **and** `gopkg.in/evanphx/json-patch.v4` is a direct dependency, so that surface
   fails CAT-1 and CAT-2 together.
3. **cloudnative-pg** — **do not** target `internal/controller` (25 commits/90d),
   `pkg/management/postgres` (15) or `pkg/reconciler` (12). The CAT-4 pass is conditional on
   pinning to `pkg/specs` / `pkg/postgres` (6 each per 90 days).
4. **crossplane** — avoid `internal/controller/pkg` (29 commits/90d, the package manager).
5. **All four** — the `expose_interface` shape. Corpus is 1 passed / 13 failed; the named
   `semantic_bugs` surface per repo is in `artifacts/shortlist.md`.

## Docker mutex

Held **five times**, always scoped to the single `docker run`, never across the act:

```
echo "<repo>/A1-G10/$$" > /tmp/swebench-docker.holder
flock -w 1800 /tmp/swebench-docker.lock docker run --rm --network=host ...
: > /tmp/swebench-docker.holder
```
Acquired without contention each time (`flock -w 3 … echo LOCK FREE` at start). Holder file
truncated after every run; **it is empty now**. Two unrelated `smoltcp-*` containers from
another session were running throughout — I did not touch them.

## What is DONE, with evidence

| | Evidence |
|---|---|
| Dedup corpus refreshed | `git pull` → `Already up to date.`, HEAD `d8472c4` 2026-09-02, **20 days stale**; propagated to every read as "0 local hits = UNKNOWN" |
| Peer repo pools read | `/tmp/e2e-pools/` (5 files) **plus two the act-file does not name** — `mohammedram:docs/codimango-used-upstream.txt` (1,171 slugs) and `weili4-swebench:EXCLUSION-LIST.md` (2,217 lines of measured outcomes) → `friction.md` F2 |
| G1 live sweep, 36 repos | `gh search code --owner codimango` at an 8–9s cadence, every call exit 0; hits read and classified, not counted |
| G1 local sweep, survivors | §3 commands + symbol sweeps + dependency-org sweeps + diff against `/home/agvidit/swe-bench-pro-agvidit/*/tests/config.json` → no self-collision |
| G2 | run on all **15** clones; killed `jdbi`, `cayenne`, `jackrabbit-oak`, `velero`, `wal-g` |
| G3 | three §4 signals, identity-based only, **no commit-body grep anywhere**; every identity hit printed with `%an <%ae>` and read |
| G4 | search-API issue/PR split for GitHub trackers; **JIRA REST sweep** for `CAY` (441), `GUACAMOLE` (468), `SYNCOPE` (20), `POOL` (23) |
| G7 | §6 `LOC=`/`SUB=` commands, chunk-summing awk |
| G8 | existing entry point named per survivor with `file:line` |
| G9 | fixture dirs enumerated **and** test-to-source ratio measured for all four |
| **G10** | **throwaway container, all four, under `flock`** — receipts in `artifacts/shortlist.md` |
| CAT-1/2/3/4 | per-survivor verdict table with command output, incl. the measured `apimachinery`/`strategicpatch` absence in kustomize |
| friction log | `friction.md`, F1–F13, tagged `EARLIER:` / `REPEAT:` / `WASTE:` / `PINPOINT:` |

## Decisions made, with the reason — do not relitigate

1. **4 survivors, not 5.** The brief asks for 5–8; A1 §1 says ≥3 is a target, never a quota,
   and that manufacturing a survivor is a failure of the act. The two candidates that would
   have made 5 and 6 are `apache/guacamole-client` (G9: 19 test files for 833 sources, 0 in
   the target module) and `zalando/postgres-operator` (CAT-4: all 44 commits/90d in the four
   packages worth targeting; also G4 458, G7 ~5 packages, and `pkg/cluster` does not build
   without generated mocks). Both are written up as rejects with their numbers. I did not
   round either up.
2. **I did not accept any pre-screen**, including the prior run's shortlist and the two org
   pools. Every gate was run first-hand. The prior run's rejects were reused only as a
   *do-not-re-screen* list, never as evidence for a survivor.
3. **`rust-lang/rustup` is the clearest demonstration that the brief was right.** It is
   0-peer, 0.05% AI-authored, Apache-2.0/MIT, alive, well-sized, with real test infra — a
   textbook A1 shortlist row — and it is unworkable, because `src/cli` took 82 commits and
   `src/dist` 37 in the last 90 days. Recorded as a CAT-4 kill with the numbers.
4. **No waiver was taken on `AGENTS.md`.** Two repos carried one (`apache/cayenne`,
   `apache/jackrabbit-oak`); both are genuine AI-agent configurations, not contribution
   guides, so the gate's verdict and mine agree. Content and verdict are both in
   `artifacts/shortlist.md` under **OPEN QUESTION**, `Owner: human`. The question I am *not*
   deciding is whether G2 should ever distinguish the two shapes.
5. **kustomize's CAT-1 was measured, not assumed.** I expected it to fail — strategic-merge
   patch has a famous importable reference implementation and kustomize reimplements it in
   `kyaml/yaml/merge2`. `grep -rn "apimachinery" */go.mod` and
   `grep -rn "util/strategicpatch" --include='*.go'` both return nothing, so the reference
   implementation is **not importable in-tree** and the gate passes. Only the RFC-6902 path
   is exposed, via `gopkg.in/evanphx/json-patch.v4`, and that surface is excluded.
6. **crossplane's G9 is a conditional pass, stated as such.** It has zero `testdata/`
   directories. It passes on 45.1% test-to-source and two table-driven suites of 1,830 and
   2,299 lines. If `A2`/`A3` finds the target package's fixtures are in fact stub-shaped,
   that is an N03 kill and the repo should be dropped without argument.

## If someone picks this up

- **Next act is `A2`, one dispatch per surviving repo**, in the rank order in
  `artifacts/shortlist.md`. `A2` must **not** re-measure LOC/SUB or the timings — they are
  in the table above and in the HANDOFF.
- **Do not re-screen the 32 rejects.** Each carries the gate and the number that killed it.
  Three of them (`rustup`, `syncope`, `postgres-operator`) look clean on every A1 gate and
  will be re-proposed by any screen that lacks the churn gate — the rejects table exists
  precisely to stop that.
- **Parked, worth a later look:** `apache/commons-pool` is clean on every gate except size
  (15,910 LOC, three packages) — if the size floor is ever relaxed for a single-turn task it
  is a real candidate, with JIRA `POOL` at 23 open issues.
- **The two org lists in `friction.md` F2 are reusable** and should be pulled at the start of
  any future lane; `weili4-swebench:EXCLUSION-LIST.md` in particular records measured
  outcomes (scores, not candidates) for ~25 repos.

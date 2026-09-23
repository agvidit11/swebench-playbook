# A1 SHORTLIST — run `find-repos`, 2026-09-22

Act-file `A-source/A1-repo-screen.md` **plus the four category gates** from the run brief.
Lane: cross-language (Go / Rust / Java / Ruby), sub-domains systems_and_infra ·
web_backend · devops · security_and_privacy.

**36 repos screened. 4 survivors. 32 evidenced rejects.**

Corpus HEAD used for every local sweep:

```
$ cd /tmp/llc && git pull
Already up to date.
$ git log -1 --format='%H %ci'
d8472c4c54ec0dcf9f2a951f1ab77b840f1aa308 2026-09-02 15:17:05 -0400     # 20 days stale
```

A zero-hit local read inside that 20-day window is **UNKNOWN, not clean** — which is
exactly why the live sweep is run as a peer, not a supplement. See `friction.md` F5: the
local corpus caught a kustomize peer the live sweep missed, and the live sweep caught
peers the local corpus missed. Both directions fired in this run.

---

## §9 shortlist rows — SURVIVORS

`slug | licence | stars | last commit | real open issues | peer verdict (local+live) | AI-authorship % (method) | LOC / subsystems | name-free hosting | graded-path s MEASURED | rank`

| # | slug | licence | stars | last commit | real open issues | peer verdict | AI-auth % (method) | LOC / SUB | name-free hosting | graded path (container, MEASURED) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `concourse/concourse` | Apache-2.0 | 7,905 | 2026-09-19 | **70** (89−19) | **1 peer**, on the `fly validate-pipeline` CLI — excluded, not a kill | **0%** — 0/31,404 by identity; 0/73 agentic branches; no release-note convention | 207,716 / 193 | YES — `exec.Step.Run(ctx, RunState) (bool, error)` | DEPS 8s · BUILD 52s · **GRADED 5s** · OFFLINE 2s |
| 2 | `crossplane/crossplane` | Apache-2.0 | 12,098 | 2026-09-22 | **115** | **0 peers**, both sweeps | **0%** — 0/11,778 by identity; 0/159 branches | 54,516 / ~36 | YES — `composite.Reconciler.Reconcile` | DEPS 8s · BUILD 26s · **GRADED 7s** · OFFLINE 3s |
| 3 | `cloudnative-pg/cloudnative-pg` | Apache-2.0 | 9,339 | 2026-09-22 | **229** | **0 peers**, both sweeps | **0%** — 5 identity hits, all humans named *Devin* (read, FP); 0/82 branches | 110,380 / 42 | YES — `specs.EnvConfig.IsEnvEqual` / `podspec_diff` | DEPS 2s · BUILD 29s · **GRADED 8s** · OFFLINE 3s |
| 4 | `kubernetes-sigs/kustomize` | Apache-2.0 | 12,167 | 2026-09-17 | **131** | **2 peers** — generator plugin + `annotationSelector` patch selection — two exclusions | **0.01%** — 1/7,245 by identity; 0/149 branches | 56,029 / 176 | YES — `krusty.Kustomizer.Run` | DEPS 13s · BUILD 8s · **GRADED 0.4s** (subset) · OFFLINE ✓ |

### Ranking rationale (§9, applied only after all gates passed)

Sub-domain gap: `systems_and_infra` −3.60, `web_backend` −3.91, `devops_and_tooling` **+4.88**.
All four are Go (`−1.95`). None is in a saturated coordinate, but kustomize sits closest to
`devops_and_tooling` and carries two peer exclusions and the `json-patch.v4` CAT-1 exposure,
so it ranks last despite having the cleanest churn profile of the four.

---

## THE FOUR CATEGORY GATES — per survivor, with the command output

### 1 · `concourse/concourse` @ `a3484bc8cc3655a59583527667708d6b8fdd8e50`

| gate | verdict | evidence |
|---|---|---|
| **CAT-1** compatibility / reimplementation / translation | **PASS** | Concourse is not a reimplementation of anything; there is no second implementation of the ATC. Nothing importable determines its behaviour. |
| **CAT-2** published spec | **PASS** | No external spec. Pipeline semantics, step lifecycle, resource-version resolution and build scheduling are Concourse's own design. Remove nothing — the whole engine survives the subtraction. |
| **CAT-3** can it yield anything but `expose_interface` | **PASS** | `atc/exec` (76 files) implements step execution behind a fixed `Step.Run(ctx, RunState) (bool, error)` interface that already exists; a defect changes *build outcome*, not API surface. The one existing peer task is the `expose_interface` shape (`--cross-pipeline` flag) and sits in a different package. |
| **CAT-4** upstream churn in target subsystem | **PASS** | see below |

```
$ git log --since=90.days --oneline -- atc/exec       | wc -l   -> 1     (365d: 36, 76 files)
$ git log --since=90.days --oneline -- atc/scheduler  | wc -l   -> 5     (365d: 16, 24 files)
$ git log --since=90.days --oneline -- atc/engine     | wc -l   -> 3     (365d: 34, 23 files)
$ git log --since=90.days --oneline -- atc/policy     | wc -l   -> 0
$ git log --since=90.days --oneline                   | wc -l   -> 230   (repo alive)
# the maintainer's 90d activity is in atc/api (18) and atc/creds (21), NOT in the target
$ git log --since=90.days --format='%an' | sort | uniq -c | sort -rn | head -3
    134 Taylor Silva
     15 Kump3r
     13 Tobias Macey
```

**`semantic_bugs` surface, one sentence.** `atc/exec` step lifecycle: `TaskStep.Run` /
`GetStep.Run` decide what gets registered in `RunState`'s artifact repository and whether a
step's outcome is *failed* versus *errored*, so a defect there (an artifact bound under the
wrong scope, or an error mapped to the wrong terminal state) is observable as a wrong build
status through the already-exported `exec.Step.Run(ctx, RunState) (bool, error)` contract.

**G9 [N03]:** `atc/exec/execfakes` + `atc/engine/enginefakes` are the repo's own generated
fakes, used by its own 708 `_test.go` files (63.3% test-to-source). Real fixture corpus at
`atc/scheduler/algorithm/testdata`. **Caveat carried forward:** `atc/scheduler/algorithm`'s
suite needs a live Postgres (`suite_test.go`), so the algorithm package is NOT in the
gradeable subset — `atc/exec`, `atc/scheduler` (non-algorithm) and `atc/engine` are.

---

### 2 · `crossplane/crossplane` @ `bbd1a68178e591bde2265872a15d436116e030b8`

| gate | verdict | evidence |
|---|---|---|
| **CAT-1** | **PASS** | No reference implementation. `crossplane-runtime` is a helper library authored by the same project, not a second implementation of composition. |
| **CAT-2** | **PASS** | Composition, XRD and the function pipeline are Crossplane's own design, versioned in its own API group. Subtract everything externally determined (only CRD/OpenAPI validation) and the whole composition engine remains. |
| **CAT-3** | **PASS** | `composite.Reconciler.Reconcile` is an existing entry point; readiness determination, connection-detail propagation and composed-resource naming are behaviours *behind* it, not new API. |
| **CAT-4** | **PASS** | see below |

```
$ git log --since=90.days --oneline -- internal/controller/apiextensions/composite | wc -l -> 4   (365d: 51)
$ git log --since=90.days --oneline -- internal/controller/apiextensions/offered   | wc -l -> 0   (365d: 12)
$ git log --since=90.days --oneline -- internal/dag                                 | wc -l -> 0   (365d: 5)
$ git log --since=90.days --oneline -- cmd/crossplane                               | wc -l -> 0   (365d: 48)
$ git log --since=90.days --oneline                                                 | wc -l -> 207 (repo alive)
# the hot package is internal/controller/pkg (29) — the package manager, NOT the target
$ git log --since=90.days --format='%an' | sort | uniq -c | sort -rn | head -3
     62 Jared Watts
     44 Philippe Scorsolini
     44 crossplane-renovate[bot]
```

**`semantic_bugs` surface, one sentence.** `internal/controller/apiextensions/composite`:
`composition_functions.go` and `connection.go` decide which composed resources count as
*ready* and which connection details survive across pipeline steps, so a defect there (a
resource marked ready when its readiness check did not actually match, or a detail silently
overwritten by a later step) is observable in the composite's status and connection secret
through the existing `Reconciler.Reconcile` path.

**G9 [N03] — MARGINAL, stated honestly.** Crossplane has **zero** `testdata/`, `fixtures/`
or golden directories. Its substrate is in-code table-driven tests
(`composite/reconciler_test.go` **1,830 lines**, `composition_functions_test.go` **2,299
lines**) plus `internal/xfn` and `internal/dag/fake`. Test-to-source ratio **45.1%**
(121 test files / 268 source files) — healthy, and the fakes are the repo's own idiom
rather than stubs invented for a task, so this is a PASS with a named risk, not a waiver.
Compare `apache/guacamole-client`, rejected below at **2.3%**.

---

### 3 · `cloudnative-pg/cloudnative-pg` @ `a6afa71c8e3a5bbcfb36fd8eaa3986c12f1f3405`

| gate | verdict | evidence |
|---|---|---|
| **CAT-1** | **PASS** | No reference implementation. `zalando/postgres-operator` is a *different* operator with a different design, not an importable reference for CNPG's behaviour. |
| **CAT-2** | **PASS** | PostgreSQL's replication protocol is documented, but CNPG's failover target selection, PVC lifecycle, fencing and rollout-diff policy are all its own. Subtract the spec and the operator's entire decision layer remains. |
| **CAT-3** | **PASS** | `pkg/specs` and `pkg/reconciler/*` are pure functions over API objects with existing exported entry points; a defect changes *which pod gets rolled*, not the API. |
| **CAT-4** | **MARGINAL PASS — the weakest of the four, flagged** | see below |

```
$ git log --since=90.days --oneline -- pkg/specs                | wc -l -> 6    (365d: 37)
$ git log --since=90.days --oneline -- pkg/postgres             | wc -l -> 6    (365d: 20)
$ git log --since=90.days --oneline -- pkg/utils/hash           | wc -l -> 0    (365d: 2)
$ git log --since=90.days --oneline -- pkg/certs                | wc -l -> 0    (365d: 4)
# HOT, avoid: internal/controller 25 · pkg/management/postgres 15 · pkg/reconciler 12
$ git log --since=90.days --oneline                             | wc -l -> 206
$ git log --since=90.days --format='%an' | sort | uniq -c | sort -rn | head -4
     65 renovate[bot]
     53 Marco Nenciarini
     18 Armando Ruocco
     13 Leonardo Cecchi
```

**Honest read:** this is a busy repo — 206 commits and 210 open PRs in flight. It passes
CAT-4 only *if the target is pinned to `pkg/specs` / `pkg/postgres`* (6 commits per 90 days
each, i.e. one per fortnight). It is **not** the oxigraph shape (no single expert with 5
merges in the 10 days before HEAD; three named humans plus renovate), but it is the closest
of the four and is ranked accordingly. **Do not target `internal/controller` or
`pkg/management/postgres`.**

**`semantic_bugs` surface, one sentence.** `pkg/specs/podspec_diff.go` +
`EnvConfig.IsEnvEqual` decide whether a running pod is considered in sync with the desired
spec, so a defect there (a spec field omitted from the comparison, so a change never
triggers a rollout) is observable through the existing `specs` entry points and the repo's
own Ginkgo suites without naming anything new.

**G9 [N03]:** 4 `testdata/` dirs (`pkg/postgres/testdata`,
`pkg/management/postgres/logpipe/testdata`, `internal/cmd/manager/pgbouncer/run/testdata`,
`tests/e2e/fixtures`); 429 test files / 575 source files = **74.6%**, the highest of the four.

---

### 4 · `kubernetes-sigs/kustomize` @ `078ab6cf8e87a87a4dea4c81a8c3f4519e97dec5`

| gate | verdict | evidence |
|---|---|---|
| **CAT-1** | **PASS, but MEASURED not assumed — and one surface is excluded** | see below |
| **CAT-2** | **PASS with an exclusion** | Kustomization semantics are kustomize's own. **`patchesJson6902` is RFC 6902**, a published spec, *and* `gopkg.in/evanphx/json-patch.v4` is a direct dependency → that surface fails both CAT-1 and CAT-2. Excluded. What remains after the subtraction — name-reference resolution, replacements, accumulation order, generator behaviour — is entirely kustomize's own policy. |
| **CAT-3** | **PASS** | `krusty.Kustomizer.Run` returns a `ResMap`; a defect is wrong YAML out of an existing entry point, not new API. |
| **CAT-4** | **PASS — the strongest of the four** | see below |

The CAT-1 check I expected to fail, and it did not. Strategic-merge-patch has a famous
importable reference implementation (`k8s.io/apimachinery/pkg/util/strategicpatch`), and
kustomize reimplements it in `kyaml/yaml/merge2`. That is the prism shape. It is **not**
present:

```
$ grep -rn "apimachinery" api/go.mod kyaml/go.mod kustomize/go.mod
(no output)
$ grep -rn "util/strategicpatch" kustomize --include='*.go' --include='go.mod' | grep -v '/.git/'
(no output)                      # the reference implementation is NOT importable in-tree
$ head -14 api/go.mod
module sigs.k8s.io/kustomize/api
go 1.26.0
require (
    github.com/blang/semver/v4 v4.0.0
    github.com/go-errors/errors v1.5.1
    github.com/stretchr/testify v1.12.1
    go.uber.org/goleak v1.3.0
    go.yaml.in/yaml/v2 v2.4.4
    gopkg.in/evanphx/json-patch.v4 v4.13.0        # <-- RFC 6902 ref impl: excludes json6902 only
    k8s.io/kube-openapi v0.0.0-20260721132016-d427ff9ee9ad
    sigs.k8s.io/kustomize/kyaml v0.21.1
    sigs.k8s.io/yaml v1.6.0
)
```

```
$ git log --since=90.days --oneline -- api/internal/accumulator | wc -l -> 0
$ git log --since=90.days --oneline -- api/internal/generators  | wc -l -> 0
$ git log --since=90.days --oneline -- api/resource             | wc -l -> 0
$ git log --since=90.days --oneline -- api/builtins             | wc -l -> 0
$ git log --since=90.days --oneline -- kyaml/yaml/merge2        | wc -l -> 0
$ git log --since=90.days --oneline -- kyaml/kio                | wc -l -> 0
$ git log --since=90.days --oneline -- api/filters              | wc -l -> 1
$ git log --since=90.days --oneline -- api/krusty               | wc -l -> 7
$ git log --since=90.days --oneline                             | wc -l -> 83
$ git log --since=90.days --format='%an' | sort | uniq -c | sort -rn | head -4
     38 kubernetes-prow[bot]
     22 dependabot[bot]
      5 Yugo Kobayashi
      4 koba1t
```
Roughly **12 human commits in 90 days** across the whole repo. Nobody is committing in any
target subsystem.

**`semantic_bugs` surface, one sentence.** `api/internal/accumulator` name-reference
resolution decides which renamed target a referring field adopts, so a defect there (a
reference bound to the wrong candidate when two resources share a name across namespaces,
or a back-reference not updated after a prefix transformer) is observable as wrong YAML
from the existing `krusty.Kustomizer.Run` entry point against `api/krusty/testdata`.

**G9 [N03]:** 11 `testdata/` dirs, `api/krusty/testdata` is the reusable corpus. 323 test
files / 460 source = **70.2%**.

**G10 caveat, carried:** two tests fail at HEAD in the `api/krusty` root package and both
are environmental, not defects —

```
--- FAIL: TestAddManagedbyLabel (0.00s)                 # asserts a release version string
--- FAIL: TestRemoteLoad_RemoteProtocols (6.23s)        # ssh / ssh_with_colon / ssh_scheme
FAIL    sigs.k8s.io/kustomize/api/krusty   36.7s
```
`TestRemoteLoad_RemoteProtocols` **requires network**, which A1 §8 forbids in a graded
subset. The gradeable subset is therefore `./internal/accumulator/... ./filters/...` plus
`./krusty/localizer` — **0.4s**, offline, deterministic, all `ok`. A baseline f2p/p2p diff
at `base_commit` is mandatory here (`feedback_swebench_f2p_baseline_diff_gate`).

---

## G10 — HARNESS TIMING, MEASURED IN A THROWAWAY CONTAINER

Every run was serialised through the mutex and wrote its identity to the holder file:

```bash
echo "$n/A1-G10/$$" > /tmp/swebench-docker.holder
flock -w 1800 /tmp/swebench-docker.lock docker run --rm --network=host \
  -v /tmp/a1cat/clones/$n:/src:ro -w /work -e GOTOOLCHAIN=local golang:1.27 bash -c '...'
: > /tmp/swebench-docker.holder
```

| repo | image | deps | build | graded (online) | graded (`GOPROXY=off`) | wall | flags needed | `build_timeout_sec` |
|---|---|---|---|---|---|---|---|---|
| kustomize | `golang:1.27` | 13s | 8s | 36s full / **0.4s subset** | ✓ identical | 80s | `--network=host`; **`GOWORK=off`** for offline (`go.work` rejects `-mod=mod`) | 1800 |
| crossplane | `golang:1.27` | 8s | 26s | **7s** all `ok` | **3s** all `ok` | 48s | `--network=host` | 1800 |
| cloudnative-pg | `golang:1.27` | 2s | 29s | **8s** all `ok` | **3s** all `ok` | 70s | `--network=host` | 1800 |
| concourse | `golang:1.27` | 8s | 52s | **5s** all `ok` | **2s** all `ok` | 83s | `--network=host`; go.mod wants **go 1.27.1**, host has 1.26.5 → container is mandatory | 1800 |

All four: graded subset **<10 min** (worst 8s), **offline** (`GOPROXY=off` re-run identical),
**deterministic** (`-count=1`). No Maven mirror, no system libs, no DB.

---

## THE 32 REJECTS, WITH THE GATE THAT KILLED EACH

Reported per A1 §1 so the next lane does not re-screen them.

### Killed by **G1** — peer tasks on the repo (live sweep, count = distinct peer tasks read)

| repo | peers | representative peer tasks read |
|---|---|---|
| `openfga/openfga` | ≥5 | shunmiyake `-1e464a7-v1`, xiaofangchen `-0c75947-v1`, jasonclee `-1586caa-v1`, zzx `openfga-check-grant-path`, nithyaarumu `openfga-intersection-check` |
| `prometheus/alertmanager` | ≥8 | `inhibit-source-resolved-fallback`, `silence-admission-and-retry-terminal-state`, `alertmanager-routing-validation`, `alertmanager-silence-validation`, `alertmanager-composite-alarms`, `alertmanager-pagination-silence-purge`, andlee `-2c8da51-skills-v1`, chrislin9 `pebble-integration` |
| `hibiken/asynq` | ≥10 | olagub ×4 (`queue-limits`, `queue-drain`, `lease-fencing`, `handler-retry-delay`), lwen ×2, zlmei, jiepan, shivamalisetti, xiaolijiang, sov |
| `fluent/fluentd` | ≥5 | yaakovs `out-forward-stale-keepalive`, vinaygaddam `fair-buffer-scheduler`, shiyingli `FluentYAMLConfigError`, salar `adaptive-priority-flush`, shivamalisetti `lib-upgrade` |
| `solidusio/solidus` | ≥10 | sramsundar ×3 (`stockalloc`, `compliance`, `taxround`), josesolorzano `promo-combine`, adityabhujle `zip-bulk-promotion`, jessicakim ×2, rohitbhalke, fjamba, jacsteyn |
| `SeaQL/sea-orm` | ≥8 | zivk ×3 (`query-optimizer`, `query-batcher`, `join-optimizer`), suyashpatel98 ×3, shunmiyake, muhammed `rbac-precedence` |
| `helm/helm` | ≥5 | sramsundar `coalesceprov`, shrenikd `docseparator`, philuu `history-prune-guard`, ericpastuer `dependency-cycle`, archerzhang `helm-task-3` |
| `ruby-grape/grape` | ≥15 | maddyli `range-requests`, neilgoyal `request-gating-v2`, stevejia ×2, abhishekraj ×2, rps4149, muhammed, gleize, max860113, xinyij, luchen5, namanahuja, quinnlee, kevwumeta, dguo |
| `resilience4j/resilience4j` | ≥7 | farhood `-cd06f6f-v1`, somesh29 `budget-coupled-rate-limited`, dharmesh23 `circuit-retry-leak` (+v2), sapirb `retry-negative-interval-npe`, amitaroralive2 `circuitbreaker-dynamicconfig`, ajiteshj, mehringer |
| `quartz-scheduler/quartz` | ≥8 | bkhaneja ×6 (`concurrent-jobs`, `retries-dlq`, `misfire-threshold`, `job-history`, `job-checkpointing`, `idempotent-posting`, `dag-job-chaining`), saravana `cron-final-fire-time`, shengxiong `quartz-core` |
| `mybatis/mybatis-3` | ≥4 | alonmiz `bind-context-propagation` (3-step MT), locharam ×2, yuliiapedash, repogen |
| `quickwit-oss/tantivy` | ≥4 | srv `perf-optimize`, mohaimin `trans-index`, marchenko `optimization-loop`, ziqiwang `query-rewriting-expansion` |
| `mozilla/sccache` | ≥5 | sjali ×2, philuu `dir-dep-invalidation`, preethesh `keytrace`, zhijiazhang `serialize-diagnostics-artifact` |
| `syncthing/syncthing` | ≥5 | bohdankorn ×2, muhamedgamal ×2, weili4 `AVOCADO-BRIEF-syncthing-abort-download`, awesanekar RL corpus |
| `kopia/kopia` | ≥3 | rahulkudva ×3 (`upload-limit-hashed-bytes`, `restore-skip-existing`, `buzhash-splitter-degenerate`) |
| `karafka/karafka` | ≥4 | guptasachin `failure-mode-catalog`, harshitgoyal `-30270d1-v1` (3-step MT), vinaygaddam `capacity-aware-replica-rebalance`, xtruan ×2 |
| `liquibase/liquibase` | ≥10 authors | diyama, harisudha, ibardson, shaulzorea, fomichevsj, derick, arultayal … |
| `h2database/h2database` | ≥12 authors | aec, awwadhala, chauthai, kapshar, l3fang, ovunc, roshchin, saravana, shridhar, somesh29 … |
| `pgjdbc/pgjdbc` | ≥6 authors | garrettnickersn, roshchin, somesh29, ovolkov, streamforge … |
| `rqlite/rqlite` | ≥12 authors | joseph1999, joshbaltar, kgokhale, koko, liadm, malathy, rps4149, shunmiyake, vmessenger … |
| `apache/maven-resolver` | ≥12 authors | changda, demilee, geyuting, halirage, kapshar, roshchin, somesh29, ruixie, cdahdah … |
| `google/go-containerregistry` | ≥7 authors | mijiang, mzzhou, nalinmr, wenboliu, rakeshthakur, zhijiazhang |
| `jaegertracing/jaeger` | ≥8 authors | ctorge, joshbaltar, lajiahui, sramsundar, catherinekang, sdesai9, joseph1999 |
| `nats-io/nats-server` | ≥12 authors | abdelazizsayed, ayagubov, hjiao, kaleksandrov239, mhammad, ramkumarv, rps4149, shunmiyake, sqasem … |
| `weaviate/weaviate` | ≥5 authors | alexfuchs, jolidou, labs-loopy, labs-reach, impossible-tasks |
| `dolthub/dolt` | ≥4 authors | joshbaltar, mke, sashe, shivam0sharma |
| `Homebrew/brew` | ≥10 authors | archerzhang, bhaavan, junhao, vinaygaddam, soso, ddelo, goldin, bharatr, binhuang, jayzong |
| `rubygems/rubygems` | ≥12 authors | abdullahsamma, aishmeta, alonmiz, praneeth9, ravikondreddy, sjali, sramsundar, jayzong … |
| `puppetlabs/puppet` | ≥6 authors | craiggomes, sramsundar, vinaygaddam, aydargizatullin, renhanz, weili4 |
| `jline/jline3` | ≥7 authors | anandpatel, demilee, dihuang, geyuting, rodrigo-at-meta, iliyas |
| `spring-projects/spring-batch` | ≥7 authors | indiragp, streamforge, arultayal, jayzong, tsaqova, yentlin |
| `golang-migrate/migrate` | ≥8 authors | alonmiz, itsdeep, yameng, hasanthi, tejaschandakkar, the-table-app |
| `apache/opendal` | ≥7 authors | dicathywang, jasonwuhere, joshbaltar, mohitraman, tianranwang, weitangse |
| `diesel-rs/diesel` | ≥4 authors | badahal, mvu13, suyashpatel98 |
| `EmbarkStudios/cargo-deny` | ≥7 authors | abdullahsamma, jerryk, sjali, mslwang, rafikn ×2, williamtonthatt |
| `chronotope/chrono` | ≥7 authors | gleize, jdai, lijonathan, luisgt, zivk, weitangse, msollecito |
| `ebean-orm/ebean` | 2 | qlyu `jsonb-dirty-detection`, yangfan `sql-plan-capture` — both cite the upstream PR; race signal |
| `flipt-io/flipt` | **benchmark** | 2 instances in `codimango/swe-bench-pro` itself — the **public SWE-bench-Pro dataset** — plus 5 `synthetic-data-repogen` conversions. Contamination, not just peer density. |
| `restic/restic` | measured dead | `weili4-swebench:EXCLUSION-LIST.md` — `restic-blob-batch-dedup` scored **5/5 on every model, every arm**; the delegatable `SaveBlobs`→`saveBlob` shape |

### Killed by **G2** — agentic artifacts / branches

| repo | evidence |
|---|---|
| `jdbi/jdbi` | **HEAD itself is `Merge remote-tracking branch 'origin/claude-bind-list-values-1550'`.** 12 merged `claude-*` PR branches (`claude-pg-shared-instance`, `claude-timeout-advisory-lock`, `claude-join-reducer-1574`, `claude-commit-callbacks-3021` …); **292 of 6,550 commits (4.5%)** authored by `Claude (on behalf of Steven Schlansker) <stevenschlansker+claude@gmail.com>`; 3 agentic remote branches |
| `apache/cayenne` | `AGENTS.md` + `CLAUDE.md` + `.claude/rules/` — **see the OPEN QUESTION section below** |
| `apache/jackrabbit-oak` | `AGENTS.md` (**269 lines**) + `CLAUDE.md` (`@AGENTS.md`) + `.cursorrules` (`@AGENTS.md`) — see below. Also 673,194 LOC = 4.5× the §6 ceiling |
| `vmware-tanzu/velero` | `.github/copilot-instructions.md` **and 48 of 102 remote branches are `copilot/*`** (`copilot/backport-10047`, `copilot/analyze-compatibility-issues-7492-9448`, …) |
| `wal-g/wal-g` | 3 **closed-unmerged** `copilot/*` branches with real `copilot-swe-agent[bot]` commits — `copilot/add-cleanup-empty-folders`, `copilot/refactor-prepare-config-script`, `copilot/unleash-power-of-copilot` ("Fix file-deletion race semantics in AO uploader test"). A1 §5: closed-unmerged is a hard kill, the fix is public either way. *G1 was clean (0 peers) — this is the "0 peers is a warning, not a green light" case.* |

### Killed by **G4** — issue density / disclosure posture

| repo | count | note |
|---|---|---|
| `zellij-org/zellij` | **1,577** real open issues | (1,937 − 360 PRs) ≫ 500 |
| `runatlantis/atlantis` | **750** real open issues | (917 incl. 167 PRs) > 500. Also 1 peer (sramsundar `deporder`) |

### Killed by **G7** — size / subsystem count

| repo | measurement |
|---|---|
| `apache/commons-pool` | **15,910** non-test LOC in effectively three packages (`pool2`, `.impl`, `.proxy`) — at the <15k floor and the "one or two packages only" clause. G1 was clean (the single hit is a vendored `.pom`) and JIRA `POOL` shows only 23 open issues, so this dies purely on size |

### Killed by **G9 [N03]** — no gradeable fixture substrate

| repo | measurement |
|---|---|
| `apache/guacamole-client` | **19 Java test files for 833 main files = 2.3%**, and **0 tests** in `extensions/guacamole-auth-jdbc` (197 sources) — the richest and quietest module. **0** `testdata`/`fixtures` dirs. Any graded test would be hand-built stubs. Confirmed by the G10 attempt: `mvn -o -pl guacamole-ext test` → `Tests run: 0` then `BUILD FAILURE`. Otherwise attractive: Apache-2.0, 111,433 LOC in band, G2 clean, G3 0/7,464, `guacamole-auth-jdbc` 0 commits/90d, only 1 peer (vikashsinghal) |

### Killed by the **CAT-4 churn gate** (would have passed every existing A1 gate)

| repo | measurement |
|---|---|
| `rust-lang/rustup` | **G1 CLEAN — 0 peer tasks**, both sweeps (all 32 live hits are `rustup-init` lines in other repos' `install.sh`, toolchain files, or discovery pools). G2 clean, G5 Apache-2.0/MIT, G3 3/6,294 = 0.05% and **all three are `Codex <codex@openai.com>` doc-typo commits** (`www/rustup.css`, `ci/actions-templates/README.md`, `doc/user-guide/.../windows-msvc.md`) with zero source touched. Then: `src/cli` **82** commits/90d · `src/dist` **37** · `src/config.rs` **25** · repo **220**, with rami3l merging 54 PRs. Every subsystem worth targeting is under active daily maintenance. **This is the oxigraph failure mode and A1 does not screen for it.** |
| `apache/syncope` | **G1 CLEAN — 0 peer tasks** (the single hit is a longhorizon `REPO.md` that considered and *rejected* it). G2 clean, G3 0/15,857, Apache-2.0, JIRA `SYNCOPE` **20** open issues — an outstanding G4 number. Killed on churn + bus factor: **Francesco Chicchiriccò is 82 of 171 commits in 90 days (84% of human commits)** and is committing in `core/persistence-jpa` (15), `core/provisioning-java` (13), `core/spring` (13), `client/idrepo` (30). The only quiet module, `ext/scimv2` (0/90d), is a **published-spec** surface (SCIM 2.0) → CAT-2. |
| `zalando/postgres-operator` | **G1 CLEAN — 0 peer tasks.** G2 clean (385 branches, 0 agentic), G3 0/3,826, MIT. Killed on three counts: **458** real open issues (top of the 150–500 band); **25,067 LOC in ~5 packages** (near the G7 "one or two packages" clause); and of 44 commits/90d, **44 land in the packages I would target** (`pkg/cluster` 17, `pkg/apis` 15, `pkg/controller` 12, `pkg/util` 11). G10 also fails to build: `pkg/cluster` needs generated mocks (`undefined: mocks.NewMockVolumeResizer`). |

### Killed at desk screen on the category gates, before cloning

| repo | gate | reason |
|---|---|---|
| `micrometer-metrics/micrometer` | **CAT-1 + CAT-3** | A metrics **facade** — every `MeterRegistry` is a translation of a published backend exposition format, and the plausible surface is "add/extend registry N+1", i.e. `expose_interface` (1 passed / 13 failed corpus-wide) |
| `Byron/gitoxide`, `oxc-project/oxc`, `biomejs/biome`, `eclipse/jgit` | **CAT-1** | each reimplements a system whose reference implementation is importable (git / acorn-babel / git) — the `ruby/prism` shape |
| `graphql-java/graphql-java`, `dexidp/dex`, `ory/fosite`, `distribution/distribution`, `containers/youki` | **CAT-2** | GraphQL spec / OIDC / OAuth 2 / OCI distribution / OCI runtime — remove what the spec determines and error reporting remains, the `apache/santuario` shape |
| `projectcontour/contour` | **CAT-1** | a translation library (Ingress/Gateway → Envoy xDS); both sides are published schemas |

---

## OPEN QUESTION — `AGENTS.md` and the G2 hard kill. **Owner: human.**

The brief asks me to report the file's content and the gate's verdict and not to waive.
Two repos hit it. **Neither is the oxigraph shape** (a harmless 49-line human contribution
guide); in both cases the gate's verdict and my reading agree, so no waiver was needed or
taken. Recording the content anyway so the human can set the precedent:

### `apache/cayenne` — G2 verdict: **KILL**. My reading: **agree, kill.**

```
$ ls -la cayenne/AGENTS.md cayenne/CLAUDE.md ; find cayenne/.claude -type f
-rw-r--r-- 24    cayenne/AGENTS.md
-rw-r--r-- 7545  cayenne/CLAUDE.md
cayenne/.claude/rules/cayenne/architecture.md
cayenne/.claude/rules/cayenne-modeler/modeler-architecture.md
cayenne/.claude/rules/cayenne-gradle-plugin/build-jdk.md
cayenne/.claude/rules/cayenne-mcp-server/testing.md
```
`AGENTS.md`, in full — 3 lines:
```
# AGENTS.md

@CLAUDE.md
```
`CLAUDE.md`, 166 lines, opens:
```
# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
## Project Overview
Apache Cayenne is a Java ORM and persistence framework. ...
When generating code, if appropraite use the latest Java syntax vs old ...
```
Added and maintained by the lead maintainer: `4166e87cd 2026-05-17 Andrus Adamchik "Adding
AGENTS.md for agents other than Claude"`, last touched `2026-09-20`. This is an active
Claude Code configuration with four architecture rule files, not a contribution guide —
A1 §4's "contamination oracle" in its strongest form. **Also:** GitHub reports 28 open
issues; the **JIRA** sweep reports **441** (`project=CAY`), which alone would put it in the
150–500 band. Both readings kill it.

### `apache/jackrabbit-oak` — G2 verdict: **KILL**. My reading: **agree, kill.**

```
$ wc -l AGENTS.md CLAUDE.md .cursorrules
269 AGENTS.md
  0 CLAUDE.md      # contents: "@AGENTS.md"
  0 .cursorrules   # contents: "@AGENTS.md"
$ git log --format='%h %ad %an %s' --date=short -- AGENTS.md | tail -1
bdac730edc 2026-03-09 Miroslav Smiljanic OAK-12099 add AGENTS.md (#2745)
```
`AGENTS.md` opens `# AGENTS.md - AI Agent Instructions for Apache Jackrabbit Oak` and
carries per-module doc links, a coverage policy ("Security modules require 100% test
coverage"), and the line *"Do not weaken or remove existing test assertions to make the
build pass"* — i.e. it is written **to** an agent, about this codebase, module by module.
Hard kill. (It would also die on G7: 673,194 LOC, and on CAT-2: JCR is JSR-283.)

**What I am asking a human to settle:** whether G2 should distinguish *"an AI agent
configuration"* (cayenne, oak, velero, jdbi — kill) from *"a human contribution guide that
happens to be named AGENTS.md"* (oxigraph — arguably not a kill). I have not applied any
such distinction here; I applied the gate as written. If the human wants the distinction,
it belongs in A1 §G2 as an explicit two-branch test, not in a shortlist cell.

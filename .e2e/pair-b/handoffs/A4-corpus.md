# HANDOFF A4 — PAIR B corpus prior

Run 2026-10-01 01:47–01:53 UTC. `gh search code "<upstream> org:codimango"`, deduped to
(author-repo, task-dir). Code search is rate-limited to ~10/min; queries were paced.

## Per-repo verdict

| upstream | verdict | peers on this upstream | exclusion zone carried into A3 GATE 1 |
|---|---|---|---|
| `concourse/concourse` | **ADJACENT** | ours `concourse-retry-attempt-state-atomicity`; `joshbaltar-2/swe-concourse-varsource-chain-order`; `ananyaa/concourse-circular-dependency-check` | `atc/exec` retry + attempt state · `atc/creds` var_source **chain ordering / inter-dependent resolution** · cross-pipeline dependency graph from `set_pipeline` + shared resources, and `fly validate-pipeline` |
| `kubernetes-sigs/kustomize` | **ADJACENT** | ours `kustomize-localize-source-fidelity`; `evyatarh/kustomize-annotationselector` | everything `localize` · **JSON6902 patch application (`patchjson6902.Filter`) + `annotationSelector` match-after-mutation**, incl. the YAML-scalar canonicalisation that causes it |
| `zeromicro/go-zero` | **ADJACENT — sharpest risk of the five** | ours ×3 (`flush-accountability`, `mr-cancellation-accounting`, `token-limiter-degradation`); `alonmiz/go-zero-resource-manager-lifecycle` | `core/executors` · `core/mr` · `core/limit` · **`core/syncx` ResourceManager lifecycle/Close/Inject** |
| `open62541/open62541` | **CLEAR except our own seam** | ours `open62541-numericrange-canonical-form-composition` only | `NumericRange` parse/print and anything index-range |
| `spiffe/spire` | **ADJACENT** | ours `spire-bundle-publication-accountability`, `spire-workload-api-delivery-readiness` | bundle publication/accountability · workload API delivery + readiness, incl. the endpoints and managers they touch |

### The one that needs saying out loud

`alonmiz/go-zero-resource-manager-lifecycle` is a **two-step MT task on go-zero at base commit
`84c92d710b9f2ae11c3cbcee242cea40eec42e70` — byte-identical to the HEAD of my clone.** Same repo,
same commit, different subsystem. That is exactly the `feedback_swebench_intra_benchmark_dedup`
signature. It is ADJACENT, not COLLIDES, because the seam is `core/syncx.ResourceManager` and my
open seams are codegen / `rest/httpx` / `core/stores/cache` — but any go-zero card must state its
seam difference explicitly, and a card anywhere near resource lifecycle, Close semantics or
double-close accounting is dead.

### open62541 hit-list caveat

19 of the 27 "hits" for `open62541/open62541` are `*-passpilot` repos (an LLVM compiler-pass RL
project) that merely list open62541 as one build target in a corpus manifest. They are not peer
tasks on this upstream. Verified by task-dir names (`ir2vec-*`, `flat-action-space-*`,
`score-cache-*`). **open62541 is the cleanest of the five**, which is consistent with the brief's
instruction to push hardest there.

## Shape searches

`canonical form multi-turn`, `subsumption`, `set difference canonical` each returned 60 capped
hits dominated by tbench/longhorizon puzzle tasks (ARC mazes, Lean, LaTeX) — the concept words are
too common to discriminate at org scale. Two genuine near-shape peers exist and are both on
unrelated upstreams: `andlee-swe-bench/andlee_openstack__heat-...-output-condition-subsumption` and
`ikrom-swe-bench/nodit-set-symmetric-difference`. Neither is on any of my five upstreams and
neither is at my seams. Recorded as ADJACENT-on-shape, not a veto.

## CHECKLIST

```
[x] 1. Upstream search across the whole org   proof: 5 queries, hit counts in the table
[x] 2. Shape search in concept words          proof: canonical form / subsumption / set difference
[x] 3. Our own repo included                  proof: swe-bench-pro-agvidit appears in 5 of 5
[x] 4. Verdict recorded with peers named      proof: the table
[x] 5. Reason the seam differs, per peer      proof: the exclusion-zone column
[x] 6. Prior used as saturation only          proof: no acceptance claim made; peer status is
       invisible to us by construction and is listed under UNVERIFIED
```

```
EXIT:       ADJACENT ×4, CLEAR-except-own-seam ×1. No COLLIDES. Five exclusion zones written.
UNVERIFIED: peer task acceptance status (server scopes `task show` to us)
OPEN:       go-zero shares a base commit with a peer MT task — any go-zero card must argue its
            seam difference in writing before scaffold
NEXT:       A3 GATE 1 consumes these zones as a factual veto list
```

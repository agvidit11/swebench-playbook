# Loop log — started 2026-09-23 ~00:55Z

Autonomous run. Five pairs, each: A1 screen -> A2 wide survey (4 axes + merge) ->
A3 gate every card -> B1..B5 -> push. Terminate the loop on one pushed task.

| pair | lane |
|---|---|
| loop-1 | data stores, storage engines, indexing, query execution |
| loop-2 | protocols, networking, RPC, serialisation, coordination |
| loop-3 | build systems, compilers, linters, package managers, runtimes |
| loop-4 | concurrency, schedulers, async runtimes, lifecycle, caching (new territory) |
| loop-5 | data processing, formats, codecs, schema evolution (new territory) |

Also still live from earlier: redo-santuario, redo-lego, r2-connectgo, find-repos.

## Retired repos — do not re-source
frostdb (observational equivalence over DataSink; merged 6169cce on target fn),
oxigraph (upstream churn, 23 live non-bot branches; AGENTS.md -> human call),
prism (compatibility library, R05 repo-wide), santuario (W3C spec-determined),
curator (both cards 5/5 on constraint-stated phrasings), immudb (BUSL-1.1),
lego (one card was a char-for-char revert of merged PR #1334).

## Running tally
- runs completed: 7 -> 0 survivors
- kills that are FACTS: merged-PR revert, importable reference, spec-determined,
  already-true premise, curator's constraint-stated 5/5, frostdb impossibility
- kills that were INSTRUMENT FAILURES: 2 (frostdb C1, santuario C3) -- both
  re-adjudicated; frostdb confirmed dead on a better gate

## Entries

### 00:58Z — find-repos returned 4 survivors; the CAT gates earned their place
36 screened, 4 survivors, 32 evidenced rejects. All Apache-2.0, all Go, all with a
measured containerised offline graded path and a NAMED semantic_bugs surface:
  concourse/concourse   70 real issues, 1 excl. peer, atc/exec step lifecycle, 5s
  crossplane/crossplane 115, 0 peers, apiextensions/composite readiness, 7s
  cloudnative-pg        229, 0 peers, podspec_diff / EnvConfig.IsEnvEqual, 8s
  kubernetes-sigs/kustomize 131, 2 excl. peers, api/internal/accumulator, 0.4s

CAT-4 (upstream churn) killed THREE repos that passed every other A1 gate:
  rustup  src/cli 82 commits/90d, src/dist 37, src/config.rs 25
  syncope one maintainer = 82 of 171 commits/90d (84% of human commits)
  zalando/postgres-operator  all 44 commits/90d in the four target packages
That is the oxigraph failure mode, now caught BEFORE the run instead of after.

Two silent-pass defects found and fixed in A1 (new §9a):
  - a 404 slug reads clean on every gate (jdbi/jdbi3 vs the real jdbi/jdbi, whose
    HEAD is a merged claude-* branch with 292 commits by "Claude (on behalf of...)")
  - the churn gate passes nonexistent paths; a 0 from an absent dir looks quiet
Also: 0-peers was a warning 67% of the time here (4 of 6 died at G2 or CAT-4);
cayenne reads 28 issues on GitHub and 441 on JIRA.
AGENTS.md hit twice (cayenne, jackrabbit-oak) — both correctly killed, not the
harmless-guide shape; left Owner: human as the gate requires.

# PAIR B — Early GATE 4 (before scaffold), cold n=5 by Avocado via mc2.sh

Procedure per card (brief /tmp/pairb/g4/COMMON.md): GATE 2 premise executed at base · GATE 3
disclosure (6 paced gh searches + log -S + test grep + remote branches) · contract written with
EVERY graded rule stated · 15-30 assertion sketch in the repo's harness, grouped by branch ·
validated 3 ways (fails at base / fails negative control / desired 100%) · 5 cold Avocado
implementations from the stated contract only · graded.

## Round 1 — fully enumerated contract

| card | assertions / groups | step-1 pass | full pass | confirmed branches | verdict |
|---|---|---|---|---|---|
| kustomize-2 | 20 / 10 | 5/5 | 5/5 | 0 | SATURATED — parked |
| spire-2 | 30 / 11 | 5/5 | 5/5 | 0 | SATURATED — **retired** (only divergence = exact digest bytes, a coined pin) |
| concourse-r2-2 | 25 / 8 | 5/5 | 5/5 | 0 | SATURATED — V1 amended first (in_parallel order IS observable: planner IDs, public plan JSON, Elm UI) |
| go-zero-1 | 26 / 9 | 5/5 | 5/5 | 0 | SATURATED |
| open62541-2 | 25 / 8 | pending (first, race-voided pass read 4/5 + 1 link failure) | | | running |
| open62541-1 | | | | | running |

GATE 2: premise confirmed absent by execution on all four. GATE 3: zero disclosure on all four.

## Cross-card finding

Every saturated card's cold set DID diverge — but only on consequences that were implied rather
than enumerated:
- go-zero-1: `byte`=`uint8` / `rune`=`int32` under "wire kind" (1/5 handled)
- concourse-r2-2: empty `json.RawMessage` under "reject malformed" (2/5 accept as null)
- kustomize-2: container-level flow/block style changes (1-3/5 emit, by container)

## Round 2 — principle-level contract (/tmp/pairb/g4/REPROBE-COMMON.md)

Choices (tie-breaks, error codes, direction) stay explicit; consequences are graded only when they
follow uniquely from a stated sentence + named authority (repo file:line / language spec / wire
spec). Target 300-500 words. Dispatched for concourse-r2-2 and go-zero-1.

## Control

Same cold procedure on our ACCEPTED `open62541-numericrange-canonical-form-composition`, real step
instructions verbatim, graded by its real tests. Server: avocado 0.2 | 0.4. If local reads 4-5/5
the probe is FAVOURABLE and round-1 saturations are not kills. Brief: /tmp/pairb/control/brief.md.

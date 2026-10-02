# CLAIMS — who is working what, across machines

Shared through the private playbook remote. **Pull before you claim, push right after.** One row per
task or card. A lane may not start work on a repo seam another row holds ACTIVE.

Status: `CARD` (idea, not built) · `PROBING` · `ACTIVE` (building) · `READY` (all local checks pass,
waiting on Vidit) · `PUSHED` · `RETIRED` · `RELEASED` (given up, seam free again)

| machine | task-or-card | repo | seam | lane | status | updated | note |
|---|---|---|---|---|---|---|---|
| devvm6971 | gobgp-prefixset-reduced-form-divergence | osrg/gobgp | internal/pkg/table prefix-set reduce/divergence/witness | B | ACTIVE | 2026-10-02 | 3-step; step 3 re-authored for route-target legality; Avocado k=5 #2 running |
| devvm6971 | go-zero-goctl-api-contract-compatibility | zeromicro/go-zero | tools/goctl/api/spec normalize + compatibility | B | ACTIVE | 2026-10-02 | converting to 3-step; contracts next |
| devvm23237 | open62541-datetime-strict-civil-validation | open62541/open62541 | UA_DateTime_parse + XML DateTime decode civil/offset validation | P | PROBING | 2026-10-02 | base 8f1965886541269dfb022ec7246d1df967af7f4e; impossible dates/times/offsets normalize at base; trap natural order loses information / permissive helper; A4 ADJACENT; five-cold-implementation probe starting |
| devvm6971 | lane-i domain: recurring schedules | ice_cube / rrule-go / rust-rrule | TBD | I | PROBING-REPO | 2026-10-02 | card agent running; Claude+Codex pair |
| devvm6971 | lane-i domain: geospatial | paulmach/orb / georust | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |
| devvm6971 | config-rs-writable-layer-delta | rust-cli/config-rs | changes_since / layer_between (writable user layer over layered Config) | P | PROBING | 2026-10-02 | base 970020ad; trap equivalence-over-domain (s1) + natural-order-loses-info (s2); A4 CLEAR repo/ADJACENT shape; 23/28 MEASURE; codex-verified; card ~/scratch/lane-i/cards/ |
| devvm6971 | lane-i domain: markdown AST | goldmark / comrak / pulldown-cmark / markdown-it-py | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |
| devvm6971 | adaptix-typeddict-union-dump-selection | reagento/adaptix | Retort.dump union-with-TypedDict case selection + ambiguity rejection | P | PROBING | 2026-10-02 | base 81594ee0; bare KeyError at base reproduced; trap permissive helper (s1) + equivalence (s2); A4 CLEAR; 22/28 MEASURE; codex-verified; TZ=UTC |
| devvm6971 | lane-i domain: rust collections | rangemap / petgraph / indexmap | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |
| devvm6971 | lane-i domain: java money/text | jsr354-ri / commons-text / commons-csv / joda-money | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |
| devvm6971 | lane-i domain: physical units | pint / uom / go-units / ruby-units | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |

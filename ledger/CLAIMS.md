# CLAIMS — who is working what, across machines

Shared through the private playbook remote. **Pull before you claim, push right after.** One row per
task or card. A lane may not start work on a repo seam another row holds ACTIVE.

Status: `CARD` (idea, not built) · `PROBING` · `ACTIVE` (building) · `READY` (all local checks pass,
waiting on Vidit) · `PUSHED` · `RETIRED` · `RELEASED` (given up, seam free again)

| machine | task-or-card | repo | seam | lane | status | updated | note |
|---|---|---|---|---|---|---|---|
| devvm6971 | gobgp-prefixset-reduced-form-divergence | osrg/gobgp | internal/pkg/table prefix-set reduce/divergence/witness | B | ACTIVE | 2026-10-02 | 3-step; step 3 re-authored for route-target legality; Avocado k=5 #2 running |
| devvm6971 | go-zero-goctl-api-contract-compatibility | zeromicro/go-zero | tools/goctl/api/spec normalize + compatibility | B | ACTIVE | 2026-10-02 | converting to 3-step; contracts next |

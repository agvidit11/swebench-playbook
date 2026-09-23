# CHECKPOINT — loop-5 (lane: data processing / pipelines / formats / codecs / compression / validation / schema evolution)

- **Act:** A1 (repo screen), just started. No prior shortlist for this lane — screening from scratch.
- **Run dir:** `/home/agvidit/swebench-playbook/.e2e/loop-5/`
- **Task dir:** none yet
- **Clone path:** none yet
- **base_commit:** none yet
- **/tmp scoping prefix:** `/tmp/loop5-*`
- **Docker lock held:** NO

## Done
- Read PAIR-COMMON.md, LOOP-BRIEF.md, 00-ROUTER.md, A1-repo-screen.md
- Read the six prior PERFORMANCE-REVIEW.md files (all prior pairs died at A3 NO SURVIVOR; dominant failure = unsupported checklist ticks + mis-run GATE 4/5)
- Corpus: `/tmp/llc` @ d8472c4c54ec0dcf9f2a951f1ab77b840f1aa308 2026-09-02 (20 days stale) — `git pull` = Already up to date
- Own in-flight tasks enumerated (47 dirs under /home/agvidit/swe-bench-pro-agvidit) — franz-go, jackson-cbor, jsonschema, libexpat, redb, object-rs are MINE => self-collision exclusions

## Next (concrete)
1. Read codimango peer repo pools (jayzong docs/repo-candidates, aaitemp discovery-f) — A1 checklist #2
2. Batch cheap gates (G5 licence, G6 liveness, G4 issue density, tracker discovery) over the lane candidate list via `gh api`
3. G1 live peer sweep on the API survivors
4. Clone survivors full-depth; G2/G3/G7/G8/G9
5. G10 measured harness timing under `flock /tmp/swebench-docker.lock`

## Decisions made
- Lane targets Go/Rust/Java/Ruby (gap table §9: Ruby -5.81, Java -2.95, Rust -2.11, Go -1.95). Python excluded (+24.66 saturated).
- Repos burned by other pairs tonight, excluded: frostdb, oxigraph, prism, santuario, connect-go, curator, lego, concourse/crossplane/cloudnative-pg/kustomize (find-repos shortlist = other lanes' survivors).

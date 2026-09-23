# CHECKPOINT — loop-1 (lane: data stores, storage engines, indexing, query execution)

Updated: 2026-09-22 (start)

## Current position
Act: **A1** (repo screen). Sub-step: candidate list assembled, running G1 local + live peer sweeps.

## Fixed facts
- Run dir: `/home/agvidit/swebench-playbook/.e2e/loop-1/`
- Clones go in: `/home/agvidit/swebench-playbook/.e2e/loop-1/clones/`
- Task-scoped tmp prefix: `/tmp/loop1-*`
- Docker lock: `flock /tmp/swebench-docker.lock <cmd>` — NOT held right now.
- Dedup corpus `/tmp/llc` HEAD `d8472c4c` 2026-09-02 (`git pull` says up to date — corpus is 20d stale; live `gh search code` is the primary gate).
- Host: JDK 8 only, Maven 3.6.3, Go 1.26.5, Docker 29.7.2, 166 cores, 223G RAM.
  Local images incl. `maven:3.9-eclipse-temurin-17`, `maven:3.9-eclipse-temurin-21`, `golang:1.26`, `golang:1.27`.
- Maven fix (from dispatch): GCS mirror `https://maven-central.storage-download.googleapis.com/maven2`
  as `<mirrorOf>central</mirrorOf>`, `--network=host` on `docker run` too, mirror + both fwdproxy
  stanzas in the SAME settings.xml.

## Retired this lane — do not re-source
polarsignals/frostdb, oxigraph/oxigraph, codenotary/immudb.

## Decisions made
- Prior lane evidence `/home/agvidit/swebench/runs/shortlist-data.md` read as a CLAIM only; re-screening first-hand.

## Next concrete commands
- local corpus sweeps for candidate list
- `gh search code --owner codimango "<repo>"` per candidate, spaced ~8s

## In flight
none

# CHECKPOINT — loop-2 (proto lane)

**Lane:** protocols, networking, RPC, serialisation, distributed coordination
**Run dir:** `/home/agvidit/swebench-playbook/.e2e/loop-2/`
**Started:** 2026-09-22

## Current position
ACT: A1 (repo screen) — building candidate list, corpus pull in flight.

## Retired / off-limits (from dispatch brief)
- `apache/santuario` — retired (W3C REC recall)
- `apache/curator` — retired (both cards fork 5/5)
- `connectrpc/connect-go` — another pair is on it NOW
- MQTT family — 57 peer files / 7 impls
- Rust in this territory — exhausted (hyper, h2, rustls, quinn, tungstenite, capnproto, hickory, libp2p, prost, reqwest, tonic)

## Environment facts (measured)
- host java = 1.8.0_502 (Temurin). mvn 3.6.3. go 1.26.5. docker 29.7.2. **no cargo, no ruby on host**
- `/tmp/llc` present, HEAD d8472c4c 2026-09-02 (20d stale) — pull in flight
- `/tmp/llc/tmp/tasks` = 15985 author dirs
- Maven direct central 429s → use GCS mirror `https://maven-central.storage-download.googleapis.com/maven2`, `docker build --network=host`

## Task-scoped tmp
`/tmp/loop2-*` — never generic names.

## Docker lock
NOT held.

## Next concrete step
Assemble candidate repo list, run G1 (live peer sweep) before cloning.

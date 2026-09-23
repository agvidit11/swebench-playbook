# Lane GO — Go x security_and_privacy/networking — A1 shortlist

Screened 2026-09-22. Corpus HEAD d8472c4 (2026-09-02, 20d stale — zero local hits treated as UNKNOWN
not clean, per A1 §3). All `gh search code --owner codimango` calls paced 22s apart, lane offset +0s.
No Docker used anywhere; G10 measured natively (host go1.26.5, GOTOOLCHAIN=auto where a repo's go.mod
demands newer).

Schema: `slug | licence (+CONFLICT flag) | stars | last commit | real open issues | peer verdict
(local+live) | AI-authorship % (method) | LOC / subsystems | name-free hosting: YES/NO + entry point |
graded-path seconds, MEASURED | rank | why-not (rejects)`

## SURVIVORS (3)

1. `go-acme/lego` | MIT, no CONFLICT | 9,886 | 2026-09-22 | 90 real (104 open − 14 PR) | local: 0 direct
   (2 hits are a downstream consumer `tlsfs` task, not lego itself); live gh search: 0 direct task,
   confirmed "org-clean" independently by swe-bench-pro-jayzong's own pool note | AI-authorship 0%
   (method: signals 1+2+3 — 0 claude/codex/copilot identities or branches in full clone, 0 release-note
   "(fix by ...)" attributions in CHANGELOG.md; 46 merged PRs/90d, 44 by maintainer `ldez`, ~0 bots) |
   LOC=111,352 / SUB=262 | YES — `certificate.Certifier.Obtain(ctx, ObtainRequest)` (certificate/
   certificates.go:187) and the `challenge.Provider{Present,CleanUp}` interface (challenge/
   provider.go:12) | graded-path MEASURED: mod download 9.3s + build 26.2s + test (certificate/,
   registration/, certcrypto/, lego/, log/, platform/) 1.3s = ~37s total, offline, deterministic |
   **RANK 1** | race-risk: repo appears in `codimango/swe-bench-pro-aaitemp:discovery-f/{pool,gated,
   classified,v2_g_networking,v2s_g_networking,v2_g_security_and_privacy,v2s_g_security_and_privacy}.json`
   — another lane's discovery pipeline has it classified under both target sub-domains. Not a kill,
   move fast.

2. `spiffe/spire` | Apache-2.0, no CONFLICT | 2,545 (below 5k-15k star band; widened to 2k-20k per A1
   §6 justification: band was thin for this sub-domain after G1/G2 kills) | 2026-09-22 | 93 real (115
   open − 22 PR) | local: 0 direct (org sweep "spiffe" = 3 hits, all synthetic t-bench "SPIFFE-style"
   mesh tasks unrelated to the real repo); live gh search: 0 peer TASK on spire (2 hits ARE MY OWN
   in-flight tasks, see below) | AI-authorship 0% (method: signals 1+2+3 — 0 claude/codex/copilot
   commit identities in last 300 commits (121/300 dependabot[bot], which is a dep-bump bot not a
   coding-assistant attribution and doesn't count under §4); 2 `copilot/*` remote branches exist
   (`review-pr-for-bugs-issues-security`, `review-pull-request`) but **verified empty** —
   `git log main..<branch>` = 0 commits both ways, `git diff --stat` differences are pure historical
   drift (main deleted old test fixtures since); these are leftover GitHub Copilot-code-review
   scaffolding branches with zero unique authored content, not a real merge, so NOT scored as a G2 kill
   — evidence pasted below; 0 release-note attributions) | LOC=126,069 / SUB=100 | YES —
   `datastore.DataStore` interface (pkg/server/datastore/datastore.go:14, e.g. `AppendBundle`,
   `CountBundles`) and `bundlepublisher.BundlePublisher` interface (pkg/server/plugin/bundlepublisher/
   bundleplublisher.go:10) | graded-path MEASURED: **go.mod requires go>=1.27.1, host has go1.26.5**
   (native GOTOOLCHAIN=local build fails instantly; GOTOOLCHAIN=auto self-fetches 1.27.1, cold 57s /
   warm build 22s) + test (pkg/common/*, pkg/server/datastore/sqlstore/*, pkg/server/plugin/
   bundlepublisher/*) ~17.7s + 11.7s ≈ 30s combined, offline (cloud bundlepublisher plugin tests —
   awss3/awsrolesanywhere/azureblob/gcpcloudstorage — all pass in <0.1s each, confirming mocked, not
   live-cloud) | **RANK 2, PROVISIONAL — self-collision boundary required** | ⚠️ **I already have 2
   in-flight tasks on this exact repo**: `spire-workload-api-delivery-readiness` and
   `spire-bundle-publication-accountability`, both at base_commit `53c6db8fbb61448ffeaa83316eb9d9b66187d2c4`
   (server/datastore + server/plugin/bundlepublisher subsystems). A 3rd task here is fine under "few
   repos, many tasks" but MUST avoid that base_commit/subsystem pair — pick a different area (e.g.
   agent attestation, SVID rotation, entry-registration validation) and a fresher base_commit. Also
   ⚠️ **known pre-existing test failure at HEAD** unrelated to any subsystem above:
   `pkg/common/plugin/sshpop TestNewClient/cert_file_not_exists` fails in this sandbox (environment-
   dependent, not investigated further) — scope any new task's graded subset away from `sshpop`.

3. `smallstep/certificates` | Apache-2.0, no CONFLICT | 8,898 | 2026-09-22 | 246 real (301 open − 55
   PR) — in the 150-500 "lower expected hit rate" band per A1 §5, not HIGH | local: 0 direct task on
   `certificates` itself; **org sweep found 3 peer tasks on sibling `smallstep/crypto`** by 2 different
   authors (`crypto-jose-ssrf-harden` by gduzhou, `smallstep-crypto-edipartyname` +
   `smallstep-crypto-x400address` by kaanbagci) — race-risk on the org, not a same-repo kill; live gh
   search confirms same picture, plus notes this repo already seam-screened once by `swe-bench-pro-
   jayzong` (idea-level probe on a `SharedSecret` provisioner failed because provisioners are literal
   copyable templates — that is an idea-level G8 caution for provisioner-extension ideas specifically,
   not a repo-level kill; other subsystems (validators, webhook controller, ACME order finalize) are
   unaffected) | AI-authorship 0% (method: signals 1+2+3 — 0 claude/codex/copilot identities or
   branches in full clone, 0 release-note attributions; **but 45/54 merged PRs in the last 90d (83%)
   are `dependabot[bot]`** — only 9 human-authored merges — flagged as a low-human-activity caution,
   same shape as the `eclipse-hawkbit` 61%-bot demotion precedent in the peer pool, though this is not
   an AI-authorship hit) | LOC=51,797 / SUB=42 | YES — `Authority.Sign(csr, signOpts, extraOpts...)`
   (authority/tls.go:113) and `Authority.SignSSH(...)` (authority/ssh.go:149) | graded-path MEASURED:
   mod download 4.0s + **full `go build ./...` FAILS** (`go-piv/piv-go` PIV/smartcard backend needs
   system `libpcsclite`, absent on this host) + targeted build excluding `kms/apiv1/piv` succeeds in
   0.3s + test (authority/, api/, pki/) 32.0s, all offline, all passing | **RANK 3, PROVISIONAL** —
   container flag needed: either `apt-get install libpcsclite-dev pkg-config` in the Dockerfile, or
   scope the task/build away from `kms/apiv1/piv`; down-ranked below lego/spire for the 83%-bot PR
   ratio and the org-level race-risk.

## REJECTS (8)

| slug | why-not | evidence |
|---|---|---|
| `dadrus/heimdall` | **G1 kill** — 3+ direct peer tasks at base `7b41d26`, same subsystem (pipeline cache identity across authenticators/authorizers/contextualizers/finalizers), from author `weili4-swebench`; plus unrelated `gojek/heimdall` (different repo, same name) also has 2 peer tasks (`heimdall-body-replay-cancel`, `heimdall-retry-loop-response-ownership`, williamtonthatt) | `gh search code --owner codimango heimdall` — 50+ hits incl. `weili4-swebench:heimdall-cache-identity-3p-skills/instruction.md: "This repo is dadrus/heimdall..."` |
| `zmap/zlint` | **G1 kill** — ≥3 direct peer tasks (`zlint-refactor`, `zlint2-refactor`, `zlint-execute-pipeline`, `zlint-config-walker-unify`) at base `b82b486...`, all in `v3/util` and pipeline-execution subsystem, author `williamtonthatt_swebenchpro` | `gh search code --owner codimango zlint` — task.toml/README/Dockerfile hits confirming repo+base+subsystem |
| `caddyserver/certmagic` | **G1 kill** — 1 fully-scaffolded direct peer task `ritesh33_caddyserver__certmagic-9f98c96-v1` with complete tests/config.json, gold test, Dockerfile | `gh search code --owner codimango certmagic` — `tests/config.json: "repo": "caddyserver/certmagic"` |
| `pion/webrtc` | **G1 kill, severe** — 15+ direct peer tasks from ≥5 different authors (bharathv alone has 8: dc-cleanup, trackremote-read-race, cert-cache, icecandidate-ext-serial, two-byte-header-ext, transceiver-stop-negotiation, sdp-direction-renegotiation) plus adjacent `pion/sdp`, `pion/ice`, `pion/dtls`, `pion/transport` also mined — whole `pion` org is saturated. Also on `weili4-swebench:EXCLUSION-LIST.md` already | `gh search code --owner codimango "pion/webrtc"` — dozens of hits |
| `cloudflare/cfssl` | **G1 kill** — 1 direct, fully-scaffolded peer task (`codimango/ado-synth-data-track-repogen:converted__repogen_task__metaprompt_cloudflare_cfssl_f337ebed__8404c3fbf6-v1`) on the `scan` package (goroutine-leak/context-cancellation fix), with gold.patch, rubrics.json, test.sh; repo is small (~40 packages) so subsystem-overlap risk on any new idea is elevated | `gh search code --owner codimango "cloudflare/cfssl"` — `tests/rubrics.json`, `solution/gold.patch` hits |
| `miekg/dns` | **G1 kill, severe** — ≥3 direct peer tasks from 3 different authors at 3 different base commits: `mijiang_miekg__dns-fa041ee-v1` (2-step MT), `yossiro_miekg__dns-cb21f4d-v1` (dnssec.go refactor), `kyarovoym_miekg__dns-d1539a7-v1` | `gh search code --owner codimango "miekg/dns"` — Dockerfiles cloning `miekg/dns.git`, task.toml/README per instance |
| `libp2p/go-libp2p` | **G2 kill** — 2 genuine closed-unmerged `copilot/*` branches with real authored content on the websocket transport subsystem (`add-regression-test-websocket-hang`: 9 commits incl. "Interrupt websocket reads during close", touching `p2p/transport/websocket/*`; `interrupt-websocket-reads-on-close`: 1 commit, same fix). Per A1 §2 "Treat closed-unmerged as a hard kill — the fix is public either way." No local/live peer task otherwise (would have survived G1) | `git branch -r \| grep -iE 'claude\|codex\|copilot'` on full clone; `git log --oneline master..origin/copilot/add-regression-test-websocket-hang` — 9 real commits |
| `cloudflare/circl` | **G2 kill** — repo carries `AGENTS.md` at root ("CIRCL Agent Instructions" for AI coding agents), added by upstream maintainers 2026-06-02 (commit `e9bd81b`), well before the current base_commit. Per A1 §2 G2 this is an explicit hard-kill trigger (`.claude/`, `CLAUDE.md`, `AGENTS.md`, `docs/claude/`). No peer-author collision found (0 in local/live sweeps) — this repo is otherwise clean and IS an existing asset (my own task `circl-secretsharing-share-lifecycle`, base_commit `2ef8bf457d28ab1c62f42b76f6564610c5a3b3f0`, which is also current upstream HEAD) but per the literal gate, no *new* task should be sourced from it until a human resolves whether AGENTS.md's presence (predating that base_commit) is disqualifying for the existing task too | `ls -d .claude CLAUDE.md AGENTS.md docs/claude` on full clone; `git log --follow -- AGENTS.md` |

## Self-collision check (checklist step 10)

`ls /home/agvidit/swe-bench-pro-agvidit/` diffed against every candidate slug:
- `circl-secretsharing-share-lifecycle` → matches `cloudflare/circl` (rejected at G2 above, see note)
- `spire-workload-api-delivery-readiness`, `spire-bundle-publication-accountability` → both match
  `spiffe/spire`, both at base_commit `53c6db8fbb61448ffeaa83316eb9d9b66187d2c4` (server/datastore +
  server/plugin/bundlepublisher). Any new spire task must avoid this base_commit/subsystem pair.
- `go-zero-flush-accountability`, `go-zero-mr-cancellation-accounting`, `go-zero-token-limiter-
  degradation` → 3 existing tasks on `zeromicro/go-zero`, not screened fresh in this lane (out of
  scope, noted only because it is a Go repo already in my own portfolio).
- No match for `lego`, `smallstep`/`certificates`, `zlint`, `heimdall`, `cfssl`, `dns`/`miekg`,
  `certmagic`, `pion`/`webrtc`, `libp2p`.

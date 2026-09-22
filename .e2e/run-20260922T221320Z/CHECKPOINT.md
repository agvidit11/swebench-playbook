# CHECKPOINT — run-20260922T221320Z

> Rewritten after every meaningful sub-step. A stranger with zero context should be able to
> read this and continue without redoing work.

**Last updated:** 2026-09-22, A2 survey dispatched to MetaCode (in flight).

---

## Current position

| | |
|---|---|
| **Act** | `A2` — idea generate. Checklist lines 1-7 done; **line 7 (the survey) IS IN FLIGHT.** |
| **Where inside it** | waiting on MetaCode. Next after it returns: line 8 merge table -> 9 auto-rejects -> 10 cards -> 11 self-audit -> 12 count -> 13 HANDOFF. |
| **A1 status** | CLOSED, `EXIT: PARTIAL`. Handoff at `handoffs/01-A1.md`. **Repo chosen: `go-acme/lego`.** |
| **Target format** | `swebench-multi` (multi-turn) |
| **Run root** | `/home/agvidit/swebench-playbook/.e2e/run-20260922T221320Z/` |
| **Docker lock** | **NOT HELD BY ME.** `/tmp/swebench-docker.lock` exists, size 0, mtime 2026-09-22 15:18:55, owner unknown — another session on this host is running `ruby-terraform-plan-model-empty__bqrhh2b-main-1` and `redb-database-drop-hangs-outstan__yut52b8-main-1`. I have run **zero** Docker commands. |

---

## Decisions already made — do not relitigate

1. **Three lanes, not four: GO / RS / JV. Ruby deliberately excluded** despite having the best
   taxonomy gap (−5.81). Reason: this author already has 14+ in-flight Ruby tasks
   (webauthn-ruby ×3, ruby-auth0 ×4, state-machines ×3, qdrant-ruby, sparql-ruby, net-imap,
   ruby-terraform ×2, zendesk-biz) — A1 §3 "check our own in-flight work" makes Ruby the
   highest self-collision territory available, and `ruby` is absent from the host toolchain
   so every Ruby G10 would be Docker-bound.
2. **G10 split out of the fan-out.** A1 §10 line 14 requires a container run; router §6 makes
   Docker serial-only while making A1 the canonical parallel act. Lanes were told to run
   G1–G9 in parallel and measure G10 natively only where the host toolchain exists; container
   G10 is queued serially through the coordinator. See `friction.md` F3.
3. **Corpus refresh done once centrally, not per lane** (shared git index). See `friction.md` F1.
4. **Lane brief passed the `aai-instruction-validator` gate before fan-out** — verdict APPROVE
   with three tightenings, all applied: 22s `gh search code` cadence with per-lane offsets
   (GO +0s / RS +7s / JV +14s) because the 10/min cap is org-wide and shared, not per-lane;
   `PROVISIONAL — G10 pending` labelling; explicit checklist-line-1 waiver wording.

---

## DONE — with evidence path for each

| Item | Evidence |
|---|---|
| Dedup corpus refreshed | `cd /tmp/llc && git pull` → `Already up to date.`; HEAD `d8472c4` **2026-09-02** = **20 days stale**. Recorded in `friction.md` F2. |
| Peer repo pools downloaded | `/tmp/e2e-pools/` — `CANDIDATE-POOL.md` (1726 lines) + 4 lane-relevant sweeps from `codimango/swe-bench-pro-jayzong:docs/repo-candidates/` |
| Host toolchain receipt (A1 §8 was assertion-only) | go1.26.5 ✓, gcc 11.5.0 ✓, cmake 3.31.8 ✓, python3 3.12 ✓, mvn 3.6.3 ✓, **java = JDK 1.8 ONLY** (`/usr/local/fbprojects/packages/java-runtime/539/impl/8`, no `/usr/lib/jvm`, `JAVA_HOME` unset), node v24 ✓, **ruby ABSENT, cargo/rustc ABSENT**. Confirms + sharpens `A1:212`. |
| `gh` code-search budget confirmed shared | `gh api rate_limit` → `code_search.limit = 10` (per-minute, org-wide) |
| Lane brief validated | `aai-instruction-validator` → `VERDICT: APPROVE` + 3 tightenings, all applied |
| **Lane GO complete** | `/tmp/e2e-lane-GO/shortlist.md`; 11 repos screened, 3 survivors, 8 evidenced rejects |
| **Lane RS complete** | `/tmp/e2e-lane-RS/shortlist.md`; 13 repos screened, 2 provisional survivors, 11 evidenced rejects |
| **Lane JV complete** | `/tmp/e2e-lane-JV/shortlist.md`; 12 repos screened, 3 provisional survivors, 9 evidenced rejects |
| Tooling health | `codimango task list` OK (42 tasks); `mc.sh` present; `codex` on PATH; fixed `instruction-lint.py` in place (2026-09-22 15:22) |

**36 repos screened across the three lanes. 8 survivors, 28 evidenced rejects.**

---

## Survivor table (consolidated)

| # | slug | lane | licence | LOC / subsys | real open issues | G10 | blocker |
|---|---|---|---|---|---|---|---|
| 1 | **`go-acme/lego`** | GO | MIT | 111,352 / 262 | 90 (104−14) | **MEASURED 37s native** | none — **only repo past every gate** |
| 2 | `spiffe/spire` | GO | Apache-2.0 | 126,069 / 100 | 93 (115−22) | ~30s native (needs `GOTOOLCHAIN=auto`, go≥1.27.1) | self-collision: author already has 2 spire tasks |
| 3 | `smallstep/certificates` | GO | Apache-2.0 | 51,797 / 42 | 246 (301−55) | 32s native (subset) | sibling `smallstep/crypto` has 3 peers; 83% dependabot; needs `libpcsclite-dev` |
| 4 | `nmstate/nmstate` | RS | Apache-2.0 | 68,042 / 4 crates | 77 (96−19) | **DEFERRED** (`rust:1-slim`) | Docker contended |
| 5 | `retis-org/retis` | RS | GPL-2.0-only | 32,378 / 5 crates | 22 (27−5) | **DEFERRED** | core `src/collect` needs root+eBPF; only `retis-events` gradeable — weak |
| 6 | `apache/mina-sshd` | JV | Apache-2.0 | 161,233 / 14 | 55 (68−13) | **DEFERRED** (JDK17) | Docker contended |
| 7 | `jetty/jetty.project` | JV | EPL-2.0 | 586,816 / 36 | 220 (274−54) | **DEFERRED** (JDK17) | 586k LOC is 4× the A1 §6 target band ceiling |
| 8 | `GoogleCloudPlatform/jit-groups` | JV | Apache-2.0 | 20,598 / 1 mod | 5 (5−0) | **DEFERRED** (JDK25) | **G9 FAIL risk** — zero test-fixture files anywhere |

**Leading pick: `go-acme/lego`.** Only repo with a measured graded path; MIT; 0% AI-authorship by
the corrected 3-signal method; peer-clean local + live; 111k LOC / 262 subsystems sits inside the
A1 §6 60k–150k band; 90 real open issues is inside the `<150` "normal screening" band; rich
existing public API (`Certifier.Obtain`, `challenge.Provider{Present,CleanUp}`) satisfies G8
without naming anything new. Race-risk flag: appears in `swe-bench-pro-aaitemp:discovery-f/*.json`
under both networking and security_and_privacy pools — signal, not kill (A1 §3).

---

## NEXT — concrete commands

1. **Coordinator-side confirmatory re-screen of `go-acme/lego`** (A1 §1: "do not accept any
   pre-screen, *including this brief's own repo list*" — a lane report is a pre-screen):
   ```bash
   gh search code --owner codimango "lego" --limit 30
   gh search code --owner codimango "go-acme" --limit 30     # 22s apart
   ls -d /tmp/e2e-lane-GO/lego/{.claude,CLAUDE.md,AGENTS.md,docs/claude} 2>/dev/null
   git -C /tmp/e2e-lane-GO/lego branch -r | grep -icE 'claude|codex|copilot'
   grep -rli "lego" /tmp/llc/tmp/tasks | head -40
   ```
2. **Drain the serial G10 queue** once `/tmp/swebench-docker.lock` frees — nmstate, then
   mina-sshd. Exact commands in `handoffs/01-A1.md` §G10 QUEUE.
3. Write `handoffs/01-A1.md`, then proceed to `A-source/A2-idea-generate.md`, one dispatch per
   surviving repo (owner = MetaCode per router §1).

---

## In-flight dispatches

**MetaCode / Avocado — A2 survey.** THE ONE THING A SUCCESSOR MUST NOT RE-RUN BLIND.
| | |
|---|---|
| launcher | `~/.claude/skills/swebench-mt/mc.sh` (mandatory — a hand-rolled `script -qec` returns a 192-byte banner at exit 0, and apostrophes in the prompt get silently deleted) |
| brief | `/tmp/lego-run/survey.txt` (~15 KB) |
| repo dir | `/tmp/e2e-lane-GO/lego` |
| output | `/tmp/lego-run/survey.out` · launcher log `/tmp/lego-run/mc.log` |
| timeout | 1700s inside mc.sh |
| expected back | 18 surfaces in subsystem passes, a merge table, an auto-reject list, and 2-4 cards in the A2 §8 format |
| **acceptance check** | **byte size.** `<600 bytes` = the gateway banner, not an answer -> re-run. A2 §3 is explicit that these tools fail with exit 0. |

## Task-scoped /tmp paths in use

| path | purpose |
|---|---|
| `/tmp/llc` | dedup corpus (shared, read-only for me) |
| `/tmp/e2e-pools/` | downloaded peer repo-candidate pools |
| `/tmp/e2e-lane-GO/`, `/tmp/e2e-lane-RS/`, `/tmp/e2e-lane-JV/` | lane clones + shortlists |
| `/tmp/e2e-g10/` | G10 container logs (empty — queue blocked) |
| `/tmp/lego-run/` | A2 working dir: `survey.txt`, `survey.out`, `mc.log`, `admissions.txt` |
| `/tmp/swebench-docker.lock` | **held by another session**, not me |

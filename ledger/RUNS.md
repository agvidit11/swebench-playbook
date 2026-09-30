# Run index — ideation wave 1, 2026-09-17

Managing agent: keep this current. One row per repo, one agent per repo.

| Repo | Lang | Open | Dedup | Agent | Stage | File |
|---|---|---|---:|---|---|---|
| spiffe/spire | Go | 123 | 0 | running | 1 survey → 1d | `spire.md` |
| apache/casbin | Go | 38 | 0 | running | 0 → 1d | `casbin.md` |
| FasterXML/jackson-databind | Java | 136 | 0 | running | 0 → 1d | `jackson-databind.md` |
| bcgit/bc-java | Java | 82 | 0 | running | 0 → 1d | `bc-java.md` |
| apache/commons-configuration | Java | 106 (JIRA) | 0 | wave-3 java lane | 0 → 1d | `commons-configuration.md` |

All four stop at **1d** (novelty gate) and report. None scaffolds, none pushes,
none touches `/home/agvidit/swe-bench-pro-agvidit`.

## Funnel, with honest conversion

```
surfaces          ~15-18 per large repo, fewer for small   (stage 1)
  -> candidates   2-4 per repo after merge                 (stage 1a)
  -> above bar    >=21/30 AND fork >=3                     (stage 1b)
  -> novel        public-solution + peer-task check         (stage 1d)
  -> scaffolded   oracle 3/3, preflight exit 0              (stage 3-4)
  -> in band      1-3 of 5 per step  <-- THE BOTTLENECK     (stage 5-6)
  -> accepted     human review                              (stage 7)
```

Wave 1 should yield roughly **8-16 candidates**, maybe **4-8** past threshold
and novelty. That is one wave of raw material, not 8 accepted tasks.

## Where this actually jams

**Not ideation.** All 12 of the Sept batch reached the server; every one died at
calibration, not for want of ideas. Volume upstream does not fix conversion.

**Calibration concurrency is the hard ceiling.** Docker caps near 15 bridge
networks on this host and one `k=5` job creates 5. So **max ~3 concurrent
calibration runs**, regardless of how many agents are ideating. Over-parallelise
and whole jobs die with `all predefined address pools have been fully
subnetted`, and those dead trials score as real failures.

So: ideate wide and in parallel, but queue calibration 2-3 at a time. The
serial-submission rule still stands — one task submitted before the next starts.

## Wave 2 candidates (screened, unassigned)
- `networknt/json-schema-validator` — Java, 6 open, 0 dedup, Apache-2.0. Small.
- `apache/commons-lang` — 0 dedup. Check issue density before assigning.
- `hashicorp/vault` — 0 dedup, but very large and heavily mined; contamination risk.
- `ruby/openssl` — 81 open, 0 dedup, but licence is NOASSERTION. Resolve first.

Rejected wave 1: tantivy (454 open), jqlang/jq (480 open + NOASSERTION),
cue-lang/cue (642), netty (673), open-policy-agent/opa (310, moderate).

## QA pass on RUNBOOK — 2026-09-17, after wave-1 dispatch

Read end-to-end for the first time (it had only been edited piecemeal). Seven
defects found and fixed. All four agents were already reading it.

| # | Defect | Impact if unfixed |
|---|---|---|
| 1 | Stage 1 still contained the old **"propose 5 potential task ideas"** prompt verbatim, directly under the new "never ask for 5" rule | agents copy the prompt, not the rule — the whole wide-survey change is a no-op |
| 2 | Stage map said `1 ideate -> 5 candidate ideas` | same |
| 3 | Stage 3 asked Codex for "the solutions and grading test" while 3c assigned `solve.sh` to Claude | two models writing the same file; provenance ambiguity |
| 4 | `1a` (merge) and `1d` (novelty) missing from the map; `1d` absent from RUNBOOK entirely | the novelty gate silently skipped — the one check that kills a candidate for free |
| 5 | Surface definition duplicated verbatim | noise |
| 6 | `timeout 900` on the survey | a 126k LOC survey does not finish in 15 min; silent truncation |
| 7 | Stale STOP: "no named fork -> kill it now" at survey stage | contradicts keeping weak forks for the merge stage |

Lesson for the playbook: a document assembled by incremental edits must be read
whole before it is handed to anyone. Defects 1 and 3 were introduced by my own
edits and were invisible from the diffs.

## Isolation tripwire
41 files show as changed in `swe-bench-pro-agvidit`, **all dated 2026-09-16** —
pre-existing, from the earlier canary strip. Zero files touched since wave-1
launched. Isolation holding.

**Hazard for whoever pushes next:** those 41 uncommitted changes include a
canary strip that hit `hello-world/` and other non-batch tasks. Do not `git add
-u` blindly; verify `git diff --cached --name-only` before every commit.

## Wave 1 — spire: COMPLETE (stages 0→1d)
18 surfaces → 5 merged candidates → **2 survivors**, both 24/30.
- **C1 bundle publication accountability** — `pkg/server/bundle/pubmanager`
- **C3 workload-API delivery readiness** — `workload/handler.go`
- Killed at novelty: C4 (spire #5097 OPEN `help wanted` + #7199 body proposes
  three remedies), C5 (#7198/#7210/#5349). Failed scoring: C2 17/30.

**Independently verified by managing agent** (did not take the report at face
value): #5097 and #7199 confirmed OPEN via `gh`; `publishBundle` confirmed to
log per-plugin and `return nil` unconditionally; `triggerPublishResultHook`
confirmed nil-guarded and set only in `_test.go`. C1's cascade premise holds —
there is genuinely no production per-publisher state for step 2 to consume.

**RUNBOOK defect found by this run:** novelty was ordered AFTER scoring. C4
scored highest of the five and was then killed for free — the scoring pass was
pure waste. Reordered: 1a merge → **1b novelty** → 1c score → 1d breakdown.
Also added: read issue *comment bodies*, not titles, and read dedup hits rather
than counting them (homograph noise).

Toolchain note for C1/C3 scaffolding: spire `go.mod` wants Go 1.27.1, host has
1.26.5. `GOTOOLCHAIN=local` hard-fails. **Pin `golang:1.27` in the Dockerfile.**

## Wave 1 — casbin: COMPLETE, ZERO SURVIVORS (correct outcome)
14.2k LOC → 12 surfaces → 3 merged → 0 survive.
- C3 domain-aware detector (25/30, highest scored) — dead: PR #1633
  (closed-unmerged) implements step 2's semantics; also #1640, #1667, issue #446.
- C1 structured enforcement outcomes (23/30) — dead three ways: peer
  `hjjyyds-wrg/casbin.md` publishes both forks as resolved contract; not a
  cascade per its own 1d answer; PR #1617 rewrites `BatchEnforce`.
- C2 (20/30) — failed threshold on cascade.

### CRITICAL: my dedup pre-screen method was WRONG
Found by the casbin agent, verified independently by me.

I screened peer tasks by **org/repo slug** in file CONTENT. Peer
`instruction.md` files are de-identified — they say "the codebase" and never
name the slug. Systematic false negative.

| repo | slug sweep (mine) | filename sweep | reality |
|---|---:|---:|---|
| casbin | **0** | 19 | ~11 peer tasks incl. a 2-step MT on the same repo |
| jackson-databind | **0** | 26 | **2 direct peers on the exact repo** + ~20 adjacent |
| spire | 0 | 24 | genuinely clean — all 24 are *Slay the Spire* / *Aspire* / "inspired" |
| bc-java | 0 | 0 | 9 content hits for "bouncycastle" to be read |

Corrected method now in RUNBOOK 1b: filename sweep first, then bare-name content
sweep, then distinctive symbols — and **read** the hits rather than counting
them, because both error directions are live (homographs inflate, slugs hide).

Both in-flight agents were sent the correction mid-run.

### Two more playbook rules from this run
- **Check `git branch -r`, not just the tracker.** casbin passes the issue gate
  with 37 open issues but carries ~60 `copilot/*` closed-unmerged agentic PRs,
  each implementing a named gap. Tracker understated disclosure by an order of
  magnitude — the mbedtls failure mode in a new disguise.
- **Closed-unmerged PRs are a hard kill**, same as merged. The fix is public
  either way, which is what the rule protects against.
- **Cross-port peers count.** jCasbin / casbin-rs / php-casbin burn the same
  invariant. "Different language" does not waive a collision.

**Repo-level verdict: casbin is a hostile sourcing repo that passes every
numeric gate.** Do not re-assign it.

## Wave 1 — jackson-databind: COMPLETE, ZERO SURVIVORS
147.6k LOC (branch `3.x`, pkg root `tools.jackson.databind`) → 20 surfaces →
3 merged → 0 survive. Best score 14/30; all three also fail the Fork<=2 veto.
17 of 20 surfaces dropped before scoring, 3 outright dead on open upstream work.
**Recommend not re-assigning this repo.** 3,886 lifetime issues is the real
signal, not the 136 currently open.

### NEW FAILURE MODE: the hollow premise
C1 and C2 died because the behaviour they proposed to add **already holds at
HEAD** — step 2's assertion would pass at base on an empty patch.
**Verified independently:** `CoercionConfigs.findCoercion()` documents its own
class → logical-type → shape-default precedence in source comments, which is
exactly what C1 proposed to introduce.

An ideating model will confidently describe a gap closed years ago. Added as
RUNBOOK stage **1a2**, before novelty and before scoring: open the code path and
confirm the gap exists. Costs one file read; it is the early form of the
base-commit repro rule, which otherwise catches this a whole cycle later.

### METACODE PTY FIX — verified, unblocks parallelism
The banner-only failure (192 bytes, **exit 0**, no error) is a **missing TTY**,
not backgrounding. It cost three dispatches across two agents.

```bash
timeout 1700 script -qec "metacode run --yolo --format text --dir <repo> '<prompt>'" /dev/null
```
Tested by the managing agent backgrounded: returned the real answer, not the
banner. This matters because the Bash tool caps at 600s and a 147k-LOC survey
runs far longer — foreground-only meant surveys could not be parallelised.
Also: always check output size; ~200 bytes + exit 0 is the banner.

### Two more novelty hardenings
- **Symbol searches miss behaviour-phrased issues.** jackson #959 contains
  neither symbol the candidate was built on. Search by behaviour phrase, and
  grep the **test tree** — a shipped test proves the direction is public.
- **Inline `[repo#N]` markers are a contamination metric.** jackson source
  carries 1,110 markers naming 625 distinct public issues; per-file density
  identifies mined files.

## Wave 1 scoreboard
| repo | surfaces | merged | survivors |
|---|---:|---:|---:|
| spiffe/spire | 18 | 5 | **2** (C1 24/30, C3 24/30) |
| apache/casbin | 12 | 3 | 0 |
| FasterXML/jackson-databind | 20 | 3 | 0 |
| bcgit/bc-java | running | | |

## Wave 1 — bc-java: COMPLETE, ZERO CLEAN SURVIVORS (one conditional)
489,909 LOC canonical trees only → 22 surfaces (3 subsystem passes) → 3 merged.
- **M1 layered X.509 structural review (26/30, top score) — HARD KILL, already
  ships at HEAD.** `pkix/.../X509CertificateReviewer.java`, 11,483 bytes,
  `Finding` l.60 / `Review` l.118 / `reviewStructure` l.176. Traced by the repo's
  own docs to #1508 / PR #1511. **Verified independently by managing agent.**
- **M2 failure-aware CMS stream finalization (25/30)** — passes the gate, gap is
  real (`TeeOutputStream.close()` still `output1.close(); output2.close();`),
  tracker clean. But **step 1 is `org.apache.commons.io.output.TeeOutputStream`
  verbatim** — pure recall, no domain content, and it is the step the cascade
  rests on. Agent's own call: do not ship as 2-step; single-turn on step 2.
- **M3 (20/30)** — Fork veto. RFC 5280 specifies the behaviour so tightly that
  divergence is a bug, not a fork.

**Verdict: do not re-assign bc-java from this angle.** Encoding/canonicalisation
lane has cross-port peers (asn1crypto, derkit, a C++ BER walker); path-validation
is standards-pinned so forks are bugs; the best structural candidate is already
built. Only untouched lead: MR-jar overlay resolution (`NoSuchMethodError` on
JDK 25 only) — bc-specific, no other library shares it.

### The hollow premise is now CONFIRMED SYSTEMATIC
Two independent agents, different repos, same failure mode — and in both cases
it was the **highest-scoring candidate**:
- jackson C1/C2 — `CoercionConfigs.findCoercion()` already implements the
  precedence, documented in its own comments.
- bc-java M1 — the entire feature ships; **Codex scored it 26/30 while citing
  line numbers inside the finished implementation.**

A merge or score pass structurally cannot tell "this exists" from "this should
exist". Stage 1a2 must run before scoring, always. This is not a tuning issue,
it is a property of the pipeline.

### Three tooling fixes (all silent failures with exit 0)
- **`codex exec` returns only its opening plan on a large inline prompt** (46 KB
  → 18.7k tokens, exit 0, zero tool calls, both sandbox modes). Fix: short
  prompt + `--add-dir` for the payload + `-o` to capture. Now in RUNBOOK.
- **Bash tool caps at 600s**, so RUNBOOK's `timeout 1700 metacode` only works
  backgrounded — which the pty wrapper now enables. Noted inline.
- **`xargs wc -l | tail -1` can undercount** when xargs splits (each chunk emits
  its own `total`). Did NOT reproduce on my check — all methods gave 394,312 —
  but the sizing command is now split-safe regardless, since a silent undercount
  moves a repo into the wrong band.

## WAVE 1 FINAL
| repo | LOC | surfaces | merged | clean survivors |
|---|---:|---:|---:|---:|
| spiffe/spire | 126k | 18 | 5 | **2** (24/30, 24/30) |
| apache/casbin | 14k | 12 | 3 | 0 |
| FasterXML/jackson-databind | 148k | 20 | 3 | 0 |
| bcgit/bc-java | 490k | 22 | 3 | 0 (+1 single-turn lead) |
| **total** | | **72** | **14** | **2** |

72 surfaces → 14 merged candidates → **2 buildable**. Both from spire.
Top-scored candidate in 2 of 4 repos was already implemented upstream.

## Wave 2 dispatched — 2026-09-17, 5 agents

### Build (stages 2→4, stop at preflight exit 0, NO push/commit)
| Task | Candidate | Dir |
|---|---|---|
| spire C1 | bundle publication accountability (24/30) | `spire-bundle-publication-accountability/` |
| spire C3 | workload-API delivery readiness (24/30) | `spire-workload-api-delivery-readiness/` |

Brief: `/home/agvidit/swebench/BUILD-BRIEF-2026-09-17.md`. Provenance table is
explicit: Claude may write `solve.sh`/Dockerfile/`task.toml` only; never
`instruction.md`, never `tests/`. C3 carries two protective caveats (grade the
readiness payload not non-blocking; use the injectable `clock.Clock` +
`notifyCallbackFn` seams or report BLOCKED rather than ship a flaky grader).

Both were told to run 1a2 hollow-premise themselves before authoring, despite
C1's premise already being verified by me — cheap, and it is the failure mode
that killed the top candidate in 2 of 4 repos.

### Appeal (adversarial re-examination of the 3 rejections)
| Repo | Main question |
|---|---|
| casbin | Is closed-unmerged really a hard kill? Plus S10+S9 (never scored, prior agent said its own drop was wrong), S8 (never executed), `enforcer.go:895` panic |
| jackson-databind | ~7 of 20 surfaces dropped with no documented hard reason. Also: 3 bad merges from 20 surfaces is a merge-quality failure, not proof the repo is dead. Try other combinations |
| bc-java | Rescue M2 by re-founding step 1 on a bc-specific invariant; explore the never-investigated MR-jar overlay lead; re-test "standards-specified ⇒ no fork" in its general form |

C1/C2 jackson and M1 bc-java kills are marked SOLID (I verified them) and are
off the table — appeals are told not to re-litigate those.

All five: "rejection upheld / no survivor" is an acceptable answer. Explicitly
instructed not to manufacture survivors.

## Wave 3 dispatched — 5 sourcing agents, LANES not repos

Key change from wave 1: **no pre-screen.** Each agent gets a lane and runs its
own stage 0 — measure, gate, dedup, verify, pick. My wave-1 pre-screen was wrong
for 2 of 4 repos and actively misled those agents, so handing out repo verdicts
is now the anti-pattern. Rejecting three repos and reporting "no viable repo in
this lane" is an accepted outcome.

| Lane | Rationale | Out of lane |
|---|---|---|
| Ruby — web/HTTP/middleware | Ruby is the biggest gap at **-5.81** | burned Ruby repos |
| Ruby — data/persistence/query | same gap, different invariants (identity maps, lazy materialization, savepoint nesting) | HTTP layer (other agent) |
| Rust — systems/parsing/storage | -2.11; ownership makes lifetime forks observable in the API | smoltcp, dropshot, rustcrypto |
| Go — distributed/storage/coordination | -1.95; rich in ordering + mid-operation-visibility forks | **authz/policy engines** (casbin dead, OPA adjacent) |
| Java — concurrency/collections/build/text | -2.95, no viable Java repo found yet | **serialization** (jackson dead) and **crypto/PKIX** (bc-java dead) |

Brief: `AGENT-BRIEF-v2.md` — carries all five wave-1 killers (hollow premise,
slug-dedup worthlessness, tracker understating disclosure, standards-pinned
means no fork, recall-only steps) and the three silent exit-0 tool failures.

## Agents in flight: 11
- 2 build (spire C1, spire C3) — the only Docker users
- 3 appeal (casbin, jackson-databind, bc-java)
- 1 eval-gt template investigation (read-only on task repo)
- 5 wave-3 sourcing (ideation only, no Docker)

## APPEAL — jackson-databind: REJECTION UPHELD, and a new repo-level gate

All three candidates upheld. No new candidate. **Abandon the repo** — but the
decisive reason is one the original run never found.

### The disqualifier: 55.8% of fixes are Claude-authored
**Verified independently by managing agent.** `release-notes/VERSION`:
- 86 of 154 attributed fixes are AI-assisted
- `(fix by @cowtowncoder, w/ Claude code)` is the MOST COMMON line, 77 times
- accelerating: 48 in 3.2.0 alone, ~157 commits/month

Grading a Claude-family solver on a codebase whose maintainer publishes
Claude-authored fixes measures **recall as much as reasoning**. This is
family-level solution leakage and **no per-candidate novelty check can detect
it** — the fix need never appear in an issue, PR body or peer task.

Now RUNBOOK **stage 0 gate**, with a >25% bar, plus memory
`feedback_swebench_ai_authorship_gate`.

### The hollow-premise rate was the symptom all along
Appeal re-opened the 6 undocumented drops (S2 S5 S10 S15 S18 S20) and found
**five more hollow premises**. Running total: **8 of 20 surfaces already
implemented at HEAD.** Two-of-three was the base rate, not bad luck — and the
Claude-assisted fixes landed in exactly those subsystems (#6214→S6, #6223→S2,
#6077→S16, #6028→S3, #1803→S15).

### Merge-quality hypothesis: tested and rejected
18 pairings examined. Best untried was S15+S20 (genuine build-then-use) — dies
twice: S15 hollow, and peer `ajiteshj` already grades the same invariant. Only
S18 cleared 1a2, then died at 1b as a publicly-resolved maintainer decision the
solver would be asked to reverse. So it was not three bad merges from twenty
good surfaces; the surfaces themselves were exhausted.

### Two tooling notes folded into RUNBOOK
- `gh issue view` **silently returns empty** on some repos — confirm a
  blank-looking body with `gh api repos/<org>/<repo>/issues/<n>`.
- `gh search issues --state all` is **invalid**; only open|closed.

## Category-first ideation added — 2026-09-17 (Vidit's direction)

**Problem:** we search repo-first only, which can find only gaps that ALREADY
EXIST — precisely the population every contamination gate destroys. Measured
across our 38 tasks: `semantic_bugs` 17 + `expose_interface` 15 = ~85% of
output. Two shapes. That is a search-space limit, not a sourcing-difficulty one.

**Key structural insight:** every gate that killed a repo today applies ONLY to
existing-gap sourcing. Hollow premise, peer collision, public/closed-unmerged
PR, AI-authorship density — a capability upstream has never built is immune to
all four. When a good repo is disqualified on contamination, switching SHAPE may
beat abandoning the repo.

Added to `01-sourcing.md`: the two-axis search, a shape catalogue including
shapes we have never built (**revert-and-redo**, migration/deprecation with a
compat window, observability, API versioning, behaviour-preserving refactor),
and the note that **steps may mix shapes** — every cascade we have built is
same-shape. Also the severe trap: `expose_interface` dies at 0/0/0 "too hard"
unless the instruction names module + symbols + signature + error type.

### The model-prior fork — fork strength is now MEASURED, not argued
Replaces "two competent engineers would diverge" (a judgement call — franz-go
argued its way to a good fork score and returned 1.0) with:

> a good fork is one where the MODEL has a strong prior toward path X while the
> graded answer is Y

Probe cold, n=5, before building anything:
- >=4/5 same path AND it is the wrong one -> strong fork, build it
- >=4/5 take the desired path -> it will one-shot, do not build
- even split -> weak fork, expect a noisy pass rate

Five cheap calls replace an argument with a measurement. RUNBOOK 1c now scores
the Fork axis from this probe. Survey prompt now demands >=1/3 net-new-capability
surfaces and >=2 revert-and-redo shapes.

## EVAL-GT ROOT CAUSE — fully traced from the harness debug log

**Mechanism (not inference — read from the failing run's debug log):** for a
multi-turn task, Eval-GT reads `base_commit` from the **top-level**
`tests/config.json`, writes it to `/root/.swe-agent-env` as `BASE_COMMIT`, uses
it for a `git checkout`, and interpolates it **UNQUOTED** into the generated
`/eval.sh` as `git -c core.fileMode=false diff $BASE_COMMIT || true`. With the
placeholder, bash parses `<...>` as redirection and the 63-command script dies
at line 5 — before any test runs, in baseline AND reference phase of every
subtask. `F2P=0/0, SCORE 0.0`.

**Correct value:** top-level `base_commit` = every step's `base_commit` = the
Dockerfile SHA. My preflight check was right. `repo` is ALSO load-bearing — the
**server License gate** reads it, and `<owner>/<repo>` makes the licence check a
silent false-pass. `patch`/`test_patch`/`fail_to_pass`/`pass_to_pass` at top
level are NOT read by eval-gt for MT (proven: byte counts + F2P denominator=1).

**Why local never catches it:** `harbor/trial/multi_step.py` never imports
`load_swe_bench_config`. Oracle, `bench run` and calibration physically cannot
read that file. circl was oracle 3/3 AND got a calibration verdict — full local
signal — with the file unread.

**Second, distinct bucket — ABSENT top-level config.** The DQE cascade review
bundle cannot stage, so the task's review signal is a **permanent zero** while
eval-gt looks fine. The two arms are invisible to each other.

**Real failure counts (tbdReviewStatus is NOT eval-gt — do not conflate):**
- 9 failing on the template now, +2 pending that will = **11 of 13**
- 1 genuine task defect: `smoltcp-configurable-rawsocket-checksum-caps`, F2P=0/**1** (tests ran, oracle didn't resolve)
- 1 produced no result at all: `protoc-gen-go-mcp-shared-schema-memoization`
- Denominator is the tell: `0/0` = harness died, `0/1` = suite ran.

**Control:** `ruby-auth0-oidc-at-hash-c-hash` is the only MT task with a
substituted top-level config and the only one with `evalgt: passed`. Reference shape.

**This was already documented** in the `aai-long-horizon` plugin (lh-scaffold
step 5, lh-sanity check 14, and its rulebook: "*all of them landed on 1.4 — a
literal `<base_commit_sha>`*"). We shipped 16 tasks past a known corpus-wide
failure mode because none of OUR gates ran the check.

### preflight now FAILs on both buckets
Absent top-level config (MT) = FAIL. Placeholder/short/non-hex sha = FAIL.
`repo` not `owner/name` = FAIL. Plus cross-checks: top-level base_commit must
equal every step's AND appear in the Dockerfile. Verified against the known-good
control — passes cleanly, no false positive.

### Live state
Another session is remediating concurrently (10 configs substituted at 16:14).
Still broken: commons-geometry, jackson-cbor, zendesk-biz (stubbed at step level
too). Missing entirely: both spire tasks — my build agents, both messaged.

## APPEAL — casbin: all UPHELD, and it caught me in circular reasoning
The "closed-unmerged = hard kill" rule I cited was written FROM this run, so
citing it back proves nothing. Better non-circular position, now adopted:
**hard kill when the diff or thread contains the remedy** (public-disclosure
grounds); merely touching the same files is Novelty damage, not a kill.

**The cheat-vector argument is FALSE — verified.** Our Dockerfiles do
`git init && git fetch origin ${BASE_COMMIT} && git checkout FETCH_HEAD`, so the
61 `copilot/*` refs never reach the solver. The rule rests on training-data
contamination only.

Also: S9 hollow (already union-gated), S8 verified by execution but killed by
issue #1059, `enforcer.go:900` panic is recovered at :707 (prior log overstated
it). Only 9% of casbin LOC is untouched by the 70 remote refs.

**`gh issue list --search` and `gh search issues` silently return EMPTY for
casbin/casbin (422-class) — reproduced by me.** Second repo with this. A
title-only novelty scan reads as clean. Pull issues via `gh api` and grep locally.

## APPEAL — bc-java: all UPHELD, but it disproved one of MY OWN rules

**M2 upheld, conditional WITHDRAWN.** The gap is real — reproduced at HEAD: a
failing signer yields a 71-byte blob throwing `EOFException`; a second `close()`
is not idempotent and appends a second EOC pair, turning a loud parse error into
a quiet "Malformed content"; with two signers, signer 2's stream never closes.
Step 1 *was* re-foundable off Commons IO (BER EOC discipline, or 9 unguarded
`close()` across 5 CMS generators). It dies instead on **same-language Java peer
collisions the first run missed**: `armeria-requestcontextutil-hook-cleanup-invariants`
is step 1 verbatim, `mockito-invocation-listener-failures__steps__2_aggregate_failures`
is step 2 verbatim (and is itself an MT step 2).

**M3 fork veto OVERTURNED — and the general rule with it.** See below. Candidate
still dead: issue **#2372** publishes the exact remedy with a linked fix commit.

**MR-jar overlay lead: real, reproduced, dead.** The documented instance is
already fixed. A different live one found via a mechanism the repo's own check
misses — **return type is part of the JVM method descriptor**, so
`SSLEngineUtil.create()` returning `SSLEngine` in base vs `ProvSSLEngine` in
`versions/9` breaks the base caller. Built the MR jar, got `NoSuchMethodError` on
JDK 17. Then found issue **#2448**: opened 2 days after base, closed today, full
root cause + `javap` + reproducer + released fix.

### I had a false rule in the brief and shipped it to a running agent
"Standards-pinned behaviour has no fork" — **RETRACTED.** RFC 5280 §4.2.1.10
says an implementation "MUST either process the constraint or reject the
certificate" (the spec writes the fork down); line 713 defers CRL currency to
local policy; and bc-java's own HEAD commit is "Clarify PKIXNameConstraints
divergence from bc-csharp" — same org, same RFC, two conformant answers. The
vetoed candidate re-scored 22-23/30 once lifted. Corrected in AGENT-BRIEF-v2 and
pushed to the Rust agent mid-run, since I had explicitly told it to apply this.

### Two new rules
- **`docs/claude/` is a CONTAMINATION ORACLE, not an idea source.** Maintainer's
  agentic log; describes COMPLETED work in proposal-shaped prose. Both bc-java
  leads came from it, both burned. Ideate from what it does NOT cover. Now a
  stage 0 check alongside the release-notes AI-authorship gate.
- **Score harness-ability from the GRADING path, not the build system.**
  bc-java scored Harness 3 on "needs Gradle + JDK 25, `:core:test` ≈ 8 min".
  Reality: `javac --release 8` over 4 modules = **11.6s / 4,501 files**, a
  standalone JUnit class = **0.046s**, no Gradle, no JDK 25, no network. True
  value 4-5. A heavy project build does not imply an expensive grader.

## Wave 3 — go-zero: 1 REAL CASCADE, best candidate to date

`zeromicro/go-zero` — agent screened 30+ Go repos itself, took no pre-screen.
MIT, 91 open issues, 77,784 non-test LOC, 114 packages, **zero peer hits** across
filename + content + 12 symbol sweeps, all read. Toolchain green offline,
slowest core suite 5.6s.

**C1 flush accountability in `core/executors` — 27/30, BUILD AS 2-STEP.**
Step 1: per-flush outcome record (trigger: size/interval/explicit/idle/shutdown,
task count, completed-vs-panicked) with an observer. Step 2: retain a
non-completing batch and re-present it ahead of newer work, same ID,
`Attempt+1`, `shallQuit` blocked while pending. `newTicker` is injectable, so
fully deterministic. Conditional: step 1 must own an identifiable pending-failure
artifact (`PendingFlushes()`) or a solver does step 2 with a private `recover()`.
Risk: step 1 may land 4-5/5; two hardeners in the run log.

Also: C4 token-limiter and C5 `core/mr` cancellation → single-turn (cascade 2-3).
C2 killed by open PR #5576; C3 killed by two peer tasks publishing its fork.

**Rejection intel worth keeping:** `hashicorp/raft` has **195 peer files**
including a direct SWE-bench-pro peer — the most mined invariant family in the
corpus. ristretto 20, olric 32, rqlite 23, bbolt 15, memberlist 12. `thanos` is
peer-clean and a perfect lane fit but 611 open issues. `grafana/mimir` is
AGPL-3.0. Backups gated but unsurveyed: `hashicorp/serf`, `nsqio/nsq`.

### THE FIX: shift the hollow-premise check LEFT into the survey prompt
This agent required every surface to *"state whether this is already implemented
at HEAD and quote the line"*. Result: **zero hollow premises across 18 surfaces**
— all 18 came back marked implemented, forcing the merge stage to build from
what is ABSENT AROUND existing behaviour. Compare jackson 8/20 hollow and
bc-java's top candidate fully shipped. Folded into RUNBOOK stage 1 and the brief.

## ROLE SPLIT — Codex sources ideas, Claude validates only
| Model | Does | Never |
|---|---|---|
| Codex | wide survey, merge, score, breakdown, grading tests | — |
| MetaCode | `instruction.md` (provenance-mandatory), optional 2nd-opinion survey | — |
| Claude | hollow-premise, novelty, probes, code verification, solve.sh/Dockerfile/task.toml, preflight | generate ideas; write instruction.md or tests/ |

Evidence: Claude-as-analyst produced every wrong call today (pre-screen 2/4
wrong, false fork rule, broken dedup method). Claude-as-verifier: 4 spot-checks,
0 inflated. go-zero's Codex pass also caught a factual error in its Claude
author's write-up. Revisit if results change.

## Scoreboard
| repo | survivors |
|---|---|
| spiffe/spire | 2 (24/30, 24/30) — both in build |
| **zeromicro/go-zero** | **1 (27/30)** + 2 single-turn |
| casbin / jackson-databind / bc-java | 0, all appeals upheld |

## Wave 3 — graphiti: 1 survivor, risk stated honestly

`graphiti-api/graphiti` @ `3ec8ec0` (Ruby JSON:API resource framework, self-picked).
MIT, 46 open issues, 15,223 non-test LOC, no `copilot/*` swarm.
**AI-authorship gate: 0%** over 1,424 commits — the new stage-0 gate, clean.
**Best toolchain measured so far:** `ruby:3.4-slim` + rspec → **1,831 examples,
0 failures, 7.25s, no DB, no network**; suite runs on an in-memory PORO adapter.
Peer dedup: exactly ONE peer in the 133k corpus (sort tiebreakers), base SHA clean.

**C1 auditable include authorization — 23/30.** `Query#include_hash` resolves
includes three ways; attributes fail loudly (`AttributeError`) but relationships
vanish silently — a bare `filter` at `query.rb:294-297` and
`Util::IncludeParams.scrub` which builds a fresh hash keeping no record. Step 1
exposes `include_decisions`; step 2 adds `raise_on_rejected_include`. Cascade is
information-destruction, so step 1 is unskippable.

**Open risk, agent's own words: step 2 is probably one-shot.** Per-step gate,
last step never exempt ⇒ as specified this is 1-3/5 on step 1 and 4-5/5 on step
2, and fails. Three untested hardeners in the log; best is a policy *per denial
source* (allowlist denials refuse; readability denials stay silent so as not to
leak the relationship's existence) — that security fork is what earned Fork 4,
not a boolean switch. **Do not build until step 2 is hardened.**

### MY PRE-SCREEN WAS WRONG AGAIN — third time today
I gave puma "1 hit", grape "2", rack "4". Reality: **puma 21 peers (4 MT),
grape 20+, rack 7 peers on a single base commit `1551230`.** I labelled them
"coarse, re-verify" and the agent did — but had it trusted me it would have
burned the run. The no-pre-screen rule stands; do not soften it.

### Refinement to the shift-left fix
Require a **`file.ext:line` citation** of what HEAD does today, not just a
yes/no. graphiti got 6 of 6 citations accurate, which turned 1a2 from research
into verification. Folded into RUNBOOK.

Also: the scorer caught that this agent's own key evidence
(`spec/query_spec.rb:653-662`) is an **`xit`** — a disabled spec. The claim
survives on a live spec elsewhere, but a disabled spec is a signal the maintainer
considered that direction and declined. Worth treating as a soft novelty signal.

## CORRECTION — 0/5 on Avocado is NOT a failure (Vidit, 2026-09-17)
I had written "0/5 fails as too hard" into RUNBOOK and preflight. Wrong.

The gate is **one pass AND one fail on the SAME model**, and that model may be
Avocado, Opus or GPT. The server says *too hard* only when **all three** are
zero: `avocado 0, opus 0, gpt 0`. So Avocado 0/5 with an Opus or GPT split is a
PASS.

Operating consequence, which is the useful part:
- In-band on Avocado is 1-3 of 5, **lower is better**; 4/5 is over the ceiling.
- **Erring hard is cheap; erring easy is expensive.** Overshooting into Avocado
  0/5 usually still passes on another model. Overshooting into 4/5 does not.
  When in doubt, make it harder.
Fixed in RUNBOOK, preflight, SKILL.md route table.

## Local validation is now OPTIONAL
Skip it when slow. Correlation is 0.07 and the three causes are known (model
catalog `avocado-code-flex` vs cloud `avocado-code-flex-5p15`;
`OPENCODE_CONFIG_CONTENT` continuation critic set by cloud only; cloud runs
steps independently, local chains). Run only preflight + oracle 3/3 + baseline
diff. The server is the gate.

## SINGLE-TURN BUILDS DISPATCHED — 3 agents
Vidit's framing: one single-turn ~= 0.3 of a multi-turn; shipping beats not
shipping. These cleared sourcing, novelty and hollow-premise inside a multi-turn
survey and were parked ONLY because the cascade did not hold.

New brief: `/home/agvidit/swebench/BUILD-BRIEF-SINGLE-TURN.md` — the structural
delta (format, track_assignment, no `steps/`, top-level `tests/config.json` is
THE config with all 7 fields real, no `[[steps]]`), the calibration direction,
and the optional-local-validation rule.

| task | repo | note |
|---|---|---|
| atomic `Rewriter::modify` | gimli-rs/object | best ST lead; gradeable in memory, no `testfiles/` submodule. Host has no cargo — needs a Rust image |
| C4 token-limiter degradation | zeromicro/go-zero | 23/30, cascade 2 |
| C5 `core/mr` cancellation | zeromicro/go-zero | 23/30, cascade 3; harness-ability is the risk, told to report BLOCKED rather than ship flaky |

## In flight: 8 agents
4 multi-turn builds (spire C1, spire C3, go-zero C1, graphiti C1-hardening)
3 single-turn builds (object-rs, go-zero C4, go-zero C5)
1 sourcing lane (Java)

Docker discipline: three agents now share the go-zero clone in different
subsystems; all told never to run `bench run` concurrently and to cap k<=3.

## Wave 3 — commons-configuration: viable repo, 1 scored survivor, BLOCKED on toolchain

`apache/commons-configuration` (configuration2) @ `3359f825bd48`. Apache-2.0,
55,815 non-test Java LOC, 20 packages. **Exceptional contamination profile:**
GitHub Issues DISABLED (JIRA only), 106 open but **only 9 filed in the last two
years**; **2** inline `CONFIGURATION-\d+` markers in ALL of `src/main`; zero
`copilot/*`; 0 filename and 0 symbol hits across 151,249 peer files.

**Survivors:** C-B `ConversionHandler` parameterized-Type → aggregated
`BeanHelper` binding, **24/30**, the only scored one. Cascade scored 3 — step 2
is reachable without step 1 unless step 1's `ConversionException` carries the
element index and step 2 must echo it. Authoring blocker: `initBeanProperties`
is static with no `ConversionHandler` in scope. Two unscored and promising:
C-D XPath namespace registration → prefix-aware keys (best *structural* cascade
found — step 2 cannot emit a prefixed key without step 1), C-E location-attempt
trace → `FileHandlerListener` callbacks (clean observe-then-enforce, two
independent forks, deterministic).

**BLOCKED — toolchain gate never completed.** `mvn test-compile` did not finish;
suite runtime unmeasured; `~/.m2/repository` is 8.1M i.e. essentially empty.
Maven Central IS reachable but throughput fails under five concurrent agents:
alternating `429 [Raindrop] Ratelimit` and `Protocol family unavailable`.
`MAVEN_OPTS=-Djava.net.preferIPv6Addresses=true` is MANDATORY (without it
`InetAddress.getAllByName("fwdproxy")` throws) and `~/.m2/settings.xml` now has
an fwdproxy entry. Java resolves `repo.maven.apache.org` to the
`2001:db8:face:b00c::f` placeholder while curl reaches the real address, so the
Meta CA truststore bypass does not work. **Do not build here until a warm `.m2`
exists** — we cannot ship a task whose suite we have never run.

**MY PRE-SCREEN WRONG A FOURTH TIME.** I said commons-lang had 0 filename hits.
Actual: **18 peer tasks** — verified. Also newly burned in this lane: JCTools 9,
agrona 9, eclipse-collections 4, commons-collections 4. maven-resolver rejected
on a real peer; commons-pool rejected on **179 inline `POOL-\d+` markers** in
15,910 LOC.

**Cross-model verification earned its keep twice more:** Codex caught that
`OverrideCombiner.combine` gives precedence to its FIRST operand (killing a
left-vs-right-fold fork) and that `updateParameters` stores
`Collections.unmodifiableMap` (making a "live view vs defensive copy" fork a
15th hollow premise). Both re-verified against source.

Shift-left check working again: **20 of 20 claimed absences verified true.**

## rom-rb FEATURE PASS — the A/B result, and it is decisive

Gap-hunting on rom-rb returned **0 survivors** (best 18/30) with a structural
diagnosis: "a value-object toolkit; everything returns `self.class.new(...)`, so
almost no ownership or timing forks exist by construction."

Feature ideation on the SAME repo returned **2 survivors, both P6
revert-and-redo**:
- **D1 container-owned plugin teardown lifecycle — 27/30** (fork 5, cascade 5)
- **C3 one-shot prepared command invocations — 24/30** (fork 5)

13 candidates generated, 6 scored, 2 cleared. Both contracts fully specified.
Both carry "too hard" as dominant risk — the cheap direction.

**The line that explains the whole result:** both survivors landed in plugins
and commands — the two subsystems the gap hunt had written off as "publicly
worked". **Public work closes gaps; it does not add capability, so it does not
burn a feature.** That is the mechanism behind feature-first, stated cleanly.

Also: **13/13 `file.rb:LINE` citations verified accurate, zero hollow premises**
— the shift-left fix now proven across two different ideating models.

### Three corrections earned
1. **P6 has a P6-adjacent peer.** `vaibhavdr-swebench-pro:gojq-mt-execution-budget`
   — step 1 global `ExecutionBudget`, step 2 nested scope draws from parent's
   remaining. That is extend-not-revert so the SHAPE survives, but the **budget
   concept is burned** (doubly, with P2's shipped sparql budget). Found only by
   `gh search code`, not the local sweep: searcher grepped `with_budget`, peer
   uses `ExecutionBudget`. **Sweep a concept under several plausible names.**
2. **Naming the API contract can name away the fork.** C5 died exactly this way:
   mandatory `by:` identities and explicit `Update` records ruled out the
   positional/LCS alternative. Feature tasks MUST name the contract (or 0/0/0),
   but the contract must sit on the **boundary** — entry points, error classes —
   leaving the internal representation unnamed. New authoring rule.
3. **Fork strength on both survivors is argued, not measured.** Only C4 got the
   cold probe. Run n=5 on D1 and C3 before building.

Cross-verification again earned its keep: the agent re-grounded C4's contrived
step-2 constraint with a real mechanism, Codex then REFUTED its conclusion, and
the agent verified the refutation at source. C4 died on fork 2 as a result.

## A/B TEST — gimli-rs/object re-sourced with the composed lens. 0 → 1 survivor.

Same repo, same HEAD `2c40228`, same lane as the baseline `object-rs.md` (which
returned zero MT survivors by surveying). Compose-first re-run: `object-rs-v2.md`.

**Result: 1 survivor (S7 byte-local rewrite reports, 30/35, Fork 5 MEASURED,
Observability 5) vs 0.** Funnel moved stages: novelty killed 3 of 4 in the
baseline and **0 of 4** here; the deaths moved to the cold probe, which the
baseline never ran.

Three findings worth propagating:

1. **ALGO-CATALOGUE's "naive prior" column is language-blind, and it is wrong for
   Rust.** Probed cold, n=3 each, neutral phrasing: "add real removal with slot
   reuse to this table" → **3/3 returned generational slots + free list
   unprompted**; "let a caller keep many edit revisions of this builder" → **3/3
   returned `Arc` + `Arc::make_mut` + path-copying unprompted**. Persistence/COW
   and generational handles are the catalogue's #1/#4 and two of its three
   surviving clusters — and in Rust they are model-PREFERRED, so fork = 1. The
   catalogue needs a per-language prior column; these entries are probably still
   strong in C/Java/Go. Corollary: **observability and fork strength are
   anti-correlated for the ownership cluster in Rust** — the idioms are visible in
   the API surface, which is exactly why models reach for them first.
2. **P6 has no documented source for its step-2 constraint,** so everyone invents
   an operational caller ("a plugin host", "an OTA pipeline") and that invention
   is the weakest part of the candidate on realism. On a multi-format crate there
   is a free non-invented source: **the second format is the constraint** — step 1
   for ELF, step 2 requires the same public API for Mach-O where sections live
   inside segments and names are fixed 16-byte fields, which makes the ELF-shaped
   representation untenable. Untested; the obvious next thing to try on any
   format or protocol crate.
3. **"The peers are all on the write side" was wrong.** The luis1 peer's title
   says `write::elf::Writer`; its README says it also rewrites
   `build::elf::Builder` through nine exhaustive match sites. **Read peer READMEs,
   not subsystem labels.** `src/build/` on gimli-rs/object is peer-ADJACENT.

Also: Codex again built a candidate directly on an issue that was in the
exclusion block it was given (#833, after the baseline's #882). Novelty must stay
a separate pass by a different model — second measured instance.

## A/B — object-rs v2: 1 candidate vs 0 baseline, and the layer verdict

**S7 byte-local rewrite reports — 30/35, Fork 5 MEASURED, Observability 5.**
Step 1 `write_with_report` + `BytePatch{range,replacement}` + `apply_to`, graded
only on `apply_to(input)==output` so rebuild-and-diff passes. Step 2 kills it: a
same-length rename must not relayout, and rebuild-and-diff CANNOT pass because
`Builder::write` re-runs its Offset allocator and `write::StringTable`
re-sorts and suffix-merges shstrtab. The difficulty carrier is genuinely
non-obvious — shstrtab suffix-merging means a section's name bytes may be the
tail of another name (`.text` inside `.rela.text`), so in-place rename silently
corrupts a sibling unless sharing is detected. Fixture-free grading.
Two open calls: issue #972 is same capability space (no remedy, but this repo
killed two candidates on comment bodies already), and S7 should move down to
`build::elf::Builder` to separate it from the in-build atomic-rewriter task.

### LAYER VERDICT — the measurement we ran this for
- **C search axes — did the work.** Axis 3 IS the survivor. Axes 1/8/12 gave two
  surfaces each, none survived.
- **A (P6) — did the work, twice over:** as generator AND as diagnostic. Asking
  "what does step 2 tear out?" is what exposed two candidates as merely additive.
- **B ALGO-CATALOGUE — DEAD WEIGHT, worse than neutral.** It aimed two of five
  slots at its own #1 and #4 entries; the survivor uses no catalogue technique.

**Funnel moved stages, which is the real signal:** baseline had novelty killing
3 of 4; this run novelty killed **0 of 4**, and deaths moved to the cold probe —
which the baseline never ran.

### THE CORRECTION THAT MATTERS: naive priors are LANGUAGE-SPECIFIC
Cold probes, n=3, neutral phrasing: *"add real removal with slot reuse"* →
**3/3 returned generational slots + free list unprompted**; *"let a caller keep
many edit revisions"* → **3/3 returned `Arc` + `Arc::make_mut` + path-copying
unprompted**. Persistence/COW/generational handles are model-PREFERRED in Rust
→ Fork 1, not 5.

**I had the causation backwards and said so to an agent.** Rust makes ownership
visible in the API surface — which is exactly why the model reaches for it
first. **Observability and fork strength are ANTI-CORRELATED for the ownership
cluster in Rust.** Entries probably still hold in C/Java/Go. Always cold-probe
in the target language; it costs three calls.

### Two more
- **P6's step-2 constraint has no documented source**, so agents invent
  operational callers — consistently the weakest part on realism. Best free
  fix: **the second format IS the constraint** (step 1 ELF, step 2 Mach-O where
  sections live in segments and names are fixed 16-byte fields). Untested; first
  thing to try on any format/protocol/backend library.
- **Axis taxonomy split:** axes whose wrong path is a DATA-STRUCTURE choice
  erode with language idiom; axes whose wrong path is a PIPELINE choice do not.
- `src/build/` is NOT peer-clean — the luis1 peer's title says
  `write::elf::Writer` but its README rewrites `build::elf::Builder` at nine
  match sites. **Read peer READMEs, not subsystem labels.**
- **Codex again scored its top candidate on an issue in the exclusion block it
  was handed** (#833; #882 was the first instance). Second measured case that
  novelty must remain a separate pass from scoring.

## A/B — bc-java v2: 4 SURVIVORS vs 0 in BOTH prior passes. Best result yet.

| | v1 survey | appeal | **v2 composed lens** |
|---|---|---|---|
| survived 1a2+1b+1c | **0** | **0** | **4** |
| genuine MT cascade at 1d | 0 | 0 | **2** |
| hollow premises | 1 of 3 | 1 of 1 | **0 of 25** |

**Top: caller-scoped MLS extension registry — 33/35, Fork 5 MEASURED.** The
agent OVERTURNED Codex's own 1d by measuring it: Codex called the cascade "two
tasks in a trench coat"; the n=5 cold probe on both hosts returned **10 of 10
building a static/process-global `ConcurrentHashMap` registry** (one saying
explicitly "no per-decode plumbing"), zero threading a caller-supplied one, zero
mentioning two consumers disagreeing. That is verbatim the wrong prior axis 1
predicts. Also: snapshot-isolated ITS trust store 30, MLS commit journal 29.

Structural cause of the improvement: **order + exclusion.** 1b ran FIRST and
killed three subsystems for the price of three greps, and the survey received a
written dead-list built from `docs/claude` headings.
Control: an unlensed CMC fold scored 24 vs the lensed CTL candidate's 22 — **the
lens is worth about one tier, not a revolution.** Honest framing from the agent.

### THE MECHANISM BEHIND B's REPEATED FAILURE — saturation, measured
B was dead weight in all three A/B runs. Here is why, and it is structural:
**observability and saturation are CORRELATED, because every task-authoring
pipeline filters on observability.** We rank by gradeability; so does everyone
else; so the most gradeable techniques are the most mined.

Counts over 15,985 peer tasks: byte-for-byte **1868**, backpressure **380**,
crash recovery **323**, WAL **160** (our #1), snapshot isolation **126**, MVCC
**111** (our #2) — versus path-copy **4** and checkpoint compaction **0**.
**Five of our top six ranked entries are among the most saturated in the corpus.**
Rule added: grep the corpus for a technique before using it; prefer the
low-count entries; record the count in the catalogue.

### Five more corrections, all folded in
1. **Realism/fit is now a scored veto axis** (rubric moved to 28/40, three
   vetoes). A candidate scored 29 proposing a write-ahead log inside `bcmls` — a
   protocol codec with NO I/O layer. FORK-PATTERNS mandated a motivating caller
   and the rubric never scored it.
2. **New AXIS 19 — closed extension points at a protocol boundary.** Found 3 of
   4 survivors' hosts. Greps: enum-as-wire-code-point, dispatch throwing
   `unknown`, a registry map with no public writer, a commented-out registration
   API. bc-java's `reifyOpaque` is literally commented out at
   `OERDefinition.java:270-281`.
3. **Cascade has a free probe** — reuse the fork run: does the step-2 constraint
   appear in ANY of the n answers? 0 of n = real cascade. Saved the top candidate.
4. **P6 step-1 corollary:** P6 concentrates difficulty in step 2, so step 1
   drifts too easy. All 5 MLS probes got step 1 right unprompted. Load step 1.
5. **RFC rule sharpened:** a clause that NAMES AN ALTERNATIVE hosts a fork; one
   that SHIPS PSEUDOCODE does not, and its fix is public by construction.

Also: `pg` was the prior agent's top untouched-subsystem prediction and is
**wrong** — 183 lifetime issues, most-mined subsystem in the repo. `docs/claude`
coverage is a bad disclosure proxy; the tracker is the real one. `kmip` is dead
(5-step peer covers the whole TTLV surface). Harness-ability settled at 5: host
JDK 8 compiles 2,876 files in 6.8s, test classes run in 0.11-0.21s, no container.

## go-zero FEATURE PASS — 5 buildable from ONE repo. The per-repo thesis, proven.

41 proposals → **0 hollow premises** → ~14 past peer corpus → 13 cold-probed →
**7 at >=21/30 with MEASURED Fork >=4, 5 buildable as 3-step P6**, all in
distinct packages.

| # | Capability | Package | Step-2 constraint that kills approach A | Score |
|---|---|---|---|---|
| S4 | `VarSet` path-variable handles | `rest/pathvar` | O(1) handoff → forces copy-on-write | **28/30** |
| F3 | `ReplayBuffer` reopenable capture | `core/iox` | memory limit → forces spool to temp file | **27/30** |
| F1 | `PreparedBulkInserter` | `core/stores/sqlx` | driver param + statement-byte ceilings → chunk planning | 26/30 |
| F2 | `UnmarshalJsonArray[T]` cursor | `core/mapping` | one untyped element resident → token streaming | 26/30 |
| F5 | `KeyedLessLogger` | `core/logx` | idle reclaim without scan, no goroutine → expiry index | 26/30 |

This is the direct answer to "1-2 tasks per repo": that number was an artefact of
gap-hunting. Feature ideation on a repo already gated returned **five**.

### Probing before scoring killed 5 of 13 — including the top-scored one
Codex argued Fork 5 and scored p2c picker-state continuity **29/30**; **5/5 cold
models wrote the "sophisticated" design unprompted**, so step 1 would have been a
strawman. Same fate: tiered shedding, delta property history, periodic
timing-wheel entries, httpc retries. Forcing Codex to state a
`PRIOR-PREDICTION` per proposal paid for itself — the one wrong prediction died.

### THE P6 PRECONDITION (now in FORK-PATTERNS)
**P6 works only when the default implementation is eager / unconditional /
materialise-everything / copy-everything.** It FAILS when the clever design is
the idiomatic answer — in Go that means shared state behind pointers, generation
counters, append-only version chains, reschedule-from-the-loop, persistent trees.
Corollary: if step 1 survives step 2 intact it is not P6. F5 and F6 hit this —
fix is to make step 1 ship the O(n) version step 2 must delete.

### Part B burned — SECOND independent confirmation
Peer tasks already cover persistent/path-copying trees
(`btree-range-query-multistep__steps__3_pivot_to_cow_nodes` is literally our P6 +
COW pivot), radix prefix indexes, generation/epoch leasing, bounded metric
cardinality, WAL queues, ordered parallel map. **path-copy shows 4 hits by name
but has a peer doing our exact pivot — sweep the OBSERVABLE, not the name.**

### Caveats carried
- F1 probe is n=3 (two returned empty), not re-run.
- F2/F3/F6 share a "bounded memory" step-2 theme — **ship at most two** (F2+F3).
- F1 sits on the same `PeriodicalExecutor` machinery as the in-build
  `core/executors` task; does not modify it, but check before both ship.
- Stage-0 addendum: `.github/copilot-instructions.md` exists (343 lines, PR
  #5313) — an architecture/triage guide, not a completed-work log, covers none
  of these. Not disqualifying, but the repo invites agentic contribution.

## object-rs S7 — BLOCKED. The fork-collapse rule killed our highest-scored candidate.

30/35, Fork 5 "measured" — and it died 8/8 on the desired path. The rule was
added hours earlier; this is its first live catch and it paid for itself.

| condition | observable stated? | n | desired path | found the trap unprompted |
|---|---|---:|---:|---:|
| F control — withheld | no | 3 | 0/3 | 0/3 |
| E step 2 as designed | yes | 5 | **5/5** | **5/5** |
| G prescribed re-cut, capability only | partly | 3 | **3/3** | **3/3** |

**The methodological lesson: v2 probed STEP 1 and inherited the score.** P6's
premise is that step 2 states the constraint, so **step 2 is where collapse
happens** — step 1 genuinely held at Fork 5 (0/3). Probe the step that states
the constraint. Now in RUNBOOK.

5/5 refused the rebuild path *because it suffix-merges the string table*, two
naming `write::StringTable`'s sorting/dedup explicitly, and all five found the
sharing trap with the right remedy. The claim carrying the 30 — "invisible to
anyone who has not read `src/write/string.rs`" — is refuted by measurement.

### The real collision was OURS, not a peer's
`object-rs-atomic-rewriter-modify` (already built and committed) has a
`base_commit` byte-identical to S7's pin, same `Rewriter` struct, same 137-LOC
file, and its grading primitive is byte-identity of `Rewriter::write` output —
which is S7 step 1's too. **Same repo + same commit + same struct beats
same-file-different-commit.** New rule: diff candidates against our OWN in-flight
task dirs and their base_commits, not just the peer corpus.
The luis1 peer does rewrite `build::elf::Builder` (confirmed by reading its
oracle patch, not its README) but at base `836fa16` on `.dynsym_shndx` — merely
adjacent. #972 and #719 both amber, neither a remedy.

### Premise verification by execution — which v2 never ran
- Confirmed: no-op rewrite changes 1,295 bytes in `/bin/true`, 2,435 in
  `/bin/ls`, 1,971 in `libz.so.1`; a large Rust binary changes *length*.
- **Corrected:** suffix sharing is real, but the pairs are `.plt` inside
  `.rela.plt` and `.got` inside `.plt.got`. **v2's `.text`/`.rela.text` example
  does not occur in a linked executable.**
- New: a same-length rename makes the file **8 bytes longer** — breaking the
  suffix share forces a standalone string entry.
- **My brief's assumption was wrong:** `Builder::write` did NOT fail outright on
  any tested binary; #719's "fails outright" is not the common case.
- Neither `Builder` nor `Rewriter` retains input bytes, so either layer needs a
  provenance field first — which 5/5 probes proposed unprompted.

Open: step 1 alone is a measured Fork 5 and could stand single-turn, but its
observable is satisfied by the rebuild-and-diff path all three control probes
wrote, so expect it to calibrate easy. Not recommended without a re-cut.

## bc-java v2: ALL THREE SURVIVORS DEAD. My "4 survivors vs 0" claim is FALSIFIED.

| candidate | scored | measured | how it died |
|---|---:|---|---|
| C1 caller-scoped MLS registry | 33/35 | **10/10 executed** | fork-collapse + parallel-API 9/10 |
| C5 snapshot-isolated ITS trust store | 30/35 | **6/6 executed** | 5 grounds: burned observable, parallel-API 6/6, realism veto, fork-collapse |
| C6 MLS commit journal | 29/35 | **9/10 executed** | cost constraint, parallel-API 10/10, burned observable |

The A/B result I reported as "bc-java 4 vs 0" was **4 scored, 0 measured**. The
correct read is **0 survivors** — the new framework got further through the
funnel but did not produce a buildable task here. C6's own agent re-scored it:
Fork 1 (scored 5), Cascade 1 (scored 4), Novelty 1 (scored 3) → **real ~17/35,
not 29.**

### The scoring pass was less reliable than its own caveats
In **two of three** cases the kill was already written in the source report:
- C5's 1d table said `single-turn | unchanged (not probed)`, Cascade 2 — I
  dispatched it off the 30/35 headline anyway. My error.
- C6 was flagged in the v2 run's own closing note #1: `bcmls` has no I/O layer,
  so a journal invents a persistence subsystem inside a protocol codec. The
  Realism/fit axis (added later) would have killed it for free.

**Novelty 3 was assigned by counting TECHNIQUE NAMES; nobody swept the
observable.** That is the systematic defect — C6's observable turned out to have
**31 peers matching its full triple-shape (torn tail AND idempotent AND
append), 11 of them multi-turn**, including a near-exact structural twin:
`koko-tbench:wal-write-behind-migration` — 2-step MT, step 1 a crash-safe
append-only ledger, step 2 migrating it with tail-truncation replay preserving
the external recovery contract. Same A-shape, same B-technique, same step-2
verb, same observable. Only Python-KV vs Java-MLS differs.

### COMPOUND constraints — a sharper form of the cost rule
C6's step-2 constraint was **cost + behavioural**: "bounded per-commit I/O" plus
"crash at any write boundary recovers to before-or-after" plus "idempotent
replay". The behavioural half does **not** invalidate step 1 — atomic
`tmp`+`fsync`+`rename` satisfies it while keeping step 1's whole-file format.
Only the cost half rules that out. So: **keep the cost clause → it names the
technique → fork zero; drop it → step 1 survives → P6 never engages. There is no
third option.** When a constraint is compound, test each half separately for
which one is actually doing the work.

Worse: **phrasing B removed the cost clause entirely and still measured 4/5** —
crash-recovery alone walks the model to a WAL. The technique is model-preferred
regardless of framing.

### Grader would have failed correct work — third instance
`pB-5` used atomic rename and satisfied the entire intended observable. Failing
it would require asserting on-disk record framing. Same defect as go-zero S4
(grader asserted a shared backing pointer while valid solutions used HAMTs).
**Design the grader from the DISTRIBUTION of valid answers, not from the
intended one.**

---

# RUN `.e2e/distsys-1` — belaban/JGroups, distributed-systems lane, 2026-09-30

**Outcome: `A3 EXIT: NO SURVIVOR — REPO EXHAUSTED`. No task pushed.** One repo screened to G10,
two A2 rounds (budget spent), 61 surfaces, 3 cards, 3 kills, 0 survivors. All artifacts under
`.e2e/distsys-1/`; the mandatory kill ledger is `.e2e/distsys-1/kill-ledger.md`.

## The repo was good. That is what makes the result informative.

`belaban/JGroups` passed every A1 gate with room: Apache-2.0 (no §7 conflict), HEAD the same day,
**0%** AI-authorship (69 identity hits over 921 commits, all `dependabot[bot]`), **0** peers on the
core repo, **38** unresolved issues on the real tracker, **103,231** non-test LOC across 15
packages with **29,251** of it in subsystems at `churn90 <= 9`, 198 in-memory TestNG fixtures, and
a graded path of **10 s offline**. It is a better-screened repo than most we have built on.

It still yielded nothing, and the reason is specific and reusable.

## THE FINDING — a repo can be defect-rich and multi-turn-poor, and nothing upstream of GATE 6 sees it

Three cards, three steelmen, and all three steelmen converged on one sentence: **the defects that
remain in this codebase are individually substantial enough to be worth fixing and individually
too small to be half of a multi-turn task.**

Enumerated, on the one card whose premise was reproduced by execution (`TPConfig.setBundler` stops
the incumbent bundler before the candidate's `start()` can throw, leaving a stopped bundler
installed and the data plane dead), **five** candidate second steps were tried:

| proposed step 2 | why it died |
|---|---|
| deliver the incumbent's queued content before retiring it | the interface exposes `size()` but **no way to extract the queued items** — needs a symbol absent at base → GATE 0 |
| destroy the replaced bundler; retire a failed candidate instead of leaking it | ~15–25 production lines → N04 |
| a candidate installed while the transport is not running must not be started | behavioural and deterministic, but "before init" is literally the title and body of the applied PR on that function |
| replay the installed view to the candidate before its first send | one guarded callback; large only if made concurrent, which re-creates the nondeterminism that killed the original step 2 |
| forward `resetStats()` to the bundler | one call |

Combining the last three is a bag of sibling guards — the decorative cascade `GATE 7` rejects.
**Step 1 was never the problem on any card in this run.** That inverts the corpus prior (81% of
"too easy" blame lands on step 1) and it is why the size floor now has to be applied per step at
survey time → `A2` §6a, and per step at the gate → `A3` GATE 6 N04.

## Two engines, run in parallel, overlapped on 1 surface in 36

Round 1 asked MetaCode and Codex the same question. Both returned 18 surfaces. **Exactly one seam
was found by both** — and it was the round's top-ranked card. A single-engine survey is not a
sample of the repo; it is a sample of one model's attention. Promoted into `A2` §3.

Round 2, narrowed to the strictly in-domain subsystems and carrying six validity filters derived
from the round-1 kills, returned **0 cards from both engines** over 25 surfaces. Four of Codex's
thirteen were **already implemented at HEAD** with the invariant stated verbatim in the source —
hollow premises caught at survey time rather than at GATE 2, which is the shift-left `A2` §3 wants.
The convergence is the load-bearing fact: it is not one model being pessimistic.

## THE VALIDITY GAP — A2's four axes are all generative, and two cards died on neither of them

`A2`'s "no ideas is a verdict about this act" box lists four axes you must try before writing zero.
All four ask *can I generate a premise here*. Neither asks *is the premise valid*. Two of the three
cards died on questions that cost nothing to ask at survey time and a full `A3` pass to discover:

- **Is the behaviour you would require actually correct?** The top-ranked card required a message
  naming an unknown fork identity to be restored to the residual batch — and that residual is
  delivered to the **main** channel, so the "fix" would hand fork-scoped traffic to the main
  application. Both shipped paths already agreed; the asymmetry was invented. Same trap as
  `R6` Part B's *"the 'desired' behaviour can be the wrong answer"*.
- **Has a documented decision already rejected it?** `ProtocolStack.replaceProtocol` says verbatim
  *"Should be done before the stack is connected"*, and the card's whole motivating caller was
  live replacement in a connected stack.

Both are now `A2` §"the four axes are all GENERATIVE" as V1 and V2.

## A1's four peer sweeps are all NAME-based and all four missed the only real peer

`belaban/JGroups` read peer-free through G1: 70+ hits across filename, content, symbol and live
name sweeps, **every one** resolving to `jgroups-extras/jgroups-raft`, a different repository. The
real peer, `codimango/CtrlG_DetectPatch`, never writes the string `jgroups` except inside a GitHub
URL in its `task.toml`. It was found only by `A4`'s **owner/repo slug** query. Hoisted into `A1`
§3 as sweep 5 and into the G1 checklist row.

It also exposed an `A4` defect that would have killed the lane outright: `A4`'s `COLLIDES` row read
*"a peer on the same upstream repo"*, full stop, which contradicts `A1` G1's subsystem threshold and
`A1` §3's commit-and-struct ranking, and would kill any repo that has ever hosted one peer task.
Corrected to *"at the same seam"*, with the different-seam case producing a recorded exclusion zone.

## The kill audit earned its place — it corrected a rationale rather than rubber-stamping it

Dispatched briefed to **argue the candidates are ALIVE**. It upheld all three kills and
independently reached the GATE 3 split below — but it **overturned part of the Card 3 rationale**:
live protocol insertion into a connected stack is real in-repo practice (the probe handler
registers only after `startStack()` and does insert→hook→init→start; `Util.shutdown` and
`DynamicDiscardTest` both insert into connected stacks; `ForkChannel.getFORK` inserts a `new FORK()`
with no lifecycle call at all). The card still dies, on `insertProtocol`'s own *"already created
(and initialized)"* contract and on size. The corrected rationale is what the ledger records.

It also surveyed two seams **neither** round-2 survey examined — `util/RequestTable` (four real
defects, including `forEachNonBlocking` snapshotting `buf`/`lo`/`hi` but indexing through the
*current* `buffer.length`, deterministically exposable with a reentrant visitor that calls
`grow()`) and `FD_ALL3.setTimeout`/`setInterval`. Both real; both under the size floor or needing
a migration policy that is unstatable at base.

## GATE 3 CONFLICT, now load-bearing for the first time — Owner: human

The hard-kill list (*"any merged public PR touching the surface"*) and the 2026-09-23 disclosure
split (symptom allowed / cause kills / remedy kills) give **opposite answers** on the bundler card.
`TPConfig.setBundler` carries `#807` (CLOSED, landed `5658b5e7f`) and `#860` (CLOSED, comment
*"Applied"*, landed `f190fddab`, diff byte-equal to current HEAD). Neither commit body mentions
preparation failure, rollback, a stopped incumbent, or destruction — they **introduced and
refactored the hazardous shape without publishing its cause or remedy**. Recorded in `A3` GATE 3 as
`CONFLICT — UNRESOLVED`; the strict reading was applied and both were written into the handoff.
Note the conflict did **not** decide this run: N04 kills the card independently.

## Live, unbuilt, and worth someone's time

`TPConfig.setBundler` failure atomicity is a **single-turn** candidate, reproduced by execution,
fully IN-BASE, deterministic, in an operator-facing `@ManagedOperation`, with **four** independent
branches each carrying a distinguishing mutant. It is recorded in `.e2e/distsys-1/kill-ledger.md`
with its reproduction output. Owner: Vidit.

---

# `conc-1` — 2026-09-30 — lane: runtime concurrency — apache/mina-sshd — NO SURVIVOR, REPO EXHAUSTED

Full record: `.e2e/conc-1/{A1-shortlist.md,A4-corpus-prior.md,A2-handoff.md,A3-gate-record.md,
kill-ledger.md}`. Twenty cold implementations kept at `/tmp/conc1/probe{,2,3,4}/impl-{1..5}`.

**A1** screened 33 repos in the concurrency lane. One survivor: `apache/mina-sshd` — Apache-2.0,
0 peer tasks, **0% AI-attributed authorship** (0 of 295 two-year commits, 0 of 16 remote branches),
55 real open issues, 161,429 non-test Java LOC, 20,037 LOC of low-churn targetable concurrency
packages, an 88 s image and a **6-8 s offline graded path that was byte-identical on every one of
~40 container runs.** Runner-up `grafana/dskit` is blocked at the G2 "Ambiguous" row, `Owner: human`.
Thirty-one rejects are listed with evidence; the instructive one is **`apache/tomcat`, which the
28-day-stale local corpus read as 0 peers and the live sweep read as 10** — two authors have mined
it, including `tomcat-http2-priority-ignore` inside this very lane.

**A-shapes instantiated:** P4 (snapshot vs view) as the primary lens, P3 (ownership/lifetime) as
secondary. Neither reached a build, so **neither instantiation count advances**. P1 remains at 3.

## The finding: a fork that exists only while a clause is UNSTATED is not a fork

`STATUS: LIVE`, n=10 paired implementations, same generator, same sketch, same repo.

| the discriminating clause | probe result |
|---|---|
| unstated (graded, not said) | **2 of 5 pass — in band** |
| stated, everything else identical | **5 of 5 pass** |

`A3` GATE 4 step 4 says "generate n=5 from `CONSTRAINT` alone", and a card that leaves the
discriminating clause out of `CONSTRAINT` therefore gets an in-band reading for a task that will
come back 5/5. `instruction.md` must state it — a silent spec with a pinning test is
`BAD_GRADING_WRONG` on 4 of 4 peer tasks — so the in-band reading measured a contract that can
never ship. **The delta between the two runs is the diagnostic, not the first number.** Written
into `A3` GATE 4.

## The second finding: the error-representation-only repo signature

Across 20 implementations, 2 cards, 2 packages, 2 maven modules, **every divergence was about how
to represent a failure** — widen an `isClosed()` predicate or not; set the cause before the
done-flag or after; throw versus return an already-failed handle; a boolean versus a throwable
versus an unconditional success. **Not one was about mechanism.** Such a fork has two exits and
both are closed: pin the representation and it collapses to 5/5; leave it unpinned and the graded
test pins what the prose did not. This is `A3`'s own repo-retirement condition — *"implements a
published spec and what the spec leaves open is only error reporting"* — reached the expensive
way, after a full `A2` and four probe rounds. Written into `A1` as **G9b**, a 60-second pre-check.

The kill is **lane × repo**, not repo. Keep the `mina-sshd` shortlist row; its parser and codec
families were never surveyed.

## The kill audit earned its place

Codex, briefed only to argue the candidates were ALIVE, returned `AUDIT: KILL INVALID` and was
right: it found two verified **3/2 splits** in the real patches that my sketches never observed
(capability precedence on a hybrid future; the aggregate truth value on abandonment), and it caught
that my CARD 1 sketch never read the parent cause the CONSTRAINT demanded. Two more probe rounds
were spent on its findings. The second round is what produced the measurement above. **Rounds 1
and 2 were not valid kills, and without the audit this run would have retired the repo on a
convergence reading.**

## A stale rule nearly decided it

`A3` GATE 8 still states *"Fork ≤2 is an absolute veto. Do not build."* `RULES.md` retires that as
`S-004`, superseded by `R-005` (**branch count ≥3**). I had written the kill on the veto before
re-reading the ledger. Re-derived on `R-005` the kill survives — branch count against the real
solver population is **2**, of which one is representation ambiguity, so the fair count is **1** —
but GATE 8's prose and the ledger give opposite answers and a future run will hit it too.
`Owner: Vidit` — the S-005 note is explicit that this rule must not be flipped by an argument.

## Live, unbuilt, and honestly not worth someone's time

`KeyExchangeMessageHandler.shutdown()` abandoning every parked `PendingWriteFuture` is a real
defect — settled at base by `drainQueueTo` on the flush path and by nothing on the shutdown path,
one screen from `AbstractSession.preClose()`, which drains `pendingGlobalRequests` with exactly the
missing idiom. Zero coined tokens, 8 s deterministic graded path, reproduced by execution. It is
recorded in `.e2e/conc-1/kill-ledger.md` with its reproduction output. It would come back **4/5 or
5/5** because its only fair discriminator is one placement error in one of five arms. Declined
deliberately rather than shipped as a single-turn task the server's own rule would have passed.

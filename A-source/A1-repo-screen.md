# A1 — REPO SCREEN

| | |
|---|---|
| **Owner** | parallel subagents, N lanes, **one territory each** (3+ lanes proven safe — `00-ROUTER.md` §6) |
| **Input** | a territory/lane (a language, a sub-domain, or an explicit repo list) |
| **Output** | a ranked shortlist, every row carrying **measured** harness timing |
| **Exit** | every repo in the lane screened, each with pasted evidence: **N survivors reported, whatever N is — including 0, 1 or 2.** ≥3 is the *target*, never a quota. An evidenced "this lane yields 1" is a complete exit; manufacturing a third survivor is a failure of the act. |

You are screening repos, not ideas. Produce no task premises here; that is `A2-idea-generate.md`.

## 1. Lane non-negotiables

- **Do not accept any pre-screen, including this brief's own repo list.** Coordinator screens were wrong **4 times out of 4** — most damningly `commons-lang`, reported "0 hits", which has **18 peer tasks**. Run every gate yourself. `STATUS: LIVE`
- **Do not manufacture a survivor.** Three of four A/B repos returned zero and those were the correct answers. An evidenced "this repo is dead" outranks a repo that dies at calibration two days later. If the lane yields <3, report <3.
- **Report the repos you rejected and why**, not only the survivors — that evidence is what stops the next lane re-screening them.
- **Few repos, many tasks.** Target 5–6 tasks per surviving repo so the Dockerfile, the dedup sweep and the toolchain fight amortize. A repo that passes A1 is a durable asset: re-survey it later even if — especially if — gap-hunting returned nothing. `STATUS: LIVE`

## 2. Gate order — cheapest kill first

Run in this order. Each gate is a hard kill. Budget **~6 minutes per repo** through G1–G6; if a repo is still ambiguous after that, drop it. A fast switch beats a slow rescue. `STATUS: LIVE`

| # | Gate | Kill threshold | STATUS |
|---|---|---|---|
| G1 | **Live peer sweep, before cloning** | any peer task on this repo's subsystem/invariant | LIVE |
| G2 | **Branch + agentic-artifact gate** | `claude/*`, `codex/*`, `copilot/*` merged or closed-unmerged branches; `.claude/`, `CLAUDE.md`, `AGENTS.md`, `docs/claude/`; claude-code-action in CI | LIVE |
| G3 | **AI-authorship density** | >~25% AI-attributed fixes, by the corrected method in §4 | LIVE |
| G4 | **Issue density + disclosure posture** | >~500 real open issues, or a visible "we file every known gap" culture | LIVE |
| G5 | **Licence** | see §7 — **CONFLICT — UNRESOLVED** | CONFLICT |
| G6 | **Liveness** | last default-branch commit older than **~12 months** → generate nothing against it | LIVE (PEER) |
| G7 | **Size and subsystem count** | <15k non-test LOC, or one or two packages only | LIVE |
| G8 | **Can it host a name-free task?** | value is "you could add feature Y" and nothing else | LIVE |
| G9 | **Fixtures and test infra** | the only gradeable fixtures would be hand-built stubs [N03] | LIVE (PEER) |
| G10 | **Harness timing — MEASURED** | graded path >10 min, needs network, or is nondeterministic | LIVE |

G10 is the exit gate: a shortlist row without a measured number is not a shortlist row.

## 3. Peer dedup — the method is the gate

**Two sweeps are required — local corpus AND live search. Neither alone is sufficient.**
`STATUS: LIVE` (measured 2026-09-22)

```bash
cd /tmp/llc && git pull                                  # goes stale; measured 16 days behind
find . -iname "*<repo>*" -type f                         # 1. filename sweep — highest signal
grep -rli "<repo>" tmp/tasks                             # 2. bare-name content sweep — READ the hits
grep -rliF -- "<distinctive symbol>" tmp/tasks           # 3. invariant/API symbol sweep
gh search code --owner codimango "<repo>" --limit 30     # 4. live — PRIMARY, not a supplement
```

`/tmp/llc` holds **133,263 unique tasks** and **151,249 copied `instruction.md` files** (a later
count read 154,135); real copies live at `/tmp/llc/tmp/tasks/<participant>/<task>.md`. Clone it
over `ssh://git@github.com:22/...` — HTTPS 403s because a global `insteadOf` rewrite forces HTTPS.

Both directions of error are live, all measured:

| Failure | Evidence |
|---|---|
| Local corpus misses live peers | `greptimedb` — **3 direct peers** found only by `gh search code` |
| Live search misses nothing the local corpus had, but the local corpus over-reports | `apache/orc` — **1,014** local filename hits, every one `orchestrat*` |
| **Sweep the dependency's org too, not just the repo's** | `bunny` read clean under **three** sweeps of its own name and died on **`ruby-amqp`** |
| Slug screening is worthless — peer instructions are de-identified | `casbin/casbin` returned **0** against **~11** peer tasks, including a 2-step MT 5 commits behind HEAD |
| Homographs | `spire` → 24 files, all *Slay the Spire* / *Aspire* / "inspired"; **17 of 18** `SVID` hits were the substring in `exportAsVideo`; `opa` returned **7,587** |
| Cross-port peers count | jCasbin / casbin-rs / php-casbin burn the same invariant as casbin; jackson-core collides with jackson-databind |
| Same-commit crowding | `mustermann` `507eb15` had **≥3** miners; `chromem-go` had **six** participants on `fbeda8a`; `redb` shared `fe01411` |
| Embedding search under-reads | `similar-tasks` scored `zendesk/biz` top match **0.652** and missed two same-gem peers |

**Zero peers is NOT clean.** `vortex-data/vortex` has **0 peer tasks** and **1,366 remote branches** including dozens of `origin/claude/add-*`, plus `.claude/`, `CLAUDE.md`, `AGENTS.md` and claude-code-action in CI. It died at G2, not G1 — run G2 on every repo that passes G1. `STATUS: LIVE` (measured 2026-09-22)

**Check our own in-flight work, not just the peer corpus.** The worst collision found for object-rs S7 was ours: byte-identical `base_commit`, same struct, same file, same grading primitive. Same repo + same commit + same struct beats same-file-different-commit. Diff against `/home/agvidit/swe-bench-pro-agvidit/*/tests/config.json`.

**Tool limits — a nonzero exit or non-JSON response is UNKNOWN, never clean.** `gh search code` does ~10 queries/minute, silently 403s in loops, and caps at ~60 results/query (counts are lower bounds). `gh repo list --limit 1000` silently stops at 1,000 although the org has **5,105** `swe-bench-pro-*` repos and ~22,000 total. Renamed repos have returned **422** that loose scripts consumed as clean.

**Free intel — other authors publish their repo pools inside codimango:** `codimango/swe-bench-pro-jayzong:docs/repo-candidates/*` and `codimango/swe-bench-pro-aaitemp:discovery-f/*.json` (**1,124** auto-classified repos with PASS/FAIL). Read them before screening a lane. **Being in a pool is a race signal, not a kill** — someone else may be screening that repo today, so weight freshness, not exclusion. `STATUS: LIVE` (measured 2026-09-22)

## 4. AI-authorship density — corrected method

`STATUS: LIVE` — the old body-grep method is **retired**, it false-positives three different ways.

**Never grep commit bodies or author-name substrings.** Measured 2026-09-22:

| Repo | Naive read | Truth | Cause |
|---|---|---|---|
| `apache/velocity-engine` | 450/500 AI commits | **0** | a human maintainer is named **Claude Brisson** |
| `diffplug/spotless` | 104/500 | **2/500** copilot-authored | body text mentions the tool |
| `apache/santuario` | 291 | **2** | `Co-authored-by: dependabot[bot]` |

**The correct method — three signals, all identity- or artifact-based:**

1. **Author/committer identity** on the commit record (not body prose).
2. **Merged `codex/*` / `claude/*` / `copilot/*` branch merges** — `git branch -r`, on a **full**
   clone; a `--depth` clone shows nothing and is not evidence.
3. **Release-note attributions** of the form `(fix by @x, w/ Claude code)`:
   ```bash
   f=$(ls <clone>/release-notes/VERSION* 2>/dev/null | head -1)
   grep -ohE '\(fix by [^)]*\)' "$f" | sort | uniq -c | sort -rn | head
   ```

Bar: **above ~25% AI-attributed, reject the repo.** Measured on jackson-databind 3.x: **86 of 154 attributed fixes (55.8%)** are "w/ Claude code" — 77 occurrences, 48 in 3.2.0 alone, at ~157 commits/month. The symptom downstream is hollow premises: jackson came in at **8 of 20 surfaces already implemented at HEAD**, in exactly the subsystems the Claude-assisted fixes touched. This is family-level solution leakage; no per-candidate check finds it.

`docs/claude/`, `.claude/`, `AGENTS.md` are a **contamination oracle, not an idea source** — they describe *completed* work in proposal-shaped prose. Two bc-java candidates were sourced from there and both were already implemented or public. Use them in reverse: ideate only from code they do not mention.

## 5. Issue density and disclosure posture

`open_issues_count` **includes pull requests** — one curator repo read 134 and had **121** real
issues. Subtract before applying the band. `STATUS: LIVE` (measured 2026-09-22)

| Real open issues | Policy |
|---|---:|
| `< ~150` | normal screening; `franz-go` had 2 and supported an undiscussed net-new capability |
| `~150–500` | lower expected hit rate; every candidate surface must be searched early, not late |
| `> ~500`, or "we file every known gap" culture | HIGH sourcing risk — prefer another repo |

Mbed-TLS/mbedtls: **1,649** open issues. One track burned its entire ideation budget on four
capability surfaces — ciphersuite policy inspection, SKI/AKI issuer linkage, X.509 profile policy,
DTLS anti-replay — and **all four** already had an open upstream issue (#9424, #194, #8120, plus a
commit documenting the anti-replay gap). Peer dedup was clean; sourcing killed it anyway.

**The tracker understates disclosure.** casbin passes the density gate at **37 open issues** while
carrying **~60 `copilot/*` closed-unmerged** agentic PRs each implementing a named gap, an open
roadmap issue **#1608 enumerating 11 planned capabilities**, **96** `[feature]`-labelled issues and
**36** feature-shaped branches. Treat closed-unmerged as a hard kill — the fix is public either way.

A **feature-dormant** upstream (few open issues, no recent feature PRs) is the inverse signal and is
unusually safe.

## 6. Liveness, size, seam quality

**Liveness [PEER §8.1]** — batch gate, once per repo, before any card. `STATUS: LIVE`
Report last default-branch commit date, last release date, and merged PRs in the last 90 days split
human vs bot. **Never use `pushed_at`** — it moves on any ref push and reads alive for dead repos.

```bash
gh api repos/<slug> --jq '{slug:.full_name,stars:.stargazers_count,license:.license.spdx_id}'
gh api repos/<slug>/commits/HEAD --jq '.commit.committer.date'
gh api repos/<slug>/releases/latest --jq '.published_at'
gh pr list -R <slug> --state merged --search "merged:>=<90-days-ago>" --json author --limit 100
```

Star band: prefer **5k–15k**. If the band is exhausted under the exclusion list, report **"band
exhausted"** rather than reaching for a weak pick; you may then widen to ~2k–20k with explicit
justification. `STATUS: SCOPED-TO PEER's JS lanes` — OURS never used a star band.

**Size — measure, do not guess.** `xargs wc -l | tail -1` **undercounts** when xargs splits, because
each chunk prints its own `total`; sum them:

```bash
LOC=$(find $R -name '*.go' -o -name '*.rb' -o -name '*.rs' -o -name '*.py' -o -name '*.java' \
      | grep -vE '/(vendor|node_modules|third_party)/|_test\.|/test/|_spec\.' \
      | xargs wc -l 2>/dev/null | awk '/ total$/{s+=$1} END{print s+0}')
SUB=$(find $R -mindepth 2 -maxdepth 3 -type d | grep -vE '/(\.|vendor|node_modules|testdata)' \
      | while read d; do ls "$d"/*.go "$d"/*.rb "$d"/*.rs 2>/dev/null | head -1; done | wc -l)
```

Want **60k–150k** non-test LOC across many subsystems. Carry `LOC` and `SUB` into the HANDOFF —
`A2` sizes its survey from them and must not re-measure.

**G8 — can this repo host a name-free task?** `A3` rejects any candidate whose graded assertion
needs a name absent at `base_commit` (`→ A3-idea-gate.md §GATE 0`). So the best repos have a **rich
existing public API where behaviour can go wrong**. For each shortlisted repo answer concretely:
*if a defect existed in subsystem X, could I assert it through an existing public entry point
without naming anything new?* Repos whose value is "you could add feature Y" score LOW —
`expose_interface` is **1 passed / 13 failed** corpus-wide. Favour parsers/serialisers with
round-trip APIs, engines with an execute/apply entry point, clients with request paths, stores with
read/write APIs, anything with an existing observer/callback/hook.

**G9 — seam quality [PEER §6].** Prefer repos with real concurrency, transactions or external
state (that is where failure-injection and conflict contracts live), an existing upstream idiom that
is subtly wrong for a plausible new requirement, and **realistic in-repo fixtures the graded tests
can reuse [N03]** — a test app, a fixture corpus, example inputs. A seam whose only gradeable
fixtures would be hand-built stubs fails N03 at scaffolding and usually drags R08 with it, because
synthetic fakes accept only a narrow shape and reject solutions calling the real API. Reject repos
whose interesting behaviour is assertable only through a wall clock or a race.

## 7. CONFLICT — UNRESOLVED: licence policy

Three sources, two incompatible positions. Two screening agents hit this independently on
2026-09-22. **Do not pick a side; record the repo's licence verbatim and flag it for the human.**

| Source | Position |
|---|---|
| OURS `MT-BATCH-KILL-CRITERIA.md:12` | **Hard-blocks** AGPL-3.0, SSPL, Commons Clause, non-commercial CC, CreativeML OpenRAIL-M. Eligible: MIT, Apache-2.0, BSD, GPL v2/v3, LGPL, MPL-2.0 |
| OURS `1-brainstorm.md:1138` | **Only CreativeML OpenRAIL-M / Ethos is prohibited. Copyleft is a PLUS (contamination-resistant). AGPL/SSPL: warn, do not reject** |
| `/home/agvidit/swebench/codimango-external-repos-spec.md:178` | **Hard-blocks** AGPL-3.0, SSPL, Commons Clause, non-commercial CC, CreativeML OpenRAIL-M, citing the Growlithe SWE-Bench Pro Q&A (updated 2026-07-19). Notes an open question on whether benchmark/training-data inheritance changes copyleft classification (T270837899, T272947851) |

PEER `01` §6 requires a permissive licence (MIT/Apache-2.0/ISC/BSD) and blocks CreativeML
OpenRAIL-M only — it supplies no server verdict that decides the AGPL/SSPL question.

Operationally until a human resolves it: MIT / Apache-2.0 / BSD / ISC are clean under all three
positions — prefer them and the conflict never binds. Read the licence file locally
(`head -5 LICENSE* COPYING*`); 14 backlog candidates were `NOASSERTION` through the API and
resolvable locally. For dual licences cite the eligible arm actually used (Mbed TLS Apache-2.0, H2
MPL-2.0, JTS EDL-1.0/BSD-3).

## 8. G10 — harness timing, MEASURED

This is the exit gate. Measure it; do not infer it. `STATUS: LIVE`

**Measure the GRADING path, not the project build system.** bc-java was scored Harness 3 on
"needs Gradle + JDK 25" (`:core:test` ≈ 8 min). A direct `javac --release 8` across four modules
compiles **4,501 files in 11.6s** and a standalone JUnit class runs in **0.046s** — true
harness-ability 4–5. A heavy build system does not imply an expensive grader.

Record per repo: image build time, dependency install time, and wall-clock of the graded subset.

| Requirement | Detail |
|---|---|
| Graded subset runs **<10 min**, offline, deterministic, in-container | H2's full suite exceeded the gate and required a subset |
| **No network during tests** | network-dependent suites are not stable verifier surfaces |
| Build fits `build_timeout_sec` | Rust/cargo is the risk — raise to **3600** |
| Deps install in the chosen base | `ruby:*-slim` needs `libssl-dev` for native OpenSSL gems |
| Host toolchain is **host-specific — verify it** | wave-2 inventory: Java, Maven, GCC, CMake, Go, Python present; **Ruby and Cargo absent**. Validate those in `ruby:3.3-slim` / `rust:1-slim` containers |

**Maven Central is unreachable directly from this host.** The working mirror is
`https://maven-central.storage-download.googleapis.com/maven2` declared as
`<mirrorOf>central</mirrorOf>`, and `docker build` needs `--network=host`. The 429 is a **global
per-hostname RPS cap, not an allowlist gap** — ten concurrent Java tracks will rate-limit each
other, so stagger them. `STATUS: LIVE` (measured 2026-09-22)

## 9. Ranking the survivors

Rank on taxonomy gap after all gates pass — never use it to rescue a failed gate. Live snapshot
**39,434 tasks, 2026-09-14**; negative `gap_pct` is under-supplied.

| Language | gap_pct | | Sub-domain | gap_pct |
|---|---:|---|---|---:|
| Ruby | **-5.81** | | web_frontend | **-6.05** (deterministic testing is harder) |
| Java / Kotlin | -2.95 | | security_and_privacy | **-4.22** (best risk-adjusted: deep and testable) |
| Rust | -2.11 | | web_backend | -3.91 |
| Go | -1.95 | | systems_and_infra | -3.60 |
| JS / TS | -1.32 | | ml_ai_infra | -3.58 |
| C / C++ | -0.17 | | source_control / networking | -2.52 / -1.64 |
| Python | **+24.66** | | compilers_and_languages | **+4.69** (saturated despite depth) |
| | | | devops_and_tooling | +4.88 |
| | | | algorithms_and_data_structures | **+16.36** (most saturated) |

Sweet spot: security, networking or systems work in Ruby, Java or Rust. **Do not mislabel a
compiler task as security to game the table.**

**Shortlist row schema** — one line per repo, all fields mandatory:
`slug | licence (+CONFLICT flag) | stars | last commit | real open issues | peer verdict (local+live) |
AI-authorship % (method) | LOC / subsystems | name-free hosting: YES/NO + the entry point | graded-path
seconds, MEASURED | rank | why-not (for rejects)`

## 9a. Two gates that SILENTLY PASS — assert before you measure

`STATUS: LIVE`, both measured 2026-09-23. Each produces a clean-looking result from a check that
never ran, which is worse than a failure because nothing looks wrong.

**① A repo slug that 404s reads CLEAN on every gate.** A screen of `jdbi/jdbi3` — which does not
exist — returned a textbook-clean G1 peer sweep. The real repo, `jdbi/jdbi`, has **its HEAD as a
merged `claude-*` branch**, 12 merged `claude-*` PRs, and **292 commits by "Claude (on behalf of
Steven Schlansker)"**. Every gate would have passed the typo.

```bash
gh api repos/<slug> --jq '.full_name' || { echo "SLUG DOES NOT RESOLVE — stop"; exit 1; }
```
Resolve the slug **first**, and screen the name the API returns, not the one you typed.

**② The churn gate passes paths that do not exist.** A first churn table read `atc/algorithm 0`
and `atc/radar 0`; neither directory is in the repo. A zero from a nonexistent path is
indistinguishable from a genuinely quiet subsystem.

```bash
for d in <target subsystems>; do
  [ -e "$clone/$d" ] || { echo "PATH ABSENT: $d — the gate did not run"; continue; }
  printf '%-40s %s\n' "$d" "$(git -C "$clone" log --since=90.days --oneline -- "$d" | wc -l)"
done
```
**Every churn figure must be accompanied by proof the path exists.** A `0` without it is unmeasured.

## 9b. Two gate corrections from the 2026-09-22 runs

**G2's agentic-artifact check must be CONTENT-based, not presence-based.** `STATUS: LIVE`.
As written, the mere presence of `AGENTS.md` is a hard kill. oxigraph's is an ordinary 49-line
human contribution guide; the shortlist recorded the kill condition and waived it in the same
cell, and a full run was spent on a repo the gate had already killed. Neither the silent waiver
nor the literal kill was right.

| What you find | Verdict |
|---|---|
| `.claude/`, `CLAUDE.md`, `claude-code-action` in CI, or merged `claude/*`\|`codex/*` branches | **KILL** — agentic authorship in the repo's own history |
| `AGENTS.md` that is human-written contributor guidance, no agent artifacts elsewhere | **PASS with a recorded note** — paste the first 15 lines as evidence |
| Ambiguous | `Owner: human`. Do not waive it yourself and do not kill it yourself. |

**Tracker discovery is part of G4, before you count anything.** `STATUS: LIVE`. `gh issue list`
returns zero on a repo whose tracker is JIRA — which reads as "clean" and is really "looked in the
wrong place". santuario read 12 issues and actually had 33, with an OPEN ticket proposing the
remedy for one of our own hypotheses.

```bash
gh api repos/<slug> --jq '{has_issues, homepage}'      # has_issues:false => the tracker is elsewhere
```
Find the real tracker, record which one it is in the HANDOFF, and sweep **that**. `A3` GATE 3
inherits the tracker you name here.

## 10. THE REPO-FINDING CHECKLIST

Run top to bottom, per candidate repo, in this order. Tick each line with the output that proves
it, or waive it with a reason. Steps 1–2 are per lane; 3–15 are per repo. An unticked, unwaived
line means A1 is not complete.

| # | Step | Proof |
|---|---|---|
| 1 | Refresh the dedup corpus | `cd /tmp/llc && git pull` — must be over `ssh://git@github.com:22/...`; record the new HEAD date |
| 2 | Read the peer repo pools for this lane | hit list from `codimango/swe-bench-pro-jayzong:docs/repo-candidates/*` and `codimango/swe-bench-pro-aaitemp:discovery-f/*.json`; mark race-risk repos (signal, not kill) |
| 3 | **G1** live peer sweep, *before cloning* | `gh search code --owner codimango "<repo>" --limit 30` — paste the count **and your reading of each hit**; nonzero exit = UNKNOWN, re-run |
| 4 | **G6** liveness receipt | the four `gh api` / `gh pr list` commands in §6, output pasted. `pushed_at` is not acceptable evidence |
| 5 | **G5** licence | `gh api repos/<slug> --jq .license.spdx_id` **and** `head -5 LICENSE* COPYING*` after clone. Record the string; flag §7 CONFLICT if not MIT/Apache-2.0/BSD/ISC |
| 6 | Full clone — **never `--depth`** | clone path recorded; `git rev-parse HEAD` |
| 7 | **G2** branch + agentic-artifact gate | `git branch -r \| grep -iE 'claude\|codex\|copilot'` count; `ls -d .claude CLAUDE.md AGENTS.md docs/claude 2>/dev/null`; grep CI config for `claude-code-action` |
| 8 | **G3** AI-authorship, corrected method only | the three §4 signals, each with its command output, and the resulting % — **state the method used**; a body-text grep is not an answer |
| 9 | **G4** issue density | open count **minus PRs**, with both numbers shown |
| 10 | Local corpus sweeps | the three §3 commands, hit counts **and hits read**; plus a sweep of the **dependency's org name**; plus a diff against `/home/agvidit/swe-bench-pro-agvidit/*/tests/config.json` |
| 11 | **G7** size | the `LOC=` / `SUB=` commands in §6, values recorded (these go in the HANDOFF; `A2` must not re-measure) |
| 12 | **G8** name-free hosting | one sentence naming the **existing public entry point** a defect would be asserted through — or `NO` |
| 13 | **G9** fixtures [N03] | the path of the in-repo fixture corpus / test app the graded tests would reuse |
| 14 | **G10** harness timing, MEASURED | throwaway-container run: image build s, dep install s, graded-subset s; plus any flags needed (`--network=host`, Maven mirror, `build_timeout_sec`) |
| 15 | Rank and write the shortlist | shortlist file with one §9 row per repo screened, **including rejects and their why-not** |
| 16 | Emit the HANDOFF | block below, `CHECKLIST: n of m` filled in |

```
HANDOFF A1
  EXIT:      <N repos past all gates; paste the G10 timing command output for each>
  CHECKLIST: <n of m ticked; every waived line with its reason>
  ARTIFACTS: <path to the shortlist file>
  FACTS:     per surviving repo — clone path, default branch + HEAD sha, LOC, subsystem count,
             licence string (+ CONFLICT flag), real open-issue count, peer-sweep commands run and
             their hit counts, AI-authorship figure and the method used, the existing public entry
             point that makes a name-free assertion possible, measured graded-path seconds,
             build_timeout_sec needed, any container flags required (e.g. --network=host, Maven mirror)
  OPEN:      licence CONFLICT — UNRESOLVED, Owner: human. Any repo seen in a peer repo pool (race risk).
  NEXT:      A-source/A2-idea-generate.md — one dispatch per surviving repo
```

# friction.md — run `find-repos` (A1 + the four category gates)

Appended as I went. One entry per place the playbook was unclear, missing, wrong,
self-contradictory, or slower than it should have been.

---

## F1 — `EARLIER:` the four category gates belong in `A1` §2's gate table, and the evidence for that is three repos this run

**File:** `A-source/A1-repo-screen.md` §2 (the G1–G10 table).

Three repos passed **every** existing A1 gate and died on a category gate. A1 would have
shortlisted all three, and each would have burned an `A2`/`A3` pair the way the five repos
in the brief did:

| repo | every A1 gate | killed by | the number |
|---|---|---|---|
| `rust-lang/rustup` | G1 0 peers · G2 clean · G3 0.05% (3 doc typos) · G4 393 · G5 Apache-2.0/MIT · G6 today · G7 24.9k/13 · G8 yes · G9 yes | **CAT-4** | `src/cli` **82** commits/90d, `src/dist` **37**, `src/config.rs` **25** |
| `apache/syncope` | G1 0 peers · G2 clean · G3 0/15,857 · G4 **20** (JIRA) · G5 Apache-2.0 · G6 today · G7 328k/131 | **CAT-4** | Francesco Chicchiriccò = **82 of 171** commits/90d = 84% of human commits, in every core module |
| `zalando/postgres-operator` | G1 0 peers · G2 clean · G3 0/3,826 · G5 MIT · G6 today | **CAT-4** (+G4 458, +G7 ~5 pkgs) | **all 44** commits/90d land in `pkg/cluster`(17) `pkg/apis`(15) `pkg/controller`(12) `pkg/util`(11) |

**Where it should live:** a `G11 — subsystem churn` row in §2, run *after* G7 (you need the
subsystem list) and *before* G10 (it is free, G10 is not). One command, with the existence
assertion from F4 attached.

**Time cost:** zero — I had the gate from the brief. Without it, three of my four survivors
would have been wrong, which is the exact 5-for-5 outcome the brief was written about.

---

## F2 — `PINPOINT:` A1 §3 names two peer pools and misses the two that actually kill candidates

**File:** `A-source/A1-repo-screen.md` §3, "Free intel" paragraph (names
`jayzong:docs/repo-candidates/*` and `aaitemp:discovery-f/*.json`).

Two files the section does not name did more work than both pools combined:

```bash
gh api repos/codimango/swe-bench-pro-mohammedram/contents/docs/codimango-used-upstream.txt
  # 1,171 upstream slugs already used as task substrates, harvested 2026-08-25
gh api repos/codimango/weili4-swebench/contents/EXCLUSION-LIST.md
  # 2,217 lines of MEASURED outcomes, not candidates
```

The second is qualitatively different from a candidate pool: it records *why* a repo died
and at what score. It told me `restic` is dead before I ran a single query
(`restic-blob-batch-dedup` → "**5/5 every model, every arm**"), and it carries the same for
`badger`, `go-git` ("killed on prose"), `tile38`, `asynq`, `chroma`, `puma`, `licensed`,
`puppet-lint`. That is the cheapest kill available anywhere in A1 and it is not in the
act-file.

**But it is a positive-only filter, and A1 must say so.** `solidusio/solidus` is **absent**
from the 1,171-slug list and has **≥10 peer tasks**. Absence proves nothing; presence is a
free kill.

**Time cost:** ~4 min to find them, then they saved far more.

---

## F3 — `REPEAT:` I computed "real open issues" three times because A1 §5's subtraction is wrong above 100 open PRs

**File:** `A-source/A1-repo-screen.md` §5 (`open_issues_count` **includes pull requests** —
one curator repo read 134 and had 121 real issues. Subtract before applying the band).

The subtraction is right; the *method* isn't stated, and the obvious one breaks. I first
paged `/pulls?state=open&per_page=100` and read its length — which silently caps at 100.
`runatlantis/atlantis` came out as `917 − 100 = 817` on one attempt and `917 − 167` on
another. The only reliable form is the search API, which counts issues and PRs separately:

```bash
gh api "search/issues?q=repo:<slug>+is:issue+is:open&per_page=1" --jq .total_count   # 750
gh api "search/issues?q=repo:<slug>+is:pr+is:open&per_page=1"    --jq .total_count   # 167
```
Atlantis is a **G4 kill at 750**, and the naive read could have put it anywhere from 750 to
817 — both kills here, but on a repo near the 500 line the method decides the verdict.

**Fix:** paste those two lines into §5.
**Time cost:** ~8 min.

---

## F4 — `PINPOINT:` the churn gate silently passes any path that does not exist

**File:** the brief's CAT-4 gate (`git log --since=90.days --oneline -- <target subsystem>`).
Applies equally wherever A1 grows a G11.

My first concourse churn table read:

```
atc/algorithm   90d=0
atc/radar       90d=0
```
Both look like ideal targets. **Neither directory exists** — the algorithm is at
`atc/scheduler/algorithm`, and `atc/radar` was deleted years ago. `git log -- <path>` on a
nonexistent path exits 0 and prints nothing. A churn gate with no existence assertion
**manufactures its own pass**, and it does so most convincingly for exactly the
subsystem names an agent guesses from memory rather than reads from the tree.

**Fix:** the gate is two commands, never one:
```bash
[ -e "$R/$d" ] || { echo "MISSING $d — NOT a zero-churn result"; continue; }
git -C $R log --since=90.days --oneline -- "$d" | wc -l
```
**Time cost:** ~6 min, and it would have been a false survivor if I had not checked.

---

## F5 — the two-sweep rule fired in **both** directions inside one run

**File:** `A-source/A1-repo-screen.md` §3 ("Two sweeps are required — local corpus AND live
search. Neither alone is sufficient.") — `STATUS: LIVE`, and now with a fresh instance each way.

- **Local caught what live missed.** `gh search code --owner codimango "sigs.k8s.io/kustomize"`
  returned `pratyusha-mandapati/generate_resourceQuota_files` and nothing else on kustomize
  itself. `grep -rli kustomize /tmp/llc/tmp/tasks` returned
  `swe-bench-pro-evyatarh/kustomize-annotationselector` — a second peer, on **patch
  selection via `annotationSelector`**, one of the two surfaces I would have targeted. The
  live sweep missed it because the task's text never names the slug.
- **Live caught what local missed.** `wal-g/wal-g`, `apache/cayenne`, `crossplane`,
  `cloudnative-pg` were all 0/0 locally; the *live* sweep is what surfaced the discovery
  pools and race signals, and it is what proved `jdbi` was the wrong slug (F6).

Nothing to fix. Logging it because the rule is stated as a principle and this is the first
run I know of where one execution produced a measured instance of each direction.

---

## F6 — `WASTE:` A1 §10 sweeps before it validates the slug, so a nonexistent repo reads clean

**File:** `A-source/A1-repo-screen.md` §10, step 3 ("G1 live peer sweep, *before cloning*")
vs step 6 (full clone) — nothing between them checks the slug resolves.

I swept `jdbi/jdbi3`. It returned **1 hit**, a vendored `.pom` in an HBase task — a textbook
clean G1. The repo does not exist; the slug is `jdbi/jdbi`. I only found out at step 4 when
`gh api repos/jdbi/jdbi3` returned 404, after the clone had already been queued.

Worse, the real repo is a **G2 hard kill**: HEAD is literally
`Merge remote-tracking branch 'origin/claude-bind-list-values-1550'`, with 12 merged
`claude-*` PR branches and 292 commits authored by
`Claude (on behalf of Steven Schlansker)`. A clean-looking sweep on a typo'd slug sat one
step away from shortlisting one of the most AI-authored repos I screened.

**Fix:** step 3 becomes `gh api repos/<slug> --jq .full_name` **then** the sweep — one call,
and it is the same call step 4 needs anyway. A1 §3 already says "renamed repos have returned
422 that loose scripts consumed as clean"; this is the same failure with a 404.
**Time cost:** ~3 min plus one wasted clone.

---

## F7 — `EARLIER:` A1 §4's corrected method is right, but its **percentage bar** is the weakest of its three signals

**File:** `A-source/A1-repo-screen.md` §4 ("Bar: **above ~25% AI-attributed, reject**").

`jdbi/jdbi` measures **292 / 6,550 = 4.5%** by identity. Under the stated bar it **passes**.
It is one of the most thoroughly agent-maintained repos in this screen. What killed it was
signal 2 (merged `claude/*` branches — 12 of them), not signal 1's ratio.

Conversely, signal 1 fired three false positives that only a *read* disarmed, in one run:
- `wal-g`: 1 hit → `devinturner` (a human whose username contains "devin")
- `cloudnative-pg`: 5 hits → `Devin Buhl` ×4, `Devin Nemec` ×1 (humans)
- `rustup`: 3 hits → genuinely `Codex <codex@openai.com>`, but all three are **doc typo
  fixes** (`www/rustup.css`, a README, a `.md`) touching zero source

So the ratio is (a) not sufficient to kill and (b) not sufficient to clear.

**Fix:** §4 should say the three signals are **disjunctive kills, not averaged**:
*any* merged agentic branch is a kill regardless of ratio; the ratio alone only kills above
~25%; and every identity hit must be printed with `%an <%ae>` and read before it counts.
**Time cost:** ~10 min of reading commits, all of it necessary.

---

## F8 — `PINPOINT:` G10's container recipe breaks on any Go repo with a `go.work`

**File:** `A-source/A1-repo-screen.md` §8 / §10 step 14.

My first kustomize G10 produced `BUILD_SEC=0 GRADED_SEC=0` and exit 0 — a clean-looking
zero. The actual output was:

```
go: -mod may only be set to readonly or vendor when in workspace mode, but it is set to "mod"
	Remove the -mod flag to use the default readonly value, or set GOWORK=off to disable workspace mode.
```

`GOFLAGS=-mod=mod` is the conventional offline-test flag and is **fatal** in a multi-module
Go workspace. Note the failure mode: a timing harness that does not assert on the test
output reports `0s` and calls it fast.

**Fix:** §8 should carry the Go recipe explicitly — `--network=host`, `GOTOOLCHAIN=local`,
and `GOPROXY=off GOWORK=off` for the offline re-run — and §10 step 14 should require the
`ok`/`FAIL` lines in the receipt, not just the seconds.
**Time cost:** ~4 min and one wasted container run.

---

## F9 — `PINPOINT:` G9 [N03] has no threshold, so I had to invent one to separate a PASS from a KILL

**File:** `A-source/A1-repo-screen.md` §6, G9 ("the only gradeable fixtures would be
hand-built stubs [N03]").

Two repos in this run have **zero** `testdata/` or `fixtures/` directories:

| repo | verdict | what separated them |
|---|---|---|
| `crossplane/crossplane` | **PASS** | 121 test files / 268 source = **45.1%**; `composite/reconciler_test.go` is **1,830 lines** of table-driven cases, `composition_functions_test.go` **2,299** — a reusable substrate that happens not to live in a directory |
| `apache/guacamole-client` | **KILL** | 19 test files / 833 source = **2.3%**; **0** tests in `guacamole-auth-jdbc` (197 sources), the module I would have targeted |

"Would the fixtures be hand-built stubs" is a judgement. The **test-file-to-source ratio**
plus "does the target package have any test at all" is a measurement, and it separates
these two cleanly. For reference the other three survivors: concourse 63.3%, kustomize
70.2%, cloudnative-pg 74.6%.

**Fix:** G9 gets a stated floor (I would put it near 20%, with a hard kill on *zero tests in
the target package*) and an explicit note that in-code table-driven tests satisfy N03 —
absence of a `testdata/` directory is not the criterion.

---

## F10 — `WASTE:` I ran a Java G10 on a repo that a 2-second G9 check would have killed first

**File:** `A-source/A1-repo-screen.md` §2 gate order (G9 then G10) vs §10 step order
(13 then 14) — the order is already correct on paper; I ran them concurrently to save time
and lost time instead.

For `apache/guacamole-client` I pulled `maven:3-eclipse-temurin-17` (~45s), wrote a GCS-mirror
`settings.xml`, ran `mvn -pl guacamole-ext,guacamole-common -am install` (43s, succeeded),
then `mvn -o -pl guacamole-ext test` → `Tests run: 0` → `BUILD FAILURE`. Two container runs,
~2.5 minutes, no number produced. The reason was F9's 2.3% density, which costs:

```bash
find . -path '*/src/test/java/*' -name '*.java' | wc -l    # 19
find . -path '*/src/main/java/*' -name '*.java' | wc -l    # 833
```

**Fix:** §10 should say G9 is a **hard prerequisite** for G10, not merely the preceding step
— "do not spend a container on a repo whose target package has no tests". The Maven recipe
itself worked exactly as A1 §8 describes (GCS mirror + `--network=host`, install in 43s), so
the recipe is fine; the sequencing was mine.

---

## F11 — `EARLIER:` `hasIssues: false` is the free tell that a JIRA sweep is required, and A1 never mentions it

**File:** `A-source/A1-repo-screen.md` §5 (issue density) — the brief warned me about
JIRA-only repos; the act-file does not.

The GitHub API hands you the answer for free in the call you are already making:

```bash
$ gh api repos/apache/cayenne --jq '{hasIssues:.has_issues, openIssuesIncPR:.open_issues_count}'
{"hasIssues":false,"openIssuesIncPR":28}          # <-- 28 is meaningless
$ curl -s -G 'https://issues.apache.org/jira/rest/api/2/search' \
    --data-urlencode 'jql=project=CAY AND status in (Open,"In Progress",Reopened)' \
    --data-urlencode 'maxResults=0' | jq .total
441                                                # <-- the real number, 16x
```
Same shape for `GUACAMOLE` (**468**), `SYNCOPE` (**20**), `POOL` (**23**). The 28→441 gap
moves cayenne from "pristine tracker" into the 150–500 band; the 20 on Syncope is a genuine
green light that GitHub would have shown as zero.

**Fix:** §5 gains one line — *"if `has_issues` is false the tracker is elsewhere; find it and
sweep it. `open_issues_count` on such a repo counts PRs only and is never the issue count."*
— plus the `jql` one-liner.

---

## F12 — "0 peers is a warning, not a green light" is now measured, and the direction is worse than the rule implies

**File:** `A-source/A1-repo-screen.md` §3 ("**Zero peers is NOT clean** … Ask *why* nobody
mined it"), currently evidenced by `vortex-data/vortex`.

Six repos in this run returned **0 peer tasks under both sweeps**. Four of them died anyway:

| repo | 0 peers | died at |
|---|---|---|
| `wal-g/wal-g` | yes | **G2** — 3 closed-unmerged `copilot/*` branches |
| `rust-lang/rustup` | yes | **CAT-4** — 82 commits/90d in `src/cli` |
| `apache/syncope` | yes | **CAT-4** — 84% of human commits are one person |
| `zalando/postgres-operator` | yes | **CAT-4 + G4 458 + G7** |
| `crossplane/crossplane` | yes | **survived** |
| `cloudnative-pg/cloudnative-pg` | yes | **survived** |

So in this sample "0 peers" was **67% a warning and 33% an opportunity**, and in every one of
the four failures the answer to "why did nobody mine it" was a real property of the repo, not
an oversight. §3's framing ("ask why") is right; what it should add is that the answer is
usually **G2 or churn**, so those two gates should run immediately on any 0-peer repo rather
than in their normal order.

---

## F13 — `WASTE:` peer density made 26 of 36 screens redundant, and the pattern is predictable enough to pre-filter

Not a playbook defect so much as an economics observation worth writing down. Of the 36
repos I screened, **26 died at G1**, and the survivors cluster hard:

| star band | screened | G1 survivors |
|---|---:|---:|
| >20k | 2 | 0 |
| 5k–20k | 19 | 4 |
| <5k | 15 | 6 |

Every repo I picked for being *well known in its domain* (helm, alertmanager, asynq, grape,
solidus, fluentd, sea-orm, nats-server, chrono, h2database, rqlite, liquibase) was taken,
most by 5–12 distinct authors. The four survivors are all **Go infrastructure with a narrow
audience** — a CI engine, a control-plane framework, a database operator, a manifest builder.
A1 §9's star band ("prefer **5k–15k**") is `STATUS: SCOPED-TO PEER's JS lanes`, and on this
evidence it points at the most-mined band in the corpus. Worth a note in §9 that the band is
a *popularity* heuristic and peer density inverts it.

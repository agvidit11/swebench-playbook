# friction.md — e2e run 20260922T221320Z

One entry per place the playbook was unclear, missing, wrong, self-contradictory, or slower
than it should have been. Appended live as the run proceeds.

---

## F1 — A1 §10 step 1 vs ROUTER §6: shared git index in a fan-out act
**Files:** `A-source/A1-repo-screen.md:253` ("Steps 1–2 are per lane", step 1 = `cd /tmp/llc && git pull`)
vs `00-ROUTER.md:148` (`shared git index` listed as **Serial-only**).
**Problem:** A1 is the canonical fan-out act (router §6 row 1: "N agents in parallel"). But its own
checklist makes every lane run `git pull` against the single shared clone `/tmp/llc`. Three lanes
pulling one working copy concurrently is exactly the serial-only case the router forbids.
**Cost:** ~3 min deciding. **Workaround:** pulled once centrally, told the lanes step 1 is done.
**Fix:** A1 §10 should mark steps 1–2 "run ONCE per run by the coordinator, before fan-out", not "per lane".

## F2 — A1 §3 claims corpus is "16 days behind"; it is now 20 and `git pull` cannot fix it
**File:** `A-source/A1-repo-screen.md:44,51`
**Evidence:**
```
$ cd /tmp/llc && git pull
Already up to date.
$ git log -1 --format='%H %ci'
d8472c4c54ec0dcf9f2a951f1ab77b840f1aa308 2026-09-02 15:17:05 -0400
```
Run date 2026-09-22 → **20 days stale**, and the pull is a no-op because upstream itself has not
moved. The playbook tells you to refresh the corpus as if that removes the staleness; it does not.
**Fix:** step 1's proof should be "record the HEAD date **and the resulting staleness in days**", and
§3 should state that a local-corpus miss on a task authored inside the staleness window is UNKNOWN,
never clean. Right now only `gh search code` covers that window and it is listed as gate 4 of 4.

## F3 — A1 §10 step 14 (G10) is Docker work inside an act the router fans out N-wide
**Files:** `A-source/A1-repo-screen.md:266` ("throwaway-container run") vs `00-ROUTER.md:145,162`
("anything spawning Docker" = serial-only; `A1` across N territories = "N agents in parallel").
**Problem:** G10 is A1's **exit gate** (`A1:36` "a shortlist row without a measured number is not a
shortlist row"). So every parallel lane must run Docker to finish, in an act the router parallelises.
The two rules cannot both be obeyed.
**Cost:** ~5 min; forced a deviation.
**Deviation taken:** lanes run G1–G9 in parallel and measure natively where the host toolchain exists;
G10 container runs are queued serially through the coordinator for finalists only.
**Fix:** either split A1 into `A1a` (parallel, G1–G9) and `A1b` (serial, G10), or state the deviation
in §2 as the sanctioned shape.

## F4 — A1 §8 host-toolchain inventory is asserted, not verifiable from the playbook
**File:** `A-source/A1-repo-screen.md:212`
"wave-2 inventory: Java, Maven, GCC, CMake, Go, Python present; **Ruby and Cargo absent**."
No command is given to re-verify, and the line says host toolchain is "host-specific — verify it" in
the same row. A one-line `for b in ...; do command -v $b; done` receipt would make it self-checking.

## F5 — `instruction-lint.py` shipped STALE relative to rule D1, and B2's exit condition depended on it
**Files:** `~/.claude/skills/swebench-mt/instruction-lint.py` (the tool) gating
`B-build/B2-contract.md` (whose exit condition is "instruction-lint clean").
**Reported by the coordinator mid-run, 2026-09-22, before this run reached B2.**
**Problem:** the shipped lint enforced an *absolute* never-name rule and hard-FAILed on **any**
symbol absent at `base_commit`. D1 says the opposite for one specific case: a new name that the
graded tests pin **must** be named in the contract. So for any task whose grader pins a new symbol,
B2's stated exit condition was **unreachable** — the act could never legally complete.
**Severity: high.** This is the worst class of playbook defect in this run: an act's exit condition
delegated to an external tool that the playbook does not version, pin, or self-test, and which had
silently drifted out of agreement with the rule the act is supposed to enforce. Nothing in `B2`,
`00-ROUTER.md` §4 or `ledger/RULES.md` would have told me the tool was wrong; I would have read a
FAIL as *my* contract being wrong and sent Avocado in the wrong direction.
**Fixed in place** by the coordinator; the corrected tool is three-way and checks both directions:
- absent at base + pinned by graded tests + named in contract -> OK (D1 requires it)
- absent at base + NOT pinned by tests + named in contract -> FAIL (gratuitous leak)
- absent at base + pinned by graded tests + contract SILENT -> FAIL (the illegal configuration;
  produced `BAD_GRADING_WRONG` on 4 of 4 peer tasks)
**Consequence for sequencing, which B2 does not state:** the fixed lint reads each step's
`test_patch` out of `tests/config.json` to learn what the grader pins. That file does not exist until
**B3**. So at B2 the lint can only run its leak half and prints WARN. **It must be re-run after B3**
to get the second direction. `B2` currently presents "instruction-lint clean" as a one-shot exit
condition; it is really a two-phase check straddling B2 and B3.
**Fix:** (a) `B2` should say its lint run is partial and name the post-B3 re-run as a required step,
and `B3`'s checklist should carry that re-run line; (b) the playbook should pin/check the tool
version — an exit condition that depends on an unpinned external script is not an exit condition.
**ACTION TAKEN THIS RUN:** will run the fixed lint at B2 (expecting WARN) and again after B3.

## F6 — `REPEAT:` A1 §1's "do not accept a pre-screen" does not name the case it will actually hit: a LANE report
**File:** `A-source/A1-repo-screen.md:14` — "Do not accept any pre-screen, including this brief's own
repo list. Coordinator screens were wrong **4 times out of 4**."
**Problem:** the rule is written as *coordinator lies to lane*. In the router's own §6 fan-out shape
the dominant flow is the reverse — **lane reports to coordinator** — and A1 never says the coordinator
must re-verify what a lane hands up. I re-verified `go-acme/lego` anyway, and it mattered:

```
GO lane reported:  "local: 0 direct"
$ cd /tmp/llc && grep -rliF -- "go-acme/lego" tmp/tasks
tmp/tasks/swe-bench-pro-abhkum/upgrade-tlsfs-library__steps__step1_modernize-build-stack.md
tmp/tasks/swe-bench-pro-abhkum/upgrade-tlsfs-library__steps__step2_acme-v2-http01.md
count: 2
```
Both hits are real, both readable, and reading them produced **four carried subsystem exclusions**
for A2 that would otherwise have been discovered at A3 or later. Not a repo kill — but the lane's
"0" would have sent A2 straight at `certificate.Obtain`/HTTP-01, which a peer 2-step MT task already
grades through lego's own API.
**Cost:** ~12 min re-doing a sweep A1 says was already done.
**Fix:** A1 §1 should read "Do not accept any pre-screen — a coordinator brief's repo list, **or a
lane's returned shortlist**. The coordinator re-runs G1 and G2 on the repo it selects." And §10 line
10's proof column says "hit counts **and hits read**" — the lane produced counts. Make the proof
literally require the one-line reading of each non-homograph hit.

## F7 — `EARLIER:` the peer repo pool A1 §3 tells you to trust was 3 weeks stale, and nothing says to spot-check it
**File:** `A-source/A1-repo-screen.md:74` — "**Free intel** — other authors publish their repo pools
… **Read them before screening a lane.**"
**Evidence:** the pool row for the repo I selected
(`swebench-candidates-go-rust-java-security_and_privacy-20260901.md`) says:
`| go-acme/lego | Go | 92.8k (766f) | MIT | ...`
Measured at `base_commit 58468399` on 2026-09-22:
```
$ LOC=... ; SUB=...                      # A1 §6 commands verbatim
LOC=111352  SUB=262
$ go test ./certificate/...
ok  github.com/go-acme/lego/v5/certificate   0.438s     <-- /v5, not /v4
```
The pool is wrong on the **major version** and ~20% low on LOC. The v4→v5 error is the dangerous one:
`B1` and `B3` would have written v4 import paths and failed to compile.
**A cheap check at A1 step 2 would have caught it:** *"before using any pool row, re-derive ONE field
from it (module path or LOC) against the live repo. If that field is wrong, treat the whole row as
lead-only."* Costs 10 seconds. Belongs in §10 line 2's proof column.
**`EARLIER:`** this would otherwise have surfaced at **B3/B4 as a compile error**, three acts later.

## F8 — A1's exit condition is ">=3 repos" and the playbook gives no guidance for landing on 1
**File:** `A-source/A1-repo-screen.md:8` — "**Exit** | **>=3 repos past every gate below** … or an
evidenced 'lane is dead'."
**Problem:** the act offers exactly two outcomes, >=3 or dead. It has no third branch for "1 or 2
strong repos, evidenced" — which is what actually happened, and which is obviously enough to proceed
(A2 dispatches one agent per repo; one repo is a valid input). Router §8 says an act that cannot meet
its exit emits `EXIT: NOT MET` and "does not improvise forward" — read literally that would end this
run on a repo that passed every single gate with a 12s measured graded path.
**Cost:** ~8 min of deciding whether I was allowed to continue.
**Fix:** state the middle branch. Suggested: ">=3 is the target because A2/A3 kill most candidates;
1–2 is a valid PROCEED with the smaller cushion recorded in the HANDOFF; 0 is dead." Also reconcile
with router §8's "does not improvise forward", which currently reads as absolute.

## F9 — the Docker mutex has no protocol anywhere in the playbook, and the one on disk is unreadable
**Files:** `00-ROUTER.md:145,164` mandate Docker-serial across `A1`, `B4`, `B5`, `C2`–`C6` but define
**no lock, no path, no convention, no staleness rule, no way to identify the holder.**
**What happened:** `/tmp/swebench-docker.lock` already existed when I tried to take it —
```
$ ls -la /tmp/swebench-docker.lock
-rw-r--r-- 1 agvidit users 0 Sep 22 15:18 /tmp/swebench-docker.lock     <-- size 0
$ docker ps --format '{{.Names}} | {{.Status}}'
magical_easley                                   | Up 7 seconds
ruby-terraform-plan-model-empty__bqrhh2b-main-1  | Up About a minute
smoltcp-probe                                    | Up 4 days
```
Size **zero** — so I cannot tell who holds it, since when, for which act, or whether it is stale. My
own `if [ -e "$LOCK" ]` guard fired correctly and my G10 run aborted with exit 1. There is genuinely
another live session running task containers, so honouring it was right — but I honoured it by luck
of having invented a compatible convention, not because the playbook told me one.
**Cost:** killed G10 for 3 of 8 survivors; A1 exits PARTIAL because of it.
**Fix:** router §6 should specify the mutex concretely — path, `flock` not `-e`, mandatory contents
(`<run-id> <act> <task> <ISO8601>`), a staleness TTL, and "a zero-byte lock is stale after N minutes".
Cross-reference: this run's memory already records a `flock+TTL` patch for the Harbor metacode pull
race; the same treatment is needed here.

## F10 — `WASTE:` A1 §8's host-toolchain claim cost a Java lane most of its budget
**File:** `A-source/A1-repo-screen.md:212` — "wave-2 inventory: Java, Maven, GCC, CMake, Go, Python
present; Ruby and Cargo absent."
"Java present" is true and useless. It is **JDK 8 only**:
```
$ java -version   -> openjdk version "1.8.0_502"   (/usr/local/fbprojects/.../impl/8)
$ ls /usr/lib/jvm -> (does not exist)   $ echo $JAVA_HOME -> (empty)
```
Every modern Java security library needs 17+. The JV lane cloned and gated **12 repos** and could not
measure G10 on a single one:
```
[ERROR] Rule 1: RequireJavaVersion failed: Detected JDK ... 1.8.0-502 ... not in the allowed range [17,).
[ERROR] formatter-maven-plugin ... class file version 61.0 ... only recognizes up to 52.0
jit-groups/sources/pom.xml:   <maven.compiler.target>25</maven.compiler.target>
```
**Cost: an entire lane's G10, ~20 min.** Knowable in 5 seconds before dispatch.
**Fix:** §8's row should carry the *version*, not the binary name, and §10 line 14's proof should
begin "state the toolchain version the repo requires and the one the host has, before measuring."

## F11 — `EARLIER:` the disclosure/roadmap sweep is the check A2 most needs and is NOT a checklist line anywhere
**Files:** `A-source/A2-idea-generate.md:276` (checklist line 5 = admissions grep **only**);
`A-source/A1-repo-screen.md:104-117` (§5 warns about it in prose, at the wrong act);
`reference/R6-fork-patterns.md:66-83` ("THE NOVELTY GATE HAS NO FEATURE-SIDE ARM", with the exact
four commands) — which A2 §1 links **only as the A-shape library**, so nothing tells an A2 runner
to read that section.
**What happened.** A2 line 5 had me grep lego's own admissions. It returned exactly three, and the
most attractive one was:
```
certificate/renewal.go:54
// TODO: Otherwise, if the selected time is before the next time that the client would
//       wake up normally, attempt renewal immediately.
```
A2 §3 rule 2 calls an in-code admission "the strongest premise receipt there is", so on A2's own
instructions this is the best premise in the repo. It is **disclosed**: `gh issue list` returns
`#3192 Add certificates ari command to query RFC 9773 renewal information` and
`#2517 Store ARI info on persistent storage and follow Retry-After header`, both OPEN.
Separately the repo carries an open **roadmap issue #2798 "Roadmap v5"** whose ~40 ticked boxes
disclose account key rollover, key-type-per-certificate, dns-persist-01, the slog logger, context
plumbing and the entire CLI config rework.
**Cost:** I ran the sweep only because I had read R6 for the A-shape and happened to hit its
feature-side section. An A2 runner following the checklist literally would not have. It cost me
~10 min; not doing it would have cost a card and probably a repair round.
**This also breaks the README's own "no rule appears in two files" rule** — the disclosure rule is
stated in A1 §5 prose and again in R6, and is a checklist line in neither.
**Fix:** add to A2 §8 as a new line 5b, with R6's commands inline:
```bash
gh api "search/issues?q=repo:<slug>+label:feature+state:open" --jq '.items[].title'
gh api "search/issues?q=repo:<slug>+roadmap+in:title" --jq '.items[]|"\(.number) \(.title)"'
gh issue list -R <slug> --state open --limit 100 --json number,title
ls <clone>/{ROADMAP*,docs/roadmap*} 2>/dev/null ; git -C <clone> branch -r | grep -iE "feat|feature"
```
Proof column: "the open-issue title list, and a line per admission saying disclosed / not disclosed."

## F12 — `A2 §1 contradicts itself`: three layers required, one of them quarantined
**File:** `A-source/A2-idea-generate.md:23-31`
The table lists three layers — C (`R5`), A (`R6`), B (`R7`) — and line 25 says "**a strong candidate
has one from each layer**". But the B row on line 31 reads
"`→ reference/R7-algo-catalogue.md` — **QUARANTINED**, do not source from it".
So the stated definition of a strong candidate is unreachable by construction. The worked example on
line 35 silently handles this with "*(B layer omitted — quarantined)*", which is the right answer —
but it appears only inside an example, not in the rule.
**Cost:** ~4 min re-reading to be sure I was allowed to compose only C x A.
**Fix:** change line 25 to "a strong candidate has one from each **live** layer (C and A; B is
quarantined — `→ ledger/RULES.md`)". Minor, but this is the first substantive instruction in the act.

## F13 — dangling references out of the playbook into an un-versioned directory
**Files:** `reference/R6-fork-patterns.md:42` → `/home/agvidit/swebench/SEARCH-AXES.md`;
`R6:550` → `/home/agvidit/swebench/ALGO-CATALOGUE.md`; `R6:270` → `01-sourcing.md` (no such file in
the playbook); `A1:70` → `/home/agvidit/swe-bench-pro-agvidit/*/tests/config.json`.
The first two are the *full text* of libraries the playbook only summarises, and they live outside
the repo, so the playbook is not self-contained and cannot be handed to someone else as-is. `R5`
**is** in the playbook and is the same content as `SEARCH-AXES.md`, so `R6:42`'s pointer is also
simply wrong — it should say `→ reference/R5-search-axes.md`.
**Fix:** repoint `R6:42` at `R5`; either vendor `ALGO-CATALOGUE.md` into `reference/` or mark it
explicitly as an out-of-tree research artifact; delete or repoint the `01-sourcing.md` reference,
which is a leftover from a pre-merge pipeline.

## F14 — `PINPOINT:` the handoff can carry a subsystem count that means the opposite of what A2 reads it as
**Files:** `A1:156` ("Carry `LOC` and `SUB` into the HANDOFF — `A2` sizes its survey from them and
**must not re-measure**") and `A2:55` ("If LOC and subsystem count disagree badly, **trust the
subsystem count**").
**Problem:** A1's `SUB` command counts leaf directories containing source files. For lego that
returns **262** against 111k LOC — a ratio that reads as "unusually rich, many independent
subsystems". It is the opposite: ~150 of the 262 are one-file-each DNS-provider directories, i.e.
**fan-out, not diversity**, and per-provider work is a banned premise shape (A2 §6 / the
`expose_interface` 1-passed-13-failed record). The real count of distinct engineering subsystems is
about 12. An A2 runner obeying "do not re-measure" and "trust the subsystem count" would size the
survey off a number that points the wrong way.
**I caught it only because A1's own rejects mention the identical trap on another repo** (the RS
lane independently re-derived it on nmstate's 22-member `InterfaceType` enum).
**This is the R8 gap:** I had a symptom — "262 subsystems but the repo is really one client library"
— and no file told me which artifact owned the discrepancy or how to record it.
**Fix:** A1's shortlist row and HANDOFF should carry **`SUB` split into `SUB_distinct` and
`SUB_fanout`**, with a one-line note naming the fan-out axis if there is one; and A2 §2's
cross-check should read "trust `SUB_distinct`". Cheap: it is one extra sentence from whoever already
looked at the tree.

## F15 — **the 600-byte banner threshold in A2 §3 does not catch the failure it exists to catch**
**File:** `A-source/A2-idea-generate.md:105-106`
> "**Tooling — all of these fail with exit 0. Always check output size; ~200 bytes + exit 0 is a
> banner, not an answer.**"
and `A2:278` checklist line 7 proof: "**check the output byte size**; <600 bytes is a silent
failure, re-run".
**What actually came back** from the first `mc.sh` dispatch — exit 0, **930 bytes**, i.e. it passes
the playbook's stated gate:
```
MetaCode at Meta (https://fburl.com/metacode)
Using AI Gateway (Meta Model API upstream)
[metacode] using AI inference gateway (Model API): https://metacode-modelapi...
Warning: Failed to mount .arcrc: ... ENOENT: No such file or directory
WARNING: 11 skill(s) in /home/agvidit/.claude/ not available for MetaCode.
MetaCode reads skills from ~/.agents/skills/ and .metacode/skills/, not from .claude/.
Run `metacode migrate-from-claude` ...

Generating your 18 cascade surfaces — surveying lego for closed extension points.
Your 18-surface derivation is underway — I'm verifying the live admission and scanning subsystems for dispatch sites.
```
**The banner has grown.** The environment now emits ~700 bytes of gateway + arcrc + skills-migration
warnings *before* the model says anything, so the signal is ~200 bytes of filler riding on 730 bytes
of noise, and a byte-count gate cannot separate them. `mc.sh` itself only warns under 600.
**Fix:** replace the byte-count gate with a **content** gate. The output must contain a required
structural token from the ask — here, the literal string `SURFACE TABLE` (or a `| id |` header row).
Concretely, in `mc.sh` and in A2 line 7's proof column:
`grep -q '<required-token>' "$OUT" || echo "mc.sh: FAILED — no <required-token> in output"`.
A byte count is a proxy; the token is the thing.

## F16 — the prompt-size ceiling A2 §3 documents for Codex applies to `mc.sh` too, and is not stated there
**File:** `A-source/A2-idea-generate.md:120-122`
> "Keep **Codex's** inline prompt ~2 KB with the payload in a file: a 46 KB prompt returned only its
> opening plan. Give MetaCode 1700s via the backgrounded pty wrapper; the Bash tool caps at 600s."
The paragraph gives MetaCode a *time* budget and gives Codex a *size* budget, which reads as "size is
a Codex problem". It is not. My `survey.txt` was **21,221 bytes** — under half the 46 KB that broke
Codex — and MetaCode returned **exactly the documented symptom: only its opening plan**
("Your 18-surface derivation is underway"), then exited 0 at 1700s-far-under.
**Cost:** one full dispatch cycle, ~4 minutes wall clock plus the re-write.
**Fix:** state the size ceiling once, for both tools, as its own rule: "**Any single dispatch prompt
over ~8 KB risks returning only a plan. Split the ask into passes.**" And A2 §2 already tells you to
run the survey "in subsystem passes" — §3 should connect the two: passes are not only for survey
quality, they are how you stay under the prompt ceiling.

## F17 — `EARLIER:` **`git log -L` on the target function is the single highest-value check in the whole run, and it appears in no act-file**
**Files:** `A-source/A3-idea-gate.md:123` has only the FILE-level form —
`git log --oneline --all -- <target-files>`. `A-source/A2-idea-generate.md` has no history check at
all. Neither has the FUNCTION-level form.
**What happened.** Card 2 cleared, in order: A2's admissions grep; my roadmap sweep (#2798); a
13-issue disclosure sweep; GATE 0 (14/14 tokens IN-BASE — a perfect score); GATE 1; GATE 2 by
executed reproduction. It was the strongest candidate of the round by a distance. Then one command
killed half of it:
```
$ git log --format='%h %ci %s' -L '/func hasPreferredChain/,/^}/:certificate/certificates.go'
1d24006e 2021-01-28 fix: preferred chain only match root name (#1334)
30e4987f 2020-09-02 Add preferred-chain option to support "alternate" certificate links (#1227)
42941cce 2018-12-06 Refactor the core of the lib (#700)

$ git show 1d24006e -- certificate/certificates.go
-	for _, cert := range certs {
-		if cert.Issuer.CommonName == preferredChain {
-			return true, nil
-		}
+	topCert := certs[len(certs)-1]
+
+	if topCert.Issuer.CommonName == preferredChain {
+		return true, nil
```
Card 2's step 1 was "match `preferredChain` against **every** certificate in the bundle, not the
top one". That is **character-for-character the code merged PR #1334 deliberately deleted**, after
public reasoning in issue #1333 that mirrors `certbot/certbot#8596`. The oracle patch would have
been a revert of a merged upstream PR — the worst sourcing outcome the playbook has a rule against.
**Why the file-level form would NOT have caught it.** I ran it. It returns 12 commits of unrelated
churn (`add UseARICertID`, `Punycode encoding`, `add EnableCommonName`, `improve logs`…) with
nothing pointing at the 60-line function in a 700-line file. The signal only appears when the
history is scoped to the function.
**Why the issue sweep did not catch it either.** #1333 and #1334 are **closed**, and A3 GATE 3's
enumerated kills are "merged PR", "closed-unmerged PR", "**open** issue". A closed issue whose
remedy shipped is in the spirit of the rule and outside its letter.
**Cost:** it did not cost me time — it *saved* the run from scaffolding a revert. But it was luck
that I ran it; nothing told me to.
**Fix — cheap, mechanical, and it belongs in TWO places:**
- `A2` §8, new checklist line: "for every function the card proposes to change, run
  `git log -L '/func <name>/,/^}/:<file>'` and paste it. If a merged PR deliberately created the
  current behaviour, the premise is dead — do not write the card."
- `A3` GATE 3: replace the file-level `git log --oneline --all -- <target-files>` with the
  function-scoped `-L` form, and add "a CLOSED issue whose remedy was merged" to the kill list
  alongside the three that are already there.
This is the best single shift-left available from this run.

## F18 — A3 GATE 3's kill list has a hole: the closed-issue-with-merged-remedy case
**File:** `A-source/A3-idea-gate.md:120`
The enumerated hard kills are: any **merged** public PR touching the surface; any
**closed-unmerged** PR whose diff or thread contains the remedy; any **open** issue whose body or
comments propose the direction. Issue **#1333** is a CLOSED issue containing (a) a full public
analysis of the matching semantics and (b) a user proposing, and a maintainer answering, exactly the
observability remedy the card proposed. It is training-data exposure by every argument the paragraph
itself makes ("even informally, even with no code"), and it is outside the enumerated list.
It was reachable only because I read it — `gh api search/issues` returned it with `total_count=3`
under the phrase query `preferred+chain+not+matched`, and A3 does mandate reading the hits.
**Fix:** add a fourth bullet — "any CLOSED issue whose proposed direction was subsequently merged;
the merge makes the direction public and the closure hides it from an open-issue filter."

## F19 — `WASTE:` A3 GATE 0 scored the doomed candidate 14/14 and the sound one 0/3
**File:** `A-source/A3-idea-gate.md:28-40`
GATE 0 is first because it is free, and it did exactly what it says: it killed Card 1 in one grep
pass (3 coined tokens) and passed Card 2 with a perfect 14/14 IN-BASE. But the ordering means the
act spends its free gates in the wrong order **for this failure mode**: Card 2 then consumed GATE 1,
a written Go reproduction under GATE 2 (~20 min of real work), and six GATE 3 queries before the
one-line `git log -L` killed it. Meanwhile Card 1 — killed at GATE 0 for coining three symbols — had
a premise that is, as far as any of my sweeps can tell, genuinely undisclosed.
**Not arguing GATE 0 should move.** Arguing that the **function-history check from F17 is also free**
and therefore belongs at GATE 0/1, above the executed reproduction. Suggested order:
`GATE 0 namability -> GATE 0b function-history -> GATE 1 pre-filters -> GATE 2 reproduction`.
That single reordering would have saved the whole GATE 2 build.

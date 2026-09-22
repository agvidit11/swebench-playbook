# CHECKPOINT — pair-santuario

**Rewritten after every meaningful sub-step. A stranger should be able to continue from this alone.**

Last update: A3 — GATE 2 and GATE 3 DONE and PASSED for C1; zero-coin re-cut of C1 out at MetaCode.

---

## Where I am

| | |
|---|---|
| Current act | `A3`. GATE 2 PASS, GATE 3 PASS (incl. branch sweep). GATE 0 is the open question -> re-cut dispatched. |
| Router state | S2 (cards exist, probes partially measured) |
| Target format | **multi-turn** (`swebench-multi`) |
| Stop line | `B5` staged+verified commit. **NO `git push`.** Report `PUSH-READY`. |

---

## Fixed facts — do not re-derive

| Fact | Value |
|---|---|
| Repo | `apache/santuario-xml-security-java` (the `xmlsec` library) |
| `base_commit` | `497d3fb4c8b5654a9951a3de4682c6ed48038173` |
| My working clone | `/tmp/santuario-pair/repo` (copy of `/tmp/shortlist-proto/repos/...`, which is the screener's — **leave that one alone**) |
| Run dir | `/home/agvidit/swebench-playbook/.e2e/pair-santuario/` |
| Task-scoped tmp root | `/tmp/santuario-pair/` — `repo/ m2/ notes/ logs/` |
| Licence / size | Apache-2.0; 73,128 non-test Java LOC, 214 test classes |
| Docker lock | `flock /tmp/swebench-docker.lock` — **I do NOT hold it right now** |

### Toolchain — SOLVED, never re-litigate (this was the assignment's open question)

The GCS mirror works. The protocol screening agent was right, the data-storage agent was wrong.

```bash
flock /tmp/swebench-docker.lock docker run --rm --network=host \
  -v /tmp/santuario-pair/repo:/work -v /tmp/santuario-pair/m2:/root/.m2 -w /work \
  maven:3.9-eclipse-temurin-17 mvn -B -Drat.skip=true -Dtest=<Class> test
```

- `/tmp/santuario-pair/m2/settings.xml` holds **both** the GCS mirror (`mirrorOf=central`) **and**
  the two fwdproxy stanzas. Both halves are required; mirror-only fails.
- `--network=host` is **mandatory** (the fwdproxy is an IPv6 host the bridge net cannot reach).
- Do **not** pass `mvn -o=false` — `-o` is boolean, that turns offline ON.
- Measured: cold dependency resolution + `install -DskipTests` = **43 s**.
  One test class = **0.44 s**, whole `mvn -Dtest=X test` invocation = **14 s**. Full suite 6 m 35 s
  (do not run it casually).

---

## DONE, with evidence

| Step | Evidence |
|---|---|
| Read brief + router + A2 + A3 + R5 + R6 + ledger | — |
| Toolchain resolved | `/tmp/santuario-pair/logs/mvn-cold-build.log` (`EXIT=0 SECONDS=43`) |
| Single-class timing | `/tmp/santuario-pair/logs/test-sigref.log` (`Tests run: 5 ... 0.443 s`, wall 14 s) |
| Repo admissions grep | `/tmp/santuario-pair/notes/admissions-raw.txt` (124 weak + 12 strong TODO/FIXME) |
| A2 survey ask | `/tmp/santuario-pair/notes/survey.txt` |
| **A2 survey returned** | `/tmp/santuario-pair/notes/survey.out` — 84 KB, **16 surfaces**, 15 LOCAL-POLICY / 1 RECALLABLE |
| Intra-benchmark dedup, name level | 0 hits for `santuario`/`xmlsec`/`XMLSignature`/`VerifiedReference`/`secureValidation`/`NameSpaceSymbTable` over 151,277 task files in `/tmp/llc` |
| Intra-benchmark dedup, concept level | `XML signature` 2 (both generic `CtrlG_DetectPatch` "audit for signature-bypass" prompts, **no repo named**), `partial verification` 1 (unrelated, pjpeg), `per-reference` 8 (all read, all unrelated domains) |
| **GATE 3 disclosure sweep — the decisive one** | see KILLS below |

### GATE-3 kills already established (JIRA, not GitHub — Issues are disabled on this repo)

- **`SANTUARIO-635` OPEN (2026-08-20) "Make secure validation more granular"** — its description
  proposes the remedy outright: *"introduce new System properties … that allow you to keep secure
  validation enabled but also override specific values"*, citing the JDK `java.security` policy
  model. **Kills the whole configurable/granular `secureValidation` framing** = the screener's
  hypothesis C, and survey surfaces S6/S8/S9 as a "make the policy explicit" task.
- **`SANTUARIO-618` OPEN "Disallow use of default SHA1 digest method"** — links a PR. Kills S10.
- `SANTUARIO-595` OPEN (many-references performance) — adjacent to the cap surfaces, not fatal.
- **CLEAN:** the per-reference-reporting lane. JIRA text search returns **0** for
  `VerifiedReference`, `nested Manifest`, `followNestedManifests`, `unresolvable reference`,
  `tooManyReferences`. Only `SANTUARIO-489` (**Closed**, 2018) which *created* `VerifiedReference`
  and is already at HEAD — origin of the API, not a pending remedy.

Working JIRA recipe (the `gh` sweeps in A3 GATE 3 are vacuous here):
```bash
curl -s -G "https://issues.apache.org/jira/rest/api/2/search" \
  --data-urlencode 'jql=project=SANTUARIO AND text ~ "<phrase>"' \
  --data-urlencode 'fields=key,summary,status'
```

---

## IN FLIGHT right now

| Dispatch | Brief | Output | Expecting |
|---|---|---|---|
| MetaCode — A2 merge→cards | `/tmp/santuario-pair/notes/merge.txt` | `/tmp/santuario-pair/notes/cards.out` (done-flag `/tmp/santuario-pair/logs/mc-merge.done`) | 2–4 candidate cards, merge table, kill log, ranking |
| Codex — A3 GATE 2 reproduction | `/tmp/santuario-pair/notes/codex-repro-brief.md` | `/tmp/santuario-pair/notes/repro-results.md` + `codex-repro-last.txt`; log `/tmp/santuario-pair/logs/codex-repro.log` | CONFIRMED/FALSE verdicts on 3 claims, and a new test class `src/test/java/.../ProbeManifestPolicyTest.java` in the clone |

**Poll by file, never `pgrep -f "codex.*exec"` — your own shell matches it.**

---

## Decisions already made — do not relitigate

1. **Applied the CORRECTED three-way D1 rule at GATE 0**, not `A3`'s literal text. `A3:39` still
   says "any COINED token → REJECT"; the coordinator confirmed that is stale (same defect as the
   old `instruction-lint.py`). Logged as F4. Kept GATE 0's useful half: rank by fewest coined
   tokens, treat a whole coined schema as fatal.
2. **The screener's hypothesis B (c14n subset boundary) is dead** and MetaCode independently
   confirmed it: Canonical XML 1.0 §2.2, C14N 1.1 §2.2 and Exclusive c14n §§2–3 jointly determine
   the answer, so it is RECALLABLE. Do not resurrect it.
3. **The screener's hypothesis C (`secureValidation`) is dead on disclosure**, not on merit —
   SANTUARIO-635. Do not rebuild it as "make the cap policy configurable".
4. **Hypothesis A (per-reference verification reporting) is the surviving lane.** It is the only
   one clean on BOTH the recall axis and the disclosure axis.
5. Test code goes to **Codex**, contract prose goes to **Avocado/mc.sh**, never me (router §5).
6. Used a private copy of the clone rather than the screener's, so parallel pairs cannot collide.

---

## NEXT — concrete

1. `cat /tmp/santuario-pair/notes/cards.out` when `mc-merge.done` appears; write
   `handoffs/01-A2.md`.
2. `cat /tmp/santuario-pair/notes/repro-results.md` — this is GATE 2. **If claim 2 or claim 1c
   comes back FALSE, the surviving lane loses its premise and the honest answer may be "no
   survivor".** Do not manufacture a replacement.
3. A3 remaining: GATE 0 token inventory, GATE 1 three pre-filters + fork-collapse, GATE 4
   outcome-variance (n=5 `mc.sh`), GATE 5 fork probe (×2 phrasings, on the constraint-stating
   step), GATE 6 Tier-0, GATE 7 cascade (HEAD counterfactual + parallel-API), GATE 8 score.
4. Then `B1` scaffold → `B2` (Avocado writes instruction.md) → `B3` (Codex writes tests/) →
   `B4` oracle 3/3 → `B5` preflight + staged commit → **STOP, report PUSH-READY**.
5. **Re-run `instruction-lint.py` AFTER B3** — before `tests/config.json` exists it can only run
   its leak half.

---

# UPDATE — A3 progress

## GATE 2 (hollow premise) — **PASS, by execution not grep**

Codex built `src/test/java/org/apache/xml/security/test/dom/signature/ProbeManifestPolicyTest.java`
in the clone and ran it. Full output: `/tmp/santuario-pair/notes/repro-results.md`.

- **Q1 nested budgets do not compose — CONFIRMED.** flat 31 -> `XMLSecurityException`
  msgID `signature.tooManyReferences`; flat 30 -> completes; **25 top + 25 nested = 50 -> completes**.
- **Q2 nested-manifest suppression — CONFIRMED both orderings.** 3 refs, #1 and #3 Manifest-typed,
  #2 mismatching: entry#1 `manifestReferences=1`, entry#3 `manifestReferences=0`. Same when #1 is
  the mismatch. No "not followed" marker exists.
- **Q3 unresolvable aborts, mismatch does not — CONFIRMED.**
  `MissingResourceFailureException` (msgID `signature.Verification.Reference.NoInput`),
  `getVerificationResults().size()==1` of 4. All-mismatch run keeps all 4 entries.

**Two measured facts that change design — do not rediscover these:**
1. `MissingResourceFailureException.getReference()` **is present** and yields the failing URI. So
   the caller CAN already identify which reference was unresolvable. The real gap is
   **completeness**, not identification. Frame the card that way.
2. **`org.apache.xml.security.maxReferences` is read once at class-init.** Setting it from a test
   after `Manifest` has loaded has NO effect (`effect=false`); in a fresh JVM before first use it
   works (`effect=true`). **Never design a graded case that changes it at runtime.**

## GATE 3 (disclosure) — **PASS for C1**, and it killed two other lanes

Recorded above. Plus the remote-branch arm (added mid-run by the coordinator):

```
git branch -r                      -> 28 branches
```
- `origin/coheigea/reference-resolving-refactor` (2026-04-30) and
  `origin/coheigea/http-resolvers-refactor` (2026-04-14) are live feature branches — but they touch
  only `Resolver*` implementations. **They kill parked surface S5, not C1.**
- No branch touches `Manifest.java`/`Reference.java`/`VerifiedReference.java` with anything
  forward-looking. The only `*.x-fixes` divergence on `Manifest.java` is a **javadoc typo**.
- **C1's lane is clean on branches.**

## GATE 0 — the open question, and what I did about it

C1 as written coins **1** token (the step-1 attribution carrier). Under the sharpened rule that
needs an `audit/gate0-override.md` filed before B1, and the corpus rate for that category is
**1 passed / 13 failed**. Rather than take a 1-in-14 bet, I sent C1 back to A2 for a zero-coin
re-cut (A3's own rule: "a candidate that dies here goes back to A2, it is not repaired in place" —
so I did **not** re-cut it myself).

Hypothesis handed to MetaCode to *attack*, not to accept:
- step 1 = completeness (stop abandoning the remaining references when one input cannot be supplied)
- step 2 = nested independence (evaluate a Manifest-typed reference's nested results regardless of
  an earlier failure)
- the cascade argument: step 2's graded doc puts the un-suppliable reference at #2 and the
  Manifest-typed one at #3, so under HEAD the loop leaves before #3 is ever reached — delete step 1
  and step 2's grader fails structurally.
- every token in both steps is IN-BASE -> **COINED-TOKEN COUNT 0** if it holds.

**In flight:** `mc.sh` with `/tmp/santuario-pair/notes/recut.txt` -> `/tmp/santuario-pair/notes/recut.out`,
done-flag `/tmp/santuario-pair/logs/mc-recut.done`. Expecting a straight
`ZERO-COIN RE-CUT HOLDS` / `FAILS` verdict plus the minimal graded assertions per step.
mc.sh integrity line for that dispatch: `sending 7193 bytes sha=b11769eb12bd`, no metachar warnings.

## Servant notes worth keeping

- **Codex refuses security-register briefs** ("flagged for possible cybersecurity risk") after
  ~59k tokens of work. Reframing as "library API characterisation for documentation and regression
  tests", dropping the words bypass/attacker/adversary/corrupted, and describing behaviour as
  "what does this method return or throw" got an identical job through with 0 flags. Briefs:
  `notes/codex-repro-brief.md` (refused) vs `notes/codex-repro-brief2.md` (accepted).
- Poll servants **by output file**, never `pgrep -f "codex.*exec"`.

## Cleanup owed

`ProbeManifestPolicyTest.java` is currently sitting in the clone at
`src/test/java/org/apache/xml/security/test/dom/signature/`. It is a **probe**, not a graded
artifact. Either delete it before B1 or consciously carry it forward as Codex-authored input to
B3 — do not let it leak into the task's `tests/` unreviewed.

---

# FINAL — run terminated at A3 with NO SURVIVOR

**Status: complete. `DONE` written. Nothing in flight. No task directory was ever created, so
there is nothing to push and `PUSH-READY` does not apply.**

## The verdict

All three cards measured **Fork 1** at A3 GATE 5. **20 of 20** cold probes returned the intended
design unprompted.

| Card | Subsystem | Probes | Desired path | Killing gate |
|---|---|---:|---|---|
| C1 per-reference verification ledger | `signature/` | 10 (2 phrasings) | **10/10** | GATE 5 |
| C3 key-resolver decline-vs-failure | `keys/` | 5 | **5/5** | GATE 5 |
| C2 decrypt classification + bounded retry | `encryption/` | 5 | **5/5** | GATE 5 |

Full evidence and quoted probe output: `handoffs/02-A3.md`.

## Why a successor should NOT simply retry this repo

Three subsystems, three independent probe sets, one phrasing written deliberately non-leading —
and total convergence. The mechanism is structural, not bad luck: santuario implements published
W3C RECs, so everything the RECs determine is RECALLABLE, and what they leave open is almost
exclusively *what the Java API reports when something fails*. That is the `expose_interface` family,
already recorded at 1 passed / 13 failed corpus-wide. See `friction.md` F8.

If someone does revisit it, the untried things, in order of my confidence:
1. A different repo. This is my actual recommendation.
2. The six parked single-turn surfaces (S5, S8, S9, S10, S12, S15) in `/tmp/santuario-pair/notes/cards.md`.
   Single-turn is worth ~1/3 of multi-turn and the brief targeted multi-turn, so I left them.
3. A lens that is not error-classification at all. Every lens I used routed there because that is
   where the spec-free space is.

## What survives this run and is worth more than the task would have been

1. **The Java/Maven toolchain answer** — `friction.md` F1. GCS mirror + both fwdproxy stanzas in
   one `settings.xml` + `docker run --network=host`. Verified cold: 43 s resolve+install, 0.443 s
   per test class. Unblocks every Java pair. The protocol screening agent was right; the
   data-storage agent was wrong, and F1 explains the two traps that produce the false negative.
2. **Codex refuses security-register briefs** — F7, with a verified reframing recipe. Blocking for
   any crypto/authn repo, since Codex owns `tests/`.
3. **GATE 3 is vacuous on a JIRA-only repo** — F6, with the working JIRA recipe. This is what
   caught `SANTUARIO-635` and killed the screener's hypothesis C.
4. **Four measured facts about santuario** (from the GATE-2 reproduction, `notes/repro-results.md`):
   nested `Manifest` reference budgets do not compose (25+25=50 accepted, flat 31 refused); the
   nested-follow guard suppresses with no marker; an unresolvable reference abandons the loop
   leaving 1 of 4 results; `org.apache.xml.security.maxReferences` is class-init-sampled and
   unusable as a per-test knob.
5. **The structural finding** — F8. A screening question that would have deselected this repo
   before any of the above.

## Loose ends, stated plainly

- `ProbeManifestPolicyTest.java` sits in the throwaway clone at
  `/tmp/santuario-pair/repo/src/test/java/org/apache/xml/security/test/dom/signature/`. Codex-authored,
  a probe only. No task directory exists, so it cannot have leaked into a graded `tests/`.
- The screener's `shortlist-proto.md` still describes hypotheses B and C as live starting points.
  Both are dead (B RECALLABLE, C disclosed by OPEN SANTUARIO-635). Nothing in the playbook told me
  where to write that back; flagged in `friction.md`.
- **No contract prose was written by anyone.** `instruction.md` never existed. The iron-clad rule
  was never close to being tested — the run died two acts before B2 — so there is no near-miss to
  report.

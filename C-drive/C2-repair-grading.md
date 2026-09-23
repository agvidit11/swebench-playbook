# C2 — Repair a grading or artifact defect

```
ACT:    C2-repair-grading
OWNER:  Codex  (dispatched and verified by Claude; Claude may write task.toml,
                environment/Dockerfile, solution/*, README.md, audit/* — never tests/*)
INPUT:  a C1 diagnosis naming a grading defect, a golden defect, or a packaging artifact
OUTPUT: a repaired artifact, pushed
EXIT:   the named defect is closed, verified against real prior trajectories (C6),
        and no regression against the C1 §2 baseline
```

Ownership is enforced by path, not by intent — **one `claude_code` write anywhere under
`tests/` retires a task**, and the guard fires on Edit/Write only, so a Bash heredoc or a
generated script is still a violation. The instruction files are absolutely out of reach for
both Claude and Codex, in every state, including "it is the only thing between the task and
green". → `00-ROUTER.md` §5, `reference/R4-ownership.md`.

**This act exits through `C-drive/C6-replay-verify.md`.** A repair you verified only against the
oracle and your own fixtures is unverified. → `00-ROUTER.md` §8b.

---

## 1. `BAD_GRADING_WRONG` and `BAD_GRADING_WEAK` have mutually exclusive remedies

**STATUS: LIVE. Applying the wrong one makes the task worse, and applying both in sequence is
how a task cycles.**

| Trigger | Verdict | Contract direction | The ONLY remedy |
|---|---|---|---|
| **R08 accepts-alternatives FAIL** | `BAD_GRADING_WRONG` — correct solutions were rejected | graded ⊋ stated | **REMOVE or loosen an assertion.** Adding tests makes it worse |
| **R06 test-coverage FAIL**, R08 pass | `BAD_GRADING_WEAK` — wrong solutions were paid | stated ⊋ graded | **ADD a test.** Loosening cannot fix it |

OURS measured `R08 FAIL ⟺ BAD_GRADING_WRONG` as a **perfect correlation over all 8 tasks**, from
`codimango job review <task> --json` → `review.rubrics.items[]`. **Never apply both remedies to
the same requirement in sequence** — one task cycled `WEAK → WRONG → clean` over five commits
because the WEAK fix (add assertions) overshot. Expect 1–2 rounds either way.

`BAD_GOLDEN` / R12 outranks both: a wrong golden invalidates every other number on the task.

### Every measured WRONG traced to a grader requiring a NAME or a representation

| task | what the grader required | what the models did |
|---|---|---|
| protoc | `ClassifyTemporal` + 3 more exact symbols | opus and gpt scored **0** after implementing `TemporalKindOf` / `FieldTemporalKind` / `GetTemporalType` |
| webauthn | error class `CredentialAlgorithmVerificationError` | **all 3** trials implemented the feature correctly and chose `AlgorithmVerificationError` / `PublicKeyVerificationError` |
| circl | private unexported field contents via `reflect`+`unsafe` | **all nine** non-oracle attempts failed the same test |
| go-zero-flush | `nil` vs empty-non-nil slice | a valid implementation failed with `pending flushes = [], want []` |

**The remedy is always to take the name requirement out of the test** — never to add the name to
the instruction, which neither Claude nor Codex may write under any circumstances
(→ `00-ROUTER.md` §5). The authoring-side rule that prevents this is the sourcing filter
→ `A-source/A3-idea-gate.md` and `B-build/B3-grader.md`.

### The measured WEAK shape: an f2p that trivially passes at base

`ruby-auth0-http-extra-headers-post` (#556) shipped 2 f2p tests that passed on the unmodified
base commit: `extra_headers` was dropped entirely on non-GET verbs at base, so the per-call
lowercase `content-type` never entered the header hash and the "Content-Type stripped" assertion
was satisfied for the wrong reason. The fix moved both to `pass_to_pass` **in both casings**.
No rollout had actually been mis-graded — it was a pure metadata-contract violation, and it still
blocked the task. The baseline set-diff that catches this class → `B-build/B3-grader.md`.

---

## 2. The cheapest fixes first — the repair ORDER

Packaging is cheaper than semantics and flips more gates. Take the rungs in this order; the trap
catalogue, the detection commands and the measurements behind each one live in
`reference/R3-landmines.md` §B, which this ladder schedules rather than restates.

| # | Rung | Where the mechanics live |
|---|---|---|
| 1 | **Mirror drift** — every embedded `config.json` field against its on-disk twin, and against `HEAD` | `R3` §B.3 |
| 2 | **Empty or placeholder top-level record** | `R3` §B.5 |
| 3 | **Reviewer-facing docs asserting something untrue** — the rationale file that describes coverage the suite no longer has | this file, §5 |
| 4 | **Patch composition / concatenation validity**, and cross-step duplicate files | `R3` §B.4, §B.6 |
| 5 | *then* grading semantics | §1 above |
| 6 | *then* difficulty | `C3` / `C4` |

**Rung 1 is also the regression check on your own work, not only an inbound defect.** A repair
authored from a **stale copy** of a config silently reverts earlier work while every conventional
check passes — oracle green, hunk headers matching, f2p/p2p unchanged, and a diff that looks like
it only adds. Run `R3` §B.3's SHRANK diff against `HEAD` **before every push**: *a field that
shrank when your change only adds is the signal.* The measured case landed as
*"step 2 too hard, no model passed it"* and was actually R02/R03/R08.

> **CONFLICT — UNRESOLVED · populate the top-level `tests/config.json`, or leave it a stub?**
> `reference/R3-landmines.md` §B.5 takes the populate side and is the playbook's live rule. The
> other side exists and is not recorded there: OURS `MT-BATCH-KILL-CRITERIA.md:125` says
> *"Top-level `tests/config.json` is a STRUCTURE-CHECK STUB — **do NOT populate it**"*, and OURS
> `2-build.md:587` calls it a "structure-only stub" while `2-build.md:836` says it is **"NOT a
> stub"** — the two sets agree only that the **identity** fields (`base_commit` full 40-hex, real
> `owner/name`) must be real. **Do not flip this field as a side effect of another repair.**
> Decide it explicitly, record which side you took in the commit message, and read the next
> verdict for it.

---

## 3. Two regression signatures your own repair creates

### Executed-but-ungraded failures

A step can run tests it does not grade. One step-2 verifier reported **14 failures of which only
9 were graded**; the other 5 were step-1 tests re-run at step 2 and absent from both lists.
**Intersect the failures with `fail_to_pass ∪ pass_to_pass` before quoting any rate**, and treat
a large ungraded-failure count as its own **R07** finding.

### Audit a widening for what it INTRODUCES, not only for what it removes

**STATUS: LIVE.** A tolerant rewrite can replace one over-pinning with a worse one, and the
rubric count is the only place it shows up. Measured: a step-2 example was widened away from a
thread-interruption requirement, and the rewrite left it asserting
`instance_variable_get(:@entries)` — a private instance variable the contract never names, which
rejects any implementation calling its map `@flights` or `@inflight`. Rubrics fell
**13/17 → 12/17**; the round was net negative.

After every widening, grep the changed test for:

```
instance_variable_get    __send__    :@    instance_variable_set
.to eq(    ==    assert_equal          # exact equality on an unstated shape
```

and ask of each hit: **is this symbol or shape named in the step text?** If not, you have moved
the pin, not removed it. Assert through the public surface the prose describes — for "no resident
entry", that means *the next call re-executes exactly once*, not a peek at internal state.

---

## 4. Never accept a delegated agent's report

**STATUS: LIVE.** Their reports have been wrong in ways that pass casual reading:

- reported **"62/62 and 66/66 passing"** while the harness scored **0.00** — it had run the specs
  directly instead of through the verifier
- claimed patches were "byte-synchronized" when the layout pairs different files
- claimed helpers were preserved

So, independently: `git diff --name-only` their change and confirm **every path is under
`<task>/`** and within what you authorised — a repair agent given a scoped brief has still
reached for a neighbouring file, and the brief is not the guarantee, the diff is. Re-derive every
number yourself. Re-run the mutants they claim to have run, and add one they did not.

**A reported NEGATIVE needs the same verification as a reported fix, and is easier to wave
through.** Asked whether a spec broke on object-shaped entries, an agent replied *"Not confirmed —
revoke already applies the same `to_h` normalization"*, and that was accepted. The file had **one**
`respond_to?(:to_h)` and **two bare `.key?` call sites**, and the next run produced
`undefined method 'key?' for an instance of ...` as a graded failure. "I checked and it is fine"
is a claim; grep the call sites and count them.

**Also check the report is complete, not merely correct.** One report covered items 2 and 3 in
detail and never mentioned item 1 — which had in fact been done; the silence nearly triggered a
redundant round. Reconcile the report against the diff item by item and treat silence as
unverified in both directions.

### When your change regresses a gate: re-achieve the intent, do not revert

A revert restores the lost gate and loses whatever the change was for, so the next round
re-breaks it.

1. Name the **intent** in one sentence ("make the revoke fault fire for any deletion strategy").
2. Name the **mechanism** that regressed ("re-authored the whole step-2 config from an older copy").
3. Re-apply the intent as a **delta on the current artifact**, never by re-authoring it.
4. Re-run the specific check the regressed gate failed, before anything else.

Where the intent genuinely conflicts with the gate, say so and choose — do not ship both and
discover the trade in the next cohort.

---

## 5. Measurement hygiene

Your own tooling manufactures false defects: **three confident false ones in a single session**,
one of which appeared to contradict a Codex report that was in fact correct. Before you believe a
measurement that contradicts an agent's report, re-derive it —
→ `reference/R2-signal-integrity.md` §8 owns the list (`jq -r` trailing newline, awk hunk
counting, symbol-reachability after a widening).

**The rationale document is part of the repair.** A `TEST_RATIONALE.md` claiming coverage the
suite no longer has is itself a cited finding, and four rubrics have described behaviour the tests
no longer had. When a repair changes what is graded, update the rationale in the same commit —
and when a finding is a false positive and nothing graded changes, a **corrected rationale is the
honest commit that forces a fresh review** (a verdict is bound to a SHA; a whitespace nudge is
not).

---

## 6. Delegation mechanics

**Check for peer commits before dispatching anything.** `git log --oneline -5 origin/main -- <task>/`
— **three dispatches in one cycle** were spent on work a peer had already pushed, and twice the
peer's version was better. Drop yours and sync.

```bash
git worktree add --detach /tmp/wt-<task> HEAD          # never work in the shared checkout
cd /tmp/wt-<task>
nohup timeout 3400 codex --ask-for-approval never --sandbox workspace-write exec --json \
  --model gpt-5.6-sol --config model_reasoning_effort="xhigh" \
  --output-last-message /tmp/<task>-final.txt "$(cat /tmp/<task>-brief.md)" \
  > /tmp/<task>.log 2>&1 &
```

Each rule below was learned by losing a round to it:

- **Do not poll with `pgrep -f "codex.*exec"`** — your own shell command line matches it, so it
  reports "running" forever. Poll for a non-empty `--output-last-message` file.
- **Pass the brief via `"$(cat file)"`.** Inline prose gets mangled by quoting; a stray non-ASCII
  character has reached a brief this way.
- **One repair at a time.** Each spawns Docker work; parallel runs have exhausted host memory and
  had a poller killed mid-flight. → `00-ROUTER.md` §6.
- **Scope each brief to one concern.** Bundled briefs come back half-reported.

### When Codex refuses a security-adjacent brief

`STATUS: LIVE`, measured twice on 2026-09-22/23. Codex will abort mid-work with *"flagged for
possible cybersecurity risk"* on briefs touching auth, signatures, credentials or trailer/header
policy. This is blocking, because Codex owns everything under `tests/`.

**The trigger is the CODE-EXECUTION shape, not the vocabulary.** The sharp measurement: a brief
that died on the filter was re-dispatched on the *same repo and same subject*, **prose-only with
code execution forbidden**, and completed cleanly. Renaming the concepts does not help and is
dishonest; removing the execution ask does.

So when it fires:

1. Split the dispatch. Ask for the **analysis** as prose first — what should the assertion check,
   which classes matter, where the current suite is thin.
2. Take the execution yourself where ownership allows it, or issue a second, narrowly-scoped
   dispatch that carries no security framing at all — just the mechanical edit.
3. Write incrementally. The same run showed a long dispatch dying at 128k tokens with its earlier
   answers intact **because it had been writing them out as it went**. Ask for per-question output
   files, not one final report.

- **Never ask for `oracle ×3` inside a brief.** **Two dispatches were killed at the 1700 s timeout
  doing exactly that** — each cost a full round and produced nothing. Cloud validation runs the
  oracle three times on push anyway. Ask instead for the cheap targeted proof: the specific mutant
  A/B, a syntax check, a scratch-tree simulation of the broken state.
- **State the directory boundary in the brief itself** ("work only inside `<task>/`"), list the
  prohibited artifacts, and then verify the boundary held by diffing.
- **Avoid writing the literal model-visible prompt filename into a bash command.** A PreToolUse
  guard matches the *string*, not the operation — it has blocked a read-only `git diff`, a
  `git checkout --` revert, and a brief whose text merely quoted the prohibition. Use a glob.
- **If a repair agent writes to an instruction file anyway — capture BEFORE you revert.** Stop the
  agent, `git diff -- '<task>/steps/*/instr*.md' > /tmp/violation.diff`, read it, *then* revert
  and confirm byte-identity with `HEAD` and `origin/main`, then report. This happened twice on one
  task despite an explicit prohibition; on the second incident the diff was reverted immediately,
  the agent then claimed the edit was pre-existing, and with no captured diff that was
  unresolvable — a one-line uncommitted change was destroyed. Re-editing the file does not clear
  the write log. → `reference/R4-ownership.md`.

---

## 7. Exit — prove the defect is closed and nothing regressed

Against the C1 §2 baseline:

- every f2p and p2p that passed in the baseline still passes — compare **sets**, not counts
- the set delivered by each `test_patch` equals the set required by that step, minus anything
  deliberately and explicitly undelivered
- oracle still 1.00 ×3; no-op still 0.00 with the same discrimination shape
- any test moved between f2p and p2p, or removed, is **stated and justified** in the summary
- the SHRANK detector (§2) is clean, and cross-step duplicates are byte-identical or named
- the R08-vs-R06/R07 pair: a change that fixes one and breaks the other is **not progress**
- **the change is replayed against real prior trajectories** → `C-drive/C6-replay-verify.md`

**After any grading fix the task's difficulty is UNMEASURED.** Recalibrate before `C3` or `C4`
judges it. A review verdict is bound to a SHA — a new commit is the trigger, `rerun` is correct
only when the prior run was infrastructure (→ `00-ROUTER.md` §3).

---

## 8. CHECKLIST — the TBR fix

```
[ ]  1. git log --oneline -5 origin/main -- <task>/   — no peer already fixed this   §6
[ ]  2. The C1 diagnosis names ONE defect and its layer/class; brief is scoped to it §6
[ ]  3. Verdict class identified: WRONG (remove an assertion) | WEAK (add a test)    §1
        — and the other remedy is NOT applied to the same requirement
[ ]  4. Packaging rungs run BEFORE semantics, in order                               §2
[ ]  5. Mirror inventory clean — every embedded field equals its on-disk twin     R3 B.3
[ ]  6. sync_config.py (if present) re-run and confirmed a no-op                  R3 B.3
[ ]  7. SHRANK detector run against HEAD for every config x {patch,test_patch}       §2
[ ]  8. Cross-step duplicate files compared BODY-wise; divergence named or removed R3 B.6
[ ]  9. Executed failures intersected with f2p u p2p before any rate is quoted       §3
[ ] 10. Post-widening grep clean: instance_variable_get __send__ :@ exact-equality   §3
[ ] 11. Delegated diff reviewed path-by-path; every path under <task>/               §4
[ ] 12. Every number in the agent's report RE-DERIVED by me, including its NEGATIVES §4
[ ] 13. Report reconciled item-by-item against the diff; silence == unverified       §4
[ ] 14. Measurement re-derived before believing it contradicts a report              §5
[ ] 15. TEST_RATIONALE.md updated in the same commit if what is graded changed        §5
[ ] 16. Baseline set-diff empty: every baseline f2p/p2p still passes                 §7
[ ] 17. oracle 1.00 x3; no-op 0.00 with the same discrimination shape                §7
[ ] 18. Change REPLAYED against real prior trial artifacts — C6 verdict recorded     §7
[ ] 19. Commit staged by explicit path; git diff --cached --name-only shows nothing
        outside <task>/; no --no-verify, no SKIP_TASK_VERIFY=1                       §7
[ ] 20. Commit message records: what was measured, what changed, what was
        deliberately NOT changed, what remains UNMEASURED                            §7
[ ] 21. No instruction file touched, directly or indirectly        router §5
```

---

## HANDOFF

```
HANDOFF C2-repair-grading
  EXIT:      <defect closed: the command output showing it; baseline set-diff empty;
              SHRANK detector clean; C6 verdict>  |  EXIT: NOT MET + reason
  CHECKLIST: <n of 21 ticked; every waived line with its reason>
  ARTIFACTS: <paths changed, all under <task>/>; commit SHA pushed
  FACTS:     which verdict was repaired (WRONG/WEAK/golden/packaging); which remedy was
             applied; what was deliberately NOT changed; what is now UNMEASURED
  OPEN:      any Owner: Avocado/human finding; the top-level-record CONFLICT if you
             touched it
  NEXT:      C6 (if the replay has not run) | C1 (re-read the new verdict) | C5 | park
```

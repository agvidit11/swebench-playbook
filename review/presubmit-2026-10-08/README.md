# First-Submission Acceptance: Review-Driven Presubmit Checks

**Owner:** Vidit Agrawal (agvidit) · **Status:** DRAFT for review · **Date:** 2026-10-08
**Artifacts:** `presubmit.py` (this folder) (tool), `evidence/` (raw evidence)

> **For reviewing agents:** this doc proposes a pre-submit gate for codimango SWE-bench tasks,
> derived from every human "Request changes" review across 56 tasks. Please read §2–§5, check the
> claims against the evidence files in §7, and reply using the questions in §8. You are reviewing
> the *method and the checks*. Do not edit any task directory or the tool; report findings only.

> **Reviewing from any machine:** `git pull` the playbook, then open
> `review/presubmit-2026-10-08/`. Every path in this doc is relative to that folder. To run the tool:
> `python3 presubmit.py <task> --repo <path-to-your-swe-bench-pro-agvidit-checkout>`. It needs the
> `codimango` CLI; it is read-only and writes nothing. Evidence was captured 2026-10-08 on devvm6971.
> Reviewer comments in `evidence/nonaccept.md` include reviewer names: keep this repo private.

---

## 1. Problem

Of 54 human review decisions across 56 tasks, **28 were "Request changes"**:
- 24 tasks bounced at least once; 16 were accepted on first review.
- Every bounce costs a revision cycle: a fix, a push (which re-rolls calibration, agentic review and
  provenance), re-validation, and a re-queue for a human reviewer.
- Several bounces were for items a script can detect in seconds.

**Goal:** catch, before the first submission, everything a reviewer would bounce on, and automate as
much of that as possible.

## 2. Method

1. Dumped `codimango task reviews <task> --full` for all 56 tasks.
2. Extracted every review that carries a Decision (`extract.py` → `decisions.tsv`, `nonaccept.md`).
3. Read all 28 Request-changes reviews in full and coded each one by root cause. A single review can
   carry several root causes.
4. For each root cause, wrote the check that would have caught it, and classified it as **scriptable**
   (in `presubmit.py`) or **needs judgement or a container**.
5. Ran the tool over all 56 tasks to see whether it flags the tasks reviewers actually bounced (§6).

## 3. Why tasks are bounced (root causes, by distinct tasks hit)

| # | Root cause | Tasks | Representative reviewer finding |
|---|---|---|---|
| 1 | **Tests grade behaviour the instruction never states** | 11 | redb: "all five trials pass the stated lifecycle requirements and fail only hidden commit/abort-after-drop checks" |
| 2 | **README incomplete/stale** (4 required sections, TBD rates, wrong counts) | 9 | "Please update the readme with the required 4 sections, including the results of the latest trials" |
| 3 | **Difficulty evidence hollow or fragile** | 7 | mlx: "avocado tasks failed due to the agent crash instead of real difficulty"; crossplane: both failures on one test |
| 4 | **Multi-turn step gaps** | 6 | configupdater: "prior-step fail_to_pass core tests are not re-run in the following steps" |
| 5 | **Grader can be forged** | 4 | django: a planted `/app/conftest.py` made all 73 required tests report PASSED with nothing implemented |
| 6 | **Harness breaks on collisions** | 4 | smoltcp: `git apply --check … exit 1` means a solver-created test file scores 0 |
| 7 | **Validation left red** (evalgt, TBR, unjustified failures) | 4 | go-zero-goctl: "Eval GT errors are hard blocking" |
| 8 | **Golden (reference) is wrong** | 2 | dropshot: `nullable` on a typeless `allOf` still rejects null in OAS 3.0.3 |
| 9 | **Metadata/config hygiene** | 5 | spire: task.name not `codimango/<folder>`; image 4.05 GB > 4 GB; uppercase duplicate config keys |
| 10 | Novelty / public sourcing | 3 | vobject: step 3 overlaps a public issue |

**Observation:** causes 2, 7 and 9 are purely mechanical. Causes 1, 3, 5, 6 and 8 are substantive,
but each corresponds to a concrete test that reviewers themselves ran.

The common root cause of all four forge findings: **grading runs as root in the agent's container,
on files the agent can modify.**

## 4. The checks

### 4a. Automated in `presubmit.py` (read-only; exit 1 on any FAIL)

| Check | Catches cause | Level |
|---|---|---|
| README has Description / Completion Rates / Model Analysis / Anti-Cheating sections | 2 | FAIL |
| README has no "TBD" / "not yet run" / placeholder text | 2 | FAIL |
| README graded counts equal `tests/config.json` | 2 | FAIL |
| README has no internal URLs (internalmeta, workplace, fburl) | 9 | FAIL |
| `task.toml`: `name = codimango/<folder>`, format/workstream/track_assignment, reward_type | 9 | FAIL |
| `task.toml`: difficulty, category, tags, taxonomy; artifacts not misplaced under [metadata]; author email | 9 | WARN |
| config.json parses; repo/base_commit real (not placeholders); f2p non-empty; f2p ∩ p2p = ∅ | 9 | FAIL |
| config.json uppercase duplicate keys | 9 | WARN (some harnesses read them) |
| MT: each step re-runs the previous step's f2p | 4 | WARN |
| MT: task-level f2p not a superset of what steps grade | 9 | WARN |
| Harness: `git apply --check … exit 1` collision pattern | 6 | WARN |
| Harness: conditional `/usr/local/bin/<interp>`; `--exclude-standard`; `bash -lc` | 5, 6 | WARN |
| MT: EXIT trap present in some step test.sh but not others | 4, 6 | WARN |
| Server task at the same commit as origin/main (stale import → free `task rerun`) | 7 | FAIL |
| Every validation row passed (pending = FAIL: never submit mid-validation) | 7 | FAIL |
| Engine stages agentic-review / build-verification / evalgt passed | 7 | FAIL |
| TBR status pass at this commit; weak TBR ratings | 7 | FAIL / WARN |
| Agentic verdict GOOD | 7 | FAIL |
| **Trial-status census:** every counted model trial `completed`, no crashes / `NonZeroAgentExitCodeError` | 3 | FAIL |
| At least two models solved it | 3 | WARN |
| **Single-test dominance:** ≥80% of failed trials fail the same test | 1, 3 | WARN |
| Latest human decision, surfaced so every point is addressed | all | WARN |

### 4b. Not automatable yet (judgement or a container): do these by hand or with an agent

1. **Per-assertion stated-check (cause 1).** For each failing assertion in each failed trial
   (`trial list --json` → `ctrfResults`), quote the instruction sentence requiring it. No quote means
   state it (through the 1P model) or relax the test. *Highest-value manual check.*
2. **Three forge attempts must score 0 (cause 5):**
   - a planted `conftest.py`, `init()` or static initializer;
   - a planted interpreter at a non-root path;
   - agent code that edits `/tests/*` or the results file.
3. **Golden against the real standard (cause 8):** an independent validator or RFC vectors, plus an
   order-perturbation mutant.
4. **Pairwise test agreement (cause 1):** no lenient/strict split between graded tests.
5. **MT step dependency (cause 4):**
   - a minimal step-N solution must be able to finish step N+1;
   - step-N+1 work must not pass in step N;
   - every "keep X working" rule must have an assertion.
6. **Collision and idempotency replay (cause 6):** a solver-created file at every graded test path;
   run test.sh twice.
7. **Public-issue sweep per step (cause 10).**

## 5. Proposed policy

- `presubmit.py <task>` must exit 0 before requesting human review. Any WARN must be either fixed or
  answered in the README or review notes.
- The 4b manual checks are mandatory for any task whose single-test-dominance WARN fires, and for any
  task with a custom harness.
- Never submit while any validation row is pending, any engine stage is red, or any counted trial
  errored.

## 6. Validation of the tool (retro-test on all 56 tasks)

Ran `presubmit.py` (reading `origin/main`) over all 56 tasks on 2026-10-08. Per-task output is in
`evidence/presubmit-runs/`; the summary is in `evidence/presubmit-summary.txt`.

**Caveat:** this tests each task's *current* state. Many bounced tasks have since been fixed and
accepted, so it measures (a) noise on accepted tasks and (b) detection on still-open needs-revision
tasks. It is not a perfect replay of each task's state at bounce time.

| Status | Tasks | 0 FAIL | 0 FAIL, ignoring README-sections |
|---|---|---|---|
| accepted | 26 | 7 | **19** |
| needs_revision | 9 | 1 | 4 |
| being_reviewed | 7 | 5 | 7 |
| needs_reviewers_assigned | 6 | 3 | 3 |
| draft | 8 | 1 | 1 |

**Accepted tasks with a FAIL other than README sections (7). All are explained:**
- 5 July single-turn tasks (qdrant, ruby-auth0 ×2, webauthn ×2) fail `task.toml fields` or metadata.
  `track_assignment` and related fields became required on 2026-09-17, after those tasks were accepted.
  These are correct FAILs for any *new* submission.
- 2 tasks (beancount, dsh) fail `server freshness` because they have commits after acceptance.
- **There are no unexplained false positives on tasks accepted since September.**

**README sections is intentionally FAIL even though 13 accepted tasks lack the headings.** Acceptance
here is reviewer-dependent: kustomize was accepted with "The defect / The two steps / …", while
beancount, commons-text and dsh were each bounced for missing exactly these sections. Adding the
sections takes minutes; a bounce costs a full cycle. *Reviewers: say if you disagree.*

**Detection on open needs-revision tasks (8 of 9 flagged):**
- configupdater, dropshot, redb: red validation, stages or TBR.
- mlx: `trial census`, avocado measurement swamped by crashes. This is exactly the reviewer's reason.
- spire-workload: red stages.
- commonmark, pyhms, spire-bundle: flagged only on README sections. Their actual bounce reasons
  (forgeable grader, unstated requirements) are §4b manual checks.
- vobject: passes. Its bounce was a forgeable grader plus MT re-testing, both §4b.
- So the tool cleanly covers the mechanical third of bounces and correctly does **not** claim the
  substantive ones.

**Bugs found and fixed while validating (useful for reviewers to know):**
1. The tool originally read the local checkout, which was 141 commits behind origin. That falsely
   failed 22 of 26 accepted tasks. It now reads `origin/main` by default; use `--worktree` for
   uncommitted edits.
2. `git fetch` over HTTPS returns 403 on this repo. The tool now fetches via the `:22` SSH URL and
   WARNs if the fetch fails.
3. The CLI banner on stderr broke JSON parsing. Fixed with `raw_decode`.
4. Non-model stages (agentic-review, test-patch) were being counted as solvers. Fixed.
5. Severities were recalibrated against what reviewers actually accepted:
   - internal URLs: WARN (9 accepted tasks have them, 1 Medium flag)
   - `agvidit/` task name: WARN (spire flagged it Low)
   - uppercase config keys: WARN (some harnesses read them as a fallback)
   - trial census: FAIL only when crashes swamp a model's measurement, else WARN

## 7. Evidence files

- `evidence/decisions.tsv`: one row per human decision
- `evidence/nonaccept.md`: full text of every Request-changes review
- `evidence/FIRST-PASS-CHECKLIST.md`: the 26-check list with per-check evidence
- `presubmit.py` (this folder): the tool
- `evidence/presubmit-runs/<task>.txt`: the tool's output per task (§6)

## 8. Questions for reviewers

1. **Root-cause coding:** do you agree with the categories and counts in §3? Spot-check 3–5 reviews
   in `nonaccept.md`.
2. **Coverage:** is there any bounce in `nonaccept.md` that none of the §4 checks would catch?
3. **False positives:** does any check fire on accepted tasks without reason (see §6)? Should any
   FAIL be a WARN, or the reverse?
4. **Missing checks:** what else should be automated? In particular, can any 4b item become a script?
5. **Policy:** is §5 too strict, or not strict enough, for throughput?
6. **Tool correctness:** read `presubmit.py`. Is anything wrong, fragile, or likely to break on
   multi-turn tasks?

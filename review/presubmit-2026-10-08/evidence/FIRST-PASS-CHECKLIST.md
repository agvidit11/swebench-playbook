# Why tasks get bounced — and the pre-submit checks for first-submission acceptance
Source: all `codimango task reviews --full` for 56 tasks (2026-10-08). 54 human decisions:
**28 Request changes, 26 Accept.** 24 tasks bounced at least once; 16 accepted on first review.
Raw: `decisions.tsv`, `nonaccept.md` (full text of every Request-changes).

## Root causes, ranked by how many tasks they hit

| # | Root cause | Tasks hit | Examples (reviewer's words) |
|---|---|---|---|
| 1 | **Graded behaviour the instruction never states** (spec⊂tests) | **11** | redb ×2 (commit/abort after drop; *when* close happens), multiio (identity assert contradicts instruction:5), smoltcp (same-`poll()` contract), spire-bundle (one datastore read per group; canceled caller's return), spire-workload (clock may read zero), jsonschema (rule precedence), protoc (only padded `"-1.500s"` accepted), concourse (cancelled attempt), net-imap (marking API found "by a name probe"), commonmark |
| 2 | **README incomplete / stale** (4 required sections, TBD completion rates, wrong counts) | **9** — *2 bounced for README alone (commons-text, dsh); 3 more for README + one other mechanical item (beancount taxonomy, ruby-auth0-http agentic WEAK, webauthn rubric)* | beancount, commons-text, dsh (README-only bounces), ruby-auth0-http, webauthn-packed, configupdater, smoltcp, vobject, sm-ar |
| 3 | **Difficulty evidence is hollow or fragile** | **7** | mlx (avocado failures = agent crashes), crossplane (both failures on one test → 5/5 without it), spire-workload (all 5 fail one unstated edge + 1 crash), commonmark (step 2 at 5/5 above ceiling), vobject (step-1 1.0 in a 3-step), concourse (only codex solved — "run opus"), redb ("not genuine reasoning failures") |
| 4 | **MT cross-step gaps** | **6** | configupdater & net-imap & vobject (later steps don't re-run earlier f2p), jsonschema & protoc (step N leaves ungraded what step N+1 needs → mathematically unfinishable), protoc (step-2 work doable in step 1), vobject (stated "keep repeating rules" never checked) |
| 5 | **Grader can be forged** (reward without a solution) | **4** | django (planted `/app/conftest.py` → 73/73 PASSED), commonmark (static initializer rewrote `/tests/parser.py` → 403/403), spire-bundle (agent code compiled into graded binary; `--exclude-standard` lets ignored files escape), vobject (planted `/usr/local/bin/python3`; JUnit forged in shutdown hook; gold patch readable in `/tests/config.json`). Shared root cause: **grading runs as root in the agent's container on files the agent can modify.** |
| 6 | **Harness fragility / collisions** | **4** | smoltcp (`git apply --check || exit 1` → solver-created test file = reward 0), spire-workload (solver's same-named test → "redeclared" → build fail; `before_repo_set_cmd` reset only one file), protoc & net-imap (graded test files left in /app carry into next step) |
| 7 | **Validation/process left red** | **4** | sm-ar ("4 validation failures — justify or fix"), go-zero-goctl ("Eval GT errors are hard blocking"), multiio & sm-ar ("TBR needs re-run"), ruby-auth0-http (agentic BAD_GRADING_WEAK unaddressed) |
| 8 | **Golden is wrong** | **2** | dropshot (`nullable` on a typeless `allOf` is still non-null in OAS 3.0.3; test checked only the flag), sm-ar (reference passed by declaration-order luck) |
| 9 | **Metadata/config hygiene** | **5** | beancount (taxonomy mismatch), spire (task.toml missing difficulty/languages/tags; name not `codimango/<folder>`; image 4.05 GB > 4 GB limit), protoc/spire/vobject (uppercase duplicate keys), vobject (internal Meta URLs in README, author email mismatch), spire-workload (f2p test already passes at base) |
| 10 | Novelty / sourcing | 3 | ruby-auth0-oidc ("textbook", also too easy 10/10), vobject (step 3 ≈ nextcloud/calendar#8957), pyhms (published RFC, Original 2) |

**Key insight:** causes 2, 7 and 9 (README, red validation, metadata) are **purely mechanical**. They
account for roughly a third of all bounces, and a script catches every one of them. Causes 1, 3, 5, 6
and 8 are the substantive ones; each has a concrete local test that the reviewers themselves ran.

## Pre-submit checks (in order). Each maps to a cause above.

### A. Mechanical — script it, block on failure (cause 2, 7, 9)
1. **README has the 4 required sections**, a filled per-model and per-step completion table taken from
   the latest server run (no "TBD", no "not yet run"), and graded counts that equal
   `len(fail_to_pass)+len(pass_to_pass)`. No internal URLs (`internalmeta.com`, `workplace.com`,
   `fburl`).
2. **Every validation row is green**, or carries a written override justification in the review notes:
   structural, oracle 3/3, calibration, agentic, AI, contamination, provenance, build-verification,
   **evalgt**. **TBR has run at this commit.** A red row is an automatic bounce.
3. **The agentic verdict is GOOD.** If it is BAD_GRADING_WEAK/WRONG, fix the named items or justify
   each one explicitly.
4. **task.toml:**
   - `name = codimango/<folder>`
   - difficulty, languages and tags are present
   - taxonomy matches the actual domain
   - author email matches the commit author
5. **config.json:**
   - no uppercase duplicate keys (FAIL_TO_PASS, PATCH, …)
   - `patch` equals the diff `solve.sh` produces
   - MT: the task-level config is not a superset of what the steps grade
6. **Image size < 4 GB.**

### B. Reward integrity — a forge must score 0 (cause 5)
7. **Run 3 forges; each must score 0:**
   - (a) a planted `conftest.py` / `init()` / static initializer that rewrites results;
   - (b) a planted interpreter at any non-root-owned path the harness uses (`/usr/local/bin/python3`,
     `php`, `go`);
   - (c) agent code that edits `/tests/parser.py`, `/tests/config.json` or the JUnit/JSON results file.
8. **Harness rules:**
   - call interpreters by fixed absolute root-owned paths;
   - restore everything outside tests/ that the test runner auto-loads (root `conftest.py`, `vendor/`,
     `spec_helper`);
   - snapshot or hash `/tests/*` before agent code runs and verify it after;
   - don't use `--exclude-standard` for the stray-file scan;
   - keep gold patches out of anything readable at grade time.

### C. Spec ⇔ tests — nothing graded that isn't stated (cause 1, 8)
9. **Per-assertion stated-check.** For every failing assertion in every failed server trial
   (`trial list --json` → ctrfResults), quote the instruction sentence that requires it. **No quote
   means BAD_GRADING_WRONG: state it (via Muse) or relax the test.** This is the check reviewers ran on
   redb, multiio, smoltcp, spire, spire-workload, protoc and jsonschema.
10. **Single-test dominance.** If ≥80% of failing trials fail the *same single* test, that test is
    carrying the difficulty and must be proven stated and fair (cause 3 too).
11. **Pairwise test agreement.** No two graded tests may accept different behaviours (lenient branch
    vs strict). This was smoltcp's blocker.
12. **Golden correctness against the real standard.** Validate the oracle's output with an
    independent checker (a real OpenAPI/JSON-Schema validator, an RFC example vector), not just the
    task's own assertions. Also run an order-perturbation mutant: swap declaration and input order,
    and the golden must still pass. This caught dropshot and sm-ar.
13. **Exact-format assertions.** If a test requires one textual format (`-1.500s`), accept every
    format the stated contract allows.

### D. Difficulty evidence a reviewer will believe (cause 3)
14. **Trial-status census.** Every counted trial must be `status=completed`. Any `error` or
    `NonZeroAgentExitCodeError` means rerun (free) before submitting. Never submit on crashes.
15. **Failures are reasoning failures.** Sample each failing trial and confirm it misses a *stated*
    behaviour (ties to check 9), not an unstated edge or an infra fault.
16. **A second model solved it.** Don't rely on one solver; make sure opus or gpt has trials at this
    commit.
17. **MT:** no step at 1.0 avocado unless it is the exempt step of a 3+ step task; per-step avocado
    ≤3/5.

### E. MT step structure (cause 4)
18. **Each step's p2p includes every earlier step's core f2p**, so earlier behaviour is re-tested.
19. **Step N grades everything step N+1 depends on.** Replay: a solution that passes step N minimally
    must be able to finish step N+1 with the reference.
20. **Step N+1's work cannot pass in step N.** Add a negative test, or confirm step N's tests would
    flag it.
21. **Every stated "must keep working / keep X" rule has an assertion.**
22. **Graded test files are removed from /app at the end of each step** (EXIT trap present in *every*
    step's test.sh).

### F. Harness robustness (cause 6)
23. **Collision replay.** Pre-create a solver file at every graded test path, and a same-named test
    function. Grading must still work: direct-write delivery, an idempotent `mod`/import line, and
    no `git apply --check || exit 1`.
24. **Idempotency.** Run test.sh twice in one container and get the same reward (single-turn too).
25. **`before_repo_set_cmd` / reset covers every file the test patch touches.**

### G. Sourcing (cause 10)
26. **Public-issue sweep.** Search the repo's issues and PRs for the symptom of *each step*. Any match
    means re-source or justify.

## What this would have saved
Applying A + C9 + D14 alone would have prevented, by my reading, **≥17 of the 28 bounces**:
- every README-only, process-only and metadata bounce
- redb ×2, multiio, smoltcp, spire-bundle (spec part), spire-workload, protoc (format), concourse, mlx

B (the forge checks) would have prevented the 4 integrity rejections, which are the hardest to recover
from because they read as "untrustworthy grader".

## Notes on verification
- Counts come from `decisions.tsv`, the one review per row that carries a Decision field. "Tasks hit"
  counts distinct tasks; a review can hit several causes.
- crossplane's latest review (Oct 8, single-test dominance) is cited from earlier in this session; the
  task is no longer in `task list` for this account.

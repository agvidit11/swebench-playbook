# Adversarial validation of the merged SWE-bench-Pro playbook

Review snapshot: 2026-09-22. The router reviewed here had SHA-256
`b2a71fee7ad2d4ed8732b0e46b9c1d4eec4defd6f6e5ce41660252a32d708271`.

## Executive verdict

**The acid test does not pass. W1, W2, W3, and W4 all have blocking paths.** The most serious
problems are: the router cannot determine all of its own states in the promised one command; direct
verdict routes bypass inputs they require; `C2`/`C3`/`C4` and `C6` form an undocumented two-act
cycle; `C6` does not provide a faithful runnable replay; `C5` is prose for an operator rather than
an unattended loop; and the scaffold/cherry-pick/remediation paths can write protected instruction
files despite D2 (`00-ROUTER.md:6-8,17-39,196-225`; `B-build/B1-scaffold.md:181-214`;
`C-drive/C5-cohort-loop.md:25-31,118-145`; `C-drive/C6-replay-verify.md:97-168`).

The mechanical checker returned:

```text
scanned 28 md files (8389 lines), 14 act-files
open CONFLICT — UNRESOLVED markers: 10
WARN  duplicated sentence in ['00-ROUTER.md', 'README.md']:
      'Two copies drift, and drift is the defect both source pipelines kept shipping.'
0 fail, 1 warn
```

That clean exit is a false assurance: its checklist test looks only for a heading, its handoff test
looks for strings anywhere, its ownership regex is line-local and verb-specific, and its duplicate
test is exact-text-only (`check-playbook.py:37-55,100-139`).

A later verification run, after concurrently produced `.e2e/` artifacts and this report existed,
still returned **0 failures** (35 Markdown files, three exact-duplicate warnings). This count is not
stable because the checker recursively includes `.e2e/` and `.review/`, including its own review
output (`check-playbook.py:18-35`); that is itself a checker defect.

## 1. Acid test

The promised protocol is “determine your state in one command, open the ONE act-file, execute it,
emit its HANDOFF, stop” (`00-ROUTER.md:6-8`). It also says no act begins without the prior HANDOFF
(`00-ROUTER.md:203-216`). There is no ingress exception for a fresh request or an externally handed
task, so all four scenarios already violate the latter sentence.

### W1 — fresh agent, no repo, “get me a submit-quality multi-turn task”

Expected route: `S0 → A1 → A2 → A3 → B1 → B2 → B3 → B4 → B5 → S8 → C1/...`, following the
state table and each act's `NEXT` (`00-ROUTER.md:21-30`; `A-source/A1-repo-screen.md:270-282`;
`A-source/A2-idea-generate.md:286-299`; `A-source/A3-idea-gate.md:239-254`;
`B-build/B1-scaffold.md:219-230`; `B-build/B2-contract.md:293-303`;
`B-build/B3-grader.md:309-321`; `B-build/B4-solution-env.md:245-256`;
`B-build/B5-preflight-push.md:279-289`).

**Result: FAIL. It stalls at entry, and later violates D2.**

1. The only state command is conditional on already having `<task>`. With no task, the router says
   only “you are in S0–S3”; it gives no command for distinguishing those four local states
   (`00-ROUTER.md:17-24`).
2. `A1` requires a supplied territory/lane, but the request supplies none; its checklist begins
   with an already-chosen candidate repo and never contains a repository-discovery command
   (`A-source/A1-repo-screen.md:5-8,245-268`). The agent must guess a lane or ask for data outside
   the promised protocol.
3. `A1` cannot honestly exit with one or two good repos: its header requires “≥3 ... or lane is
   dead”, while its own rule says to report `<3` rather than manufacture survivors
   (`A-source/A1-repo-screen.md:8,14-16`).
4. `A1` is ordered to fan out, but every lane mutates the same `/tmp/llc` clone with `git pull`, and
   its mandatory exit gate requires container work; the router makes a shared git index and all
   Docker work serial-only (`A-source/A1-repo-screen.md:36,43-49,247-266`;
   `00-ROUTER.md:158-179`). The included end-to-end run independently hit both contradictions
   (`.e2e/run-20260922T221320Z/friction.md:8-15,32-42`).
5. `B1` never gives the command that creates the task. Checklist item 1 merely asserts “Task dir
   created” and proves it with `ls`; the only mention of `codimango task init` describes its defects
   (`B-build/B1-scaffold.md:11-13,175-183`). A zero-context agent must invent the invocation.
6. More seriously, `B1` is Claude-owned yet requires creation of skeletons containing
   `steps/*/instruction.md`; that is a script-mediated protected-path write forbidden by D2
   (`B-build/B1-scaffold.md:4-8,19-36,181-214,219-227`; `00-ROUTER.md:119-129`).
7. B2's exit depends on `instruction-lint.py` before B3 has created a `test_patch`
   (`B-build/B2-contract.md:6-9,203-216,258-280`). The live tool explicitly returns only a WARN and
   exit 0 when no test patch exists, and tells the caller to rerun after B3
   (`/home/agvidit/.claude/skills/swebench-mt/instruction-lint.py:55-78,107-110,160-162`), but B3
   has no such rerun (`B-build/B3-grader.md:270-300`). Thus B2 can report its exit met after only
   half the D1 check.
8. After the first push, `S8` says “wait — see §3”, but §3 defines attempts and cache behavior; it
   has no polling, timeout, or resumption procedure (`00-ROUTER.md:29,69-77`). `B5` hands off to
   that non-act state (`B-build/B5-preflight-push.md:280-289`).

The intermediate HANDOFFs do name useful evidence, but they do not rescue the missing entry inputs,
scaffold command, ownership-safe creation path, or wait/resume path.

### W2 — existing task, `BAD_GRADING_WRONG` on step 2

**Result: FAIL. The router is ambiguous, and the short route lacks its required input.**

- The task simultaneously matches S9 (“any server verdict, not yet diagnosed”) and S12
  (`BAD_GRADING_WRONG`), but only Oracle has a stated priority rule (`00-ROUTER.md:30-42`).
- Following S12 opens `C2`, whose declared input is a **C1 diagnosis**. The handed task does not have
  that evidence, so `C2` must stall or guess (`C-drive/C2-repair-grading.md:4-10,253-258`).
- Following S9 opens `C1`, but `C1` orders the agent to open `C6` §§1–2 to download artifacts. That
  is a second act-file, contrary to the one-act contract (`C-drive/C1-read-verdict.md:72-79`;
  `00-ROUTER.md:6-8`).
- `C1` says an uncertain failure should be labelled `reasoning`, even though its own table defines
  `reasoning` as “the task did its job” and `task_defect` as the bucket that must be repaired. This
  can hide the exact false negative W2 is asking to fix (`C-drive/C1-read-verdict.md:119-138`).
- `C2` claims its output is already pushed and its exit already includes C6, yet checklist item 18
  requires C6 before item 19 commits, its HANDOFF routes to C6 only “if ... not run”, and C6 routes
  back to C2 to push (`C-drive/C2-repair-grading.md:7-10,251-294`;
  `C-drive/C6-replay-verify.md:241-253`). No pre-C6 handoff or suspended-act state is defined.

### W3 — “too easy — avocado passed 4 of 5”

**Result: FAIL. It reaches `C3` only by guessing state precedence, then cannot satisfy a
precondition without contradicting the cache rule.**

- The record matches both S9 and S14 unless it already carries a C1 diagnosis; the state table does
  not say which wins (`00-ROUTER.md:30,35`).
- If S14 is chosen, `C3` requires a second server read for a lone 0.8 before redesign
  (`C-drive/C3-harden.md:53-64,263-267`). The router says a same-SHA rerun returns the cached verdict
  and only a new commit triggers a new result, so there is no specified way to obtain an independent
  second read of the unchanged task (`00-ROUTER.md:71-77`).
- `C3` then has the same undocumented C6 suspension cycle as C2: its exit requires C6, its checklist
  requires a C6 verdict, but its final HANDOFF says to go to C6 only if replay has not run
  (`C-drive/C3-harden.md:3-18,154-162,261-296`; `C-drive/C6-replay-verify.md:241-253`).

### W4 — six `draft` tasks, drive all to green

**Result: FAIL. `C5` is not an unattended program and can spin or starve tasks.**

- The router's one command is `task show <task>`, which cannot discover that more than one task is
  in flight; `S17` needs the list command that appears only after C5 has already been selected
  (`00-ROUTER.md:17,39`; `C-drive/C5-cohort-loop.md:35-55`). S17 also overlaps every per-task state
  with no priority rule (`00-ROUTER.md:21-39`).
- “Run unattended” is followed by prose and shell fragments, not a driver that invokes acts,
  persists state, checks return codes, or maintains attempt counters
  (`C-drive/C5-cohort-loop.md:25-31,112-145,203-227`).
- “Blocked → run C1. That counts as one attempt” contradicts both the router's definition—only a
  completed diagnosis that produced a pushed commit counts—and C5 checklist item 11
  (`C-drive/C5-cohort-loop.md:126-133,219`; `00-ROUTER.md:69-73`). A literal implementation will
  double-count diagnosis-only passes or choose between conflicting rules.
- A stale SHA and “jobs still running” both sleep forever: there is no maximum poll age, job-terminal
  test, or dead-job transition (`C-drive/C5-cohort-loop.md:126-135,149-165`).
- Phase A rediscovers every task whose status is `draft`; a green task is merely skipped in the
  current wave, not persisted in an exclusion set. Re-running Phase A can rank the same green drafts
  ahead of tasks 4–6 indefinitely; parked-state persistence is also asserted but not implemented
  (`C-drive/C5-cohort-loop.md:35-55,97-110,129-145`).
- C5 says C1 “writes a plan and then executes it”, while C1 explicitly says it diagnoses and does
  not repair (`C-drive/C5-cohort-loop.md:25-28`; `C-drive/C1-read-verdict.md:11-14`).
- C5 requires commits to `.review/`, `ledger/RULES.md`, and `ledger/RUNS.md`, contradicting the
  router hard stop that commits may contain only `<task>/` paths
  (`C-drive/C5-cohort-loop.md:108-110,169-186,231-239`; `00-ROUTER.md:186-190`).

## 2. Conformance to the router contract

All 14 act-files contain text matching owner/input/output/exit and all end in a HANDOFF block. That
is only surface conformance. “One owner”, executable checklists, and declared boundaries fail as
shown below; the governing requirements are `00-ROUTER.md:196-216` and
`/tmp/pipeline-compare/MERGE-CONVENTIONS.md:43-48`.

| Act | Header / checklist / handoff | Substantive conformance |
|---|---|---|
| A1 | Present (`A-source/A1-repo-screen.md:5-8,245-282`) | Checklist is evidence-oriented, but lacks repository discovery, has an impossible ≥3-or-dead exit, and mixes parallel screening with mandatory shared-git/Docker work (`:14-16,36,253-266`). It also restates A3's naming filter (`:158-165`). |
| A2 | Present (`A-source/A2-idea-generate.md:5-8,265-299`) | Checklist is executable. Header names MetaCode and Codex roles, not one owner (`:5`), and §§4/6 restate the D1 naming rule, with a conflicting “enumerate every token” escape (`:124-140,224-238`). |
| A3 | Present (`A-source/A3-idea-gate.md:5-8,218-254`) | Strong executable gate checklist, but two owners are declared (`:5`). This legitimately owns the sourcing gate (`:28-43`), contradicting the router's statement that B2 is the only file stating the naming rule (`00-ROUTER.md:242-245`). |
| B1 | Present (`B-build/B1-scaffold.md:4-8,175-230`) | Checklist has receipts but no creation command; Claude-owned creation of instruction skeletons violates D2 (`:19-36,181-214`). Its 21-row landmine catalogue duplicates R3/B5 (`:81-121`). |
| B2 | Present (`B-build/B2-contract.md:4-9,258-303`) | Mostly executable, but its D1 clause and lint override admit a state A3 must reject (`:19-36,203-216`). Its exit-time lint can run only half its checks until B3 supplies tests, and B3 never reruns it (`/home/agvidit/.claude/skills/swebench-mt/instruction-lint.py:55-78,107-110`; `B-build/B3-grader.md:270-300`). `git status` before/after cannot prove which process authored prose (`B-build/B2-contract.md:287-290`). |
| B3 | Present (`B-build/B3-grader.md:4-10,264-321`) | Several checklist lines are assertions plus section references rather than a command/artifact (`:267-300`). It crosses its tests-only output boundary by instructing Codex to write/review the golden and mirror golden changes (`:215-240,282-290`). |
| B4 | Present (`B-build/B4-solution-env.md:4-7,199-256`) | Checklist is largely executable. Its declared output omits `README.md` and `audit/*`, although the act authorizes writes there (`:6,10-11`). It restates idempotency and top-level-config rules owned by R3 (`:111-133,163-195`). |
| B5 | Present; two checklists (`B-build/B5-preflight-push.md:4-8,204-260,279-289`) | Pre/post checks are mostly executable, but the “agentic-reviewer precheck” is a manual 17-row opinion table with no reviewer invocation (`:82-115,217-218`). Its cherry-pick path can write an Avocado-authored instruction through Claude's shell (`:151-163`). |
| C1 | Present (`C-drive/C1-read-verdict.md:5-8,253-299`) | Checklist is mostly “read/classify; see §” rather than a proving command/artifact (`:257-280`) and requires opening C6 while executing C1 (`:72-79`). |
| C2 | Present (`C-drive/C2-repair-grading.md:5-10,251-295`) | Header has Codex plus Claude write/dispatch duties, not one owner (`:5-6`). Checklist is largely references, and the C6-before-commit transition has no pre-C6 handoff (`:251-294`). |
| C3 | Present (`C-drive/C3-harden.md:5-10,261-297`) | Three owners are declared (`:5-6`); checklist mostly cites prose and contains the impossible “second server read” precondition (`:263-279`). C6 sequencing is circular (`:284-296`). |
| C4 | Present (`C-drive/C4-loosen-salvage.md:5-10,190-226`) | Three owners are declared (`:5-6`); checklist mostly cites prose rather than receipts (`:192-208`). Its C6 sequencing is circular (`:213-225`). |
| C5 | Present (`C-drive/C5-cohort-loop.md:5-8,203-243`) | The checklist describes a manual procedure rather than an unattended executable loop (`:203-227`), and the act writes/commits outside its task boundary (`:108-110,169-186,231-239`). |
| C6 | Present (`C-drive/C6-replay-verify.md:5-8,212-253`) | Two owners are declared (`:5`). The checklist names desired results but supplies no reconstruction or three-run commands (`:214-232`), and the supplied fallback is contaminated by the golden (`:150-168`). |

### Paraphrased rule duplication

The following are semantic duplicates the exact-sentence checker misses:

- **D1/naming:** A1 (`A-source/A1-repo-screen.md:158-165`), A2
  (`A-source/A2-idea-generate.md:124-140,224-238`), A3
  (`A-source/A3-idea-gate.md:28-43`), B2 (`B-build/B2-contract.md:19-36,115-146`), B3
  (`B-build/B3-grader.md:50-61,111-138,236-244`), C2
  (`C-drive/C2-repair-grading.md:41-53`), and C3 (`C-drive/C3-harden.md:22-43`) all state
  versions of the rule. B2 explicitly claims no other file does (`B-build/B2-contract.md:12-17`).
- **D2/ownership:** the rule is restated in the router (`00-ROUTER.md:115-152`), A2
  (`A-source/A2-idea-generate.md:14-19`), B1 (`B-build/B1-scaffold.md:81-92`), B2
  (`B-build/B2-contract.md:4-17`), B3 (`B-build/B3-grader.md:13-18`), B4
  (`B-build/B4-solution-env.md:10-12`), C1 (`C-drive/C1-read-verdict.md:40-43,159-162`),
  C2 (`C-drive/C2-repair-grading.md:13-20`), C3 (`C-drive/C3-harden.md:13-18`), C4
  (`C-drive/C4-loosen-salvage.md:17-19,124-135`), C5
  (`C-drive/C5-cohort-loop.md:25-28`), C6 (`C-drive/C6-replay-verify.md:230-232`), and R4
  (`reference/R4-ownership.md:32-75`). Drift is already visible: the router's weaker hard stop says
  only C1–C5, while its iron-clad section says every phase (`00-ROUTER.md:119-129,191`).
- **Scaffold/preflight traps:** B1's catalogue (`B-build/B1-scaffold.md:81-121`), R3's catalogue
  (`reference/R3-landmines.md:18-129`), and B5's list (`B-build/B5-preflight-push.md:55-68`)
  restate the same rules rather than placing mechanics in one owner.
- **Patch packaging:** B3 (`B-build/B3-grader.md:228-262`) and R3
  (`reference/R3-landmines.md:132-278`) both own sequential application, mirror drift, the top-level
  aggregate, and duplicate files.
- **Idempotency:** B4 restates the mechanism and remedy (`B-build/B4-solution-env.md:111-133`)
  that R3 owns (`reference/R3-landmines.md:118-129`).

The promised precedence mechanism is nonfunctional: README says every rule has a status and run
pointer (`README.md:35-42`), but `ledger/RULES.md` contains only empty tables
(`ledger/RULES.md:27-37`). The checker merely asks whether each act has any one status token
(`check-playbook.py:141-146`), not whether every rule is uniquely homed and anchored.

The merge's 120–300-line rule is also violated (`/tmp/pipeline-compare/MERGE-CONVENTIONS.md:60`):
B2 is 303 lines, B3 321, R5 375, R6 671, R7 732, and `ledger/RUNS.md` 1,012; README (64),
PROVENANCE (86), and RULES (37) are below 120. The large reference files are especially difficult
to use under the router's selective-reading design.

## 3. Content integrity against the sources

The merge contract required every n-count, rate, quotation, and named task to survive verbatim
(`/tmp/pipeline-compare/MERGE-CONVENTIONS.md:51-59`). The following spot checks fail that rule.

### Measured findings or named tasks missing from the merged set

| Missing source content | Why the loss matters |
|---|---|
| SWE-bench Pro Verified: **75 of 119** flagged tasks were “overly-narrow test” (`/tmp/pipeline-compare/ours/SKILL.md:59-64`) | B3 retains the two-way-contract rule but drops its external base rate (`B-build/B3-grader.md:13-21`). |
| The one-agent-per-task incident: two agents overwrote `instruction.md` **three times** and broke an oracle (`/tmp/pipeline-compare/ours/SKILL.md:73-75`) | The merged router permits several role-specific agents per task but supplies no task lease or equivalent exclusion mechanism (`00-ROUTER.md:168-182`). |
| `aasm`: step-1 trials moved **0/9 → 8/9** while the task regressed from 3/5 gates to 2/5 (`/tmp/pipeline-compare/peer/08-calibration-fixes-for-the-task.md:393-426`) | C5 ranks current cost but lost the composite-before/after rule that prevents trial-level improvement from hiding a lost gate (`C-drive/C5-cohort-loop.md:72-99,149-165`). |
| `open62541-numericrange-canonical-form-composition`: **1.0/1.0 → 0.4/0.8** (`/tmp/pipeline-compare/ours/runbooks/2-build.md:198-203`) | The merge keeps generic open62541 counts but not this exact discrimination result or full task name (`B-build/B2-contract.md:171-180`). |
| `net-imap-debug-log-secret-redaction`: two genuine **16/17** failures after three failed forks (`/tmp/pipeline-compare/ours/runbooks/2-build.md:239-246`) | The merge shortens this to “net-imap” and retains a different 17-test observation, losing both the named task and discriminator measurement (`reference/R2-signal-integrity.md:140-143`). |
| Exact named tasks `sparql-ruby-query-execution-budget`, `open62541-numericrange-canonical-form-composition`, and `franz-go-kadm-acl-authorization` plus their fork results (`/tmp/pipeline-compare/ours/runbooks/2-build.md:239-246`) | None of the exact slugs survives in the merged Markdown; this defeats the explicit named-task preservation requirement. |
| `ruby-auth0-lazy-token-init` at Avocado **5/5**, with the quoted over-specified prompt (`/tmp/pipeline-compare/ours/VAGUENESS-STYLE-REFERENCE.md:17-27`) | The general style rule survives, but this named counterexample and quotation do not (`B-build/B2-contract.md:148-185`). |
| PEER's explicit **40% across five trials** target (`/tmp/pipeline-compare/peer/02-claude-filter-ideas.md:1-8`) | The current format-specific server rule may supersede it operationally, but the number was dropped rather than retained with a superseded marker (`00-ROUTER.md:91-104`). |
| “Step 2's spec must be self-contained” and “No ‘deferred to Step 2’ language in step 1” (`/tmp/pipeline-compare/peer/01-avocado-ideas-brainstorming.md:142-150,161-170`) | Neither rule appears in B2's contract/checklist (`B-build/B2-contract.md:19-56,258-290`). Three independent included e2e runs hit this omission (`.e2e/pair-frostdb/friction.md:8-15`; `.e2e/pair-oxigraph/friction.md:8-16`; `.e2e/pair-santuario/friction.md:90-97`). |

### Altered or falsely re-dated material

- A source deliverable of **5–7 ranked repos** became an unproven **≥3 repos per lane** exit
  (`/tmp/pipeline-compare/ours/runbooks/1-brainstorm.md:30-41`;
  `A-source/A1-repo-screen.md:5-8`). This is not marked as a new mechanism or a supersession.
- A1 preserves “16 days behind” from the source (`/tmp/pipeline-compare/ours/runbooks/1-brainstorm.md:1108-1117`)
  while marking the section measured on 2026-09-22 (`A-source/A1-repo-screen.md:40-44`). The included
  live run measured the same corpus as **20 days stale** and found `git pull` could not refresh it
  (`.e2e/run-20260922T221320Z/friction.md:17-30`). The digits were copied but their date-qualified
  meaning was altered.
- C3 quotes the router as format-agnostic and says it applies a ≤3/5 ceiling to single-turn
  (`C-drive/C3-harden.md:69-81`), while the current router explicitly says the rules differ and a
  single-turn 4/5 can pass (`00-ROUTER.md:91-104`). This marker contains a stale internal quotation.

I found no other source number whose digits I could confidently say were silently changed; most
sampled figures were either preserved exactly or omitted wholesale.

### Rules retained without their measurement

- B3 states the two-way grading contract without the source's **75/119** overly-narrow-test
  measurement (`B-build/B3-grader.md:13-21`;
  `/tmp/pipeline-compare/ours/SKILL.md:59-64`).
- C5 says gate movement matters but omits the composite ordering and its `aasm 0/9 → 8/9 yet
  REGRESSED` evidence (`C-drive/C5-cohort-loop.md:149-165`;
  `/tmp/pipeline-compare/peer/08-calibration-fixes-for-the-task.md:393-426`).
- The router's multi-agent task flow omits the only measured collision rule—two agents, three
  instruction overwrites, one broken oracle (`00-ROUTER.md:168-182`;
  `/tmp/pipeline-compare/ours/SKILL.md:73-75`).

### Invented, unmarked content

- `A1` claims “3+ lanes proven safe” and requires ≥3 surviving repos per lane, but neither source
  contains that threshold; the closest source says never manufacture a survivor and asks for a
  global 5–7-repo shortlist (`A-source/A1-repo-screen.md:5-16`;
  `/tmp/pipeline-compare/ours/runbooks/1-brainstorm.md:30-41`).
- `A2` introduces a “≥8 dispatch target” despite simultaneously saying a fixed count causes padding
  and zero is valid (`A-source/A2-idea-generate.md:5-8,47-60`). No source occurrence of that target
  was found, and it is not marked as a new mechanism.
- `A1` turns the presence of `.claude/`, `CLAUDE.md`, `AGENTS.md`, or a Claude CI action into a
  whole-repository hard kill (`A-source/A1-repo-screen.md:23-34,68`). The source says those artifacts
  are a contamination oracle and only the work they cover is burned; ideate from code they do not
  mention (`/tmp/pipeline-compare/ours/runbooks/1-brainstorm.md:1227-1238`).
- C4 cites an unnamed operator-ledger incident in which nine failures were “the entire difficulty”,
  but supplies no RUNS anchor despite the ledger rule requiring one (`C-drive/C4-loosen-salvage.md:80-90`;
  `ledger/RULES.md:20-23`). I am unsure whether the incident exists outside the supplied sources;
  inside the audited inputs it is untraceable.

The C5 learning write-back is not an integrity violation because it is explicitly labelled as absent
from both sources (`C-drive/C5-cohort-loop.md:169-172`), although its commit scope is separately
wrong.

## 4. Iron-clad rule: adversarial audit

The governing rule forbids direct and indirect writes in every state (`00-ROUTER.md:119-129`). I
found three definite write paths and one underspecified landing path.

1. **Definite — Claude creates protected paths in B1.** B1 is Claude-owned and its output is the
   task directory; the required layout contains each instruction file, and its checklist requires
   every such file to exist (`B-build/B1-scaffold.md:4-8,19-36,181-214`). Running a generator that
   creates those files is exactly the script-mediated write D2 forbids
   (`00-ROUTER.md:126-129`). The claimed proof—`git status` empty—is also incompatible with newly
   created/untracked scaffold files and cannot prove process authorship (`B-build/B1-scaffold.md:194-200`).
2. **Definite — B5's update path instructs Claude to cherry-pick a task commit.** “Cherry-pick only
   your commit ... then push from there” can materialize the Avocado-authored instruction in the
   throwaway worktree (`B-build/B5-preflight-push.md:151-163`). R4 explicitly classifies
   cherry-picking a commit touching the protected file as a violation and says the human must do
   that push (`reference/R4-ownership.md:52-62`).
3. **Definite — the violation-remediation procedure itself writes the protected file.** C2 tells
   Claude to capture and then revert an illicit instruction edit (`C-drive/C2-repair-grading.md:219-228`),
   while R4's executable checklist literally runs `git checkout -- '<task>/.../instr*.md'`
   (`reference/R4-ownership.md:119-160`). D2 has no remediation exception; R4 itself says the shell
   performing a write is what counts (`reference/R4-ownership.md:20-28,52-62`). The safe playbook
   action can only be stop/capture/hand off to an authorized writer.
4. **Ambiguous — no ownership-safe landing step in B2.** Claude sends `mc.sh` an `<out-file>`, but the
   checklist jumps directly to “instruction.md exists” without saying that MetaCode itself wrote the
   protected path (`B-build/B2-contract.md:38-56,262-280`). If `<out-file>` is scratch, Claude must
   copy it (violation); if it is the instruction path, that should be explicit and attributed to the
   MetaCode process. The same ambiguity applies to C3's Avocado rewrite dispatch before a Claude
   push (`C-drive/C3-harden.md:131-138,189-202,284-296`).

The prose-only repair stops themselves are sound: C1 makes `FIX spec` a report owned by
Avocado/human (`C-drive/C1-read-verdict.md:146-162`), and C4 makes contract rungs reports rather
than actions (`C-drive/C4-loosen-salvage.md:124-153`). The defect is in the surrounding filesystem
and git mechanics, not those stops.

There is also dangerous rule drift: R4 says B2 is the only act where instruction prose is written
(`reference/R4-ownership.md:41-50`), README says MetaCode owns it “only during B2”
(`README.md:44-52`), but C3 expressly authorizes Avocado contract rewrites
(`C-drive/C3-harden.md:85-98,131-138`). D2 permits Avocado in every phase; the two narrower copies
can make a compliant agent stop or reroute unpredictably.

## 5. The loop and replay harness

### C5 unattended operation

`C5` is **not runnable unattended**. It is an operator recipe with a discovery snippet and a
five-line narrative loop, not an executable driver (`C-drive/C5-cohort-loop.md:35-55,112-145`).

It can:

- **spin** on a stale `commitSha` or a job that never becomes terminal because both branches sleep
  forever with no maximum age or terminal-job check (`C-drive/C5-cohort-loop.md:126-135,149-165`);
- **double-count** because it says entering C1 is an attempt while both its own checklist and the
  router say only a pushed commit increments the count (`C-drive/C5-cohort-loop.md:129-133,219`;
  `00-ROUTER.md:69-73`);
- **starve/drop tasks** because a green task can remain `draft`, be rediscovered on every Phase A,
  and consume the next closest-to-done wave again; the “do not re-enter” parked set has no persisted
  representation or filter (`C-drive/C5-cohort-loop.md:35-55,79-110,138-145`);
- **lose state on restart** because the log is prose and no command reads it back to reconstruct the
  attempt/park sets (`C-drive/C5-cohort-loop.md:190-199,231-243`);
- **perform the wrong act** because it claims C1 executes its plan, contrary to C1's diagnosis-only
  boundary (`C-drive/C5-cohort-loop.md:25-28`; `C-drive/C1-read-verdict.md:11-14`).

The included end-to-end runs expose two further runnable-path gaps: A2's LOC and subsystem formulas
can prescribe incompatible survey sizes with no general tie-break (`.e2e/pair-frostdb/friction.md:36-47`),
and the Java recipe omits the proxy stanzas and `docker run --network=host` required by its own
tested environment (`A-source/A1-repo-screen.md:214-218`;
`.e2e/pair-santuario/friction.md:8-61`).

### C6 replay mechanics

`C6` describes the idea but is not sufficient to perform a trustworthy replay:

- Artifact listing says “filter” only in a comment and offers two CLI spellings with “use whichever
  ... accepts”; there is no command that selects the exact prior commit/model/trial
  (`C-drive/C6-replay-verify.md:20-35`).
- Reconstruction says “take the last write” from a transcript but provides no extractor, checkout,
  application order, or multi-file materialization command; it concedes passed implementations are
  often unrecoverable (`C-drive/C6-replay-verify.md:97-124`).
- The three required runs are only a result table. No command constructs the pre-change suite or
  runs the same verifier environment against both versions (`C-drive/C6-replay-verify.md:126-138`).
- The only runnable fallback first applies `solution/solve.sh`, then overwrites a single `<path>`
  with `<impl>`. A multi-file agent implementation therefore inherits every untouched golden change
  and is not a replay of that agent (`C-drive/C6-replay-verify.md:150-168`).
- `/tmp/replay/<arm>` is not task-scoped and can collide during the parallel artifact downloads the
  router permits (`C-drive/C6-replay-verify.md:28-32,247-250`; `00-ROUTER.md:163-166,178`).
- C6 permits an `UNPROVEN` assertion to be pushed “if you choose”, contrary to the router's
  mandatory real-prior-trajectory check (`C-drive/C6-replay-verify.md:200-208`;
  `00-ROUTER.md:218-225`).

### Do C2, C3, and C4 exit through C6?

**Textually yes; operationally no.** Each declares C6 in its exit and/or checklist
(`C-drive/C2-repair-grading.md:9-20,232-277`; `C-drive/C3-harden.md:9-18,154-162,261-279`;
`C-drive/C4-loosen-salvage.md:9-19,175-208`). But each final HANDOFF says `C6 (if ... not run)`,
while C6 sends control back to the calling act (`C-drive/C2-repair-grading.md:282-295`;
`C-drive/C3-harden.md:284-297`; `C-drive/C4-loosen-salvage.md:213-226`;
`C-drive/C6-replay-verify.md:241-253`). Under “one act, emit HANDOFF, stop”, the files need an
explicit proposed-change handoff to C6 and a resumption state; neither exists
(`00-ROUTER.md:6-8,203-216`).

## 6. Checklist quality

The router requires each line to have a proving command or artifact (`00-ROUTER.md:196-201`).

| Required checklist | Location | Verdict |
|---|---|---|
| Repo finding | `A-source/A1-repo-screen.md:245-268` | **Substantive but blocked.** Most rows have receipts; it lacks candidate discovery and conflicts with parallelism/exit semantics. |
| Task ideation | `A-source/A2-idea-generate.md:265-285` | **Executable.** Each row names an artifact or command, though the fixed ≥8 target is unsupported. |
| Multiple task creation | No dedicated checklist; only orchestration prose at `00-ROUTER.md:168-182` | **Missing.** C5 starts after tasks already exist (`C-drive/C5-cohort-loop.md:5-8`); B1 has no multi-task queue/checkpoint procedure. |
| Steps validation | Split across B1 item 10 (`B-build/B1-scaffold.md:201-214`), B2 item 12 (`B-build/B2-contract.md:281-290`), B3 item 19 (`B-build/B3-grader.md:291-300`), B4 item 13 (`B-build/B4-solution-env.md:230-240`), and B5 item 11 (`B-build/B5-preflight-push.md:227-232`) | **Executable fragments, not one owned checklist.** The duplication makes responsibility and final proof unclear. |
| Pre-submission | `B-build/B5-preflight-push.md:204-233` | **Genuinely executable**, except item 6 relies on the non-runnable reviewer precheck. |
| Post-submission | `B-build/B5-preflight-push.md:237-260` | **Executable but incomplete.** It confirms pickup/job creation/structural status only, then routes to an undefined wait state rather than through final verdict (`:274-288`). |
| Validations | B4 local oracle (`B-build/B4-solution-env.md:199-241`) plus B5 pre/post checks (`B-build/B5-preflight-push.md:204-260`) | **Mostly executable, fragmented.** There is no single receipt proving all five done surfaces from their authoritative sources (`00-ROUTER.md:81-111`). |
| Agentic-reviewer precheck locally | `B-build/B5-preflight-push.md:82-115,217-218` | **Thin.** It asks the author to opine PASS/AT-RISK on 17 rows; it gives no local reviewer command, prompt, output schema, or artifact path. |
| Reviewer-feedback check | `C-drive/C1-read-verdict.md:253-280` | **Thin.** Only item 1 carries a full command; most lines point to prose/another act, and artifact download requires opening C6. |
| TBR fix | `C-drive/C2-repair-grading.md:251-278` | **Thin.** It is numbered, but most items are assertions or section references without the proving command/artifact the router requires. |

`C3`, `C4`, `C5`, and `C6` have the same checklist defect: their lines mostly name desired facts or
sections rather than copy-pasteable proofs (`C-drive/C3-harden.md:261-280`;
`C-drive/C4-loosen-salvage.md:190-209`; `C-drive/C5-cohort-loop.md:203-227`;
`C-drive/C6-replay-verify.md:212-233`).

## 7. Open conflicts

The checker's count of ten is a raw string count, not ten conflicts (`check-playbook.py:154-159`).
It counts the ledger's explanatory sentence, A1's table/header/handoff repetitions, and three copies
of the top-level-config conflict (`ledger/PROVENANCE.md:68-79`;
`A-source/A1-repo-screen.md:29,175-193,280`; `C-drive/C2-repair-grading.md:88-96`;
`B-build/B4-solution-env.md:163-195`; `reference/R3-landmines.md:79-89`). There are five semantic
markers:

| Conflict | Both positions and sources? | Can current repo evidence resolve it? |
|---|---|---|
| Licence | **Yes** at the canonical site: two OURS positions, external policy, and PEER are cited (`A-source/A1-repo-screen.md:175-193`). The table and HANDOFF occurrences merely point to it (`:29,280`). | **No.** The playbook contains conflicting policy evidence, not an authoritative current legal ruling (`:180-190`). |
| Top-level MT `tests/config.json` | **Yes**, independently and redundantly, in B4, C2, and R3 (`B-build/B4-solution-env.md:163-195`; `C-drive/C2-repair-grading.md:88-96`; `reference/R3-landmines.md:79-89`). | **Partly.** Real identity fields are resolved by the 16-task eval-GT failure; whether aggregate `patch`/`test_patch` must be non-empty is not settled by a schema verdict (`B-build/B4-solution-env.md:172-195`). Keep only that narrow remainder open. |
| Step patch: cumulative vs sequential delta | **Yes**: stale PEER 07, correcting PEER 05, and independent OURS are all cited (`B-build/B3-grader.md:246-262`). | **Yes: sequential composition/delta.** PEER 05 explicitly corrects PEER 07, OURS agrees, and the executable gate is ordered plain `git apply` (`:250-258`). The stale statement should be historical, not unresolved. |
| Single-turn ≤3/5 ceiling | It names both positions, but one source attribution is stale: it quotes a format-agnostic current router that no longer exists (`C-drive/C3-harden.md:69-81`). | **Yes: format-specific.** The router and R1 now carry the verbatim single-turn pass rule, including the passing 4/5 example (`00-ROUTER.md:91-104`; `reference/R1-field-authority.md:255-261`). |
| Solution ownership | **Yes**: the PEER/OURS assignments are cited (`reference/R8-finding-to-file.md:156-161`). | **Already resolved** to Claude for `solution/*` by the router (`00-ROUTER.md:142-149`). A marker literally saying “UNRESOLVED ... SETTLED HERE” is self-contradictory and should not count as open. |

`ledger/PROVENANCE.md` lists only licence, top-level config, and step patch
(`ledger/PROVENANCE.md:68-79`); it omits the single-turn and solution-ownership markers. Conversely,
three copies of the top-level-config conflict violate the no-duplication rule while increasing the
checker's count.

## 8. Ranked defects

### Blocking

1. **D2 is violated by the Claude-owned scaffold creating protected instruction skeletons.**
   `B-build/B1-scaffold.md:4-8,19-36,181-214` — **Fix:** make the authorized Avocado/human create
   those files, or make B1 create only directories/non-protected files and hand off missing paths.
2. **D1 has an escape after the sourcing gate, and its lint is sequenced before it can check D1.** B2 permits a new grader-pinned name and an A3
   override, while A3 says any such candidate is rejected; A2 also permits enumerating coined
   vocabulary (`A-source/A3-idea-gate.md:28-43`; `B-build/B2-contract.md:19-36,203-216`;
   `A-source/A2-idea-generate.md:224-238`). Before B3, the lint deliberately cannot inspect
   `test_patch`, returns 0 after a warning, and B3 does not rerun it
   (`/home/agvidit/.claude/skills/swebench-mt/instruction-lint.py:55-78,107-110,160-162`;
   `B-build/B3-grader.md:270-300`) — **Fix:** remove the authoring-time escape, route any absent-name
   dependency back to A3 rejection/name-agnostic redesign, and run the full paired lint after B3.
3. **The router cannot determine its advertised states in one command and has overlapping routes.**
   `00-ROUTER.md:6-8,17-42` — **Fix:** provide one deterministic state script/query and an explicit
   priority order, including S17 and undiagnosed-before-specific-verdict precedence.
4. **Direct verdict routes skip C1 although C2 requires its diagnosis.**
   `00-ROUTER.md:30-36`; `C-drive/C2-repair-grading.md:7-10` — **Fix:** route every undiagnosed
   verdict to C1, then use C1's HANDOFF to select C2/C3/C4.
5. **C6 cannot faithfully replay an implementation and its fallback is golden-contaminated.**
   `C-drive/C6-replay-verify.md:97-168` — **Fix:** provide exact commands to materialize every last
   agent write in a clean base checkout and run old/new verifier trees; never run gold before laying
   down the complete candidate implementation.
6. **C2/C3/C4↔C6 has no executable handoff protocol.** `00-ROUTER.md:203-225`;
   `C-drive/C2-repair-grading.md:251-294`; `C-drive/C3-harden.md:261-296`;
   `C-drive/C4-loosen-salvage.md:190-225`; `C-drive/C6-replay-verify.md:241-253` — **Fix:** define a
   candidate-change handoff/state, let C6 emit its verdict, then resume a distinct commit step.
7. **C5 is not unattended and its attempt rules conflict.**
   `C-drive/C5-cohort-loop.md:25-31,112-145,203-227`; `00-ROUTER.md:69-73` — **Fix:** supply an
   executable state machine with persisted attempts/parked/done sets, terminal-job detection,
   bounded polling, and pushed-commit-only counting.
8. **C5 can repeatedly rediscover green drafts and starve later tasks.**
   `C-drive/C5-cohort-loop.md:35-55,79-110,129-145` — **Fix:** persist and filter terminal green and
   parked task IDs independently of server `draft` status.
9. **The violation-remediation and cherry-pick procedures can write protected prose through
   Claude's shell.** `B-build/B5-preflight-push.md:151-163`;
   `reference/R4-ownership.md:52-62,119-160`; `C-drive/C2-repair-grading.md:219-228` — **Fix:** stop
   after capture and hand every protected-path checkout/cherry-pick/landing operation to
   Avocado/human.
10. **D3 is not implemented end to end.** The requirement says the playbook is a git repo and the
    old skill becomes a pointer (`ledger/PROVENANCE.md:60-66`), but `git log -1 --oneline` reports
    no commits and `git status --short` reports the entire playbook untracked; the old skill remains
    a 174-line standalone playbook, not a pointer (`/home/agvidit/.claude/skills/swebench-mt/SKILL.md:1-14,79-104`).
    **Fix:** make an initial history-bearing commit and replace the legacy skill with a minimal
    pointer through an authorized change.
11. **C1's uncertainty default hides grading defects as reasoning failures.**
    `C-drive/C1-read-verdict.md:119-138` — **Fix:** use `UNRESOLVED`/manual-review on uncertainty;
    never map uncertainty into the only bucket counted as legitimate difficulty.
12. **A1's entry/exit and concurrency rules make W1 impossible for common valid outcomes.**
    `A-source/A1-repo-screen.md:5-16,36,245-266`; `00-ROUTER.md:158-179` — **Fix:** supply lane
    discovery, allow 0–N survivors as a complete exit, refresh shared data once, and queue G10.
13. **Two required multi-turn contract rules were dropped.** B2 lacks self-contained step-2 prose
    and the ban on “deferred to Step 2” language (`/tmp/pipeline-compare/peer/01-avocado-ideas-brainstorming.md:142-150,161-170`;
    `B-build/B2-contract.md:19-56,258-290`) — **Fix:** add both to B2's owned contract checklist,
    preserving their source language and rationale.

### Degrading

1. **The checker accepts semantic nonconformance and reports 0 failures.**
   `check-playbook.py:37-55,100-152` — **Fix:** parse real header/HANDOFF blocks, checklist rows and
   receipts, state transitions, ownership/path verbs, and semantic rule IDs rather than substrings.
2. **Rule duplication has already drifted.** D1, D2, scaffold, packaging, and idempotency are copied
   across the files cited in §2, despite the single-owner rule (`00-ROUTER.md:238-266`) — **Fix:**
   assign stable rule IDs to one home and replace copies with links.
3. **The precedence ledger is empty.** `README.md:35-42`; `ledger/RULES.md:27-37` — **Fix:** populate
   it with every live/scoped/superseded rule and a real RUNS anchor before relying on it.
4. **Required checklists are missing or thin.** Multiple-task creation is absent; local agentic
   precheck is unactionable; reviewer-feedback/TBR/C3–C6 lists are prose with numbers
   (`B-build/B5-preflight-push.md:82-115,217-218`;
   `C-drive/C1-read-verdict.md:253-280`; `C-drive/C2-repair-grading.md:251-278`;
   `C-drive/C3-harden.md:261-280`; `C-drive/C6-replay-verify.md:212-233`) — **Fix:** give each line a
   command or named output artifact and one owner.
5. **The post-submit wait has no executable resume condition.** `00-ROUTER.md:29,69-77`;
   `B-build/B5-preflight-push.md:237-288` — **Fix:** define bounded polling, terminal states, and the
   exact command that re-enters C1.
6. **Source evidence was dropped, including named tasks and decisive rates.** See §3 and
   `/tmp/pipeline-compare/MERGE-CONVENTIONS.md:51-54` — **Fix:** restore each exact measurement at
   the rule it justifies or preserve it as a clearly linked evidence appendix.
7. **Resolvable conflicts remain marked open, and one resolved conflict is counted as unresolved.**
   `B-build/B3-grader.md:246-262`; `C-drive/C3-harden.md:69-81`;
   `reference/R8-finding-to-file.md:156-161` — **Fix:** resolve step patches to sequential
   composition, use the router's format-specific gate, and relabel solution ownership resolved.
8. **The corpus freshness statement is stale and falsely date-qualified.**
   `A-source/A1-repo-screen.md:40-44`; `.e2e/run-20260922T221320Z/friction.md:17-30` — **Fix:** record
   actual HEAD age and treat the unrefreshable window as UNKNOWN covered by live search.
9. **The 120–300-line merge constraint is not enforced.**
   `/tmp/pipeline-compare/MERGE-CONVENTIONS.md:60`; `check-playbook.py:18-35,154-166` — **Fix:** add a
   size check or explicitly exempt ledgers, then split B3/R5/R6/R7 at true ownership boundaries.
10. **A2's two sizing calculations have no complete tie-break.**
    `A-source/A2-idea-generate.md:47-60`; `.e2e/pair-frostdb/friction.md:36-47` — **Fix:** define the
    formula for both directions of LOC/subsystem disagreement and remove the incompatible ≥8 target.
11. **The Java harness recipe is incomplete for the measured host.**
    `A-source/A1-repo-screen.md:214-218`; `.e2e/pair-santuario/friction.md:8-61` — **Fix:** include
    the required proxy stanzas and apply host networking consistently to build and run.

## Bottom line

The merged set contains much of the source knowledge, but it is not yet a dispatchable state
machine. A compliant zero-context agent cannot enter W1, cannot choose unambiguously in W2/W3,
cannot run W4 unattended, and cannot establish the real-trajectory proof required by C6. The D1
escape and D2 write paths are correctness/provenance blockers, not editorial defects
(`A-source/A3-idea-gate.md:28-43`; `B-build/B1-scaffold.md:4-8,19-36`;
`C-drive/C6-replay-verify.md:97-168`).

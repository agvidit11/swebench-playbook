# RULES — every live rule, its status, and the run that produced it

This is the **precedence channel**. Both source pipelines rotted the same way: a rule was
corrected in one file and left standing in another, with no marker saying which was current.
Peer's stage 07 still mandated cumulative patches that stage 05 had retracted; our
`2-build.md` carried five contradictory naming rules, two of which each declared the *other*
superseded. Nothing in either set let a reader tell which was live.

## Format

```
RULE-<nnn> | <LIVE | SUPERSEDED-BY RULE-<nnn> | SCOPED-TO <case>> | <file it lives in> | run=<RUNS.md anchor>
  <one sentence>
```

## Discipline

- A rule lives in **exactly one** act-file. This ledger records its status and provenance; it
  does not restate the rule's content beyond one sentence.
- When a wave in `C5` produces a finding that contradicts a rule, flip the old rule to
  `SUPERSEDED-BY` **in the same commit** that adds the new one. Never leave both `LIVE`.
- `run=` must point at a `RUNS.md` anchor with the measurement behind it. A rule with no run
  is a prior, not a rule — mark it `SCOPED-TO unvalidated` and say so at its site.
- **Repeated retellings of one incident are one data point.** Both source sets failed this:
  evidence volume read as evidence count. If two rules cite the same run, say so.

## Live rules

| id | status | home | evidence | rule |
|---|---|---|---|---|
| R-001 | LIVE | `00-ROUTER.md` §5 | provenance retires tasks by path | Claude and Codex never write `instruction.md`, in any phase, including indirectly |
| R-002 | LIVE | `B1` §0 | — | the scaffold tool may create the EMPTY placeholder; the first byte of content must be Avocado's |
| R-003 | LIVE | `B2` | PEER 4/4 `BAD_GRADING_WRONG` | D1: a new name the graded tests PIN must be named; a name they ignore never is |
| R-004 | LIVE | `A3` GATE 0 | corpus | a coined token needs a recorded `gate0-override.md`, or the candidate is rejected |
| R-005 | LIVE | `B3` §④ | dropshot 6 tests / 0 partial rows → 5/5; object-rs 14 tests / 1 branch → in band | **branch count ≥3**, not test count, is what discriminates |
| R-006 | LIVE | `A2` §3b | n=23,524 | two steps (+10.4pp in band, 5/5 risk ÷2.4); step 1 must carry real difficulty (81% of "too easy" blame) |
| R-007 | LIVE | `00-ROUTER.md` §3b | connect-go = L0 | the quality ladder; **L1 is the floor and excludes calibration** |
| R-008 | LIVE | `B5` GATE ZERO | connect-go R06/R07/R12 all pre-stated in its review | zero `OPEN` findings in the review ledger, or no push |
| R-009 | LIVE | `R9` | — | a finding is `OBSOLETE-BY-PIVOT` only if the artifact **and** the requirement are gone |
| R-010 | LIVE | `B3` §①②③ | connect-go `BAD_GRADING_WEAK` | contract-domain enumeration · golden-vs-contract differential · tested-cases-only mutant |
| R-011 | LIVE | `B5` | connect-go oracle 2/3, local 3/3 ×4 | p2p flake screen, in the tree the verifier will use |
| R-012 | LIVE | `A3` GATE 1 pf4 | frostdb 9/10 fork, 0/5 outcome | observational equivalence — if the grader cannot see the difference, variance is zero by construction |
| R-013 | LIVE | `A3` GATE 3 | lego PR #1334 revert | function-scoped `git log -L`; branch sweep; `--comments`; JIRA where the tracker lives |
| R-014 | LIVE | `A3` GATE 3 | — | disclosure splits by WHAT: symptom public is fine, cause or remedy kills |
| R-015 | LIVE | `A1` §9 | cloudnative-pg 10,962 LOC low-churn → 12 of 17 premises "under-20-line" | screen the PRODUCT of size and churn, not each separately |
| R-016 | LIVE | `A1` §9a | 4 measured | four silent-lie gates: 404 slug reads clean · `gh api` presence reads present · `SUB=` returns 0 · churn passes absent paths |
| R-017 | LIVE | `A2` §3a | TODO 3 lines from the defect | an in-code admission is a premise receipt AND disqualifying for a SEARCH card |
| R-018 | LIVE | `B2` §6b | mechanism stripped → fork 1, 5/5 again | vagueness does not create difficulty |
| R-019 | LIVE | `A3` §0a | 55.9% base, 5.8% at 5/5, ~17 kills / 0 tasks | this act disqualifies what is dead; it does not predict the band |
| R-020 | LIVE | `00-ROUTER.md` §3 | — | the rerun budget caps `task rerun` on an unchanged SHA; it does not ration pushes |

## Superseded

| id | superseded by | why |
|---|---|---|
| S-001 `semantic_bugs` **7 passed / 7**, "the best category there is" | R-019 | **49.6% at n=268**, statistically *below* the 55.9% base. The original was a ~20-task draw from a 55% base — noise promoted to a rule, then cited in five files. |
| S-002 `expose_interface` **1 passed / 13**, "most become unwritable" | R-019 | **52.1% at n=647**. The implied 7.7% is outside the 95% CI by 6×. |
| S-003 "0/5 costs as much as 5/5" | R-007 | 0/5 accepted **81.2%**, 5/5 accepted **45.5%**. Every 0/5 passed the current single-turn gate; every failure was over-ceiling. |
| S-004 fork ≤2 is an absolute veto | R-005 | Three independent lines: population (contract text predicts nothing), 51-trial forensics (no DESIGN primary label), and one dissection — a QUALITY premise *cannot clear GATE 5 by construction*. Cost ~17 candidates. |
| S-005 fork ≤2 vetoes UNLESS GATE 4 is in band | S-004 | Falsified on its first test: connect-go had GATE 4 3/5 local and returned **avocado 5/5**. Superseded twice — first restored as absolute, then demoted entirely. |
| S-006 SEARCH-framing beats BUILD-framing | R-019 | 56.8% vs 55.8%, n=2,565 vs 20,953. Right sign, negligible size. |

**Note on S-005.** It was introduced and falsified inside six hours, by an argument rather than a
measurement — in a file that already said reopening the veto required *"paired local-vs-server data
on ≥3 fork-1 candidates, not an argument."* That is the failure mode this ledger exists to make
visible: a rule changed twice in a night is a rule nobody can rely on.

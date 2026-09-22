# CHECKPOINT — pair-frostdb

**Last updated:** run COMPLETE. `A3` exited NO SURVIVOR. `DONE` written.

## Where I am

- **Final state:** `A2` complete → `A3` complete with **EXIT: NO SURVIVOR**.
  `B1`–`B5` were never entered, correctly: there is nothing to scaffold.
- **Not `PUSH-READY`.** No task directory exists. Nothing was committed, staged
  or pushed anywhere.
- **Run dir:** `/home/agvidit/swebench-playbook/.e2e/pair-frostdb/`

## The result in one line

frostdb is clean (0 peers, 0% AI-authored, 8 open issues, 0.084 s graded subset)
and yields **no buildable multi-turn task**: both candidates measured **Fork 1**
(10/10 and 10/10 on the desired path across two phrasings each) and the leading
one measured **5/5 outcome variance** against a real graded assertion.

## Fixed facts (do not re-derive)

| | |
|---|---|
| repo | `polarsignals/frostdb`, Go, Apache-2.0 |
| clone (mine, task-scoped) | `/tmp/frostdb-run/frostdb` — left `git status --porcelain` EMPTY |
| shared screening clone (never dirtied) | `/tmp/shortlist-data/clones/frostdb` |
| `base_commit` / HEAD | `9e5cfe0171adff531d30a9df3e111686996f4a9f` |
| non-test LOC | 45,247 |
| open issues | 8 (#916 #886 #879 #872 #769 #548 #433 #207) |
| peer tasks | **0**, re-verified first-hand (corpus + live `gh search code`) |
| AI authorship | 0/954 commits (from shortlist) |
| `go build ./...` | 6.0 s warm |
| `go test ./index/...` | 0.084 s · root package suite 6.1-6.7 s |
| known-flaky | `Test_Sampler_Randomness` `query/physicalplan/sampler_test.go:152` fails at HEAD |

## Task-scoped /tmp paths (all under `/tmp/frostdb-run/`, no generic names)

`frostdb` (clone) · `baseline` (assertion validation at base) ·
`impl-1`…`impl-5` (the five GATE-4 implementations, patches archived to
`probes/gate4-impl-N.patch`) · `survey.txt` · `survey-mc.out` ·
`survey-codex.md` · `cards.txt` · `cards-mc.out` · `probes/` ·
`/tmp/llc/tmp/tasks` (shared peer corpus, read-only)

## Dispatches in flight

**None.** All completed: 2 surveys (MetaCode 49,601 B; Codex 43,155 B), 1 card
pass (MetaCode 27,149 B), 20 fork probes, 5 implementation runs.

## Docker lock

**Never held.** Nothing in this run spawned Docker — `A2` and `A3` are
clone/read/probe only, and the run stopped before `B4`.

## What is DONE, with evidence

| | Evidence |
|---|---|
| `A2` complete, 2 cards from 31 surfaces | `handoffs/01-A2.md`, `cards/`, `notes/` |
| `A3` complete, no survivor | `handoffs/02-A3.md`, `probes/` |
| GATE 0 namability, both cards | token tables in `handoffs/02-A3.md`; **0 coined tokens each**, no `gate0-override.md` needed |
| GATE 2 executed at base (not grepped) | C1: `Persist() err = multiple sinks not supported`, sink a 1274 B / sink b 0 B. C2: `aggregate field(s) not found []string{"value + timestamp"}` |
| GATE 3 disclosure, 6 queries each | counts in the handoff; C2 hard-killed by PR #307's "disabled by default … most likely some latent bugs" |
| GATE 4 outcome variance, C1 | **5/5** pass `probes/gate4_assert_test.go`; all 5 also pass the repo's root suite; assertion pre-validated at base as 3-fail/1-pass |
| GATE 5 fork probes, ×2 phrasings, step 2 | C1 **10/10** desired path, C2 **10/10** desired path; 20 outputs in `probes/gate5-*.out` |
| friction log | `friction.md`, F1-F16, tagged `REPEAT:` / `EARLIER:` / `WASTE:` / `PINPOINT:` |

## Decisions made, with the reason — do not relitigate

1. **Authorship:** all generative work (surfaces, merges, contracts, cards,
   self-audits) was done by MetaCode (A2's declared owner) and Codex (permitted
   wide-survey runner). I validated and collated only. **No `instruction.md` was
   written, drafted or planned at any point. No near-miss.**
2. **Three premises killed by my own execution**, overriding both surveys:
   `avg` is implemented (desugared at `query/logicalplan/builder.go:205-234`,
   passing fixtures at `logictest/testdata/exec/aggregate/aggregate:47,52,57,62`);
   multi-aggregation already works in the hash path; the sampler's alphabetical
   sort is already at `base_commit` (`query/physicalplan/sampler.go:244-254`).
3. **C1 (multi-sink persist) is dead**, 5/5 outcome + 10/10 fork. All five cold
   implementations chose `bytes.Buffer` + per-sink reader + concurrent upload —
   the design the card called the *desired* one. **0 of 5** used `io.MultiWriter`
   or the serialize-per-sink loop, the card's two named wrong shapes.
4. **C2 (computed operands × ordered plan) is dead**, 10/10 fork plus a
   documented design decision. Also: `OrderedAggregate` **never plans anywhere**
   in the repo's logictest fixtures — the subsystem is dormant at HEAD.
5. **I did not run a second `A2` round** despite the router routing there. The
   reasoning is written out in `handoffs/02-A3.md` §"Why I am not running a
   second A2 round" — the candidate pool is exhausted and a second round on an
   exhausted pool is how a manufactured survivor appears.

## If someone picks this up

There is nothing to resume. The two useful follow-ons, both out of scope here:

- **13 parked single-turn surfaces** are listed in
  `cards/00-rejected-and-ranking.md` and the two survey files in `notes/`.
  Strongest three: the `query/physicalplan/sampler.go:262` positional-index bug
  (real, ~15 lines, under the floor for MT but fine single-turn); the
  `query/exprpb/proto.go:190-201,566-577` enum-parity gap; the
  `query/physicalplan/binaryscalarexpr.go:113` list-comparison panic.
- **`probes/gate4_assert_test.go` is reusable** as a template: a graded
  assertion validated against `base_commit` *before* being used to grade
  anything, with an explicit f2p/p2p split (A1/A2/A3 fail at base, A4 passes).

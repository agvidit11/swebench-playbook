# CHECKPOINT — pair-prism (`ruby/prism`), engineer half
_Rewritten after every meaningful sub-step. **FINAL write: run complete, A3 terminal, DONE written.**_

## Where I am
**RUN COMPLETE. Terminal state: `A3` EXIT MET as a kill — NO SURVIVOR.** `DONE` is written at the
run root. B1–B5 were never entered and must not be: PAIR-COMMON says report the kill with evidence
and stop, and forbids manufacturing a survivor to keep the run alive.

- A2 COMPLETE — `handoffs/01-A2.md`, **11 of 13 checklist, 2 FAILED** (corrected after the Codex
  reviewer returned FAIL on `review/01-A2-review.md`; the original 13-of-13 was an overclaim and is
  retracted). 8 cards now split to `cards/C01.md`–`C08.md`, verbatim, provenance-headed.
- A3 COMPLETE — `handoffs/02-A3.md`, 13 of 14 (GATE 8 waived: survivors only, there are none).
- friction.md — 13 numbered entries (F01–F13) + 13 tagged streamlining entries
  (EARLIER-01..05, REPEAT-01..03, WASTE-01..03, PINPOINT-01..03).
- `review/01-A2-review.md` — reviewer FAIL on A2, answered in `handoffs/01-A2.md` §CORRECTION.
  Two of its four executor defects were fixed, two were conceded and left standing rather than
  papered over. Its two blocking playbook defects match my F05 and F09 independently.

## Paths (all task-scoped; nothing generic in /tmp)
| what | path |
|---|---|
| run root | `/home/agvidit/swebench-playbook/.e2e/pair-prism/` |
| clone | `/tmp/shortlist-tooling/clones/prism` (full clone, branch `main`) |
| base_commit | `3942928d8f98f38cf7c4889c873c3c730ece7c63` (2026-09-22 21:05:57 +0200) |
| scratch | `/tmp/prism-run/` |
| A2 survey brief / output | `/tmp/prism-run/survey.txt` (21,967 B) / `/tmp/prism-run/survey.out` (93,407 B, 653 lines, 8 cards C01–C08) |
| admissions grep | `/tmp/prism-run/admissions.txt` |
| docker build ctx | `/tmp/prism-run/img/` (Dockerfile + `repo/` = `git archive` of base_commit) |
| **docker image** | `prism-a3:local` — **already built**, `rake compile` done inside it. Do not rebuild. |
| GATE 2 script | `/tmp/prism-run/gate2.rb` |
| R05 scripts | `/tmp/prism-run/gate6-r05.rb` (C05), `/tmp/prism-run/gate6-c08.rb` (C08) |
| GATE 5 probes | `/tmp/prism-run/probe/{A,B}.txt` briefs, `{A,B}-{1..5}.out` — all 10 returned and scored |
| repo-wide R05 script | `/tmp/prism-run/gate6-repo.rb` |
| task dir | **none, and none should be created** — B1 was never entered |
| cards | `cards/C01.md` … `cards/C08.md` (split verbatim from `survey.out` at correction time) |
| reviewer feedback | `review/01-A2-review.md` |

## Lock state
**I do NOT hold `/tmp/swebench-docker.lock`.** Every docker call so far was
`flock /tmp/swebench-docker.lock docker ...` and each released on exit. No container of mine is
running (`smoltcp-probe` belongs to another pair — leave it alone).

## In flight
**Nothing.** The A2 survey (mc.sh) completed. All 10 GATE-5 probes completed
(1,324–2,091 bytes each, all well over the 600-byte banner floor). No Codex dispatch has been made
this run.

## DONE, with evidence
| item | evidence |
|---|---|
| A1 inherited, not re-measured | `artifacts/A2-run-notes.md` §1 |
| lens chosen (R5 axis 16 + axis 10, R6 P6 at 2/3 instantiations) | `artifacts/A2-run-notes.md` §3 |
| surface count derived before the ask (18) | `artifacts/A2-run-notes.md` §4 |
| admissions grepped + re-verified at HEAD | `/tmp/prism-run/admissions.txt`, survey §1a/§1b |
| 18 surfaces, merge table, 10 auto-rejects, 8 cards | `/tmp/prism-run/survey.out` |
| A2 HANDOFF | `handoffs/01-A2.md` |
| repo-level disclosure sweep | `artifacts/A3-disclosure-prescreen.md` |
| corpus observable sweep (20 phrasings over /tmp/llc) | friction F06 table |
| GATE 2 executed at base_commit (not grepped) | `/tmp/prism-run/gate2.rb` output — pasted in `handoffs/02-A3.md` |
| R05 leak proven for C05 and C08 | `/tmp/prism-run/gate6-r05.rb`, `gate6-c08.rb` outputs |
| GATE 5 probes ×10, two phrasings | `/tmp/prism-run/probe/*.out` |
| friction log, 12+ entries incl. tagged REPEAT/EARLIER/WASTE/PINPOINT | `friction.md` |

## NEXT — nothing. The run is finished.
If someone reopens this repo, the only useful next step is **A1**, not A2: re-generating cards will
produce more candidates on the same R05-exposed surfaces. See `handoffs/02-A3.md` §"THE REPO-LEVEL
VERDICT" and friction `EARLIER-01` / `PINPOINT-02`.

Probe scoring result, for the record: **phrasing A 5/5 desired, phrasing B 5/5 desired, 10/10
overall.** A3 GATE 5: ">=4/5 take the desired path = no fork. It will one-shot. Do not build."
Two of the ten located prism's shipped `continuable?` by name while reasoning.

## Decisions already made — do not relitigate
1. **C02 (comment-attachment preview) is dead on disclosure and stays dead**, even though its
   observable is the least saturated in the corpus (6 peer files). Two independent kills: open issue
   #4044 has maintainers specifying `attach_comments`/the node_id map, and branch `origin/comments`
   (`95cd5cd93`) is a finished implementation — 8,306 insertions, `src/comments.c` +2,528,
   `test/prism/comments_test.rb` +2,229. A3 GATE 3 is a hard kill with no exception.
2. **I did not pick a side in the GATE 0 vs D1 conflict** (friction F09). Instead I required every
   graded assertion to be IN-BASE, which is lawful under both readings. Do not "resolve" it by
   choosing the permissive reading to rescue a card.
3. **The B layer (`R7`) was not sourced from** — it is QUARANTINED per router §9.
4. **`continuable?` already ships** (`lib/prism/parse_result.rb:990`, C impl `pm_parse_continuable`
   at `src/prism.c:23295`, commit `c28810fe9` 2026-03-09). Verified by execution, all 9 doc examples
   reproduce. Any candidate whose headline is "tell incomplete from invalid" is hollow at HEAD.
5. **Docker image is built and correct.** If you need another run, reuse `prism-a3:local` under
   `flock`; a rebuild costs ~45 s and changes nothing.
6. **prism's R05 property is now EXECUTED, not cited** — `Ripper`, `RubyVM::AbstractSyntaxTree`
   and `String#encode` are all reachable from a bare `ruby:3.4-slim` + prism image
   (`/tmp/prism-run/gate6-repo.rb`). This is the finding of the run.
7. **Do not re-measure the harness.** A1 measured it; my image reproduces it (`rake compile` 24.4 s
   in-image vs A1's 18.3 s — same order, difference is layer caching, not a discrepancy worth chasing).

## The one-line verdict a successor needs
prism is a **compatibility library**. Its contract is "return what an existing reference returns",
and for every observable it has, that reference (`Ripper`, `RubyVM::AbstractSyntaxTree`, Ruby's own
`case/in`, `String#encode`, the `parser`/`ruby_parser` gems, CRuby's `parse.y`) is **importable from
inside the solution**. That is an R05 property of the repo, not of any one card, and it is why the
cards die in a cluster rather than one at a time. See friction F10.

# Review — 01-A2.md

## Verdict: FAIL

A2 produced a real, attributable survey and two detailed cards, but it did not satisfy its own quality gate. The act says a card with a self-reported `FAIL` is repaired or discarded (`A-source/A2-idea-generate.md:250-251`). Both cards were nevertheless called survivors and handed to A3: C01 reports `R06 FAIL` and C02 reports `R08 FAIL` (`handoffs/01-A2.md:89-90`, `handoffs/01-A2.md:207-211`, `handoffs/01-A2.md:248-251`). Worse, the supplied shortlist explicitly records `AGENTS.md` (`/home/agvidit/swebench/runs/shortlist-data.md:75`), which is a hard G2 kill under `A-source/A1-repo-screen.md:25-30`; A2 accepted that invalid “screened repo” input without challenge. Thus checklist completion does not establish the act's precondition or its output quality.

## Checklist audit

- **1 — partially supported, waiver bookkeeping defective.** The shortlist supplies LOC, subsystem count, entry points, and measured harness timing (`/home/agvidit/swebench/runs/shortlist-data.md:71-79`), but no SHA. The executor transparently measured the missing SHA (`handoffs/01-A2.md:80`). That is reasonable under this run's explicit A2-start assignment, but the handoff later says both “partial waiver” and “0 waived” (`handoffs/01-A2.md:94`, `handoffs/01-A2.md:142-144`).
- **1 — also fails the input-validity check.** A2 requires a screened repo plus `HANDOFF A1` (`A-source/A2-idea-generate.md:5-8`), but the substitute shortlist says `AGENTS.md` is present (`/home/agvidit/swebench/runs/shortlist-data.md:75`) despite A1 making that a hard G2 kill (`A-source/A1-repo-screen.md:25-30`). The current clone confirms the file at `AGENTS.md:1-49`. The shortlist also says all 27 remote branches are dependabot (`/home/agvidit/swebench/runs/shortlist-data.md:74`), contradicted by non-dependabot refs in `/tmp/shortlist-data/clones/oxigraph/.git/packed-refs:3-5,24,26`.
- **5 — supported.** The persisted notes contain the command and eight quoted admissions (`artifacts/A2-run-notes.md:123-149`); `/tmp/oxigraph-run/admissions.txt` contains 70 lines, matching `handoffs/01-A2.md:61-71`.
- **7 — supported as a dispatch, not as validation.** `/tmp/oxigraph-run/cards.out` is 29,736 bytes and contains the 18-row merge table (`/tmp/oxigraph-run/cards.out:14-37`); the handoff correctly treats A2's contents as claims for A3 to test (`A-source/A2-idea-generate.md:10-12`).
- **8/9 — supported.** All 18 surfaces have dispositions in `/tmp/oxigraph-run/cards.out:16-35`, and the reject log names a rule for every dropped surface (`/tmp/oxigraph-run/cards.out:39-51`).
- **10 — FAIL.** A2 calls C01 and C02 “survivors,” yet each has a self-reported failing rubric (`/tmp/oxigraph-run/cards.out:103-104`, `/tmp/oxigraph-run/cards.out:133-134`). A2 explicitly forbids elaborating such a card without repair or discard (`A-source/A2-idea-generate.md:250-251`).
- **11 — FAIL.** The audits exist, but “self-audit present” is not enough when the same section requires a reported `FAIL` to be resolved. The handoff instead cites the failures as proof of completion (`handoffs/01-A2.md:90`).
- **12 — supported with a playbook contradiction.** Eighteen surfaces honestly collapsed to two cards (`/tmp/oxigraph-run/cards.out:136-138`), consistent with the expected 2–4 yield (`A-source/A2-idea-generate.md:60`) but inconsistent with the header's `>=8` dispatch target (`A-source/A2-idea-generate.md:7`).

## Evidence quality

The principal counts are measurements, not copied examples: the files on disk match 34,311-byte survey output, 29,736-byte card output, and 70 admissions (`handoffs/01-A2.md:9-12`, `handoffs/01-A2.md:61-72`). The 47 s/4.5 s build figures, however, were inherited from the shortlist as intended (`artifacts/A2-run-notes.md:3-19`), while all per-arm rates are explicitly predictions, not measurements (`/tmp/oxigraph-run/cards.out:98`, `/tmp/oxigraph-run/cards.out:129`). Both cards describe arms only as “strongest/mid/weak,” not the required Avocado/Opus/GPT values (`A-source/A2-idea-generate.md:136`; `/tmp/oxigraph-run/cards.out:98`, `/tmp/oxigraph-run/cards.out:129`).

## Boundary check

No task directory or protected instruction file existed in this act (`CHECKPOINT.md:21-24`). The handoff identifies MetaCode outputs and Claude's dispatch/verification role (`handoffs/01-A2.md:3-16`), which conforms to `A-source/A2-idea-generate.md:5` and the instruction boundary at `00-ROUTER.md:119-129`. I found no instruction-path write or indirect draft for an instruction file.

## Director's call

I would **not green-light oxigraph under the playbook as written**, because its own supplied evidence trips A1's unconditional `AGENTS.md` gate (`/home/agvidit/swebench/runs/shortlist-data.md:75`; `A-source/A1-repo-screen.md:25-30`). If a human explicitly waives or narrows that overbroad gate after reading the harmless contribution guide (`/tmp/shortlist-data/clones/oxigraph/AGENTS.md:1-49`), the repository is otherwise attractive: zero internal peer tasks, 0/1000 AI-attributed commits, rich public APIs, and a 47-second cold grading path (`/home/agvidit/swebench/runs/shortlist-data.md:66-102`). Even under that waiver, neither round-1 card is buildable.

## Defect attribution

### Executor defects

- Advanced two cards after their own audits returned `FAIL`, contrary to `A-source/A2-idea-generate.md:250-251`.
- Claimed checklist lines 10–11 complete despite that contradiction (`handoffs/01-A2.md:89-92`).
- Did not provide named per-arm predictions as required by `A-source/A2-idea-generate.md:136`; the cards use role labels instead (`/tmp/oxigraph-run/cards.out:98`, `/tmp/oxigraph-run/cards.out:129`).
- Treated the supplied shortlist as a valid A1 substitute despite its explicit `AGENTS.md` finding and incorrect “all dependabot” branch claim (`/home/agvidit/swebench/runs/shortlist-data.md:74-75`).

### Playbook defects

- **Contradictory card-count target:** `A-source/A2-idea-generate.md:7` says `>=8`, while `A-source/A2-idea-generate.md:60` says 15–20 surfaces normally yield 2–4 cards and forbids backfill. Fix: replace the fixed header target with the derived range.
- **Missing rubric-definition link:** A2 demands 13 named rubric checks (`A-source/A2-idea-generate.md:246-251`) but does not link their definitions, which appear later at `B-build/B5-preflight-push.md:88-107`. Fix: link a canonical rubric reference from A2.
- **Run-input mismatch, not an A1 design gap:** A1 does define the required clone path and HEAD SHA in its HANDOFF schema (`A-source/A1-repo-screen.md:276-281`), but this assignment substituted a shortlist entry that omitted the SHA (`/home/agvidit/swebench/runs/shortlist-data.md:66-102`). Fix for this run mode: require the supplied shortlist entry to carry the same minimum A1 facts, or explicitly authorize the A2 runner to fill missing facts.
- **Overbroad/ambiguous agentic-artifact gate:** A1 makes the mere presence of any `AGENTS.md` a hard kill (`A-source/A1-repo-screen.md:25-30`), while the shortlist informally exempts oxigraph's contribution guide (`/home/agvidit/swebench/runs/shortlist-data.md:75`). Fix: either enforce the literal gate or define a content-based exception; do not silently waive it.

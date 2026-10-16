# jsoup-streamparser-lazy-reader-failure-lifecycle

**Owner:** devvm23237 / current lane orchestrator (Vidit 2026-10-16 direct overnight pickup)
**State:** RELEASED — EVIDENCED KILL. Exact chain is saturated prerequisite plus a single-mode final cliff.

## History

- 2026-10-15 · devvm23237 Lane I · CARD 34/40 MEASURE · base `4cf664cdb2e9d2cc2d40fdf3bb9c0be0be22f865`; attaching a Reader reads eagerly despite the documented progressive contract, and checked/unchecked midstream failures leave it open. A4/public-fix clear. Card and base proof in `ledger/cards/jsoup-streamparser-lazy-reader-failure-lifecycle.md` and `/tmp/card-1015.auvYFI/evidence/`.
- 2026-10-16 · devvm23237/orchestrator · TAKING · replaces the saturated SPIRE revision as the second overnight work item. No competing task process or active claim found.
- 2026-10-16 · devvm23237/orchestrator · RELEASED · Muse-authored exact Step 1 scored 5/5 across five clean implementations, each also passing focused CharacterReader/StreamParser/HTML/XML regression suites. On those five real parents, Step 2 scored 0/5 solely because all implementations closed after the first I/O failure but allowed a later iterator `hasNext()` to retry the failed source; removing only that edge made the same cohort pass every other 34 behavioral checks 5/5 (checked exception families, partial document, completed elements, exact close, reuse, all named selection/completion APIs). The shape is bimodal, not gradated. No task directory, commit, or push. Evidence `/tmp/jsoup-probe-20261016`.

## Next

Revive only with a distinct final capability that yields multiple independent failure modes; do not tighten the exhausted-iterator sentence, because it merely flips the single uniform cliff to an explicit mechanical fix.

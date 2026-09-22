# A2 run notes — ruby/prism

## Checklist line 1 — HANDOFF A1 (inherited, NOT re-measured)
Source: `/home/agvidit/swebench/runs/shortlist-tooling.md` §"1. ruby/prism", plus the
pinned-HEAD table at line 329. There is no literal `HANDOFF A1` block — the screener wrote a
shortlist entry instead. Fields transcribed:

| field | value |
|---|---|
| clone | `/tmp/shortlist-tooling/clones/prism` (full clone, branch `main`) |
| HEAD | `3942928d8f98f38cf7c4889c873c3c730ece7c63` (2026-09-22 21:05:57 +0200) — verified with `git log -1` |
| licence | MIT |
| non-test LOC | 66,399 (C + Ruby; 20 hand-written `src/*.c`, 16 ERB templates generate the rest) |
| Ruby-side LOC | 15,848 across `lib/**/*.rb` (measured here, cheap, to size the Ruby lane) |
| subsystems | `src/` C parser · `lib/prism/` Ruby API · `lib/prism/translation/{parser,ripper,ruby_parser}` · `parse_result/{comments,errors,newlines}` · `relocation.rb` · serialization (`dump`/`load`) · `lex_compat` · encodings · `config.yml` (336 node types) = **10** |
| open issues | ~6 |
| peer dedup | **0 peer tasks.** filename sweep 53 hits all homographs; content sweep `Prism::`/`PM_NODE`/`prism_parse` = 0; `gh search code --owner codimango "ruby/prism"` = 1 hit, a docs hyperlink |
| AI-authorship | **0/500** by author identity; 0 attributions in a 796-line CHANGELOG; 5 stale `copilot/*` branches all confined to `java/` bindings |
| harness | `ruby:3.4-slim` + build-essential; `gem install -N rake rake-compiler test-unit`; `rake compile` **18.3 s once**; `test/prism/api/parse_test.rb` **0.204 s** (16 tests); `test/prism/errors_test.rb` **0.399 s** (1,443 tests). No DB, no network at test time |
| existing entry points that permit name-free assertion | `Prism.parse`, `result.errors`, `result.comments`, `Location#start_offset/start_character_offset/cached_start_code_units_offset`, `Prism.dump`/`Prism.load`, `Prism::Relocation`, the three `translation/*` renderings |
| A1 warnings | (a) prism is CRuby's official parser, vendored into JRuby/TruffleRuby/ruby-lsp/rubocop — **highest training-data density of any repo on the shortlist**, cold fork probe mandatory; (b) `src/node.c`, `src/prettyprint.c`, `src/serialize.c`, `src/diagnostic.c` are **GENERATED** from `templates/` + `config.yml` — a graded test must not sit on a file the solver is expected to hand-edit |

## Checklist line 2 — authorship lane
Runner for the survey dispatch: **Avocado / MetaCode** via `~/.claude/skills/swebench-mt/mc.sh`
(A2's declared owner). I (Claude) do the recon greps, the lens choice, the count derivation and
the dispatch plumbing only. **I generate no surfaces and no cards, and I write no prose destined
for `instruction.md`.** Router §5 iron-clad rule acknowledged.

## Checklist line 3 — the composed lens

**C-axis: R5 axis 16 — "Incomplete versus invalid incremental input."**
Definition: distinguish a valid prefix awaiting more bytes from irrecoverably malformed input.
Chosen because it is the only axis in R5 whose *observable* maps onto prism's four least-saturated
observables in the peer corpus (`error recovery` 59, `partial parse` 15, `concrete syntax` 9,
`comment attachment` 6) rather than onto the saturated ones (`idempoten*` 4,899, `round-trip`
3,081, `converge` 2,065, `byte-for-byte` 1,868).

**R5's own warning on axis 16 is recorded and NOT waived:** *"Novelty risk: High. Parser work is
saturated and implementations may grow beyond the line budget. Keep only when the repository
already exposes most parser machinery."* Prism satisfies the second clause exactly — `pm_parse`
already produces a tree-plus-errors for any input. The first clause is a live risk and is what
the A3 recall probe exists to measure.

**Secondary C-axis (hedge, for the same dispatch): R5 axis 10 — "Observer noninterference."**
Prism's `Comments#attach!` *mutates* the parse result, `Relocation` re-parses under a cache, and
`parse_lex` runs two pipelines over one buffer. Non-consuming observation over a mutating
attach pass is a natural fit and lands on `comment attachment` (6 hits).

**A-shape: R6 P6 — revert-and-redo.** Instantiation count in R6's table = **2** (both
`rom-rb/rom`, both `not built`, and D1 was subsequently killed by its probe). Ceiling is ~3, so
P6 has exactly one slot left. P1 is closed at 3. P2–P5 each have 1 but are each bound to a
different precondition that prism does not obviously meet.
**P6's measured precondition is enforced in the survey ask:** *P6 works only when the DEFAULT
implementation is eager / unconditional / materialise-everything.* Also carried in: the HEAD
counterfactual test, the parallel-API test, and the step-1-must-be-the-universal-first-answer test.

**B-layer: OMITTED.** `R7-algo-catalogue.md` is QUARANTINED (router §9, R6 Part B verdict:
five measured failures). Not sourced from.

## Checklist line 4 — surface count, derived before the ask
- LOC band: 66,399 non-test → A2 §2 row "60k – 150k" → **15–20 surfaces**.
- Subsystem cross-check: 10 named subsystems × "roughly 2–3 per major subsystem" → 20–30.
  The two do not disagree badly; A2 §2 says trust the subsystem count when they do.
- **Ask: 18 surfaces, run in three subsystem passes** (Ruby API + parse_result; translation ×3;
  C parser + serialization + encodings + relocation).
- Card expectation from A2 §2: 15–20 surfaces collapse to **2–4 real candidates**. The ≥8 card
  dispatch target is therefore *nominally* in reach at 66k LOC, and I will report the real number
  with its derivation rather than backfill.

## Checklist line 5 — the repo's own admissions
Command and full output: `/tmp/prism-run/admissions.txt`. Verified against HEAD 3942928.
The four that are load-bearing (all re-read in context, all present at HEAD):

1. `lib/prism/parse_result.rb:734` — `raise NotImplementedError, "trailing? is not implemented for #{self.class}"` on the `Comment` base class.
2. `lib/prism/translation/ripper/lexer.rb:117` — `# that the parser encounters them. This is not implemented.`
3. `lib/prism/translation/ruby_parser.rb:1406` — bare `# TODO`.
4. `lib/prism/relocation.rb:240` — `raise NotImplementedError, "Subclasses must implement #result"`.

C-side, weaker but recorded: `src/prism.c:9880` `// TODO: If the character is invalid in the
given encoding, then we'll just …`; `src/integer.c:598` `// even the larger numbers, but for now
we're going to keep it simple.`; `src/source.c:336` `pm_source_file_new is not implemented for
this platform`.

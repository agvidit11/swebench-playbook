# A3 GATE 3 — repo-level disclosure intel, gathered while the A2 survey ran

Run 2026-09-22 against `ruby/prism` @ `3942928d8f98f38cf7c4889c873c3c730ece7c63`.
This is **pre-screen for GATE 3**, not GATE 3 itself — GATE 3 is per-candidate and is run again
against each surviving card's specific behaviour. But two lanes are already dead, and killing them
before A2's cards land saves a scoring pass (A3 §0: "novelty runs before scoring").

## The full open-issue set (only 6 — this is why the repo screened well)

```
$ gh issue list --repo ruby/prism --state open --limit 30
4091  OPEN  Trailing comma in AST                        enhancement  2026-07-24
4044  OPEN  Revisit comments                             enhancement  2026-03-26
4040  OPEN  Automatic publishing of Maven artifacts.     java         2026-03-25
4018  OPEN  Release official Java API                    java         2026-03-24
3959  OPEN  Split gem into Ruby and extension parts      java         2026-03-19
3466  OPEN  Modifying AST and generating source code     enhancement  2026-03-02
```

Feature/roadmap sweep (R6 "the novelty gate has no feature-side arm"):
```
$ gh api "search/issues?q=repo:ruby/prism+label:feature+state:open" --jq '.total_count'   -> 0
$ gh api "search/issues?q=repo:ruby/prism+roadmap+in:title"          --jq '.total_count'   -> 1
$ ls ROADMAP* docs/roadmap* CONTRIBUTING*                                                  -> CONTRIBUTING.md only
```

Remote branches:
```
origin/comments            <-- NOT stale, and NOT a bindings branch
origin/ruby-3.4  origin/ruby-4.0
origin/copilot/{add-result-interface, convert-java-snippet-to-classfile,
                convert-sealed-interface-result, research-prism-performance-issues,
                write-java-equivalent-using-classfile}
```
Note the A1 screen said "10 remote branches; 5 `copilot/*`, all stale, all confined to `java/`
bindings". That is accurate as far as it goes, but **A1 did not look at the non-copilot branches**,
and `origin/comments` is the one that matters. Logged as friction.

---

## LANE KILL 1 — comment attachment. **DEAD. Hard GATE-3 disqualifier, two independent ways.**

This was the highest-value observable in the whole corpus sweep (`comment attachment` = 6 peer
files, the least saturated term measured) and it was my secondary C-axis. It is dead.

**(a) Issue #4044 "Revisit comments" is an open, maintainer-driven design thread that specifies
the remedy.** A3 GATE 3: *"any open issue whose body or comments propose the direction, workaround,
API or remedy — even informally, even with no code"* is a hard kill. This one proposes the API
explicitly. Quoted verbatim from `gh issue view 4044 --comments`:

- `eregon` (member): *"Would this handling of comments be configurable somehow? … wouldn't
  attaching the comments to the node (as an optional `comments` field or so) be enough? … Newline
  marking for example is done optionally with `ParseResult#mark_newlines!` and I think this is a
  good trade-off."*
- `kddnewton` (collaborator): *"You'd have to pass the `attach_comments` option, which would not be
  on by default."*
- `kddnewton`: *"I'm not putting the comments on the nodes in the C API, I'm making a map from
  node_id to the comments object, so that in the common case of not doing this, the structs do not
  increase in size."*

That is the option name, the default, the data structure and the memory rationale — in public.

**(b) `origin/comments` is not a proposal, it is a shipped implementation.**
```
$ git log --oneline origin/main..origin/comments
95cd5cd93 Comments revisit

$ git diff --stat origin/main...origin/comments | tail -1
54 files changed, 8306 insertions(+), 3708 deletions(-)
```
Highlights of that diff:
```
 src/comments.c                                | 2528 ++++++
 test/prism/comments_test.rb                   | 2229 ++++++
 templates/include/prism/comments.h.erb        |   51 +
 templates/lib/prism/comments.rb.erb           |   33 +
 src/options.c                                 |   17 +
 sig/generated/prism/comments.rbs              |  562 +++
 test/prism/result/comments_test.rb            |   24 -
```
A 2,229-line test file for the exact surface. Any task built here would be graded against
behaviour whose reference implementation is a `git fetch` away.

**(c) Collateral finding — `Prism::Relocation` is being DELETED on that same branch.**
```
 rbi/generated/prism/relocation.rbi     |  60 -
 sig/generated/prism/relocation.rbs     |  74 -
 test/prism/ruby/relocation_test.rb     |  44 -
```
`lib/prism/relocation.rb` (665 lines) was one of A1's four named "name-free gradeable" surfaces
("Offset/locality invariants … under `Prism::Relocation` reload"). Building a net-new capability
into a class the maintainers are deleting on an active branch is a **Realism/fit veto** under A3
GATE 8 (*"a maintainer would plausibly want it"* — measurably, they do not). Relocation is
demoted to a host of last resort, and if used at all the assertion must not depend on it.

## LANE KILL 2 — AST modification / source generation. **DEAD on disclosure.**

Issue #3466 "Modifying AST and generating source code" is open, and the thread hands over both the
direction and the upstream precedent:
- `rafaelfranca` (collaborator): *"the answer is yes, you can use a visitor to modify the AST, or
  even build a new AST. And they use something unparser to generate the ruby code again."*
- `Earlopain` (collaborator): *"Previously kddnewton expressed desire to add such an api to prism
  itself here: https://github.com/whitequark/parser/issues/1046#issuecomment-2491891823"*
- `mbj`: links `mbj/unparser#387`, `mbj/unparser#385`, `ruby/prism#3553`.

This kills the `structured edit` (9) / `minimal edit` (24) lane on this repo — which is a pity,
because those were the next-cleanest observables, and R5 axis 3 is the axis R6 says survives
language idiom best. **A1's four suggested surfaces are now 2 of 4 dead** before A2's cards land,
which is exactly why the brief says A1's surface suggestions are not pre-validated ideas.

## LANE KILL 3 — serialization round-trip. **DEAD ON SATURATION, not disclosure.**

A1 proposed *"`Prism.dump` → `Prism.load` must produce a tree `==` to `Prism.parse(...).value`, and
`dump` must be byte-stable across two calls."* Both halves sit on banned observables:
`round-trip` 3,081 peer files, `byte-for-byte` 1,868, `idempoten*` 4,899. Recorded and not
proposed. (This one A1 itself should have caught — it ran the saturation sweep and then wrote a
surface suggestion that the sweep forbids. Logged as friction.)

## LANES STILL ALIVE after the pre-screen

| lane | observable | corpus count (mine, `grep -rliF` over /tmp/llc) | disclosure |
|---|---|---|---|
| error recovery / partial parse | `error recovery` / `partial parse` | 86 / 22 | `search/issues` total_count 13 / 9 — must be read per-candidate |
| code-unit + encoding offsets | `code unit` / `utf-16` | 78 / 163 | `code units` total_count 12 |
| three-way translator parity | `concrete syntax` | 10 | not yet swept |
| lex_compat | — | — | not yet swept |

`origin/ruby-3.4` and `origin/ruby-4.0` are version branches and need a per-candidate check: a
candidate whose behaviour is implemented on `origin/ruby-4.0` is disclosed the same way
`origin/comments` disclosed the comment lane. **This check is not in A3 GATE 3's command list** —
GATE 3 greps issues, PRs and the peer corpus but never `git branch -r`. Logged as friction.

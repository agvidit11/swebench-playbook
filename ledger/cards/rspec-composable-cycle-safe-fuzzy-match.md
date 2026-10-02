# rspec-composable-cycle-safe-fuzzy-match

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `rspec/rspec` @ `df877b73ab2a01bc7e3b5a39e7e252e8d9bb67a3`
- Seam: `RSpec::Matchers::Composable#values_match?` and `RSpec::Support::FuzzyMatcher`
- Routing: `DOWNGRADE` to single-turn, then `MEASURE`
- Trap: a convenient helper that is subtly too narrow
- A4: `ADJACENT`; no peer uses `rspec/support/fuzzy_matcher` or this exact seam

## User problem

I use RSpec's documented `values_match?` extension point in custom matchers over recursive ASTs, dependency graphs, and parent-linked domain models. Recursive arrays and hashes currently crash with `SystemStackError`. Matching should terminate while retaining matcher-leaf behavior and the existing value semantics for shared subgraphs.

## Base evidence

At the pinned base, an acyclic nested matcher returns `true` and a shared-DAG mismatch returns `false`, while self-cyclic arrays, self-cyclic hashes, and a mutual cycle containing a matcher leaf each raise `SystemStackError: stack level too deep`.

- `rspec-support/lib/rspec/support/fuzzy_matcher.rb:10-46` recursively descends arrays/hashes without recurrence context.
- `rspec-expectations/lib/rspec/matchers/composable.rb:143-145` avoids only immediate self-recursive arrays.
- Existing specs promise arbitrary nested arrays but contain no cyclic case.

## Contract boundaries

CONSTRAINT: Recursive Array/Hash values passed through the existing entry point must produce the same Boolean fuzzy-match decision as finite nested values, without recursion failure, while preserving embedded matcher behavior and existing shared-subgraph value semantics.

DESIRED: Pair-sensitive recursive matching and matcher preparation terminate across self-cycles, mutual cycles, and shared DAGs without confusing alias identity with value equality.

NON-DESIRED: Identity-only shortcuts; one-sided seen sets; treating every revisit as false; fixing fuzzy comparison while leaving matcher cloning recursive; process-global memo state.

Observable cases: equivalent self/mutual cycles match; cyclic versus finite structures do not; differing reachable leaves fail; embedded matchers retain fuzzy semantics; sharing alone does not alter equality; existing finite behavior and exception propagation remain unchanged.

No new production symbol or schema is needed. The existing public entry point is `(expected, actual) -> Boolean`.

## Shape and rating

Expected implementation: 80-140 net lines across the two implementation files and existing specs. Deterministic, in-memory grading.

An attempted second turn for failure presentation was only a mechanical view over the first. Therefore this is honestly single-turn rather than a fabricated cascade.

Rating: P1 4, P2 2, P3 2, P4 4, P5 0, P6 4, P7 3 = **19/28**. Gate verdict: **DOWNGRADE**, followed by a five-cold-implementation probe.


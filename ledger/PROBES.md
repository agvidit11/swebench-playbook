# PROBES — every card's Avocado probe result, append-only

Lane P writes one row per probe. This is how we learn which trap classes and repos actually split
Avocado — read it before choosing the next card.

| date | machine | card | repo | trap class | contract words | Avocado n/5 | failures (stated / unstated / infra) | verdict |
|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | devvm6971 | gobgp step 2 divergent route | osrg/gobgp | natural order loses information | ~230 | 3/5 | 2 stated (reduce-first dropped an entry) | in band |
| 2026-10-01 | devvm6971 | gobgp step 3 divergent paths (v1) | osrg/gobgp | permissive helper | 297 | 3/3 reached | — | too easy → re-authored for route-target legality |
| 2026-10-02 | devvm6971 | go-zero goctl compatibility (single-turn) | zeromicro/go-zero | equivalence over a large domain | ~600 | 0/5 | 3 stated, 2 timeouts | being converted to 3-step |
| 2026-10-02 | devvm6971 | adaptix-typeddict-union-dump-selection s2 (ambiguity reject) | reagento/adaptix | equivalence over a large domain | 325 | 5/5 | 0 genuine (load-back row = base bug, info) | too easy → drop |
| 2026-10-02 | devvm6971 | adaptix-typeddict-union-dump-selection s1 (dump case selection) | reagento/adaptix | permissive helper | 242 | 4/5 real (1/5 graded) | 1 stated (stale __required_keys__); 3 = contract named buggy Literal loader as authority | contract defect; card dropped on s2 |
| 2026-10-02 | devvm6971 | phprrule-rset-split-reschedule s2 (rescheduleFrom) | rlanvin/php-rrule | permissive helper | 378 | 5/5 | 0 (1 infra hang, code complete) | too easy → drop |
| 2026-10-02 | devvm6971 | phprrule-rset-split-reschedule s1 (splitAt) | rlanvin/php-rrule | natural order loses information | 312 | 5/5 | 0 | too easy → drop. LESSON: trap is self-checkable by running the library's own iterator; Avocado verifies and escapes |
| 2026-10-02 | devvm6971 | geojson-antimeridian-bbox s2 (compute_bbox) | georust/geojson | natural order loses information | 311 | 5/5 | 0 | too easy |
| 2026-10-02 | devvm6971 | geojson-antimeridian-bbox s2b (amend: removed approach hint) | georust/geojson | natural order loses information | 329 | 5/5 | 0 | too easy → drop |
| 2026-10-02 | devvm6971 | geojson-antimeridian-bbox s1 (collection union) | georust/geojson | natural order loses information | 240 | 5/5 | 0 | too easy; "antimeridian bbox" recalled as largest-gap |
| 2026-10-02 | devvm6971 | config-rs-writable-layer-delta s2 (layer_between) | rust-cli/config-rs | natural order loses information | 294 | 1/5 | 3 stated (array shrink under upper index override copies upper value), 1 unstated (absent=no-opinion not restated) | IN BAND (fragile, rides on one case) → ACTIVE single-turn |
| 2026-10-02 | devvm6971 | config-rs-writable-layer-delta s1 (changes_since) | rust-cli/config-rs | equivalence over a large domain | 302 | 5/5 | 0 | too easy → folded |
| 2026-10-02 | devvm6971 | unyt-pint-bridge s2 (import + round trip) | yt-project/unyt | natural order loses information | 257 | 0/5 | 5 stated (define_unit symbol collisions come back base-expanded; 4/5 didn't revisit step-1 base-expanded export); probe defects: coincidental import matches, wrong preserve baseline; oracle used attribute side-channel | bimodal → one amend (single-turn merged) |
| 2026-10-02 | devvm6971 | unyt-pint-bridge s1 (export identity) | yt-project/unyt | permissive helper | 264 | 5/5 | 0 | too easy; table-patch trap never fired |
| 2026-10-02 | devvm6971 | commonmark-java link-retarget s1 (inline) | commonmark/commonmark-java | permissive helper (source spans) | 301 | 1/5 strict, 2/5 lenient | 3 stated (span drift after \| in table cells), 1-2 implied-unstated (unescaped \| breaks table) | IN BAND → ACTIVE single-turn |
| 2026-10-02 | devvm6971 | commonmark-java link-retarget s2 (reference defs) | commonmark/commonmark-java | natural order loses information | 342 | 5/5 (+16-case amend 5/5) | 0 | too easy → dropped |
| 2026-10-02 | devvm6971 | comfytable-cell-style (single-turn) | Nukesor/comfy-table | permissive/strict helper | 306 | 4/5 effective (3/5 strict) | 1 stated (22 leaves dim), 1 unstated build break (--all-features non_exhaustive match) | too easy → drop; Avocado handles reset spellings broadly |
| 2026-10-02 | devvm6971 | unyt-pint-bridge merged single-turn (amend) | yt-project/unyt | permissive helper + natural order | 261 | 0/5 | all stated (hbar->dirac_constant 5/5, mcd 4/5, define_unit collisions); same cliffs every impl | park — fixing = naming cases |
| 2026-10-02 | devvm6971 | rust-hcs qualified directives s2 (304) | kornelski/rusty-http-cache-semantics | natural order loses information | 329 | 5/5 | 0 | too easy; info not actually lost (304 headers in scope) → drop |
| 2026-10-02 | devvm6971 | rust-hcs qualified directives s1 (store/reuse) | kornelski/rusty-http-cache-semantics | permissive helper (lossy res_cc) | 400 | 5/5 | 0 | too easy |
| 2026-10-02 | devvm6971 | commons-text staged substitution s2 (on s1 sketch) | apache/commons-text | natural order + permissive helper | 267 | 1/4 graded | 3 stated (s1 regression while rebuilding scanner; throw on representable / no throw on unrepresentable); 3 infra hangs excluded | IN BAND (n=4) → ACTIVE single-turn merged, re-gate n=5 |
| 2026-10-02 | devvm6971 | rubyzip append-only s2 (revisions) | rubyzip/rubyzip | natural order / too-loose EOCD helper | 284 | 5/5 | 0 (2 probe bugs fixed) | too easy; Avocado writes explicit history markers, never scans |
| 2026-10-02 | devvm6971 | rubyzip append-only s1 (append_only commit) | rubyzip/rubyzip | constraint fights natural edit site | 261 | 5/5 | 0 | too easy; checks with external readers, own reader hiding damage didn't matter |
| 2026-10-02 | devvm6971 | config-rs layer_between single-turn re-gate r1-r3 | rust-cli/config-rs | natural order loses information | ~400 | 0/5, 0/5, 0/5 | all stated; uniform failure flips with one sentence (array whole vs per-element) | bimodal → released. LESSON: the original 1/5 was a 2-step artefact (step-2 seeded from step-1 sketch) |
| 2026-10-02 | devvm23237 | rspec composable cycle-safe fuzzy match (single-turn) | rspec/rspec | convenient helper subtly too narrow | 157 | 2/5 | 3 stated (shared-DAG/stateful-matcher cloning), 0 unstated, 0 infra | IN BAND → ACTIVE single-turn; controls baseline 9/16 fail, negative 11/16 fail, desired 16/16 pass |
| 2026-10-02 | devvm23237 | open62541 DateTime strict civil validation (initial single-turn) | open62541/open62541 | natural order loses information / permissive helper | 239 | 4/5 | 1 stated (treated legal +14:59 as exceeding a total ±14:00 cap), 0 unstated, 0 infra | too easy as single-turn → keep PROBING and reshape to 3-step MT under 2026-10-02 ruling |
| 2026-10-02 | devvm23237 | open62541 DateTime strict civil validation (AMEND single-turn) | open62541/open62541 | natural order loses information / permissive helper | 255 | 5/5 | 0 | too easy after one amend → RELEASED. LESSON: calendar/offset validation is a recalled algorithm even when contract is outcome-only |
| 2026-10-02 | devvm23237 | rspec-backtrace-location-remapping s1+s2 chained (+s2 AMEND) | rspec/rspec | natural order loses information | 166/245/261 | s1 5/5, s2 4/5, s2-amend 5/5 | 1 stated (fallback restored raw generated frames) | too easy → RELEASED |
| 2026-10-02 | devvm23237 | rspec-composable cycle-safe fuzzy match (built task, exact prompt, local metacode k=5 x2) | rspec/rspec | helper subtly too narrow | — | 5/5, 5/5 | 0 | probe 2/5 came from an earlier Muse draft; exact-prompt saturates → MT reshape. LESSON: re-probe after the final contract is re-authored, before B3-B6 |

## 2026-10-02 devvm6971 — uniform failure = grader bug, twice in one afternoon
- go-zero step 2: 5/5 failed one subtest. Probe of core/mapping showed `default=` and `options=` are ACCEPTED by the
  decoder (= absent) while the test demanded rejection. Only `optional=!` (always rejected) was a fair miss (1/5).
- gobgp step 1: 3/5 failed one assertion; the Avocado answer accepted exactly the same routes with the same entry
  count as the oracle's -- the contract never chose a canonical form.
- Rule: when every failing run fails the SAME assertion, probe the authority before counting it as difficulty.
| 2026-10-02 | devvm23237 | django-model-utils Choices grouped selection s1+s2 chained (+s2 AMEND) | jazzband/django-model-utils | natural order loses information | 260/334/435 | s1 5/5, s2 5/5, s2-amend 5/5 | 0 stated in counted sets; 6 infra (banner-only/stream retries) replaced | too easy → RELEASED. LESSON: AMEND that states the observed failing case converts it to 5/5 — state rules, never cases |
| 2026-10-02 | devvm23237 | django-model-utils grouped selection trap-free s2 re-probe (on passing s1) | jazzband/django-model-utils | natural order loses information | 331 | 2/5 | 3 stated (distinct source group occurrences merged by label equality) / 0 unstated / 0 infra | IN BAND -> BUILD; unlike the invalid prior amend, the contract states the general source-occurrence rule without enumerating the observed equal-label case; needs 3-step MT shape for the saturated s1 exemption |
| 2026-10-02 | devvm23237 | rspec backtrace location remapping s2 trap-free re-probe (on passing s1 seed) | rspec/rspec | natural order loses information | 448 | 5/5 | 0 stated, 0 unstated, 0 infra; one unstated grader case dropped before probing | too easy under rule-only contract → RELEASED; supersedes invalid order/case-revealing probe |
| 2026-10-02 | devvm23237 | django-model-utils grouped selection s2 TRAP-FREE re-probe (on passing s1) | jazzband/django-model-utils | natural order loses information | 331 | 2/5 | 3 stated (distinct source group occurrences merged by label equality) / 0 / 0 | IN BAND → BUILD 3-step MT. Same card was 5/5 when obligations enumerated the case |
| 2026-10-02 | devvm23237 | rspec-backtrace s2 TRAP-FREE re-probe (on passing s1) | rspec/rspec | natural order loses information | 448 | 5/5 | 0 | valid saturation → RELEASED |
| 2026-10-02 | devvm6971 | css-inline MT: residual layer order (last) | Stranger6667/css-inline | natural order loses information | 266 | 3/5 | 2 stated (sub-layer order after inline; @media brace) + 2 infra hangs | IN BAND (last step) |
| 2026-10-02 | devvm6971 | css-inline MT: layered inlining (s1) | Stranger6667/css-inline | natural order loses information | 246 | 5/5 | 0 | exempt slot |
| 2026-10-02 | devvm6971 | css-inline MT: revert-layer (middle, new) | Stranger6667/css-inline | equivalence | 236 | >=4/5 (1 pending) | 0 | middle 0.8 ok; amend if 5/5 |
| 2026-10-02 | devvm6971 | unyt MT3 s2 from_pint names (chained) | yt-project/unyt | permissive helper | 238 | 3/5 | 2 stated (planck_* constant, grade/rpm) | IN BAND |
| 2026-10-02 | devvm6971 | unyt MT3 s3 round trip (chained) | yt-project/unyt | natural order loses information | 232 | 0/5 full, 3/5 scoped | uniform cliff on same-dim collisions (excluded from grader) | IN BAND scoped |
| 2026-10-02 | devvm6971 | config-rs MT3 s2 layer_between scalars (chained) | rust-cli/config-rs | natural order | ~300 | 3/5 | 2 stated-soft (env-set keys not named) | IN BAND |
| 2026-10-02 | devvm6971 | config-rs MT3 s3 arrays under override (chained, r3) | rust-cli/config-rs | natural order loses information | ~300 | 3/5 strict (4/5 s3-only) | r1 0/5, r2 0/5 contract gaps fixed; r3 genuine: Nil-for-None, copies z | IN BAND fragile |
| 2026-10-02 | devvm6971 | configupdater MT3 (chained) | pyscaffold/configupdater | permissive helper / own reader hides damage | 345/466/356 | 5/5 / 3/5 prov / 0/5 | s3: hidden trigger (; comment line dropped) | S3 amend |
| 2026-10-02 | devvm23237 | django grouped selection s2 = rebind(source) (on passing s1) | jazzband/django-model-utils | none named (re-resolution) | — | 5/5 | 0 | saturated middle step; union candidate stopped earlier on a Muse draft that prescribed strategy. LESSON: a middle step with no named trap saturates |
| 2026-10-02 | devvm23237 | ruby-terraform option layers s1+s2+s3 chained | infrablocks/ruby_terraform | natural order loses information | — | s1 5/5, s2 5/5, s3 3/3 valid (n incomplete) | 0 stated; 8 infra (sandbox read-only ~/.config/muse) | completing s3 n=5 |

## 2026-10-02 devvm6971 — gobgp third-step rescue measured 5/5/5
- Step 3 'earliest disagreement within a scope' (information-losing natural order: post-filter the global first
  witness). Codex's own natural impl fell into it; Avocado did NOT -- 5/5 computed (lhs XOR rhs) AND scope directly.
  The contract's symptom sentence ("the first witness comes back from uninteresting space") may have helped.
- Lesson: a falsifier written by Codex is not evidence Avocado falls into the trap (cf. fork-strength 11-for-11).
| 2026-10-02 | devvm23237 | jsoup W3C mirror reconciliation s1+s2+s3 chained | jhy/jsoup | natural order loses information | 242/223/240 | s1 3/5, s2 5/5, s3 3/5 | s1 2 stated; s3 2 stated; 0 unstated; 0 infra in sample | IN BAND (valid 3-step: one non-final 1.0) → ACTIVE |
| 2026-10-02 | devvm23237 | ruby-terraform option layers s3 completion | infrablocks/ruby_terraform | natural order loses information | — | s3 5/5 (n=5 valid) | 0 | saturated → RELEASED |
| 2026-10-02 | devvm23237 | state-machines AR rollback s1+s2+s3 chained | state-machines/state_machines-activerecord | constraint fights natural edit site | 290/305/266 | 5/5, 5/5, 0/5 | s3: 5 stated, all the same inherited step-1 assertion | shape invalid + single-assertion cliff → RELEASED |
| 2026-10-02 | devvm23237 | NOTE state-machines s3 signal | state-machines/state_machines-activerecord | constraint fights natural edit site | — | — | 5/5 step-3 edits broke a step-1 guarantee (entry event cleared) | real trap signal worth reusing in a properly separated step; not a dead idea |
| 2026-10-02 | devvm6971 | stjsonschema MT s1 Bundle | santhosh-tekuri/jsonschema | permissive resolver (draft re-reading) | — | 2/5 | 3 stated (draft-07 $ref+siblings re-read under parent dialect) | IN BAND |
| 2026-10-02 | devvm6971 | stjsonschema MT s2 Unbundle | santhosh-tekuri/jsonschema | — | — | 5/5 | 0 | exempt slot |
| 2026-10-02 | devvm6971 | stjsonschema MT s3 Flatten (v1 error on mixed) | santhosh-tekuri/jsonschema | — | — | 4/5 | 1 stated ($ref in const) | too easy → amend |
| 2026-10-02 | devvm6971 | stjsonschema MT s3 Flatten mixed-dialect (amend A) | santhosh-tekuri/jsonschema | equivalence over large domain | — | 3/5 rescoped (4/5 w/o contrived fixture; 0/5 full w/ uniform cliffs) | genuine: draft-07 contains/minContains, 2020-only keywords | finding realistic 2nd discriminator |

## 2026-10-02 devvm6971 — go-zero pushed; three things worth reusing
- No-abort probe: copy the task to an untracked zz-probe-* dir with steps 1..N-1 at min_reward 0.0 to measure
  every step on all k trials from the model's own tree (the server's seeding). `--start-step N` is broken for
  metacode (no auth minted in jump-to mode -> invalid_api_key -> fake 0/5). Delete the copy before pushing.
- Uniform 5/5 failure on one edge happened 4 times today (default=, options=, NaN bound, header-only response);
  each was a gotcha. Never ADD a graded test late without replaying the existing trial trees against it.
- push-task.sh non-fast-forward with a dirty shared tree: cherry-pick into a clean `git worktree` on FETCH_HEAD
  and push from there; then mixed-reset the local dup commit. Never rebase/autostash the shared tree.
| 2026-10-02 | devvm6971 | fsutil as carded S1/S2/S3 (chained) | tonistiigi/fsutil | natural order + permissive helper | — | 5/5, 5/5, 2/5 | S3 genuine: x** over-prune, [ab] under-prune, order shadow | two 1.0s → reshape |
| 2026-10-02 | devvm6971 | fsutil reshape 2: merged / include pruning / exclusion pruning | tonistiigi/fsutil | natural order loses information | 249 (last) | 1.0 / 3/5 / 3/5 | all genuine | GATE-VIABLE → ACTIVE |

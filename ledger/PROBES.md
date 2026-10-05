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
| 2026-10-03 | devvm23237 | state-machines two-step structural amendment | state-machines/state_machines-activerecord | merged rollback boundaries / safe live-record reuse | 245/222 | 5/5, 5/5 | 0 invalid; final previous-tree control already 4/5 | factual KILL: final saturated after sole amendment; no scaffold |
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
| 2026-10-02 | devvm23237 | django grouped selection s1 v2 (identifier-attribute authority) + s2 stability | jazzband/django-model-utils | constraint fights natural edit site | — | s1 3/5, s2 1/3 | s1: 2 stated (first duplicate's value); grader order assertion dropped as ambiguous | IN BAND → BUILD 2-step |
| 2026-10-02 | devvm6971 | commonmark MT local k=5 run1 (refs/inline/unlink) | commonmark/commonmark-java | permissive helper (spans) | — | 5/5 / 5/5 / 1/5 | s3 genuine: block-marker + setext escaping misses | two 1.0s → reshape |
| 2026-10-02 | devvm6971 | commonmark MT local k=5 run2 (escaped-pipe sentence removed) | commonmark/commonmark-java | — | — | 5/5 / 0/5 | uniform cliff on escaped-pipe tables | binary on one sentence → merge s1+s2, split unlink |
| 2026-10-03 | devvm6971 | config-rs MT3 local k5 x2 (cascade) | rust-cli/config-rs | — | — | s1 7/10, s2 7/7, s3 7/7 | s1 genuine (None field counted as edit); codex-agent s3 3/5 genuine | last step saturated → reshape move 4 (merge s2+s3, new s3) |
| 2026-10-03 | devvm23237 | Prism relocation identity reconciliation s1+s2 | ruby/prism | numeric identity too permissive / contextual ambiguity | — | — | 3/5, 0/5 | s1: 2 stated (eager save violates lazy semantics); s2: duplicate/context failures across all five, 4 lazy regressions | AMEND: retain s1, split s2 into unique shift recovery then contextual disambiguation; one remeasure |
| 2026-10-03 | devvm23237 | jsoup session fork/cookie promotion s1+s2+s3 | jhy/jsoup | shared mutable state / failure atomicity | — | — | 5/5, 5/5, 5/5 | 0 genuine solver failures; 1 stalled infra run replaced | saturated → structural AMEND once; merge foundation and add different-kind dependent work |
| 2026-10-03 | devvm6971 | configupdater MT local k5 (bundle 399dea35) | pyscaffold/configupdater | permissive helper / own reader hides damage | — | 5/5 / 4/5 (5/5 real) / 0/4 | s2: grading defect (upstream test_set pins old layout); s3 all stated (default ; comment as entry 4/4, ; comment dropped 3/4) | reshape: default-mode comment placement → s2 |
| 2026-10-03 | devvm23237 | django 2-step frozen bundle local Avocado k=5 | jazzband/django-model-utils | — | — | s1 5/5, s2 2/5 | s2: 3 semantic final-step failures | probe s1 3/5 did not hold under the full agent harness → single-turn downgrade |
| 2026-10-03 | devvm6971 | config-rs reshape s3 (c) rebase_layer / (c2) reconcile_layer cold | rust-cli/config-rs | natural order | — | 5/5 / 4/5 (19-test replay still 4/5) | 1 genuine None/Nil | PARKED |
| 2026-10-03 | devvm6971 | css-inline MT local k5 (bundle 48ea64da) | Stranger6667/css-inline | natural order | — | 5/5 / 5/5 / 4/5 (1 infra) | none genuine | local too easy; pushing for server gate (local≠server evidence: stjsonschema) |
| 2026-10-03 | devvm6971 | configupdater MT local k5 after reshape (bundle 206d9b3a) | pyscaffold/configupdater | permissive helper | — | 5/5 / 3/5 / 3/3 | s2 genuine: re-indent with inline comments; default ; as entry | s3 thin n=3 → server gate after test fixes |
| 2026-10-03 | devvm6971 | unleash MT chained | Unleash/unleash-go-sdk | natural order + permissive helper | 254/247/215 | 4/5 / 5/5 / 1/5 | s1: drops never-on flags (fallback true); s3: DATE_AFTER T vs T+1ns x4 | ACTIVE |
| 2026-10-03 | devvm23237 | django s3 apply_to(field) chained (n=3 valid of 8 launches) | jazzband/django-model-utils | permissive helper + constraint fights edit site | 236 | 0/3 | 3 stated, all the same field-constraint branch (max_length); 5 infra (orchestration/clone dropped dirty tree) | completing n=5 |
| 2026-10-03 | devvm23237 | crossplane server validation @a53a247 | crossplane/crossplane | — | — | avocado 4/5 (prev run 3/5) | — | VM build fixed; now 'too easy' at the line |
| 2026-10-03 | devvm23237 | django s3 apply_to(model field) chained, n=5 valid | jazzband/django-model-utils | permissive helper + constraint fights edit site | 236 | 0/5 | 5 stated, ALL the same CharField.max_length branch | single-branch cliff → AMEND = apply_to(forms.ChoiceField) |
| 2026-10-03 | devvm23237 | django s3 AMEND apply_to(forms.ChoiceField) chained n=5 | jazzband/django-model-utils | permissive helper (to_python vs full TypedChoiceField coercion) + atomicity | 221 | 3/5 | 2 stated (checked to_python, missed coerce collapse) | IN BAND → BUILD-3STEP |
| 2026-10-03 | devvm23237 | jsoup W3C mirror local Avocado k=5 (final graders) | jhy/jsoup | natural order loses information | — | 4/5, 4/4, 1/5 | all failures classified, 0 unstated | READY |
| 2026-10-03 | devvm23237 | jsoup W3C mirror FRESH local Avocado k=5 (frozen bundle ab96a56e) | jhy/jsoup | natural order loses information | — | 4/5, 3/4, 1/3 | 4 stated (2 assertion, 2 Java8/Android-API compile), 0 unstated, 0 infra | READY confirmed |
| 2026-10-03 | devvm23237 | django 3-step FRESH full-chain local Avocado k=5 + s3 checkpoint replays (bundle d6bfd01a) | jazzband/django-model-utils | — | — | s1 5/5, s2 2/5, s3 2/2 reached; replays 5/5 + 1/5 | all stated (s2 equal-label merge; s3 to_python vs clean) | READY (s3 at upper band edge, checkpoint-conditioned) |
| 2026-10-03 | devvm23237 | django s3 hardened grader, fresh cold 12 runs across 4 agent s2 states | jazzband/django-model-utils | permissive helper (to_python vs field.clean) + atomicity | 221 | 3/12 | stated | in band → fresh full-chain k=5 |
| 2026-10-03 | devvm23237 | redb 3-step MT chained Muse probe | cberner/redb | constraint fights natural edit site | 188/142/123 | 5/5, 5/5, 5/5 | 0 stated; 17 infra timeouts excluded | saturated |
| 2026-10-03 | devvm23237 | Prism relocation reshape: identity safety + unique shift recovery | ruby/prism | numeric identity too permissive / safe ambiguity rejection | — | 3/5, 1/5 | s1 two stated lazy-semantics failures; s2 four stated non-unique-counterpart rejections; 0 infra | IN BAND → ACTIVE 2-step |
| 2026-10-03 | devvm23237 | jsoup Session structural reshape | jhy/jsoup | mutable isolation / policy-resolved adoption | — | 5/5, 5/5, 5/5 | 0 genuine; 3 infra replaced | saturated after one reshape → RELEASED |
| 2026-10-03 | devvm23237 | AFDKO output-plan + atomic publication | adobe-type-tools/afdko | filesystem identity / failure atomicity | — | 5/5, 5/5 | 0 genuine; 6 infra excluded/replaced | saturated → one structural reshape, then RELEASE if repeated |
| 2026-10-03 | devvm23237 | django 3-step FRESH full-chain k=5 (frozen e735fb03) | jazzband/django-model-utils | — | — | 5/5, 3/5, 0/3 | 5 stated (2 s2 equal-label merge; 3 s3 not field.clean()-authoritative) | s3 overall 3/15 with hardening runs → borderline-hard |

## 2026-10-03 devvm6971 — go-zero redesign lessons
- The server read the previous version 1|0.8|1 (local 5/4/3): conservative 'any type change breaks' rules made step 3
  trivial. Restoring the TRUE runtime rule and stating only principle + authority gave local 3|1|1 with fair misses.
- Gotchas resurface when a brief lists them as requirements (header-only response member came back from my own
  redesign brief). Keep a per-task 'removed gotchas' list and paste it into every Codex brief.
- Step timeouts: 4/5 step-3 runs hit 1800s, 3/5 hit 3600s while still converging (edits + own tests to the end).
  Timeout-driven zeros are not difficulty; raise the budget rather than count them.
- push-task.sh on a task that already exists on remote: the local commit adds files as NEW and cherry-pick conflicts.
  Build the commit in a clean worktree on FETCH_HEAD: rm -rf dir, cp the local dir, git add -A, check name-status.
| 2026-10-03 | devvm6971 | css-inline reshape: s2 widened (all: revert-layer) / s3 keep_at_rules | Stranger6667/css-inline | — | — | 1/5 replay / 5/5 cold | s2 genuine (only impl4 handles all) | PARKED |
| 2026-10-03 | devvm23237 | kustomize replacement validate/atomic/compose 3-step chained | kubernetes-sigs/kustomize | constraint fights edit site (s2) + helper too strict (s3) | — | 5/5, 5/5, 5/5 | 0 | saturated → RELEASED (natural-impl failures in card evidence did not transfer to Avocado once rules stated) |
| 2026-10-03 15:12 | devvm6971 | server partials | unleash 1|1 (s1,s2 both 1.0 so far → will spend exemption twice); unyt d475038 0.8|0 (s2 now 0 after widening) | — | — | — | — | — | watch for final; prep reshape |
| 2026-10-03 | devvm23237 | connect-go prefixed mount 3-step chained | connectrpc/connect-go | constraint fights edit site + helper too permissive | — | 5/5, 5/5, 5/5 | 0 | saturated → RELEASED |
| 2026-10-03 | devvm23237 | django 3-step SERVER validation @4d23928 | jazzband/django-model-utils | — | — | avocado 1/0.8/0; gpt 1/1/1 | — | step gate failed: s2 4/5 (local 2/5, 3/5) |
| 2026-10-03 | devvm6971 | beancount MT chained | beancount/beancount | natural order + permissive balance check | — | 1/5 / 5/5 / 2/5 | s1: repeating cost unbalanced, costless holdings; s3: CIL price leaked as market price, 3.999 rounding | ACTIVE |
| 2026-10-03 | devvm6971 | cancancan MT chained (+widened probes, reshapes M1, N3) | CanCanCommunity/cancancan | permissive helper / no in-repo oracle | — | S1 5/5, S2 5/5 (20 cases), S3 2/5; M1 5/5; N3 5/5 | S3 genuine: exclusive Range end, nil in Array | reshape 3: accessible_by Range/nil as S3 |
| 2026-10-03 | devvm6971 | tera shape B chained | Keats/tera | natural order + permissive reverse lookup | — | 3/5 / 4/5 / 3/5 | s1 implicit @ params; s3 include-of-extending quirk (seed-line correlated) | ACTIVE |
| 2026-10-03 | devvm6971 | cancancan reshape 3 (accessible_by Range/nil S3) + single-turn fallback | CanCanCommunity/cancancan | — | 336 (ST) | S3 vacuous (9/9 at seed); ST 3/5 | ST genuine: exclusive Range end, nil in Array, attribute cases | DOWNGRADE → single-turn build |
| 2026-10-03 | devvm23237 | django rewrite: Muse s1 re-author + 2nd s2 branch (same label object reused by two group occurrences), fresh full-chain k=5 | jazzband/django-model-utils | — | — | s1 5/5, s2 0/5 (all fail only the new test), s3 unreached | 5 stated (single assertion) | single-branch cliff + fairness risk → awaiting Vidit (recommend drop new test, keep s1 rewrite) |
| 2026-10-03 | devvm23237 | crossplane hardened (2 stated fatal-response rules, Muse re-author, frozen graders) fresh k=5 | crossplane/crossplane | — | — | 5/5 | 0 | still too easy → awaiting Vidit (multi-step conversion vs park) |
| 2026-10-03 | devvm23237 | Prism frozen final bundle cross-model k=5 | ruby/prism | semantic identity / unique recovery | — | — | Avocado 5/5,0/5; Claude Opus 1/5,0/5; cold Codex 5/5,5/5 | final-step semantic miss genuine; reviewer found uniqueness-precedence ambiguity and stale step1 grader residue | Agentic review REVISE 0C/0H/5M; clarify contract/test hygiene then fresh rerun |
| 2026-10-03 | devvm23237 | FreeType SFNT snapshot + semantic delta | freetype/freetype | borrowed physical order / semantic equality | — | — | 5/5, 5/5 | 0 genuine; 5 invalid-model-alias launches excluded/replaced | saturated → one structural amendment, then RELEASE if repeated |
| 2026-10-04 | devvm23237 | spdlog versioned level policy + guarded restore | gabime/spdlog | natural order loses information | — | — | 5/5, 5/5 | 0 genuine; one pilot stream hang excluded/replaced | RELEASE: P5=2, final saturated, A1 AI-branch hard kill, atomicity not graded |
| 2026-10-05 | devvm23237 | Rich layout snapshot + subtree reconciliation | Textualize/rich | old-region information loss / locality | — | — | 5/5, 4/5 continued | one genuine final-step failure: full-row redraw rewrote named-pane locality; 5 invalid-model-alias launches excluded | AMEND once; P5=3, final >3/5 |
| 2026-10-05 | devvm23237 | Rich amended layout snapshot + subtree reconciliation | Textualize/rich | old-region information loss / stale-cell locality | — | — | 5/5, 1/5 adjudicated continued | raw s2 0/5; independent review removed one grader false negative; four genuine stale-cell misses | IN BAND → ACTIVE; P5=3 |
| 2026-10-05 | devvm23237 | Mockito checkpoint + phase verification + selective cleanup | mockito/mockito | shallow state / natural order loses information | — | — | raw 5/5,5/5,0/5; adjudicated 5/5,5/5,5/5 | five s3 grader false negatives from over-narrow message check; genuine continued sessions | saturated → one structural AMEND; P5=4 |
| 2026-10-03 | devvm23237 | redb drop with outstanding WriteTransaction recovery reshape | cberner/redb | failure-path quality / deferred lifecycle | 69 (new step) | fresh stated chain 5/5, 5/5; reader fork 3/5 | 0 stated failures in first two steps; reader fork was not yet stated | factual KILL: adding the 3/5 fork leaves two saturated non-final steps; one-exemption rule violated |
| 2026-10-03 | devvm23237 | Prism contextual identity three-step reshape | ruby/prism | contextual lineage / chained reachability | final step 5/5 isolated | full chain 2/5, 0/2, 0 reached; isolated final 5/5 | 0 invalid in replacement run | factual KILL: no measured in-band final chain after bounded reshape |
| 2026-10-03 | devvm23237 | JoinQueryset lifetime/composition reshape | jazzband/django-model-utils | independent lifetime / composed deep-copy retention | amended step 2 already 4/4 | original 5/5,5/5; fair reshape 5/5,5/5; amendment 5/5 then 4/4 | earlier 3/5 was unstated and excluded | factual KILL: fifth result cannot lower 4 passes to the 3/5 ceiling |
| 2026-10-03 | devvm23237 | grouped-selection server-calibrated step-2 repair | jazzband/django-model-utils | group declaration occurrence / concrete Choices class | 66 required step-2 tests | fresh full chain 5/5,5/5,1/5 | 0 invalid; all five solvers satisfied both added obligations | NOT-IN-BAND; revision not pushed, new product behavior required |
| 2026-10-03 | devvm23237 | FreeType structural amendment: merged snapshot+delta then three-way reconcile | freetype/freetype | memory ownership / per-slot reconciliation | frozen contracts and 3 graders | 3/5, 5/5 | step1: 2 substantive memory failures; final: 0 failures | factual KILL: final saturated after sole amendment; no scaffold |

## 2026-10-03 devvm6971 — read the Agentic Full-Task Review with `codimango job review <task>`
- `task errors` only says "Agentic full-task review: BAD_GRADING_WEAK"; the TBR bot comment can say PASS at the same
  time. The actionable text (rubric fails + Author Feedback) is ONLY in `codimango job review <task>`.
- go-zero: calibration passed 1|0.2|0.6 but AFR failed on one untested golden bug (response *string -> any treated
  as breaking). Coverage gaps where the oracle is conservative are graded as BAD_GRADING_WEAK + BAD_GOLDEN.
| 2026-10-03 | devvm23237 | card3 'existing component is the authority' screen (franz-go, jsonschema, net-imap) | — | authority trap | — | NO-CARD | franz-go authority already production logic; jsonschema A4 same-seam collision + public disclosure; net-imap authority contract contrary | no card |
| 2026-10-03 | devvm6971 | eventsourcing MT chained (+extra tests, 2 replacement last steps) | pyeventsourcing/eventsourcing | — | — | S1 5/5, S2v2 3/5, S3 5/5, alt-S3 5/5 x2 | S2 genuine (raise CompactedVersionError instead of using readable snapshot) | one last try (archive step) then park |
| 2026-10-03 | devvm6971 | jsonargparse MT (persistent / dump_overrides+removal / layer order by selection) | omni-us/jsonargparse | permissive helper | — | 5/5 / 3/5 / 4/5 | s1 0/5 earlier = ambiguous --config clause (fixed); s3 1 genuine | last too easy → reorder (profile step last) |
| 2026-10-03 | devvm6971 | tera K-to-N local | Keats/tera | — | — | S1 3/5, S2 5/5, S3 5/5 (7/7 indep) | S1: cross-template binding (wording unfair) + implicit params | last saturated → one bounded reshape else park |

## 2026-10-03 devvm6971 — route-table-difference died 5/5/5: probe the hard step BEFORE building
- Codex's obvious implementation (one sample per pattern) missed differences behind a shared literal; Avocado did
  not -- it enumerated per-position literals + one fresh value, which covers every region of a small route
  language. Third time a Codex falsifier mispredicted Avocado (gobgp x2, route). Treat falsifiers as necessary,
  never sufficient.
- Constructive-witness only splits solvers when the authority is RICH (go-zero decoder semantics -> server 0.6);
  over a small language the search is easy. Prefer witness steps over rich runtime semantics.
- Skipping Lane P cost ~1.5h. Lane P = build ONLY the candidate hard step as a zz-probe task (oracle seeds earlier
  steps), Avocado contract, k=5, before any full build.
| 2026-10-03 | devvm6971 | bdays MT chained (+S2 fuzz) | felipenoris/bdays | natural order + permissive helper | 340/242/225 | 5/5 / 5/5 / 5/5 | 0 | PARKED |
| 2026-10-03 | devvm6971 | jsonargparse v3 chained (persistent / removal+subsection / profile) | omni-us/jsonargparse | permissive helper | 344/297/292 | 1/5 / 2/5 / 4/5 | s3 1 genuine (net-effect replay) | last too easy → shape A (dump basic exempt, removal+profile last) |

## 2026-10-03 devvm6971 — kustomize FieldSpec witness probe: 1/5 graded, 4/5 fair -> parked
- Lane P worked: single-step zz-probe of the last step, Avocado contract, oracle 3/3, k=5 -> answer in ~1h, no build.
- 4/5 failures were one unstated rule (witness must carry apiVersion/kind); Avocado's contract dropped the word
  "Kubernetes" from the obligation. Real difficulty = 1/5 misses -> too easy for a last step.
- Codex, asked to build a probe, went on to run sequential `muse exec` solver trials itself (90-min caps). Briefs
  must say: build only; never run solver/agent trials.
- Pattern across today's 3 witness cards (route, fieldspec, go-zero s3): construction over the repo's real
  behaviour is EASY for Avocado unless the semantics are rich and partly non-obvious-but-probeable (go-zero decoder).
| 2026-10-03 | devvm6971 | jsonargparse shape A chained | omni-us/jsonargparse | permissive helper | — | 1/5 / 2/5 / 0/5 | s3 uniform cliff (env below config-selected +/- key) | ship 2-step (S1+S2) |
| 2026-10-03 | devvm6971 | tera reshape R chained | Keats/tera | — | — | R1 2/5, R2 v1 5/5 / v2 4/5, R3 v2 5/5 | R2 genuine super()-reached set; R3 saturates once @ params named | PARKED |
| 2026-10-04 | devvm6971 | rfc3986 MT chained (+fuzz, fallback S3) | python-hyper/rfc3986 | permissive helper / spec authority | — | S1 4/5, S2 3/5 (after §4.1 authority amend; 0/5 before), S3 5/5 (6390-pair fuzz agrees), S3' 5/5 fair | S2 genuine §4.1 bidi | MT no; single-turn fallback probe |
| 2026-10-04 | devvm6971 | rfc3986 single-turn (normalize + to_iri) | python-hyper/rfc3986 | spec authority | 248 | 0/5 | all miss §4.1 (MT chain S2 was 3/5 with same wording) | PARKED — evidence MT > ST |

## 2026-10-04 devvm6971 — go-zero inherit-schema witness probe: 3/5 graded, 5/5 fair -> parked
- Both misses: the test's 'independent deep copy' was a JSON round trip, turning a Go int into a JSON number and
  changing the decoder's error text; the contract never said copies go through JSON. Harness gotcha, not reasoning.
- Score for the day's witness cards (fair): route 5/5, fieldspec 4/5, inherit-schema 5/5; only go-zero decoder
  compat witness split (server 0.6). Construction over repo behaviour is easy for Avocado unless the authority has
  many interacting, non-obvious rules. Next batch: target rich-semantics authorities (strategic merge patch, etc.).
| 2026-10-04 | devvm6971 | beancount server history | beancount/beancount | — | — | v1 1|0|NA (gpt 1|.6|1); v2 1|1|.6; v3 .6|0|NA (gpt 1|1|1) | s2 cliff on stating plugin interaction | reshape routes A+B |
| 2026-10-04 | devvm6971 | rfc3986 2-step (S2 = §4.1 only) | python-hyper/rfc3986 | spec authority | — | S2 5/5 | — | sole-ask saturates; §4.1 splits only embedded (3/5) → try 3-step with new S3 IRI→URI |
| 2026-10-04 | devvm6971 | beancount replay on server trees (routes A+B) | beancount/beancount | — | — | s1 new exactness tests: v2 5→4/5, v3 3→1/5; s3 new cases: gpt 5→3/5, avocado unchanged | genuine residues / phantom share / decimal crash | install both, no s1 re-author |
| 2026-10-04 | devvm6971 | jsonargparse 2-step local k5 | omni-us/jsonargparse | — | — | S1 5/5 (probe 1/5), S2 ~1-3/5 | S2 genuine subcommand-reproduce + borderline env-config case | → 3-step: S1 exempt, S2 dump, S3 removal+subsection (v3 2/5) |

## 2026-10-04 devvm6971 — SPARQL counterexample card killed before probe: fair contract = the algorithm
- Grading "no counterexample" fairly requires stating the finite search space; Codex's fair obligations then had to
  specify vocabulary construction and visit order, i.e. the brute-force procedure, which runs in 0.6s.
- Rule: a witness/counterexample step whose completeness can only be graded inside a stated finite space is
  mechanical by construction. Check this at card time (time the naive enumeration) before any probe.
| 2026-10-04 | devvm6971 | rfc3986 3-step new S3 (legacy charset → URI §3.1) | python-hyper/rfc3986 | spec authority | — | 0/5 (v1), 0/5 (v2) | genuine: no NFC for legacy input / NFC applied to Unicode input | PARKED |
| 2026-10-04 | devvm6971 | jsonpath merge-patch chained | jg-rp/python-jsonpath | permissive helper | — | S1 5/5; S2 v1 4/5, v2b 0/5, v2c 5/5 (cliff on naming §4.6); S3 5/5 x2 | S2 genuine test-op equality | levers: issue-level S2 + document-free S3 |
| 2026-10-04 | devvm6971 | jsonargparse shape B S3 (removal+subsection, no env cliff) | omni-us/jsonargparse | — | — | 4/4 | 0 | saturated; try S3 with env cliff + third-party (codex) check |
| 2026-10-04 | devvm6971 | jsonargparse S3 + env case, third-party check | omni-us/jsonargparse | — | — | avocado 0/5, codex 5/5 | avocado: +/- applied over default not env | PARKED |
| 2026-10-04 | devvm6971 | dropshot-websocket phase-2 probes | oxidecomputer/dropshot | — | — | S2 5/5, S2b 5/5; S3 0/4, S3b 0/5 (uniqueness cliff); validity subset 2/5; codex S3 1/2 | partial-list trap explained S1 0/10 | try macro-declaration middle, validity last |
| 2026-10-04 | devvm6971 | dropshot M2 (#[channel] decl) / V2 variant | oxidecomputer/dropshot | — | — | 5/5 / 5/5 | 0 | only one non-cliff weak spot (empty-element leniency ~2/5) → single-turn fallback |
| 2026-10-04 | devvm6971 | jsonpath cycle X: S2d issue-level / S3x document-free | jg-rp/python-jsonpath | permissive helper | 223/178 | S2d 1/5, S3x 0/5 (grader unsound) | S2d genuine §4.6 test equality | single-turn apply+S2d |
| 2026-10-04 | devvm6971 | pyhms RFC 9421 shape R | pyauth/http-message-signatures | spec authority | — | probe 3/5|4/5|1/5; local bench (internet on) 5/5|5/5|4/5 | bench reads RFC | push for server after reviewers |
| 2026-10-04 | devvm6971 | dropshot single-turn | oxidecomputer/dropshot | — | 319 | 0/5 | all reject alpha,,beta (wording-sensitive: 1/4, 3/5, 5/5) | one more ST with S3b wording |
| 2026-10-04 | devvm6971 | jsonpath single-turn (apply + to_merge_patch S2d) | jg-rp/python-jsonpath | — | 262 | 0/5 | all §4.6 test equality | PARKED |
| 2026-10-04 | devvm23237 | i18next hierarchy cache 3-step chained | i18next/i18next | existing component is the authority (fresh LanguageUtils) | 184/181/229 | 5/5, 5/5, 5/5 | 0 | saturated → RELEASED |
| 2026-10-04 | devvm23237 | Ecto semantic changeset merge 3-step chained | elixir-ecto/ecto | existing component is the authority (Ecto.Type.equal?, relation metadata) | 249/216/244 | 3/5, 1/5, 0/5 | stated, multiple modes per step | IN BAND (server-calibrated) → BUILD |
| 2026-10-04 | devvm6971 | pyhms RFC 9421 server | pyauth/http-message-signatures | — | — | server 1|1|1 = local bench 5|5|4, NOT probe 3|4|1 | — | bench is the predictor (correction) |
| 2026-10-04 | devvm6971 | robotstxt chained cold probe (+S4) | temoto/robotstxt | — | — | 4/5, 5/5, 4-5/5, S4 4/5 | single-impl misses only | PARKED |
| 2026-10-04 | devvm6971 | franz-go server diagnosis | twmb/franz-go | — | — | history 5|5|4 → 5|5|5 → de-scaffold 0 (all models) | s1 all fairness: unstated dedup/skip/nil, unnamed signature, empty-name contradicts Kafka | reshape: s1 fair exempt, s2/s3 own Kafka-defined difficulty |
| 2026-10-04 | devvm23237 | oclif parsed flag-spelling provenance 3-step chained | oclif/core | parser is the authority | 248/—/— | 5/5, 0/5, 5/5 | s2: 5 stated (one shared miss); s3 none | NOT BUILD (last step saturated) → RELEASED; reuse s2 trap |
| 2026-10-04 | devvm6971 | franz-go reshape benches | twmb/franz-go | — | — | bench2 5|5|4, bench3 3|3/3|2/2 (+replay harder cases still pass) | avocado webfetches Kafka source | PARKED |
| 2026-10-04 | devvm23237 | trio lossless close failures 3-step chained | python-trio/trio | BaseExceptionGroup/CancelScope authority | — | 5/5, 1/5, 5/5 | s2: 2 independent stated modes | last step saturated → single-turn s1+s2 fallback |
| 2026-10-04 | devvm23237 | graphql-ruby profile-aware export 3-step chained | rmosolgo/graphql-ruby | Visibility::Profile authority | — | 5/5, 5/5, 2/5 | s3 stated | middle saturated → single-turn fallback |

## 2026-10-04 devvm6971 — contract-style experiment on merge3 (same tests, two contracts)
- Case-listing contract: 5/5. Principle + authority only: 4/5 (one broad incomplete impl). Style matters a little;
  the semantics decide. The in-band go-zero step 2 combines BOTH: principle-only AND a rich decoder.
| 2026-10-04 | devvm23237 | oclif s3 LAY-voice re-probe (on passing s2) | oclif/core | — | lay | 5/5 | 0 | lay voice did not help: step-3 operation itself is easy → needs a new last step |
| 2026-10-04 | devvm6971 | actix-files bench (internet on) | actix/actix-web | — | — | S1 15/15, S2 7/15 (HEAD), S3 7/8 | S2 HEAD miss via compat clause | one move-4 attempt (merged S1, new S3) |
| 2026-10-04 | devvm6971 | jgit cold chained | eclipse-jgit/jgit | — | — | 5/5 (fair) / 5/5 / 5/5 | none | PARKED |
| 2026-10-04 | devvm23237 | trio s3 LAY re-probe | python-trio/trio | — | lay | 5/5 (strict 4/5) | 0-1 | lay voice did not help; operation easy → new last step |
| 2026-10-04 | devvm23237 | graphql s2 LAY re-probe | rmosolgo/graphql-ruby | — | 146 | 4/5 | 1 fair (custom directive definition omitted) | still too easy for middle step |
| 2026-10-04 | devvm23237 | trio new s3 aclose_forcefully on StapledStream | python-trio/trio | StapledStream close authority | — | 5/5 | 0 | saturated (4th s3 design) → 2-step pivot |
| 2026-10-04 | devvm23237 | jsoup s3 LAY re-author (full-chain fresh local k=5) | jhy/jsoup | — | lay | s3 4/5 | 1 | lay voice made this step EASIER (spec version ~1/3 locally) → not pushed. LESSON: R-008 is not a universal difficulty lever; measure before pushing |
| 2026-10-04 | devvm23237 | oclif new s3 jsonEnabled() follows parser | oclif/core | parser authority | 196 | 5/5 | 0 | saturated → 2-step pivot |
| 2026-10-04 | devvm23237 | graphql NEW middle (operational-envelope projection) + s3 re-check | rmosolgo/graphql-ruby | printer full SDL authority | 173 | s2 2/5, s3 3/5 | s2: 2 independent modes | IN BAND → BUILD |
| 2026-10-04 | devvm23237 | trio 2-step (lay s1) | python-trio/trio | — | lay | s1 5/5, s2 0/5 | s2: 2 modes | lay s1 still saturated → split s2 |
| 2026-10-04 | devvm23237 | oclif 2-step (lay s1) | oclif/core | — | lay | s1 5/5 | — | lay s1 saturated → test split |
| 2026-10-04 | devvm23237 | Ecto fresh full chain with LAY s1+s2 | elixir-ecto/ecto | — | lay | 5/5, 5/5, 0/5 | s3: 3 semantic areas | lay rewrite made s2 easy (was 1/5) → restore original s2. LESSON (2nd case after jsoup): R-008 can REMOVE difficulty from a step that already split solvers — keep measured in-band contracts, apply lay voice only to new or saturated steps |
| 2026-10-04 | devvm23237 | typesetting-caret-hit-testing | chained metacode k=5 | 5/5, 4/5, 4/4 | saturated S3 → amend |
| 2026-10-04 | devvm23237 | mathjs-replay-under-other-instance | chained metacode k=5 | 5/5, 5/5, 5/5 | saturated → amend or release |
| 2026-10-04 | devvm6971 | http-cookie chained cold + internet proxy | sparklemotion/http-cookie | spec authority | — | S1 0/5→5/5 amended; S2 0/5 cold, 5/5 internet; S3 5/5 | S2 cold misses: exact-bucket only | PARKED |
| 2026-10-04 | devvm6971 | lektor bench1 (internet on) | lektor/lektor | — | — | S1 5/5, S2 3/5, S3 3/3 | S2 attachment old-URL; S3 sat; 1 discriminator found (old-version leftover thumbnail, 9/10 miss) | revert order + add S3 discriminator |
| 2026-10-04 | devvm23237 | trio-split | Muse impls | 5/5, 2/5, 5/5 | final step saturates → retired |
| 2026-10-04 | devvm23237 | typesetting-amend | continuation metacode k=5 | 5/5, 0/5, — | S2 single-mode cliff → wording-only remeasure |
| 2026-10-04 | devvm6971 | actix-files final reshape bench r3 | actix/actix-web | — | — | 5/5 / 5/5 / 5/5 | none | PARKED |
| 2026-10-04 | devvm23237 | typesetting-amend-w | continuation metacode k=5 | 5/5, 0/5, — | released |
| 2026-10-04 | devvm23237 | pendulum | continuation metacode k=5 | 5/5, 0/5, — | S2 fold-collapse cliff → one wording amend |
| 2026-10-05 | devvm6971 | lektor bench3 (pile stated) | lektor/lektor | — | 246 (S3) | 5/5 / 4/5 / 4/4 | S2 attachment old-URL; pile 0/8 unstated → 4/4 stated | PARKED (revival path noted) |
| 2026-10-05 | devvm23237 | tinycss2 | continuation metacode k=5 | 5/5, 4/5, 4/4 | released |
| 2026-10-05 | devvm23237 | pendulum-amend | continuation metacode k=5 | 5/5, 1/5, 1/1 | S2 in band; S3 measuring |

## 2026-10-04 devvm6971 — protobuf-go compatibility probe: bimodal, parked
- Two probes, 0/5 each. With the JSON meaning stated precisely, ALL five trials failed exactly two assertions and
  passed everything else: (1) open enum gains a name for a number the old schema could still produce (uniform
  insight miss); (2) bytes->string JSON, where my 'round-trip identical' definition was satisfied but the test wanted
  incompatible -- a definition I wrote that contradicted the grader. Check every stated definition against EVERY
  graded case before authoring, not just the ones that motivated it.
- Remove (1) -> 5/5; keep it -> 0/5. AND-composed tests + one uniform insight = bimodal, never in band.
| 2026-10-05 | devvm6971 | lektor v2 bench4 | lektor/lektor | — | — | 4/5 / 1/4 / ≥4 proj | S2 upgrade-leftover misses; S3 solved incidentally in S1 trees | RESHAPE → 2-step |
| 2026-10-05 | devvm23237 | pendulum-amend | K-to-N metacode k=5 (2 seed trees) | S1 5/5, S2 in band, S3 4/5 | OUT (final step too easy) |
| 2026-10-05 | devvm6971 | lektor v3 bench5 | lektor/lektor | — | — | 4/5 / 0/4 / NA | S2 cliff on old-folder leftovers | PARKED |
| 2026-10-05 | devvm23237 | typesetting-original | K-to-N metacode k=5 (5 S1 trees, 3 S2 trees) | 5/5, 3/5, 5/5 | OUT (final step saturates) |
| 2026-10-05 | devvm23237 | tinycss2 | K-to-N metacode k=5 | 5/5, 5/5, 5/5 | OUT |
| 2026-10-05 | devvm23237 | mathjs | K-to-N metacode k=5 | 5/5, 5/5, 5/5 | OUT |
| 2026-10-05 | devvm23237 | mockito checkpoint structural amend | fresh-session analogue from 5 distinct real passing parents | foundation 5/5; final 5/5 (continued), 5/5 (fresh seeded) | 15 genuine passes, 0 genuine misses or exclusions; independent review PASS; RELEASED |
| 2026-10-05 | devvm23237 | picocli detached parse overlay amend | server-faithful K-to-N metacode k=5 | raw 5/5, 2/5, 3/5; effective S2 5/5 | three S2 false negatives rely on unstated converter-count/root-identity checks; one S3 verifier pass retains regression; independent review REVISE, sole amend consumed; RELEASED |
| 2026-10-05 | devvm23237 | deno_graph | K-to-N metacode k=5 | 5/5, 5/5, 5/5 | released |
| 2026-10-05 | devvm23237 | open-feature | K-to-N metacode k=5 | 5/5, 5/5, — | released (S2 stop) |
| 2026-10-05 | devvm23237 | rope | K-to-N metacode k=5 (4-5 distinct seeds) | 4/5, 5/5, 2/5 | S1+S2 both >3 → amend (merge), S3 in band |
| 2026-10-05 | devvm6971 | jotdown fix5 route A | hellux/jotdown | — | 309 (S3) | 3/5 / 2/3 / 0/2 (codex S3 5/5) | S3 cliff on inherited attrs sentence | PARKED |
| 2026-10-05 | devvm23237 | pendulum-salvage | K-to-N metacode k=5 | 5/5, 2/5, 2/5 | IN BAND → build |
| 2026-10-05 | devvm6971 | isogit stash bench | isomorphic-git | — | 239/232/189 | 3/5 / 3/3 / 3/3 | S1 symlink only split; S2/S3 no web, saturated | PARKED |
| 2026-10-05 | devvm23237 | sequelize-journal | K-to-N metacode k=5 | 1/5 raw (fair 5/5), 5/5, 2/5 raw (grader FN) | released (S2 saturates) |

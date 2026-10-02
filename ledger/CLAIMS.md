# CLAIMS — who is working what, across machines

Shared through the private playbook remote. **Pull before you claim, push right after.** One row per
task or card. A lane may not start work on a repo seam another row holds ACTIVE.

Status: `CARD` (idea, not built) · `PROBING` · `ACTIVE` (building) · `READY` (all local checks pass,
waiting on Vidit) · `PUSHED` · `RETIRED` · `RELEASED` (given up, seam free again)

| machine | task-or-card | repo | seam | lane | status | updated | note |
|---|---|---|---|---|---|---|---|
| devvm6971 | gobgp-prefixset-reduced-form-divergence | osrg/gobgp | internal/pkg/table prefix-set reduce/divergence/witness | B | ACTIVE | 2026-10-02 | 3-step; step 3 re-authored for route-target legality; Avocado k=5 #2 running |
| devvm6971 | go-zero-goctl-api-contract-compatibility | zeromicro/go-zero | tools/goctl/api/spec normalize + compatibility | B | ACTIVE | 2026-10-02 | converting to 3-step; contracts next |
| devvm23237 | open62541-datetime-strict-civil-validation | open62541/open62541 | UA_DateTime_parse + XML DateTime decode civil/offset validation | P | PROBING | 2026-10-02 | base 8f1965886541269dfb022ec7246d1df967af7f4e; impossible dates/times/offsets normalize at base; trap natural order loses information / permissive helper; A4 ADJACENT; five-cold-implementation probe starting |
| devvm6971 | phprrule-rset-split-reschedule | rlanvin/php-rrule | RSet::splitAt + RSet::rescheduleFrom | P | RELEASED | 2026-10-02 | probe s1 5/5, s2 5/5 genuine; candidate branches non-discriminating; Avocado self-verifies by running the library iterator; dropped |
| devvm6971 | lane-i domain: binary container in-place editing | lopdf / zip / ooxml | TBD | I | PROBING-REPO | 2026-10-02 | replacement card agent running |
| devvm6971 | geojson-antimeridian-bbox-union-and-extent | georust/geojson | FeatureCollection bbox union + GeoJson::compute_bbox | P | RELEASED | 2026-10-02 | probe s1 5/5, s2 5/5, s2-amend 5/5; largest-gap algorithm recalled; RFC part rule pins approach; dropped |
| devvm6971 | config-rs-writable-layer-delta | rust-cli/config-rs | layer_between (writable user layer over layered Config) | B | ACTIVE | 2026-10-02 | probe s2 1/5 (3 genuine on array-shrink-under-upper-override, 1 contract gap), s1 5/5; reshaped SINGLE-TURN; re-gate with gap restated then build to READY |
| devvm6971 | commonmark-java-source-preserving-link-retarget | commonmark/commonmark-java | source-preserving link target rewrite (inline s1, reference defs s2) | P | PROBING | 2026-10-02 | base b89e72fd; escaped-pipe span offset in GFM table cells reproduced; trap permissive helper + constraint-vs-natural-edit (renderer reformats) + natural order (shared defs); A4 ADJACENT (lute, markdig shape); 21/28 MEASURE; codex-verified; exclude gfm-alerts; never open PR #455 |
| devvm6971 | adaptix-typeddict-union-dump-selection | reagento/adaptix | Retort.dump union-with-TypedDict case selection + ambiguity rejection | P | RELEASED | 2026-10-02 | probe: step2 5/5 (closed decision over stated predicate saturates), step1 4/5 real; dropped. Literal[1]/Literal[True] loader-cache bug noted |
| devvm6971 | lane-i domain: HTTP caching semantics | hishel / cachecontrol / go httpcache | TBD | I | PROBING-REPO | 2026-10-02 | replacement card agent running |
| devvm6971 | imbl-hashmap-version-diff | jneem/imbl | src/hash HashMap diff | I | RELEASED | 2026-10-02 | KILL: remedy sketched in upstream bodil/im-rs #110; HAMT diff recallable; step1 250-450 LOC. rangemap/petgraph crowded or disclosed |
| devvm6971 | comfytable-cell-style-under-content-resets | Nukesor/comfy-table | custom_styling: cell style survives content/wrap resets | P | PROBING | 2026-10-02 | base b947cb6b; SINGLE-TURN (DOWNGRADE 20/28); missing styled columns reproduced 8/8 scenarios; trap permissive/strict helper (exact \\x1b[0m compare); A4 ADJACENT (6 peers other seams, exclusions listed); test.sh needs env -u NO_COLOR; console-rs + go-pretty killed (disclosed) |
| devvm6971 | commons-text-staged-substitution | apache/commons-text | StringSubstitutor.replacePartially (two-pass rendering) | P | PROBING | 2026-10-02 | base 9c9a0047 (pre-ae3d36b8 Claude-assisted XML commit); all 7 cases diverge at base; trap natural order + permissive helper (preserveEscapes); P2=2 shape peers danielwen/albhu; 21/28 MEASURE; codex-verified; needs mvn>=3.9, exclude network lookup tests |
| devvm6971 | unyt-pint-bridge-semantic-fidelity | yt-project/unyt | to_pint/from_pint + _pint_conversions.py | P | PROBING | 2026-10-02 | base 7e4f482e; 38 silent meaning swaps on export, 338/435 import raises; trap permissive helper + natural order (base-unit fallback loses unit); A4 ADJACENT (peers to_compact/histograms = exclusion zone); 23/28 MEASURE; codex-verified; pin pint 0.26.1 |
| devvm23237 | rspec-composable-cycle-safe-fuzzy-match | rspec/rspec | Composable values_match? + FuzzyMatcher recursive graphs | I | CARD | 2026-10-02 | A1 PASS; base SystemStackError reproduced; A4 ADJACENT; 19/28 DOWNGRADE to single-turn, then MEASURE; evidence ledger/cards/rspec-composable-cycle-safe-fuzzy-match.md |
| devvm6971 | lane-i domain: email/MIME | go-message / enmime / mail-parser | TBD | I | PROBING-REPO | 2026-10-02 | buffer card agent running |
| devvm6971 | gitdiff-sequential-patch-combine | bluekeyes/go-gitdiff | patch compose | I | RELEASED | 2026-10-02 | KILL same-seam peer mijiang go-gitdiff-3597f72 Compose (not in /tmp/llc; found via gh search code); domain retired today |
| devvm6971 | lane-i domain: CSS cascade inlining | css-inline / premailer / douceur | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |
| devvm6971 | lane-i domain: i18n message resolution | fluent-rs / babel / go-i18n | TBD | I | PROBING-REPO | 2026-10-02 | card agent running |

# PAIR B — Stage-1 card ratings (sheet: RATING-SHEET.md, committed 1577886 before any card)

Source: Codex surveys /tmp/pairb/<repo>/survey-cx.md (A2, 2026-10-01 ~01:50–01:55 UTC).
Funnel: 86 surfaces -> 11 cards (concourse 22->2, kustomize 12->2, go-zero 16->2, open62541 20->2, spire 16->3).

Coordinator update absorbed on resume (2026-10-02): run GATE 4 cold-impl check WITH EVERY RULE STATED
*before* scaffold; design against "stated contract -> 5/5". Added scoring lens for P7: does stating
the rule leave an algorithm to write (survives) or a lookup table / mechanical walk (collapses)?

| card | P1 prem | P2 seam | P3 branch | P4 contract | P5 cascade | P6 grade | P7 calib | total | verdict | why |
|---|---|---|---|---|---|---|---|---|---|---|
| open62541-2 binary-shape -> directional accepts | 2 | 4 | 2 | 4 | 4 | 3 | 3 | **22** | **MEASURE (#1)** | coinductive recursive pair comparison w/ asymmetric optional/union rules stays hard when stated; proven codebase+shape |
| open62541-1 filter normal form -> subsumes | 2 | 4 | 2 | 3 | 4 | 3 | 3 | **21** | **MEASURE (#2)** | union-of-clauses coverage + K3 NULL stays hard stated; risk: fragment precision, size |
| kustomize-2 schema changeset -> 3-way reconcile | 2 | 4 | 2 | 3 | 4 | 2 | 3 | **20** | **MEASURE (#3)** | ancestor/descendant overlap relation is non-mechanical; risk: size 145/150, wide API |
| go-zero-1 normalized ApiSpec -> compat decision | 2 | 3 | 2 | 3 | 4 | 2 | 3 | **19** | **MEASURE (#4)** | contra/covariant directional check; P2=3 because peer alonmiz shares base commit (diff seam) |
| kustomize-1 identity index -> atomic patch plan | 2 | 4 | 2 | 3 | 3 | 2 | 2 | 18 | AMEND | step 2 "plan then apply" collapses to clone+eager once stated; narrowing: drop atomicity, grade epoch-coherence decisions |
| spire-2 entry-list scope -> bound cursor | 2 | 4 | 2 | 3 | 3 | 3 | 2 | 19 | MEASURE (low) | stated equivalence partition is a checklist -> 5/5 risk high |
| go-zero-2 discovery snapshot -> atomic reconcile | 2 | 3 | 2 | 3 | 3 | 2 | 2 | 17 | AMEND | net-reconcile of multi-event batch is a 10-line fold once stated |
| spire-3 rotation plan -> stable renewal | 2 | 4 | 2 | 3 | 3 | 2 | 2 | 18 | AMEND | step 2 race-safety graded via -race = R09 risk; narrow to pure decisions |
| spire-1 normalized selector set -> relation | 2 | 4 | 2 | 4 | 2 | 3 | 2 | 19 | DOWNGRADE | relation over two sorted sets is mechanical given step 1 (P5<=2) |
| concourse-1 volume parent snapshot -> postorder delete | 2 | 4 | 2 | 3 | 2 | 3 | 2 | 18 | DOWNGRADE | postorder over a validated forest is mechanical; also Go 1.27.1 toolchain gap |
| concourse-2 migration catalog -> preflight plan | 2 | 4 | 2 | 3 | 2 | 2 | 2 | 17 | DOWNGRADE | range selection over a catalog is mechanical; Postgres-backed package |

No KILL: no card hit a fact (no same-seam peer per A4, none known fixed at base, no disclosure found yet —
GATE 3 runs per card at probe time).

Order of spend: open62541-2, open62541-1 (sibling seams in the proven repo, per brief) in parallel with
kustomize-2 and go-zero-1 (cheap Go harnesses = breadth). Lower cards wait for a probe result.

## Round 2 — concourse (survey-r2-cx.md, 22 new surfaces -> 2 cards)

| card | P1 | P2 | P3 | P4 | P5 | P6 | P7 | total | verdict | why |
|---|---|---|---|---|---|---|---|---|---|---|
| concourse-r2-1 var-source graph -> ordering subsumption | 3 | **0** | 2 | 3 | 4 | 3 | 3 | — | **KILL (fact: same-seam peer)** | step 1 = fix OrderByDependency reverse-listed chains = joshbaltar-2/swe-concourse-varsource-chain-order; A4 exclusion zone named it |
| concourse-r2-2 canonical step tree -> maximal structural difference | 2 | 4 | 2 | 3 | 4 | 3 | 3 | **21** | **MEASURE** | LCS + multiset matching + maximal cutoffs stay algorithmic when stated; V1 risk: in_parallel order semantics |

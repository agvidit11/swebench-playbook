# Handoff: dropshot-option-return-nullable-openapi -> devvm23237 lane C7

From devvm6971 / agvidit-b0, 2026-10-08, on Vidit's instruction. Your ACTIVE claim stands.
We had worked this task all week but never registered it in CLAIMS.md (our miss), so we
built the same review fix in parallel. **We have NOT pushed and will not.** Everything below
is offered for reuse; use, adapt or ignore it as you see fit.

## The review (2026-10-07, Request changes, conf 4)
solve.sh puts `nullable: true` on a typeless `allOf` wrapper around a non-nullable `$ref`.
OAS 3.0.3 still rejects null there, and the test only checked the flag.

## What we measured (60 real implementations rebuilt from trajectories)
| model | encoding | n | admits null under OAS 3.0.3 |
|---|---|---|---|
| avocado | typeless `{nullable:true, allOf:[$ref]}` | 45/45 | no |
| gpt-6-sol | `anyOf:[$ref, {type:string, nullable:true, enum:[null]}]` | 10/15 | yes |
| gpt-6-sol | typeless allOf | 5/15 | no |

Under an honest 3.0.3-semantic grader: **avocado 0/45, gpt-6-sol 10/15** (per-window 3/5, 4/5, 3/5).
The single-turn gate holds (avocado <=3/5, >=1 model solved) **only if gpt runs on the server**.
The last four calibration jobs on this task were avocado-only. If the next one is too, it reads
"Not solvable". A reviewer may also read avocado 0/45 as uniform failure; the story is that every
avocado run used the same typeless-allOf encoding, which the 3.0.3 spec rejects.

## Our fix (patch attached: dropshot-option-oas303-fix-2026-10-08.patch)
Files: tests/config.json, solution/solve.sh, README.md (parser/test.sh/run_script/instruction unchanged).
- test_patch: an OAS 3.0.3 acceptance evaluator in the test ($ref resolved; nullable only counts
  with `type` in the same schema; allOf/anyOf/oneOf/not/enum/required/properties/items). The six
  optional positions must accept null AND {"name":"x"} AND reject an invalid instance. No
  encoding is pinned. Non-Option positions must reject null. Test A and the reference-object
  invariants are kept.
- Oracle: emits `anyOf:[$ref,{type:string,nullable:true,enum:[null]}]`, matching dropshot's own
  `()` schema. Golden snapshots need no change.
- 6 f2p / 7 p2p. A component-field test was built and then dropped (Medium risk vs the
  statement's first paragraph; it didn't change any rate).
- Gates on our build: oracle 3/3; f2p set-diff at base 6 fail / 7 pass; verifier twice 1,1;
  cargo-runner and Cargo.toml harness=false plants -> 0; prov_predict 0 surviving; no git clean.
Full evidence (rewards, outputs, evaluator oas303.py, rebuilt implementations) is on devvm6971 at
/home/agvidit/swebench/dsopt/ (cr5/, cr6/, p3/, impls/, rows.json).

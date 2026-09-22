# CHECKPOINT — pair-oxigraph

Rewritten after every meaningful sub-step. A stranger should be able to continue from this
file alone.

**Last updated:** RUN COMPLETE. **FINAL VERDICT: NO SURVIVOR.** `DONE` written at the run root.

---

## 0. Identity / paths

| thing | value |
|---|---|
| repo | `oxigraph/oxigraph` |
| shared clone (read-only, other pairs use it — DO NOT WRITE; `cp -r` fails on root-owned `target/*.lock`) | `/tmp/shortlist-data/clones/oxigraph` |
| **my scratch tree at base_commit** (made with `git archive HEAD \| tar -x`) | `/tmp/oxigraph-work` |
| persistent cargo cache volume | `/tmp/oxigraph-cargo` |
| base_commit | `450d2fe0ea8b9aa457ad41dbf542582d1d443150` |
| run dir | `/home/agvidit/swebench-playbook/.e2e/pair-oxigraph/` |
| task-scoped tmp dir | `/tmp/oxigraph-run/` |
| tasks repo (for B1+) | `/home/agvidit/swe-bench-pro-agvidit` (branch `main`, 39 PRE-EXISTING uncommitted files — never `git add -u` / `git add .`) |
| task dir | NOT CREATED — no survivor yet |
| docker lock held? | **NO** |
| target format | `swe_bench_multi_turn` |

## 1. THE EXECUTION HARNESS — working, reusable, needed again at B3 and B4

```bash
# one-time: clean tree at base_commit (plain cp -r FAILS on root-owned target/*.lock)
rm -rf /tmp/oxigraph-work && mkdir -p /tmp/oxigraph-work
cd /tmp/shortlist-data/clones/oxigraph && git archive HEAD | tar -x -C /tmp/oxigraph-work

# every run (cold 48.6 s, warm 0.9 s):
flock /tmp/swebench-docker.lock docker run --rm \
  -v /tmp/oxigraph-work:/work -v /tmp/oxigraph-cargo:/cargo -w /work rust:1-slim \
  sh -c 'cd /work && CARGO_HOME=/cargo cargo test -p spareval --test a3_repro -- --nocapture --test-threads=1'
```

`lib/oxigraph` works with `--no-default-features` (RocksDB optional) — it IS in the cheap path.
Integration tests under `lib/<crate>/tests/` need the crate's siblings added as
`[dev-dependencies]` (I added oxiri/oxstr/oxrdf/spargebra/sparesults to
`lib/spareval/Cargo.toml` in the scratch tree only).

## 2. Current act and position

**RUN COMPLETE — A2 x2, A3 x2, NO SURVIVOR. B1-B5 did not run and correctly could not.**
Nothing is in flight. No lock held. No task directory exists.

Exit state per act: A2 r1 DONE (2 cards) · A3 r1 NO SURVIVOR · A2 r2 DONE (0 cards) ·
A3 r2 NO SURVIVOR, FINAL · B1-B5 NOT ENTERED (B1's input is a survivor card; there is none).

Read `handoffs/03-A2r2-A3r2-FINAL.md` for the full kill ledger.

## 3. DONE, with evidence

| # | Thing | Evidence |
|---|---|---|
| A2 r1 | 18 surfaces, merge table, 2 cards | `handoffs/01-A2.md`, `/tmp/oxigraph-run/{surfaces.md,cards.out}` |
| A3 r1 | **NO SURVIVOR**, 9/14 ticked, 5 waived | `handoffs/02-A3.md` |
| GATE 2 harness | built and run twice | `/tmp/oxigraph-run/gate2-{spareval,both,update}.log` |

### The four kills (do not relitigate)
- **C02 / GATE 2** — hollow. MEASURED: `explain()` already returns the complete plan tree
  before any solution is consumed (plan JSON byte-identical before vs after); statistics
  on-vs-off already yields identical solution sequences.
- **C02 / GATE 0** — `PreparedQuery::plan` is COINED, no spelling-indifferent rewrite. No
  override written: the card's own predicted step-1 rate is 4-5/5 on every arm, so the override
  would buy difficulty the candidate does not have.
- **C01 / GATE 3** — merged public PR **#1938** = commit `4a611b81` (2026-09-12, ten days before
  base_commit), *"SPARQL UPDATE LOAD: make sure the operation is atomic even when SILENT is
  set"*, same file, same contract. Hard stop, no exception.
- **C01 / GATE 7** — cascade decorative. `QueryEvaluationError` (spareval) and
  `UpdateEvaluationError` (oxigraph) are separate enums in separate crates;
  `grep -rn "can_be_silent\|QueryEvaluationError" lib/oxigraph/src/sparql/update.rs` -> nothing.

## 4. Verified facts about the repo (feeds any future round — do not re-derive)

- Plan JSON keys, all IN-BASE: `"planning duration in seconds"`, `"plan"`, `"name"`,
  `"number of results"`, `"duration in seconds"`, `"children"`. Stats keys only under
  `compute_statistics()`.
- Plan node labels NAME THE ALGORITHM (`Join(HashBuildLeftProbeRight, keys = ?o)`,
  `AntiJoin(...)`, `Distinct(Hash)`, `ForLoopLeftJoin(...)`) — asserting on one is
  mechanism-naming and disqualifying. Only per-node `"number of results"` and tree position are
  safe.
- `without_optimizations()` observably changes the plan (`keys = ?o` -> `keys = `).
- `ADD`/`MOVE`/`COPY` are not operations; desugared at
  `lib/spargebra/src/algebra_builder.rs:1873-1913` per the W3C rewriting (cited in-code).
- **Real measured defect, UNUSABLE (PR #1938 covers the class):** `COPY <missing> TO <dst>` in
  STRICT mode returns Ok and destroys `<dst>`; `MOVE SILENT <missing> TO <dst>` likewise;
  retried `MOVE SILENT` wipes both graphs; `ADD` and strict `MOVE` do not.
- `can_be_silent` is `pub(crate)` (`lib/spareval/src/error.rs:54`).
- Built-in arity errors are PARSE errors, so `UnsupportedFunctionArity` is unreachable from a
  query string.
- `FailingDataset` (`lib/spareval/src/lib.rs:1043`) is an existing in-repo fault-injection
  `QueryableDataset`.
- **Churn is the binding constraint.** One expert maintainer, daily commits across every crate.
  The "silently swallows" direction alone: 2 closed issues + 4 merged commits in one month.

## 5. Decisions already made — do not relitigate

| decision | reason |
|---|---|
| P1 banned (at 3-instantiation ceiling); **P2 banned for this repo** | R6 self-collision — P2's shipped instantiation is `ruby-rdf/sparql`, same subsystem. |
| AXIS-19 primary, AXIS-10 secondary; P6 primary, P8 secondary; Layer B omitted | R7 is QUARANTINED; AXIS-10 is a pipeline-choice axis, which survives the Rust data-structure prior. |
| Ask was 18 surfaces, cards expected 2-4, **never backfill** | A2 §2 band + subsystem cross-check. |
| No GATE-0 override written for C02 | see §3. |
| Round 2 adds a **CHURN CHECK** as a first-class gate | it is what killed round 1 and no act-file measures it (friction F10). |
| GATE 4/5 probes not run in round 1 | A3 §0 economy — both candidates dead on cheaper gates. |

## 6. NEXT — nothing. If someone picks this repo up again, read this first.

1. **`AGENTS.md` is present at the clone root and `A1-repo-screen.md:25` (G2) makes its presence
   a HARD KILL.** The shortlist waived it in a parenthetical. Resolve that with a human before
   spending anything. Owner: human.
2. The failure was **premise freshness, not premise quality**: 5 merged commits in the 10 days
   before the pin, all inside the target crates; 23 in-flight non-dependabot maintainer
   branches (3 of them on carded surfaces); 72 open `enhancement` issues. Screening measured
   *other task authors* (0 peers, 0% AI authorship) and never measured *the upstream author*.
3. Do not re-cut any of: S01 (open issue #1624 + maintainer comment), S02 (hollow — DISTINCT
   already handled), S05/S06 (hollow — measured), S07/S17 (merged PR #1938), S08 (churn
   `bb2fb65b` + branch `origin/sparql-exist`), S14 (`Dataset::canonicalize` ships). Full ledger
   in `handoffs/03-A2r2-A3r2-FINAL.md`.
4. Do NOT rewind `base_commit` behind `4a611b81`/`bb2fb65b` to revive a premise — A3 GATE 3
   names that as a hard kill.
5. Genuine upstream bug found and unused, worth reporting to the project:
   `COPY <missing> TO <dst>` in STRICT mode returns Ok and DESTROYS `<dst>`; a retried
   `MOVE SILENT` wipes both graphs. Reproduced at base_commit; harness in §1.

## 7. Standing constraints

- **NEVER** write `instruction.md` / `steps/*/instruction.md`. Avocado via `mc.sh`, or Vidit.
- **NEVER** write anything under a task's `tests/` — Codex or 1P only; provenance scores by PATH
  (a Bash heredoc into that dir is the same violation). *(The A3 repro tests live in
  `/tmp/oxigraph-work`, not in a task dir — that is Claude's own diagnosis work and is allowed.)*
- Do not `git push` anywhere. Stop at a staged, verified commit; report `PUSH-READY`.
- Do not modify `~/swebench-playbook/` outside this run dir; do not touch another pair's run dir.
- Task-scoped `/tmp` paths only.
- Anything spawning Docker: `flock /tmp/swebench-docker.lock`.
- Write `DONE` at the run root when stopping for any reason.

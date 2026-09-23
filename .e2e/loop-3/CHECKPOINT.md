# CHECKPOINT — loop-3 (lane: build systems / compilers / linters / formatters / package managers / language runtimes)

Rewritten after every meaningful sub-step.

## Current position
- ACT: `A1` repo screen. Step 1-2 of the §10 checklist.
- Run dir: `/home/agvidit/swebench-playbook/.e2e/loop-3/`
- Clones go to: `/home/agvidit/swebench-playbook/.e2e/loop-3/clones/<name>`
- Task-scoped /tmp prefix: `/tmp/loop3-*`
- Docker lock: NOT held.

## Done
- Read PAIR-COMMON.md, LOOP-BRIEF.md, 00-ROUTER.md, A1-repo-screen.md, and the prior-lane
  CLAIM at `/home/agvidit/swebench/runs/shortlist-tooling.md`.
- `cd /tmp/llc && git pull` -> "Already up to date", HEAD `d8472c4c5` dated **2026-09-02**
  (20 days stale). Logged in friction.md.
- Host toolchain: gh, go, java, mvn, javac, docker, python3 PRESENT. **ruby and cargo ABSENT**
  (matches A1 §8 wave-2 inventory). 223G RAM, 166 cores.

## Retired by the brief — do NOT re-source
- `ruby/prism` (R05: Ripper / RubyVM::AbstractSyntaxTree importable repo-wide)
- `go-acme/lego` (worked by a pair tonight)
- `golangci/golangci-lint` — GPL-3.0, A1 §7 licence CONFLICT -> `Owner: human`

## Lane warning (from dispatch, measured)
- peer `saravana` = 170 tasks concentrated in Java dev-tooling (checkstyle 41, picocli 9,
  gradle 6, sootup 5, spotbugs 4, ant 4, maven 3, javaparser 3, jshell 3).
- taxonomy: `compilers_and_languages` +4.69 saturated, `devops_and_tooling` +4.88 saturated.
  Language gap is the only lever: Ruby -5.81, Java -2.95, Rust -2.11, Go -1.95.
- Target surface shape: **semantic_bugs** (7 passed / 7) not `expose_interface` (1 / 13).

## Next concrete commands
1. Read peer repo pools (`codimango/swe-bench-pro-jayzong:docs/repo-candidates/*`,
   `codimango/swe-bench-pro-aaitemp:discovery-f/*.json`).
2. G1 live peer sweeps on the screening set.
</content>

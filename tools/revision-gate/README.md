# revision-gate

One command before ANY push of a SWE-bench task, first push or revision:

```bash
cd ~/swe-bench-pro-agvidit
python3 ~/swebench/revision-gate/gate.py <task>          # full run, issues the push stamp
python3 ~/swebench/revision-gate/gate.py <task> --fast   # stages 1-5 while iterating
```

**PROVISIONAL (2026-10-13).** Not yet verified by 3 independent agents. See
`ledger/VERIFY-revision-gate.md`. Until then a FAIL means "look at this", not proof.

| # | Stage | Catches (reviewer finding it stops) |
|---|---|---|
| 1 | preflight | structure, server-only checks, oracle 3/3 |
| 2 | presubmit | README sections and counts, metadata, config (mechanical third of all bounces) |
| 3 | provenance | logged Claude writes still in the files |
| 4 | carry | later steps not re-running earlier steps' graded tests |
| 5 | forge | grader pays reward 1 with no solution (planted conftest/pytest.ini/plugins, runner wrappers) |
| 6 | review | the reviewer's own agent (`review-task-swebench-v2`); fix every finding (R-026) |
| 7 | calibrate | `bench run --k2n` twice; every step 1-3/5 in both runs (one non-final 5/5 allowed when the task has 3+ steps, as on the server); waits for the one-per-host bench slot |

- Writes nothing inside the task directory. Logs go to `/tmp/revision-gate/`, stamps to `~/swebench/gate-stamps/`.
- `push-task.sh` refuses to push without a clean full-run stamp for the exact task files.
- A git **pre-push hook** enforces the same on every push path (custom scripts, plain `git push`).
  `install-hook.sh` also installs the gate itself at `~/swebench/revision-gate/` (what the hook and
  push-task.sh run), so re-run it after every gate update. Install in every task-repo clone on a host:
  `~/swebench-playbook/tools/revision-gate/install-hook.sh` (`--list` to check, `--uninstall` to remove).
  Changes only under `<task>/audit/` need no new run. Never use `git push --no-verify`.
- Stages 1 and 5 (short) run under `/tmp/swebench-docker.lock` and print who holds it before waiting; stage 7 does not hold it (hours long) and instead waits up to 6 h for the one-per-host bench slot.
- A forge only counts if a marker shows its code actually ran during grading.
- Validated so far: carry-forward, Python and Go forges, the reviewer-agent stage, the k2n parser.
  Not yet run end to end: stage 7 (two live k2n runs) and the Ruby/JS/Rust/Java/PHP forges.
- Forge coverage: Python, Go, Ruby, Rust, Java (Surefire), PHP (conf.d prepend + phpunit.xml). JS/TS is weak:
  graders that run `node` directly with their own NODE_OPTIONS never load it. A step where no forge can be
  planted is UNCOVERED: the gate FAILs it unless you check the grader by hand and pass
  `--accept-uncovered "<what you checked>"` (recorded in the stamp).
- `gate.py --version` prints the build id; it is also printed in every run and written into every stamp.

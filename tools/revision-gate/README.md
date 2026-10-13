# revision-gate

One command before ANY push of a SWE-bench task, first push or revision:

```bash
cd ~/swe-bench-pro-agvidit
python3 ~/swebench-playbook/tools/revision-gate/gate.py <task>          # full run, issues the push stamp
python3 ~/swebench-playbook/tools/revision-gate/gate.py <task> --fast   # stages 1-5 while iterating
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
| 7 | calibrate | `bench run --k2n` twice; every step 1-3/5 in both runs |

- Writes nothing inside the task directory. Logs go to `/tmp/revision-gate/`, stamps to `~/swebench/gate-stamps/`.
- `push-task.sh` refuses to push without a clean full-run stamp for the exact task files.
- A git **pre-push hook** enforces the same on every push path (custom scripts, plain `git push`).
  Install it in every task-repo clone on a host, and again after making a new clone:
  `~/swebench-playbook/tools/revision-gate/install-hook.sh` (`--list` to check, `--uninstall` to remove).
  Changes only under `<task>/audit/` need no new run. Never use `git push --no-verify`.
- Stage 7 refuses to start while another `bench run` owns the host (one per host).
- Validated so far: carry-forward, Python and Go forges, the reviewer-agent stage, the k2n parser.
  Not yet run end to end: stage 7 (two live k2n runs) and the Ruby/JS/Rust/Java/PHP forges.
- Forge coverage: Python, Go, Ruby, JS/TS, Rust, Java (Surefire), PHP (PHPUnit). Other languages get
  the controls only and a coverage WARN.

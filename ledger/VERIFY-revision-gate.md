# VERIFY: revision-gate (PROVISIONAL until 3 agents confirm)

Vidit, 2026-10-13: the revision gate (`tools/revision-gate/`) and its precheck wiring were built by
**agvidit-ee** (devvm23237). Until **3 different agents** have checked it independently and posted
CONFIRMED below, treat its results with a grain of salt: a FAIL means "look at this", not proof.

## Who may verify
- Not agvidit-ee (the author), and not the same session twice.
- The three must be different agents. At least one should be non-Claude (Codex or Muse).
- Work read-only on task files. Never write inside a task directory.

## What each verifier checks (all of it, independently)
1. **Read the code**: `tools/revision-gate/gate.py`, `carry_forward.py`, `forge_probe.py`,
   `forge_payloads/plant.sh`, and the `== 0.` block in `assets/skills/swebench-mt/push-task.sh`.
   Look for checks that can pass when they should fail, and anything that writes into a task dir.
2. **Carry-forward**: run `carry_forward.py` on a task a reviewer flagged for "later steps do not
   re-test earlier steps" (wtforms-fieldlist-row-identity-writeback-redisplay, vobject-series-edit-split-move)
   and on one that carries its tests (jedi-behaviour-preserving-refactorings). Expect FAIL, FAIL, PASS.
3. **Forge probe**: run `forge_probe.py <task> --steps 1` on django-model-utils-fieldtracker-db-truth
   (reviewer forged it; expect FAIL on py_ini_plugin) and on a hardened accepted task such as
   django-model-utils-choices-grouped-selection-materialization (expect no FAIL), and on
   reversion-selective-undo-revisions --steps 1 (reviewer showed an interpreter swap; expect FAIL on
   py_interpreter_swap only). Use a clean worktree of origin/main, not the shared checkout.

Author's own validation (2026-10-13, agvidit-ee; logs in /tmp/gate-dev on devvm23237) matched every
expectation above, plus: Go forge blocked on spire-bundle (controls OK), reviewer agent gave Revise on
wtforms (human reviewer also said revise), k2n parser read 69's dropshot run as 5/5 then 3/5.
**Not yet run end to end: stage 7 (calibrate, two k2n runs) and Ruby/JS/Rust/Java/PHP forges.**
Please exercise at least one of those.
4. **Gate end to end**: `gate.py <task> --fast` on one task; confirm the verdict, the logs and the stamp
   in `~/swebench/gate-stamps/` make sense, and that `--check-stamp` flips after any task-file edit.
5. **Wiring**: `push-task.sh` and the pre-push hook (`tools/revision-gate/pre-push`, installed by
   `install-hook.sh`) refuse without a stamp, accept with one, re-block after an edit, allow audit-only
   changes, and log `GATE_OVERRIDE`. Test in a throwaway clone pushing to a local bare repo, never the real remote.
6. Anything the gate claims to catch that it does not, or blocks that it should not.

## Post your result (one block each; edit this file, commit, push)

### Verifier 1
- agent / session / machine:
- date:
- ran:
- findings:
- verdict: CONFIRMED / ISSUES (list)

### Verifier 2
- agent / session / machine:
- date:
- ran:
- findings:
- verdict: CONFIRMED / ISSUES (list)

### Verifier 3
- agent / session / machine:
- date:
- ran:
- findings:
- verdict: CONFIRMED / ISSUES (list)

## When all three say CONFIRMED (and every ISSUE is fixed and re-checked)
Whoever posts the third CONFIRMED does this in one commit:
1. Delete this file.
2. Remove the PROVISIONAL lines from `tools/revision-gate/gate.py` (docstring, banner print, and
   `"provisional": True` in the stamp), from `tools/revision-gate/README.md`, and drop the `GATE_OVERRIDE`
   branch from `tools/revision-gate/pre-push`; then re-run `install-hook.sh` on every host.
3. In `assets/skills/swebench-mt/push-task.sh`, drop the `GATE_OVERRIDE` branch and its comment, so a
   missing stamp always blocks. Do the same in RUNBOOK.md hard stop 2 and B5/C7, then run
   `tools/sync-skill.sh install` and tell agvidit-b0 (skill owner).
4. Move the ledger CLAIMS row for revision-gate to RELEASED with the commit hash.

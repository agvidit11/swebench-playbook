# TASK-LOG — one file per task, shared by every machine and lane

Why (Vidit 2026-10-15): two workers pushed to the same task within hours (lektor 44a5bec over
ec0d1b9) and undid each other's calibration. CLAIMS.md says WHO holds a task; TASK-LOG says WHAT
has been done and WHY, so a new owner never starts from zero.

## Protocol (every lane, every machine)

1. **Before touching a task** (any push, statement edit, test edit, rerun): `git pull` the playbook,
   read `ledger/TASK-LOG/<task>.md` top to bottom, and check the CLAIMS.md row. If another lane holds
   it ACTIVE, do not push — append a `REQUEST` entry and wait, or ask Vidit.
2. **Owner line at the top is authoritative.** Only the current owner pushes to the task repo.
3. **Every push / server result / review / decision gets one appended entry** (newest last):
   `- YYYY-MM-DD HH:MM UTC · <machine>/<lane> · <commit or action> · <one-line what + why> · <result>`
4. **Handoff:** the giving owner writes a `HANDOFF` entry (current state, open review items, what was
   tried and failed, next step) and changes the owner line; the receiver writes `ACCEPTED` before work.
5. **Statement changes need a reason entry** citing the measurement or reviewer item that forced them.
   A statement change made only to satisfy a local checklist must first check it does not narrow scope
   to exactly what is graded (that made lektor step 2 saturate, 3/5 -> 4/5).
6. Push the playbook right after writing (`git pull --rebase && git push`).

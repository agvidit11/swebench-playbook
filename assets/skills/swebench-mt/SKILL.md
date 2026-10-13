---
name: swebench-mt
description: "Vidit's personal playbook for SWE-bench multi-turn (swebench-multi) tasks — signal integrity, sourcing a repo and idea, authoring tests and instruction.md, and moving a task into the calibration band, plus a RUNBOOK that drives them. Use for 'swebench multi-turn', 'calibration gate', 'step gate failed', 'too easy', 'too hard', 'my task failed validation', 'new MT task', or when picking a repo for a new MT task."
restrict-3p-model: true
---

# SWE-bench Multi-Turn — personal playbook

Built from a 12-task batch run in Sept 2026. Every claim here is backed by a
measured result, not a guess. Where something is inferred, it says so.

This is the **delta** from the team skills. `swebench-flow` covers end-to-end
creation and `aai-difficulty-tuner-orchestrator` covers difficulty tuning — this
covers what neither of them knows.

---

# ROUTE BY WHAT THE SERVER SAID

Get the verdict first: `codimango task errors <task>`

| Server says | What it means | Go to |
|---|---|---|
| `Oracle validation: N/3 passed (all must pass)` | **Everything else is skipped.** Fix this first — nothing else is measurable. Often a race that only appears under load. | `references/signal-integrity.md` → oracle flakiness |
| `Step gate failed — "<step>" too hard — no model passed it (avocado 0, opus 0, gpt 0)` | Note ALL THREE are 0. Avocado 0 alone is fine. Usually a FALSE NEGATIVE, not difficulty — prove it before narrowing scope. | `runbooks/3-harness.md` → **prove false negative first** (relax ladder) |
| `Step gate failed — "<step>" too easy — avocado passed 4 of 5, over the 3/5 ceiling` | In-band is **1–3 of 5**. Needs a structural fork, not more edge cases. | `runbooks/3-harness.md` → too-easy ladder |
| `Step gate failed — "<step>" too easy — 1.0 on every model` | Same, more severe. | `runbooks/3-harness.md` → too-easy ladder |
| `"<step>" has no gradient — avocado never reached it and every model that did passed every attempt` | Not reached ≠ failed. Read the **Steps** view, check seeds. | `runbooks/3-harness.md` → "Current server rules" (no gradient) + "First classify the signal"; `references/signal-integrity.md` |
| `has a 1.0 pass-rate and the single-1.0 exemption needs 3+ declared steps` | Add a step, OR harden. Exemption is **one per task**, never the last step. | `runbooks/3-harness.md` → "Current server rules" (exemption) + too-easy ladder rung 5 |
| `the single-1.0 exemption is already spent on an earlier step` | A second step hit 1.0. Adding steps won't help again. | `runbooks/3-harness.md` → too-easy ladder (tighten) |
| `Benchmark canary string found` | Scaffold ships a canary on line 1 of `environment/Dockerfile`. Strip it. | `runbooks/2-build.md` → hard failure checklist → Contamination |
| `task.toml is missing required [task].track_assignment` | **Derivable from `format`** — do not ask. | `runbooks/2-build.md` → hard failure checklist → `task.toml` |
| `Passed under the pre-9/15 rules (current rules: ... too easy ...)` | Grandfathered and fragile. Counts today; do not build on it. | `runbooks/3-harness.md` → "Current server rules" |
| `Passed — every step has a pass and a fail on the same model, and avocado is never at 1.0` | Done. | `runbooks/3-harness.md` → stage 7, submit (after RUNBOOK.md hard stop 4) |
| `BAD_GRADING_WRONG` | Graded is a superset of stated. | `runbooks/2-build.md` → BAD_GRADING_WRONG vs WEAK; **remove** an assertion |
| `BAD_GRADING_WEAK` | Stated is a superset of graded. | `runbooks/2-build.md` → BAD_GRADING_WRONG vs WEAK; **add** a test |
| `Unauthorized third-party model authorship` | Provenance L3. | `RUNBOOK.md` → "Who writes what" / provenance; `runbooks/2-build.md` → Provenance checklist; Codex re-author |
| Nothing — `(no jobs on Nest)` | Validation job was never created. `codimango task rerun <task>` | — |

**Starting fresh instead?** → `RUNBOOK.md`.

---

# THE SIX NON-NEGOTIABLES

**1. Never trust a number without checking it is real.**
~30% of trials once died to a binary-pull race and scored as legitimate
`reward 0.0`. `n_errored_trials` undercounts. Read `references/signal-integrity.md`
before acting on any calibration result.

**2. Local Avocado is NOT predictive of server Avocado.**
Same commit: `3/5` locally, `1.0` on the server. Correlation measured at 0.07
over 120 paired samples. Use it as a **one-sided kill gate only** — local 0/5 or
5/5 means fix before pushing; anything between tells you nothing.

**3. Probe before grading.**
Before grading a property, write an alternative-but-valid implementation and run
it against the tests. If it passes, the property is not a discriminator and
grading it changes nothing. This is **differential testing** (PatchDiff), not
mutation testing — mutation testing measures the opposite direction.

**4. The grading test is a two-way contract.**
Every requirement in the instruction MUST be graded, **and nothing may be graded
that is not in the instruction.** Half two is our most common defect — webauthn
pinned an unstated error class, jsonschema an unstated internal representation.
SWE-bench Pro Verified's own re-audit: 75 of 119 flagged tasks were
"overly-narrow test".

**5. Authorship is contractual.**
`instruction.md` — Muse ONLY, via `mc2.sh` (Vidit, 2026-10-02); never Claude,
Codex, MetaCode, or an indirect generator. Muse must originate it from the
**repo**, not from another model's proposed wording. **Every other file in a task
dir** — all of `tests/`, plus `solve.sh`, Dockerfile, `task.toml`, README,
`audit/` — **Codex** (Muse if clearly better). **Claude writes nothing inside a
task directory** (Vidit, 2026-09-30, reaffirmed 2026-10-02): it briefs, verifies
and measures, with its own scripts in `/tmp`. The full table, and how to clear
legacy provenance, are in RUNBOOK.md → "Who writes what".

**6. One agent per task.**
Two agents on one task overwrote each other's `instruction.md` three times and
broke an oracle. If another process is editing your files, stop and report.

---

# THE DRIVER, THREE RUNBOOKS, ONE REFERENCE

| File | Use it when |
|---|---|
| `RUNBOOK.md` | **Start here.** The driver: which phase runbook, in what order, who owns what, the four hard stops. |
| `runbooks/1-brainstorm.md` | Stages 0→1d. Pick a repo, find candidates, MEASURE outcome variance before scoring. |
| `runbooks/2-build.md` | Stages 2→4. Instruction, tests, plumbing, preflight. Provenance rules. |
| `runbooks/3-harness.md` | Stages 5→7 + salvage. Read the verdict, both ladders, false-negative first. |
| `references/signal-integrity.md` | **Read before believing any number.** Dead trials, variance, races, host limits. |

**`RUNBOOK.md`** drives them: the order to apply them in, the MetaCode/Codex
delegation prompts, and the four hard stops. It holds no rules of its own.

**Three idea libraries feed RUNBOOK stage 0**, which composes one choice from
each into a candidate:

| File | Layer | Question |
|---|---|---|
| `~/swebench/SEARCH-AXES.md` | C — search axis (18) | how do I look at this repo? |
| `~/swebench/FORK-PATTERNS.md` | A — fork shape (P1-P6) | what shape of divergence? |
| `~/swebench/ALGO-CATALOGUE.md` | B — technique (46) | what makes it hard? |

(missing ~/swebench? run ~/swebench-playbook/tools/bootstrap-swebench-home.sh)

`FORK-PATTERNS.md` is the index to all three and carries the selection rules.
**Observability, not difficulty, is the binding constraint** — it eliminated
half the algorithm catalogue, including every DP optimisation and classic string
structure, because "faster but behaviourally identical" cannot be graded.

---

# THE ONE IDEA THAT MATTERS MOST

**Edge cases do not create difficulty. Structural forks do.**

open62541 more than doubled its graded surface — unused-bits sweeps, 200 KB
payloads, malformed input, injected allocation failures — and stayed at **5/5**.
franz-go had **5 of 7** alternative implementations pass its shipped tests.

What moved every task into band was a single property where two *reasonable*
designs diverge observably:

| Task | The fork |
|---|---|
| sparql | counters update live during iteration vs after materialisation |
| net-imap | beginning-of-line state relative to a masked write |
| open62541 | each residual lent to a callback and released before the next |
| franz-go | the decision HOLDS the binding rather than windowing into the table |

Edge-proofing is still necessary — it stops a wrong solution passing and a right
solution failing. It is just a **different job** from creating difficulty. Doing
the first and expecting the second is the most expensive mistake available.

---

# QUICK COMMANDS

```bash
# verdict
codimango task errors <task>
codimango task rerun <task>          # if "(no jobs on Nest)"

# the one local gate that matters — runs all of the below plus the 3 server-only checks
~/.claude/skills/swebench-mt/preflight.sh <task-dir> --with-oracle   # exit 0 = safe to push

codimango bench run -p <task> -a oracle -k 3         # MUST be 3/3 or calibration is SKIPPED
codimango bench validate -p <task> --structural-only # Overall: PASS
#   plain `bench validate` HANGS on the AI stage (needs `codimango api setup`)

# extract what the models actually WROTE (needs artifacts= in task.toml)
codimango trial artifacts <tid> --json | jq '.files[] | select(.name|contains("<impl>")) | {name,key}'
codimango trial artifacts <tid> --key "<s3-key>" > /tmp/impl_<tid>.ext   # --key: 1-2s; --download: 40s

# dedup — the local corpus, NOT gh search
grep -rl -i "<repo>" /tmp/llc | grep -v '\.json$'
#   then grep distinctive API symbols, not just the repo name

# delegation
~/.claude/skills/swebench-mt/mc2.sh /tmp/p.txt <repo> /tmp/p.out   # Muse; `metacode run` is retired and no-ops
codex exec -s workspace-write --skip-git-repo-check -C <dir> "<brief>" < /dev/null   # < /dev/null matters

# push
git fetch ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git main
git add -u -- <task-dir>/
git diff --cached --name-only        # ALWAYS verify; other agents stage into the shared index
git push ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git HEAD:main
```

CLI renamed 2026-09-15: `api tasks` → `task`, `api jobs` → `job`,
`api models` → `model`. `bench` unchanged.

---

# CURRENT BATCH

Live state of the 12 tasks in `~/swe-bench-pro-agvidit`:
`~/swebench/START-HERE.md` — priority order, per-task blockers,
and the two blockers that affect everything. (missing ~/swebench? run ~/swebench-playbook/tools/bootstrap-swebench-home.sh)

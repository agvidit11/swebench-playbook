# 00-LANES — running the pipeline as lanes, on any number of machines

`STATUS: LIVE`, 2026-10-02. This is the operating manual. The act-files (`A*`, `B*`, `C*`) are the
reference it points into. An agent running a lane reads THIS file and the act-file for its current
stage — not all 36 files.

## 0. Target and funnel — per machine, per day

| stage | target | what counts |
|---|---:|---|
| ideas (cards) | **8** | a card with a problem statement, a named trap, a seam, an A4 corpus verdict |
| probed in band | **6** | the card's Avocado probe landed 1–3 of 5 on a stated contract |
| READY | **3** | every local check in §8 passes; waiting only on Vidit's push decision |

Three machines → ~9 READY a day. **Nothing is pushed without Vidit's confirmation.**

**Vidit ruling 2026-10-02: multi-turn is the requirement — at least 4–6 multi-turn READY tasks per day.**
Single-turn is a deprioritised fallback, never the default rescue. A card whose steps do not land is
**re-divided** (split the hard step, add a third step, move cases between steps — §3 "Shape"), not
discarded or downgraded. DOWNGRADE is legal only after a measured 3-step reshape has failed.

**Why we were producing ~0, measured over the week before this file existed:** ideas were generated from
scratch one repo at a time; most were algorithms, which Avocado implements as soon as they are stated
(6 of 6 cards in one run); the discriminating check ran *after* hours of building; 2–3 serial agents;
and infra failures ate whole runs. Each lane below exists to remove one of those.

## 1. Roles — the same on every lane

| who | does | never does |
|---|---|---|
| **Claude** | the **consistent reviewer and orchestrator**: owns the rating sheet, decides AMEND/KILL/DOWNGRADE/MEASURE, writes briefs, dispatches, reads every result, updates ledgers | writes **any** file inside a task directory (preflight blocks on it) |
| **Codex** | **builds everything** except contracts: scaffold, graded tests, oracle, environment, task.toml, parser, test.sh, cold implementations, probe tests, fixes | writes or edits any `instruction.md` |
| **Avocado / Muse** (`~/.claude/skills/swebench-mt/mc2.sh`) | **writes every `instruction.md`** (full delete-and-re-author, never a patch); the calibration model for probes and local runs; builds integrity graders when Codex's cyber filter blocks | — |

Claude rates every card and every build against **one sheet fixed before the first card is seen**
(`.e2e/pair-b/RATING-SHEET.md` is the template: premise, seam novelty, branches, statability, cascade,
grading integrity, calibration). Same sheet all day, so scores are comparable across lanes and machines.

## 2. How a contract is written — the rule that changes ideation

**The contract is a user describing a problem and the outcome they want. It never prescribes the
method.** The solver decides the algorithm, the data structures, how the code is split, and how well it
is built. That judgement *is* the task.

| allowed in a contract | not allowed |
|---|---|
| the symptom, the situation, who is hurt by it | the algorithm or approach |
| the observable outcome required, including exact values where they matter | helper names, internal structure, file splits |
| the entry point the user will call — its name and signature (coining one is fine) | step-by-step procedure, ordering of internal work |
| a genuine constraint: "this region stays unchanged", "no new dependency", "existing callers keep working" | anything justified only by "a previous solver got it wrong" |
| which existing component is the authority for a rule | |

Why: every card whose contract stated an algorithm saturated (Avocado implements stated algorithms). The
splits we have measured came from **judgement the contract leaves to the solver** — see §3.

Mechanics: Claude or Codex writes **obligations** ("A reader must come away knowing that …") to `/tmp`,
never into a task dir. `tools/avocado-brief.sh` lints them and builds the prompt. `~/.claude/skills/swebench-mt/mc2.sh` sends it.
Avocado deletes any old contract unread and writes the new one. **Diff the whole task afterwards** —
Avocado does not reliably respect scope.

## 3. Where ideas come from — two sources, every card names its trap

### Source A — port an accepted shape (this produced 38 of the reference portfolio's 40 accepts)

Accepted tasks are a catalogue of shapes that clear review. Read one, extract the **pattern** (never the
behaviour, names, tests or text), and find a repo that lacks the same thing.

- ours: `kustomize-localize-source-fidelity`, `django-model-utils-fieldtracker-related-snapshot`,
  `open62541-numericrange-canonical-form-composition`, `jsonschema-schema-subsumption-checker` (grandfathered —
  shape only), `ruby-auth0-oidc-at-hash-c-hash`
- reference portfolio: 40 accepted tasks at `~/swebench-reference/beka/` (`task-manifest.tsv` lists them)
- peer status is readable: `codimango task show <name> --json` works on other authors' tasks

### Source B — design around a trap that has actually split real solvers

| trap class | what it looks like | measured on |
|---|---|---|
| **a stated constraint that fights the natural edit site** | the obvious place to make the change is inside something the contract says must stay unchanged | open62541 step 1: 4 of 5 solvers broke "the parser stays byte-for-byte" |
| **a natural order that loses information** | doing the obvious first step (normalise, reduce, dedupe) throws away exactly what a stated rule needs | gobgp step 2: both failing Avocado trials reduced first, dropped an empty entry, missed a family mismatch — 3/5 |
| **a convenient helper that is subtly too permissive or too strict** | the repo already has a helper that *almost* answers the question | gobgp step 3: all passing trials used permissive extended-community helpers for route targets |
| **equivalence over a large domain** | many spellings or forms must be treated as one (numeric spelling, conditional precedence, aliases) | go-zero: numeric default spelling and conditional precedence split solvers |
| **failure-path quality** | correct behaviour under allocation failure, cancellation, partial writes | open62541 step 2 (needs Muse for the grader — Codex's filter blocks it) |

**Every card names its trap class.** A card that cannot name one is an algorithm card and will most
likely saturate — probe it last, if at all.

### Shape of a multi-turn card

2 or 3 steps. **The last step must split solvers.** With 3 declared steps the server lets one non-final
step sit at 1.0 (kustomize, accepted, used exactly this). Step 2+ must be a different kind of operation
over what step 1 built — not the same property at a second site, not a report over step 1.

**Reshape moves (2026-10-02, measured on 6 cards that day):** a saturated step becomes step 1 of a 3-step
task (the exempt slot); a 0/5 cliff step is split along its failure fault line; a saturated LAST step is
replaced by a new different-kind operation — never left last. Non-last steps at 0.8 have passed on the
server (kustomize, net-imap). **Probe chained, like the server:** step N impls start from a *passing*
step N−1 tree, not from base. A single-turn merge of a 2-step card can destroy the band (config-rs:
2-step step 2 = 1/5; merged single-turn = 0/5 ×3, bimodal). Working brief:
`~/scratch/lane-i/MT-RESHAPE-BRIEF.md` on devvm6971.

## 4. Repo budget

- **Up to 4 tasks per repo**, each at a different seam (A4 `COLLIDES` is same-seam only). Half the
  reference portfolio's accepts are a second-or-later task on a repo already used. A repo is not spent
  after one task.
- **Prefer repos that already produced an accepted or passing task** — the environment, licence and
  determinism questions are already answered. Screening new repos is the expensive part; do it in the
  Idea lane only when the reuse list is dry.
- **Stop a repo** after 2 consecutive cards from it die at probe for the same reason.
- Minimum for a new repo: permissive licence, commit within 6 months, deterministic offline test suite,
  no peer task at the seam (A4), AI-authorship check (A1).

## 5. The lanes

Run each lane as **its own Claude session** (one task or card per agent context — never batch). Long
commands run **detached** (`setsid nohup … &`) and are polled; never as a foreground or background Bash
job that can hit a time limit.

### Lane I — Ideas (target 8 cards/day/machine)

1. Pull the playbook; read `ledger/CLAIMS.md`.
2. Pick a repo by §4. Run `A4` (whole-org corpus search at the seam) — record CLEAR/ADJACENT/COLLIDES.
3. Produce cards from §3. Each card: repo, base commit, seam, **problem statement in user voice**, trap
   class, 2–3 step shape (or single-turn), behaviour reproduced at base (Codex executes; a card whose
   behaviour already works at base is dead).
4. Typed verdicts (`A3` §0): only facts KILL. Quality problems AMEND. No second step DOWNGRADE to
   single-turn. Calibration questions go to the probe — MEASURE.
5. Claim each surviving card in `CLAIMS.md` as `CARD`, push. Hand to Lane P.

### Lane P — Probe (20–40 minutes per card; the gate that saves the hours)

1. Codex writes a scratch checkout at base (step N: base + earlier steps' sketch) under `~/scratch/`.
2. Claude writes the card's obligations to `/tmp`; `avocado-brief.sh` + `~/.claude/skills/swebench-mt/mc2.sh` → Avocado writes a
   **draft contract into /tmp** (not a task dir).
3. **Five cold implementations by Avocado** via `muse exec`, each in its own scratch dir, from the draft
   contract alone. (Avocado is the gated model; Codex cold implementations ran stronger on one task and
   weaker on another, so Avocado is the honest probe.)
4. Codex writes a quick probe test from the draft contract and grades the five.
5. Read **every failure**: a genuine miss on a stated rule, or an unstated rule (fix the obligations), or
   infra (exclude and replace).
6. Verdict: **1–3 of 5 → build** (claim `ACTIVE`). 0/5 → check for unstated rules first. 4–5/5 → one
   AMEND round targeting a trap class, then drop. Log to `ledger/PROBES.md`.

### Lane B — Build (one task per agent, to READY)

Order matters; each stage's act-file is the reference.

1. `B1` scaffold — Codex (`codimango task init … --type swebench-multi`), patch the scaffold landmines (`R3`).
2. `B2` contracts — obligations → Avocado writes each step's `instruction.md` (§2).
3. `B3` graded tests — Codex; every assertion traces to a contract sentence; collision-resistant hidden
   identifiers; several assertions on one behaviour are one branch.
4. `B4` oracle + environment — Codex; oracle 3/3.
5. **Grader integrity** — `test.sh` idempotent across two runs in one container; git attributes/filters
   sanitised (refuse to grade if present); solver-authored `*_test.go` swept before hidden tests apply; a
   parser that cannot be forged by printed output (Go: `go test -json` or a TestMain nonce). Negative
   control: an untouched tree scores 0, and a forging tree scores 0 (Muse builds the forge if Codex's filter
   blocks it).
6. `preflight.sh <task> --with-oracle` exit 0, **including TIER 4b replay**. Single-turn tasks: run the
   same-container replay by hand — preflight only replays `steps/` tasks.
7. Cold pass — 5 Codex implementations per step from the contract alone (step N on its own step N−1).
8. **Local Avocado k=5** (`codimango bench run -p <task> -a metacode -k 5`) and **every failing trajectory
   classified** from `<trial>/agent/.local/share/opencode/log/*.log`.
9. `B6` reviewers (`tools/review-gate.sh`), verdicts bound to the bundle hash, run on a `/tmp` copy.
10. Mark `READY` in `CLAIMS.md` with the evidence path. **Stop. Vidit pushes.**

### Lane W — Watch (every 2 hours, report only)

A Claude session on each machine running:

```
/loop 2h Run ~/swebench-playbook/tools/watch.sh. Then: for every STALE claim, every task whose server
verdict changed, and every infra signature, report one line with what it means and who should act. Append
any NEW infra signature to ~/swebench-playbook/ledger/ISSUES.md. Do not fix, build, push or edit any task
directory — report only. If a detached job has died, say so and name the lane that owns it.
```

It is deliberately passive. Its job is that nothing silently stalls for a day.

## 6. Infra failures — what to do, so a lane never stops

| signature | cause | do this |
|---|---|---|
| `mc.sh` exit 0, ~250-byte banner, no work | MetaCode retired | use `~/.claude/skills/swebench-mt/mc2.sh` |
| `flagged for possible cybersecurity risk` (Codex) | provider filter on exploit-shaped content (forge controls, malloc interposers) | route that one artefact to Muse via `~/.claude/skills/swebench-mt/mc2.sh`; keep Codex on the rest; word briefs neutrally |
| background job killed at time limit | harness limit | relaunch detached with `setsid nohup`; poll |
| `agent/metacode.txt` tiny, `[[: not found`, no tool calls | capture truncation, agent still working | read `<trial>/agent/.local/share/opencode/log/*.log` |
| `MetaModelCatalogError` on every trial | `network_mode` blocks the model catalogue | match sibling tasks' `[agent]` network setting |
| `AgentInstallError` | Harbor pull race | exclude the trial, replace it; flock patch (memory: harbor pull race) |
| `AgentTimeoutError` on every trial | step too large for the limit | not difficulty — raise the step timeout (+50%, ≥300s, ≤3600s) and rerun the same contract |
| team-aai guard blocks a Bash command | heredoc mentions `instruction.md`, or a `docker cp` from `tests/` | write briefs with the Write tool; have Codex run the docker step |
| `authorship-audit.sh` BLOCKED on a task you never touched | audit false positive | check the paths it lists; `/tmp` and `~/scratch` paths are not writes. Report in ISSUES |
| `codimango … --json` won't parse | banner of varying length | `sed -n '/^[[:space:]]*[{[]/,$p'`, never `tail -n +2` |
| verifier passes locally, reward 0 on server | verifier not idempotent | preflight TIER 4b; fix cleanup to reverse the test patch after the reward |

Every failure that costs time goes in `ledger/ISSUES.md` immediately. Twice → it gets a row here.

## 7. Three machines — coordination

- The playbook remote is **private** (`agvidit11/swebench-playbook`). Never make it public: it quotes task
  content.
- **Pull before claiming; push right after.** `ledger/CLAIMS.md` is the lock. One row per card or task.
- Each machine names itself in the `machine` column (`hostname -s`).
- The task repo (`codimango/swe-bench-pro-agvidit`) is shared too; `push-task.sh` handles the index — but
  **only Vidit-confirmed tasks are pushed**.
- Split the work: give each machine different repos from §4 so Lane I on two machines never mines the same
  seam. Write the split in `CLAIMS.md` as `CARD` rows before starting.

## 8. READY means all of this, evidence attached

- [ ] oracle 3/3 (`codimango bench run -p <task> -a oracle -k 3`)
- [ ] `preflight.sh --with-oracle` exit 0, TIER 4b replay passing (or the manual replay for single-turn)
- [ ] negative controls: untouched tree 0, forging tree 0
- [ ] cascade applies with plain `git apply`
- [ ] every graded assertion traces to a contract sentence (reverse trace)
- [ ] cold pass per step reported
- [ ] local Avocado k=5 with **every** failing trajectory classified; last step 1–3/5; at most one
      non-final step at 1.0 and only with 3+ steps
- [ ] `B6` reviewers bound to the current bundle hash, no Critical/High open
- [ ] `authorship-audit.sh` clean since the task's first commit
- [ ] `CLAIMS.md` row set to READY with the evidence path

## 9. Setting up a new machine

1. `gh auth login`; clone the playbook (`git clone git@github.com:agvidit11/swebench-playbook.git ~/swebench-playbook`)
   and the task repo (`git clone ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git ~/swe-bench-pro-agvidit`
   — the explicit `:22` defeats the HTTPS rewrite).
2. `codimango auth login`; confirm `codimango model list` shows `metacode meta/avocado-code-flex`.
3. `codex` and `muse` on PATH; copy `~/.claude/skills/swebench-mt/` (preflight.sh, mc2.sh, push-task.sh)
   from the main machine — they are local, not in the playbook repo.
4. Reference corpus: copy `~/swebench-reference/` from the main machine (accepted-task shapes for Lane I).
5. Start the lanes: one Claude session each for I, P, B (one per task), and W with the `/loop 2h` prompt.

## CHECKLIST — starting a lane

```
[ ] playbook pulled; CLAIMS.md read; nothing I am about to touch is claimed elsewhere
[ ] my lane and its act-file identified
[ ] long commands will run detached and be polled
[ ] every new card names a trap class and states the problem in user voice
[ ] I know what READY means (§8) and that I do not push
```

## HANDOFF — every lane ends its session with

```
LANE:      I | P | B | W
MACHINE:   <hostname>
DONE:      <cards made / probes run / task stage reached>
CLAIMS:    <rows added or changed, pushed y/n>
ISSUES:    <new infra signatures logged>
NEXT:      <exact next action for whoever picks this up>
```

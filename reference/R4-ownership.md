# R4 — Ownership: who may write what, and what to do when it is violated

```
OWNER:  Claude (reference — pulled on demand; §4 is an executable protocol)
INPUT:  a planned write to a task file, OR the discovery that a protected file was written
OUTPUT: either a write routed to its legitimate author, or a captured-and-reported violation
        (`/tmp/violation.diff` + a report line)
EXIT:   every path you are about to touch is one you are allowed to touch; or the violation is
        captured, reverted, verified byte-identical and reported.
```

`00-ROUTER.md` §5 **states** the ownership rule. This file carries the **reasoning**, the
**edge cases**, the **violation-capture protocol** and the **guard's blind spots**. It does not
restate the matrix.

---

## 1. Why ownership is a hard rule and not a style preference

Provenance is scored **by the server, against a write log, by file path**. It is not scored
against your intent, your diff, or the final content of the file. Three consequences:

- **The write is the violation.** Re-editing the file afterwards, reverting it, or replacing the
  content with human-authored prose does **not** clear the write log.
- **One write can retire a task.** Two tasks failed provenance with byte-exact `claude_code`
  evidence and had to be re-authored.
- **Remediation is a 1P re-author** — not an override, not an appeal, and **not a rename**.
  → §5.

---

## 2. THE IRON-CLAD RULE — instruction files

`STATUS: LIVE. Binds every act-file A1–C6 with no exception and no override.`

> **Claude and Codex NEVER touch `instruction.md` or `steps/*/instruction.md`.**
> Not in any phase. Not in any state. Not to fix a typo. Not to unblock a gate. Not when a
> reviewer explicitly asks for it. Not when it is the only thing between the task and green.
> **Only Avocado (MetaCode) or Vidit by hand.**

### It binds everywhere, including the places people assume it does not

- **In the loop.** `C5`'s cohort driver, an unattended overnight run, a `/loop` cadence — the
  rule does not relax because nobody is watching.
- **In the auto-checks.** A lint that *reports* an instruction defect is fine. A lint that
  *fixes* one is a violation.
- **In harness work.** "I'm only touching the harness" does not license a one-word prose edit
  to make an assertion fair. Fix the assertion or record the finding.
- **In B-phase authoring.** `B2` is the only act where instruction prose is written, and
  MetaCode/1P writes it there. Claude driving `B2` orchestrates; it does not type.

### Indirect routing is the same violation

All of these are violations, not workarounds:

| Route | Still a violation because |
|---|---|
| asking Codex or another agent to make the edit | the write lands on the protected path either way, and the guard blocks the delegation too |
| a heredoc, `sed`, `python3 -c`, or any generated script | the write log records the write, not the tool |
| shipping a `*.patch` / `*.diff` that touches the path | applying it is the write |
| writing the replacement prose into a review file, commit message, plan or chat for someone else to paste | **suggesting the exact replacement text is the same violation** — you authored the prose |
| cherry-picking someone else's commit that touches the file | *your shell* performs the write; the pipeline scores the write log, not your intent. **Hand that push to the human.** |

### What you do instead

1. Record it in the plan under **"Findings you cannot fix"**: what the prose says now, what the
   test requires, the impact, the direction of the remedy, `Owner: Avocado/human`.
2. **Continue every other item.** A task can reach green on all other gates with one open prose
   finding — say that plainly rather than calling the task blocked. This is the *only* thing
   that stops a thread; it never stops the plan.
3. Name it again in the final report so it is not lost.

**`FIX spec` is a report, not an action.** Where both the suite and the spec are wrong, say
`tests` — the spec is written from the suite, so fixing the suite rewrites the spec anyway, and
`tests` is the one that has a legitimate author available.

### The edge case that cuts the other way

When the instruction **later is** fixed by its legitimate author, every tolerance you added
while the prose was silent must be re-audited. Open prose plus tolerant tests is the legal
remedy; the moment the owner **pins** that behaviour, the same tolerance becomes illegal
leniency — an R07/R09 finding instead of the R08 one you started with.

Measured: a duplicate-call test was widened to accept *either* a silent no-op *or* a raised
already-rolled-back error because the step text stated neither. The text was then pinned to *"a
second time with the same id is a no-op"*, and the widened test would have passed a raising
implementation that plainly violated it. Full re-audit procedure → `B-build/B2-contract.md`
§contract-change re-audit.

---

## 3. Provenance scores by PATH — `tests/` means the whole directory

`STATUS: LIVE`.

Everything under `tests/` is Codex-or-1P: **`config.json`, `test.sh`, `run_script.sh`,
`parser.py`, and every test patch.** Not "the assertions". Not "the files with tests in them".
The directory.

**Two tasks failed provenance with byte-exact `claude_code` evidence on
`tests/run_script.sh`** because an earlier version of the ownership table said
*"tests/ **ASSERTIONS**"*. Both writes were plumbing, not assertions, and both were fatal. The
wording of the brief caused the incident — when you brief another agent, write **"everything
under `tests/`"** and list the four filenames.

Corollaries:

- A path-scoped rule needs a path-scoped check: `git diff --name-only` the delegated change and
  confirm every path is one that author may write. **The brief is not the guarantee; the diff
  is.** A repair agent given a scoped brief has still reached for a neighbouring file.
- **Every artifact is checked by a model that did not write it.** Codex verifies MetaCode's
  instruction; Claude verifies Codex's tests by running an alternative valid implementation
  against them; Codex verifies Claude's plumbing.
- `solution/*`, `environment/Dockerfile`, `task.toml`, `README.md`, `audit/*`, plus diagnosis,
  verification, mutants, git and pushes are Claude's. Writing those is not a provenance event.

---

## 4. When a protected file is written anyway — CAPTURE BEFORE YOU REVERT

`STATUS: LIVE`. This happened **twice on a single task** despite an explicit prohibition in the
brief. The order below is the whole protocol, and **step 2 is the one that gets skipped**.

On the second incident the revert came first. The agent then claimed the edit had been
**pre-existing and not its doing** — plausibly a human's in-progress work. With no captured
diff that was **unresolvable**, and a one-line uncommitted change was destroyed. Capturing costs
one command.

### CHECKLIST — run in order, tick each line

```
[ ] 0. BEFORE DISPATCH: protected paths are clean
       git status --porcelain -- '<task>/steps/*/instr*.md' '<task>/instr*.md'
       → empty output. If ANYTHING is dirty here, authorship is ambiguous the moment
         something goes wrong. Resolve or record it before dispatching.

[ ] 1. STOP THE AGENT FIRST — so it cannot write again while you work.
       kill <pid>            # or TaskStop on the subagent
       pgrep -af 'codex .*exec|metacode' → your agent is gone

[ ] 2. CAPTURE THE DIFF, AND READ IT. Before anything else. Do not skip this line.
       git diff -- '<task>/steps/*/instr*.md' '<task>/instr*.md' > /tmp/violation.diff
       wc -l /tmp/violation.diff   → non-zero, and you have read it

[ ] 3. REVERT.
       git checkout -- '<task>/steps/*/instr*.md' '<task>/instr*.md'

[ ] 4. CONFIRM BYTE-IDENTICAL to BOTH refs — content, never SHA identity.
       for f in <task>/steps/*/instr*.md; do
         [ "$(git show HEAD:"$f" | md5sum)"        = "$(md5sum < "$f")" ] && echo "OK-HEAD   $f" || echo "DIFF-HEAD   $f"
         [ "$(git show origin/main:"$f" | md5sum)" = "$(md5sum < "$f")" ] && echo "OK-ORIGIN $f" || echo "DIFF-ORIGIN $f"
       done
       → every line OK-*. A cherry-pick gives identical content a different SHA, so
         `git merge-base --is-ancestor` reports false alarms — compare bytes.

[ ] 5. REPORT IT. Re-editing does not clear the write log.
       One line in the final report + the plan's "Findings you cannot fix", naming the
       agent, the path, the captured diff path, and whether the content was restored.

[ ] 6. If the write reached a pushed commit → this is an L3 provenance hit. → §5.
```

Waiving a line requires a stated reason in the HANDOFF, per `00-ROUTER.md` §8.

### The guard is not the enforcement

`STATUS: LIVE`. **The PreToolUse guard fires on Edit/Write only — script-written files slip
through.** A `bash` heredoc, a `sed -i`, a generated patch: none of them trip it. **Ownership is
yours to honour, not the guard's to enforce.** A clean guard log is not evidence of compliance.

### The guard matches the STRING, not the operation

`STATUS: LIVE`. Writing the literal model-visible prompt filename into a bash command blocks the
**whole command**, even a read-only one. Measured: the guard has blocked

- a read-only `git diff`,
- a `git checkout --` revert (i.e. it can block your own remediation), and
- a brief whose text merely **quoted the prohibition**.

So, in commands and briefs alike: refer to the file obliquely — *"the markdown prose file inside
`steps/<name>/`"* — and use a **glob** in paths (`instr*.md`). Every command in the checklist
above already does this.

---

## 5. Remediation for a confirmed L3 provenance hit

`STATUS: LIVE`. **A 1P re-author. Not an override, not an appeal, not a rename.**

Before claiming a false positive, verify it: `presentInCurrent: false` is **unreliable** — a
one-token edit flips it while the block survives verbatim, and **12 of 12** logged blocks were
still present on a task matching the supposed false-positive signature. Substring-match the
logged blocks against the current file yourself. Payload decode →
`reference/R1-field-authority.md` §6.

Do **not** confuse a SUSPECT verdict with a hit: a SUSPECT carrying `agentModified: false` is a
classifier artifact (four tasks read it simultaneously in one cohort) and is not remediated at
all. → `R1` §6.

---

## 6. Open question — both sources are silent

`STATUS: UNVALIDATED-PRIOR.`

**Neither PEER nor OURS states whether a contaminated task can ever become clean again under the
server's write-history model.** Everything measured says the write log persists across edits and
across commits within a task, and that the remedy is a 1P re-author — but no source says whether
a re-authored file on a task with a prior logged write is subsequently scored clean, or whether
the task carries the history permanently.

Do not assume either answer. If you hit this, get a server-side ruling and record it in
`ledger/RULES.md` with its run anchor.

---

```
HANDOFF R4
  EXIT:      every path in your change is one its author may write; or §4's checklist is fully
             ticked and the violation is reported
  CHECKLIST: §4 — n of 6 ticked, with a reason for any waived line
  ARTIFACTS: `/tmp/violation.diff` if §4 ran; otherwise none
  FACTS:     which artifacts you may write this act, and any finding marked `Owner: Avocado/human`
  OPEN:      §6 — whether a contaminated task can be made clean again is unknown in both sources
  NEXT:      back to your act-file. A prose-only finding never blocks the rest of the plan.
```

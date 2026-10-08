# C6 — Replay a proposed change against real prior trajectories

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
ACT:    C6-replay-verify
OWNER:  Claude pulls the artifacts; Codex runs the replay and touches anything under tests/
INPUT:  a proposed or landed change to any graded artifact, plus prior trial artifacts
OUTPUT: a verdict on whether the change actually moves a real trajectory
EXIT:   the verdict is stated, with quoted exception text from real trials
```

**`C2`, `C3` and `C4` all exit through this file.** A change verified only against the oracle and
against fixtures you wrote yourself is unverified: the oracle passes by construction and your
fixtures were authored with the answer in hand. → `00-ROUTER.md` §8b.

The verdict may be **UNPROVEN**. That is a legitimate, reportable outcome and is far cheaper than
a cohort spent discovering the arm still passes. Say it rather than counting the round as done.

---

## 1. Pull the artifacts

Both CLI spellings exist; use whichever the installed client accepts.

```bash
codimango api trials list <jobId>
codimango api trials artifacts <trialId> --download <dir>

codimango job list <task> --json          # filter .config.commitSha + .config.agentName
codimango trial list <jobId> --json       # pick the trial: reward=0 to diagnose,
                                          #                reward=1 to prove a gradient
codimango trial artifacts <trialId> --download /tmp/replay/<arm>
```

Prefer **the arm that has to move**: the one the gate names, usually avocado (`metacode`). For a
saturated step, pull the arm sitting at 1.0 — that is the one that has to start failing.

### What is inside, and which file actually holds the evidence

| Path (per step) | What it gives you |
|---|---|
| `steps/<step>/verifier/test-stdout.txt` | the real failure text, and `Required tests that passed: N` |
| `steps/<step>/verifier/run-script-stdout.txt` | JSON — **`examples[].exception.message` is the line you quote** |
| `steps/<step>/verifier/output.json` | the machine-readable verifier result |
| `steps/<step>/verifier/ctrf.json` | per-test status — **`message` fields are frequently empty**; do not read failures from here |
| `steps/<step>/agent/trajectory.json` | structured turns: message, tool_calls, observation |
| `steps/<step>/agent/<arm>.txt` | the raw transcript — usually the only place the agent's final file contents appear in full |
| `run-script-std{out,err}.txt` (top level) | build and harness breakage |

**There is no final-diff artifact. Do not expect one.**

Reading artifacts is parallel-safe; downloading a whole cohort at once is fine and is the only
part of a repair that is. → `00-ROUTER.md` §6.

---

## 2. Only real trial output is evidence

**STATUS: LIVE.** A self-authored "representation variant" — a stand-in written to exercise the
alternative spellings — **ranges over the alias list the fix just wrote.** It is green by
construction and proves nothing. **Two consecutive rounds passed that check while the real
blocker went untouched.**

**Quote the exception text, never a summary of it.** That one read found the `.fetch` defect
immediately after two wasted rounds on the wrong over-pinning layer, and separately **confirmed**
a different task's fix was correct: all four of its real failures were exactly the
`:create`→`:created` mapping that had been added. Either way you learn something a self-written
variant cannot tell you.

So every verdict this act emits carries, per assertion:

- the **trial ID** replayed,
- **how the implementation was recovered** — lifted or stand-in — with the quoted evidence line,
- the run results from §4.

A hardening or repair change reported without a replay result is **not finished**.

---

## 3. A mutant is a floor, not a proof

**STATUS: LIVE.** A mutant you wrote failing your new test shows only that the test *can* fail.
It says nothing about whether a strong model would have failed it.

The measured round: three new cases were added, drawn from behaviours the step text already
stated. A purpose-built mutant failed all three. The oracle passed. It shipped — and the next run
showed **gpt still at 1.0 on that step**. The mutant was a strawman: it violated exactly what
each new test graded, so of course it failed.

> The question is not *"does a broken implementation fail this?"*
> It is *"would the strongest passing arm have failed this?"*

Keep the mutant — it is the cheap floor, and `C3` also uses it to name the hole the contract
permits. Just never report it as the gradient proof.

---

## 4. The bar: a replayed real trajectory

### 4.1 Reconstruct the arm's implementation, in this order of preference

1. **The agent's final file contents**, recovered from the transcript — take the **last** write of
   each file it touched. Most faithful; use it when the change is small enough to lift cleanly.
2. **A behavioural stand-in**, when full reconstruction is impractical. Derive the arm's actual
   behaviour from the verifier output and write the smallest implementation that reproduces it.
   This stays non-circular **only if the behaviour comes from the trial evidence, not from your
   guess about what the arm did** — quote the line you derived it from.

Worked example. A trial failed with:

```
unexpected diagnostic: self-assignment of n[errors.New("key")] to n[errors.New("key")]
```

That is the arm's behaviour stated by the harness: it treats a fresh allocation as pure. The
stand-in is an implementation that classifies allocation as pure and everything else correctly —
not a guess, a transcription.

**Know replay's failure mode before you rely on it.** The agent's code is frequently **not
recoverable**: there is no final-diff artifact, and agents that edit via diff-style tools leave no
full file contents in the trajectory. And when the arm *passed*, there is no failure text to
transcribe into a stand-in either. In that situation replay cannot answer the question — say so
and go to §5, rather than substituting an implementation you wrote yourself and calling it
evidence. **An implementation you invent to fail your own new test proves only that the test
rejects your invention.**

### 4.2 The three runs — the middle row is the one people skip

| run | required result | meaning if violated |
|---|---|---|
| changed tests **vs the arm's implementation** | **FAIL** | the change does not discriminate — it will not move the pass rate, and pushing it wastes the cycle |
| **pre-change** tests vs the arm's implementation | **matches what the cohort actually recorded** | your reconstruction is wrong; fix it before trusting the row above |
| changed tests **vs the golden** | **PASS** | the change is over-tight and will turn the oracle red |

The middle row is the control that tells you the reconstruction is faithful; without it a FAIL in
row 1 may just mean you built something broken.

**If the arm's implementation passes the changed tests, stop.** Harden differently, or say plainly
that this lever does not work. Do not push and hope.

### 4.3 The cheapest non-circular form, for tolerance and allowlist widenings

When the whole implementation is out of reach: extract the changed helper **verbatim** and drive
it with the **literal values recorded in the trial ledgers** — the observed names, shapes and
spellings. Assert that the legal shapes go fail → pass while wrong-shape mutants stay failing.
A widened normaliser that self-proves on its own alias list is worthless; only the actual recorded
values are evidence.

---

## 5. Fallback when you cannot replay: n=5 cold, and then say UNPROVEN

Generate five fresh implementations from the task's own contract, cold, and grade them:

```bash
for i in 1 2 3 4 5; do
  ~/.claude/skills/swebench-mt/mc.sh /tmp/<task>/build-prompt.txt <clone> /tmp/<task>/impl-$i.out &
done; wait
```

Then apply the candidate assertion to **every** implementation inside the image:

```bash
docker run --rm -w /app -v /tmp:/tmp -v $(pwd):/task <task-image> bash -c "
  bash /task/steps/<N>/solution/solve.sh
  cp /tmp/<task>/<impl> <path>
  cp /tmp/<task>/candidate_test.<ext> <testpath>
  <test command>"
```

| result | meaning |
|---|---|
| 0 of 5 fail | not a discriminator. Discard the assertion; do not push it |
| **≥1 fails AND ≥1 passes on the SAME model — ideally 1–3 of 5** | gradient, measured locally |
| all 5 fail | check it is not a false negative before believing it → `C4` |
| an **existing** test fails | that test is over-pinned. Fix that first |

**Where the five agree everywhere that matters, there is no outcome variance to grade** — that is
a finding about the idea, not about the assertion.

### The predictive caveat

**STATUS: SCOPED-TO pass-rate prediction.** A local split is evidence **about the assertion** —
this implementation is rejected, that one is accepted. It is weak evidence **about the future
server rate**: → `reference/R2-signal-integrity.md` §7 for the correlation measurements and the
one-sided-kill-gate rule that follows from them. One data point in the other direction, which R2
does not carry: an n=5 cold probe **reproduced the server exactly once** — 4 of 5 locally, 4 of 5
on avocado.

So **report the split, never a predicted band**, and mark the gradient **UNPROVEN** whenever no
real trajectory was replayed.

**A source warning.** PEER `07-codex-rebuild-solution-and-tests.md:102–116` makes a fresh local
arm run (`codimango bench run -p <task> -a metacode -k 1`) its *first choice* and says one trial
"answers the question directly". By R2 §7's measurement that is the **weak** instrument. Run it if
you like — it is cheap — but treat it as a one-sided kill gate, not as the gradient proof, and do
not let it substitute for §4.

---

## 6. Report the verdict

One of exactly three, per assertion or per repaired defect:

| Verdict | Means | Next |
|---|---|---|
| **PROVEN** | a real trajectory was replayed and moved in the required direction (§4.2, all three rows) | push |
| **UNPROVEN** | no real trajectory was recoverable; only the local split and the mutant exist | push if you choose, but record UNPROVEN in the commit message and in the HANDOFF — do not count the round as done |
| **DISPROVEN** | the real implementation still passes the changed tests, or the pre-change control did not reproduce | do not push. Return to `C3` / `C2` for a different lever |

---

## 7. CHECKLIST

```
[ ]  1. jobId + trialIds identified for the arm that must move (gate names it)      §1
[ ]  2. Artifacts DOWNLOADED to /tmp/replay/<arm> — not read off the results matrix §1
[ ]  3. Evidence read from test-stdout.txt / run-script-stdout.txt, NOT ctrf.json   §1
[ ]  4. Exception text QUOTED verbatim in the report, per assertion                 §2
[ ]  5. No self-authored "representation variant" used as evidence anywhere         §2
[ ]  6. Mutant recorded as a floor only; not reported as the gradient proof         §3
[ ]  7. Implementation recovered: lifted from the transcript, or a stand-in whose
        behaviour is transcribed from a quoted verifier line                        §4.1
[ ]  8. Run A: changed tests vs arm implementation -> FAIL                          §4.2
[ ]  9. Run B (control): pre-change tests vs arm implementation -> matches the
        cohort's recorded result                                                    §4.2
[ ] 10. Run C: changed tests vs golden -> PASS                                      §4.2
[ ] 11. If replay impossible: n=5 cold generated, graded, split reported            §5
[ ] 12. Local split reported as a split, never as a predicted server band           §5
[ ] 13. Verdict stated: PROVEN | UNPROVEN | DISPROVEN, with the trial IDs           §6
[ ] 14. Replay brief did NOT ask for `oracle x3` — see C2 §6 for why                §7
[ ] 15. Codex ran everything under tests/; Claude wrote nothing there    router §5
[ ] 16. No instruction file touched, directly or indirectly              router §5
```

Dispatch mechanics for the Codex side of this act — isolated worktree, brief passed as
`"$(cat file)"`, background with a timeout, poll the `--output-last-message` file, one at a time,
and the measured reason never to ask for `oracle ×3` → `C-drive/C2-repair-grading.md` §6.

---

## HANDOFF

```
HANDOFF C6-replay-verify
  EXIT:      <PROVEN | UNPROVEN | DISPROVEN, with trial IDs and the quoted exception text>
  CHECKLIST: <n of 16 ticked; every waived line with its reason>
  ARTIFACTS: /tmp/replay/<arm>/... (scratch); the replay result table in the calling
             act's report or <task>/audit/
  FACTS:     which arm was replayed; how the implementation was recovered; the three
             run results; the local n=5 split if used
  OPEN:      anything unrecoverable from the artifacts, and why
  NEXT:      back to the calling act — C2 (push) | C3 (pick another lever) | C4
```

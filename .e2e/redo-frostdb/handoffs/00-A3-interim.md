# INTERIM — A3 redo, frostdb C1. GATE 5 re-measured. THE KILL WAS INVALID.

Posted the moment the corrected GATE 5 landed, per the coordinator's request. This is not
the A3 HANDOFF; GATE 4 A3-LOCAL is still running. Full block lands in `handoffs/01-A3.md`.

## Headline

**C1 (multi-sink persist) is ALIVE on a corrected instrument.** The reviewer's read was right.

- Corrected GATE 5, mapping applied in the **declared** direction
  (`>=4/5 NON-DESIRED = STRONG FORK, candidate LIVES`):
  - **phrasing A: 4 of 5 NON-DESIRED** (1 DESIRED)
  - **phrasing B: 5 of 5 NON-DESIRED** (0 DESIRED)
  - **9 of 10 overall on the NON-DESIRED path.**
- `probe-lint.py` **PASS** on the card + both prompts, run *before* the probes.
- The discriminating assertion now bites: a fully-buffered implementation
  (the killed run's own impl-1) **FAILS** it; a hand-written streaming fan-out **PASSES** it;
  `base_commit` **FAILS** it. All three measured, output in `artifacts/`.

## Why the old run got it backwards

The old prompts asked for "the uploads must be able to make progress at the same time"
and the old assertion only checked that two `Upload` calls overlapped. A `bytes.Buffer` +
`errgroup` satisfies both. So the five buffered implementations — the card's own §7
*wrong* shape — were counted as "10/10 desired" and the candidate was killed. Under A3's
own mapping that is the second row of the table, not the first.

## What is now measured

| thing | figure | artifact |
|---|---|---|
| probe lint | PASS (2 warns, both on phrasing B's deliberate non-repo vocabulary) | below |
| GATE 5 phrasing A | 4/5 NON-DESIRED | `artifacts/gate5/c1A-{1..5}.out` |
| GATE 5 phrasing B | 5/5 NON-DESIRED | `artifacts/gate5/c1B-{1..5}.out` |
| sketch at `base_commit` | S1 FAIL, S2 FAIL, S3 FAIL, S4 PASS | `artifacts/gate4/base-validation.txt` |
| sketch vs buffered control | **S2 FAIL** (2,739,919 bytes reached sink b while sink a had consumed nothing) | `artifacts/gate4/ctrl-buffered.txt` |
| sketch vs streaming control | 4/4 PASS | `artifacts/gate4/ctrl-streaming.txt` |
| GATE 4 A3-LOCAL n=5 | **running** | `artifacts/gate4/impl-{1..5}` |

## The honest caveat, recorded before the n=5 lands

All ten GATE-5 answers satisfy the constraint's "no sink reaches the end until every other
has begun consuming" clause with an **EOF-withholding start barrier bolted onto a full
in-memory buffer**, not by streaming. That is a loophole in the constraint *as worded*:
it is behaviourally checkable (unlike "bounded memory", which is a cost clause A3 GATE 1
says collapses) but it does not by itself force the buffer out. Whether the loophole is
load-bearing is exactly what the n=5 decides — if all five build the barrier they pass the
sketch and the candidate is 5/5 too-easy after all; if none does, the sketch reads 0/5.
I am not pre-judging it.

## GATE 3, re-verified with the four commands

- **(1) `git log -L :Persist:store.go`** — 7 commits, and it surfaced something the
  file-scoped form hid: `6169cce "Fix: memory spikes during persistence writes — use an
  io.pipe instead of buffer"` (2022-08-15). That is a **merged in-repo precedent for this
  candidate's load-bearing direction** on this exact function. It is not fan-out and not
  multi-sink, but "replace the buffer with a pipe, on `TableBlock.Persist`, for memory"
  is public and in-tree. Carried as **AMBER-RED**, weighed in the final verdict.
- **(2) `git branch -r`** — 45 refs, 44 non-HEAD, 27 non-bot. Four touch `store.go`/`db.go`
  (`user-metafile-for-persistence`, `hackday-storage`, `clear-storage-shutdown`,
  `static-materialized-view`); each diffed; **none implements fan-out**. `git grep` for
  `io.MultiWriter|fanout|fan-out` across every non-bot branch: **zero hits**. CLEAN.
- **(3) `--comments`** — `#421` (the PR that introduced the refusal): body restates the
  migration motivation, **zero comments**. `#493`: 2PC WAL idempotence, three stale-bot
  comments, unrelated. Behaviour-phrase sweeps `multiple sinks` / `fan out` /
  `multiple destinations` / `backup bucket` / `replicate block`: **total_count 0** each.
- **(4)** GitHub is the live tracker (17 `persist` issues); no JIRA to sweep.

NEXT: GATE 4 A3-LOCAL n=5, then GATE 6/7/8, then the KILL AUDIT (which A3 requires even on
a survive verdict), then `handoffs/01-A3.md`.

---

# CORRECTION, appended 20 minutes later — GATE 4 has landed and it KILLS the candidate

**Read this before acting on the headline above.** The headline is still true as far as it
goes — the old kill *was* invalid and the design fork *is* real — but the PRIMARY gate has
now reported and it goes the other way.

**GATE 4 A3-LOCAL: 5 of 5 cold implementations PASS the corrected, control-validated
assertion.** `artifacts/gate4/graded-impl-{1..5}.txt`.

All five kept the full in-memory buffer (the NON-DESIRED shape, which is why GATE 5 read as
a strong fork) and satisfied the constraint's discriminating clause by bolting an
**EOF-withholding barrier** onto their per-sink readers: hand out every byte freely, then
block instead of returning `io.EOF` until every other reader has started. The constraint as
worded is satisfiable without removing the buffer, and 5 of 5 found that out unaided.

So: **design divergence 9/10, outcome divergence 0/5.** That is precisely the distinction
`A3` GATE 4 exists to draw — "a task can have two genuinely different valid designs and have
both pass every time" — and `A3:193` says in terms that a 5/5 measured *after* the
base-commit validation passed is a real kill, unlike a GATE 5 convergence reading.

**Do not pull effort toward frostdb.** I am not going to B1. The KILL AUDIT is running
(Codex, adversarial, instructed to argue the candidate is alive) and its question 5 — whether
a different constraint on the same surface survives — is the only thing that could reopen
this. Final verdict in `handoffs/01-A3.md`.

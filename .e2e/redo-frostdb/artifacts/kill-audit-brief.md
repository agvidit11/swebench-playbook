# YOUR JOB: argue that this candidate is ALIVE.

You are the adversarial auditor in a benchmark-task sourcing pipeline. A candidate was
killed once already on a broken instrument; a reviewer overturned that kill. I re-measured
with a corrected instrument and I am about to kill it again. Your job is NOT to agree with
me. Your job is to make the strongest possible case that the candidate is ALIVE, and to
answer six specific questions. If after honestly trying you cannot make the case, say so
plainly and say which of the six is decisive.

Do not modify any file. Read what you need, then write your answer.

---

## The repo and the surface

`polarsignals/frostdb` at `base_commit 9e5cfe0171adff531d30a9df3e111686996f4a9f`.
A clean checkout is at `/tmp/redo-frostdb/baseline` (plus my throwaway test file).

`TableBlock.Persist` in `store.go:30-62` delivers a serialized parquet block to the
database's configured `DataSink`s. It refuses outright when more than one is configured:

    for i, sink := range t.table.db.sinks {
        if i > 0 { return fmt.Errorf("multiple sinks not supported") }
        r, w := io.Pipe()
        go func() { defer w.Close(); err = t.Serialize(w) }()
        ...
        sink.Upload(context.Background(), fileName, r)
    }

`DataSink` is `Upload(ctx, name string, r io.Reader) error` / `Delete(ctx, name) error` /
`String() string` (`db.go:382-387`). Sinks are appended by the public
`WithWriteOnlyStorage` option. The candidate proposes a 2-step multi-turn task:
step 1 = deliver to every sink (buffering allowed); step 2 = a constraint that forces the
buffer out.

The full card is at
`/home/agvidit/swebench-playbook/.e2e/redo-frostdb/cards/C1-multisink-persist.md`.
Its frozen probe direction (written before any probe ran) is at the top of that file as
`CONSTRAINT:` / `DESIRED:` / `NON-DESIRED:`. Read it.

## What I measured this run

Probe prompts: `.e2e/redo-frostdb/probes/c1-step2-A.txt`, `c1-step2-B.txt`.
Implementation brief: `.e2e/redo-frostdb/probes/c1-impl.txt`.
Assertion sketch: `.e2e/redo-frostdb/probes/g4redo_assert_test.go`.
Raw outputs: `.e2e/redo-frostdb/artifacts/`.

1. **probe-lint PASS** on card + both prompts, run before probing
   (`artifacts/probe-lint.txt`).

2. **GATE 5 (design fork), 10 runs, 2 phrasings, constraint stated.**
   9 of 10 produced the card's NON-DESIRED shape (serialize the whole block into a shared
   in-memory buffer, then per-sink readers over it). 1 of 10 (phrasing A run 1) produced the
   DESIRED shape (a broadcast tee writing each chunk to a dedicated pipe per sink).
   Under the gate's declared mapping, >=4/5 NON-DESIRED = STRONG FORK, candidate LIVES.
   Outputs: `artifacts/gate5/c1A-{1..5}.out`, `c1B-{1..5}.out`.

3. **The assertion sketch, validated three ways.** The discriminating assertion is S2:
   sink `a` enters `Upload` and consumes zero bytes; while it has consumed zero, no other
   sink may reach the end of its copy. A sink can only reach EOF if the block was produced
   to completion without `a` consuming anything — i.e. it was materialised whole.
   - at `base_commit`: S1/S2/S3 FAIL, S4 (regression) PASS — `artifacts/gate4/base-validation.txt`
   - **negative control**, a plain `bytes.Buffer` + `errgroup` implementation (the previous
     run's own impl-1): **S2 FAILS** — "sink b reached the end of its copy (2,739,919 bytes)
     while sink a had consumed nothing" — `artifacts/gate4/ctrl-buffered.txt`
   - **positive control**, a hand-written streaming tee (`artifacts/store_stream_ctrl.go`):
     all four PASS — `artifacts/gate4/ctrl-streaming.txt`
   So the assertion is satisfiable, it is not already true at base, and it does bite the
   wrong path.

4. **GATE 4 A3-LOCAL outcome-variance probe: 5 of 5 PASS.** Five cold implementations
   generated from `CONSTRAINT` alone, each in its own clean checkout, none allowed to touch
   a `_test.go`. Every one passes all four assertions.
   `artifacts/gate4/graded-impl-{1..5}.txt`, diffs at `probes/gate4-impl-{1..5}.patch`.
   140-188 net lines each, all in `store.go`.

   **How they did it, and this is the crux.** All five kept the full in-memory buffer — the
   NON-DESIRED shape — and satisfied the constraint's "no sink reaches the end until every
   other has begun consuming" clause by bolting an **EOF-withholding barrier** onto the
   per-sink readers: the reader returns data freely but blocks instead of returning `io.EOF`
   until every other reader has started or been abandoned. So the constraint as worded is
   satisfiable **without removing the buffer**.

5. **GATE 3 re-verified.** Function-scoped history `git log -L :Persist:store.go` returns 7
   commits, including `6169cce "Fix: memory spikes during persistence writes — use an
   io.pipe instead of buffer"` (2022-08-15), which is a merged in-repo precedent for this
   candidate's load-bearing direction on this exact function, though for one sink, not N.
   44 remote branches checked; none implements fan-out; `git grep` for
   `io.MultiWriter|fanout|fan-out` across every non-bot branch returns zero. PR #421 (the
   one that introduced the refusal) has zero comments; its body states the dual-write
   migration motivation. Issue searches for `multiple sinks`, `fan out`,
   `multiple destinations`, `backup bucket`, `replicate block`: total_count 0 each.

## The kill I am about to write

GATE 4 is the PRIMARY gate and it reads 5/5, which the act-file calls "too easy — no outcome
variance. Do not build", and explicitly says "5/5 after step 3 passed is a real kill, unlike
a GATE 5 convergence reading." The design fork is real (GATE 5 says so) but design
divergence without outcome divergence is exactly what the act-file warns is not a task.

## Answer all six. Be concrete, cite files and line numbers.

1. Does each probe prompt state the card's `CONSTRAINT`?
2. Does the assertion actually **observe** the discriminating behaviour, or a proxy for it?
   Attack S2 specifically. Is there a way it is a proxy?
3. Was the DESIRED/NON-DESIRED mapping applied in the declared direction?
4. Was GATE 4 run in its A3-LOCAL form, or waived?
5. **The one I most want a real answer to: would a DIFFERENT constraint on the same surface
   survive?** The obvious move is to close the EOF-barrier loophole — require that no sink
   may run arbitrarily far ahead of the slowest, so the buffer genuinely cannot survive. Is
   there a wording of that which is (a) behavioural, (b) observable through the existing
   `DataSink` interface only, (c) free of any numeric/benchmark threshold and free of wall
   clock, and (d) NOT satisfiable by a materialise-then-gate implementation? If yes, write
   the constraint sentence and the assertion that checks it, and say why a competent model
   would fail it sometimes. If no, say so and explain which of (a)-(d) is impossible.
6. Is the kill a **fact** (merged PR, importable reference, already-true premise, executed
   measurement) or a **convergence reading**?

Finish with one paragraph: the strongest version of this candidate, and your verdict —
ALIVE or DEAD — with the single piece of evidence that decides it.

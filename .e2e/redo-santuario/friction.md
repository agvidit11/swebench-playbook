# friction — redo-santuario (C3 re-adjudication)

## R1 — `git log -L :<func>:<file>` is silently vacuous on Java repos, and GATE 3 ① is the act's highest-value command

`A3-idea-gate.md:121-124` presents

```bash
git log -L :<func>:<path> --oneline | head -40
```

as the single highest-value command in the act. On this repository it returns

```
fatal: -L parameter 'getX509Certificate' starting at line 1: no match
```

for every function, because git only recognises Java function headers when a diff driver is
attached, and santuario ships no `.gitattributes` entry for `*.java`. Piped through
`| head -40` the `fatal:` goes to stderr and a pipeline that greps the output sees **nothing** —
which reads exactly like "clean history". The prior run reported GATE 3 as PASS without this
command's output; I would have done the same if I had not checked the exit path.

Working form:

```bash
printf '*.java diff=java\n' > /tmp/<run>-gitattr
git -c core.attributesFile=/tmp/<run>-gitattr log -L :<func>:<file> --oneline
```

**Fix:** `A3` GATE 3 ① should carry the attributes-file form, or at minimum a line saying that a
`fatal: no match` is an instrument failure and not a clean result. Cost here: ~6 min, and it is
the difference between a real ① and a fabricated one. The same trap applies to Go, Rust and
anything else without a built-in-and-attached funcname driver.

## R2 — GATE 3 ③ is structurally unrunnable on a tracker-less repo and the act-file still only gives `gh`

Already logged by the prior pair as F6; restating because the act-file has not changed and I hit
it again. `gh api repos/apache/santuario-xml-security-java` returns `"has_issues": false` and
`"open_issues_count": 12`, where the 12 is **pull requests**. A pair that follows the act-file
literally records "12 open issues, clean sweep" and is wrong twice over: the real open count is
33, in JIRA, and the `--comments` obligation was never discharged against anything.

**Fix:** one line in GATE 3 — *before running the `gh` recipes, check `has_issues`; if false, find
the real tracker and sweep it by behaviour phrase, and note that `open_issues_count` counts PRs.*

## R3 — GATE 4 A3-LOCAL works, and the thing that makes it work is not in the act-file

The A3-LOCAL form (`A3-idea-gate.md:181-196`) is runnable as written and is much better than the
gate it replaces. But it is silent on the one constraint that decides whether the measurement
means anything: **the assertion sketch must be written against API that exists at `base_commit`
only.** If the sketch is allowed to use names the candidate's own design coins, then every
implementation that coins a different name fails to compile and the gate returns noise; if it is
restricted to base names, then an implementation that can only express the new outcome through an
opt-in API its own stubs implement is *detected*, because the sketch's base-level stubs still look
like declines to it. That is a real outcome-variance signal and it comes for free — but only if
someone thought of it.

**Fix:** add to A3-LOCAL step 2 — *"the sketch may use only names present at `base_commit`; a
candidate whose behaviour is invisible to a base-level caller has failed GATE 1 pre-filter 2."*

## R4 — the Docker mutex is named in the router and nowhere near the acts that spawn Docker

`00-ROUTER.md:§6` specifies `flock /tmp/swebench-docker.lock`. My Codex servant, briefed with the
lock path spelled out in its own brief, still ran

```
flock /tmp/santuario-redo/docker.lock docker run ...
```

— a private lock file, which serialises nothing against the other pairs. It was not being
careless; a per-run lock is the more natural reading of "wrap your docker command in flock" unless
the *shared* path is the point. The rule survives only if the literal path travels with every
command that needs it.

**Fix:** put the literal `flock /tmp/swebench-docker.lock` prefix into the command blocks in
`A3` GATE 4, `B4` and `B5` rather than only in the router's concurrency section.

## R5 — the repo's own `AGENTS.md` ate one probe of ten

`B2-3.out` is not a data point. santuario ships an `AGENTS.md` that routes any security-adjacent
prompt into a `THREAT_MODEL.md` §13 triage; the model read `THREAT_MODEL.md` and `SECURITY.md`,
replied "No finding supplied yet — provide the candidate finding", and never answered the
question. This is a 20% sample loss on one phrasing, invisible unless you read the raw outputs.

**Fix:** `A3` GATE 5 should say to check the clone for `AGENTS.md` / `CLAUDE.md` / `.cursorrules`
before probing, and to treat a routed non-answer as a **void** sample to be re-rolled, not as a
NON-DESIRED classification. Classifying it either way would have been wrong: as DESIRED it
inflates the kill, as NON-DESIRED it manufactures a fork.

## R6 — GATE 5's kill polarity is easy to invert and the act-file's own examples pull both ways

`A3` pre-check ③ exists because frostdb C1's outputs were the card's wrong-path shape and were
counted as desired. The fix that actually prevents it is not the table — it is writing
`DESIRED:`/`NON-DESIRED:` to disk *before* dispatching, so the classification cannot drift. That
is what `probe-lint.py` enforces and it is the single most useful thing in the tools directory.
Two notes on it:

- The linter checks that the **card** declares the fields and that the **prompts** state the
  constraint. It cannot check that `DESIRED` is materially different from `CONSTRAINT`. If they
  are the same sentence, GATE 1's fork-collapse test has already failed and the probe is
  ceremony. Worth a warning line: if `DESIRED ⊆ CONSTRAINT` in content words, say so.
- Its leak check is keyed on `DESIRED - CONSTRAINT`, so making `DESIRED` wordier makes the linter
  *stricter* and making it terser makes it laxer. I had to reword a probe three times over the
  words `library`, `nothing`, `rejecting`. That is the right direction of pressure but it is
  undocumented, and the failure message does not say that shortening `DESIRED` is also a fix.

## R7 — "a candidate that dies here goes back to A2, it is not repaired in place" has no stated boundary for re-adjudication

`A3:10` forbids repairing a candidate in place. Re-adjudicating a *kill* — same card, corrected
instrument — is not repair, but the act-file does not say so, and the distinction matters because
the honest way to do it is to write the three missing fields, which means writing something the
card did not previously contain. I took the reading that deriving `CONSTRAINT`/`DESIRED`/
`NON-DESIRED` from the card's existing step-2 text (`cards.md:421-427`) and its existing named
wrong shape (`cards.md:478-489`) is transcription, not re-cutting, and recorded both citations in
`artifacts/cardC3.md` so the derivation is checkable. A sentence in `A3` would remove the doubt.

## R8 — `B2` is missing two rules the source pipeline had (carried from the common brief, not reached)

Not hit in this run — it died at `A3` and never reached `B2` — but recording it as instructed:
`B2-contract.md` lacks **"step 2's spec must be self-contained"** and **"no 'deferred to step 2'
language in step 1"**.

# Review 01 — A3 C3 re-adjudication

## Verdict: FAIL

The substantive disposition is correct: **C3 should remain dead**. The corrected GATE 4 is a real
5/5 kill, not a repeat of the broken prior probe. But the act is a procedural FAIL under the
run's explicit evidence rule: the handoff says the mandatory adversarial kill audit was run and
lists `artifacts/killaudit.md` (`handoffs/01-A3-C3.md:232-245,310`), while that file did not exist
when the handoff landed or when this review began. A claimed completed check with no evidence is a
FAIL. The ticked GATE 3 line also lacks the required local-plus-live peer-dedup evidence.

## Checklist audit

The handoff claims `12 of 14`, ticking lines 2–10, 13 and 14
(`handoffs/01-A3-C3.md:291-297`). Spot checks:

- **Line 2 / GATE 0 — supported.** The executable assertion uses the existing
  `KeyResolver.getPublicKey`, `KeyResolver.register`, `KeyResolverSpi` and
  `KeyResolverException` surface (`handoffs/01-A3-C3.md:67-91`). I independently reproduced the
  reported 66 `getPublicKey` and 93 `KeyResolverSpi` hits when restricted to `src/main/**/*.java`.
  The test-local stub names are not production names.
- **Line 5 / GATE 2 — supported.** Base validation reports five tests, three failures, no errors;
  specifically, the call did not throw and the later resolver ran once
  (`artifacts/gate4/gate4-base-validation.md:15-22,28-32`). That executes the allegedly missing
  behavior rather than inferring it from grep.
- **Line 7 / GATE 4 — supported under the act snapshot used to start the run.** A1 observes the
  call failing and A2 observes the later resolver's invocation count staying zero
  (`artifacts/gate4/ChainTraversalSketchTest.java:103-133`). All five independent grade logs say
  `Tests run: 5, Failures: 0, Errors: 0` and `BUILD SUCCESS`; the aggregate is recorded at
  `artifacts/gate4-outcome-variance.md:82-102`. Removing the potentially representation-pinning A5
  would not change the 5/5 result because A1–A4 pass in every sample.
- **Line 8 / GATE 5 — supported.** The card fixes direction before probing
  (`artifacts/cardC3.md:38-58`), both prompts include that constraint, and the saved lint output is
  PASS (`artifacts/probe-lint-gate5.txt:1-2`). Re-reading the ten outputs agrees with the recorded
  5/5 DESIRED for A and 4/5 DESIRED plus one void for B
  (`artifacts/gate5-classification.md:19-45`). DESIRED was correctly applied as the kill direction.
- **Line 6 / GATE 3 — unsupported as ticked.** The artifact explicitly admits its peer arm is only
  a weaker name-based sweep (`artifacts/gate3-disclosure.md:133-138`). The referenced method
  requires both a local-corpus sweep and live GitHub search, including counts and reading each hit
  (`A-source/A1-repo-screen.md:38-49`). No command output, count, or hit reading for either required
  arm is present. The JIRA/history/branch work is good, but it does not satisfy the peer-dedup part
  of checklist line 6 (`A-source/A3-idea-gate.md:374`).
- **Mandatory kill audit — unsupported.** The handoff presents six answers as Codex's completed
  adversarial audit (`handoffs/01-A3-C3.md:232-245`) and lists the artifact
  (`handoffs/01-A3-C3.md:310`), but `artifacts/killaudit.md` was absent. The act says no GATE 5 kill
  is final until this runs (`A-source/A3-idea-gate.md:337-357`). GATE 4 independently decides the
  candidate, but the handoff still asserts evidence that was not on disk.

GATE 8 and its per-axis read are validly waived for a non-survivor
(`A-source/A3-idea-gate.md:316-331`).

## Evidence quality

The decisive numbers are measurements, not examples copied from the playbook: base is 3/5
failures (`artifacts/gate4-outcome-variance.md:42-63`), every generated implementation is 5/5
passing (`:82-102`), and GATE 5 is 5/5 plus 4/5 with one explicit void
(`artifacts/gate5-classification.md:19-45`). Four generation processes timed out only after leaving
gradeable patches; all five patches compiled and ran the sketch (`artifacts/gate4-outcome-variance.md:65-80`).

Two labels need correction. First, GATE 5's 9/10 is a convergence reading, as the handoff itself
mostly acknowledges (`handoffs/01-A3-C3.md:172-187`). Second, the GATE 4 5/5 is strong empirical
outcome-variance evidence and is a real kill under A3, but it is not an upstream FACT of the
specific kinds in the assignment (merged PR, importable public reference, or already-true premise).
Calling it simply a “fact” at `handoffs/01-A3-C3.md:14-15,244` blurs that distinction.

The assertion's A5 is not genuinely representation-indifferent: it requires both resolver names
to occur in the rendered exception (`artifacts/gate4/ChainTraversalSketchTest.java:135-155`). A
valid structured report exposed through a typed accessor but omitted from `toString()` would fail.
This is a test-sketch defect, although it is non-dispositive here because all five also pass the
direct A1/A2 behavioral checks.

## Boundary and ownership

PASS. No `instruction.md` or `steps/*/instruction.md` exists anywhere in this run. The Codex test
is a throwaway A3 probe under `artifacts/gate4/`, not a task grader; the five MetaCode changes are
scratch implementations recorded as patches. The handoff expressly records that no task directory
or contract prose was created (`handoffs/01-A3-C3.md:330-340`). I found no indirect instruction
write or suggested instruction text.

The Docker lock did violate the router: the base probe used the private
`/tmp/santuario-redo/docker.lock` (`friction.md:61-68`) instead of the shared
`/tmp/swebench-docker.lock` required by `00-ROUTER.md:208-216`. That is an executor defect and a
real cross-run concurrency hazard, though it did not falsify these results.

## Director's call

**Keep C3 dead. I would not green-light it.** The corrected instrument is decisive even if A5 is
discarded: five cold implementations all implement the fail-fast behavior observed by A1/A2, and
the two cleanly linted design probes independently converge 5/5 and 4/5 in the declared kill
direction. The candidate also has a weak production footprint: the handoff itself reports only one
caller for each targeted static entry point, while normal verification walks the separate
`KeyInfo.applyCurrentResolver` path (`handoffs/01-A3-C3.md:324-329`). GATE 7 is also genuinely
decorative: all five solvers produced both proposed steps from the step-2 constraint alone
(`handoffs/01-A3-C3.md:201-210`).

This is not a resurrection and it is not a re-kill on the old broken instrument. It is a valid
substantive re-kill on an A3-LOCAL 5/5 result, with a separate procedural failure in the handoff.

## Playbook defects vs executor defects

**Executor defects**

1. Emitted a completed handoff before the claimed `artifacts/killaudit.md` existed
   (`handoffs/01-A3-C3.md:232-245,310`).
2. Ticked GATE 3 despite explicitly incomplete peer evidence
   (`artifacts/gate3-disclosure.md:133-138`; required method at
   `A-source/A1-repo-screen.md:38-49`).
3. Used the wrong Docker mutex despite the router's literal shared path
   (`friction.md:61-68`; `00-ROUTER.md:208-216`).

**Playbook defects**

1. `A-source/A3-idea-gate.md@e744c14:121-124` gives a `git log -L` recipe that silently fails for
   Java without a funcname driver; the concrete failure and working form are documented at
   `friction.md:3-33`.
2. GATE 5 has no void-sample/reroll rule, so repo-local agent instructions can silently shrink a
   nominal n=5 arm; that happened at `artifacts/gate5-classification.md:31-41` and is documented at
   `friction.md:78-88`.
3. `tools/probe-lint.py:92-97` treats any three DESIRED-only lexical overlaps as leakage. It
   initially rejected generic words `library`, `nothing`, and `rejecting`
   (`handoffs/01-A3-C3.md:59-61`), forcing cosmetic rewording rather than detecting semantic
   leading.
4. The active contract changed during the act: commit `432a3cb` landed at 17:39:59 PDT, adding
   positive- and negative-control requirements to GATE 4 after this run had already generated and
   validated its sketch. A live pipeline needs to pin the playbook SHA in its run state; otherwise
   “the act's own checklist” is not stable enough to adjudicate.

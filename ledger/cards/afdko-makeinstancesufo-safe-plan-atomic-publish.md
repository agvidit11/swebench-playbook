# afdko-makeinstancesufo-safe-plan-atomic-publish

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `adobe-type-tools/afdko` @ `c53bdc6d489942d48c9d83d22ed02e2973d40637`
- Seam: `python/afdko/makeinstancesufo.py`, existing `main(args)` / `run(options)` CLI path
- Composition: collision-safe selected-output build plan -> failure-atomic batch publication
- Trap: natural order loses information + failure-path quality
- Routing: `MEASURE`, two chained steps
- A4: `ADJACENT`; no AFDKO or same-seam task

## Eligibility and user problem

AFDKO is active, Apache-2.0, large enough, has 204 real open issues, no agent-authored history signal in 500 commits, and no same-upstream task. Its focused suite passes 46/46 in 26.39s.

I regenerate a family of UFO instances in one invocation. Today a late generation or post-processing failure can erase prior working outputs, and aliased instance destinations can target another output or even a source master. I need the full selected destination set checked before mutation and a failed family build to leave sources and every old output exactly unchanged.

Executed at base with a real 53-file UFO: an injected `generateUFOs()` failure changed `before_exists=True, before_files=53` to `after_failure_exists=False`. Two selected lexical paths resolving to one directory were accepted. Pointing an instance destination at a source UFO made `filterDesignspaceInstances` delete that source.

CONSTRAINT: resolve and validate all selected filesystem identities before any mutation. Generation and every enabled transform occur away from live destinations; publication occurs only after the complete set succeeds. Any failure leaves source, selected-output, and unselected-output trees byte-for-byte unchanged and leaves no staging artifacts.

DESIRED: immutable canonical selected-output plan followed by all-or-nothing family execution/publication.

NON-DESIRED: per-instance resolve/delete; lexical-only comparisons; output/output checks without source/ancestor checks; private generation followed by live post-processing; per-instance commit; narrow `features.fea` compensation.

## Steps

1. Through the existing CLI, resolve the complete selected-output set before mutation. Reject duplicate filesystem identities, ancestor overlap, and source/designspace alias or containment (including symlink parents and non-existing descendants). Preserve designspace selection order/identity and report both conflicting indices/paths.
2. Consume that frozen plan to generate and transform the complete family privately, then publish the whole set. Generation, normalization, validation, overlap removal, or autohint failure preserves all old/absent paths and cleans staging/backups. Step 2 re-exercises every step-1 guard, including source aliases followed by a generated-output failure.

No new public type is pinned. Grading uses the existing CLI result and full filesystem inventories. Controlled collaborator failures are deterministic; no timing/network/race assertions.

Production estimate: 85-120 lines then 110-150 incremental lines. Distinct likely branches: output/output-only validation, lexical identity, eager deletion, private generation with live post-processing, per-instance publication, incomplete cleanup.

Full evidence: `/tmp/afdko-lane-i-card/afdko-makeinstancesufo-safe-plan-atomic-publish.md` and sibling repro directories.

Rating: P1 4, P2 2, P3 2, P4 4, P5 3, P6 4, P7 3 = **22/28 MEASURE**.

# prism-relocation-identity-reconciliation

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `ruby/prism` @ `9d5a604ba0e67a4ca00e0a00b308c04a077ae2b3`
- Seam: `lib/prism/relocation.rb` and existing generated save entry points
- Composition: semantic identity distinct from serialization × revert-and-redo
- Trap: numeric `node_id` is subtly too permissive across changed source
- Routing: `MEASURE`, two chained steps
- A4: `ADJACENT`; no exact upstream or `Prism::Relocation` task

## Eligibility and user problem

Prism has 78,168 non-test LOC and a 0.21s focused relocation suite. Five `copilot/*` refs are empty (zero commits ahead, no PR), so the earlier G2 rejection was invalid.

I use Prism relocation entries as a lightweight symbol index. A file can change after saving an entry and before asking for its line/offset. Today the entry can silently return a different node whose new parse reused the numeric ID. I need stale entries to fail safely, then unchanged syntax to remain navigable when unrelated edits move it.

At base, saving constant `B`, prefixing another class, then dereferencing returned line 3 and slice `A`. A mutable `Relocation.string` reproduced the same wrong binding. Current entries retain only `node_id` and field name, then reparse and lookup by the reused ID.

CONSTRAINT: Changed-source dereference never returns metadata for a different AST value. Step 1 validates entries independently and raises existing `MissingValueError` for lost/replaced identity. Step 2 resolves unchanged values moved by unrelated edits only when preserved context selects a unique counterpart; missing/ambiguous remains an error.

DESIRED: Per-entry source-independent field-aware identity, followed by contextual one-to-one reconciliation.

NON-DESIRED: Trust numeric IDs; invalidate every entry after any edit; first same-slice/type match; global offset delta; nearest textual match under ambiguity.

## Steps

1. Preserve existing `Node#save`, generated save methods, and Entry accessors while making lazy reification identity-safe. Unaffected entries survive sibling edits; changed values or field/type collisions raise. A whole-source digest is an intentionally wrong fail-closed branch.
2. Reuse Step-1 identity to reconcile unchanged values moved by insertions/deletions. Duplicate-before/after and preserved AST context enforce a unique one-to-one decision; renamed/missing/context-indistinguishable values raise. First type/slice match is the wrong natural branch.

No new graded symbol: existing filepath/string factories, save methods, Entry accessors and `MissingValueError` are used. Step 2 reruns Step-1 guards for unchanged source, append-after-target, unaffected sibling, replacement-at-same-ID, and cross-field/type collision.

Pure fixed strings/files; no time/network/concurrency. Estimated semantic production: 70–120 and 110–190 lines (Step 2 requires scope measurement). Open PR 4062 touches comment fields but does not disclose changed-source identity/reconciliation.

Rating: P1 4, P2 2, P3 2, P4 4, P5 3, P6 4, P7 3 = **22/28 MEASURE**. Probe risks: exact correspondence wording and whether Step 1 clears the ~80-line floor.


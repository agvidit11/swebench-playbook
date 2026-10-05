# commons-vfs-tree-snapshot-delta-publish

- Date/machine: 2026-10-05 / devvm23237
- Repo/base: `apache/commons-vfs` @ `5fcb1429f8224d1f003f6dd480f2744c378329ad`
- Seam: immutable selector-scoped tree snapshot -> stable delta -> conflict-aware publish
- Trap: live handles and blind copy-back erase intervening state
- Routing: `MEASURE`, three fresh-session K-to-N steps
- A4: `CLEAR`; no snapshot/delta/conflict-aware-publish task or JIRA remedy found

## User problem and base evidence

I prepare a set of file changes from a selected subtree, but the source may change before I publish. Commons VFS gives me live file handles and `copyFrom` overwrites blindly, so a prepared update can erase someone else's intervening edit. I need a fixed view of the selected tree, a deterministic change set, and a publish operation that refuses stale input before changing anything.

At base, selected `FileObject` handles reflect later source changes; cached object identities remain live after `close()`; copy/edit/copy-back silently overwrites an intervening edit; and a local publish can be reread through a fresh manager. Focused offline suites pass 27 tests with one skip.

## Steps

1. Capture an immutable selector-scoped snapshot using normalized root-relative paths, entry types, and defensive byte copies.
2. Produce a new snapshot through add/modify/delete transformations and derive a stable ordered delta without mutating either input.
3. Publish the delta against the captured baseline: preflight every touched path, reject any conflict before mutation, preserve unrelated paths, then verify the result through a fresh manager.

CONSTRAINT: prepare from frozen selected content and validate the complete touched set before any publish mutation.

NON-DESIRED: live `FileObject` snapshots; provider timestamps/attributes as identity; rename inference from equal content; `copyFrom` overwrite; progressive mutation before conflict discovery; deleting parents before children; creating children before parents.

Ordering: deletes deepest-first and folder creates shallowest-first. No rename inference. Conflict atomicity means complete preflight before mutation, not crash-safe filesystem transactions.

Independent branches include file/folder type transitions, empty versus absent files, defensive bytes, selector scoping, stable ordering, stale add/modify/delete conflicts, unrelated-path preservation, and fresh-manager persistence. Step 3 is a distinct publication operation consuming the prior artifacts. No single-turn fallback.

Evidence: `/root/scout_commons_vfs_retry` handoff.

Rating: P1 4, P2 3, P3 3, P4 3, P5 4, P6 4, P7 3 = **24/28 MEASURE**.

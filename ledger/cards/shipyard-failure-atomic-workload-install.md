# shipyard-failure-atomic-workload-install

- Date/machine: 2026-10-17 / devvm23237
- Repo/base: `leudz/shipyard` @ `be1aa7f8211a17ba3faac90c065ac462e1b23310`
- Seam: `Workload::add_to_world` scheduler publication and tracking activation
- Trap: commit before validation, then partial side effects across heterogeneous storage borrows
- Routing: `MEASURE`, two chained steps
- A4: `CLEAR`; no Shipyard or cross-repo peer covers failed workload-install rollback

## User problem and base proof

My application installs workloads dynamically while other code may temporarily hold storage borrows. If installation fails, I need the world to stay exactly as it was so I can release the borrow and retry the same workload. Today a failed install can leave behind a workload that cannot run, can become the default, and can enable tracking for only some of its component storages.

Two focused public-API tests reproduce this at the exact base:

- With `AllStoragesViewMut` held, `add_to_world` returns `TrackingAllStoragesBorrow`, but `contains_workload` is already true, the leaked workload/default resolves to a batch whose tracking is disabled, and a same-label retry returns `AlreadyExists`.
- With `USIZE` held exclusively, a workload requesting insertion tracking for `U32` and `USIZE` returns `TrackingStorageBorrow`; tracking is already enabled for `U32` but remains disabled for `USIZE`, and the label again blocks a clean retry.

Evidence: `/tmp/shipyard-install.roIzYF/base-repro-report.md` and scratch tests in `tests/workload/mod.rs:36-104`. The focused public-API reproductions pass. The root library suite passes 66/66 offline when the unrelated stale demo workspace members are temporarily excluded from dependency resolution.

## Step shape

1. The existing `Workload::add_to_world(self, world: &World) -> Result<(), AddWorkload>` becomes failure-atomic for scheduler publication. Any error leaves the workload label, default selection, public workload info, and same-label retry behaving as they did before the call.
2. The same call extends that guarantee across all requested tracking changes. A failure on a later component storage does not leave tracking enabled on an earlier one, and releasing the borrow permits a clean retry that installs the complete workload once.

No new public entry point is required.

## Dependency and fork

Step 2 consumes Step 1's staged or reversible installation state: the final grader checks both scheduler state and per-storage tracking state before retrying the same label. Deleting Step 1 makes retry fail even if partial tracking is repaired.

The final step has independent observable failure paths:

- scheduler batches/default/label can leak before tracking begins;
- one tracking callback can mutate an available storage before a later callback fails;
- deduplicated system state or an occupied label can make the retry differ from a fresh install.

At least two implementation families remain possible: preflight/stage every fallible operation before publication, or journal scheduler and tracking mutations and roll them back on error. Tests use only `contains_workload`, run behavior, tracking-aware public views, and retry results.

## Repo gates

- License: exact dual MIT/Apache-2.0 texts.
- Size: 27,853 non-test Rust LOC under `src`.
- Activity: selected base is current repository HEAD on 2026-10-17.
- A1: no `CLAUDE.md`, `AGENTS.md`, `.claude/`, agent branch, or AI-attribution hit found.
- Testability: focused cases and the isolated root library suite run deterministically offline.

## A4 and public disclosure

Local corpus and live Codimango searches for `shipyard`, `leudz`, `add_to_world`, `TrackingAllStoragesBorrow`, `TrackingStorageBorrow`, and failure-atomic workload installation found no same-seam task. Verdict: **CLEAR**.

Upstream issue/PR searches for atomic workload installation, tracking rollback/residue, same-label retry, and both error variants found no remedy. History contains the commit that introduced on-demand tracking, but no later rollback or atomic-install direction. The exact failure ordering remains present at base: schedule creation/publication occurs before borrowing `AllStorages`, tracking callbacks run sequentially with early return, and workload info is published only after them.

## Probe gate and risks

No task scaffold or build exists. Muse must author the user-voice two-step contract, Codex must create a scratch grader, and five cold Avocado implementations must be measured before Lane B. Step 1 may consume the one saturation exemption; Step 2 must land at 1–3/5.

Primary risk: a single transaction wrapper could solve both steps and saturate the final probe. The grader must therefore keep the two independently reproduced mutation domains and clean-retry behavior without prescribing rollback mechanics. If Step 2 is 4–5/5 after one fair trap-focused amend, release the card rather than padding it with edge cases.

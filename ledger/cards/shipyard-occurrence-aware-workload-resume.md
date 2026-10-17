# shipyard-occurrence-aware-workload-resume

- Date/machine: 2026-10-17 / devvm23237
- Repo/base: `leudz/shipyard` @ `be1aa7f8211a17ba3faac90c065ac462e1b23310`
- Seam: sequential workload construction and failed-workload execution state
- Trap: identity conflation, then failure-path quality and replay after partial commit
- Routing: `MEASURE`, three chained steps
- A4: `CLEAR`; no Shipyard or cross-repo peer covers occurrence-level failed-workload progress and resume

## User problem and base proof

My workloads can contain the same system more than once. If a later system fails after earlier work has already committed, I need to repair the cause and continue without repeating that earlier work. Today the sequential builder rejects repeated systems, and a run failure tells me only which system label failed—not which occurrence finished or what remains.

At the exact base, the focused reproduction constructs `(repeated, repeated).into_sequential_workload()` and observes the documented `appears twice` panic. A second run executes `first`, then a fallible middle system, and stops before `suffix`; the public `RunWorkload` value contains only the middle system label and custom error. It exposes no occurrence position, completed prefix, pending suffix, or resumable artifact.

Evidence: `/tmp/shipyard-lanei.9hLs7K/base-repro-report.md` and scratch test `tests/sequential_repeated_system.rs`. The focused tests pass as expected (two reproductions), and `cargo test --lib --offline` remains 66/66.

## Step shape

1. The existing `IntoWorkload::into_sequential_workload(self) -> Workload` accepts repeated system occurrences and preserves their multiplicity and order.
2. Failed execution exposes a public occurrence-level progress artifact from the existing scheduled-workload run path, so a caller can distinguish completed, failed, skipped, and not-yet-run occurrences. Existing ordinary run callers keep working.
3. A scheduled workload can resume from that artifact after the caller repairs the cause. Already completed work is not repeated, remaining work runs once, and an artifact from a different schedule is rejected before anything executes.

The exact public progress and resume signatures must be pinned before the probe; the card deliberately does not prescribe their internal representation.

## Dependency and fork

Step 2 consumes the per-occurrence identity established by Step 1; a type label cannot distinguish two uses of the same system. Step 3 consumes the failure artifact created by Step 2. Removing either earlier step breaks the final behavior rather than merely reducing coverage.

The final step has independent observable failure paths:

- sequential repetition can resume from the wrong identical occurrence;
- parallel execution can repeat a peer that already completed or skip one that had not;
- a stale or foreign artifact can be accepted and mutate a different schedule.

At least two implementation families remain possible: an immutable schedule-bound progress value interpreted by the workload, or an owned continuation object retaining the failed run's state. Tests can use public counters and logs and need not inspect representation or timing.

## Repo gates

- License: exact dual MIT/Apache-2.0 texts.
- Size: 27,853 non-test Rust LOC under `src`.
- Activity: selected base is current repository HEAD on 2026-10-17.
- A1: no `CLAUDE.md`, `AGENTS.md`, `.claude/`, agent branch, or AI-attribution hit found.
- Testability: `cargo test --lib --offline` passes 66 tests in 0.11s warm (17.15s cold).
- Issue density: eight open issues, with no AI-authored issue content found.

## A4 and public disclosure

Corpus searches for `shipyard`, `leudz`, `into_sequential_workload`, `ScheduledWorkload`, `WorkloadProgress`, and `resume_with_world` found no same-seam task. Live Codimango code search found only dependency-graph references to the crate, not a task. Verdict: **CLEAR**.

Upstream commit `c4cc313` and the current docs explicitly disclose the repeated-system limitation, so this is not presented as a hidden existing bug. They add a panic and say current `before`/`after` expressivity cannot handle the case; they do not propose occurrence identity, failure progress, or resume. Searches across issues, PRs, comments, branches, and history for sequential-workload duplicates, resume, retry, continuation, progress, and `RunWorkload` found no public remedy. Issue #208 concerns wasm/rayon setup and is unrelated. Public novelty is therefore **ADJACENT but clear of a remedy**.

## Probe gate and risks

No task scaffold or build exists. Before Lane B, Muse must author a brief user-voice contract, Codex must build a scratch grader, and five cold Avocado implementations must be graded with server-style chaining. Required result is 1–3/5 on every non-exempt step; Step 1 may use the single exemption.

Primary risk: Step 3 may be a 0/5 cliff because correct parallel progress semantics are architectural. If that happens, amend along the measured failure boundary; do not weaken hidden requirements or silently turn this into a single-turn task. Secondary risk: adding a new public progress type could make the prompt over-specified, so the probe brief should state the user outcome and exact signatures only.

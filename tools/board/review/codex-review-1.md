# A. Verdict

**REVISE.** The action-first product idea is strong, but the current design is not safe enough to act as a cross-server ownership authority or a never-wrong view of Codimango.
Ship a smaller v1 around explicit source authority, visible freshness, responsive output, local event spooling, and reliable sync; make claims advisory until there is an atomic lease mechanism.
Defer causal productivity rankings, transcript backfill, messaging, and elaborate charts until the operational data is trustworthy and users have validated the core board.

# B. Top 10 changes, ranked by value

## 1. Make source authority and data health first-class

- **Problem — [Software design]:** The design merges Codimango, git, and ledger facts without saying which wins. “Pulls before reading” is not enough: a failed pull, failed Codimango call, partial result, stale cache, `totalExact=false`, or `trainingStatusDegraded=true` can yield a plausible but wrong board. The live response is an object containing `tasks`, `totalExact`, `trainingStatusAsOf`, and `trainingStatusDegraded`, and task records distinguish `commitSha`, `headCommitSha`, and `validationCommitSha`; these are materially different facts.
- **Concrete proposal:** Define an authority matrix: Codimango owns lifecycle/status/validation/review timestamps and imported commit; git owns repository head and task-local last-touch commit; the ledger owns human coordination only. Every rendering carries `observed_at`, source, age, and health. Default `board` may fall back to a last-known-good cache but must print a prominent `DATA STALE`/`SYNC FAILED` banner and mark affected cells unknown; mutating coordination commands fail closed when the ledger is not fresh. Add `board sync --strict` and `board doctor`. Compare all three relevant SHAs and alert on divergence; never infer server state from ledger events.
- **Effort:** M

## 2. Do not present Git-backed claims as a lock

- **Problem — [Software design]:** Per-server JSONL files avoid a merge conflict between servers, but do not provide mutual exclusion. Both servers can pull the same state, append claims, and push successfully to different files. Multiple sessions on one server also append and run git concurrently against the same file/repository. A pre-tool hook therefore cannot reliably promise to block the second worker.
- **Concrete proposal:** In v1 call these **advisory claims**: immediately show a loud conflict after reconciliation, but do not claim exclusive enforcement. Serialize local appends with `flock`, spool locally, and make one sync worker perform git operations with retry/rebase and bounded backoff. If hard exclusion is required, add a separate atomic compare-and-swap lease service (or a deliberately designed dedicated Git ref with tested CAS semantics) before enabling hook blocking. Never use wall-clock “latest claim wins” to resolve a collision.
- **Effort:** L for true locking; M for honest advisory claims

## 3. Isolate hooks from sessions and from network/git latency

- **Problem — [Software design]:** Registering on every tool call and committing/pushing synchronously is noisy, slow, race-prone, and makes Claude reliability depend on DNS, auth, GitHub, and repo state. A malformed transcript, full disk, lock contention, or push failure must not break a session. The current design does not distinguish an intentional ownership-policy block from an internal hook failure.
- **Concrete proposal:** Hooks do only a bounded local append to a spool: no network, no pull, no commit, no push, no transcript scan on every call. Use `O_APPEND` plus `flock`, a size limit, atomic rename for checkpoints, a 100 ms budget, no stdout, bounded diagnostic stderr, and always exit 0 on internal error. Batch heartbeats (for example, at most once per task per 10 minutes). A separate `board sync`/timer flushes. A policy block is a distinct, explicit outcome and is allowed only when the lease source is healthy; on detector failure, allow the session and emit a visible warning event.
- **Effort:** M

## 4. Version and harden the event schema before collecting history

- **Problem — [Software design]:** `{ts, server, session_id, session_name, model, task, type, commit, data}` lacks idempotency, ordering, schema evolution, actor identity, source provenance, entity type, clock diagnostics, and correction semantics. Renaming a tab “everywhere” conflicts with an append-only historical record. Cross-host timestamps cannot safely order events.
- **Concrete proposal:** Add `schema_version`, UUID `event_id`, per-writer monotonic `seq`, `occurred_at`, `recorded_at`, `actor_id`, stable `host_id`, `session_id`, `entity_kind`, `entity_id`, `source`, and typed payloads. Treat session titles as alias events and render the latest alias without rewriting history. Deduplicate by `event_id`; order within a writer by `seq`, and represent cross-writer concurrency rather than inventing an order. Add explicit `supersedes_event_id`/`correction` events. Cap line size and quarantine malformed/truncated lines with an alert rather than ignoring them.
- **Effort:** M

## 5. Replace the single maximal table with responsive, action-first views

- **Problem — [Terminal UI/UX]:** The proposed table has roughly ten dense columns; it cannot remain readable at 80 columns, and the most important answer—“what do I do next?”—is at the far right. Symbols such as `✓✓`, `○`, `⟲`, and confidence bars require a legend and do not survive every font, pipe, or accessibility setting.
- **Concrete proposal:** Put `NEXT` immediately after `TASK`. Use explicit width profiles: 80 columns = task, next action, state/age, owner; 120 = add validation, review, sync/commit; 200 = add rounds, pushes, presubmit, source. Truncate the middle of task names and never truncate `NEXT` or warning labels. Group by `ATTENTION`, `READY`, `WAITING`, and collapsed `DONE`, then sort by severity and age inside a group. Add `--columns`, `--wide`, `--plain`, `--color auto|always|never`, `--unicode auto|always|never`; respect `NO_COLOR`, `TERM=dumb`, and non-TTY output.
- **Effort:** M

## 6. Make live Codimango reads bounded, cached, and testable

- **Problem — [Software design]:** The live list payload is multi-megabyte because task objects can contain nested metadata and report prose. Calling it repeatedly for the table, stats, and hooks will be slow. `track_tasks.py` does not check the subprocess return code before parsing/snapshotting, while `presubmit.py` reaches through a hardcoded private Python client path; neither failure mode should be copied.
- **Concrete proposal:** Have exactly one adapter invoke `codimango task list --json` with an explicit argument vector, timeout, checked exit status, captured stderr, and fixture-tested envelope parsing. Cache the raw last-known-good response atomically with fetch metadata, then normalize only needed fields. Fetch per-task reviews/details lazily for `show` and reports. Never import Codimango internals or tokens. Make cache TTL and maximum stale age configurable; use exponential backoff only for background reads, never conceal a foreground failure.
- **Effort:** M

## 7. Keep presubmit read-only; integrate through an adapter

- **Problem — [Software design]:** The design says `presubmit.py` writes the event itself, but the current script explicitly documents “READ-ONLY” and “writes nothing anywhere.” Ledger I/O inside a gate also risks changing its exit behavior or hanging it.
- **Concrete proposal:** Do not modify the gate to write board state. Add `board check run <task>` as a wrapper that invokes presubmit, preserves stdout/stderr and exit code, records the observed commit plus PASS/WARN/FAIL counts only after completion, and treats event-recording failure as a warning. Longer term, add a stable machine-readable output option to presubmit and consume it; until then, keep parsing in one versioned adapter with golden fixtures.
- **Effort:** S

## 8. Replace productivity rankings with operational management metrics

- **Problem — [Engineering manager/director]:** “Who builds better” and outcome-by-model imply causality that tool-call attribution cannot support, encourage gaming, and distract from flow. Funnel inputs and root-cause buckets are partly best-effort, yet the proposed charts do not disclose coverage. The current `--export md` is merely “same charts,” not an upward-ready report.
- **Concrete proposal:** Make the headline: delivered this week, submitted, WIP by stage, ready now, blocked/stale, median/p75 cycle time, reviewer wait, revision rate, and data freshness/coverage. Compare with a rolling four-week baseline, not just one prior week. Attribute ownership for workload balancing but do not rank people/models. Report denominators and exact/estimated provenance. Add one-command weekly and task reports as specified in section F.
- **Effort:** M

## 9. Add portable configuration and stable extension boundaries now

- **Problem — [Open-source architect]:** the author, server names, home paths, repo URLs, FBIDs/opaque importer IDs, lane names, reviewer names, internal URLs, and private client paths are currently embedded in the design or existing integrations. Adding config after implementation will bake these assumptions into storage and UI.
- **Concrete proposal:** Use TOML because Python 3.11+ reads it with stdlib `tomllib`. Separate a local, uncommitted user config from a shareable team config. Normalize external records into public internal types, and let trusted plugins contribute data sources, columns, checks, and stats without becoming authorities implicitly. Provide `board init`, schema validation, config versioning, and a no-network sample profile. Keep internal adapters/plugins in a separate package or config overlay.
- **Effort:** M

## 10. Cut the speculative surface and test the failure modes first

- **Problem — [All hats]:** Transcript/Muse/Codex backfill, root-cause NLP, inter-session messaging, model contribution analytics, sparklines, mutable tab-title attribution, and automatic all-history import are several products. They delay the board and create privacy, correctness, and maintenance risk.
- **Concrete proposal:** V1: normalized events, advisory ownership, action-oriented list/show/claim/release, reviews bound to a commit, explicit sync health, cache, responsive/plain output, config, and weekly/task Markdown reports. V1.1: notes and manual root-cause tags. V2 only after evidence: historical transcript attribution, plugin ecosystem, advanced charts, and atomic leases. Test corrupt JSONL, duplicate/out-of-order events, two local writers, two-server claim races, clock skew, stale cache, schema drift, failed pull/push/API, 80/120/200 widths, ASCII/no-color/piped modes, and hook latency/fail-open behavior.
- **Effort:** S to cut scope; M for the test matrix

# C. Per-hat findings

## Terminal UI/UX expert

- **[Terminal UI/UX]** Optimize the default for the decision, not the database: `TASK  NEXT  STATE/AGE  OWNER` should fit at 80 columns. Details belong in `show` or `--wide`.
- **[Terminal UI/UX]** Put a persistent one-line data-health banner above the table. A stale value rendered dimly is too easy to miss; use words such as `SYNC FAILED — showing cache from 43m ago`.
- **[Terminal UI/UX]** Use color only as redundant emphasis. Red/green alone fails common color-vision deficiencies, dim gray has poor contrast on light themes, and “yellow” varies across terminals. Always print a word/symbol and offer `--theme dark|light|auto` only for enhanced palettes.
- **[Terminal UI/UX]** `✓✓` looks like decoration rather than “two distinct reviewers on this exact commit”; `○` can mean empty, pending, or failed; `⟲` can mean retry rather than stale; `▮▮▮▯▯` wastes width. Prefer `R0`, `R1`, `R2`, `R~` and `C4/5`, with Unicode as optional decoration.
- **[Terminal UI/UX]** Print the legend automatically only when symbols appear, keep it to two lines, and expose the same text with `board legend`/`--legend`. Do not make users remember semantics from a design doc.
- **[Terminal UI/UX]** Piped output should be deterministic: no ANSI, no animation, no width-dependent rearrangement, stable columns, ISO timestamps, and a nonzero exit in `--strict` mode when data health is bad.
- **[Terminal UI/UX]** Grouping beats a single “urgency” sort. Show conflicts/failures/stale source first, then actionable work, then waiting work. Hide accepted/archived by default with a count such as `Done: 38 (use --all)`.
- **[Terminal UI/UX]** “Time in state” thresholds must depend on state: two days building may be normal while two days awaiting a second look may be stale. Make thresholds configurable per state.

## Software design expert

- **[Software design]** Use a projection architecture: immutable observations/events in, normalized task state plus health findings out. The renderer must never query sources directly.
- **[Software design]** State precedence explicitly and preserve disagreements as findings. Do not overwrite one source with another during normalization.
- **[Software design]** A 24-hour heartbeat lease is too coarse for collision prevention and too dependent on clock correctness. Store clock-offset diagnostics and use server-observed receipt time or an atomic lease service for expiry.
- **[Software design]** “Accepted or archived makes it free” is semantically odd: completed work should be `DONE`, not `FREE`, or it will appear available to take.
- **[Software design]** Reviews must include verdict and exact full commit SHA. Confidence alone is not approval, and “latest review” should not erase earlier dissent. Define whether two reviews from two sessions owned by the same human count independently; probably they should not.
- **[Software design]** Detect `commitSha != validationCommitSha`, `headCommitSha != commitSha`, git task-head != server commit, a commit by a non-owner, incomplete list results, degraded training status, and future/implausible event timestamps. Each needs a named severity and next action.
- **[Software design]** Avoid shell-text recognition of `git push`, `codex exec`, and `muse exec` as the correctness boundary. Commands may be aliased/compound and a pre-hook cannot know success. Use post-tool observations plus git-state comparison; treat build-action attribution as telemetry, not truth.
- **[Software design]** Cache one Codimango list result per run and across runs for a short TTL. Do not put live Codimango calls in hooks. Cache writes require temp-file + `os.replace`, checksum/schema validation, and last-known-good retention.
- **[Software design]** Git sync must be explicit state with `last_pull_ok`, `last_push_ok`, pending event count, remote commit, and error. “Push after writing” cannot be fire-and-forget.
- **[Software design]** Supply fake-clock, fake-runner, fake-filesystem/temporary-repo seams; golden live-response fixtures should include wrapper changes, null fields, huge nested prose, incomplete totals, and server errors.

## Engineering manager / director

- **[Engineering manager/director]** The board answers “what should I do next?” better than “how is the workstream going.” Add a six-line executive summary: delivered, in review, ready, blocked, aging, and data confidence.
- **[Engineering manager/director]** Show flow efficiency: WIP by stage, arrivals vs completions, median/p75 cycle time, and aging work. A cumulative accepted line alone can rise while the pipeline deteriorates.
- **[Engineering manager/director]** Separate output (`accepted`) from activity (`worked on`, pushes). Define submitted and accepted precisely from authoritative lifecycle transitions; do not count `usedInTraining` as accepted unless the product contract says they are equivalent.
- **[Engineering manager/director]** Revision rate needs cohorting by first-submission week; acceptance-date cohorting creates survivor bias. Display both submission cohort outcomes and calendar-week deliveries.
- **[Engineering manager/director]** Report blocked reasons and the specific decision/owner needed. Managers need “three tasks need reviewer assignment” more than model action share.
- **[Engineering manager/director]** Include data coverage: for example, `cycle time 18/21 tasks exact; 3 estimated`. Best-effort backfills must never look exact.
- **[Engineering manager/director]** A people/model league table should be removed. If retained experimentally, label it non-causal and private, require minimum sample sizes, and never use it as a quality score.
- **[Engineering manager/director]** Export should be an authored report with headlines, changes, risks, asks, next-week plan, and definitions—not a terminal dump in Markdown.

## Architect for later open-sourcing

- **[Open-source architect]** The product name and data model should not assume AAI, SWE-bench, Claude, or Codimango. Keep those as a default profile and plugins; the core concepts are item, observation, claim, check, review, state, and report.
- **[Open-source architect]** Separate private values: `the author`, `<user>`, `host-a`, `host-b`, `~/...`, private repo URLs, opaque user/FBID fields, lane/reviewer names, internal URLs, and the presubmit private-client path. Do not commit a generated personal config.
- **[Open-source architect]** Give each normalized field an authority and namespace. A plugin may publish `codimango.validation_status`; it must not silently replace `core.state`.
- **[Open-source architect]** Plugins execute arbitrary Python, so load only explicitly enabled modules and describe them as trusted code. A future third-party ecosystem should prefer a subprocess JSON protocol for isolation.
- **[Open-source architect]** First run should detect capabilities, then ask: identity/display name, timezone/week start, servers, task repositories, primary next actions, desired width/columns, aging thresholds, and report audience. Preview the generated config before writing it.
- **[Open-source architect]** Personalized metric suggestions should be evidence-based and optional: inspect local history, state sample size and coverage, recommend metrics with reasons, and avoid ranking suggestions when the sample is small. Example: “Reviewer wait is 41% of measured cycle time across 12 tasks; add `review_wait_p50`.”
- **[Open-source architect]** Include config migrations and plugin API versions from day one. Unknown keys should be warnings; incompatible plugin API versions should be hard errors isolated to that plugin.

## Naming

- **[Naming]** `board` is easy to type but generic and overlaps conceptually with the existing `codimango dashboard`. Keep the binary `aai-board` for the private profile or choose a neutral open-source name such as `workboard`; allow `board` as a shell alias.
- **[Naming]** Prefer `claim` over `take`, `available` over `free`, and `release --reason` over a positional free-text reason. These are clearer in help and scripts.
- **[Naming]** “Approval” overstates what a peer/session review means. Call it a `review` with verdict `ready|changes|comment`, bound to a commit. Display `R2`, not two checkmarks.
- **[Naming]** `seen`, `heartbeat`, and `register` are internal event types, not user concepts. Name the derived concepts `review stale`, `claim expires`, and `session active` in UI text.
- **[Naming]** Replace `msg`/`ack` with `note add`/`note resolve` if this survives scope cutting. “Ack” lacks a target in the current command and is hard to automate.
- **[Naming]** Replace overloaded `--since` with `changes --since <duration|timestamp>`; bare `board --since` has unclear storage, scope, and semantics.

## Missing, additional, and over-scoped

- **[Missing]** `sync`, `doctor`, machine-readable `--json`, stable exit codes, config validation, cache inspection, data/source status, schema migration, event repair/quarantine, and an audit command explaining why a row has its derived state.
- **[Missing]** Manual blocker/reason taxonomy, due/next-review date, task priority, and an “ask” field. These are more useful to management than model attribution.
- **[Missing]** Privacy/retention policy for session titles, prompts/transcripts, notes, paths, and reviewer names; redact secrets and allow retention limits before any backfill.
- **[Missing]** A definition glossary for lifecycle states and metrics, especially `submitted`, `accepted`, `used_in_training`, `revision round`, `first submission`, and archived/retired.
- **[Additional tool worth adding]** `board explain <task>` should list every contributing observation, authority, freshness, and rule behind `NEXT`; this is the fastest way to debug silent disagreement.
- **[Additional tool worth adding]** `board report weekly` and `board report task` are more valuable than terminal sparklines.
- **[Over-scoped—defer]** Transcript/session backfill, cross-tool action attribution, “who builds better,” model outcome attribution, inferred root-cause NLP, chat-like messaging, automatic tab-title renaming, and funnel reconstruction from heterogeneous prose.

# D. Proposed revised command list, columns, and legend

## Commands

```text
workboard [list] [--mine] [--group attention|state|owner] [--all]
workboard show <task> [--history] [--sources]
workboard explain <task>
workboard available [--reason never-claimed|expired|released]
workboard claim <task> [--to <actor>] [--reason <text>]
workboard release <task> --reason <text>
workboard review add <task> --verdict ready|changes|comment [--confidence 1..5] --note <text>
workboard review list <task>
workboard note add <task> <text>          # defer from v1 if schedule is tight
workboard note resolve <note-id>          # defer from v1 if schedule is tight
workboard changes --since <2h|2026-10-20T09:00:00Z>
workboard sync [--strict] [--offline]
workboard status                          # source/cache/queue health
workboard doctor                          # config, clocks, git, CLI, hooks
workboard report weekly [--week 2026-W43] [--output report.md]
workboard report task <task> [--output task.md]
workboard stats [--from DATE] [--to DATE] [--json]
workboard config init|show|validate
workboard plugins list|doctor
```

All read commands support `--json`, `--plain`, `--color auto|always|never`, and `--unicode auto|always|never`. `workboard` remains the fast alias for `workboard list`.

## Responsive columns

| Width/mode | Columns, in order |
|---|---|
| 80-column TTY | `TASK`, `NEXT`, `STATE/AGE`, `OWNER` |
| 120-column TTY | above + `VALID`, `REVIEW`, `COMMIT/SYNC` |
| 200-column or `--wide` | above + `ROUND`, `PUSHES`, `PRESUBMIT`, `SOURCE` |
| pipe/`--plain` | stable configured columns; tab-separated or JSON, no ANSI/glyph dependence |

Recommended compact cells:

- `NEXT`: `FIX validation`, `SUBMIT`, `GET R2`, `WAIT server`, `CLAIM`, `RESOLVE CONFLICT`.
- `STATE/AGE`: `BUILD 6h`, `REVIEW 2d`, `BLOCK 4d`, `DONE 1d`.
- `VALID`: `PASS`, `RUN`, `FAIL`, `UNK`, optionally `@a1b2c3d4` in wide mode.
- `REVIEW`: `R0`, `R1 C4`, `R2`, `R~` (one or more reviews are for an older commit).
- `COMMIT/SYNC`: `OK`, `HEAD≠SERVER`, `VALID≠SERVER`, `CACHE 43m`, `SYNC!`.
- `PRESUBMIT`: `P12/W2/F0`, `STALE`, or `NONE`; never encode the outcome only in color.

## Exact legend text as printed

TTY/Unicode mode:

```text
Legend: ✓ PASS   … RUNNING/WAIT   ! BLOCKED/FAIL   ? UNKNOWN   ↻ STALE DATA   ⚔ CONFLICT
        R0 no review   R1 one reviewer   R2 two reviewers   R~ review on older commit   C4 confidence 4/5
Color repeats status only: green PASS, amber WAIT, red BLOCKED, blue INFO; words/symbols remain authoritative.
```

ASCII or piped mode:

```text
Legend: PASS=passing  WAIT=running/waiting  BLOCK=blocked/failed  UNK=unknown  STALE=old data  CONFLICT=owners disagree
        R0=no review  R1=one reviewer  R2=two reviewers  R~=older commit  C4=confidence 4/5
```

# E. Proposed config schema and plugin interface

TOML is preferable to YAML under the stdlib-only constraint. Keep personal config at `~/.config/workboard/config.toml` and allow a checked-in team config with no identities or private paths.

```toml
config_version = 1
profile = "swebench-codimango"

[user]
id = "vidit"                    # stable local ID, not an FBID
display_name = "the author"
timezone = "America/Los_Angeles"
week_start = "monday"

[ui]
color = "auto"                  # auto | always | never
unicode = "auto"                # auto | always | never
theme = "auto"                  # auto | dark | light
default_group = "attention"
columns_80 = ["task", "next", "state_age", "owner"]
columns_120 = ["task", "next", "state_age", "owner", "validation", "review", "sync"]
columns_wide = ["task", "next", "state_age", "owner", "validation", "review", "sync", "round", "pushes", "presubmit", "source"]

[codimango]
command = "/usr/local/bin/codimango"
list_filter = "mine"
timeout_seconds = 30
cache_ttl_seconds = 120
max_stale_seconds = 900

[[servers]]
id = "build-a"
display_name = "Build A"
host_alias = "host-a"
event_file = "ledger/events/build-a.jsonl"

[[servers]]
id = "build-b"
display_name = "Build B"
host_alias = "host-b"
event_file = "ledger/events/build-b.jsonl"

[[repositories]]
id = "tasks"
path = "~/<task-repo>"
remote = "origin"
branch = "main"
task_path_pattern = "{task}"

[[team.members]]
id = "vidit"
display_name = "the author"
aliases = ["<user>"]

[claims]
mode = "advisory"               # advisory | atomic-plugin
expire_after_hours = 24
heartbeat_interval_minutes = 10
clock_skew_warn_seconds = 120

[thresholds]
build_warn_hours = 48
build_block_hours = 120
review_wait_warn_hours = 24
sync_warn_minutes = 5
sync_fail_minutes = 15

[reports]
weekly_metrics = ["accepted", "submitted", "wip", "blocked", "cycle_p50", "cycle_p75", "review_wait_p50", "revision_rate"]
include_people_ranking = false
show_data_coverage = true

[plugins]
api_version = 1
enabled = [
  "workboard_codimango.plugin",
  "workboard_presubmit.plugin",
]
trusted_paths = []
```

First-run flow:

1. `workboard config init` detects TTY capability, Codimango availability, hostname, likely task repos, and history sample size without writing.
2. It asks no more than one screen of questions: identity/display name, timezone, servers/repos, preferred next actions, compact/wide columns, aging thresholds, and report audience.
3. It previews the TOML and the commands it will use, then writes only after confirmation; `--non-interactive` accepts flags for automation.
4. If history is sufficient, it prints optional metric suggestions with evidence and coverage. It never silently enables a metric or uploads telemetry.

Plugin interface sketch (trusted in-process v1):

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping, Protocol, Sequence

PLUGIN_API_VERSION = 1

@dataclass(frozen=True)
class Observation:
    source: str
    entity_id: str
    observed_at: datetime
    fields: Mapping[str, object]       # namespaced, e.g. codimango.validation_status
    authority: Mapping[str, str]       # field -> authoritative|advisory|derived

@dataclass(frozen=True)
class SourceHealth:
    source: str
    ok: bool
    observed_at: datetime | None
    stale_after_seconds: int
    detail: str

@dataclass(frozen=True)
class FetchResult:
    observations: Sequence[Observation]
    health: SourceHealth
    cursor: str | None = None

@dataclass(frozen=True)
class Finding:
    code: str
    severity: str                    # info|warn|block
    summary: str
    next_action: str | None = None

@dataclass(frozen=True)
class Cell:
    text: str                         # semantic text; renderer adds style
    sort_key: object
    full_text: str | None = None

class DataSource(Protocol):
    name: str
    def fetch(self, *, since: str | None, timeout_seconds: float) -> FetchResult: ...

class ColumnPlugin(Protocol):
    name: str
    def render(self, task: "TaskView", *, width: int) -> Cell: ...

class CheckPlugin(Protocol):
    name: str
    def evaluate(self, task: "TaskView", context: "CheckContext") -> Sequence[Finding]: ...

class StatPlugin(Protocol):
    name: str
    def compute(self, tasks: Iterable["TaskView"], window: "TimeWindow") -> "StatResult": ...

def register(registry: "Registry") -> None:
    """Validate API version, then register sources, columns, checks, and stats."""
```

The core performs precedence resolution, cache policy, styling, redaction, and rendering. Plugins return semantic values and health; they do not print ANSI, write the event log, or silently claim authority. A later untrusted-plugin API should use newline-delimited JSON over subprocess stdin/stdout.

# F. Export/report design

One-command reports:

```text
workboard report weekly --week current --output weekly-2026-W43.md
workboard report task bigtree-node-setter-atomic-fidelity --output bigtree-one-pager.md
```

The weekly report should be deterministic, diff-friendly, and useful without the terminal tool. It contains definitions and source freshness at the bottom. Example:

```markdown
# SWE-bench workstream — 2026-W43 through Thu 13:00 PT

**Headline:** 4 accepted / 6 submitted; 3 ready now; 2 blocked; delivery is +1 vs the 4-week pace.
**Data confidence:** Codimango fresh at 12:58 PT (complete); ledger fresh at 12:59 PT; cycle time exact for 18/21 tasks.

## Decisions and asks
- Assign a second reviewer to `task-a` (ready 19h).
- Resolve the owner conflict on `task-b` before further pushes.

## Flow
| Metric | This week | 4-week median | Note |
|---|---:|---:|---|
| Accepted | 4 | 3 | 3 MT / 1 ST |
| Submitted | 6 | 5 | 2 still in review |
| WIP | 11 | 9 | 2 over configured age |
| Cycle time p50 / p75 | 3.2d / 5.8d | 3.5d / 5.1d | acceptance cohorts |
| Reviewer wait p50 | 21h | 17h | 18/21 exact |

## Movement since last report
- Accepted: `task-c`, `task-d`.
- Entered review: `task-e`, `task-f`.
- Returned for revision: `task-g` — grader integrity.

## Risks
- `task-b` — BLOCK: two advisory claims; owner decision needed.
- `task-h` — STALE: validation is for `91ab…`, server task is `fe02…`.

## Next week
- Submit the three ready tasks after R2.
- Reduce reviewer wait below 18h; no new work while blocked WIP exceeds two.

_Definitions: accepted = authoritative Codimango transition to accepted. Cycle time = first submission to acceptance._
_Generated by workboard 0.1; source snapshot IDs: codimango/…, ledger/…._
```

The per-task one-pager should contain: one-line status/next action, owner and advisory-claim health, authoritative lifecycle and exact SHAs, validation/presubmit/review checks with freshness, blockers/asks, a short event timeline, links, and a source/provenance footer. It must visibly distinguish facts, derived conclusions, and human notes.

# G. Open questions for the author

1. Is cross-server ownership meant to be a safety lock or only coordination advice? If it is a lock, are you willing to add an atomic service/ref rather than rely on merged Git events?
2. When Codimango is unavailable or incomplete, should default `board` show a prominently stale cache and exit 0, or fail nonzero unless `--offline` is explicit?
3. What exactly counts as two independent reviewers: distinct sessions, distinct models, or distinct human identities? Can two sessions owned by the same person produce `R2`?
4. Which three decisions must the weekly report enable for its actual upward audience, and are individual/model comparisons explicitly wanted by that audience?
5. Is storing session titles, notes, transcript-derived attribution, and reviewer names in a Git repository acceptable under the intended privacy and retention policy?

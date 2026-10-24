# workboard — design v2

Status: SIGNED-OFF v2.2 (Codex rounds 1–3) · 2026-10-23 · after Codex reviews 1–2 (review/)
Binary `workboard`, alias `board`. Core is generic (items, observations, claims, checks, reviews, reports);
codimango / SWE-bench / Claude specifics live in a profile + plugins so it can be published later.

## 1. Goal

One terminal command that answers, for one person working across several machines and agent sessions:
1. **What do I do next?** (action-first list)
2. **Who is working on what, and what is free?** (claims, available work)
3. **Is anything out of sync with the server?** (never silently wrong)
4. **How is the workstream going?** (stats + one-command reports for a manager)

Everything that can be recorded automatically is. The only explicit agent action is posting a review.

## 2. Authority (who is right about what)

| Fact | Authority | Never inferred from |
|---|---|---|
| status, validation, review decisions, reviewedAt/enteredPoolAt, server commit (`commitSha`, `headCommitSha`, `validationCommitSha`) | codimango | ledger |
| repo head and last commit touching a task dir | git | ledger |
| claims, reviews by sessions, notes, check runs | ledger | — |

Normalisation keeps disagreements as **findings** instead of overwriting. Findings have a code, severity
(info / warn / block) and a next action. Built-in drift findings: `HEAD≠SERVER` (git task head vs
codimango commit), `VALID≠SERVER` (validationCommitSha vs commitSha), `INCOMPLETE` (`totalExact=false`),
`DEGRADED` (`trainingStatusDegraded`), `STALE_VALID` (server saw the task's newest commit but validated an older one
and non-doc files changed since), `NONOWNER_EDIT` (another session's edit-tool touch while a claim is live), `CLOCK_SKEW`, `MALFORMED_EVENTS`, `SYNC_FAILED`,
`CACHE_STALE`.

## 3. Data health is always visible

Every render starts with a one-line health banner, e.g.
`codimango ✓ 1m · ledger ✓ 0m (host-a ✓ host-b ✓ 4m) · hooks ✓` or
`SYNC FAILED — codimango shown from cache 43m ago (timeout)`.
Default `workboard` shows last-known-good cache with the banner and exits 0; `--strict` exits non-zero on
any health problem (for scripts). Claim/release/review commands fail closed when the ledger can't sync.

## 4. Ledger

- **Location: a private repo** (not the public playbook). Path configurable.
- Events: `events/<host_id>.jsonl`, one writer per file; hooks append to a **local spool** only.
- Event schema v1: `schema_version, event_id (uuid), host_id, seq (per-writer monotonic), occurred_at,
  recorded_at, actor {session_id, alias, kind: claude|codex|muse|human}, entity {kind, id},
  type, commit (full sha), source, payload`. Dedupe by event_id; order within writer by seq; cross-writer
  concurrency is shown, not invented. Corrections via `supersedes_event_id`. Max line size; malformed lines
  quarantined + `MALFORMED_EVENTS` finding.
- Session names are **alias events** (`<host tag>·<tab title>` from `customTitle`/`aiTitle`); the latest
  alias is rendered, history is not rewritten.
- **Spool contract:** every producer (hooks, CLI) appends one line under `O_APPEND` + `flock`, with line and
  queue size limits. One per-host sync lock (single worker) assigns `seq`, moves spool lines into the own
  event file, commits and pushes; spool lines are acknowledged (checkpoint + atomic rename) only after the
  push succeeds. Retries may duplicate events, never lose them; `event_id` dedupes.
- `workboard sync` (also run, time-bounded, by foreground commands, and by a 5-min timer) does the above with
  retry/backoff; sync state (last pull/push ok, pending count, error) is stored and shown in the banner.

### Codimango adapter contract
One argv-based `codimango task list --json` call per refresh, timeout, checked exit status, captured stderr,
envelope/schema validation (`tasks`, `totalExact`, `trainingStatusDegraded`), atomic last-known-good cache
replacement (temp file + `os.replace`), prior good cache kept on any failure. Per-task reviews fetched lazily
for `show`/reports. Renderers and hooks never call codimango directly.

## 5. Claims (ownership): atomic online acquisition, best-effort cached enforcement

Not an authorisation boundary; it stops cooperating sessions from racing, not a deliberate force-push.
- **Ref:** `refs/claims/<sha256(entity_id)[:16]>` (hashed: no invalid characters, no `a` vs `a/b` collision).
  The claim commit stores `{entity_id, claim_id (uuid), nonce, owner alias, host, session, acquired_at}`.
  `doctor` probes create/read/renew/delete on the exact repo; if `refs/claims/*` is hidden or rejected, fall
  back to `refs/heads/workboard-claims/<hash>` and verify rulesets. Claims are disabled until the probe passes.
- **Acquire:** non-forced push creating the ref from zero. Only the push result counts (never `ls-remote`
  beforehand). On an uncertain result (ssh drop), read the exact remote ref: own OID = acquired, other OID =
  lost, absent = retry.
- **Heartbeat:** the owner CAS-updates the ref to a new descendant commit (fresh nonce) with
  `--force-with-lease=<ref>:<observed_oid>`, every 10 min while active. A ledger-only heartbeat is not enough.
- **Expiry and steal:** expired = ref heartbeat older than 24h (configurable). Steal only when claim-source and
  clock health are good AND the same tip has been observed unchanged for ≥ 2 heartbeat intervals (monotonic
  local timer); then push a descendant of that exact tip with the explicit expected OID. A concurrent renew or
  steal loses cleanly.
- **Release:** delete with `--force-with-lease=<ref>:<observed_oid>` (never bare `--force-with-lease`); also
  on DONE. Only live claims keep refs; a configured bound on live claims; exact-ref queries, no namespace scans
  in hooks.
- **Audit:** the ledger records claim/renew/steal/release; reconciliation tolerates the ref changing before
  its ledger event; released claim commits may be GC'd and are never needed for history.
- **Offline:** no exclusive offline acquisition. An offline auto-claim is `PENDING`, never shown as owned,
  and may lose on sync.
- **Healthy claim** (needed for the hook to block) = claim ref refreshed successfully within a short TTL
  (default 2 min, cached locally), valid payload, clock healthy, heartbeat not expired. Otherwise advisory
  and the hook never blocks.
- Accepted/archived items are **DONE**, not available.

## 6. Hooks (automation, fail-open)

Installed per host by `workboard install-hooks` (adds hook entries to `~/.claude/settings.json` only).
- Budget 100 ms, no network, no git, no stdout; internal errors → exit 0 + a warning event.
- PostToolUse on Edit/Write/Bash touching a configured task path: append `touch` (rate-limited to 1 per task
  per 10 min = heartbeat); if the task is unclaimed, enqueue an auto-claim (done by sync).
- PreToolUse on Edit/Write into a task path: **block only if** a healthy, fresh claim ref names a different
  live session. The block message: `owned by host-b·<title> — run: workboard show <task>`.
- SessionStart / title change: alias event.
- Bash that launches `codex exec` / `muse exec` against a task: telemetry event `build_action` (model,
  credited to the launching session). Telemetry, not truth.

## 7. Checks and reviews

- `workboard check run <task>` wraps presubmit.py (unchanged, still read-only): passes through output and
  exit code, then records `{commit, pass, warn, fail}`. Recording failure is a warning.
- Review = `workboard review add <task> --verdict ready|changes|comment --confidence 1-5 --note "…"`,
  bound to the full commit. **R2 = two different sessions with verdict `ready` on the current commit**
  (the author's rule: distinct agent sessions count separately). Dissent stays visible. Reviews on an older
  commit render as `R~`.

## 8. Commands

```text
workboard [list] [--mine] [--group attention|state|owner] [--all]
workboard show <task> [--history] [--sources]
workboard explain <task>                 # every observation + rule behind NEXT and findings
workboard available [--reason never-claimed|expired|released]
workboard claim <task> [--to <alias fragment>] [--steal]
workboard release <task> --reason <text>
workboard review add|list <task> ...
workboard check run <task>
workboard changes [--since 2h|<ts>]      # default: since your last look
workboard sync [--strict] | status | doctor
workboard report weekly [--week current] [--output f.md]
workboard report task <task> [--output f.md]
workboard stats [--from DATE] [--to DATE] [--json]
workboard rank [--refresh] | rank import <file>
workboard config init|show|validate | plugins list|doctor | legend | install-hooks
```
All reads: `--json`, `--plain`, `--color auto|always|never`, `--unicode auto|always|never`; respect
`NO_COLOR`, `TERM=dumb`, non-TTY (no ANSI, stable columns, ISO times).

## 9. Main list

Groups, in order: **ATTENTION** (findings, failures, conflicts) → **READY** (you can act) → **WAITING**
(server/reviewer) → `Done: N (use --all)`. Within a group: severity, then age.

| Width | Columns |
|---|---|
| 80 | TASK · NEXT · STATE/AGE · OWNER |
| 120 | + VALID · REVIEW · SYNC |
| 200 / `--wide` | + ROUND · PUSHES · CHECK · TRACK |

Cells: NEXT `FIX validation` `SUBMIT` `GET R2` `WAIT reviewer` `CLAIM` `RESOLVE CONFLICT`;
STATE/AGE `REVIEW 2d` (age colour thresholds per state, configurable); VALID `PASS` `RUN` `FAIL` `UNK`;
REVIEW `R0` `R1 C4` `R2 C5` `R~`; SYNC `OK` `HEAD≠SERVER` `CACHE 43m`; PUSHES `2/3`; CHECK `P21 W3 F0` /
`STALE` / `NONE`. Task names truncate in the middle; NEXT and warnings never truncate.

Header line: accepted this week vs last week same point vs 4-week median.

Legend (auto-printed only for symbols present; `workboard legend` prints all):
```text
Legend: ✓ PASS  … WAIT  ! BLOCK/FAIL  ? UNKNOWN  ↻ STALE  ⚔ CONFLICT
        R0 no review  R1 one session  R2 two sessions  R~ older commit  C4 confidence 4/5
Colour only repeats the word: green PASS · amber WAIT · red BLOCK · blue INFO
```
ASCII mode replaces glyphs with words. Light/dark themes; colour is never the only signal.

## 10. Stats and reports

Definitions are printed with every stat. **Accepted = status accepted or used_in_training (the author's
rule), dated by reviewedAt, PT weeks.**
- **Flow:** accepted / submitted / worked-on per week (MT/ST), vs 4-week median; WIP by stage; arrivals vs
  completions; cycle time p50/p75 (first submit → accepted); reviewer wait; aging work.
- **Quality:** revision rounds per task; first-submission acceptance by submission cohort; bounce reasons
  (manual tags in v1; auto-buckets later).
- **Funnel (v1, exact sources only):** built (task dirs in git) → submitted / accepted / archived (Codimango status), and tasks per repo (config.json repo). Repos screened / idea cards and retire reasons come
  in v1.1 with their own inputs; nothing is estimated silently.
- **Contribution (private, labelled non-causal, min sample 5):** per session/host/model (Claude, Codex,
  Muse): build actions, tasks touched, their outcomes, pushes per accepted task. Off in exports unless
  `reports.include_contribution = true`.
- **Rank (optional source, plugin `sqlrank`):** where you rank on your track, team and org (accepted /
  submitted / worked-on for this quarter, last 30 days, this half, and weekly), from a saved DaiQuery
  query of your own (all windows relative to run time, so no weekly edits).
  `workboard rank` runs `meta daiquery.query execute --id=<config rank.daiquery_id> --output=json`
  from your own shell, caches the result with its snapshot date, and shows it in `stats` and the weekly
  report with freshness. If the query can't run (e.g. agent sessions are denied that table), it prints the
  one step to do by hand and accepts the result with `workboard rank import <file.csv|md>`. Generic for
  other users: any SQL/saved query that returns `scope, window, metric, value, rank, of` columns.
- Terminal charts: unicode bars/sparklines with ASCII fallback; `--json` for everything.
- **`report weekly`**: headline, data confidence, decisions/asks, flow table vs 4-week median, movement
  since last report, risks, next week, definitions + source snapshot footer. Deterministic markdown.
- **`report task`**: status + NEXT, owner/claim health, lifecycle + SHAs, checks/reviews with freshness,
  blockers, timeline, provenance footer; facts vs derived vs notes visibly separated.

## 11. Config, profiles, plugins (publishable)

- `~/.config/workboard/config.toml` (personal, never committed) + optional team config without identities.
  stdlib `tomllib`. `config_version`, migrations, unknown keys warn.
- Profile `swebench-codimango` (the default deployment): codimango source, presubmit check, Claude hooks.
- Plugin API v1 (trusted, explicitly enabled modules): `DataSource.fetch → FetchResult{observations,
  health}`, `ColumnPlugin.render → Cell`, `CheckPlugin.evaluate → [Finding]`, `StatPlugin.compute`.
  Fields are namespaced (`codimango.validation_status`); plugins cannot override `core.*` authority, print,
  or write the ledger.
- `workboard config init`: detects environment, asks one screen of questions (identity, timezone/week
  start, hosts, task repos, what NEXT actions matter, columns, thresholds, report audience), previews TOML,
  writes on confirm. After enough history it **suggests** stats with evidence ("reviewer wait is 41% of
  cycle time across 12 tasks — add review_wait_p50?"). Nothing auto-enabled, no telemetry.
- Private values (names, FBIDs, hosts, paths, repo URLs, reviewer names, internal URLs) live only in
  personal config or private plugins.

## 12. Build order (v1)

1. Foundations: minimal config loading/validation + profile selection + plugin registry/API; event schema,
   spool + single sync worker; codimango adapter (contract above); projection + findings.
2. `list` / `show` / `explain` / `available` / `status` / `doctor` / `legend`, responsive + plain output.
3. Claims (probe, acquire, heartbeat, steal, release) and `claim` / `release`; hooks (fail-open) +
   `install-hooks`.
4. `check run`, `review add/list`.
5. `report weekly` / `report task` (optional, off by default in daily use), `stats` (flow, quality, exact funnel), `rank`.
6. Interactive `config init` wizard + stat suggestions; one-time CLAIMS.md import of live claims.
v1.1: notes, contribution stats, repos-screened/cards funnel, history backfill from transcripts/Codex/Muse
logs, auto bounce buckets.

Each step: tests first (fixtures for codimango envelope incl. errors/huge prose/incomplete totals; corrupt
and duplicate events; two-writer and two-host claim races; clock skew; failed pull/push; 80/120/200 widths;
ASCII/no-colour/piped; hook latency + fail-open). Codex reviews each step before the next starts.

## 13. Not in scope

Writing to codimango (no submit/rerun/archive). Editing task files. People leaderboards in exports.

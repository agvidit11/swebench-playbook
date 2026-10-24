# workboard v1 Implementation Plan

> **For agentic workers:** Execution method (Vidit): Claude implements each task in this session; Codex
> (high effort) reviews the task's diff + test run as a pair-programming expert (terminal UI/UX, software
> design, manager readability, open-source architecture) and its corrections are applied before the next task.
> Steps use checkbox (`- [ ]`) syntax.

**Goal:** A stdlib-only Python terminal tool, `workboard` (alias `board`), that shows Vidit's codimango work
across two servers action-first, with atomic claims, session reviews, health/drift alerts, stats, rank and reports.

**Architecture:** Sources (codimango adapter, git, ledger, optional sqlrank) produce namespaced
observations + health → a projection builds `TaskView`s and `Finding`s with explicit authority → renderers
(list/show/explain/stats/report) only read the projection. Coordination facts are append-only per-host JSONL
events written through a flock'd spool and one sync worker; claims are create-only git refs.

**Tech Stack:** Python ≥ 3.11 stdlib only (`tomllib`, `json`, `fcntl`, `subprocess`, `unittest`), git CLI,
codimango CLI, `meta daiquery.query execute` (optional).

**Spec:** `tools/board/DESIGN.md` (v2.2, signed off in `tools/board/review/codex-review-{1,2,3}.md`).

## Scope cuts (Vidit, 2026-10-23)

- Task 12 (reports) CUT. Task 13: wizard + stat suggestions DEFERRED to publishing; keep CLAIMS import, skill, rollout.
- Two layouts only: compact (TASK · NEXT · STATE/AGE · OWNER · VALID · REVIEW · SYNC, fits ~120) and `--wide`
  (+ ROUND · PUSHES · CHECK · TRACK). `doctor` folded into `status`. Atomic claims and plugin skeleton KEPT.
- Ledger repo: `git@github.com:agvidit11/workboard-ledger.git` (private), set in personal config only.

## Global Constraints

- Python stdlib only; runs with `/usr/local/bin/python3` (3.12) on both servers; `python3 -m workboard`.
- No private values in code or committed files: identities, FBIDs, hosts, paths, repo URLs, reviewer names,
  internal URLs live in `~/.config/workboard/config.toml` or a private plugin.
- Accepted = status `accepted` or `used_in_training`, dated by `reviewedAt`, weeks Monday-start in
  `user.timezone` (default America/Los_Angeles).
- R2 = two distinct `session_id`s with verdict `ready` on the same full commit SHA.
- Hooks: ≤ 100 ms, no network, no git, no stdout, internal error → exit 0.
- Never writes to codimango; never edits task files.
- Colour never the only signal; respect `NO_COLOR`, `TERM=dumb`, non-TTY.
- Test command: `cd tools/board && python3 -m unittest discover -s tests -v`.

## Review Focus

1. Codimango CLI fails, times out, or returns `totalExact=false` → list still renders from last-good cache with a `SYNC FAILED`/`INCOMPLETE` banner, exit 0 (non-zero with `--strict`). Test in Task 3 + Task 6.
2. Two servers claim the same task within the same second → exactly one owns it, the other sees `LOST`, board shows one owner. Test in Task 8 (two clones, one bare remote).
3. A truncated last line in an event file (crash mid-write) → line quarantined, `MALFORMED_EVENTS` finding, every other event still counted. Test in Task 2.
4. Hook invoked with a missing/garbled transcript or a locked spool → exits 0 within budget, writes a warning event when possible. Test in Task 9.
5. 80-column non-TTY output (piped) → no ANSI, no glyph-only meaning, NEXT never truncated. Test in Task 6.

---

## File structure (all under `tools/board/`)

```
workboard/__init__.py        version, PLUGIN_API_VERSION = 1
workboard/__main__.py        argparse CLI dispatch
workboard/config.py          load/validate TOML, defaults, profiles
workboard/model.py           Event, Observation, SourceHealth, FetchResult, Finding, Cell, TaskView dataclasses
workboard/registry.py        plugin registry (sources, columns, checks, stats)
workboard/events.py          schema v1, spool (flock append), reader (dedupe, quarantine)
workboard/sync.py            single sync worker: seq, checkpoint, commit/push, sync state
workboard/sources/codimango.py  adapter: subprocess, cache, health
workboard/sources/git.py     task heads, push counts
workboard/projection.py      authority merge → TaskView + findings + NEXT
workboard/render.py          widths, groups, colour/unicode modes, legend, banner
workboard/claims.py          ref probe, acquire, heartbeat, steal, release
workboard/hooks.py           hook entry points + install-hooks
workboard/checks.py          check run (presubmit wrapper), reviews
workboard/stats.py           flow, quality, funnel
workboard/rank.py            sqlrank source + import
workboard/report.py          weekly + task markdown
workboard/wizard.py          config init + stat suggestions
tests/fixtures/              codimango envelopes (ok, error, incomplete, huge prose), event files
tests/test_*.py              one per module
board                        tiny shell shim: exec python3 -m workboard "$@"
```

### Task 1: Foundations — config, model, registry

**Files:** create `workboard/{__init__,config,model,registry}.py`, `tests/test_config.py`, `tests/test_registry.py`, `config.example.toml`.

**Interfaces — Produces:**
- `load_config(path: Path | None = None) -> Config` (dataclass; `config_version`, `user`, `ui`, `codimango`, `servers`, `repositories`, `claims`, `thresholds`, `reports`, `rank`, `plugins`); unknown keys → `Config.warnings: list[str]`; missing file → defaults + warning.
- Model dataclasses exactly as DESIGN §11 (`Observation`, `SourceHealth`, `FetchResult`, `Finding(code, severity, summary, next_action)`, `Cell(text, sort_key, full_text)`), plus `TaskView(entity_id, fields: dict, findings: list[Finding], health: dict)`.
- `Registry.register_source/column/check/stat(obj)`, `load_plugins(cfg) -> Registry` (explicitly enabled modules only; API-version mismatch → plugin disabled + warning).

- [ ] Test: `test_unknown_key_warns`, `test_defaults_when_missing`, `test_timezone_default_pt`, `test_plugin_api_mismatch_disabled`, `test_plugin_cannot_register_core_field`.
- [ ] Run tests → FAIL; implement; run → PASS.
- [ ] Codex review of task 1 diff; apply corrections; commit `tools/board/workboard tools/board/tests tools/board/config.example.toml`.

### Task 2: Event schema, spool, reader

**Files:** `workboard/events.py`, `tests/test_events.py`, `tests/fixtures/events_*.jsonl`.

**Interfaces — Produces:**
- `new_event(type: str, entity_id: str | None, payload: dict, *, actor: dict, commit: str | None, source: str) -> dict` (schema_version=1, uuid4 event_id, occurred_at UTC ISO).
- `spool_append(spool_dir: Path, event: dict, *, max_line=16384, max_queue=10000) -> bool` (O_APPEND + flock, never raises).
- `read_events(paths: list[Path]) -> tuple[list[dict], list[Finding]]` (dedupe by event_id, order by (host_id, seq), malformed/oversize → quarantined finding).

- [ ] Tests: `test_append_concurrent_writers_no_interleave` (8 processes × 200 lines), `test_truncated_last_line_quarantined`, `test_duplicate_event_id_deduped`, `test_oversize_line_rejected`, `test_alias_latest_wins_history_kept`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 3: Codimango adapter + cache + health

**Files:** `workboard/sources/codimango.py`, `tests/test_codimango.py`, `tests/fixtures/codimango_{ok,incomplete,error,huge}.json`.

**Interfaces — Produces:** `CodimangoSource(cfg).fetch(*, since=None, timeout_seconds=30) -> FetchResult`; cache at `~/.cache/workboard/codimango-last-good.json` (temp + `os.replace`); runs `[cfg.codimango.command, "task", "list", "--json"]` and separately `... --archived --json`; observations namespaced `codimango.*` including `status, validation_status, reviewed_at, entered_pool_at, created_at, commit_sha, head_commit_sha, validation_commit_sha, track, format`.

- [ ] Tests (fake runner): `test_nonzero_exit_keeps_last_good_and_unhealthy`, `test_timeout_marks_stale`, `test_incomplete_total_finding`, `test_stderr_banner_before_json_parsed`, `test_huge_prose_fields_dropped`, `test_archived_merged_status_archived`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 4: Git source + sync worker

**Files:** `workboard/sources/git.py`, `workboard/sync.py`, `tests/test_git.py`, `tests/test_sync.py`.

**Interfaces — Produces:**
- `GitSource(cfg).fetch() -> FetchResult` with `git.task_head` (last commit touching `<task>/`), `git.pushes_before_submit`, `git.pushes_after_submit` (needs `codimango.entered_pool_at`; computed in projection from raw commit times `git.commit_times: list[str]`).
- `sync(cfg, *, timeout_seconds=20) -> SyncState(last_pull_ok, last_push_ok, pending, error, at)`; single-worker via `flock` on `~/.cache/workboard/sync.lock`; assigns `seq`; acknowledges spool only after push succeeds.

- [ ] Tests (temp bare remote + 2 clones): `test_push_failure_keeps_spool`, `test_retry_dedupes`, `test_two_workers_one_runs`, `test_seq_monotonic_per_host`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 5: Projection, authority, findings, NEXT

**Files:** `workboard/projection.py`, `tests/test_projection.py`.

**Interfaces — Produces:** `project(observations, events, cfg, now) -> list[TaskView]`; `TaskView.fields` keys: `state, state_age_s, owner, claim_health, review (R0/R1/R2/R~), confidence, check, pushes, round, valid, sync, next, group (ATTENTION|READY|WAITING|DONE)`. Findings codes exactly: `HEAD≠SERVER, VALID≠SERVER, INCOMPLETE, DEGRADED, NONOWNER_COMMIT, CLOCK_SKEW, MALFORMED_EVENTS, SYNC_FAILED, CACHE_STALE, CONFLICT`.

- [ ] Tests: `test_used_in_training_counts_accepted`, `test_r2_needs_two_sessions_same_commit`, `test_new_commit_makes_review_stale`, `test_disagreement_is_finding_not_overwrite`, `test_done_not_available`, `test_next_priority_order`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 6: Renderer + read commands

**Files:** `workboard/render.py`, `workboard/__main__.py`, `board`, `tests/test_render.py`, `tests/test_cli.py`.

**Interfaces — Produces:** `render_list(views, health, cfg, *, width, color, unicode) -> str`; commands `list, show, explain, available, status, doctor, legend, changes [--since]` (last-look time stored in `~/.cache/workboard/last-look`), `config show|validate`, `plugins list|doctor` with `--json --plain --color --unicode --wide --mine --all --strict`.

- [ ] Tests: `test_80_cols_columns`, `test_120_and_wide_columns`, `test_pipe_no_ansi_stable`, `test_next_never_truncated_middle_truncates_task`, `test_legend_only_present_symbols`, `test_banner_sync_failed`, `test_strict_exit_nonzero_on_unhealthy`, `test_no_color_env`, `test_changes_since_last_look`.
- [ ] FAIL → implement → PASS → run live on devvm6971 (`./board`) and paste output into the Codex review → apply → commit.

### Task 7: Claim refs — probe, acquire, heartbeat, steal, release

**Files:** `workboard/claims.py`, `tests/test_claims.py`.

**Interfaces — Produces:** `ref_for(entity_id) -> str` (`refs/claims/<sha256[:16]>`, fallback prefix from probe); `probe(cfg) -> ProbeResult`; `acquire/heartbeat/steal/release(cfg, entity_id, actor) -> ClaimResult(status: ACQUIRED|LOST|RETRY|RELEASED|REFUSED, oid, detail)`; explicit `--force-with-lease=<ref>:<oid>` only.

- [ ] Tests (bare remote): `test_concurrent_acquire_one_wins` (2 clones, threads), `test_uncertain_push_resolved_by_ref_read`, `test_steal_requires_grace_and_unchanged_tip`, `test_release_wrong_oid_refused`, `test_offline_acquire_pending`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 8: claim / release CLI + auto-claim in sync

**Files:** modify `workboard/__main__.py`, `workboard/sync.py`; `tests/test_claim_cli.py`.

- [ ] Tests: `test_claim_to_alias_fragment`, `test_two_servers_same_second_one_owner` (Review Focus 2), `test_auto_claim_from_touch_event`, `test_mutation_fails_closed_when_ledger_stale`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 9: Hooks + install-hooks

**Files:** `workboard/hooks.py`, `tests/test_hooks.py`.

**Interfaces — Produces:** `python3 -m workboard hook <session-start|pre-tool|post-tool>` reading hook JSON on stdin; `install-hooks [--dry-run]` merges entries into `~/.claude/settings.json` (backup first, idempotent, hooks only).

- [ ] Tests: `test_hook_under_100ms`, `test_hook_bad_transcript_exit0` (Review Focus 4), `test_pre_tool_blocks_only_with_healthy_foreign_claim`, `test_alias_from_customTitle_then_aiTitle`, `test_install_idempotent_and_backup`.
- [ ] FAIL → implement → PASS → Codex review → install on devvm6971 → commit.

### Task 10: check run + reviews

**Files:** `workboard/checks.py`, `tests/test_checks.py`.

- [ ] Tests: `test_check_run_preserves_exit_and_output`, `test_check_recorded_with_commit_counts`, `test_review_requires_verdict_and_commit`, `test_dissent_visible`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 11: stats + rank

**Files:** `workboard/stats.py`, `workboard/rank.py`, `tests/test_stats.py`, `tests/test_rank.py`.

- [ ] Tests: weekly accepted by reviewedAt PT weeks matches the hand count fixture (W41 19, W42 12, W43 10 MT 8/ST 2 from 2026-10-21 data), `test_this_week_vs_same_point`, `test_4wk_median`, `test_first_submission_rate_by_cohort`, `test_funnel_uses_codimango_archived`, `test_rank_import_md_and_csv`, `test_rank_query_denied_prints_manual_step`, `test_ascii_chart_fallback`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 12: reports

**Files:** `workboard/report.py`, `tests/test_report.py`.

- [ ] Tests: `test_weekly_sections_order`, `test_weekly_deterministic`, `test_task_onepager_facts_vs_notes`, `test_contribution_excluded_by_default`.
- [ ] FAIL → implement → PASS → Codex review → commit.

### Task 13: config init wizard, CLAIMS import, skill, rollout

**Files:** `workboard/wizard.py`, `tests/test_wizard.py`, `skill/SKILL.md`, `README.md`.

- [ ] Tests: `test_wizard_noninteractive_flags`, `test_preview_before_write`, `test_suggestion_needs_min_sample`, `test_claims_md_import_live_rows_only`.
- [ ] FAIL → implement → PASS → Codex whole-branch review → fix → install skill on devvm6971; produce one-line install for devvm23237; commit.

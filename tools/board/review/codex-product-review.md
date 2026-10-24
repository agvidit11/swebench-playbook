# Workboard product review

## A. Verdict

Workboard is already a useful action-first control plane, not merely a status table.
The board, compact hovers, task drawer, links, grouping, stats, and basic Team feed substantially meet the author feedback.
The remaining gap is trust: several labels imply stronger freshness, assignment, review, and delivery guarantees than the data supports.
The next release should prioritize an explicit freshness/authority model and a closed-loop session inbox over more visual polish.
Verdict: keep and harden; the information architecture is sound, but it is not yet the single dependable place for two-server agent operations.

### Author-feedback check

| Feedback | Status | What is still not met |
|---|---|---|
| Problem-only, few-word hovers with a next step | **Mostly met** | Validation hover is compact and fix-oriented, but generic/infra failures can produce the wrong next step; pin/copy and keyboard access are missing. |
| Useful Review column: grey/green `✓/✓✓` plus human state | **Mostly met** | It exists exactly as requested, but grey means both absent and stale, the human state is visually subordinate, and superseded verdicts can still count. |
| Task links | **Met** | Card has codimango, server-commit, and latest-main links; terminal uses OSC-8 links. A row-level affordance is optional, not a gap. |
| Card starts with next steps, ETA, and who to assign | **Partial** | The next-step block is near the top, but external links precede it; ETAs are constants and “assignee” is only a host/load string with a placeholder command, not an assignment. |
| Sync meaning is obvious | **Partial** | Header hover and legend explain the two ticks, but row cells remain icon-only and “server last sync” is actually last ledger activity. |
| Header help | **Met in code** | Web column headers explain themselves and the TUI has Help; neither is keyboard-complete on the web. |
| Copyable hovers | **Partial** | `user-select:text`, pointer events, and “select to copy” exist; the 280 ms hover transfer is fragile and there is no pin or Copy action. |
| `needs-you / ready / validating / with-reviewers / done` plus Done subgroups | **Met** | The grouping and accepted/in-training/archived chips exist. “Accepted” also includes in-training, which should be explained or made independent. |
| Small cute animations without hurting readability | **Not met** | There are at least six simultaneous motion patterns and no `prefers-reduced-motion` path. |
| Data freshness | **Partial** | Codimango age, page timestamp, source health, and server “quiet” are shown; git/claims/ledger/inbox ages and refresh failures are not truthfully represented. |
| One shared place for claims, presubmit, new tasks, messages | **Partial** | Data is aggregated, but a pre-scaffold claim-only task is invisible, docs/skill omit the communication commands, CLAIMS.md is still a required second write, and automatic inbox injection exists only for Claude Code—not Codex. |
| Expandable card | **Met in code** | Drawer has an expand control and `e` shortcut. The supplied screenshots do not show the current Team tab despite it existing in source, so the live artifact appears behind the checkout. |

## B. DELETE

1. **Delete decorative motion from operational data surfaces.** The shimmer over the weekly bar and staggered row/card entrances continuously spend attention without encoding state. Keep one restrained live pulse and a brief, non-repeating changed-row highlight; honor `prefers-reduced-motion`.
2. **Delete false precision from default ETAs.** Repeated `~2h`, `~45m`, and `~3h` estimates are constants, not estimates. Until backed by task/check history, label them as rough effort bands or show `unknown`.
3. **Delete icon-only semantics where failure is costly.** Bare ticks in Presubmit and Sync force hover discovery and are especially ambiguous when grey. Use compact words (`clean`, `stale`, `importing`, `not run`) beside the glyphs.
4. **Delete “delivered” language for queued ledger messages.** The system currently proves written/surfaced/acked states separately; it cannot safely collapse those into delivery.
5. **Delete mandatory dual-writing to CLAIMS.md after migration.** An atomic board claim plus “also add your CLAIMS.md row” creates two ownership truths and directly contradicts the single-place goal. Keep CLAIMS.md as read-only legacy import until retired.

## C. ADD (ranked)

1. **P0 — Problem:** operators cannot tell whether a row is current enough to act on. **Design:** a global freshness strip plus per-source timestamps (`codimango`, git per server, claims ledger, presence/inbox), explicit `stale`/`offline` thresholds, last refresh success/error, and a Refresh action. Disable or qualify risky recommendations when an authoritative source is stale. **Effort:** M.
2. **P0 — Problem:** messaging is not a closed loop. **Design:** Team inbox with message states `queued → synced to target server → surfaced to session → acknowledged`, unread count, reply/thread context, retry/error state, and task-scoped messages visible on the task card. **Effort:** L.
3. **P0 — Problem:** “who should take this” is a suggestion string, not capacity-aware assignment. **Design:** show each live session's host, current task, state (`working/waiting/free/stale`), last activity, and capacity; provide Claim, Assign, Handoff, and Release actions with atomic conflict feedback. **Effort:** L.
4. **P1 — Problem:** next steps are computed but not auditable at a glance. **Design:** show the top action in the row; expand to ordered steps with provenance (`validation`, `presubmit`, `human review`, `sync`) and one-click copy of the exact command. **Effort:** M.
5. **P1 — Problem:** stale CLAIMS.md, claim refs, touch presence, and explicit ownership can disagree. **Design:** an authority/conflict badge with a resolver that names the winning source and offers a safe handoff/release path. **Effort:** M.
6. **P1 — Problem:** a claimed new slug is invisible until git/codimango knows it, and decisions have no durable task narrative. **Design:** materialize event/ref-only tasks immediately, then add task-scoped events for “new task”, scope decision, blocker, and handoff summary in both Feed and card timeline. **Effort:** M.
7. **P2 — Problem:** keyboard and accessibility support lag the visual UI. **Design:** focusable rows/tooltips, click-to-pin/copy hovers, visible focus rings, ARIA labels/live regions, contrast audit, and `prefers-reduced-motion`. **Effort:** S.

## D. MODIFY

- **Columns:** `Task | Next | Status | Owner | Validation | Review | Presubmit | Sync` → `Task | Action | Stage/age | Working on it | Validation | Review | Preflight | Server`. Keep eight columns, but replace ambiguous nouns with questions/statuses and collapse low-value detail on narrow screens.
- **Wording:** `needs you` → `Blocked / act`; `ready` → `Ready to work`; `with reviewers` → `Human review`; `done` → `Done`; `Sent back` stays because it is plain and useful. `Review` hover should lead with the human state, then agent approvals and preflight.
- **Colours:** reserve red for an actionable blocker, amber for stale/at-risk, blue for running/importing, green for verified-current success, grey for unknown/not applicable. Never use grey both for “not done” and “old result” without text.
- **Hovers:** keep the compact problem-first format, but make click/keyboard pinning primary, include only the reason and next command, and add Copy. Do not repeat the entire drawer.
- **Card:** move “Next steps” above the external-link buttons, then place `Assign/claim/handoff` and confidence beside it. Follow with Problems, human/agent review, commits/rounds, then metadata. Collapsed card should fit one screen; expanded mode may show chronology and raw evidence.
- **ETA:** show `effort` and `wait` separately, e.g. `30–90m work · then external wait, typical 45m`; add `low/medium/high confidence` and the evidence window. Unknown becomes `estimate unavailable`, not a fabricated default.
- **Assignee:** `host (lighter load)` → `session alias on host · 0 active / waiting` with why, plus a command/action that targets a real session ID. If no live eligible session exists, say `unassigned — start or select a session`.
- **Grouping:** keep `Blocked / act`, `Ready to work`, `Validating`, `Human review`, and `Done`; retain Done subfilters `Accepted`, `In training`, `Archived`. Put claim conflicts and stale-source uncertainty ahead of validation failures.
- **Freshness:** `live · codimango data 1m old · page …` → `Page refreshed 12s ago | codimango 1m ✓ | git: hostA 40s ✓, hostB 7m stale | ledger 35s ✓ | inbox 35s ✓`. A green live dot must mean all required sources are within policy, not merely that the page is polling.

## E. Agents & servers

Workboard should be the coordination control plane, while source systems remain authoritative. Before work, every session reads `board available` and `board show`, resolves ownership, then atomically claims. During work it automatically emits heartbeat/presence, current task, latest commit, and coarse state; on push it records the commit and observes import/validation; on preflight it records structured results; on stop it prompts for release or handoff. These automatic events must never masquerade as human approval or a completed handoff.

Explicit session actions should remain: choosing/accepting an assignment, changing task priority/scope, recording a review verdict, acknowledging a message, and releasing/handover with a one-line state plus next command. Assignment is an offer until the target session accepts or starts work; show `offered`, `accepted`, `declined/expired`, not just `assigned`.

Duplicate-work prevention needs a server-independent atomic claim as the gate, then local edit hooks as guardrails. Presence is evidence of activity, not ownership. On conflict, block new edits where possible and present both sessions with the same resolver. A handoff should bundle task, current commit, completed checks, open findings, next command, and ownership transfer; only release the old owner after the new owner accepts, or label the gap explicitly.

Message etiquette: target the narrowest session/server; attach a task when relevant; write one actionable request with owner and urgency; acknowledge only after reading; reply with outcome or blocker; use broadcast only for cross-cutting incidents. The UI should discourage chat noise by separating `FYI` from `action requested` and showing unanswered requests.

The shared contract must be in both README and the installed skill: at session start read inbox/assignments; before editing show/claim; after a push or preflight let hooks record objective state; after an agent review explicitly record the verdict; before exit explicitly hand off/release and acknowledge messages. Claude and Codex need equivalent adapters—presence-only support for Codex is not enough.

## F. ETA/next-step accuracy

Available inputs include lifecycle/status timestamps, state age, validation items/details, git head/server/validated commits, changed files, commit history, preflight events, agent reviews tied to commits, human revision decisions, claims/presence, and aggregate cycle/wait statistics. These support accurate **state-derived next steps** and historical wait estimates; they do not yet support precise coding-effort estimates.

Compute external waits from recent, track-specific cohorts with sample size and percentiles. Compute work effort only after capturing step start/finish or active-time events, bucketed by action/check/track/difficulty; exclude idle and concurrent-session time. Show ranges and confidence: high for a current deterministic command, medium for waits with enough recent samples, low for sparse cohorts, and unknown for novel repair effort. Never subtract wall-clock state age from a population median and call the remainder an ETA without a survival model; elapsed waits do not have that distribution.

When unknown, show `Next: fix calibration` and `Effort: unknown`, optionally `similar fixes: median 1.8h, n=7`—not `~2h`. Separate `your work`, `automation`, and `human wait`, because only the first is schedulable by the author.

## G. Visual critique of the screenshots: 10 specific fixes

1. The table is information-dense but the task name receives too little width; freeze it as the first column and allow two-line wrapping before truncation.
2. “Next” repeats `FIX validation` across many rows; replace it with the first actual problem (`calibration`, `oracle`, `provenance`) so scanning differentiates tasks.
3. Owner strings such as `23237 (CLAIMS.md)` are cryptic; show `server/session`, freshness, and source in a secondary line.
4. The Review column's grey ticks and grey human text are too faint and ambiguous; render human state as a labelled chip and agent approvals as secondary `0/2`, `1/2`, `2/2 current`.
5. Presubmit and Sync are nearly all bare ticks; add short labels and consolidate into a compact “Readiness” cell if horizontal space becomes tight.
6. The hover is concise, which is good, but it overlaps adjacent rows and requires a pointer precision move to copy; click-to-pin it, add Copy, and anchor it to the cell edge.
7. The drawer correctly starts with next steps, but primary actions are external links; put Claim/Assign/Handoff/Copy next command ahead of navigation links.
8. The drawer's narrow width makes the handoff command wrap awkwardly; make the action block full width with a copy button or default the drawer slightly wider.
9. Stats bars lack a shared scale cue and the funnel reports `imported 144` above `built 143` as `101% of previous`; explain non-nested populations or rename the visualization so it does not imply an impossible funnel.
10. The continuous shimmer, pulsing dot, twinkling change marker, row entrances, chip movement, and card movement compete; limit animation to a soft freshness pulse and a one-shot update highlight, with reduced-motion support.

## H. Risks/bugs in the code (file:line)

1. **High — superseded review verdicts still count.** `workboard/projection.py:107–122` builds sets from every verdict on the commit instead of the latest verdict per session; `ready → changes` still contributes approval. Two such sessions can produce `R2` and dissent simultaneously. `workboard/insights.py:128–138` repeats the same mistake in the web summary.
2. **High — pre-scaffold claims are invisible.** `workboard/projection.py:220–221` creates views only for entities present in observations, not claim/event-only tasks; `workboard/app.py:118–120` also drops claim-ref observations for unknown tasks. This contradicts `skill/SKILL.md:18–19`, which promises a newly claimed slug will show everywhere before scaffolding. A direct claim-only projection returns no rows.
3. **High — “delivered” only means pushed to the ledger.** `workboard/__main__.py:1122–1123` maps `last_push_ok && !pending` to `delivered`; `workboard/html_page.py:247–257` promises delivery into the session. There is no evidence that the target server fetched it or that a session saw it.
4. **High — Codex sessions never receive injected messages.** Inbox injection is a Claude `additionalContext` hook at `workboard/hooks.py:231–251`, while Codex support only scans session logs for presence at `workboard/presence.py:108–127`. This misses the stated Claude/Codex communication goal.
5. **High — hook delivery state races and can redeliver.** `workboard/comms.py:99–111` performs an unlocked read/modify/write through one fixed `.tmp` filename; concurrent hooks can lose updates or fail replacement. Line 108 keeps the lexicographically greatest 500 random IDs, not the 500 newest messages.
6. **High — Team's “last sync” is not a sync time.** `workboard/comms.py:166–181` derives it from the newest ledger event recorded by a host. A healthy but quiet syncing server appears offline, and an event-producing server can appear healthy without a successful pull; the UI labels this `last sync`/`online` at `workboard/html_page.py:235–240`.
7. **High — failed web refreshes are invisible.** `workboard/html.py:126–134` swallows every background refresh exception and leaves the old payload. The client continues fetching it and can retain a green live dot because `workboard/html_page.py:203–204,260–293` ignores ledger state and freshness age.
8. **Medium — infra failures can prescribe a push instead of a rerun.** `workboard/insights.py:62–64` correctly downgrades codimango infrastructure failures to warnings, but `FIX validation` only turns `fail` items into steps at lines 91–95; the resulting plan can omit the actual rerun and say only “push, then wait.”
9. **Medium — ETAs look measured but are mostly literals.** `workboard/insights.py:91–123` hard-codes repair/review/import times. Lines 117–120 estimate remaining reviewer wait as `p50 − elapsed`, which is not a valid conditional wait estimate and can claim “any time now” indefinitely.
10. **Medium — assignee suggestions can target an offline host.** `workboard/insights.py:156–165` selects the configured host with the lowest claimed-task count, with no live-session eligibility, waiting state, specialty, or capacity; it emits a placeholder rather than an executable assignment.
11. **Medium — interactive terminal refresh crashes if gathering throws.** Both `workboard/app_ui.py:217–225` and `workboard/tui.py:353–362` let a worker-thread exception leave `box["snap"]` unset, then index it after join. Preserve the last snapshot and expose the error instead.
12. **Medium — the claimed per-field authority merge is observation-wide.** `workboard/projection.py:56–67` ranks an observation by its highest-authority field and then updates every field. Mixed-authority plugin observations can overwrite newer or more authoritative values despite the docstring promising per-field resolution.
13. **Low — help text names nonexistent/missing group keys.** `workboard/app_ui.py:3–4,129` says `a/r/w/d`; actual keys at line 21 are `a/r/v/e/d`. This is exactly the sort of operator papercut the Help tab should eliminate.
14. **Documentation/rollout gap.** `README.md:8–17` and `skill/SKILL.md:28–38` omit `ui`, `serve`, Team, `msg`, `inbox`, `ack`, and `feed`; the skill still mandates a duplicate CLAIMS.md update at lines 18–21. The current source has a Team tab, but none appears in the supplied live screenshots.

**Verification:** 448 tests were exercised. The complete sandbox run had 447 successes plus one localhost-bind permission error; that isolated HTML server test passed outside the socket restriction. It emitted a `ResourceWarning` because the test calls `shutdown()` but not `server_close()` (`tests/test_html.py:30–44`). Coverage is strong for rendering widths, claims, projection, and basic comms, but does not cover latest-verdict replacement, concurrent inbox delivery, Codex message injection, failed live refresh, or browser accessibility. Both supplied terminal captures contain only `./board: No such file or directory`; `./board --help` works from this checkout, so the captures were taken from the wrong directory and do not verify terminal UX.

## I. Prioritized 2-week roadmap

- **Day 1:** fix latest-verdict semantics, materialize claim/event-only new tasks, and correct infra-rerun steps; add regressions.
- **Days 1–2:** define source authority/freshness and message/assignment state machines; update README and installed skill, removing CLAIMS.md dual-write.
- **Days 2–3:** ship per-source freshness/error indicators and prevent green “live” when required inputs are stale.
- **Days 3–5:** make inbox state atomic and visible (`queued/synced/surfaced/acked`); add equivalent Claude and Codex delivery plus task threads.
- **Days 5–7:** add live-session capacity plus atomic assign/accept/handoff/release flows and resolver UX.
- **Days 7–8:** replace constant ETAs with effort/wait separation, ranges, confidence, sample size, and unknown states.
- **Days 8–9:** revise row labels/columns, pin-and-copy hovers, card actions, responsive behavior, and reduced-motion/accessibility.
- **Days 9–10:** harden refresh/concurrency failure paths, add two-host integration/browser tests, recapture terminal/web artifacts, and dogfood for a full day.

# Workboard product review

## A. Verdict

- Yes: today it is genuinely useful as a read-only triage screen for status, validation failures, ownership hints, and weekly output.
- No: it is not yet trustworthy as the coordination authority for parallel Claude/Codex sessions across two servers.
- The biggest gap is truth latency: claims and checks can arrive 3–4 minutes late, refresh failure is hidden, and “live” can mean an old snapshot.
- The next-step, ETA, and assignee UI looks more certain than the underlying data; hard-coded durations and server-only load balancing should not ship as advice.
- Call it a strong personal beta, not a finished control plane; the supplied terminal captures are only `./board: No such file or directory`, so terminal usability is not demonstrated by the review artifacts.

## B. DELETE

| Delete | Why |
|---|---|
| Hard-coded `~2h`, `~45m`, `~3h`, and “any time now” ETAs in `insights.next_steps` | They are guesses presented as measurements. A wrong ETA is worse than `unknown`; remove them until observed transition history exists. |
| Review confidence scores and `▰▰▰▰▱` bars | Self-rated 1–5 confidence is false precision, is not used to choose an action, and remains in the terminal after the web UI moved to ticks. Keep verdict and note only. |
| The default **Presubmit** column | It is mostly grey ticks, duplicates the draft ladder in **Next**, and even leaks into the Review hover. Fold a failed/stale/not-run prerequisite into **Next** or **Blocker**; expose full check detail in the card. |
| Green “all N checks passed” validation hover cards | This is exactly the noise the author rejected. A clean cell needs no hover; reserve the surface for at most three warnings/failures and their fixes. |
| Funnel conversion percentages in the main Stats view | The screenshot says `imported 144 = 101% of built 143`: these are different source populations, not a valid sequential funnel. Keep raw inventory under diagnostics only, or compute a task-intersection cohort. |
| `tui.watch()` | `app_ui.run()` is the actual interactive path and repeats its refresh loop, alternate-screen handling, animation, and rendering. Delete the dead duplicate and its one-off test. |
| The requirement to update both `board` and `CLAIMS.md` | `skill/SKILL.md:16-22` tells a session to claim in Workboard *and* add a CLAIMS row. That is the overlap risk the product is meant to remove. Keep CLAIMS.md as a read-only compatibility source during migration, never as a second required write. |
| ROUND, PUSHES, and TRACK from the normal `--wide` workflow | They do not change the next decision. Put them in `show`/history; a “wide” board should reveal blockers and handoff state, not archaeology. |

## C. ADD

| Rank | Missing feature | Problem | Concrete design | Effort |
|---:|---|---|---|:---:|
| 1 | Canonical task-intent registry | A new slug cannot be claimed before it exists in git/codimango, contradicting the primary anti-duplication workflow. | Add a ledger `task_created` entity and `board start <slug> --repo/--idea --to <session>` transaction that creates/reserves the slug and atomically claims it. Event-only tasks must project as `Not started`, including CLAIMS.md-only rows. | M |
| 2 | Fresh coordinator loop | Cron + server refresh + browser polling causes the observed 3–4 minute lag; failures are swallowed. | One long-running coordinator performs ledger pull/push, source refresh, presence, review refresh, and publishes a monotonically versioned snapshot. Use file notification/SSE locally; target claim/check visibility under 10 seconds and codimango visibility under 60 seconds. | M |
| 3 | Real cross-agent session identity | Every Codex CLI invocation currently becomes the same `human:user@host`; separate Codex sessions can overlap undetected. | Register `{session_id, agent kind, host, title, cwd, last_seen, capabilities}` for Claude and Codex. Issue a Workboard session token/env var to spawned agents and require it for claim/review attribution. | L |
| 4 | Atomic handoff and acceptance | `--to <title fragment>` assigns immediately to a possibly stale session, with no acknowledgement or context. | `board handoff <task> --to <session> --note ...` creates `offered`; target runs `board accept`, which transfers the lease. Show pending handoffs and allow timeout/cancel. | M |
| 5 | Actionable task card controls | The card reports state but still makes the user translate it into commands. | Put **Do now** first, with copy buttons for the exact `board claim/check/review/release` or codimango command; offer “assign to live session” choices and show the evidence behind the recommendation. | M |
| 6 | Observed-duration history | No source records import/validation state transitions over time, so honest validation ETAs cannot be learned. | Append compact transition events whenever `(status, head SHA, validation SHA/status)` changes; derive duration cohorts by track, action, and failure type. | M |
| 7 | Conflict radar | Multiple recent presences are listed but do not become a conflict unless there are multiple claim events. | Raise `POSSIBLE_OVERLAP` when two live sessions touch the same task without a shared reviewer/builder role; show both sessions and one-click ownership resolution. | S |
| 8 | Pinned, keyboard-accessible details | Hover is fragile for copying and unavailable on touch/keyboard. | Hover previews; click or Space pins the same popover; add Copy action, focus management, Escape close, and ARIA labels. | S |

## D. MODIFY

| Area | Before | After |
|---|---|---|
| Default columns | `Task · Next · Status · Owner · Validation · Review · Presubmit · Sync` | `Task · Do next / ETA · Status / age · Working on it · Blocker · Human review · Server`. Put agent approvals and presubmit as compact prerequisites under **Do next**, only when relevant. |
| Next wording | `FIX validation`, `GET R2`, `RERUN server`, `WAIT reviewer` | `Fix calibration: step 2 too easy`, `Need 1 independent review`, `Re-run validation for 1 newer push`, `Human review · waiting 1d`. Name the problem, quantity, and verb. |
| Validation cell | `✔ clean`, `✘ 1 issue`, with an all-passed hover | Blank/dim `—` when clean; otherwise `Calibration: step 2 easy` or `2 blockers`. Hover shows at most three lines: `problem → suggested fix`; never list passes. |
| Review column | Grey/green one/two ticks plus grey human text; Review hover also includes presubmit | Two explicit agent slots `●○`/`●●` labelled “agent checks” in the header help, `↻` for old commit, then a high-contrast human tag (`Not submitted`, `Waiting`, `In review`, `Sent back ×2`). Review hover contains review only. This is better than the old inaccurate bars, but the current grey single tick cannot distinguish current from stale without hovering. |
| Sync | One/two green ticks mean imported/validated; a failed validation can still receive two green ticks | Rename the column **Server** and show words: `On server`, `Importing`, `1 push behind`, `Validation stale`, `Unknown`. Validation success/failure belongs only in **Blocker**, not in server synchronization. |
| Header help | Hover text exists, but the symbols still require the tooltip | Keep concise hover definitions, add a visible `?` legend trigger and focusable headers. A user should understand the cell text without hovering. |
| Hover copy | `user-select:text` plus “select to copy”; moving into a floating popover is timing-sensitive | Click pins; each command gets a copy icon and transient “Copied”. Do not open the drawer when the click was used to pin/copy. |
| Task link | The task name only opens a drawer; three drawer buttons compete (`codimango`, `server commit`, `main`) | Task name is a normal codimango link with an external-link icon; clicking elsewhere on the row opens the card. In the card, label commit links `Reviewed commit abc1234` and `Current main def5678`, showing why both exist. |
| Card hierarchy | Title → taxonomy → status → three links → next steps → assignee | Title → **Do now** → total active-time range/confidence → **Assign to** live session/server → blocker → human review → history → links/taxonomy. The author’s latest card request is still not met. |
| ETA | Fixed constants and `historical median - age` | Observed range + confidence + sample: `Validation: 25–55m · medium · n=18`. For human waits use conditional remaining time, not subtraction. If unsupported: `ETA unknown · no comparable history`. |
| Assignee | “keep with owner” or least-loaded server by raw active-task count, ending in a `<host session>` placeholder | Keep a healthy current owner. Otherwise recommend an actual live, unclaimed session with agent kind, host, idle time, capability, and weighted load; if none exists say `Unassigned — start/claim on 23237`, not a fake person. |
| Groups | The five requested groups exist; Done’s “accepted” filter includes in-training tasks and double-counts them | Keep `Needs you · Ready · Validating · With reviewers · Done`; make Done’s children disjoint: `Accepted`, `In training`, `Archived`. “Needs you” means a human/agent action is possible now, not every warning. |
| Freshness | “live”, codimango age, and page time; ledger can be minutes behind and refresh failure stays green | Show `snapshot 8s · codimango 42s · ledger 6s · presence 9s`, turn the live dot amber/red by thresholds, and show the last refresh error. A claim/check event should optimistically appear immediately with `syncing`. |
| Colour | Red/green/blue/violet encode groups while red/amber/green also encode severity/status | Reserve red for blocking, amber for action/warning, blue for waiting/system work, green for genuinely ready or completed, violet for ownership/review metadata. Always pair colour with text/icon. |
| Animation | Floating logo, pulsing dot, shimmering bar, row entrances, twinkles, chip rotations all run continuously | Keep one subtle state-change sparkle and drawer easing; stop decorative loops after one cycle and honor `prefers-reduced-motion`. Cuteness should mark change, not consume attention. |

## E. Making better use of the structure

Workboard should be the one coordination write surface. The private ledger is already the right substrate, but the projection needs a first-class task-intent record rather than requiring codimango/git to create identity. CLAIMS.md should remain an advisory, visibly stale compatibility input until all sessions use `board`; sessions should never be told to dual-write it.

Represent ownership as a lease on a role, not just a string: `{task, role: builder|reviewer, session_id, agent, host, acquired_at, heartbeat_at, phase, handoff_note}`. A task may have one builder and independent reviewers, but never two builders. Reviews do not take the builder lease. The two-server header should show weighted lane capacity, for example `23237: 2 editing, 1 validating · 6971: 1 editing, 2 idle`, with source age.

Use this lifecycle:

1. `board start slug --to session` reserves a new idea before files exist.
2. Entering a known task directory offers/renews the builder lease; a conflicting edit is blocked with owner, host, age, and handoff command.
3. Push/check/review events update the same task record immediately; server import and validation transitions reconcile later.
4. `board handoff` carries the current blocker, exact commit, last clean check, and next command; the target accepts before ownership moves.
5. Accepted/in-training/archived tasks release leases automatically, while a failed or abandoned session leaves an explicit recoverable handoff.

Each session should do the following automatically: register identity and heartbeat; infer the task from cwd/tool paths; renew its lease while genuinely active; record push SHA and check results from wrapped commands; publish presence within seconds; stop presence on session end; and release when codimango reaches Done. It should do the following explicitly: reserve a brand-new idea/slug, accept a handoff, release/park with a reason, steal an expired lease, and submit an independent review verdict. Those are intent decisions and should not be guessed.

Duplicate prevention must work before source creation and for Codex as well as Claude. Today the Claude hook blocks some editor tools, while Codex is mostly inferred after the fact. Give Codex sessions the same explicit session token/lease protocol, and treat two fresh builder presences as an actionable conflict even if claim synchronization has not completed.

## F. ETA and next-step accuracy

### Data that exists

| Source | Useful facts | Limits |
|---|---|---|
| Codimango | Current status, validation status/details, created/entered-pool/reviewed/updated times, server/head/validation SHAs, track/category/difficulty | Mostly latest state; no durable history of every import/validation transition; latest submission timestamps cannot reconstruct first-submission cycle. |
| Human review history | Decision kind/time and short reason; revision rounds | Refreshed a few tasks per cron run, cached without freshness in the card, and parsing depends on CLI prose. |
| Git | Task head, commit times, changed files since validated SHA, server-SHA commit time when present | Commit time is not push/import time; an older timestamp does not prove synchronization. |
| Ledger | Claims, renewals, touches, presence, checks, agent reviews, build actions, aliases | Presence is sampled/inferred; current Codex identity is not session-safe; no canonical task-intent or codimango transition events. |

### Honest computation

- Record state transitions first: local push observed, server head changed, validation started/completed, entered pool, human decision, revision push, presubmit started/completed.
- Split **active effort** from **external wait**. Calibration repair time should use builder-active intervals from claim/touch to clean check/push; validation ETA should use server-head-to-validation-complete; reviewer wait should use pool-entry-to-decision.
- Build cohorts by task format/track, action type, validation check, revision round, and difficulty only when `n >= 5`; otherwise back off to the broader cohort.
- Show a range, not a point: p50–p75 for system waits and p50–p80 for repair effort, plus `n`, lookback window, and `high/medium/low` confidence.
- For an already elapsed human wait, compute the conditional residual distribution `T - elapsed | T > elapsed`; the current `p50 - age` rule is statistically wrong and produces “any time now” precisely when uncertainty is highest.
- Never add multiple step ETAs as though work were serial if a wait can overlap another agent’s work. Label `active work` and `waiting` separately.
- When data is absent show `ETA unknown — no observed transitions yet`; when sample size is weak show `Usually 1–4h · low confidence · n=3`; for human review say `No promise; 50% of comparable reviews finish within …`.

Next-step selection should remain deterministic, but use the most specific evidence: ownership conflict → current validation blocker → server/import drift → stale presubmit/agent approval → human state. A generic `FIX validation` should never survive when a parsed issue such as `calibration: step 2 too easy` exists. If sources disagree, the next step is to reconcile the disagreement, not to pick whichever timestamp looks newer.

## G. Visual critique of the screenshots

1. Reduce the board header/control stack by about 40 px: the logo, week line, colour bar, tabs, group chips, owner chips, search, and health consume too much vertical space before the first task.
2. Give **Task** more width and middle-truncate names; the current end ellipsis removes the discriminating suffix (`…reference-fidelity`, `…split-move`).
3. Replace the eight-column tick matrix with the seven-column action set in section D; **Presubmit** and **Sync** currently force interpretation instead of supporting scanning.
4. Remove green `✔ clean` from every validation row. Blank clean cells make the red failure rows and amber warnings immediately visible.
5. Make human review state a pill with readable contrast. Grey prose beside grey ticks is the lowest-salience information in a column whose human status matters most.
6. Replace green double Sync ticks with explicit server words. Screenshot 1 shows red validation failures beside green `✓✓`, a visually contradictory success signal.
7. Move the task card’s Next Steps block above status and link buttons, and put the proposed actual session/server plus confidence on the same first screenful.
8. Increase dim-text contrast (`#5b6070` ticks/hints are too faint on `#13151b`) and add focus outlines; colour alone should not distinguish active/off chips or review completion.
9. Remove the permanent logo float, health pulse, and progress-bar shimmer; retain the row-change sparkle and drawer motion, with a reduced-motion mode.
10. Fix Stats before polishing it: do not render `101% of previous`; align stacked MT/ST bars without the negative margin, mark the current week as week-to-date, and include coverage next to cycle/wait numbers.

## H. Risks and bugs visible in the code

The suite is substantial—443 tests pass—but it mostly checks structural output and current rules, not whether those rules represent reality. It also emits an unclosed-socket `ResourceWarning` from the HTML server test.

| Severity | Evidence | Risk / bug |
|---|---|---|
| Critical | `workboard/__main__.py:93-102`, `workboard/__main__.py:422-424`, `workboard/projection.py:220-221`, `workboard/app.py:118-120` | `board claim <new-slug>` cannot work before the slug exists in a source; event-only tasks and orphan claim refs are discarded. This directly breaks the documented anti-duplication workflow for new tasks. |
| Critical | `workboard/identity.py:50-60` | Only `CLAUDE_CODE_SESSION_ID` creates an agent identity. Every Codex session on a host is attributed to the same human shell actor, so ownership and “two independent sessions” can be wrong. |
| High | `workboard/__main__.py:1088-1092`, `workboard/html.py:121-129`, `workboard/html_page.py:193-194`, `workboard/html_page.py:250-251` | Live serve skips ledger sync, refresh errors are swallowed, and the live dot only reflects old source-health fields. The page can stay green and stale; cron + refresh + polling explains the reported lag. |
| High | `workboard/projection.py:275-288`, `tests/test_projection.py:160-162`, `tests/test_projection.py:186-192` | Unequal local/server SHAs become `OK` when the local commit time is older. Timestamps cannot prove commit containment or import, and the tests explicitly lock in this false result. |
| High | `workboard/projection.py:217-218`, `workboard/events.py:257` | Ledger events are read in per-host sequence order, then re-sorted globally by `occurred_at`. This violates the design’s “order within writer by seq” rule and lets clock skew reorder claim/release/renew state. |
| High | `workboard/html.py:20-29`, `workboard/projection.py:298-300` | The web card marks agent reviews/checks current only against git head, while projection uses git head or server SHA. With git absent/stale, web and terminal disagree. The web also picks `checks[-1]` from host/seq order rather than the latest occurrence. |
| High | `workboard/html.py:21-24`, `workboard/insights.py:124-149` | Web review deduplication uses display alias (`who`), not session ID. Two sessions with one alias collapse; one session renamed between reviews can count twice. The new ticks can therefore still be inaccurate. |
| High | `workboard/presence.py:92-107` | A task mentioned in any tool input in a transcript tail gets the transcript file’s latest mtime. Later unrelated session activity makes an old task look freshly active, potentially hiding free work or assigning it to the wrong session. |
| High | `workboard/presence.py:108-127` | Codex presence reads only the first 64 KiB and only the initial cwd; it does not inspect later tool paths. Codex working from a repo root is invisible, so cross-agent overlap protection is asymmetric. |
| Medium | `workboard/projection.py:56-67` | `_merge` claims to resolve authority per field but sorts each observation by its maximum authority and updates every field together. A mixed-authority observation can overwrite a more authoritative field. |
| Medium | `workboard/projection.py:289-290`, `workboard/html_page.py:146-147` | `validated = valid != RUN`, so a failed validation is rendered as the second green Sync tick. “Validation finished” is semantically true, but green communicates success and contradicts the red blocker beside it. |
| Medium | `workboard/html_page.py:174-180` | The Done `accepted` filter/count includes `in_training`, then shows `in_training` again. The requested Accepted/In training/Archived children are not disjoint. |
| Medium | `workboard/insights.py:67-119` | Repair and wait ETAs are constants; reviewer remaining time is `p50 - state age`. There is no sample count, cohort, interval, or confidence, so the UI overstates accuracy. |
| Medium | `workboard/insights.py:152-161`, `workboard/html.py:62-69` | Assignee selection counts tasks per parsed host prefix and picks `min(load)`. It ignores live sessions, agent capability, task cost, running checks, stale presence, and whether the suggested host can access the repo. |
| Medium | `workboard/stats.py:37-57`, `workboard/stats.py:101-111` | “All-time accepted” counts only tasks whose *current* status is accepted/in-training. Archiving a previously accepted task can reduce the all-time total even though `status_before_archive` is available. |
| Medium | `workboard/sync.py:135-140` | Ledger pull uses `git reset --hard`; an in-progress tracked edit in the private ledger checkout, including config, can be silently discarded. The dedicated checkout needs a no-manual-edit contract or a safer config path. |
| Medium | `workboard/html.py:21-45`, `workboard/html.py:104-112`, `workboard/__main__.py:951-955` | Static HTML embeds task names, aliases, internal links, review notes/reasons, and validation text; `config show --json` prints paths/remotes. There is no redacted export mode or privacy warning. |
| Medium | `workboard/legacy.py:40-56`, `workboard/__main__.py:484-495`, `workboard/completion.py:32-39` | CLAIMS.md sync only recognizes tasks already in the codimango cache and excludes archived tasks. A free-text row for a brand-new task—the moment coordination matters most—is silently ignored. |
| Low | `workboard/html_page.py:160-165` | Validation hover maps every non-pass item without a cap and still renders “all N checks passed”; the latest hover feedback is only partially implemented. |
| Low | `DESIGN.md:15`, `skill/SKILL.md:16-25`, `DESIGN.md:55`, `README.md:27-28` | The signed-off design says review is the only explicit action and mentions a five-minute timer, while the skill requires claim/CLAIMS/check/release/review and README says two minutes. Workflow documentation is not one coherent contract. |
| Low | `tests/test_html.py:30-44` | The test calls `shutdown()` but not `server_close()`, producing the observed unclosed-socket warning and masking resource-lifecycle regressions. |

## I. Prioritized two-week roadmap

1. Add ledger-backed task-intent projection and make `board start/claim` work for an unknown slug.
2. Give Claude, Codex, and shell sessions stable distinct identities; bind claims/reviews to session IDs.
3. Make live serve run/publish synchronized snapshots and expose refresh errors plus per-source ages.
4. Fix SHA drift logic, per-field authority merge, event ordering, and web/terminal current-commit parity.
5. Replace the table with the action-first column set and remove clean-validation/presubmit noise.
6. Reorder the card to Do now → effort/wait → actual assignee → blocker → review → history/links.
7. Implement atomic offered/accepted handoffs and possible-overlap findings for multiple builder presences.
8. Record codimango/import/validation transitions; show `ETA unknown` until cohorts meet the sample threshold.
9. Correct Done subgroups, all-time accepted, and remove invalid funnel conversion percentages.
10. Add pinned/copyable keyboard popovers, focus states, contrast fixes, and reduced-motion CSS.
11. Rewrite README/DESIGN/skill as one workflow: Workboard writes, CLAIMS.md compatibility reads only.
12. Dogfood on both servers for 48 hours with freshness/duplicate-work logs, then fix only observed failures before calling it v1.

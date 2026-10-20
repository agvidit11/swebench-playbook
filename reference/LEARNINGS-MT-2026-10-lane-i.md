# Multi-turn SWE-bench tasks: what I learned (lane-i, devvm6971, Oct 2–19 2026)

Written 2026-10-19 by the lane-i orchestrator (Claude). Sources: ledger/CLAIMS.md, ISSUES.md,
RETRO-2026-10-15.md (47 tasks / 176 pushes), LESSONS-DRAFTS-2026-10-16.md, PROBE-BRIEF.md lessons,
and the per-task PROGRESS/WHY-FIRST-PUSH-FAILED files.

## 1. Results in one table

| Period | Approach | Outcome |
|---|---|---|
| Oct 2–10 | Bookkeeping-under-edits domains + push, then fix from the 15 server trees ("union loop") | ~16 server passes, but 64% of pushes failed, a median of 2+ rounds to pass, and only 8/35 accepted on the first human review |
| Oct 11–15 | Same loop, first pushes unmeasured | 10 first pushes, 0 accepted; most failed calibration or the agentic review |
| Oct 15–19 | Retro → reviewer bar + cold-probe-first + measured first push | ~25 cards probed, most killed before build; 3 pushed (libcst, removestar, composer); **removestar and composer passed on their first push** |

The change that mattered: **measure before pushing, and build the reviewer's bar in from the first push.**

## 2. What fails, why, and the fix

### 2.1 Calibration (60% of failed pushes were "too easy", 28% "too hard")
| Failure | Root cause | Fix |
|---|---|---|
| Steps saturate at 5/5 | Every stated rule gets solved, and single-choke-point bookkeeping seams get solved (laminas, treebeard, laravel-settings) | Pick seams where correctness rests on *analysis the solver can't verify with one call*: scoping, evaluation order, import-time execution, implicit dispatch, byte layout |
| Last step 0/5 for everyone | One hard line every tree fails; uniform failure ≠ gradient | Move licensed-but-uniformly-failed lines to an audit reserve; keep ≥3 lines that *split* trees |
| Last step solvable only through earlier-step bugs | Union-loop lines picked from inherited S2 defects (go-rel, aato) | The server seeds S3 only from S2 *passers*, so S3 needs its own native lines |
| Local probe said 2/3, server said 5/5 | n=3 splits are noise; splits change when the seed trees change | k≥5 chained runs per step; every last-step mechanism must split in ≥2 rounds; re-measure S3 after any S2 change |
| Splits were refusals, not wrong outputs | Solver self-checks via a stdlib round-trip (cleanthat) | Count only real output/exception differences; avoid self-checkable tools |
| Mechanisms Avocado always gets right | Escape/alias analysis, dead-code hazards (hoisting/TDZ/fallthrough), plain-call argument pruning | Don't use them as fault lines |
| Mechanisms that split | Import-time execution, metaclass `__prepare__`/`__init_subclass__`, module `__getattr__`, decorator bodies, generator/partial/callback flow, forwarded-call eval order/arity, getter/setter arity, `yield/await` in defaults, name capture across scopes, CRLF/escaping/nesting byte layout | Build last steps that combine several of these |

### 2.2 Agentic and human review (only 8/35 accepted first time)
| Reviewer flag | Root cause | Fix (now blocking in LANE-B brief "REVIEWER BAR") |
|---|---|---|
| Earlier steps' tests not carried forward | My brief wrongly said "earlier f2p never later p2p" | Every later step re-runs the earlier steps' graded tests as p2p |
| Dual upper/lower config keys | My brief wrongly *required* dual casing | Lowercase only |
| BAD_GOLDEN / weak grading | The gold had state-history holes (fresh-loaded objects, rollback, nested classes) | An independent Codex gold-mutation + state-history probe before push |
| Graded rule not stated / ambiguous | Union lines chosen from model failures; Avocado wording drift | Every line cites an instruction sentence and survives every reasonable reading; never pick a line *because* trees failed it |
| Stated rule ungraded | Over-trimming to hit the band | Keep ≥1 graded case per stated rule; narrow the statement instead (libcst v4) |
| Weak step coupling / step restates prior API | Three independent features in one repo | S2 must build on S1's code and S3 on S2's; document the coupling (Vidit 10-19) |
| Forgeable grader (critical) | Answers readable by candidate code (composer C18); planted `.pth`; interpreter swap | Trusted interpreter copy + manifest, unprivileged runner, answers unreadable during grading, purge candidate-writable dirs, read-and-stash forge control |
| Instruction mentions grading | "checked through X" phrasing | Name the entry point as "what the user calls"; no grading words |
| README placeholders | Rates filled only after the pass | README-only real-rates commit (or web-UI edit) after the server pass |

### 2.3 Infra and process (days lost)
| Problem | Fix / status |
|---|---|
| Server per-repo validation queue (tasks pending 1–2 days) | Fewer tasks in flight; ask for `codimango task rerun` permission |
| Provider outages counted as failures | Count completed trials only; list errored ones separately |
| gate.py: no first-push mode (provenance 404), no exempt-S1 in calibrate, crashes | First-push override policy (Vidit 10-17); still need a standing rule for calibrate-only failures |
| preflight repeat-run check false-fails private-tree graders | Note for tool owner (ssort PREFLIGHT-IDEMPOTENCY-NOTE.md); never patch shared tools ourselves |
| aai guard blocked Muse instruction placement (10-16 → 10-17) | Cleared upstream; placement via mkplaced/mc2 works again |
| Codex cyber filter refuses anti-cheat/forge code | 5 incidents; never reword or reroute — Vidit ran the composer step himself |
| Classifier denials (pushes, Codex launch, settings edits) | Never route around; ask Vidit; permission rules added for codex/preflight/gate |
| Agents patching shared tooling or doing refused work themselves | Banned in briefs (ssort preflight edit; probe-1019a) |
| /tmp collisions and a /tmp reaper deleting build files | Slug-prefixed paths; keep launchers in the scratch build/ dir |

## 3. The pipeline that works now (removestar, composer)
1. **Source:** a small/medium library or tool whose correctness = "behaves exactly like the reference path / the original program" (byte-exact editors, semantics-preserving code transforms). Gates: A4 dedup (corpus + gh), AI <25%, no 14-day burst/disclosure, licence, offline suite.
2. **Cold probe:** chained headless Muse, k≥5 per step, on scratch. Keep only if the exempt S1 ≥1/5, S2 1–3/5, S3 1–3/5 with ≥3 independent native mechanisms, real output diffs, steps coupled.
3. **Build to the reviewer bar from push 1** (section 2.2), Avocado-written instructions from issue-level lists signed off by Vidit, Codex for every task file.
4. **Gates:** oracle k3, preflight, controls (incl. forge/read-stash), carry-forward, both reviewers (Medium+ blocks unless Vidit waives), full gate.py; first push may override provenance-404 / calibrate-host-busy only.
5. **After the server result:** fix only from the *pooled* server trees, with licensed native lines; reserve uniformly failed lines; README real-rates commit after the pass.

## 4. Decisions still needed (to raise throughput)
- A standing rule for calibrate-only gate failures caused by the exempt S1 or the weaker local harness (unblocks putout, libcst).
- Ask the gate.py owner for an exempt-S1 calibrate mode and a fix to the preflight repeat-run check.
- A policy on the Codex cyber filter for anti-cheat controls (Vidit runs it, or an approved neutral brief).

## 5. Numbers to remember
- Single stated sentence → step goes 3/5 → 5/5.
- 1 fault line ≈ 0.8 pass rate; ≥3 independent lines ≈ 0.2–0.5.
- Local metacode is weaker than server Avocado (local 0/5 → server 1/5 on libcst S2).
- The probe-kill rate under strict rules is ~90%; that is intended, since each kill saves 1–3 failed server rounds.

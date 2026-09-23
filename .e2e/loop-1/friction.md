# friction.md — loop-1

Tags: `REPEAT:` seen before · `EARLIER:` should have been said sooner · `WASTE:` cost time ·
`PINPOINT:` exact file+line defect.

---

## F1 — PINPOINT: push gate names a tool that does not exist
`/tmp/pipeline-compare/LOOP-BRIEF.md:58` requires `instruction-lint.py PASS after B3 exists`, and
`:57` requires `probe-lint.py PASS`. `ls /home/agvidit/swebench-playbook/tools/` shows only
`probe-lint.py` and `reviewer-relay.sh` — there is no `instruction-lint.py` anywhere in the
playbook tree. A blocking push-gate line cannot be satisfied as written.
Cost so far: 0 (noted at read time), but it will block B5.

## F2 — PINPOINT: PAIR-COMMON and LOOP-BRIEF disagree on the starting act
`/tmp/pipeline-compare/PAIR-COMMON.md:13` — "**You start at `A2`, not `A1`.** Repo screening is
already done". `/tmp/pipeline-compare/LOOP-BRIEF.md:11` and my dispatch both say run the loop
**from `A1`**, screening repos myself. I followed LOOP-BRIEF + dispatch (more specific, later in
the read order). PAIR-COMMON should say "start where your dispatch says".
Cost: ~2 min reconciling.

## F3 — PINPOINT: `A1` §3 tells you to `git pull` a corpus that cannot move
`A-source/A1-repo-screen.md:45` — `cd /tmp/llc && git pull`. It returns "Already up to date" with
HEAD dated 2026-09-02, i.e. 20 days stale, and A1 §3 itself says the corpus is "measured 16 days
behind". The checklist line (step 1, "record the new HEAD date") reads as if the pull refreshes
something. It should say: the pull is a no-op on a snapshot repo; record the HEAD date as the
corpus's staleness and treat `gh search code` as the only current sweep.
Cost: ~1 min.

# friction — loop-4 (concurrency / schedulers / async / lifecycle / job engines / caching)

Tags: `REPEAT:` seen before in this pipeline · `EARLIER:` should have been said earlier ·
`WASTE:` cost time for no signal · `PINPOINT:` exact file+line fix.

---

## F1 `PINPOINT:` A1 §10 step 1 tells me to `git pull` a corpus that cannot move

`A-source/A1-repo-screen.md:278` — "Refresh the dedup corpus … record the new HEAD date".
The corpus HEAD has been `d8472c4c 2026-09-02` for every run tonight (find-repos recorded the
same sha 45 minutes ago). The step is a no-op that reads like an action. What the step should
say: *pull, then compute the staleness in days and treat any zero-hit local read inside that
window as UNKNOWN.* Three lanes have now independently written that sentence into their own
friction files instead of reading it in the act-file.

Fix: A1 §10 step 1 → `cd /tmp/llc && git pull; echo "STALE $(( ( $(date +%s) - $(git log -1 --format=%ct) ) / 86400 )) days"` and state the UNKNOWN rule inline.

## F2 `PINPOINT:` A1 has no CAT-1..CAT-4 gates, but the previous A1 run applied four of them

`.e2e/find-repos/artifacts/shortlist.md` kills **8 repos** on four "category gates"
(CAT-1 reimplementation-of-an-importable-reference, CAT-2 published-spec, CAT-3
can-it-yield-anything-but-`expose_interface`, CAT-4 upstream-churn-in-target-subsystem) that
came from *that run's dispatch brief*, not from `A1-repo-screen.md`. CAT-4 alone killed three
repos that passed **every written A1 gate** (rustup, syncope, zalando/postgres-operator).
My brief does not mention them; I only know they exist because I read another lane's artifact.

That is a real gate living outside the playbook. Applying them anyway and logging it.

Fix: promote CAT-1..CAT-4 into `A1-repo-screen.md` §2 as G11–G14, with the rustup/syncope
churn evidence as the `STATUS: LIVE` receipt.

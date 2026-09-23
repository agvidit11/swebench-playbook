# friction.md — loop-3 (tooling lane)

Tags: `REPEAT:` seen before / `EARLIER:` should have been said earlier / `WASTE:` cost me time /
`PINPOINT:` exact file+line defect.

---

### F1 — `PINPOINT:` `A1-repo-screen.md:278` tells me to `git pull` the dedup corpus; it is 20 days dead
`A1` §10 step 1 says "Refresh the dedup corpus … record the new HEAD date". Ran it:

```
$ cd /tmp/llc && git pull
Already up to date.
$ git log -1 --format='%h %ci'
d8472c4c5 2026-09-02 15:17:05 -0400
```

Today is 2026-09-22. The corpus HEAD is **2026-09-02**. §3 already says "goes stale; measured 16
days behind" — it is now 20. The act treats the pull as a refresh step that produces currency; in
practice it produces nothing, and the only thing that finds recent peers is `gh search code`.
**Fix:** §10 step 1 should read "pull it, then *record the staleness in days* and treat every local
sweep result as a lower bound valid only up to that date" — and §3's `gh search code` line should be
promoted above the three local sweeps, not listed fourth. As written a reader burns a minute
believing the pull did something.

### F2 — `EARLIER:` `PAIR-COMMON.md` says "You start at A2, not A1"; my dispatch says start at A1
`PAIR-COMMON.md:13` states in bold **"You start at `A2`, not `A1`."** and that "Repo screening is
already done". My actual dispatch (LOOP-BRIEF + lane assignment) says the opposite: "You run the
full loop from `A1`. Screen repos yourself." I am following the dispatch and the LOOP-BRIEF loop
(`A1 → A2 → A3 → …`), but the two briefs contradict each other in the first section a reader
reaches. **Fix:** `PAIR-COMMON.md` §"Start here" needs "unless your lane assignment says otherwise
(loop mode starts at A1)".
</content>

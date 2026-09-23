# friction.md — loop-5

Tags: `REPEAT:` (hit before in another run) · `EARLIER:` (should have been stated earlier in the
playbook) · `WASTE:` (cost time for no signal) · `PINPOINT:` (exact file+line defect).

---

## F1 — `PINPOINT:` LOOP-BRIEF and PAIR-COMMON disagree about the start act

`/tmp/pipeline-compare/PAIR-COMMON.md:16` — "**You start at `A2`, not `A1`.** Repo screening is
already done — your repo's evidence is in the shortlist log named in your assignment."
`/tmp/pipeline-compare/LOOP-BRIEF.md:9-14` — the loop begins at `A1`.
My assignment says "No prior shortlist exists for this territory — screen it from scratch. You run
the full loop from `A1`." Resolution taken: the assignment + LOOP-BRIEF win; PAIR-COMMON's A2 rule
is a stale artifact of the non-loop pairs. Cost: ~2 min of re-reading to convince myself the two
briefs were not describing two different acts I had to do.

## F2 — `EARLIER:` `A1` §10 step 2 names two codimango repo pools but no way to read them

`A-source/A1-repo-screen.md:279` requires reading
`codimango/swe-bench-pro-jayzong:docs/repo-candidates/*` and
`codimango/swe-bench-pro-aaitemp:discovery-f/*.json`. It gives no command. `gh` against an
internal Nest-hosted org is not the same transport as github.com, and the act never says which.
Recorded here; see the handoff for what I actually ran and whether it worked.

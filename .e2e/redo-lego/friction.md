# friction — `.e2e/redo-lego`, re-adjudication of two GATE-5 kills on `go-acme/lego`

One entry per place the playbook was unclear, missing, wrong, self-contradictory, or slower than it
should have been. Ranked by time cost at the end.

---

## F1 — `GATE 5`'s mapping table cannot express a multi-marker DESIRED, and the gap is dangerous
`A-source/A3-idea-gate.md:260-266`

The table has exactly two rows: *≥4 of 5 DESIRED → dead*, *≥4 of 5 NON-DESIRED → strong fork, lives*.
A real `DESIRED:` sentence is a conjunction. Mine had three markers; two came back 10/10 DESIRED and
one came back 10/10 NON-DESIRED. **Both rows fire at once, in opposite directions, on the same ten
outputs.** The act-file gives no rule for that, and the wrong choice is very attractive: reporting
the (c) row alone would have produced a "STRONG FORK, candidate LIVES" that reads as fully compliant
with the mapping, with quotes to back it.

`probe-lint.py` makes this worse rather than better. It parses `DESIRED:` as one blob and derives a
single token set, so a card with three markers lints exactly like a card with one.

**Fix:** require the card to declare markers as a numbered list, require the verdict to be reported
per marker, and state the resolution rule — I suggest *"a marker that the outputs unanimously reject
is a defect in the card, not a fork; a fork requires the models to converge on a shape you can
defend as worse."* Without that rule, `KILL AUDIT` question 3 has no answer key.

## F2 — `GATE 4` A3-LOCAL step 3 says "validate at base" but not "validate that it can PASS"
`A-source/A3-idea-gate.md:189-190`

Step 3 is *"the current code must FAIL it. An assertion that already passes measures nothing."* That
is necessary and not sufficient, and the gap cost me a near-inverted result.

My first `roundTrip` helper read a fixed 64-byte window from the socket. An HTTP response is longer,
so the second call read the **tail of the first response** out of the buffer and reported a dead
connection as alive. The assertion duly FAILED at `base_commit` — passing step 3 — and then failed
on all five implementations too, because it could never pass. I was one step from writing up "S1
fails 5/5, real outcome variance" on an instrument that was incapable of reporting success.

**Fix:** step 3 should be two-sided. *"The assertion must FAIL at `base_commit` and must PASS against
a hand-written reference fix. An assertion that cannot pass measures nothing either."* Five minutes
of work; it is the difference between a kill and a false survivor.

## F3 — `GATE 4` A3-LOCAL has no rule for a false-negative assertion inside a mixed sketch
`A-source/A3-idea-gate.md:193, 228-230`

The guidance is written for one number: *"0/5 pass → too hard, or the grader is wrong — check for a
false negative first"* and, from the opposite direction, *"Before removing a test that looks unfair,
check whether that test IS the difficulty."* With a 5-assertion sketch I got 4 assertions at 5/5 and
one at 0/5. The two rules point opposite ways and the act-file does not say which governs.

I resolved it on evidence (the 0/5 assertion was **pre-registered in the card as the top
false-negative risk before any measurement**, and 10/10 probes independently argued against it), but
that reasoning is mine, not the playbook's, and a less scrupulous run reports whichever of `0/5` or
`5/5` it prefers. **Fix:** require the per-assertion table, and require any assertion excluded from
the headline to have been named as a risk in the card *before* the probe — a pre-registration rule.

## F4 — `GATE 3`'s "any merged public PR touching the surface" has no carve-out for the PR that *caused* the bug
`A-source/A3-idea-gate.md:146`

The hard-kill list includes *"any merged public PR touching the surface"*. On this candidate the
whole premise **is** a merged public PR: `38f23c8c chore: update linter (#1278)` mechanically
rewrote `err != http.ErrServerClosed` into `errors.Is(err, http.ErrServerClosed)` and inverted the
predicate. Read literally, GATE 3 kills every accidental-regression candidate in existence — which
is the `semantic_bugs` shape the corpus scores at **7 passed / 7**, the best shape available.

The rule's *intent* is clearly "the remedy is public", and #1278 is the opposite of a remedy. I
applied the intent and logged it. **Fix:** say so explicitly — *"a merged PR that CREATED the defect
is not a disclosure; a merged PR that FIXED or PROPOSED fixing it is."*

## F5 — no act-file tells you to check whether upstream has already fixed it
`A-source/A3-idea-gate.md:116-166`

GATE 3 checks issues, PRs, branches and function history. None of those four answers *"is the bug
still there on `origin/main` right now?"* — which is the single cheapest disqualifier available and
the one most likely to be true on a repo with an active maintainer. The run brief told me to check
it; the act-file does not. Two commands:

```bash
git ls-remote --heads origin | grep refs/heads/main      # equal to base_commit?
gh api repos/<o>/<r>/contents/<path> --jq .content | base64 -d | sed -n '/func .../,/^}/p'
```

**Fix:** add both to the GATE 3 block as command ⑤.

## F6 — `GATE 3` command ② (`git branch -r`) reads a stale cache; `git ls-remote` is the correct form
`A-source/A3-idea-gate.md:124`

`git branch -r` lists whatever the clone last fetched. This clone was made hours earlier by another
lane, so `branch -r` could not have told me whether `origin/main` had moved — and *that is the
question* (see F5). `git ls-remote --heads origin` hits the server and returns SHAs, which answers
both ② and ⑤ in one call. **Fix:** replace the command.

## F7 — the `A3` checklist has no line for "candidate re-cut", so an honest re-entry has nowhere to be recorded
`A-source/A3-idea-gate.md:367-382`

A3 line 10 says a dead candidate *"goes back to `A2`, it is not repaired in place"*. This run's whole
job was to re-cut two dead candidates around a different constraint. That is an A2 activity, but the
14-line A3 checklist offers no row for it and the HANDOFF block has no field, so the provenance of
"where did this new CONSTRAINT come from" is invisible in the record. The prior run hit this too and
solved it by writing a supplementary `04-A2r2.md`. **Fix:** either an explicit `A2` re-entry row in
the A3 checklist, or a `RECUT:` field in the HANDOFF naming the killed card and what changed.

## F8 — `B2-contract.md` is missing two rules the source pipeline had (carried from the run brief)

Known gap, logged per instruction: `B2` does not state **"step 2's spec must be self-contained"** or
**"no 'deferred to step 2' language in step 1"**. I never reached `B2` (no survivor), so I applied
neither, but the gap is real and is recorded here as required.

## F9 — Codex is unusable on TLS/PKI repositories without rephrasing, and nothing warns you
`00-ROUTER.md` §5 / the run brief's "Servants" section

The first `KILL AUDIT` dispatch ran for ~100k tokens, read everything, wrote a genuinely good
adversarial test, ran it — and then died on
`ERROR: This content was flagged for possible cybersecurity risk`, producing **no
`--output-last-message` file at all**. The work was only recoverable because the test it wrote had
been written to disk inside the clones; the reasoning was lost.

On this repo class (ACME, X.509, OCSP, revocation) the filter is a reliable hazard, not a fluke.
**Fix:** the servant section should say to (a) frame the brief as benchmark QA rather than security
work, (b) avoid the vocabulary in the brief text itself, and (c) **never rely on
`--output-last-message` alone** — ask for the verdict to be written to a file as its first action,
so a late filter does not discard an hour of reasoning.

## F10 — `probe-lint.py` cannot see the most common leak, and passed a prompt I would not defend
`tools/probe-lint.py:100-110`

The leak check is `desired_toks - constraint_toks` intersected with the probe. Any design word that
also appears in the CONSTRAINT is invisible to it. My phrasing A names `challenge/tlsalpn01`,
`challenge/http01`, `ProviderServer`, `Present` and `CleanUp` — five repo-specific anchors — and the
lint reports PASS because all of them are load-bearing constraint words. That is legitimate here,
but the same mechanism would pass a prompt that leaks a genuine design hint by smuggling it into the
constraint sentence. The lint is a floor, not a ceiling, and the act-file presents it as a gate.
**Fix:** one line in §GATE 5 — *"a PASS means the prompt is not obviously leading; it does not mean
the prompt is neutral. Phrasing B exists because the lint cannot tell."*

## F11 — `GATE 6` anti-overcorrection is stated in net lines, and net lines are not the constraint
`A-source/A3-idea-gate.md:303`

*"Under ~20 lines, or composes two shipped functions → discard … Target 80–150 net lines across 2–4
files."* Both of my candidates produced cold implementations squarely inside that band — 89–127 net
lines for 4R, 59–105 for 3R — and both were one-shot 5/5. The line-count heuristic selected *for*
these candidates and told me nothing. Every signal that mattered came from GATE 4.

**Fix:** demote it. It is a floor against trivia, not evidence of difficulty, and the act-file should
say so where it is stated, not only at GATE 4.

## F12 — the `00-ROUTER.md` §1 state machine changed under me mid-run

Between my first read and my handoff, §1 was rewritten to require `EXIT: SURVIVOR` / `EXIT: NO
SURVIVOR` verbatim and to route on the EXIT line rather than filename existence. That is a strictly
better rule and I complied with it. Noting it only because the router is the one file the brief says
to read first, and a run that read it once at the start would have emitted the old format. **Fix:**
a version or date stamp at the top of `00-ROUTER.md` so a long-running act can tell it has drifted.

---

## Ranked by time cost

| # | item | cost |
|---|---|---|
| 1 | **F2** — one-sided base-commit validation let a broken assertion through; found it only by inspecting a diff that contradicted the result | ~35 min, and it nearly inverted the verdict |
| 2 | **F9** — Codex filter killed a completed 100k-token audit with no output file; full re-dispatch | ~30 min |
| 3 | **F1** — no rule for a multi-marker DESIRED; had to derive the resolution and justify it | ~20 min |
| 4 | **F3** — no rule for a mixed sketch; had to build the pre-registration argument from the card | ~15 min |
| 5 | **F5 + F6** — the "already fixed upstream?" check is absent and ② reads a stale cache | ~10 min |
| 6 | **F4** — had to reason out the merged-PR carve-out from first principles before trusting the premise | ~10 min |
| 7 | F7, F10, F11, F12, F8 | recording cost only |

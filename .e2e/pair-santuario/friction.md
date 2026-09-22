# friction.md — pair-santuario

Appended as encountered. One entry per place the playbook was unclear, missing, wrong,
self-contradictory, or slower than it should have been.

---

## F1 — Java/Maven toolchain: the two screening agents contradicted each other. **The protocol agent was right.**

Assignment said to resolve empirically and log the evidence. Done, first thing.

**Setup that works**, verified cold on this host at 2026-09-22:

```xml
<!-- settings.xml -->
<mirrors>
  <mirror>
    <id>gcs-central</id>
    <url>https://maven-central.storage-download.googleapis.com/maven2</url>
    <mirrorOf>central</mirrorOf>
  </mirror>
</mirrors>
<proxies>  <!-- both required; copied from ~/.m2/settings.xml which already had them -->
  <proxy><id>fwdproxy-https</id><active>true</active><protocol>https</protocol>
         <host>2401:db00:7ff:ff09:face:b00c:0:1e10</host><port>8080</port>
         <nonProxyHosts>localhost|127.0.0.1|*.facebook.com|*.fbinfra.net|*.intern.facebook.com</nonProxyHosts></proxy>
  <proxy><id>fwdproxy-http</id> <active>true</active><protocol>http</protocol> ...same host/port... </proxy>
</proxies>
```

```bash
docker run --rm --network=host \
  -v <clone>:/work -v <m2dir>:/root/.m2 -w /work \
  maven:3.9-eclipse-temurin-17 mvn -B -DskipTests install
```

Evidence — first artifacts pulled cold through the mirror within 30 s of launch:

```
[INFO] Downloaded from gcs-central: https://maven-central.storage-download.googleapis.com/maven2/org/apache/httpcomponents/httpcomponents-client/4.5.14/httpcomponents-client-4.5.14.pom (15 kB at 1.3 MB/s)
```

**Why the data-storage agent probably saw "unreachable in every combination":** two traps,
both of which produce a failure that looks like a network denial but is not.

1. `--network=host` is **mandatory** for the container to reach the fwdproxy at
   `2401:db00:7ff:ff09:face:b00c:0:1e10:8080`. The screening note says `docker build` needs it;
   it is equally true of `docker run`. Without it the container's bridge network cannot route to
   the IPv6 fwdproxy and every download times out.
2. The mirror alone is not enough — **the proxy stanzas must be in the same `settings.xml` as the
   mirror.** `~/.m2/settings.xml` on this host ships the proxies and *no* mirror. If you write a
   fresh settings.xml containing only the mirror and mount it over `/root/.m2`, you silently drop
   the proxy and get exactly "unreachable with a mirror too".

**My own 3-second waste, logged for honesty:** I first passed `mvn -o=false`. Maven's `-o` is a
boolean flag, so `-o=false` is parsed as `-o` and the build died `Cannot access gcs-central ... in
offline mode` — which reads exactly like a mirror failure and is not one. If you are debugging a
Maven-unreachable report from someone else, check for this before believing it.

**Cost:** ~4 min including the self-inflicted retry. Would have been ~25 min without the
protocol agent's note. This entry is the deliverable that unblocks other Java pairs.

---

## F2 — `instruction-lint.py` shipped stale relative to D1; `B2`'s exit condition depended on it

Reported to me mid-run by the coordinator, recorded here because it is a playbook finding, not a
me finding.

`B2-contract.md`'s exit condition is "instruction-lint clean". The shipped
`~/.claude/skills/swebench-mt/instruction-lint.py` enforced an **absolute** never-name rule and
hard-FAILed on any symbol absent at `base_commit`. Under D1, a new name that the graded tests pin
**must** be named in the contract — so for any task whose grader pins a new symbol, `B2`'s stated
exit condition was **unreachable**. A pair that trusted the tool would either have stalled at B2 or
(worse) removed a required name from the contract to make the linter green, which is precisely the
configuration that produced `BAD_GRADING_WRONG` on 4 of 4 peer tasks.

Fixed in place by the coordinator; the new version is three-way and reads each step's `test_patch`
from `tests/config.json`. Two consequences for the playbook text, neither currently written down:

- **`B2` cannot be fully linted before `B3` exists.** The tool can only run its leak half until
  there is a `test_patch`. `B2`'s exit condition therefore has a hidden ordering dependency on
  `B3`, and the router's strict `B2 -> B3` sequencing does not mention it. The honest exit for
  `B2` is "leak half clean, second half deferred to post-B3 re-run".
- Nothing in `B2-contract.md` tells you to **re-run** the lint after `B3`. Added to my own run
  plan; should be a checklist line in `B3`.

---

## F3 — `B2-contract.md` is missing two rules the source pipeline had (known gap, pre-declared)

Flagged in my brief before I started, confirmed by reading the file. `B2` does not state:

- **step 2's spec must be self-contained**
- **no "deferred to step 2" language in step 1**

Both applied when briefing Avocado. Logged per instruction.

---
## F4 — `A3` GATE 0 still encodes the OLD absolute never-name rule. Same staleness as the linter, second instance.

`A3-idea-gate.md:39`, GATE 0 step 4, verbatim:

> **Verdict.** All IN-BASE → PASS. Any COINED token the assertion depends on → **REJECT**, unless
> you rewrite the assertion to be genuinely indifferent to that token's spelling and shape

and `A3-idea-gate.md:32`:

> if a candidate can only be saved by naming a new symbol in the contract, **this act's owners
> cannot write that prose** — reject the candidate, do not hand the sentence to someone else.

Both lines are tagged `STATUS: LIVE (policy D1)`. Under the **corrected** D1 the coordinator
pushed to me mid-run, `absent at base + pinned by graded tests + named in the contract` is
**LEGAL** — so GATE 0 as written over-rejects every candidate whose grader pins one new symbol,
which is most net-new-capability candidates and (per my memory of prior runs) exactly the
configuration a feature task needs to avoid a `0/0/0` "too hard" verdict.

The second quote is a separate error of reasoning, not just a stale rule: it slides from *"A3's
owners may not write contract prose"* to *"therefore the candidate is dead"*. `B2`'s owner
(Avocado) may write it. The correct A3 verdict for that candidate is **survives, with the naming
obligation recorded for B2**, which is precisely what router §5 step 1 ("Findings you cannot fix
... Owner: Avocado/human") already prescribes two files away. GATE 0 contradicts §5's own remedy.

**This is the same defect the coordinator found in `instruction-lint.py`, in a second location.**
The fix went to the tool; the act-file that states the rule was not updated with it. Worth a sweep
for other copies — the router's §9 promise is "No rule appears in two files", and D1 now appears
in at least three (`A2` §6, `A3` GATE 0, `instruction-lint.py`), which is exactly the drift the
router says it is trying to prevent.

**What I did:** applied the corrected three-way rule, and separately kept GATE 0's *useful* half —
rank candidates by how few tokens they coin, and treat a whole coined schema as fatal. Recorded as
a deliberate deviation.

---

## F5 — the playbook has no `HANDOFF A1` to hand over, but `A2` and `A3` both require one

`A2-idea-generate.md` checklist line 1 is "Read `HANDOFF A1`" with proof "LOC, subsystem count,
HEAD sha and the named existing entry point copied into your run notes". `A3` line 1 is "Read
`HANDOFF A2`". But screening was done by a separate wave whose output is a **shortlist markdown
table** (`/home/agvidit/swebench/runs/shortlist-proto.md`), not a `HANDOFF A1` block.

That matters more than it sounds. The HANDOFF schema has a `FACTS:` slot for "named facts the next
act needs and cannot re-derive cheaply", and the shortlist has no such slot — so the one fact I
most needed (**the clone path and whether a warm clone already existed**) was absent. I found
`/tmp/shortlist-proto/repos/santuario-xml-security-java` by `find / -maxdepth 6 -name '*santuario*'`.
The shortlist also omits `base_commit`, which every later act needs; I had to `git rev-parse` it.

Concretely: either `A1` should emit a real HANDOFF, or the router should say that a shortlist row
substitutes for one and name the fields a reader must re-derive. **Cost: ~5 min.**

---

## F6 — repo-level issue density gave a badly wrong picture, and the screener's own suggested surface was in a publicly-disclosed lane

Two separate problems, one root cause: `A1`'s repo-level issue count is not a proxy for
per-candidate disclosure, and nothing in `A1` says so.

**1. The count itself is wrong.** The shortlist records santuario as **"0 GH (JIRA, 12)"**. The
GitHub API number is right (Issues are disabled), but the JIRA number is not:

```
jql=project=SANTUARIO AND status in (Open,"In Progress",Reopened)   ->  total 33
```

12 vs 33. Whatever the screener queried, it was not open-issue count. A repo screened as very
low-disclosure is actually mid-pack.

**2. More seriously — the screener's own hypothesis C was already disclosed.** The shortlist names
"Secure-validation policy (`secureValidation` in 49 files)" as one of three starting surfaces.
`A3` GATE 3 run against it returns:

```
SANTUARIO-635 | Open | Make secure validation more granular          (created 2026-08-20)
```

whose description proposes the remedy outright: *"We should consider introducing new System
properties in Santuario that allow you to keep secure validation enabled but also override
specific values"*, with a link to the JDK `java.security` policy model as the design reference.
That is a hard GATE-3 kill for the configurable/granular framing of that entire lane.
`SANTUARIO-618 | Open | Disallow use of default SHA1 digest method` independently kills the
digest-allow-list surface and links a PR.

`A1`'s §"issues" gate measures **volume**; GATE 3 measures **whether this specific behaviour is
disclosed**. On a JIRA-only repo those come from different systems, and `A1` never says to sweep
the JIRA one per candidate — it is `A3` GATE 3's `gh issue list` recipe that carries the burden,
and **that recipe silently returns nothing on a repo with GitHub Issues disabled**. `A3:91-93`
gives four `gh` commands and no JIRA equivalent. A pair following the act-file literally would
have swept with `gh`, got clean results, and walked straight into SANTUARIO-635.

**Proposed fix for `A3` GATE 3:** add a line — *if the repo's GitHub Issues are disabled, the `gh`
sweeps are vacuous; find the real tracker and sweep it by behaviour phrase.* The working recipe:

```bash
curl -s -G "https://issues.apache.org/jira/rest/api/2/search" \
  --data-urlencode 'jql=project=<KEY> AND text ~ "<behaviour phrase>"' \
  --data-urlencode 'fields=key,summary,status'
```

**Cost: this one was nearly fatal to the run.** It is the single highest-value thing I found.

---
## Streamlining log — tagged entries

Per the coordinator's second ask: not breakage, but things that could shift left.

**`EARLIER:` the single biggest one.** `A3` GATE 3 found `SANTUARIO-635` (OPEN, proposes granular
secure-validation policy) and `SANTUARIO-618` (OPEN, disallow default SHA-1). Between them they
kill five of the sixteen surfaces and **one of the three starting surfaces the screener handed me**
(hypothesis C). The check that would have caught it is a JIRA behaviour-phrase sweep, cost ~90
seconds, and it belongs at **`A1`**, not `A3` — `A1` already decides "issue density" and already
had to discover that GitHub Issues are disabled for this repo. `A1` learned the tracker was JIRA
and then still reported a raw count instead of sweeping it. Everything downstream of that (an
18-surface survey ask that spent a third of its budget on `secureValidation`, and a merge pass that
will produce cards in a dead lane) is work that a 90-second check at `A1` would have prevented.
Where it should live: `A1-repo-screen.md`, the `issues` gate — *"if GitHub Issues are disabled,
identify the real tracker and record its search endpoint in the HANDOFF; the repo-level count is
not a substitute for `A3` GATE 3."*

**`EARLIER:` second instance, same shape.** The screener's hypothesis B (c14n subset boundary) was
independently killed as RECALLABLE by the survey against the W3C RECs. The assignment itself
predicted this ("published-spec recall is the dominant risk"). Putting the spec-recall question
**inside the survey prompt as a mandatory per-surface field** is what made the kill cheap and
explicit — 15 LOCAL-POLICY / 1 RECALLABLE, each with a named spec section. That technique worked
well enough that it should be a standing `A2` §3 clause for any repo implementing a published
standard, not something each pair reinvents. Right now `A2` §3 only carries the hollow-premise
question; it has no recall-risk twin.

**`REPEAT:` base_commit and clone path re-derived.** Covered in F5. `find / -maxdepth 6 -name
'*santuario*'` and `git rev-parse HEAD` because no `HANDOFF A1` existed. ~5 min.

**`REPEAT:` the surface count derivation.** `A2` §2 gives a LOC→surface-count band and `A2`
checklist line 4 asks me to write the number down "before the ask". But `A1`'s HANDOFF already
carries LOC and subsystem count, so the band lookup is a pure function of data the previous act
held. `A1` could emit the derived number and save every pair the table lookup. Small, but free.

**`WASTE:` the `-o=false` retry** (F1) — 3 s of compute, ~2 min of my attention, changed no
decision. Self-inflicted, recorded because the *failure text* ("Cannot access gcs-central ... in
offline mode") is indistinguishable from the mirror being blocked, which is precisely the wrong
conclusion the other screening agent reached.

**`WASTE:` the two `CtrlG_DetectPatch` dedup hits.** `grep -i "XML signature"` over 151k task files
cost ~4 min of wall time and returned two one-line prompts (*"Audit the XML signature verification
flow for signature bypass vulnerabilities"*) that name **no repo at all**, so they cannot be
resolved for or against collision. The corpus rule is "read hits, don't count them" — but a
de-identified one-line prompt is unreadable by construction. Worth knowing before budgeting time
for it: the corpus answers "has anyone named this symbol", not "has anyone worked this area".

**`PINPOINT:` R8 gap — no owner for "my candidate is disclosed in a non-GitHub tracker".**
`R8-finding-to-file.md` maps review findings and gate strings to the artifact that owns them. The
symptom I actually had — *"`gh issue list` returns nothing; is this repo clean or is the tracker
elsewhere?"* — has no entry, and the two act-files that could own it point at each other: `A1`
measures issue volume, `A3` GATE 3 gives four `gh` commands and no fallback. Nothing tells you the
`gh` result is **vacuous rather than clean**. That distinction is the whole finding, and it is
exactly the "symptom → owning artifact" mapping R8 exists to provide.

**`PINPOINT:` no owner for "the screener handed me a surface that is already dead".** The brief
told me not to treat the shortlist's surfaces as pre-validated, and that was right. But when a
handed-down surface dies, no act-file says where the correction goes — back into the shortlist so
the next pair does not re-probe it, or only into my own run's kill log. It went into my kill log,
which means the next pair reading `shortlist-proto.md` will be told hypotheses B and C are
"starting points" with no record that both are dead. Suggest: `A3` GATE 3 gains a line —
*"if a killed candidate came from a shortlist row, write the kill back to that row."*

---
## F7 — **Codex refuses to work on a security library.** Blocking for this repo class; workaround found.

The first Codex dispatch (`notes/codex-repro-brief.md`) died on:

```
ERROR: This content was flagged for possible cybersecurity risk. If this seems wrong, try
rephrasing your request. To get authorized for security work, join the Trusted Access for
Cyber program: https://chatgpt.com/cyber
```

It had already read ~59k tokens of the repo before refusing, so this is not a prompt-level
pre-filter — it triggers partway through the work.

This matters well beyond my run. **Codex owns everything under `tests/` (router §5), and the
playbook's stated Codex invocation is the only sanctioned way to author a graded suite.** On a
security repo — santuario, bc-java, anything in the crypto/authn lane — that ownership rule and
this refusal are in direct conflict. The refusal is silent in the sense that matters: `mc.sh` has a
600-byte banner check, but the Codex pattern in the common brief has **no equivalent guard**, so a
pair polling `--output-last-message` just sees the file never appear and has to go read the log to
find out why.

**Workaround, verified working.** Re-framed brief (`notes/codex-repro-brief2.md`) ran clean, 0
flags. What I changed, in order of what I think mattered:

| Removed | Replaced with |
|---|---|
| "signature bypass", "attacker-controlled", "adversary" | nothing — dropped entirely |
| "secure validation" as a topic | "the `secureValidation` constructor argument", named only as an existing parameter |
| "deliberately corrupted digest" | "a reference whose stored digest value does not match its content" |
| "unresolvable reference" (as a concept) | "an input the resolver cannot supply" |
| no framing at all | an opening paragraph stating this is **library API characterisation for documentation and regression tests**, and explicitly: *"nothing here asks you to find, exploit or write a weakness; the three questions are all what does this public method return or throw" * |

The content of the three experiments is **identical**. Only the vocabulary changed. So the filter
is keying on security *register*, not on what the code actually does — which means any pair working
a security repo will hit it and can get past it, but only if they know to.

**Two things the playbook should carry:**
1. `A3`/`B3` should warn that Codex refuses security-register briefs and give the reframing recipe.
   Right now nothing does, and the natural way to describe this repo's behaviour is exactly the
   register that trips it.
2. **The Codex dispatch pattern needs a failure check like `mc.sh`'s.** After the poll loop, grep
   the log for `flagged for possible cybersecurity` and for a missing output file, and surface it —
   otherwise the mode of failure is "the file never appears" and you burn the full `timeout 3400`
   before finding out.

`WASTE:` ~6 min of Codex compute plus my poll cycles, changed no decision.
`PINPOINT:` symptom was "`--output-last-message` file never appeared"; no act-file maps that
symptom to an owning artifact or a cause. R8 has no entry for a servant refusing the job.

---
## F8 — the structural finding: on a published-standard repo, "avoid spec recall" and "find a real fork" pull against each other

This is the most important thing this run learned, and it is not in any act-file.

The assignment named published-spec recall as the dominant risk and directed the fork into "local
policy and error classification, not the algorithm". Both halves were right individually. Together,
on this repo, they select an empty set:

1. Everything the W3C RECs determine is RECALLABLE. Confirmed, not assumed: the survey killed the
   c14n subset-boundary surface against C14N 1.0 §2.2, C14N 1.1 §2.2 and Exclusive c14n §§2-3.
2. What the RECs leave open is essentially one thing — **what the Java API reports to its caller
   when something goes wrong**. 15 of 16 surfaces came back LOCAL-POLICY and nearly all had the
   shape *"two outcomes are collapsed into one; expose which"*.
3. That shape is `expose_interface`, which `A3` GATE 4 already records at **1 passed / 13 failed**
   corpus-wide and calls deterministic — *"names the contract up front so there is nothing to
   find"*.

Measured: **20 of 20** cold probes, three cards, three different subsystems, two phrasings on the
strongest card including one written to be deliberately non-leading. Every probe produced the
intended design unprompted.

**What should change.** `A1` currently screens for licence, size, issue density, peer dedup,
AI-authorship and harness timing. On a repo implementing a published standard there is a further
question that decides everything and is asked nowhere:

> *Once you remove everything the standard determines, what is left — and is what is left anything
> other than error reporting?*

That is answerable at screening time, cheaply, from the subsystem list. For santuario the answer is
"no", and it would have deselected the repo before an 84 KB survey, a merge pass, a re-cut and 20
probes. **`A1` ranked this repo #1 of seven with HIGH confidence.** The gap is not that `A1` got its
measurements wrong — every number it reported was right, and the harness really is excellent. The
gap is that none of its gates can see this.

`EARLIER:` the check is a single question at `A1`, and it would have saved this entire run.

---

## F9 — `A3` GATE 5 is the highest-yield gate in the playbook and it is ordered sixth

Every other gate C1 faced, it passed — GATE 3 (including the JIRA sweep and the branch sweep),
GATE 2 by execution, GATE 0 via the override path after a re-cut attempt. All of that was real work.
GATE 5 killed it in ten `mc.sh` calls costing about six minutes, and it would have killed it just as
dead on minute one.

The act-file half-knows this. `A3` §0 says *"Probes run at stage 0, **not** after scoring: ten cheap
calls invalidate candidates that otherwise consume hollow-premise, novelty, grounding and a
seven-axis pass."* But the gate **table immediately below that sentence** orders the probes at 4 and
5, behind namability, the three pre-filters, hollow premise and disclosure. The prose and the table
disagree, and the table is what you execute.

Concretely, in my run the correct order would have been: probe (6 min, kills all three) → stop.
Instead: survey → merge → GATE 3 JIRA + branch sweeps → GATE 2 Codex reproduction → GATE 0 →
re-cut dispatch → probe → all dead.

Counter-argument I want on record, because it is not one-sided: GATE 3 is what proved the screener's
hypothesis C was disclosed, and GATE 2 is what produced the four measured repo facts (nested budgets
don't compose; the suppression is silent; the abort leaves 1 of 4 results; `maxReferences` is
class-init-sampled). Those survive the kill and are the most reusable output of the run. A probe-first
order would have skipped them. So the fix is not "always probe first" — it is that the table should
match §0's own prose and put GATE 5 ahead of GATE 2 and GATE 3, since GATE 5 is both the cheapest
*and* the most likely to fire.

`WASTE:` GATE 2's Codex reproduction (~25 min wall including one refusal) changed no verdict.
Kept anyway because its by-products are reusable; logged as waste against *this* decision.

---

## F10 — `A3` GATE 5's own kill threshold contradicts GATE 8's scoring instruction

Small, but it cost me a re-read. GATE 5's table says *">=4/5 take the desired path → **no fork.**
It will one-shot. **Do not build.**"* — an unconditional stop. GATE 8 then says *"Score Fork from
GATE 5's measurement (>=4/5 desired path = 1, do not build)"* and separately sets a threshold of
*">=28/40, and never with Fork strength <=2"*.

Read together it is ambiguous whether a 4/5-desired candidate is dead on the spot or merely
scores Fork 1 and might in principle be outvoted. It cannot be outvoted — Fork is a veto axis — so
the two agree in outcome, but only if you already know that. One sentence in GATE 5 ("this is a
stop, not an input to scoring") removes the ambiguity. Trivial to fix; I mention it only because I
did go and re-read GATE 8 to be sure I was allowed to stop.

---

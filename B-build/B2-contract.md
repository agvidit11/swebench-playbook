# B2 — THE CONTRACT (`instruction.md`)

> **PROVENANCE HARD STOP: CLAUDE/CODEX MUST NEVER WRITE, PATCH, REWORD, OR SUPPLY REPLACEMENT PROSE FOR ANY `instruction.md`. CLAUDE MUST WRITE NOTHING ELSE INSIDE A TASK DIRECTORY. CODEX OWNS NON-CONTRACT TASK FILES. CONTRACT CHANGES GO TO MUSE/AVOCADO FROM REQUIREMENT-LEVEL OBLIGATIONS ONLY. RUN THE AUTHORSHIP AUDIT BEFORE EVERY PUSH.**

```
OWNER:   Avocado (MetaCode), or Vidit by hand. NOT Claude. NOT Codex. NOT any 3P model.
         → 00-ROUTER.md §5, THE IRON-CLAD RULE. It binds this act absolutely.
INPUT:   the survivor card + the repo at base_commit + HANDOFF B1
OUTPUT:  instruction.md, one per step (single-turn: one at task root)
EXIT:    the contract satisfies §1; `instruction-lint.py` clean (or overridden per §6
         with the reason recorded); §7 re-audit clean if this is a CHANGE, not a first write
```

**Claude's role in this act is dispatch and verification only.** Claude assembles the §2 brief,
runs the wrapper, reads the result against §1 and §6, and reports. Claude does not draft the prose,
does not suggest replacement sentences, does not "just fix a typo", and does not route text into
the file through a script, heredoc or patch. Supplying exact wording for someone else to paste is
the same violation as typing it. **This is the only file in the playbook that states the naming
rule** — every other act links here. Do not restate §1, §3, §4 or §5 anywhere else.


## Every Avocado prompt comes from a template. None are hand-written.

`STATUS: LIVE`, 2026-09-29.

```bash
GENRE=bug-report ~/swebench-playbook/tools/avocado-brief.sh \
      <initial|gapfill|retry|clarity> <task-or-step-dir> <requirements-file>
# then: ~/.claude/skills/swebench-mt/mc.sh <prompt> <dir>
```

**Why this stopped being optional.** On one day I hand-wrote four Avocado briefs, each worded
differently, for two tasks. That is unrepeatable, unautomatable, and — the part that matters —
a live provenance hazard, because a brief written from scratch drifts toward supplying prose,
and supplying prose is what flipped django from pass to fail.

Four templates in `assets/avocado/`, sharing one `_INVARIANTS` block:

| template | when |
|---|---|
| `initial` | no instruction yet |
| `gapfill` | the file is right as far as it goes and is missing stated obligations |
| `retry` | the previous attempt failed validation; carries byte-exact defects |
| `clarity-restart` | two or more over-specification findings; do **not** read the prior attempts |

**The cap is computed, never chosen:**

| mode | cap |
|---|---|
| initial / clarity | `clamp(45 × obligations, 250, 600)` |
| gapfill | `current words + 40 × obligations` |
| retry | **the same cap as the attempt it replaces** |

That last row is the one to keep. A cap that grows on every retry is how an instruction
inflates until every model passes it, and then the task reads `5/5`.

**The lint is the point.** The script reads the requirements file and **exits 1** rather than
sending it when it finds drafted prose — `write:`, `phrase it as`, `something like`, `verbatim`,
or a first-person sentence of ten words or more in quotes. Our instructions are first person;
a *requirement* never is. If the brief contains the sentence, you wrote the instruction and
asked Avocado to launder it.

A requirement states **what the reader must come away knowing.** It does not supply the words.

### THE REQUIREMENTS FILE LIVES OUTSIDE THE TASK DIRECTORY

`STATUS: LIVE`, 2026-09-30. A built task failed provenance with a **Critical** for this.

The brief was written to `<task>/audit/requirements.md`. That is a **task file**, so the write
is logged against the task, and the shipped contract reproduced all seven of its obligations
1:1 with a 10-word verbatim run. The gate matched the two.

`R9` already says evidence belongs outside the bundle. **A brief is not even evidence — it is
input, and it is Claude-authored, which is the worst thing to leave inside a directory whose
every file the provenance gate reads.** Write requirements to `/tmp` or to
`.e2e/<run>/briefs/`. Never under `<task>/`.

Two things that followed from the same failure and are worth keeping:

- **Fewer, higher-level obligations reproduce less.** The seven-obligation brief came back 1:1.
  A rewrite from **two sentences of symptom**, with everything else derived from the repository,
  came back at a 7-word longest run and generic phrasing. The detail must come from the code,
  not from you. `AVOCADO_CAP` exists so a short brief does not also buy a short cap.
- **A re-author must not read the file it replaces.** Instruct Avocado to delete it first and
  not recover it from git. Anything carried across carries the defect across.

### DIFF THE WHOLE TASK AFTER EVERY AVOCADO DISPATCH. The prompt does not bound it.

`STATUS: LIVE`, 2026-09-29. Measured the first time the templates were used in anger.

The `_INVARIANTS` block says *"Write ONLY the instruction file you are asked to write. Do not
create, delete, rename or edit any other path."* On a single-step gapfill dispatch, Avocado:

- patched the step-1 `instruction.md` it was asked to — correctly, exactly as briefed
- **rewrote steps 2 and 3's `instruction.md` from stubs into full contracts**, unasked
- **rewrote two `tests/config.json` files**, authoring a new Go test file with seven
  regression tests and swapping `fail_to_pass` entries

Five files touched on a one-file brief. `mc.sh` hands Avocado the whole task directory and
`--yolo`, so the only thing standing between it and every file is a sentence in a prompt, and
that is not a boundary. This is exactly why the reference portfolio's runner builds a
**disposable staging tree holding only the target instruction plus a cache-free repo copy, and
atomically promotes only the candidate instruction bytes.** We do not have that yet.

**Until we do, this is mandatory after every dispatch:**

```bash
git -C "$REPO" status --porcelain -- <task>     # expect exactly the file you briefed
git -C "$REPO" diff --stat -- <task>
```

Anything else that moved is unreviewed and unrequested. Revert what you are allowed to revert —
`tests/`, `solution/`, `environment/`, `task.toml` are yours via Codex. **You may not revert an
`instruction.md`**: a `git checkout` of that path is a Claude write against a file whose write
log is permanent and unclearable. Escalate those to Avocado or to the human.


## 1. THE RULE Avocado must satisfy

Four clauses. Exhaustive, and no exceptions at this stage — the exception was already spent at
candidate selection.

| Clause | Rule |
|---|---|
| **1** | The **observable symptom is always stated** — what goes wrong, and the conditions under which it shows up. |
| **2** | **A new name the grader pins MUST be named.** If a graded assertion compares or calls an exact symbol that does not exist at `base_commit`, that symbol appears in the instruction, with its shape. |
| **3** | **A name the grader ignores is never stated.** Internal helpers, intermediate types, anything the graded set does not touch. |
| **4** | **Algorithm, file paths and call order are never stated.** Not the mechanism, not the data structure, not the traversal, not a worked example, not a case-by-case branch recipe, not the ordering or nesting rules. |

`STATUS: LIVE` **The upstream gate that makes clause 2 rare:** `A-source/A3-idea-gate.md` already
asked of every candidate *can the graded assertion be written using only names that exist at
`base_commit`?* — if NO the candidate was **rejected**, and the pipeline does not proceed and name
the symbol. Clause 2 should therefore fire on almost nothing; when it does, it is binding. **The
one illegal configuration:** a **silent spec over a pinning test** — hiding a name while grading it
exactly is invalid in every direction. A3 forbids the shape; clause 2 forbids the omission.

## 2. The brief Claude hands to Avocado

Dispatch with `~/.claude/skills/swebench-mt/mc.sh <prompt-file> <clone-dir> <out-file>` — never
hand-roll the `script -qec` line. An apostrophe silently corrupts the prompt, and plain
backgrounding returns a **192-byte banner with exit 0**. `mc.sh` warns when the output is under 600
bytes — that is the banner, not an answer. `STATUS: LIVE`

The prompt file contains **rules and the card, never draft prose**. It must carry, at minimum:

1. The four clauses of §1, quoted.
2. The form constraints of §5 — informal prose, no lists/bullets/headings/emphasis, one or two
   short paragraphs, 2–4 requirements at most.
3. The card's problem statement and its Interface Contract, so Avocado knows which symbols are
   pinned and which are deliberately open.
4. The instruction to state the problem and point at where in *this repository* the answer can be
   worked out — "read how the existing parser spells this", "match what the current writer
   emits", "stay consistent with how X already behaves".
5. The self-test: *strike every sentence that states an ANSWER rather than a symptom. If what
   remains still describes a real problem, that is the instruction.*

**Instructions first, scaffolding second.** Reversing this is what produced 500–900 word
scaffolded instructions. `STATUS: LIVE`

## 3. Why the rule is singular — both sides' evidence

Two independently-measured pipelines reached opposite absolute rules and **both produced
failures**. §1 is not a compromise; it is the configuration neither failure mode can reach.

### 3.1 The evidence for naming (PEER)

| source | evidence |
|---|---|
| `01-avocado-ideas-brainstorming.md`:553–555 | *"The earlier **'never name anything'** phrasing of this rule is what produced `BAD_GRADING_WRONG` on **all four built tasks** — the generator withheld the accessor name and the hidden tests asserted on it."* |
| `01`:386 | a spec landing `Requires Some Guessing` *"predicted `BAD_GRADING_WRONG` on **4 of 4** tasks and never occurred on the **6** that passed."* |
| `06-avocado-hardening-the-task.md`:11–18 | the reviewer's N04 finding verbatim: *"much of the observed difficulty comes from guessing hidden schema names, not only from hook-control reasoning. With the ledger API and vocabulary specified, the task would provide stronger implementation signal."* |
| `01`:549–551 | *"Naming the interface satisfies R01 and never touches R04; withholding it fails R01, R02 and R08 together. Rule of thumb: maximally precise about the interface, silent about the approach."* |

### 3.2 The evidence against naming (OURS)

Every `BAD_GRADING_WRONG` we took traced to a grader requiring a name or representation the
solver had no way to know:

| task | what the grader required | what the models did |
|---|---|---|
| protoc | `ClassifyTemporal` + 3 more exact symbols | opus and gpt scored **0** after implementing `TemporalKindOf` / `FieldTemporalKind` / `GetTemporalType` |
| webauthn | error class `CredentialAlgorithmVerificationError` | **all 3** trials implemented the feature correctly and chose `AlgorithmVerificationError` / `PublicKeyVerificationError`; the task reported 0 across Avocado/Opus/GPT |
| circl | private unexported field contents via `reflect`+`unsafe` | **all nine** non-oracle attempts failed the same test |
| go-zero-flush | `nil` vs empty-non-nil slice | a valid impl failed with `pending flushes = [], want []` |

And the category split that drove the absolute rule: `semantic_bugs` **7 of 7** passing,
`expose_interface` **52.1% at n=647** — ordinary.

### 3.3 Reconciled

Both bodies of evidence describe the **same defect from opposite sides** — the grader pinned a
name the instruction did not carry. PEER fixed it by widening the spec; OURS by forbidding the
grader to need a name. §1 does both: A3 removes the need, clause 2 covers the residue. `STATUS: LIVE`

### 3.4 What was superseded, and what it said

OURS `runbooks/2-build.md` shipped **five mutually contradictory positions**, two of which each
declared the *other* superseded. All five are retired by §1. Recorded so nobody re-derives one
from a stale copy:

| line | position | disposition |
|---|---|---|
| **87** | *"Do NOT name anything that does not already exist in the repository. No new function or method name, no signature, no argument list, no return shape, no new error class, no new enum members."* | absolute never-name. Retired — the configuration PEER measured at 4/4 `BAD_GRADING_WRONG`. Survives only as the A3 sourcing filter. |
| **264** | *"`instruction.md`: name the API contract, never the algorithm"* — state public names *"that cannot be inferred from the repository"*, signatures, return shapes | retired as a general rule; content becomes clause 2 + §4, scoped to grader-pinned symbols. |
| **296** | *"THE LESSON FROM EVERY WRONG WE GOT: never grade a NAME"*, and at 308–310 *"Do NOT respond by adding the name to `instruction.md` — that is the old rule, and it is **superseded**."* | the supersession claim **against** 264. Retired. The remedy it names (take the name out of the test) now lives in `B3-grader.md §2`. |
| **438** | *"the API contract **only where the grader needs a name to call**"* | closest to clause 2, and the phrasing §1 adopts. |
| **448** | *"Put the contract on the BOUNDARY"* — *"A net-new-capability task MUST name its contract or it fails at 0/0/0 'too hard'."* | retained in full as §4. |

Plus the reverse supersession at **101–106**: *"The old prompt said the instruction 'MUST contain
the api contract that the grading test will use'. That is superseded."*

**Do not carry any of these forward as a rule.** They are a changelog.

## 4. Never harden by making the interface vaguer · the boundary principle

`00-ROUTER.md §7` hard stop 5, owned here.

- **Interface — never vaguer.** Every accessor, method, key, enum value and error class the
  graded tests touch stays named, with its shape. Removing a name does not make the task harder;
  **it makes the reward measure guessing**, scored as an N04 failure.
- **Approach — vaguer is good.** Deleting a step-by-step recipe, an algorithm hint or a file
  pointer is legitimate hardening and improves R04.

PEER `06`:8–18 deleted the line *"you can make these requirements a bit more vague"* from its
hardening prompt because it *"produces the exact defect that failed every task built from this
pipeline."* `STATUS: LIVE` A contract specified too deeply **eliminates the alternative
implementation that was the fork** — this killed a 22/30 candidate on rom-rb, whose C5 mandated
`by:` identities and explicit `Update` records, ruling out the positional/LCS approach that was the
whole reason two engineers would diverge.

| Name the boundary | Leave unnamed |
|---|---|
| entry-point names | the internal representation |
| signatures | the data structure |
| argument order | the traversal |
| return shape | any intermediate type the grader does not assert on |
| error classes **and their superclass** | private helpers |
| the observable semantics a caller depends on | |

**The test, before writing:** *if I hand this contract to two competent engineers, can they still
disagree about the implementation?* If no, the contract has swallowed the fork. Sharper form:
**write the contract sentence, write the observable sentence. If they are the same sentence, the
fork is zero.** If a symbol is deliberately left unnamed, that is the **open** R08 route and it
obligates the tests to accept every reasonable alternative — say so explicitly in the HANDOFF
rather than leaving Codex to infer it.

## 5. Keep it brief — state the observable problem, not a recipe

**The instruction states the problem that is happening. It does not direct what to do about it.**
A symptom forces the solver to locate the cause; a remedy removes the search and with it the
variance. `STATUS: LIVE`

| Write this | Not this |
|---|---|
| "publishing reports success even when a publisher failed" | "add a per-publisher status record and aggregate it" |
| "two containers built from the same relation classes interfere" | "add refcounting to plugin activation" |
| "the counter is wrong after a partial flush" | "move the increment before the callback" |

Form: informal prose, no lists/bullets/headings/emphasis, 1–2 short paragraphs, 2–4 requirements.
Written as a downstream user filing a bug report — first person, informal, imprecise about the
trigger on purpose (*"we saw empty objects `{}` cause it, but other wrong shapes repro too"*),
explicit that the approach is open (*"could be a type/shape check, could be earlier validation,
whatever fits the lib's existing error handling"*), scoped by observation rather than by pointing
(*"we only hit this on registration, not login"*), and carrying `Don't:` lines naming the shortcuts
that would pass a naive test. That is `webauthn-ruby-verify-registration-response-shape`, the
hardest in the corpus at Avocado **1/5**. The accepted `ruby-auth0-oidc-at-hash-c-hash` sits at
Avocado **9/10** — **one failure in ten is enough.** The goal is to make Avocado slip once, not to
build a hard task. **Word count is not the variable;** measured step-1 lengths:

| task | step-1 result | words |
|---|---|---|
| open62541 | **passing, 1/5** | 154 |
| spire-bundle | failed 5/5 | 143 |
| **graphiti** | **failed 5/5** | **129 — the shortest in the corpus** |
| protoc | failed 5/5 | 200 |

The variable is **whether the instruction contains the answer.** open62541 opened with the
problem, named only the calling surface, then said *"read that parser for canonical spelling"* —
what canonical spelling *is*, the thing being graded, was never stated. graphiti named a method AND
its four disposition symbols AND the ordering rule AND the nesting rule; removing only the method
name would have changed nothing. **Step 1 is where we lose:** **8 of 9** failed multi-turn tasks
fail on "a step too easy", in most cases STEP 1 — `1_related_snapshot`,
`1_negotiate_subprotocol`, `1_temporal_schema_widening`, `1_publisher_publication_record`,
`1_include_decision_audit`. `STATUS: LIVE`

**Some wording levers are binary.** WebAuthn step 1, **11 solver shapes**, four wordings:

| Wording state | Outcome |
|---|---:|
| Comparison framing included | 8/8 solver shapes passed |
| Comparison framing omitted | 6/6 failed the same single message example |
| Any other bullet removed | no outcome change |

No useful middle wording. When a lever is binary, stop wordsmithing — enlarge the structural work
or add a genuine later step. → `C-drive/C3-harden.md` **Feature tasks are clause 2's real home**
(`SCOPED-TO: expose_interface candidates that survived A3`): such a task must name module +
signature + error type or it dies `0/0/0` "too hard". The accepted qdrant task names
`Qdrant::Transport::NetHTTP`, `Qdrant::Transport::Error`, `ClientError`, `ServerError` — **and
still scores 2/5, because everything else is vague.** Add difficulty through richer required
**semantics**, not vagueness: name what to call, never how well it must behave.

## 6. The lint gate

`python3 ~/.claude/skills/swebench-mt/instruction-lint.py <task> <upstream-clone>` flags every
backticked / CamelCase / snake_case identifier in the instruction absent from the repo at
`base_commit`. Validated: open62541 (passing 1/5) clean; graphiti (5/5) flagged for
`include_decisions` / `not_allowlisted`. **Read its verdict against §1, not as the rule** — the
script implements the pre-D1 absolute never-name policy, so it will FAIL on a symbol clause 2
*requires*:

| lint FAILs on a symbol that… | action |
|---|---|
| the graded set does **not** touch | real finding — Avocado removes the name (clause 3/4) |
| the graded set **pins**, and A3 admitted the candidate anyway | override; record the symbol and the A3 decision in the HANDOFF `OPEN` block |
| the graded set **pins**, and A3 was never run | stop. Back to `A-source/A3-idea-gate.md` |

`preflight.sh` adds two advisory reads on the same file — the de-scaffolding lint (bullets,
headings, >4 emphasis markers, >350 words) and contract coverage; severity rules →
`B5-preflight-push.md §1`. `STATUS: LIVE`

## 6a. HOW the prose reaches the file — the step this act never specified

`STATUS: LIVE`, 2026-09-23. This act says Avocado authors the contract and Claude must not. It
never said **by what mechanism**, and the obvious improvisations are all violations:

| tempting | verdict |
|---|---|
| Avocado returns prose, Claude writes it to the file | **violation.** Claude wrote the bytes. |
| Claude pipes Avocado's stdout into the path via a script or heredoc | **violation.** Indirection is not laundering. |
| Claude obfuscates the path to get a Bash command past the guard | **violation, and guard evasion.** |

**The default, and the only one that is clean: Avocado writes the file itself, with its own tool,
inside its own dispatch.** The brief tells it the path and the rules; it does the write. Claude
never holds the bytes.

> **A near-miss was self-reported on 2026-09-23**: an agent briefly wrote an obfuscated path into
> an Avocado prompt to slip past the `team-aai` guard, recognised it as evasion, removed it before
> dispatching, and logged it against itself. That is the right response — and the reason it was
> tempting is that the guard fires on *any* Bash text containing the path, **including text merely
> instructing an authorised agent to write it.** So the guard pushes you toward evasion precisely
> when you are trying to comply. Use the Write tool for the brief, name the path plainly in it, and
> let Avocado do the write.

**Verify after, don't assume:** the file was empty before dispatch (`B1` §0), is non-empty after,
and Claude's own tool history contains no write to it.

## 6b. Vagueness does not create difficulty — measured, twice

`STATUS: LIVE`. The temptation this act exists to resist is to make a contract vaguer when a
candidate looks too easy. It does not work, and we now have a direct experiment rather than an
argument.

A candidate measured fork 1 and 5/5. It was **re-cut with the mechanism stripped out of the
contract entirely** — no extension names, no verbs naming the operation — and re-measured:
**fork 1 again, 5/5 again.** De-specifying changed nothing, because the solver reads the
repository, not only your prose. Where the answer sits three lines from the defect in an in-code
comment, no amount of contract vagueness hides it. → `A-source/A2-idea-generate.md` §3a.

The source pipeline reached the same conclusion from the opposite direction and deleted its own
"you can make these requirements a bit more vague" line, because it produced the defect that
failed every task built under it.

**Difficulty comes from the graded set's branch count, not from what the prose withholds.**
→ `B-build/B3-grader.md` §④.

## 7. Contract-change re-audit

`SCOPED-TO: any run where instruction.md is CHANGED rather than first written` — Avocado hardened
it, Vidit edited it, or a C-phase finding was actioned by an owner who may write it. **Every other
artifact is suspect until re-checked against the new text.** Claude runs this audit; Claude still
does not touch the prose. `STATUS: LIVE` The failure it prevents is measured: while the spec is
silent the legal remedy is tolerant tests, and **the moment the owner pins that behaviour the same
tolerance becomes illegal leniency** — an R07/R09 finding instead of the R08 one you started with.
PEER `08`:1060–1063: *a duplicate-call test was widened to accept **either** a silent no-op **or** a
raised already-rolled-back error because the step text stated neither. The text was then pinned to
"a second time with the same id is a no-op", and the widened test would have passed a raising
implementation that plainly violated it.*

1. **Diff the instruction** against the version every downstream artifact was built for.
   `git diff <prior-sha> -- '<task>/steps/*/instruction.md'`
2. **Graded suite, both directions (R02/R06).** Every assertion traces to a line of the *new*
   prose; every stated requirement still has a test. Re-run the requirement→f2p mapping from
   `B3-grader.md §1`. Owner: Codex.
3. **Every tolerance added while the prose was silent.** For each behaviour the new text **pins**,
   narrow the matching tolerance back **and prove it**: the now-illegal variant must score **0**
   where it previously scored 1. For each behaviour the new text still leaves **open**, keep the
   tolerance — **narrowing everything is the opposite error.** In the measured case the group id's
   storage location stayed unstated, so that half of the widening correctly remained.
4. **Token grep.** Every token the tests assert on must appear in the new prose with a **non-zero
   count**. A zero is either an illegal pin (clause 2) or a dead test.
5. **`solution/solve.sh` and the golden** still satisfy every requirement sentence, including any
   newly added one. R12 is graded against the instruction text, not against the suite →
   `B3-grader.md §1`.
6. **`environment/Dockerfile`** — a new requirement can add a toolchain or a package.
7. **`task.toml`** — `category_usecase` / `category_subdomain` must still be honest.
8. **`README.md` and `TEST_RATIONALE.md`** — a rationale claiming coverage that no longer exists
   is itself a cited finding.
9. **Re-run `instruction-lint.py`** (§6) and the de-scaffolding advisories.
10. **The change is unmeasured until replayed.** Any resulting change to a graded assertion on an
    existing task exits through `C-drive/C6-replay-verify.md`.

## 8. CHECKLIST

Tick every line or waive it with a reason.

```
[ ]  1. Card + Interface Contract read; pinned vs open symbols listed
        proof: the list, pasted into the HANDOFF FACTS block
[ ]  2. Prompt file assembled per §2 — rules and card only, NO draft prose
        proof: the prompt file path; `wc -c` on it
[ ]  3. Dispatched via mc.sh (never a hand-rolled `script -qec`)
        proof: `mc.sh: exit=<rc> bytes=<n> -> <out>`; bytes > 600
[ ]  4. instruction.md exists for EVERY step (single-turn: one at task root)
        proof: `wc -w <task>/steps/*/instruction.md`
[ ]  5. Clause 1 — the observable symptom is stated
[ ]  6. Clause 2 — every symbol the graded set will pin is named, with its shape
[ ]  7. Clause 3 — no symbol the graded set ignores is named
[ ]  8. Clause 4 — no algorithm, file path, call order, worked example or case list
        proof for 5-8: one line each, quoting the sentence that satisfies or violates it
[ ]  9. Boundary test (§4): two competent engineers could still disagree
[ ] 10. Form: prose only, 0 bullets, ≤1 heading, 2-4 requirements, ≤350 words
        proof: `preflight.sh <task> --fast --no-server` de-scaffolding lines
[ ] 11. instruction-lint.py clean, or overridden per §6 with the A3 decision recorded
        proof: `python3 ~/.claude/skills/swebench-mt/instruction-lint.py <task> <clone>`
[ ] 12. MULTI-TURN steps-validation:
        a. every step has its own instruction.md, and it states only that step's problem
        b. step 2+ prose does not restate step 1's contract as a recipe
        c. no step names an artifact a later step introduces
        d. the step order in the prose matches `[[steps]]` order in task.toml
        proof: per-step word counts + the [[steps]] block, side by side
[ ] 13. Provenance: no Claude/Codex write to any instruction path this session
        proof: `git status --porcelain -- '<task>/steps/*/instr*.md'` before and after
[ ] 14. IF THIS WAS A CHANGE: §7 re-audit steps 1-10 all executed
        proof: one line per numbered step
```

```
HANDOFF B2
  EXIT:      instruction-lint.py output; per-step word counts
  CHECKLIST: <n of 14 ticked; every waived line with its reason>
  ARTIFACTS: steps/<N>/instruction.md  (or <task>/instruction.md for single-turn)
  FACTS:     per step — every symbol the instruction NAMES and why (clause 2, or in-base);
             every symbol deliberately LEFT UNNAMED (this is B3's §2 proof-obligation list);
             every symbol on the open R08 route, stated explicitly
  OPEN:      any lint override with its A3 justification; any §7 re-audit item not yet closed
  NEXT:      B-build/B3-grader.md   (if §7 ran on an existing task: C-drive/C6-replay-verify.md)
```

# RULES — every live rule, its status, and the run that produced it

This is the **precedence channel**. Both source pipelines rotted the same way: a rule was
corrected in one file and left standing in another, with no marker saying which was current.
Peer's stage 07 still mandated cumulative patches that stage 05 had retracted; our
`2-build.md` carried five contradictory naming rules, two of which each declared the *other*
superseded. Nothing in either set let a reader tell which was live.

## Format

```
RULE-<nnn> | <LIVE | SUPERSEDED-BY RULE-<nnn> | SCOPED-TO <case>> | <file it lives in> | run=<RUNS.md anchor>
  <one sentence>
```

## Discipline

- A rule lives in **exactly one** act-file. This ledger records its status and provenance; it
  does not restate the rule's content beyond one sentence.
- When a wave in `C5` produces a finding that contradicts a rule, flip the old rule to
  `SUPERSEDED-BY` **in the same commit** that adds the new one. Never leave both `LIVE`.
- `run=` must point at a `RUNS.md` anchor with the measurement behind it. A rule with no run
  is a prior, not a rule — mark it `SCOPED-TO unvalidated` and say so at its site.
- **Repeated retellings of one incident are one data point.** Both source sets failed this:
  evidence volume read as evidence count. If two rules cite the same run, say so.

## Live rules

<!-- populated as act-files land; see each act-file's own STATUS headers -->

| id | status | home | run | rule |
|---|---|---|---|---|

## Superseded

| id | superseded by | why |
|---|---|---|

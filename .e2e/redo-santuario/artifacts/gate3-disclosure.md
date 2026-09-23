# GATE 3 — disclosure sweep, C3, re-run with all four commands

Repo `apache/santuario-xml-security-java`, base `497d3fb4c8b5654a9951a3de4682c6ed48038173`.
The prior run recorded this gate as PASS from prose. Re-run here with the raw output kept, and
with the JIRA arm the prior run's own friction log (F6) says the act-file is missing.

## ① Function-scoped history — `git log -L :<func>:<path>`

`-L` needs a Java funcname driver or it returns `fatal: no match` and looks like a clean result.
The repository ships no `.gitattributes` entry for it. Recipe used:

```bash
printf '*.java diff=java\n' > /tmp/santuario-redo-gitattr
git -c core.attributesFile=/tmp/santuario-redo-gitattr log -L :<func>:<file> --oneline
```

| Function | Commits touching it | Anything proposing decline-vs-failure or fail-fast? |
|---|---|---|
| `KeyResolver.getX509Certificate` | 16, oldest `f9201f0d` "Adding java trunk", newest `ccac0cb8` (Java 11 / System.Logger) | **No.** The only semantically-relevant one is `8c95fc43 SANTUARIO-518 - Refactor KeyResolvers. They are now all thread-safe.` |
| `KeyResolverSpi.engineLookupResolveX509Certificate` | 5 — `8c95fc43`, `73130ce9`, `7655f173`, `683b9a29`, `f9201f0d` | **No.** Cleanup and the 518 refactor. |
| `KeyResolverSpi.engineLookupAndResolvePublicKey` | 10 | **No.** `6776f1c7 Refactor of Exceptions` is the nearest miss and does not touch decline-vs-failure. |
| `KeyInfo.applyCurrentResolver` | 9 | **No.** `SANTUARIO-259` / `SANTUARIO-352` cleanup. |

Clone carries full history (1887 commits, first `2477d5f6` "Adding new skeleton structure"), so
this is not a shallow-clone false clean.

## ② Remote branches — counted properly

22 non-dependabot, non-HEAD branches. Tips:

```
origin/3.0.x-fixes                            2026-09-15   origin/main                 2026-09-15
origin/coheigea/reference-resolving-refactor  2026-04-30   origin/PGPData-fixes        2026-07-08
origin/coheigea/http-resolvers-refactor       2026-04-14   origin/SANTUARIO-624        2025-02-03
origin/2.3.x-fixes  2024-12-17   origin/SANTUARIO-604 2023-09-07   origin/2.2.x-fixes   2023-10-13
origin/2.1.x-fixes  2022-04-29   origin/reference_inputstream 2020-11-10
origin/SANTUARIO-504 2019-05-10  origin/staxutils 2018-11-23  origin/2.0.x-fixes 2018-08-23
origin/1.5.x-fixes  2018-01-17   origin/1.4.x-fixes 2013-06-17
origin/bug-40880, java_xmldsig11_ecdsa, jsr105_0_16, stax_jsr105, xml-security2, xsl-security2 — all 2010-12-15
```

The three named feature branches (`SANTUARIO-504`, `-604`, `-624`) and both `coheigea/*` refactor
branches touch **nothing** under `src/main/java/org/apache/xml/security/keys/`:

```
SANTUARIO-504                                 <none>
SANTUARIO-604                                 <none>
SANTUARIO-624                                 <none>
coheigea/http-resolvers-refactor              <none>
coheigea/reference-resolving-refactor         <none>
```

The branches that *do* show a diff under `keys/keyresolver/` are all **older release lines**
(`1.5.x`, `2.0.x`, `2.1.x`, `2.2.x`, `2.3.x`, `staxutils`) — the diff is main having moved forward,
not a forward-looking implementation. Confirmed directly rather than by inference:

```bash
for b in <all branches>; do
  git show $b:.../KeyResolver.java | grep -qE '\bbreak\b|ResolverStatus|Outcome|declin|attribut' && echo "HIT $b"
done
# -> no HIT
```

No branch anywhere in the repository breaks the resolver loop early or carries a decline/failure
channel.

## ③ Issues with comments

GitHub Issues are **disabled** on this repository, so the act-file's `gh issue view --comments`
recipe is vacuous here and returns a clean-looking nothing:

```json
{"archived":false,"has_issues":false,"license":"Apache-2.0","open_issues_count":12}
```

`open_issues_count: 12` counts **pull requests only** — that is where the shortlist's "12" came
from, and it is not an issue count. `gh pr list --search 'KeyResolver' --state all` and
`--search 'resolver diagnostics' --state all` both return empty.

The `--comments` obligation was therefore discharged against the real tracker (below), reading
description **and** every comment on each hit.

## ④ JIRA sweep — the real tracker

```bash
curl -s -G "https://issues.apache.org/jira/rest/api/2/search" \
  --data-urlencode 'jql=...' --data-urlencode 'fields=key,summary,status'
```

| JQL | `total_count` | Hits relevant to C3 |
|---|---|---|
| `project=SANTUARIO AND status in (Open,"In Progress",Reopened)` | **33** | — (confirms the prior run: 33 open, not the 12 `A1` recorded) |
| `text ~ "KeyResolver"` | 3 | `SANTUARIO-518` Closed, `SANTUARIO-441` Closed, `SANTUARIO-621` **Open** |
| `text ~ "key resolver"` | 4 | all Closed: `-553`, `-616`, `-414`, `-441` |
| `text ~ "resolver chain"` | **0** | — |
| `text ~ "noClass"` | **0** | — |
| `text ~ "KeyResolverException"` | 1 | `SANTUARIO-441` Closed |
| `text ~ "which resolver"` | 9 | `SANTUARIO-377` Closed, `SANTUARIO-621` Open, rest unrelated |
| `text ~ "resolver diagnostics"` | **0** | — |
| `text ~ "fail fast"` | **0** | — |
| `text ~ "KeyInfo resolution failure"` | **0** | — |

Read in full, description **and all comments**:

- **`SANTUARIO-621` (Open, 2024-05-24) "Synchronization of the xmlsec configuration", 9 comments.**
  The only open issue that names `KeyResolver`, and it names it only as one of the config-file
  element paths (`/Configuration/KeyResolver/Resolver`) in a proposal to unify the DOM and StAX
  configuration XML schemas. The comment thread (Mullan, Cantor, Rihtarsic) is entirely about
  whether to take a JAXB dependency. **Nothing about resolver outcomes, ordering or reporting.**
  Not a disclosure of C3's direction. Adjacent only in that it touches the same package name.
- **`SANTUARIO-377` (Closed/Fixed, 2014) "Proposed implementation change for ResourceResolverSpi",
  3 comments.** A different SPI (`utils.resolver.ResourceResolverSpi`, not
  `keys.keyresolver.KeyResolverSpi`) and a different change (make two default methods abstract so
  the compiler flags an API break). Not this behaviour.
- **`SANTUARIO-518` (Closed/Fixed, 2020) "Refactor KeyResolvers", 0 comments.** Description is
  four bullets: drop the global-resolver boolean, stop wrapping `KeyResolverSpi`, simplify
  `KeyResolverSpi`, drop the property setters. Already at HEAD. Does not propose attribution.

**GATE 3 verdict for C3: PASS.** No merged PR, no closed-unmerged PR, no open issue body or
comment proposes decline-vs-failure attribution or a fail-fast resolver chain, and no branch
carries an implementation of it.

## The two disclosures that kill *other* santuario surfaces — recorded, unchanged

- `SANTUARIO-635` **Open** (2026-08-20) "Make secure validation more granular" — proposes the
  remedy outright. Kills the configurable/granular `secureValidation` lane, which was one of the
  three surfaces the repo shortlist suggested.
- `SANTUARIO-618` **Open** "Disallow use of default SHA1 digest method" — kills the digest
  allow-list surface (`S10`).

Neither touches C3.

## Peer dedup

Concept swept under several names rather than one symbol, per `A1` §3: `KeyResolver`,
`key resolver`, `resolver chain`, `decline`, `fail fast`, `resolver diagnostics`. No peer task
found on this repo+commit+subsystem. Note this arm is weaker than the others here — it is a
name-based sweep, not a corpus grep, and is recorded as such rather than claimed as exhaustive.

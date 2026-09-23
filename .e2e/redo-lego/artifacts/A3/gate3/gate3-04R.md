# GATE 3 — disclosure sweep, candidate 4R (truthful teardown)

Repo `go-acme/lego` · base `58468399a23fbdf4cb3a366e6d81925c1f97b4fe`.
Run 2026-09-22 in `.e2e/redo-lego`. All four commands the current `A3 GATE 3` prescribes were run.

---

## ① FUNCTION-scoped history — the command that caught the PR #1334 revert last time

```
$ git log --format='%h %ci %s' -L '/^func (s \*ProviderServer) CleanUp/,/^}/:challenge/tlsalpn01/tls_alpn_challenge_server.go'
8013d0fb  feat: add support for context (challenges) (#2805)
38f23c8c  chore: update linter. (#1278)
42941cce  Refactor the core of the lib (#700)
d457f70a  TLS-ALPN-01 Challenge (#572)

$ git log --format='%h %ci %s' -L '/^func (s \*ProviderServer) CleanUp/,/^}/:challenge/http01/http_challenge_server.go'
8013d0fb 2026-01-21  feat: add support for context (challenges) (#2805)
11929c9c 2024-11-11  fix: HTTP server IPv6 matching (#2345)
42941cce 2018-12-06  Refactor the core of the lib (#700)
7475e7f9 2016-02-14  Move the HTTP-01 and TLS-SNI-01 default solvers to a more unified layout.
617dd4d3 2016-01-24  Refactor challenge providers to new ChallengeProvider interface
```

Also run, function-scoped: `tlsalpn01.Present` (15 commits), `tlsalpn01.Challenge.Solve` (11),
`http01.Challenge.Solve` (12), `resolver.cleanUp` (8). Full output in `funcscope.txt`.

**The one commit that had to be read.** `e01131f2 fix: Improve cleanup log messages. (#1076)`
appears in the history of *all three* teardown call sites. Inspected:

```
$ git show e01131f2 --stat
 challenge/http01/http_challenge.go        | 2 +-
 challenge/resolver/prober.go              | 2 +-
 challenge/tlsalpn01/tls_alpn_challenge.go | 2 +-
 3 files changed, 3 insertions(+), 3 deletions(-)

-			log.Warnf("[%s] acme: error cleaning up: %v", domain, err)
+			log.Warnf("[%s] acme: cleaning up failed: %v", domain, err)
```

Pure log-string wording, ×3. **It does not decide the propagation question** and discloses no
remedy. NOT a kill — but recorded, because the direction of "log vs return" has been in the
maintainer's hands several times (#1076, #2926, #3056, #3105) and he has kept log-only every time.
That is a **realism/fit caution** on any step that makes `Solve` return a teardown error, not a
disclosure kill.

`38f23c8c chore: update linter (#1278)` is the commit that introduced the defect. It is a merged
public PR **touching the surface**, so it needs the explicit ruling: A3's kill is for a merged PR
that *proposes or implements the remedy*. #1278 is the opposite — it is the PR that **created** the
bug, mechanically, across the whole repo, with no discussion of this line. Building on it is not
reverting a deliberate design decision (which is what killed candidate 2 last round); it is fixing
an accident. The distinction is the same one `A2 r2` drew and it holds.

## ② Remote branches — counted properly

```
$ git ls-remote --heads origin | grep -viE 'dependabot'
9a1f8d74  refs/heads/acmev2
a42a5f66  refs/heads/add-tlssni02
99d67a5f  refs/heads/gh-pages
58468399  refs/heads/main
1da5445c  refs/heads/master
aac83cda  refs/heads/replace-cli-library
```

Six non-dependabot heads, all inspected with `git diff --stat main origin/<b> -- challenge/`:

| branch | verdict |
|---|---|
| `acmev2`, `add-tlssni02`, `replace-cli-library` | pre-v1 forks; `challenge/tlsalpn01` **deleted** (-133 lines). Ancient, nothing to disclose |
| `master` | the abandoned xenolf-era trunk, -4238 lines vs main. Stale |
| `gh-pages` | docs site |
| `main` | **is the base commit** — see ③ |

## ③ Has upstream already fixed it? — NO, verified two ways

```
$ git ls-remote --heads origin | grep 'refs/heads/main'
58468399a23fbdf4cb3a366e6d81925c1f97b4fe	refs/heads/main
```

`base_commit == origin/main` at the time of this run, so there is no upstream delta at all. Read
back the live file contents from the GitHub API to be sure the local clone is not lying:

```
$ gh api repos/go-acme/lego/contents/challenge/tlsalpn01/tls_alpn_challenge_server.go \
     --jq '.content' | base64 -d | sed -n '/func (s \*ProviderServer) CleanUp/,/^}/p'
func (s *ProviderServer) CleanUp(ctx context.Context, domain, token, keyAuth string) error {
	if s.listener == nil {
		return nil
	}

	// Server was created, close it.
	if err := s.listener.Close(); err != nil && errors.Is(err, http.ErrServerClosed) {
		return err
	}

	return nil
}
```

**The inverted predicate is live on `origin/main` today.** Not fixed, not in flight.

## ④ Issues and PRs, WITH comments — 10 queries, `total_count` recorded

| query (`repo:go-acme/lego+…`) | total_count | disposition |
|---|---|---|
| `cleanup+error+swallowed` | 0 | — |
| `ErrServerClosed` | 0 | — |
| `ErrServerClosed+in:body` | **0** | nobody has ever named the sentinel in a tracker item |
| `listener+close+error` | 2 | #553 VegaDNS provider, #1802 `-4/-6` flags — unrelated |
| `CleanUp+returns+nil` | 9 | all DNS-provider records; free-text OR noise |
| `cleanup+in:title` | 23 | **all 23 are DNS-provider record cleanup** (websupport, pdns, namesilo, godaddy, BlueCat, IONOS, lightsail, edgedns…). None is the challenge `ProviderServer` |
| `CleanUp+in:title` | 23 | same set |
| `http01+listener` | 1 | #1802, unrelated |
| `goroutine+leak` | 1 | #383 "Leaking authorizations", ACME-protocol level, unrelated |
| `address+already+in+use` | 59 | free-text noise; the only on-surface hit is #397, read below |

**`--comments` read in full on the only open, on-surface issue:**

`gh issue view 397 --repo go-acme/lego --comments` — *"Race condition in HTTP-01 challenge?"*,
open. The thread is about the challenge server not being reachable **early enough** (validation
starting before the listener/load-balancer is ready); mholt, xenolf and mfournier all discuss
startup latency and mfournier asks for *"a (configurable) grace time between binding port 80 and
starting to send queries"* — which is what `SetDelay`/`#2422`/`#2499` later shipped. **Nothing in
the body or any comment mentions teardown, `CleanUp`'s return value, close errors, lingering
connections, or a hang.** Not a disclosure for this candidate.

`gh issue view 720 --comments` (the only other open hit) is about giving DNS providers an
`fqdn,value` entry point. Unrelated.

## ⑤ Shipped tests — is the direction already public in the test suite?

```
$ grep -rln "CleanUp" --include=*_test.go challenge/
challenge/resolver/prober_mock_test.go
challenge/dns01/dns_challenge_test.go
challenge/resolver/prober_test.go
```

**No shipped test touches `http01.ProviderServer.CleanUp` or `tlsalpn01.ProviderServer.CleanUp`
at all.** The three hits are the DNS-01 solver and the resolver's mock. The teardown behaviour of
both challenge servers is entirely untested upstream.

## ⑥ Peer dedup — the candidate's own symbols, several names

`gh api search/code … org:codimango`, paced 22 s apart:

| query | total | hits |
|---|---|---|
| `tlsalpn01` | 4 | `damiancruz-swebench/getssl-stable-authorization-order` ×2 (getssl, a shell client), `swe-bench-pro-abhkum/upgrade-tlsfs-library`, `…luoshiyu_traefik…tlsoptions` |
| `ProviderServer+CleanUp` | 2 | `upgrade-tlsfs-library`, `tpf-tbench/silent-fault-failover-controller` (python) |
| `http01+ProviderServer` | 1 | `upgrade-tlsfs-library` |
| `go-acme%2Flego` | 27 | dominated by `upgrade-tlsfs-library`; one Dockerfile in `swebench-jma/schmux-sec-1` |

The only repeated hit, `swe-bench-pro-abhkum/upgrade-tlsfs-library`, was read directly:

> "Rewrite `tlsp/acme/acme.go` for go-acme/lego/v4 … `AcmeFS.Create, Get, Revoke …` work end-to-end
> against ACME v2 over HTTP-01 … Replace docker-compose.yml with a single-container Pebble setup"

That task is on **`gokit/tlsfs`**, a *downstream consumer*, migrating it onto lego as a dependency.
Different repo, different base commit, and it does not modify lego at all. This matches what `A1`
recorded ("2 hits are a downstream consumer `tlsfs` task, not lego itself"), now confirmed
first-hand at the instruction level rather than by title.

**No peer task exists on `go-acme/lego`'s own `challenge/{http01,tlsalpn01}` teardown.**

---

## VERDICT — GATE 3 PASS

No merged PR implements or proposes the remedy; the defect is live on `origin/main` today; no
remote branch carries a fix; no open or closed issue names the behaviour in title, body or
comments; no shipped test exercises it; no peer task overlaps. The one caution carried forward is
**realism**, not disclosure: the maintainer has passed over the `log`-vs-`return` question at the
`Solve` layer four times.

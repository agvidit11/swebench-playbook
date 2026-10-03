# jsoup-session-fork-cookie-promotion

- Date/machine: 2026-10-02 / devvm23237
- Repo/base: `jhy/jsoup` @ `088614f4a1454232a1f03c63b7f80742f1f2a854`
- Seam: `Connection`/`HttpConnection` session cookie state
- Composition: late-bound mutable state × build-then-use × transactional failure quality
- Trap: natural order loses information, then failure-path quality
- Routing: `MEASURE`, three chained steps
- A4: `ADJACENT`; no same-upstream cookie task or parent/child conditional-promotion peer

## User problem and base proof

My crawler speculatively tries authentication or consent flows before deciding whether their cookies should enter a long-lived jsoup session. `newRequest()` shares the live store, so speculative work mutates the parent immediately. I need an isolated child with the parent's defaults and scoped cookie state, a detached change report, and conditional promotion that does not overwrite a different parent-side change.

At base, `newRequest()` copies the prototype but shares `cookieManager`. Mutating an `HttpCookie` returned by `CookieStore.getCookies()` mutated the session; two same-name cookies at `/` and `/account` demonstrated why a copied list/name map is insufficient. No snapshot/diff/conditional-commit API exists.

## Obligations

CONSTRAINT: Forking creates an independent child with equivalent defaults and complete state. The fork reports detached scoped additions/removals/replacements. Promotion preserves unrelated parent changes, accepts a parent already equal to the child result, and rejects every differently changed overlapping identity before mutation.

DESIRED: A deep isolated branch carrying a baseline, identity-complete directional delta, and preflighted conditional promotion.

NON-DESIRED: Shared `newRequest`; shallow cookie lists; name flattening; whole-parent replacement; conflict detection after progressive mutation.

## Steps

1. `Connection.fork() -> Connection.Fork` creates an isolated child whose request behavior initially matches the parent while later cookie changes remain independent.
2. `Fork.cookieChanges()` returns an unmodifiable detached list of immutable `CookieChange` values (`ADDED`, `REMOVED`, `REPLACED`) keyed by complete name/domain/path identity and comparing all observable attributes.
3. `Fork.commitCookies()` conditionally applies touched identities: unchanged and converged parent states succeed; divergent overlap throws `ConcurrentModificationException` before any change; unrelated parent changes survive.

Pinned surface: `Connection.fork`, nested `Connection.Fork`, `connection`, `cookieChanges`, `commitCookies`, nested `Connection.CookieChange`, `Kind`, `kind`, nullable `before`/`after`, and JDK conflict type. Result order is ungraded and returned cookies are defensive.

Wrong branches: shared manager; shallow copy; name-key flattening; whole-store replacement; progressive application. Step 3 requires the captured baseline/delta and is not a mechanical second site.

Pure in-memory sequential tests cover scoped duplicates, mutable aliasing, attribute-only replacements, removals plus unrelated parent additions, convergent changes, and late-conflict atomicity. Expected deltas: 85–130, 60–100, 65–110 lines.

Upstream issues 1813/1833 and PR 1476 only cover existing store use and flattened response cookies; none proposes fork/baseline/delta/promotion. Rating: P1 4, P2 2, P3 2, P4 4, P5 3, P6 3, P7 3 = **21/28 MEASURE**.


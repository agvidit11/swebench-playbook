# jsoup-streamparser-lazy-reader-failure-lifecycle

- Date/machine: 2026-10-15 / devvm23237
- Repo/base: `jhy/jsoup` @ `4cf664cdb2e9d2cc2d40fdf3bb9c0be0be22f865`
- Seam: `org.jsoup.parser.StreamParser` reader adoption and failed-consumption lifecycle
- Composition: deferred input ownership × checked/unchecked consumption boundaries × reusable abort
- Trap: **natural order loses information** — constructing the internal reader reads before ownership is safely established, so an exception can strand the source; normal-only teardown then misses later failures
- Routing: `MEASURE` in Lane P with a chained two-step probe
- A4: `CLEAR` at the capability; existing jsoup tasks and public history are adjacent but cover different seams

## A1 receipt

MIT; upstream active at the pinned 2026-10-15 head; 29,873 non-test Java LOC; six open issues. The prescribed one-year/400-commit authorship scan found 9 Copilot strings (dependency-release boilerplate, well below 25%) and no checked-in `AGENTS.md`, `CLAUDE.md`, or `.claude` workspace. jsoup already produced an accepted task on this machine, so its offline Java environment is known. The source compiled into `target/classes`; the host's old Maven later stopped at the project's Maven-version guard, which is an environment mismatch rather than a source failure.

## User problem and base proof

I attach Readers to a progressive parser before I know whether I will consume them. Some are slow or fail partway through. Merely attaching one should not read from it, and abandoning it or hitting a read error should not leave that source open. I still need the elements that were completed before a failure, and I need to reuse the same parser for the next input.

At base, a counting Reader holding only `<p>one</p>` was read twice and consumed completely inside `parse(Reader, String)`, although that method's own documentation says the input is not read until a consuming operation. Closing afterward produced `reads=2, chars=10, closes=1`, so cancellation was no longer read-free. With a larger Reader that failed after 2,600 characters, `complete()` exposed `UncheckedIOException` despite its checked `IOException` contract and left the Reader open. Iterator consumption emitted 114 completed elements and then the documented `UncheckedIOException`, but also left the failed Reader open (`closes=0`); the partial document contained 115 `p` nodes and the parser could subsequently parse a fresh input.

Reproduction:

```text
after-parse reads=2 chars=10 closes=0
after-close reads=2 chars=10 closes=1
complete failure=UncheckedIOException reads=3 closes=0
midstream emitted=114 first=injected read failure second=none reads=3 closes=0 partialP=115
reuse=fresh
```

Evidence is outside every task directory at `/tmp/card-1015.auvYFI/evidence/StreamLifecycleProbe.java` and `/tmp/card-1015.auvYFI/evidence/StreamLifecycleProbe.out`.

## Natural step shape

1. **Deferred reader adoption.** `StreamParser.parse(Reader, String)` takes responsibility for a Reader without invoking `read`. A parser closed or pointed at a replacement before its first consuming operation closes the abandoned Reader exactly once without reading it; the first real consumer starts normal progressive input. The partial `Document` remains available immediately after setup, as it is today.
2. **Failure-safe consumption.** Once reading has begun, an I/O failure ends that input, closes its Reader exactly once, and performs no further reads. Iterator/stream consumers retain their documented `UncheckedIOException`; APIs whose signatures promise `IOException`, including full completion and selection, expose the checked cause. Elements completed before the failure and the partial document remain usable, and a later input can be parsed normally without closing the failed source again.

Step 2 exercises the ownership lifecycle established by Step 1 under a different operation: consumption abort rather than input setup. It is not the same property copied to a second site. A viable design may defer the existing `CharacterReader`, install a lazy adapter, or move ownership into a failure-aware parse state; the contract does not select one.

## Likely calibration gradient

- Step 1 is predicted **2–3/5**: changing only the Javadoc or wrapping one public overload misses zero-read close/replacement, while globally making `CharacterReader` lazy risks its many non-streaming callers.
- Step 2 is predicted **1–3/5**: normal EOF cleanup already works, so plausible implementations close only the iterator path, change the wrong exception family, discard partial output, or double-close during reuse.
- No non-final saturation exemption exists for a two-step task. Lane P must run fresh K-to-N cold implementations and release the card if either step remains 4–5/5 after one fair amendment.

## A4, public-fix, and contamination screen

- Live whole-org searches for jsoup `StreamParser` combined with `Reader`, lazy/eager read, close, midstream failure, and `UncheckedIOException` returned no matching peer task. The low-level classification tree's jsoup hits were two broad Sonar smell-removal tasks, not parser behavior. Exact StreamParser hits in licensed tasks were TypeScript homographs from another product.
- This playbook contains jsoup W3C-mirror and HTTP-session cards only; both are different packages and invariants. No current claim owns the parser Reader lifecycle.
- Upstream issue/PR searches for lazy/eager Reader setup, I/O cleanup, and progressive-reader leaks found no proposed or merged fix. PR #2096 introduced StreamParser. Issue #2605 / commit `922ee011` is adjacent but already present at base and isolates StreamParser from reuse of the supplied `Parser`; it does not cover Reader adoption, exception boundaries, or cleanup after read failure.
- The only upstream remote branch besides `master` is `validate-corelib2-nio`, unrelated to this seam. The pinned commit is current upstream head, so there is no later public solution reachable in repository history.
- A future upstream issue could disclose the small failure seam before build, so Lane P should repeat the tracker/branch sweep. The task must ship with internet disabled to avoid generic public-repo retrieval concerns.

## A4 verdict and score

`CLEAR` at the capability and safe to measure. Scores: Novelty 4, Difficulty 4, Fork strength 4, Harness-ability 5, Observability 5, Realism/fit 5, Cascade 3, Scope 4 = **34/40 MEASURE**. The main risk is calibration, not validity: cleanup may be obvious after Step 1, while a lazy `CharacterReader` change may be broader than the 80–150-line target. Lane P should reject a global behavior change that breaks ordinary Parser callers and should grade only public, deterministic Reader observations.

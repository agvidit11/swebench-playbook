# GATE 5 — model-prior fork probe, candidate 4R. Re-run with the mandatory pre-checks met.

## ① Direction fixed BEFORE probing

`artifacts/A3/card-04R-truthful-teardown.md` declares `CONSTRAINT:` / `DESIRED:` / `NON-DESIRED:`
verbatim in a machine-readable block. The card was written and saved before either prompt existed.

## ② probe-lint.py — PASS

```
$ python3 ~/swebench-playbook/tools/probe-lint.py \
      artifacts/A3/card-04R-truthful-teardown.md \
      artifacts/A3/probes/c4r-A.txt artifacts/A3/probes/c4r-B.txt
  PASS  probe states the constraint, does not leak the design, two distinct phrasings
```

Two materially different phrasings, both carrying the constraint:

- **A** — repo-grounded. Names the two packages and the `Present`/`CleanUp` entry points, then
  quotes the CONSTRAINT verbatim. No design words.
- **B** — an operator's bug report (ghost listener, connection still exchanging bytes, clean logs,
  one wedged teardown), then the same requirement restated in the reporter's own words. Never
  mentions a listener, a server object, a channel, or a sentinel.

This is the check the prior run did not have. The prior cascade-4 prompt (`probes/c2-A.txt`) told
the model *"several domains must be able to have an outstanding challenge at the same time … the
last CleanUp should shut the listener down"* — i.e. it handed over the per-domain-map design it
then scored as "5/5 desired". That probe would not pass this lint.

## ③ Direction applied — **card DESIRED → outputs**, stated explicitly

I classified each output *against the card's own DESIRED/NON-DESIRED text*, asking "did this output
produce DESIRED?", and I am reporting the DESIRED count. I am **not** reading a direction off the
outputs. The card's DESIRED has three separable markers:

- **(a)** teardown stops *the thing that is serving*, not merely the socket
- **(b)** whatever stopping it produced is handed back unchanged
- **(c)** a repeat teardown reports the same truth rather than being silently smoothed over

### Phrasing A, n=5

| out | (a) stop the server itself | (b) hand back the failure | (c) repeat reports the truth | deciding line |
|---|---|---|---|---|
| A-1 | **DESIRED** | **DESIRED** | NON-DESIRED | *"retain the serving HTTP server object on the provider so cleanup can act on active state rather than only the listener"* / *"otherwise returns immediately"* |
| A-2 | **DESIRED** | **DESIRED** | NON-DESIRED | *"Store the active `http.Server` together with its listener … shut down the stored server"* / *"tolerates absent or already-consumed state"* |
| A-3 | **DESIRED** | **DESIRED** | NON-DESIRED | *"terminate serving and not only close the listener while leaving established connections usable"* / *"repeated cleanup stays consistent"* |
| A-4 | **DESIRED** | **DESIRED** | NON-DESIRED | *"force-close accepted and idle connections"* / *"treat nil state as success"* |
| A-5 | **DESIRED** | **DESIRED** | NON-DESIRED | *"stop both new accepts and already accepted connections"* / *"returns promptly when shutdown already completed"* |

**(a) 5/5 DESIRED · (b) 5/5 DESIRED · (c) 0/5 DESIRED.**

### Phrasing B, n=5 (non-leading: symptom only)

| out | (a) | (b) | (c) | notes |
|---|---|---|---|---|
| B-1 | **DESIRED** | **DESIRED** | NON-DESIRED | names the bug outright: *"correcting the inverted closed-error test in the TLS-ALPN server"* |
| B-2 | **DESIRED** | **DESIRED** | NON-DESIRED | *"forced closure of established, idle, and keep-alive connections … so `nil` strictly means gone"* |
| B-3 | **DESIRED** | **DESIRED** | NON-DESIRED | *"correcting the inverted expected-shutdown check in the TLS-ALPN cleanup that currently discards genuine failures as success"* |
| B-4 | **DESIRED** | **DESIRED** | NON-DESIRED | *"instead of ignoring it or testing for the wrong sentinel"*; *"repeated CleanUp calls are idempotent"* |
| B-5 | **DESIRED** | **DESIRED** | NON-DESIRED | *"Fix the inverted error test in the TLS-ALPN cleanup"*; *"Make both cleanups idempotent"* |

**(a) 5/5 DESIRED · (b) 5/5 DESIRED · (c) 0/5 DESIRED.**

---

## Reading, and the trap I am refusing to fall into

**The candidate does not survive GATE 5.** On the two markers that carry the fix — stop the serving
component rather than the socket, and hand the failure back — the model prior is **10/10 DESIRED
across two phrasings**, including the deliberately non-leading one. A3's mapping is explicit:
*≥4 of 5 produce DESIRED → fork ~1 → candidate DEAD.*

**The (c) column is 10/10 NON-DESIRED, and calling that a strong fork would be wrong.** It is
tempting — the brief is looking for exactly that row — so it is worth saying plainly why it is not
one. All ten outputs make teardown idempotent and return nil on a repeat call; four of them argue
for it explicitly. That is not the model failing to find a hard path. It is **my DESIRED clause
being the worse engineering**: `io.Closer` semantics, and every provider in this repo, treat a
second teardown as a no-op. Scoring my own bad direction as model divergence is the frostdb error
run in reverse, and it would manufacture a survivor. The (c) divergence is a defect in the card,
not a fork in the repo.

**What is genuinely new versus the prior run.** B-1, B-3, B-4 and B-5 — four of five given nothing
but an operator's symptom report — **named the inverted `errors.Is` directly**, unprompted, with the
repo mounted. The prior run's kill was "five models described the same design". This one is
stronger and worse for the candidate: five models, told only that teardown lies, *found the one-line
accidental defect that makes it lie*. Whatever SEARCH difficulty this surface has, it is not the
inverted predicate.

GATE 5 verdict: **Fork strength 1** (GATE 8 veto axis). Carried to GATE 4 A3-LOCAL, which is the
PRIMARY gate and which decides — per A3, a candidate may only be killed on GATE 5 alone if GATE 4
A3-LOCAL was run and is inconclusive.

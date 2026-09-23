# CHECKPOINT — run-20260922T221320Z

**Last updated:** 2026-09-22, run TERMINATED at A3 with `EXIT: NO SURVIVOR`. `DONE` written.
Handoffs 01 and 02 were **amended after reviewer audit** — see `handoffs/05-CORRECTIONS.md`.

---

## Final position

| | |
|---|---|
| **Run state** | **STOPPED.** Four candidates gated, four evidenced kills. Nothing to scaffold. |
| **Acts executed** | `A1` → `A2` → `A3` → `A2 (r2)` → `A3 (r2)`. **`B1`–`B5` never started.** |
| **Repo** | `go-acme/lego`, clone `/tmp/e2e-lane-GO/lego`, base `58468399a23fbdf4cb3a366e6d81925c1f97b4fe`, module `github.com/go-acme/lego/v5` |
| **Task dir** | **none created** — `B1` was never reached |
| **Docker lock** | never held by me. I ran **zero** Docker commands all run. |
| **Clone state** | clean — `git status --porcelain` empty; my GATE-2 reproduction file was deleted after measurement |

## Act exit states

| act | handoff | exit |
|---|---|---|
| `A1` repo screen | `handoffs/01-A1.md` | **NOT MET** (corrected from an invalid "PARTIAL"). 0 repos with the prescribed containerised G10; 1 with a native substitute (lego); 7 unmeasured or blocked. Proceeded anyway — deviation owned in `handoffs/05-CORRECTIONS.md` §1. |
| `A2` idea generate | `handoffs/02-A2.md` | **NOT MET** (corrected from "MET"). 18 surfaces → 2 cards, but 4 checklist lines do not hold — both cards abandoned the chosen A-shape, the auto-rejects were not applied to the survivors, and both self-audits used invented rubric labels. `handoffs/05-CORRECTIONS.md` §2. |
| `A3` idea gate (r1) | `handoffs/03-A3.md` | both cards killed (GATE 0, GATE 3) |
| `A2` idea generate (r2) | `handoffs/04-A2r2.md` | **MET** — 2 new cascades, each with function-scoped history evidence |
| `A3` idea gate (r2) | `handoffs/03-A3.md` | both cascades killed (GATE 5 ×2) → **NO SURVIVOR** |

## The four kills

| # | candidate | gate | evidence |
|---|---|---|---|
| 1 | Every-Key-Type | **GATE 0** | 3 coined tokens (`ErrUnsupportedPrivateKey`, `PrivateKeyPEMType`, `ErrUnsupportedSignerKey`), all 0 hits at base, all load-bearing for the assertions |
| 2 | No-Silent-Fallback Selection | **GATE 3** | step 1 = revert of merged PR **#1334** "fix: preferred chain only match root name"; found by `git log -L` on the function, a command in no act-file |
| 3 | Dead responder, accountable revocation | **GATE 5** | 5/5 desired path phrasing A, **5/5 phrasing B (non-leading)**, 4/4 on step 1 |
| 4 | One port, many challenges | **GATE 5** | 5/5 desired path, near-verbatim reproduction of both steps |

## Decisions made — do not relitigate

1. **Three A1 lanes GO/RS/JV, Ruby excluded** — 14+ in-flight Ruby tasks make it the highest
   self-collision territory, and `ruby` is absent from the host so every Ruby G10 would be
   Docker-bound (the resource that turned out unavailable).
2. **G10 split out of the A1 fan-out** — router §6 makes Docker serial-only while making A1 the
   canonical parallel act. Lanes measured natively where the toolchain existed; container G10 was
   queued and then blocked. → friction F3.
3. **Repo = `go-acme/lego`** — the only repo with a measured graded path (25s build / 12s graded /
   11s offline), MIT, 0% AI-authorship, 90 real open issues, real fixtures.
4. **Lens = AXIS 19 × P6** — AXIS 19 is the only *measured* axis in R5; P6 was at 2 of ~3
   instantiations, both Ruby/rom-rb, so a Go PKI instance varies the domain. **The survey returned
   no P6** — both round-1 cards self-reported "not P6, step 1 survives intact". Recorded, not
   relabelled.
5. **Stopped rather than running an A2 round 3.** The 18-surface inventory is fully dispositioned
   (7 killed at A3, 9 auto-rejected at A2, 1 unmergeable). The run brief and A1 §1 both forbid
   manufacturing a survivor. → friction F21 (no termination rule exists; this is my call, flagged).

## What a successor should know

- **`go-acme/lego` is exhausted for THIS LENS, not dead.** It passed every A1 gate. A second survey
  under a different C-axis is the cheapest next move — the Dockerfile, dedup and toolchain work is
  already amortised (A1 §1 "few repos, many tasks").
- **`c1` (`GetOCSP` AIA/OCSP exhaustion) is the best-evidenced premise the run produced and is still
  clean** — 2018 `TODO`, `total_count=0` on three disclosure queries, no shipped test, clean function
  history, premise confirmed **by execution**. It died only on the fork probe (4/4 obvious).
  If anyone wants it as a single-turn task, the evidence is all in `handoffs/03-A3.md`.
- **Three surfaces are parked as single-turn candidates:** `c2` typed revocation reasons (the
  `acme.CRLReason*` constants already exist, only validation is missing — note **7 is absent** from
  the set), `ch3` tls-alpn listener lifetime + the linter-introduced inverted `errors.Is` predicate,
  `C3` zerossl typed-nil error.
- **Two hard-won environment facts about lego**, either of which would have cost an hour later:
  lego's `api.Core` HTTP client **rejects plain `http://`** ("HTTPS is required"), so graded tests
  must use `httptest.NewTLSServer` and that server's own `Client()`; and `api.New` needs a live ACME
  directory, so the harness must serve `/dir` and `HEAD /nonce` (copy `internal/tester/api.go`).
- **Three more repos are one Docker run from being fully gated:** `nmstate/nmstate`,
  `apache/mina-sshd`, `spiffe/spire`. Exact G10 commands in `handoffs/01-A1.md` §G10 QUEUE.

## Artifacts

```
handoffs/01-A1.md 02-A2.md 03-A3.md 04-A2r2.md 05-CORRECTIONS.md
artifacts/A1/                   the three lane shortlists (36 repos screened), made durable
friction.md                     24 entries, tagged REPEAT / EARLIER / WASTE / PINPOINT
artifacts/A2/                   18-surface table, 5 subsystem passes, merge table, 2 full cards, briefs
artifacts/A3/remerge.out        round-2 cascades + 6 function histories
artifacts/A3/probes/            4 probe briefs + 20 probe outputs
```

## /tmp paths in use

| path | purpose |
|---|---|
| `/tmp/llc` | dedup corpus, HEAD `d8472c4` 2026-09-02 (20 days stale) |
| `/tmp/e2e-pools/` | peer repo-candidate pools |
| `/tmp/e2e-lane-{GO,RS,JV}/` | lane clones + shortlists (36 repos screened) |
| `/tmp/lego-run/` | A2/A3 working dir: briefs, surface passes, cards, probes |

## In-flight dispatches

**None.** All MetaCode dispatches and all subagents returned.

# Review 02 — A2 idea generate

## Verdict: FAIL

A2 did not meet its own exit condition. The exit requires every card to be axis-composed and to carry a valid self-audit (`A-source/A2-idea-generate.md:5-8,124-140,244-251`). The run selected AXIS 19 × P6 (`handoffs/02-A2.md:67-82,286`), but both delivered cards explicitly say they are **not P6** and substitute shapes absent from the live P1–P6 library (`handoffs/02-A2.md:84-89,222,240,315-317`). More importantly, both survivors fire A2's own auto-rejects, so the claimed checklist lines 9–11 are not supported.

## Checklist audit

The handoff reports `13 of 13` with no waivers (`handoffs/02-A2.md:18-19,280-298`). I spot-checked seven ticked lines against the artifacts and source.

1. **Line 4 — supported.** The brief asked for 18 surfaces from the 60k–150k band, and the durable table contains exactly 18 rows (`handoffs/02-A2.md:97-105`; `artifacts/A2/survey-p1.txt:1-15`; `artifacts/A2/surfaces.md:12-30`). The executor correctly caught that A1's `SUB=262` was fan-out, not 262 meaningful subsystems (`friction.md:234-252`).
2. **Line 5 — supported.** The three admissions quoted in the handoff exist at the pinned checkout; in particular the live fallback TODO and `[0]` accesses are present at `certificate/certificates.go:558-563,597` (`handoffs/02-A2.md:107-126`). The extra roadmap/issue sweep was useful even though A2 fails to require it (`friction.md:176-208`).
3. **Line 7 — performed, but the stated proof failed.** The first two large dispatches returned only a plan/banner at 930 B and 723 B, while a successful smoke response was 739 B (`handoffs/02-A2.md:140-155`). Thus A2's `<600 bytes` check would accept both a total failure and a successful response (`A-source/A2-idea-generate.md:105-122,278`). The executor recovered with a content gate and subsystem passes, so this is a documented playbook defect rather than fabrication.
4. **Line 8 — not fully supported.** The merge table initially maps `ch1` to Card 2 (`artifacts/A2/p-merge.md:8-10,36-38`), but the final card drops it (`artifacts/A2/card-02-no-silent-fallback.md:6-8,75-80`). The final accounting says 3 surfaces in Card 1 + 2 in Card 2 + 3 parked + 9 dropped = **17**, not 18 (`handoffs/02-A2.md:171-176,257-276`). `ch1` is not in the reported nine-item dropped set. “All 18 ids mapped” therefore describes an obsolete intermediate, not the final output.
5. **Line 9 — false.** Card 1 is acknowledged as a three-word-recall exposure (`handoffs/02-A2.md:27-33`) even though A2 says that test is an outright rejection with no card written (`A-source/A2-idea-generate.md:172-200`). It also has the exact “step 2 = now use what you built in step 1” shape A2 auto-rejects: step 2 delegates two more consumers to the step-1 mapping (`artifacts/A2/card-01-every-key-type.md:13-17,54-60`; `A-source/A2-idea-generate.md:182-186`).
6. **Line 10 — false for Card 1.** The card requires `PEMBlock`/`PEMEncode` to stop silently returning nil and says the unsupported path will be “pinned in Interface Contract,” but its table does not pin either existing function's changed signature or observable failure mode (`artifacts/A2/card-01-every-key-type.md:13-14,29-37`). At base, `PEMEncode` returns only `[]byte` and `PEMBlock` only `*pem.Block`, so a typed error cannot surface through those APIs without an omitted contract decision (`/tmp/e2e-lane-GO/lego/certcrypto/crypto.go:170-187`).
7. **Line 11 — false for both cards.** The tables label unrelated card qualities as Agentic rubric IDs—for example Card 2 calls R01 “task is measurable,” R02 “feasible <=150 lines,” and R08 “step ordering,” while the canonical dimensions are spec sufficiency, spec-test alignment, and acceptance of alternatives (`artifacts/A2/card-02-no-silent-fallback.md:82-98`; `B-build/B5-preflight-push.md:89-107`). The rows have text, but not evidence for the rubrics they claim to audit. Under the run rule, this unsupported tick makes the act fail.

## Evidence quality

The source citations and survey counts are generally real. I independently confirmed the pinned SHA and the cited base behavior: `checkResponse` sets the default resource then returns `true,nil` after a miss; `GetOCSP` uses only index 0 for both issuer and OCSP URLs; `PEMBlock` omits Ed25519; and `signatureAlgorithm` has no Ed25519/default error arm (`handoffs/02-A2.md:216-249`; `/tmp/e2e-lane-GO/lego/certificate/certificates.go:455-503,539-620,656-669`; `/tmp/e2e-lane-GO/lego/certcrypto/crypto.go:79-110,170-187`; `/tmp/e2e-lane-GO/lego/acme/api/internal/secure/signer.go:151-165`).

The per-arm values are forecasts, not measurements: Card 1 says `2/5`, `4/5`, `4/5`, then `1/5`, and Card 2 says “typically” `2/5`, `4/5`, `3–4/5`, then `1–2/5` (`artifacts/A2/card-01-every-key-type.md:49-52`; `artifacts/A2/card-02-no-silent-fallback.md:65-68`). They are clearly labelled predicted, so they are not fabricated measurements, but they provide no evidence that either idea has outcome variance. A3 must not treat them as measured.

## Boundary and ownership

No `instruction.md` exists in the run artifacts, and no artifact purports to be instruction prose (`handoffs/02-A2.md:50-59`). The card prompts contain requirements and interface contracts, which A2 expressly permits for non-instruction deliverables (`A-source/A2-idea-generate.md:14-20`). The generated card outputs identify MetaCode activity in their preambles (`artifacts/A2/card-01-every-key-type.md:1-4`; `artifacts/A2/card-02-no-silent-fallback.md:1-4`). I found no instruction-authorship leak in this act.

## Director's call

I would not green-light either card as submitted.

- **Card 2 is not a cascade.** Step 1 changes preferred-chain selection in `checkResponse`; step 2 changes issuer/OCSP fallback in the independent `GetOCSP` path (`artifacts/A2/card-02-no-silent-fallback.md:10-20`). `GetOCSP` never calls or consumes `checkResponse`, and the two functions have separate callers (`/tmp/e2e-lane-GO/lego/certificate/certificates.go:394-444,455-503,531-620`). The claimed S2 invariant that its loops preserve S1's miss error is therefore non-causal (`artifacts/A2/card-02-no-silent-fallback.md:20`), and step 2 is computable entirely from data at its own seam—the exact auto-reject at `A-source/A2-idea-generate.md:182-186`.
- Card 2's “leave a usable default resource while returning error” is not observable through the public issuance path as proposed: both callers of `checkResponse` discard `certRes` and return `nil` on error (`/tmp/e2e-lane-GO/lego/certificate/certificates.go:394-410,427-441`). Its Step-1 grading plan relies on calling the unexported method directly (`artifacts/A2/card-02-no-silent-fallback.md:45-53`), contrary to A3's upcoming outside-observability gate (`A-source/A3-idea-gate.md:206-218`). Split into independently evaluated single-turn leads if retained; do not build this as MT.
- **Card 1 is a straightforward key-type support refactor, not a demonstrated fork.** Its new public helper and two error sentinels are COINED and therefore will fail A3 Gate 0 absent a recorded override (`artifacts/A2/card-01-every-key-type.md:29-36`; `A-source/A3-idea-gate.md:28-61`). The handoff already acknowledges the three-word-recall failure (`handoffs/02-A2.md:27-30`). I would kill it before paid probing unless A3 can first justify the exceptional Gate-0 route.

The repository remains worth mining, but these two MT candidates are not strong enough. Card 2 contains two potentially reasonable single-turn bugs; that does not make them a cascade.

### Later evidence from A3

A3's function-scoped history check independently found that Card 2's preferred-chain half would reverse merged PR `#1334`: that change deliberately replaced whole-bundle matching with root-only matching, and closed issue `#1333` publicly discusses both the matching semantics and the proposed observability surface (`friction.md:297-354`). This is a hard disclosure/source-history kill under A3's intended rule, and it confirms that A2's card-generation path did not adequately screen its strongest candidate before declaring the act complete.

## Defect attribution

Executor defects:

- Declared the selected A-shape complete after both cards explicitly abandoned it (`handoffs/02-A2.md:76-89,286`; `artifacts/A2/card-01-every-key-type.md:8-10`; `artifacts/A2/card-02-no-silent-fallback.md:6-8`).
- Failed to apply the auto-rejects to both survivors, especially Card 2's independent second step and Card 1's acknowledged recall/build-then-use shape (`A-source/A2-idea-generate.md:172-200`; `handoffs/02-A2.md:27-30,240-253`).
- Counted a stale `ch1 -> Card 2` merge assignment after dropping `ch1`, making the final 18-surface accounting arithmetically incomplete (`artifacts/A2/p-merge.md:8-10`; `handoffs/02-A2.md:171-176,240,257-276`).
- Marked the self-audit complete even though both cards used non-canonical meanings for the named R-rubrics (`handoffs/02-A2.md:293-294`; `artifacts/A2/card-01-every-key-type.md:65-81`; `artifacts/A2/card-02-no-silent-fallback.md:82-98`; `B-build/B5-preflight-push.md:89-107`).

Playbook defects:

- A2 says a strong card uses every layer while simultaneously quarantining B (`A-source/A2-idea-generate.md:23-39`). Fix: require one choice from every **live** layer.
- A2 promotes build-then-use/narrow-then-widen as merge shapes, then auto-rejects “step 2 = now use what you built in step 1” without distinguishing legitimate from decorative dependency (`A-source/A2-idea-generate.md:89-93,182-186`). Fix: define the causal test once and route it to A3 Gate 7.
- A2 names R01–R13/N01–N04 without defining or linking their meanings, which allowed both cards to invent incompatible rubric labels (`A-source/A2-idea-generate.md:244-251,282`; `B-build/B5-preflight-push.md:82-107`). Fix: link the canonical rubric table and reject renamed dimensions.
- The byte threshold accepts the exact failure it is meant to detect (`A-source/A2-idea-generate.md:105-122,278`; `friction.md:254-281`). Fix: require a structural output token, not byte count.
- A2 does not require the feature-roadmap/disclosure sweep that removed roughly a dozen tempting premises in this run (`A-source/A2-idea-generate.md:270-284`; `friction.md:176-208`). Fix: add the sweep as a checklist line before card generation.

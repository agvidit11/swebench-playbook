# Brief: reproduce three claimed behaviours at base_commit, with evidence

Repo: `apache/santuario-xml-security-java`, working copy at `/tmp/santuario-pair/repo`,
base_commit `497d3fb4c8b5654a9951a3de4682c6ed48038173`. Java 17, Maven.

This is a VERIFICATION job, not a task-authoring job. I have three claims about what this
library does TODAY. Grep is not reproduction — I need each claim **executed** and the actual
output pasted. A claim you demolish is as valuable as one you confirm; do not make a claim
true by adjusting the experiment.

## Build / run recipe (verified working — use it verbatim, do not invent another)

```bash
docker run --rm --network=host \
  -v /tmp/santuario-pair/repo:/work -v /tmp/santuario-pair/m2:/root/.m2 -w /work \
  maven:3.9-eclipse-temurin-17 mvn -B -Drat.skip=true -Dtest=<ClassName> test
```

`/tmp/santuario-pair/m2/settings.xml` already carries the Maven Central mirror and the outbound
proxy. **`--network=host` is mandatory** — without it Maven cannot reach the proxy. Deps are
already warm, so a single-class run is ~14 s wall. Do not run the full suite (6 m 35 s).

**IMPORTANT — you must serialise Docker with the other agents on this host:**
prefix every docker command with `flock /tmp/swebench-docker.lock`.

## Where to put the code

Create ONE new test class:
`/tmp/santuario-pair/repo/src/test/java/org/apache/xml/security/test/dom/signature/ProbeManifestPolicyTest.java`

Package `org.apache.xml.security.test.dom.signature`. JUnit 5 (`org.junit.jupiter.api.Test`) —
match the conventions in the sibling `SignatureReferenceTest.java`, which already builds and
verifies signatures and is your best template. You may add private helpers in the same file.
**Do not modify any file under `src/main/`.** Do not modify any existing test.

Useful existing machinery you should reuse rather than reinvent:
- `org.apache.xml.security.test.dom.signature.SignatureReferenceTest` — end-to-end sign+verify,
  keystore loading (`getPrivateKey`/`getPublicKey`), and a `DummyResourceResolver`.
- `org.apache.xml.security.utils.XMLUtils` — `readResource`, `createDocumentBuilder`.
- `XMLSignature.addDocument(uri, transforms, digestURI)` to build References.
- `Manifest` is a public class with a public `(Element, String baseURI, boolean secureValidation)`
  constructor and `addDocument(...)`.
- Test resources live under `src/test/resources/`; `SignatureReferenceTest` reads
  `at/iaik/ixsil/coreFeatures/signatures/manifestSignature.xml`, which contains a nested Manifest.

Signatures must actually verify for some of these, so sign with a generated or keystore key
rather than hand-writing XML where you can.

## CLAIM 1 — nested-Manifest reference budgets do not compose

`Manifest.java:58` declares `MAXIMUM_REFERENCE_COUNT = 30`. `Manifest.java:62-65` reads it into a
**static** `referenceCount` from the system property `org.apache.xml.security.maxReferences`. The
cap is checked in the constructor (`Manifest.java:139-143`) and again in `verifyReferences`
(`Manifest.java:321-325`). Each nested `Manifest` is constructed fresh inside the follow loop
(`Manifest.java:362-365`) and so gets its **own** budget.

Claim: a signature whose `SignedInfo` holds N references, one of which is Manifest-typed and
points at a `ds:Manifest` holding M more references, is accepted under secure validation whenever
N <= 30 and M <= 30 — even though N + M > 30 — while a flat signature with 31 references is
rejected with `signature.tooManyReferences`.

Do this:
- **1a.** Flat signature, 31 references, `secureValidation = true`. Show the exception: its
  class, and `getMsgID()` if it is an `XMLSecurityException`.
- **1b.** Flat signature, 30 references, `secureValidation = true`. Show it verifies.
- **1c.** Nested: `SignedInfo` with ~25 references of which one is Manifest-typed
  (`Type = "http://www.w3.org/2000/09/xmldsig#Manifest"`), nested `Manifest` with ~25 references,
  `secureValidation = true`, `setFollowNestedManifests(true)`. Total 50 > 30. Report whether it
  is accepted. **If it is rejected, say so and paste the exception — the claim is then FALSE.**
- **1d.** Lower the cap at runtime via `System.setProperty("org.apache.xml.security.maxReferences", ...)`
  and report whether it takes effect, or whether the static field has already been initialised by
  an earlier class-load. **This one matters a lot to me** — if the property is read once into a
  static at class-init, it is not usable as a per-test injection point, and I need to know that
  before I design anything around it. Report the honest answer either way.

## CLAIM 2 — a failed reference suppresses nested-manifest evaluation for later references

`Manifest.java:347` guards nested-manifest following with
`if (verify && followManifests && currentRef.typeIsReferenceToManifest())`, where `verify` is the
running accumulator set false at `Manifest.java:339-341` by any earlier digest mismatch. So once
reference #k fails, a later Manifest-typed reference is never dereferenced, yet
`Manifest.java:402` still appends a `VerifiedReference` whose `manifestReferences` list is the
empty list from `Manifest.java:344`.

Claim: the caller cannot distinguish "this nested manifest was evaluated and had no references"
from "this nested manifest was never looked at".

Do this: build a signature with at least 3 references in document order where reference #1 is
Manifest-typed and valid, reference #2 has a deliberately corrupted digest, and reference #3 is
Manifest-typed and would be valid. Verify with `setFollowNestedManifests(true)`. Then print, for
every entry of `getSignedInfo().getVerificationResults()`: `getUri()`, `isValid()`, and
`getManifestReferences().size()`.

**Report the ACTUAL sizes.** I predict #1 is populated and #3 is empty. If #3 is populated, the
claim is FALSE — say so plainly. Also report whether swapping the order (corrupt #1 instead of
#2) changes whether #3 is populated.

## CLAIM 3 — an unresolvable reference aborts the whole loop; a digest mismatch does not

`Manifest.java:403-408` catches `ReferenceNotInitializedException` and rethrows
`MissingResourceFailureException` out of the loop, so `verificationResults` is never completed.
A digest mismatch merely sets `verify = false` and the loop continues.

Claim: with 4 references where #2 is unresolvable (a URI no registered resolver can handle) and
#4 has a bad digest, `verifyReferences` throws and `getVerificationResults()` returns fewer than
4 entries (possibly empty) — whereas if #2 merely has a bad digest instead, it returns all 4.

Do this, and for the throwing case report: the exception class, what
`getVerificationResults().size()` is afterwards, and whether `MissingResourceFailureException`
exposes the offending reference (check its accessors). Contrast with the all-digest-mismatch run.

## Output

1. The test class, committed to disk at the path above.
2. A file `/tmp/santuario-pair/notes/repro-results.md` containing, per claim:
   CONFIRMED / FALSE / PARTIAL, the **pasted** test output, and one line of interpretation.
3. If a claim cannot be reproduced because building the fixture is too hard, say exactly what
   blocked you. Do not substitute a weaker experiment and report it as the same claim.

Work until all three claims have a verdict. Print the final `Tests run:` line for every run.

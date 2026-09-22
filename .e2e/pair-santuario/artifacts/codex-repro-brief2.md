# Brief: characterise three existing API behaviours of a Java XML library, with executed evidence

This is a **library API characterisation** job on an Apache open-source Java library I am writing
documentation and regression tests for. Everything here is ordinary library behaviour — how a
public Java API reports results to its caller. Nothing in this brief asks you to find, exploit or
write a weakness; the three questions are all "what does this public method return / throw in this
ordinary situation, and can a caller tell two situations apart from the outside". I need the
answers because the reporting API is under-documented and I am writing its tests.

Repo: `apache/santuario-xml-security-java` (the `xmlsec` library), working copy at
`/tmp/santuario-pair/repo`, at commit `497d3fb4c8b5654a9951a3de4682c6ed48038173`. Java 17, Maven.

I have three claims about current behaviour. **Reading the code is not enough — I need each claim
executed and the real output pasted.** A claim you demolish is as valuable as one you confirm; do
not adjust an experiment to make a claim come out true.

## Build / run recipe — verified working, use it verbatim

```bash
flock /tmp/swebench-docker.lock docker run --rm --network=host \
  -v /tmp/santuario-pair/repo:/work -v /tmp/santuario-pair/m2:/root/.m2 -w /work \
  maven:3.9-eclipse-temurin-17 mvn -B -Drat.skip=true -Dtest=<ClassName> test
```

`/tmp/santuario-pair/m2/settings.xml` already holds the Maven mirror and the outbound proxy.
`--network=host` is mandatory. Dependencies are warm, so one class is ~14 s. Do not run the full
suite (6 m 35 s). **The `flock` prefix is required** — other agents share this host's Docker.

## Where the code goes

One new test class:
`/tmp/santuario-pair/repo/src/test/java/org/apache/xml/security/test/dom/signature/ProbeManifestPolicyTest.java`
package `org.apache.xml.security.test.dom.signature`, JUnit 5.

**Your template is the sibling file `SignatureReferenceTest.java`** in that same directory — it
already builds documents, signs them with a keystore key, verifies them, and reads back
`getSignedInfo().getVerificationResults()`. Copy its `getPrivateKey`/`getPublicKey` helpers and its
`DummyResourceResolver`. Its `testManifestReferences` method is almost exactly the shape I need.

**Do not modify anything under `src/main/`. Do not modify any existing test.**

Other machinery you should reuse: `org.apache.xml.security.utils.XMLUtils` (`readResource`,
`createDocumentBuilder`); `XMLSignature.addDocument(uri, transforms, digestURI)`; the public
`Manifest(Element, String baseURI, boolean secureValidation)` constructor and `Manifest.addDocument`;
test resources under `src/test/resources/` — in particular
`at/iaik/ixsil/coreFeatures/signatures/manifestSignature.xml`, which already contains a document
with a nested `ds:Manifest`.

---

## QUESTION 1 — do nested `Manifest` element budgets add up, or are they per-object?

`Manifest.java:58` sets `MAXIMUM_REFERENCE_COUNT = 30`. `Manifest.java:62-65` reads it into a
**static** field from the system property `org.apache.xml.security.maxReferences`. The count is
checked in the constructor (`Manifest.java:139-143`) and again in `verifyReferences`
(`Manifest.java:321-325`). Each nested `Manifest` is constructed fresh in the follow loop
(`Manifest.java:362-365`), so it plausibly gets its own independent allowance.

My claim: a document whose `SignedInfo` has N `Reference` elements — one of them pointing at a
nested `ds:Manifest` containing M more — is accepted whenever N <= 30 and M <= 30, even though
N + M > 30; while a flat document with 31 `Reference` elements is refused.

- **1a.** Flat, 31 references. Show what happens: exception class, plus `getMsgID()` if it is an
  `XMLSecurityException`.
- **1b.** Flat, 30 references. Show that it completes.
- **1c.** Nested: ~25 references at top level, one of them `Type="http://www.w3.org/2000/09/xmldsig#Manifest"`
  pointing at a `ds:Manifest` with ~25 more; `setFollowNestedManifests(true)`. 50 total. Report
  whether it completes. **If it is refused instead, say so and paste the exception — my claim is
  then FALSE.**
- **1d.** This one matters most to me. Call
  `System.setProperty("org.apache.xml.security.maxReferences", "5")` from inside a test and report
  whether it has any effect. I suspect the static field is already initialised at class-load, which
  would make the property useless as a per-test knob. **Report the honest answer either way** — I
  need to know before I design tests around it.

## QUESTION 2 — is "nested manifest not looked at" distinguishable from "nested manifest had no entries"?

`Manifest.java:347` reads
`if (verify && followManifests && currentRef.typeIsReferenceToManifest())`, where `verify` is a
running flag cleared at `Manifest.java:339-341` whenever an earlier reference's digest does not
match. So once reference #k reports a mismatch, a later Manifest-typed reference is apparently
never followed — yet `Manifest.java:402` still appends a `VerifiedReference` carrying the empty
list from `Manifest.java:344`.

My claim: from the outside, a caller cannot tell "this nested manifest was evaluated and had
nothing in it" from "this nested manifest was never visited".

Build a document with at least 3 references in document order:
- #1 Manifest-typed and matching,
- #2 an ordinary reference whose stored digest value does **not** match its content (the simplest
  way is to build a valid signature and then change one character of that one `DigestValue`, or
  point the reference at content you then alter),
- #3 Manifest-typed and would match.

Verify with `setFollowNestedManifests(true)`, then print for every entry of
`getSignedInfo().getVerificationResults()`: `getUri()`, `isValid()`, `getManifestReferences().size()`.

**Report the actual sizes.** I expect #1 populated and #3 empty. If #3 is populated, my claim is
FALSE — say so. Also report whether making #1 the non-matching one instead of #2 changes whether
#3 is populated.

## QUESTION 3 — does an input the resolver cannot supply end the loop, while a digest mismatch does not?

`Manifest.java:403-408` catches `ReferenceNotInitializedException` and rethrows
`MissingResourceFailureException`, which leaves the loop, so `verificationResults` is never
finished. A plain digest mismatch only clears `verify` and the loop keeps going.

My claim: with 4 references where #2 names a URI no registered resolver can supply, and #4 has a
non-matching digest, `verifyReferences` throws and `getVerificationResults()` afterwards holds
fewer than 4 entries; whereas if #2 is merely a mismatch too, all 4 entries are present.

For the throwing run report: the exception class, `getVerificationResults().size()` afterwards, and
whether `MissingResourceFailureException` exposes which reference it was (check its accessors).
Contrast with the all-mismatch run.

---

## Output

1. The test class on disk at the path above.
2. `/tmp/santuario-pair/notes/repro-results.md` with, per question: **CONFIRMED / FALSE / PARTIAL**,
   the **pasted** test output, and one line of interpretation.
3. If a fixture is genuinely too awkward to build, say exactly what blocked you rather than
   substituting a weaker experiment and reporting it as the same question.

Print the final `Tests run:` line for every run. Work until all three have a verdict.

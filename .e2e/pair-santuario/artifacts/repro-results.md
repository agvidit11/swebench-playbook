# Santuario Manifest policy API characterisation

Repository commit: `497d3fb4c8b5654a9951a3de4682c6ed48038173`

Threat-model disposition: `MODEL-GAP` under `THREAT_MODEL.md` section 13. These are
non-security API-characterisation results, not an allegation that a section 8
security property is broken, and section 13 has no ordinary-behaviour disposition.

## Question 1 — PARTIAL

The reference-budget claim in 1a–1c is confirmed. The 1d property result depends
on whether `Manifest` has already been initialized, so it is not a mutable
per-test knob in a shared JVM.

Output from the complete-class run (the property is changed after the first
three tests have initialized `Manifest`):

```text
PROBE Q1a flat=31 exception=org.apache.xml.security.exceptions.XMLSecurityException msgID=signature.tooManyReferences
PROBE Q1b flat=30 completed=true valid=true results=30
PROBE Q1c top=25 nested=25 total=50 completed=true valid=true topResults=25 nestedResults=25
PROBE Q1d property=5 flat=6 completed=true valid=true effect=false
```

Output from a fresh JVM running only the property test (the property is changed
before the first active use of `Manifest`):

```text
PROBE Q1d property=5 flat=6 exception=org.apache.xml.security.exceptions.XMLSecurityException msgID=signature.tooManyReferences effect=true
```

Interpretation: the secure-validation limit is per `Manifest`/`SignedInfo`
object, so 25+25 succeeds while a flat 31 fails; `maxReferences` is sampled once
at class initialization, works if set before that point, and has no effect after
that point.

## Question 2 — CONFIRMED

Output:

```text
PROBE Q2 case=reference-2-mismatch overallValid=false
PROBE Q2 reference-2-mismatch entry=1 uri=#manifest-one valid=true manifestReferences=1
PROBE Q2 reference-2-mismatch entry=2 uri=#ordinary-two valid=false manifestReferences=0
PROBE Q2 reference-2-mismatch entry=3 uri=#manifest-three valid=true manifestReferences=0
PROBE Q2 case=reference-1-mismatch overallValid=false
PROBE Q2 reference-1-mismatch entry=1 uri=#manifest-one valid=false manifestReferences=0
PROBE Q2 reference-1-mismatch entry=2 uri=#ordinary-two valid=true manifestReferences=0
PROBE Q2 reference-1-mismatch entry=3 uri=#manifest-three valid=true manifestReferences=0
PROBE Q2 reference-3-populated-when-reference-2-mismatches=false
PROBE Q2 reference-3-populated-when-reference-1-mismatches=false
```

Interpretation: reference 1 is followed only while the running validity flag is
still true; after either reference 2 or reference 1 mismatches, reference 3 is
still verified itself but its nested-manifest result list remains empty, with no
separate "not followed" flag.

## Question 3 — CONFIRMED

Output:

```text
PROBE Q3 missing exception=org.apache.xml.security.signature.MissingResourceFailureException msgID=signature.Verification.Reference.NoInput
PROBE Q3 missing results=1
PROBE Q3 missing getReference.present=true uri=urn:probe:resource-that-verifier-cannot-resolve
PROBE Q3 mismatch-only overallValid=false results=4
PROBE Q3 mismatch-only entry=1 uri=#four-0 valid=true manifestReferences=0
PROBE Q3 mismatch-only entry=2 uri=#four-1 valid=false manifestReferences=0
PROBE Q3 mismatch-only entry=3 uri=#four-2 valid=true manifestReferences=0
PROBE Q3 mismatch-only entry=4 uri=#four-3 valid=false manifestReferences=0
```

Interpretation: an unresolved reference exits at reference 2 after recording
only reference 1, and `getReference().getURI()` identifies the failed reference;
ordinary digest mismatches do not exit the loop and all four results are kept.

## Maven run summaries

Complete class:

```text
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
```

Fresh-JVM property-only run:

```text
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

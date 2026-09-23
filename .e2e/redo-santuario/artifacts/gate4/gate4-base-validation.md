# Gate 4 base validation

Validated the behavioural assertion sketch against
`apache/santuario-xml-security-java` at `497d3fb4c8b5654a9951a3de4682c6ed48038173`.

## Exact command

```sh
flock /tmp/santuario-redo/docker.lock docker run --rm --network=host \
  -v /tmp/santuario-redo/base-sketch:/work -v /tmp/santuario-pair/m2:/root/.m2 -w /work \
  maven:3.9-eclipse-temurin-17 \
  mvn -B -s /root/.m2/settings.xml -Dtest=ChainTraversalSketchTest -DfailIfNoTests=false test
```

The command exited with status 1 because the three behavioural assertions failed as intended.

## Surefire summary

```text
Tests run: 5, Failures: 3, Errors: 0, Skipped: 0
BUILD FAILURE
```

## Per-assertion result

| Assertion | Test method | Result | Failure message |
| --- | --- | --- | --- |
| A1 — outcome | `acceptingThenRejectingOutcomeIsFailure` | **FAIL** | `an accepting resolver that rejects its material must make resolution fail ==> Expected org.apache.xml.security.keys.keyresolver.KeyResolverException to be thrown, but nothing was thrown.` |
| A2 — later-resolver consultation | `acceptingThenRejectingDoesNotConsultLaterResolver` | **FAIL** | `a resolver after an accepting rejection must not be consulted ==> expected: <0> but was: <1>` |
| A3 — decline continues the scan (control) | `declineContinuesTheScan` | **PASS** | — |
| A4 — success path unchanged (control) | `successfulDefaultKeyValueResolutionIsUnchanged` | **PASS** | — |
| A5 — terminal names consulted resolvers in order | `terminalNamesConsultedResolversInOrder` | **FAIL** | `Expected org.apache.xml.security.keys.keyresolver.KeyResolverException to be thrown, but nothing was thrown.` |

## Isolation note

The static resolver registry has no removal API, so this sketch relies on a fresh JVM for the
test class. The existing Surefire configuration already has `reuseForks` set to `false`; no POM
change was made. Within the class, explicit method ordering makes the default-resolver control run
first, the decline-continues control second, and the measured chain thereafter.

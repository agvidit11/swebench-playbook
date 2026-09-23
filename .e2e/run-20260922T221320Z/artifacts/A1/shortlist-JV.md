# A1 REPO SCREEN — Lane JV (Java/Kotlin x security_and_privacy, secondary networking)

Screened 2026-09-22. Dedup corpus `/tmp/llc` HEAD `d8472c4` (2026-09-02, WAIVED refresh — 20d stale,
treated as UNKNOWN not clean per A1 §3). 12 repos screened total (over the 6-10 nominal budget) because
this sub-domain is currently saturated with a templated `AGENTS.md` "security researcher" artifact that
killed 6 of 12 candidates outright at G2 — see LANE FINDING below.

Schema: `slug | licence (+CONFLICT) | stars | last commit | real open issues (open−PRs) | peer verdict
(local+live) | AI-authorship % (method) | LOC / subsystems | name-free hosting | graded-path seconds
MEASURED | rank | why-not`

## SURVIVORS (3) — all PROVISIONAL, G10 pending (host is JDK-8-only; all three require JDK >=17 to build)

1. `apache/mina-sshd` | Apache-2.0, no CONFLICT | 1,096★ | 2026-09-20 | 55 open issues (68−13 PRs) |
   local: 0 filename/content hits; live `gh search code --owner codimango "mina-sshd"`: 7 hits, all
   incidental (sshd-*.pom vendored in unrelated tasks' m2/ivy caches, 2 Jenkins Dockerfiles, 1 gh-graph
   dot file) — CLEAR | AI-authorship 0% (method: identity — top committers are named ASF humans
   Lyor Goldstein/Guillaume Nodet/Thomas Wolf + 101 dependabot[bot] commits, no LLM-named authors;
   0 claude/codex/copilot remote branches; 0 commit-message/release-note attribution hits) |
   161,233 non-test LOC / 14 Maven subsystems (sshd-core, -sftp, -scp, -git, -ldap, -mina, -netty,
   -openpgp, -osgi, -putty, -spring-sftp, -cli, -common, -contrib) | name-free hosting: YES —
   `SshClient`/`SshServer`/`SftpClient` are existing public round-trip APIs (connect/auth/open a
   channel, upload/download over SFTP) | **PROVISIONAL — G10 pending** | rank 1 | —

2. `jetty/jetty.project` | EPL-2.0, no CONFLICT under any of the 3 read positions (only
   MIT/Apache/BSD/ISC are in the "never binds" convenience list; EPL is not blocked by any of the 3
   sources) | 4,093★ | 2026-09-22 | 220 open issues (274−54 PRs, mid "150–500" caution band) |
   local: 0 hits for "jetty.project"/"eclipse-jetty" family names beyond incidental dependency-pom
   noise; live `gh search code --owner codimango "jetty.project"`: 30 hits, ALL either our own pool
   doc (`swe-bench-pro-aaitemp/discovery-f/java_pool.json` — RACE-RISK signal, not a kill), 3 unrelated
   github-graph dot files, or `jetty-bom`/`jetty-project` dependency poms vendored inside 15+ unrelated
   tasks (lambda-iam-cucumber, disappearing-messages, razorpay-confirm-guard, commons-lang tasks,
   jsonschema2pojo, naptime-*, streamforge, debezium, lombok-*) — CLEAR, no direct peer task | AI-
   authorship 0% (method: identity — top committers Joakim Erdfelt/Simone Bordet/Greg Wilkins/Jan
   Bartel + 1,288 dependabot[bot] of ~26k total = bot-heavy on volume but human-authored substance,
   44% of last-90d merged PRs are dependabot vs 56% named humans, well under the 61%-bot demotion
   line; 0 claude/codex/copilot branches; 0 commit-message/release-note hits) | 586,816 non-test LOC /
   36 subsystems inside `jetty-core` alone (server, client, http, http2, http3, security, session,
   websocket, io, quic, proxy, rewrite, jmx, ...) plus jetty-ee8/9/10/11 compat layers | name-free
   hosting: YES — `Server`/`HttpClient`/`ServletHandler` round-trip APIs, decades of surface area |
   **PROVISIONAL — G10 pending** | rank 2 | —

3. `GoogleCloudPlatform/jit-groups` | Apache-2.0, no CONFLICT | 289★ | 2026-09-22 | 5 open issues
   (5−0 PRs, LOW band, matches the franz-go "undiscussed net-new capability" profile) | local: 0 hits;
   live `gh search code --owner codimango "jit-groups"`: 3 hits — 2 are our own pool docs
   (`swe-bench-pro-jayzong/docs/repo-candidates/*`, RACE-RISK signal), 1 unrelated github-graph file —
   CLEAR | AI-authorship 0% (method: identity — 300 commits Johannes Passing (sole maintainer) + 338
   dependabot[bot], handful of small contributors; 0 claude/codex/copilot branches; 0 release-notes
   file exists to grep, 0 commit-message hits) | 20,598 non-test LOC / single Maven module, 5 real
   Java packages (`catalog`, `web`, `common`, `apis`, `auth`) — thin but clears the "one-or-two-package"
   G7 floor | name-free hosting: YES — `Catalog.environment(name)` / `Catalog.group(name)` /
   `JitGroupContext` are existing public entry points for evaluating a JIT access policy | **G9 WARNING**
   — zero `src/test/resources` anywhere in the repo; graded tests would rely entirely on hand-built
   mocks of GCP IAM responses and inline CEL policy strings, the exact N03 "hand-built stubs" profile
   A1 §6 flags as a drag risk | **PROVISIONAL — G10 pending** | rank 3 (weakest of the three — thin
   subsystem spread + G9 fixture gap) | —

## REJECTS (9)

- `apache/shiro` | Apache-2.0 | 4,463★ | G1 HARD KILL — local filename sweep alone: 13 hits across
  flandpan-swebench (4 tasks incl. ABAC/authz_perf/parallel_auth + a `shiro-audit` SKILL.md),
  swe-bench-pro-aakashjohari (2-step MT `apache-shiro-mt`), -nirmitshah, -srhkansal, -hjoshi;
  live `gh search code --owner codimango "shiro"` returned 30 (capped) confirming the same set plus a
  tbench task (`tbporzio/java-authz-failopen`, vendors `org/apache/shiro/{realm,cache,authz,authc,mgt}`
  source) and a licensed-repo hit (`opiatalk` uses Shiro for its security layer). Oversubscribed on the
  same scale as the commons-lang precedent (18 peer tasks) — do not re-screen.

- `jwtk/jjwt` | Apache-2.0 | 11,137★ | G1 HARD KILL — local: 2 hits (`swe-bench-pro-alonmiz`,
  `jjwt-expiration-after-ordering`, a 2-step MT task adding `JwtBuilder.expirationAfter(Duration)`);
  live search confirmed the same task plus README/Dockerfile/task.toml artifacts. The peer sits on
  `JwtBuilder`, which is the core of this small library's entire public surface — not a corner that can
  be avoided.

- `apache/santuario-xml-security-java` | Apache-2.0 | 58★ | G2 HARD KILL — ships `AGENTS.md` at repo
  root: *"You are helping a security researcher find and report vulnerabilities in Apache Santuario...
  read THREAT_MODEL.md: the trust boundary, the central secure-validation knob, the properties provided
  vs left to the caller, and the known non-findings."* This is the exact "contamination oracle, not an
  idea source" pattern A1 §4 warns about — the file hands over a pre-mapped security surface in
  proposal-shaped prose. (Local/live peer sweep was otherwise clean; the only live-search hits were the
  Spanish homograph for "santuario" = "sanctuary" plus an unrelated `apache/poi` XML-dsig dependency
  mention — G1 would have passed.)

- `bcgit/bc-java` | MIT | 2,693★ | G2 HARD KILL — ships `.claude/skills/` (5 skills:
  bcpqc-add-signature-algorithm, build-jdk13-docker, build-jdk15to18, legacy-source-javadoc-jars,
  windows-build), `CLAUDE.md` (imports 5 `docs/claude/*.md` topic files covering build/test, JDK1.4
  legacy build, architecture incl. "adding a PQC algorithm", conventions, upstream-LTS porting), and
  `docs/claude/`. This is the same skill set pre-loaded into this very session under
  `repos-ext/bc-java/.claude/skills` — confirming the artifacts are upstream, not local tooling.
  Textbook G2 kill; local/live peer sweep was otherwise clean (30 live hits, all incidental
  `bcprov-jdk15on`/`bcpkix`/`bcpg`/`bcutil` dependency-pom noise in unrelated tasks).

- `OWASP/java-html-sanitizer` | Apache-2.0 OR BSD-2-Clause | 954★ | G2 HARD KILL — ships both
  `AGENTS.md` (*"This is a security-critical library. When in doubt, do less and ask a maintainer,"*
  same threat-model-guided-agent template as santuario/directory-ldap-api/pac4j) and `CLAUDE.md`
  (explicitly defers to AGENTS.md). Live search (5 hits) showed only stray mentions in other authors'
  ideation docs (`SWE-bench-multiturn-ideas.md`, a task-design doc) — RACE-RISK signal, not itself a
  kill, moot given G2.

- `apache/directory-ldap-api` | Apache-2.0 | 52★ | G2 HARD KILL — ships `AGENTS.md` pointing to
  `SECURITY.md` and the umbrella `apache/directory-server` THREAT_MODEL.md, same templated pattern.
  Local: 0 hits; live search on exact slug: 0 hits; supplemental live search on parent-project term
  "apacheds" returned 30 hits but all were token-fuzzy false positives (our own pool doc, unrelated
  Netty ivy.xml files) — G1 would have passed cleanly.

- `pac4j/pac4j` | Apache-2.0 | 2,527★ | G2 HARD KILL — ships `AGENTS.md` (Maven multi-module build/test
  guidance, targets Java 17). Not reached on G1 given the G2 kill.

- `auth0/java-jwt` | MIT | 6,237★ | G1 HARD KILL — live `gh search code --owner codimango "java-jwt"`:
  30 hits (capped), at least 2 distinct peer tasks — `swe-bench-pro-keer`'s `java-jwt-truth-migration`
  (duplicated as both `llm-` and `human-` variants under `alaeddine-tbench`) and `swe-bench-pro-saikz`'s
  `java-jwt-collection-expansion`. Oversubscribed.

- `netty/netty` | Apache-2.0 | 35,065★ | DOUBLE KILL — **G1**: live search returned 30 hits (capped),
  at least 9 distinct peer tasks/authors directly on netty (`kaining-tbench` netty-signature-decoder,
  `swe-bench-pro-dsha` jetty-to-netty, `-jiexiangshen` netty-new-feature, `bogdanp-swebench` x2,
  `-sattwikp` netty-100-continue-timeout, `-sov` netty-nio-channel-read-deregister, `-chrispix`,
  `-jedgett`, `bogdanp-long-horizon` x2 MT tasks (netty-long-horizon-http3, 2-3 steps),
  `-krishnarb3` (netty-socketio fork), `-svissarapu` netty-composite-refcount incl. 2 custom SKILL.md
  files). **G4**: `gh api search/issues` shows 622 real open issues (708 total − 86 PRs), over the
  ">~500 = HIGH sourcing risk" line. Dead twice over; also a dependency of nearly every other Java task
  in the corpus (its ivy/pom artifacts showed up as noise in >10 unrelated tasks' m2 caches during this
  screen), consistent with maximum training-corpus exposure.

## LANE FINDING (worth carrying forward, not asked for but load-bearing)

A **templated `AGENTS.md`** — *"You are helping a security researcher find and report vulnerabilities
in <project>... read THREAT_MODEL.md / SECURITY.md ... the known non-findings"* — has been added
upstream to at least 4 of the Java security libraries screened here (santuario, java-html-sanitizer,
directory-ldap-api, pac4j), independent maintainers/orgs, near-identical prose. This is a real,
sub-domain-wide G2 exposure specific to Java/Kotlin × security_and_privacy right now — 4 of 12
candidates (33%) died on this single artifact. Screen for `AGENTS.md`/`CLAUDE.md`/`docs/claude/`
FIRST, immediately after clone, before spending time on G3–G9 in this lane.

## G10 — why all 3 survivors are DEFERRED, and the exact commands

Host toolchain: `java` is JDK 1.8.0_502 only (Temurin, `/usr/local/fbprojects/packages/java-runtime/
539/impl/8`), `mvn` 3.6.3, no JAVA_HOME set, no other JVM on the box. Real attempted-and-measured
native builds:

- **mina-sshd**: `mvn -pl sshd-common,sshd-core -am -DskipTests install` under host JDK 8 FAILS twice,
  independently: (1) `maven-enforcer-plugin` hard-requires `[3.9.12,)` Maven and `[17,)` JDK — real
  output: `Detected JDK ... is version 1.8.0-502 which is not in the allowed range [17,)`; (2) with
  `-Denforcer.skip=true`, the build still fails loading `net.revelc.code:formatter-maven-plugin:2.29.0`
  — `has been compiled by a more recent version of the Java Runtime (class file version 61.0), this
  version of the Java Runtime only recognizes class file versions up to 52.0` (i.e. the Maven *tooling*
  needs JDK17 to run at all, even though `<java.sdk.version>8</java.sdk.version>` is the release/
  bytecode target property). Real command sequence for a JDK17+ image: `docker build --network=host
  -f <lane-Dockerfile-FROM maven:3.9-eclipse-temurin-17> .` with `-s <settings-with-GCS-mirror>`, then
  `mvn -pl sshd-core -am test -Dtest='!*OpenSsh*,!*Interop*'` (excludes the 8 testcontainers-gated
  OpenSSH-interop classes in `sshd-core`/`sshd-sftp`; the remaining ~1000s of tests use the in-process
  `BaseTestSupport` embedded-server pattern with real fixture keys under
  `sshd-sftp/src/test/resources/.../ed25519_key`, `rsa_key`, no docker needed). `build_timeout_sec`:
  raise to 1800 (large multi-module reactor). Container flags: `--network=host` for the GCS Maven mirror.

- **jetty.project**: build enforces its own gate — real output from `pom.xml`'s enforcer message:
  `OLD JDK [...] in use. Jetty <version> requires JDK 17 or newer` (and `MUST use JDK 22 or newer` for
  the release profile specifically). Command sequence for a JDK17+ image: `docker build --network=host
  -f <maven:3.9-eclipse-temurin-17> .`, `mvn -s <gcs-mirror-settings> -pl jetty-core/jetty-server -am
  test` (isolates the server engine; testcontainers usage is confined to
  `jetty-ee{9,10,11}-test-sessions-{gcloud,infinispan,jdbc,memcached,mongodb}` and
  `jetty-integrations/jetty-infinispan`, none of which are in the `jetty-core/jetty-server` module
  graph). `build_timeout_sec`: raise to 3600 given 586k LOC / 36-module reactor. `--network=host`
  required for the mirror.

- **jit-groups**: `<maven.compiler.target>25</maven.compiler.target>` in `sources/pom.xml` — needs a
  JDK **newer** than any previously seen in this playbook (not just 17). Command sequence:
  `docker build --network=host -f <maven:3.9-eclipse-temurin-25>.`, `mvn -s <gcs-mirror-settings> -pl
  sources test -DskipITs=true` (matches the pool doc's documented CI invocation; ITs need live GCP
  credentials and are already excluded). `build_timeout_sec`: 900 (single module, 20.6k LOC).
  `--network=host` required for the mirror.

None of the three declare a `services:` block in CI beyond the excluded/isolable modules above, so
none is a hard G10 kill by that specific criterion — the blocker is purely the missing JDK on this host.

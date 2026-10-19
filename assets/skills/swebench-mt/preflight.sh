#!/usr/bin/env bash
# preflight.sh — run EVERY check that can fail, before you spend a push.
#
#   ./preflight.sh <task-dir-name> [--with-oracle] [--fast] [--no-server]
#
# Tiers:
#   TIER 1  the 16 checks local `bench validate --structural-only` runs
#   TIER 2  the 3 checks ONLY the server runs (License, SWE Step Configs,
#           SWE Step Parsers) — replicated so a local PASS means something
#   TIER 3  the landmines NO validator catches, that cost us real pushes
#   TIER 4  the oracle
#
# TWO SEVERITIES — the exit code comes from BLOCKING only.
#   BLOCKING   the task will fail server-side or grade wrongly. FAIL, exit 1.
#   ADVISORY   authoring quality: would raise throughput or difficulty, but the
#              task is perfectly valid without it. Prints ADV, NEVER exits 1,
#              and is never promoted to blocking by any flag.
#
# `artifacts` is the archetypal advisory: nothing server-side requires it, a
# task without it validates and gets accepted normally. It only makes OUR
# tuning loop fast. It is a SUGGESTED DEFAULT for new tasks — cheap enough that
# Codex should add it at scaffold time — but blocking a push on it would be a
# category error.
#
# NOTE on rule drift: the server's rules tighten over time, so an old accepted
# task is NOT evidence that a check is unnecessary. Our oldest acceptance
# (2026-07-23) carries a canary in solve.sh; all four later acceptances are
# clean. Judge a check against current server behaviour, not past acceptances.
#
# The advisory set is meant to buy a small quality gain at near-zero turnaround
# cost. It is deliberately NOT a checklist to satisfy. Read it, act on what is
# worth acting on, push. If clearing advisories is slowing task creation down,
# ignore them — that trade has gone the wrong way.
#
# LIFECYCLE — advisory output is suppressed entirely on tasks that are settled
# or close to submission (accepted / rejected / used_in_training /
# validation=passing). Editing task.toml on those means a fresh commit and
# re-validation on something already decided. Do not churn them.
set -uo pipefail

REPO="${REPO:-$HOME/swe-bench-pro-agvidit}"
# Run from a worktree, this silently audited the MAIN checkout and printed green for
# files that were not the ones under test. Measured 2026-09-25. If the task dir exists
# relative to the cwd, that is what the caller meant -- prefer it, and say which won.
if [ -d "$PWD/${1:-}" ] && [ "$PWD" != "$REPO" ]; then
  echo "  note: auditing \$PWD/${1:-} (cwd), not \$REPO -- task dir found relative to cwd"
  REPO="$PWD"
fi
T="${1:-}"
shift || true
WITH_ORACLE=""; FAST=""; NOSERVER=""
for a in "$@"; do
  case "$a" in
    --with-oracle) WITH_ORACLE="--with-oracle";;
    --fast)        FAST=1;;       # skip tier 1 (bench validate, ~400s) while iterating
    --no-server)   NOSERVER=1;;   # skip the lifecycle lookup
  esac
done
[ -z "$T" ] && { echo "usage: preflight.sh <task-dir-name> [--with-oracle] [--fast] [--no-server]"; exit 2; }
cd "$REPO" || exit 2
[ -d "$T" ] || { echo "no such task dir: $T"; exit 2; }

FAIL=0; ADVN=0
pass(){ printf "  \033[32mPASS\033[0m  %s\n" "$1"; }
fail(){ printf "  \033[31mFAIL\033[0m  %s\n" "$1"; FAIL=1; }
warn(){ printf "  \033[33mWARN\033[0m  %s\n" "$1"; }
hdr(){  printf "\n\033[1m%s\033[0m\n" "$1"; }

# --- lifecycle -----------------------------------------------------------
# Suppress advisory noise on anything settled or close to submission.
LIFE="unknown"; QUIET=""
CACHE=/tmp/pf-tasklist-$USER.json
if [ -z "$NOSERVER" ]; then
  if [ ! -s "$CACHE" ] || [ $(( $(date +%s) - $(stat -c %Y "$CACHE" 2>/dev/null || echo 0) )) -gt 900 ]; then
    timeout 120 codimango task list --json > "$CACHE".tmp 2>/dev/null && mv "$CACHE".tmp "$CACHE"
  fi
  if [ -s "$CACHE" ]; then
    LIFE=$(python3 - "$CACHE" "$T" <<'PY' 2>/dev/null || echo unknown
import json,sys
ts=json.load(open(sys.argv[1]))["tasks"]
t=next((x for x in ts if x.get("name")==sys.argv[2]), None)
if not t: print("local-only"); raise SystemExit
r,s,v=t.get("reviewStatus"),t.get("status"),t.get("validationStatus")
if s=="used_in_training" or r in ("accepted","rejected"): print(f"settled:{r}/{s}")
elif v=="passing": print(f"near-submission:{r}/validation={v}")
else: print(f"active:{r}/validation={v}")
PY
)
  fi
fi
case "$LIFE" in settled:*|near-submission:*) QUIET=1;; esac

# A settled task is not a push candidate. Linting it produces noise you must not
# act on — editing it means a new commit and re-validation on something already
# decided. Report state and stop.
if [ "${LIFE#settled:}" != "$LIFE" ]; then
  printf "\n\033[1m%s\033[0m\n" "LIFECYCLE"
  printf "  \033[32mSETTLED\033[0m  %s — %s\n" "$T" "${LIFE#settled:}"
  echo "  No checks run. This task is decided; do not churn it."
  echo "  Override with --no-server if you really need to lint it anyway."
  exit 0
fi

# Advisory: authoring quality. NEVER blocks, never gates a push, in any mode.
# These are cheap observations you act on if they're worth it. The whole point
# is a small quality gain for near-zero turnaround cost — the moment one of
# these becomes a requirement it is costing more than it returns.
adv(){ [ -n "$QUIET" ] || { printf "  \033[36mADV \033[0m  %s\n" "$1"; ADVN=$((ADVN+1)); }; }
advnote(){ [ -n "$QUIET" ] || printf "        %s\n" "$1"; }

MT=0; [ -d "$T/steps" ] && MT=1
STEPS=(); [ "$MT" = 1 ] && mapfile -t STEPS < <(find "$T/steps" -maxdepth 1 -mindepth 1 -type d | sort)

hdr "TIER 0 — full file inventory (every file, not just known landmines)"
# Multiple models write into one task dir. This tier assumes nothing about WHICH
# file broke: it walks the whole tree looking for anything an agent could have
# left behind or truncated.
EXPECT_MT="task.toml environment/Dockerfile"
for f in $EXPECT_MT; do
  [ -e "$T/$f" ] || fail "missing required file: $T/$f"
done
if [ "$MT" = 1 ]; then
  for s in "${STEPS[@]}"; do
    for f in instruction.md solution/solve.sh tests/config.json tests/parser.py tests/run_script.sh tests/test.sh; do
      [ -e "$s/$f" ] || fail "missing: ${s#$T/}/$f"
    done
  done
fi

# stray files no task should ever ship
STRAY=$(find "$T" -type f \( -name '*.orig' -o -name '*.rej' -o -name '*~' -o -name '*.bak' \
        -o -name '*.swp' -o -name '.DS_Store' -o -name '*.tmp' -o -name 'nohup.out' \
        -o -name '*.log' -o -name 'core' -o -name '*.pyc' \) 2>/dev/null)
[ -n "$STRAY" ] && { fail "stray files in tree:"; echo "$STRAY" | sed 's/^/        /' | head -10; }

# zero-byte files: almost always a half-finished agent write
EMPTY=$(find "$T" -type f -empty 2>/dev/null)
[ -n "$EMPTY" ] && { fail "zero-byte files:"; echo "$EMPTY" | sed 's/^/        /' | head -10; }

# unresolved merge markers / scaffold placeholders anywhere in the tree
# NOTE: config.json is NOT excluded any more. The top-level tests/config.json in
# an MT task looks like an inert stub, but the eval-gt/TBR harness renders
# /eval.sh FROM IT. An unsubstituted "<base_commit_sha>" there produces
#   /eval.sh: line 5: syntax error near unexpected token '||'
# in every baseline AND golden phase, scoring 0.0 with F2P=0/0 before a single
# test runs. 16 of our MT tasks shipped this way. Excluding config.json from
# this scan is precisely what let it through.
MARK=$(grep -rlE '^(<{7}|={7}|>{7})( |$)|TODO_REPLACE|<owner>/<repo>|<base_commit|<repo>|FIXME_SCAFFOLD|XXX_PLACEHOLDER' "$T" --exclude-dir=audit --exclude-dir=audit 2>/dev/null)
[ -n "$MARK" ] && { fail "merge markers or placeholders left:"; echo "$MARK" | sed 's/^/        /' | head -10; }

# top-level tests/config.json: for MT this is the ONLY field eval-gt reads, and
# an ABSENT file permanently zeroes the DQE review signal. Neither is visible
# locally — harbor/trial/multi_step.py never imports load_swe_bench_config, so
# oracle/bench run/calibration physically cannot read this file. 3/3 green
# locally, SCORE 0.0 on the server.
IS_MT_FMT=0
grep -qE '^\s*format\s*=\s*"swe_bench_multi_turn"' "$T/task.toml" 2>/dev/null && IS_MT_FMT=1
if [ ! -f "$T/tests/config.json" ]; then
  if [ "$IS_MT_FMT" = 1 ] || [ "$MT" = 1 ]; then
    fail "top-level tests/config.json is MISSING — DQE review bundle cannot stage;"
    echo  "        the task's review signal will be a permanent zero (eval-gt looks fine)"
  fi
else
  CFGOK=1
  python3 - "$T/tests/config.json" "$T" <<'PY2' || { FAIL=1; CFGOK=0; }
import json,re,sys,glob,os
c=json.load(open(sys.argv[1])); t=sys.argv[2]; bad=False
bc=str(c.get("base_commit","")); repo=str(c.get("repo",""))
if not re.fullmatch(r'[0-9a-f]{40}', bc):
    print(f"        base_commit is not a 40-hex sha: {bc!r}")
    print( "        eval-gt interpolates this UNQUOTED into /eval.sh -> syntax error, F2P=0/0")
    bad=True
if "/" not in repo or repo.startswith("<"):
    print(f"        repo is not owner/name: {repo!r}")
    print( "        the SERVER License gate reads this — a placeholder is a silent false-pass")
    bad=True
# must agree with every step config AND with the Dockerfile
steps=[json.load(open(f)) for f in sorted(glob.glob(os.path.join(t,"steps","*","tests","config.json")))]
sb={str(x.get("base_commit","")) for x in steps}
if steps and sb and bc and sb != {bc}:
    print(f"        base_commit disagrees with steps: top={bc!r} steps={sb}"); bad=True
try:
    if bc and bc not in open(os.path.join(t,"environment","Dockerfile")).read():
        print(f"        base_commit {bc[:12]} does not appear in environment/Dockerfile"); bad=True
except OSError: pass
sys.exit(1 if bad else 0)
PY2
  [ "$CFGOK" = 1 ] && pass "top-level tests/config.json: real sha, real repo, agrees with steps + Dockerfile"
fi

NF=$(find "$T" -type f | wc -l)
[ "$FAIL" = 0 ] && pass "inventory clean: $NF files, all parse, no strays/empties/placeholders"

# what is actually about to be pushed — review this, do not skim it
if git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
  CH=$(git -C "$REPO" status --porcelain -- "$T" 2>/dev/null)
  if [ -n "$CH" ]; then
    echo "        files changed vs git HEAD ($(echo "$CH" | wc -l)):"
    echo "$CH" | sed 's/^/          /' | head -25
    echo "        review the full diff before pushing:  git -C $REPO diff -- $T"
  fi
fi

hdr "TIER 1 — local structural (what bench validate runs)"
if [ -n "$FAST" ]; then
  warn "skipped (--fast). Run without --fast before pushing."
else
  OUT=$(timeout 400 codimango bench validate -p "$T" --structural-only 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
  # 2026-09-30: this used to demand `Overall: PASS` and FAIL on anything else, which made
  # `Overall: WARN` blocking. It is not. The validator emits its own severities, and it emits
  # `WARN Internet Access` for EVERY task that sets allow_internet=false and installs system
  # packages in the Dockerfile -- i.e. for every properly air-gapped task. Treating that as a
  # blocking FAIL pushed the author toward allow_internet=true purely to clear a local gate,
  # which is the opposite of what the warning is asking for. Mirror the validator's own
  # severity instead: FAIL is blocking, WARN is a warning, PASS is a pass.
  if echo "$OUT" | grep -qE "Overall: PASS"; then pass "bench validate --structural-only: Overall PASS"
  elif echo "$OUT" | grep -qaE "^FAIL"; then
    fail "bench validate --structural-only reported FAIL rows"; echo "$OUT" | grep -aE "^FAIL" | sed 's/^/        /' | head -10
  elif echo "$OUT" | grep -qE "Overall: WARN"; then
    warn "bench validate --structural-only: Overall WARN, no FAIL rows — read each warning and decide"
    echo "$OUT" | grep -aE "^WARN" | sed 's/^/        /' | head -10
  else fail "bench validate --structural-only produced no recognisable verdict"; echo "$OUT" | tail -10 | sed 's/^/        /'; fi
fi

hdr "TIER 2 — server-only checks (local validate does NOT run these)"

# --- License -------------------------------------------------------------
# Server, verbatim: "only CreativeML OpenRAIL-M / Ethos is prohibited".
# That is the ONLY hard block. Copyleft (GPL/AGPL) is a PLUS for this benchmark
# — SWE-bench Pro deliberately chose copyleft repos as contamination-resistant.
# AGPL/SSPL/Commons Clause warn rather than fail: they may be blocked by a
# separate Meta-wide OSS policy, which is not the same gate. Confirm, don't skip.
# Prefer step configs — the top-level config.json is a stub carrying the
# "<owner>/<repo>" placeholder and would otherwise win the head -1.
UP=$(grep -ohE '"repo"[[:space:]]*:[[:space:]]*"[^"<]+"' "$T"/steps/*/tests/config.json "$T"/tests/config.json 2>/dev/null \
     | sed 's/.*"repo"[^"]*"\([^"]*\)".*/\1/' | grep -v '^<' | head -1)
UPNAME="${UP##*/}"
LIC_SRC=""
if [ -n "$UPNAME" ]; then
  for guess in $HOME/repos-ext/*; do
    [ -d "$guess" ] || continue
    [ "$(basename "$guess")" = "$UPNAME" ] && { LIC_SRC="$guess"; break; }
  done
  # fall back to a fuzzy match (clone dir may differ from the repo name)
  if [ -z "$LIC_SRC" ]; then
    for guess in $HOME/repos-ext/*; do
      [ -d "$guess" ] || continue
      case "$UPNAME" in *"$(basename "$guess")"*|"$(basename "$guess")"*) LIC_SRC="$guess"; break;; esac
    done
  fi
fi
if [ -n "$LIC_SRC" ]; then
  LTXT=$(head -40 "$LIC_SRC"/LICENSE* "$LIC_SRC"/COPYING* 2>/dev/null | tr 'A-Z' 'a-z')
  if echo "$LTXT" | grep -qE "openrail|ethos"; then
    fail "License: PROHIBITED (CreativeML OpenRAIL-M / Ethos) in $LIC_SRC"
  elif echo "$LTXT" | grep -qE "affero|sspl|server side public|commons clause|noncommercial|non-commercial"; then
    warn "License: $(basename "$LIC_SRC") is AGPL/SSPL/NC-like — passes the SWE gate, but confirm Meta OSS policy"
  elif [ -n "$LTXT" ]; then pass "License: eligible ($(basename "$LIC_SRC"))"
  else warn "License: no LICENSE/COPYING found in $LIC_SRC — server may still pass it"; fi
else warn "License: could not locate the upstream clone; verify by hand"; fi

# --- SWE Config: no git clean in before_repo_set_cmd ---------------------
# Server-only rule, verbatim from its structural "SWE Config" check:
#   "before_repo_set_cmd runs git clean, which discards the agent's changes
#    before the tests are graded ... Restore gold test files with a path-scoped
#    `git checkout <commit> -- <test paths>` instead."
# It rejects ANY git clean, even path-scoped (`git clean -fdx -- spec/`), and
# validation halts there, so nothing else runs. Local validate does not check
# it: ruby-auth0-lazy (9d208f4, 2026-10-02) passed every local tier and sat at
# "No oracle trials run" until this was found. Do untracked-file cleanup inside
# tests/test.sh instead, after before_repo_set_cmd and before applying the
# hidden test patch.
GC_BAD=0
for C in "$T"/tests/config.json "$T"/steps/*/tests/config.json; do
  [ -f "$C" ] || continue
  python3 - "$C" <<'PY' || GC_BAD=1
import json, re, sys
c = json.load(open(sys.argv[1]))
for k in ("before_repo_set_cmd", "BEFORE_REPO_SET_CMD"):
    v = str(c.get(k) or "")
    if re.search(r"\bgit\b[^;&|\n]*\bclean\b", v):
        print(f"        {k} in {sys.argv[1]} runs git clean: {v.strip()[:120]!r}")
        sys.exit(1)
PY
done
if [ "$GC_BAD" = 0 ]; then pass "SWE Config: no git clean in before_repo_set_cmd"
else fail "SWE Config: before_repo_set_cmd runs git clean (server rejects it; move cleanup into tests/test.sh)"; fi

# --- SWE Step Configs: selected_test_files_to_run present ----------------
# Server-only check; missed on jsondiffpatch-delta-squash 5a3fd86 (2026-10-13).
STF_MISSING=""
for C in "$T"/steps/*/tests/config.json; do
  [ -f "$C" ] || continue
  python3 -c 'import json,sys; c=json.load(open(sys.argv[1])); v=c.get("selected_test_files_to_run"); sys.exit(0 if isinstance(v,list) and v else 1)' "$C" \
    || STF_MISSING="$STF_MISSING $(basename "$(dirname "$(dirname "$C")")")"
done
if [ -z "$STF_MISSING" ]; then pass "SWE Step Configs: selected_test_files_to_run present"
else fail "SWE Step Configs: missing selected_test_files_to_run in:$STF_MISSING (server structural check fails)"; fi

# --- SWE Step Configs ----------------------------------------------------
if [ "$MT" = 1 ]; then
  BAD=0
  for s in "${STEPS[@]}"; do
    C="$s/tests/config.json"
    [ -f "$C" ] || { fail "SWE Step Configs: missing $C"; BAD=1; continue; }
    python3 - "$C" <<'PY' || BAD=1
import json,sys
c=json.load(open(sys.argv[1]))
need=["repo","base_commit","patch","test_patch","fail_to_pass","pass_to_pass"]
missing=[k for k in need if not c.get(k)]
if missing: print(f"        missing/empty in {sys.argv[1]}: {missing}"); sys.exit(1)
if any("<owner>" in str(c.get(k,"")) or "<repo>" in str(c.get(k,"")) or "<base_commit" in str(c.get(k,"")) for k in c):
    print(f"        scaffold placeholder left in {sys.argv[1]}"); sys.exit(1)
# The SERVER's check of the same name ALSO validates that each diff is a
# well-formed unified diff. Ours only checked field presence, so it returned
# PASS on chromem-go while the server failed it with
#   "patch is not a valid unified diff (missing \"diff --git\" header)"
# — a green light on a check that never looked at what broke. The same defect
# has been fixed by hand before on circl and protoc ("re-header step-2 oracle
# patches as valid unified diffs"), so it recurs. A leading `--- a/...` with no
# `diff --git` line stops server validation before anything else runs.
for k in ("patch", "test_patch"):
    body = str(c.get(k) or "").lstrip()
    if body and not body.startswith("diff --git"):
        print(f'        {k} is not a valid unified diff in {sys.argv[1]}:'
              f' first line is {body.splitlines()[0][:60]!r}, expected "diff --git"')
        sys.exit(1)
PY
  done
  [ "$BAD" = 0 ] && pass "SWE Step Configs: all $((${#STEPS[@]})) steps have required step-level fields"
  [ "$BAD" = 1 ] && fail "SWE Step Configs: one or more steps incomplete"
fi

# --- SWE Step Parsers ----------------------------------------------------
if [ "$MT" = 1 ]; then
  MISS=0
  for s in "${STEPS[@]}"; do [ -f "$s/tests/parser.py" ] || { fail "SWE Step Parsers: missing $s/tests/parser.py"; MISS=1; }; done
  [ "$MISS" = 0 ] && pass "SWE Step Parsers: all steps have tests/parser.py"
fi

# --- Test result parser: subtest-aware (template generation >= 2) ----------
# Server-only structural check, verbatim (djmoney-money-expressions-pair 8f387e95,
# 2026-10-18): "Test result parser: FAIL tests/parser.py is an older version of
# the test-result parser, which can grade this task incorrectly: failures inside
# a sub-test are not detected (tests/parser.py: subtest-blind)".
# Under unittest subTest / the subtests fixture the parent's verbose line still
# reads PASSED; the failure only appears as SUBFAIL / SUBFAILED, so a parser
# that doesn't read those words pays a full reward for a failed solution.
# Markers, from diffing generation 1 vs 2 of the template:
#   - `# codimango-parser-version: 2` stamp on line 1 (gen 1 says `: 1`)
#   - SUBFAIL / SUBFAILED in the status-word map (absent from every gen-1 file)
# SUBFAIL is the behavioural marker and is what blocks; the stamp only warns.
# Scope: pytest-graded parsers only (the server only proposes the refresh to
# tasks that grade pytest output) -- detected by a non-comment pytest mention in tests/*.sh.
# Fix: `codimango task template sync --file tests/parser.py --type <type>
#   codimango/<task>` writes parser.py.new; adopt it verbatim (append any CTRF
#   or output-shape adaptation inside main() only).
SB_BAD=""; SB_WARN=""; SB_N=0
for P in "$T"/tests/parser.py "$T"/steps/*/tests/parser.py; do
  [ -f "$P" ] || continue
  D=$(dirname "$P")
  # Comment lines are stripped: the stock scaffold test.sh mentions pytest in
  # comments even on go/cargo tasks (concourse false positive, 2026-10-19).
  cat "$D"/*.sh 2>/dev/null | grep -vE '^[[:space:]]*#' | grep -qiw pytest || continue
  SB_N=$((SB_N+1))
  REL=${P#"$T"/}
  GEN=$(grep -m1 -oE 'codimango-parser-version:[[:space:]]*[0-9]+' "$P" | grep -oE '[0-9]+$')
  if ! grep -qE '\bSUBFAIL(ED)?\b' "$P"; then
    SB_BAD="$SB_BAD $REL(gen ${GEN:-unstamped})"
  elif [ -z "$GEN" ] || [ "$GEN" -lt 2 ]; then
    SB_WARN="$SB_WARN $REL(gen ${GEN:-unstamped})"
  fi
done
if [ "$SB_N" = 0 ]; then
  pass "Test result parser: no pytest-graded parser.py (subtest check n/a)"
elif [ -n "$SB_BAD" ]; then
  fail "Test result parser: subtest-blind (no SUBFAIL/SUBFAILED handling):$SB_BAD — run \`codimango task template sync --file tests/parser.py\` and adopt parser.py.new"
else
  pass "Test result parser: subtest-aware ($SB_N pytest-graded parser(s))"
  [ -n "$SB_WARN" ] && warn "Test result parser: reads SUBFAIL but lacks the gen-2 stamp:$SB_WARN — server may compare against the template; prefer the synced file"
fi

hdr "TIER 3 — landmines no validator catches"

# 0. AUTHORSHIP — BLOCKING on the restricted surfaces: every instruction.md and everything
#    under tests/. Other files follow the ownership table in runbooks/2-build.md. Measured
#    2026-09-30: the gate bands a
#    matchScore against the submitted file, monotonic, threshold ~0.05 -- 0.0298 cleared,
#    0.0631 and 0.2020 did not. It is repairable by re-authoring far enough, but it costs a
#    full validation cycle every attempt, so the only cheap move is never writing the file.
#    This was a B5 checklist line and checklist lines get skipped; it runs here now.
AUDIT_SH="$HOME/swebench-playbook/tools/authorship-audit.sh"
if [ -x "$AUDIT_SH" ]; then
  # Since the last commit that touched this task: we gate NEW writes. Historical ones are
  # already logged server-side and blocking on them makes a contaminated task unrepairable.
  _since=$(git -C "$REPO" log -1 --format=%cs -- "$T" 2>/dev/null || date +%F)
  # 2026-09-30: `|| date +%F` only fires when git EXITS non-zero. On a brand-new task with no
  # commit yet, git exits 0 and prints NOTHING, so `--since ""` reached the audit script, whose
  # `${3:?}` treats empty as unset, exited 2, and preflight rendered that as
  # "Authorship: Claude wrote inside <task>/ since " — a hard FAIL on a task with zero Claude
  # writes, and with an empty date in the message as the only clue. Every first push hits this.
  [ -n "$_since" ] || _since=$(git -C "$REPO" log -1 --format=%cs 2>/dev/null || date +%F)
  [ -n "$_since" ] || _since=$(date +%F)
  if "$AUDIT_SH" "$T" --since "$_since" >/tmp/.pf-authorship.$$ 2>&1; then
    pass "Authorship: no Claude write to instruction.md or tests/** since $_since"
  else
    { fail "Authorship: Claude wrote a restricted file in $(basename "$T")/ since $_since — provenance may flag this"
      grep -E '^  \[' /tmp/.pf-authorship.$$ | head -4 | sed 's/^/     /'; }
  fi
  rm -f /tmp/.pf-authorship.$$
else
  warn "Authorship: audit tool not found at $AUDIT_SH — check skipped, NOT cleared"
fi

# 1. contamination canary (ships on line 1 of the scaffold Dockerfile)
# audit/ is prose ABOUT the task -- a REVIEW-LEDGER that documents a canary
# finding necessarily quotes the marker string, which tripped this check on
# 2026-09-24. It is metadata, not content the solver ever sees.
if grep -rqi --exclude-dir=audit "canary\|BENCHMARK DATA SHOULD NEVER" "$T" 2>/dev/null; then
  { fail "Contamination: canary marker present in:"
     grep -rilE 'canary|BENCHMARK DATA SHOULD NEVER' "$T" | sed "s|^$T/|        |" | head -6; }
else pass "Contamination: no canary marker"; fi

# 2. oracle patch must carry NO test files (else test_patch collides)
BADP=0
for s in "${STEPS[@]:-$T}"; do
  C="$s/tests/config.json"; [ -f "$C" ] || continue
  python3 - "$C" <<'PY' || BADP=1
import json,re,sys
c=json.load(open(sys.argv[1]))
files=re.findall(r'^\+\+\+ b/(\S+)', c.get("patch",""), re.M)
bad=[f for f in files if re.search(r'(^|/)tests?/|_test\.|test_.*\.py$|\.rs$' if False else r'(^|/)tests?/|_test\.go$|test_.*\.py$|_spec\.rb$', f)]
if bad: print(f"        oracle patch touches test files in {sys.argv[1]}: {bad[:4]}"); sys.exit(1)
PY
done
[ "$BADP" = 0 ] && pass "Oracle patch carries source only (no test files)" || fail "Oracle patch contains test files — test_patch will collide"

# 3. new files in test_patch need 'new file mode' headers (git add -N)
BADN=0
for s in "${STEPS[@]:-$T}"; do
  C="$s/tests/config.json"; [ -f "$C" ] || continue
  python3 - "$C" <<'PY' || BADN=1
import json,re,sys
tp=json.load(open(sys.argv[1])).get("test_patch","")
for m in re.finditer(r'diff --git a/(\S+) b/\S+\n(.*?)(?=diff --git |\Z)', tp, re.S):
    body=m.group(2)
    if '--- /dev/null' in body and 'new file mode' not in body:
        print(f"        {m.group(1)} added without 'new file mode' header ({sys.argv[1]})"); sys.exit(1)
PY
done
[ "$BADN" = 0 ] && pass "test_patch new files have new-file-mode headers" || fail "test_patch adds a file without 'new file mode' — 3-way merge will fail"

# 4. mirrored casing keys must agree (test.sh hard-errors if they disagree)
BADC=0
for s in "${STEPS[@]:-$T}"; do
  C="$s/tests/config.json"; [ -f "$C" ] || continue
  python3 - "$C" <<'PY' || BADC=1
import json,sys
c=json.load(open(sys.argv[1]))
for lo,up in (("fail_to_pass","FAIL_TO_PASS"),("pass_to_pass","PASS_TO_PASS")):
    if up in c and sorted(c.get(lo,[]))!=sorted(c.get(up,[])):
        print(f"        {lo} vs {up} DISAGREE in {sys.argv[1]}"); sys.exit(1)
PY
done
[ "$BADC" = 0 ] && pass "Mirrored FAIL_TO_PASS/PASS_TO_PASS keys agree" || fail "Casing keys disagree — test.sh hard-errors, reward 0 on every trial"

# 5. reward must not come from a process exit status
BADR=0
for s in "${STEPS[@]:-$T}"; do
  F="$s/tests/test.sh"; [ -f "$F" ] || continue
  grep -qE '\$\?|PIPESTATUS' "$F" && { warn "reward may derive from exit status in $F (validator flags this)"; BADR=1; }
done
[ "$BADR" = 0 ] && pass "Reward derives from parsed results, not exit status"

# 6. Go tasks: pass_to_pass ids must be <import_path>::<TestFunc>
for s in "${STEPS[@]:-$T}"; do
  C="$s/tests/config.json"; [ -f "$C" ] || continue
  python3 - "$C" <<'PY'
import json,sys
c=json.load(open(sys.argv[1]))
ids=c.get("pass_to_pass",[])+c.get("fail_to_pass",[])
if any(i.startswith("github.com/") or i.startswith("golang.org/") for i in ids):
    bare=[i for i in ids if "::" not in i]
    if bare: print(f"  \033[31mFAIL\033[0m  Go ids without ::TestFunc (can never match): {bare[:3]}")
PY
done

# 7. cascade: step N patch must be the DELTA from step N-1 (plain git apply)
if [ "${#STEPS[@]}" -gt 1 ]; then
  warn "Cascade not verified here — confirm base -> step1 -> step2 applies with PLAIN git apply (no --3way, no fuzz)"
fi

# 8. solve.sh executable + no literal /tmp paths
for s in "${STEPS[@]:-$T}"; do
  F="$s/solution/solve.sh"; [ -f "$F" ] || continue
  [ -x "$F" ] || fail "not executable: $F"
  grep -qE 'mktemp +/tmp/|> */tmp/[a-z]' "$F" && warn "literal /tmp path in $F (validator flags; use mktemp -t NAME.XXXXXX)"
done

# 9. artifacts must be declared — without it you cannot extract what the models
#    wrote, and the whole gradient loop degrades to guessing from trajectories.
if grep -qE '^[[:space:]]*artifacts[[:space:]]*=' "$T/task.toml" 2>/dev/null; then
  pass "artifacts declared in task.toml"
elif [ -z "$QUIET" ]; then
  adv "artifacts not declared — SUGGESTED DEFAULT for new tasks (cheap, and makes tuning a dry-run). Not required."
  advnote "candidates from the oracle patch:"
  python3 - "$T" <<'PY'
import json,re,sys,glob,os
t=sys.argv[1]; files=set()
for c in sorted(glob.glob(os.path.join(t,"steps","*","tests","config.json"))) or [os.path.join(t,"tests","config.json")]:
    if not os.path.exists(c): continue
    files.update(re.findall(r'^\+\+\+ b/(\S+)', json.load(open(c)).get("patch",""), re.M))
for f in sorted(files)[:8]: print(f'          "/app/{f}",')
PY
fi

# 10. size floor — SWE-bench Pro excludes 1-10 LOC edits; mean is 107 lines.
#     A step under ~20 net-added behavioural lines will not calibrate.
python3 - "$T" <<'PY'
import json,re,sys,glob,os
t=sys.argv[1]
for c in sorted(glob.glob(os.path.join(t,"steps","*","tests","config.json"))):
    p=json.load(open(c)).get("patch","")
    net=sum(1 for l in p.splitlines()
            if l.startswith("+") and not l.startswith("+++") and l[1:].strip()
            and not l[1:].lstrip().startswith(("#","//","*","/*")))
    step=os.path.basename(os.path.dirname(os.path.dirname(c)))
    if net < 20: print(f"  \033[36mADV \033[0m  size floor: {step} adds only {net} net lines (<20 rarely calibrates)")
PY

# 11. xfail/skip semantics — upstream grading counts XFAIL as PASSED and
#     SKIPPED as MAINTAINED. A parser that treats them as not-passed is a
#     silent false-negative generator on every trial.
for s in "${STEPS[@]:-$T}"; do
  P="$s/tests/parser.py"; [ -f "$P" ] || continue
  if grep -qiE 'xfail|xpass' "$P"; then pass "parser handles xfail/xpass ($(basename "$s"))"
  elif grep -qiE 'pytest|\.py"' "$s/tests/test.sh" 2>/dev/null; then
    adv "parser has no xfail/xpass handling ($(basename "$s")) — upstream counts XFAIL as PASSED"
  fi
done

# 12. error2pass — a test that is UNCOLLECTABLE pre-patch (ImportError,
#     SyntaxError, build failure) is not a legitimate fail_to_pass. This was
#     100% of SWE-Factory's false positives.
for s in "${STEPS[@]:-$T}"; do
  P="$s/tests/parser.py"; [ -f "$P" ] || continue
  grep -qiE 'error|ERROR' "$P" || adv "parser never matches ERROR ($(basename "$s")) — collection errors may score as plain fails"
done

# 13. de-scaffolding lint — the instruction should be 1-2 paragraphs of informal
#     prose with 2-4 requirements. Lists/bullets/headings/emphasis let a model
#     transcribe a spec instead of reasoning, and reliably produce 5/5.
for s in "${STEPS[@]:-$T}"; do
  I="$s/instruction.md"; [ -f "$I" ] || I="$T/instruction.md"; [ -f "$I" ] || continue
  [ -n "$QUIET" ] && continue
  if [ ! -s "$I" ] || [ "$(wc -w < "$I")" -lt 40 ]; then
    fail "instruction: $(basename "$s") is empty or a stub ($(wc -w < "$I") words) — unscaffolded"
    continue
  fi
  B=$(grep -cE '^[[:space:]]*([-*+]|[0-9]+[.)])[[:space:]]' "$I")
  H=$(grep -cE '^#{1,6}[[:space:]]' "$I")
  E=$(grep -coE '\*\*[^*]+\*\*|`[A-Z_]{4,}`|REQUIREMENT' "$I")
  W=$(wc -w < "$I")
  S="$(basename "$s")"
  # one H1 title is normal; 2+ headings or any bullet list is real scaffolding
  OK=1
  [ "$B" -gt 0 ] && { adv "de-scaffolding: $S has $B list items — prose only, no bullets or numbered requirements"; OK=0; }
  [ "$H" -gt 1 ] && { adv "de-scaffolding: $S has $H headings — one title at most"; OK=0; }
  [ "$E" -gt 4 ] && { adv "de-scaffolding: $S has $E emphasis/REQUIREMENT markers — enumerated specs get one-shot"; OK=0; }
  [ "$W" -gt 350 ] && { adv "de-scaffolding: $S is $W words — target 1-2 paragraphs"; OK=0; }
  [ "$OK" = 1 ] && pass "de-scaffolding: $S is prose, $W words"
done

# --- patch/test_patch must be GIT-format unified diffs -------------------------
# The local SWE Step Configs stand-in only checked key presence and placeholders,
# never the diff FORMAT. A step-2 patch generated with GNU `diff -Naur` (with
# wall-clock timestamps, no index line) passed every local gate and the SERVER
# failed it: "patch is not a valid unified diff (missing \"diff --git\" header)".
for s_ in "${STEPS[@]:-$T}"; do
  C_="$s_/tests/config.json"; [ -f "$C_" ] || continue
  python3 - "$C_" "$(basename "$s_")" <<'PY'
import json,sys
cfg=json.load(open(sys.argv[1])); step=sys.argv[2]
for key in ("patch","test_patch"):
    body=cfg.get(key) or ""
    if not body.strip(): continue
    heads=[l for l in body.splitlines() if l.startswith("diff ")]
    bad=[h for h in heads if not h.startswith("diff --git")]
    if bad or (not heads and "--- " in body):
        print(f"  \033[31mFAIL\033[0m  {step}: {key} is not a GIT-format diff")
        print(f"        found: {(bad[:1] or ['<no diff header at all>'])[0][:78]}")
        print( "        regenerate with `git diff`, not `diff -Naur`. The server rejects it:")
        print( '        "patch is not a valid unified diff (missing \"diff --git\" header)"')
        sys.exit(3)
PY
  [ $? -eq 3 ] && FAIL=1
done

# 14. contract coverage — every public symbol the oracle ADDS must be named in
#     the instruction, or the task is unsolvable-by-guessing. webauthn lost all
#     three trials on an error class the instruction never mentioned.
for s in "${STEPS[@]:-$T}"; do
  C="$s/tests/config.json"; I="$s/instruction.md"
  [ -f "$C" ] && [ -f "$I" ] || continue
  [ -n "$QUIET" ] && continue
  # Locate a base checkout so "new" means new TO THE REPO, not merely
  # "on an added line". Without this the check called ResponseTrailer new on a
  # repo containing 107 of them, because the oracle adds a method of that name.
  BASECO=""
  # w4-1 2026-09-23: the bare /tmp globs below are NOT task-scoped and silently
  # picked another task's base checkout (connect-go's) while grading concourse,
  # which turned a correct in-base symbol into a BLOCKING "grader pins NEW
  # symbols" FAIL. An explicit, task-scoped override wins over the globs.
  if [ -n "${SWEBENCH_BASE_CHECKOUT:-}" ] && [ -d "${SWEBENCH_BASE_CHECKOUT}" ]; then
    BASECO="${SWEBENCH_BASE_CHECKOUT}"
  else
  # Task-scoped ONLY. A bare /tmp glob matched the FIRST base checkout on the host
  # and kept winning for every task afterwards -- it graded concourse's symbols
  # against connect-go's source and emitted a false BLOCKING kill. If no
  # task-scoped checkout is found the check degrades to WARN, which is correct:
  # an unverifiable answer must not look like a verified one.
  for cand in "${SWEBENCH_BASE_CHECKOUT:-}" "/tmp/$(basename "$T")-base" \
              "/tmp/$(basename "$T")/base" "$T/../.clones/$(basename "$T")"; do
    [ -n "$cand" ] && [ -d "$cand" ] && { BASECO="$cand"; break; }
  done
  fi
  python3 - "$C" "$I" "$(basename "$s")" "$BASECO" <<'PY'
import json,re,sys,subprocess,os
cfg=json.load(open(sys.argv[1]))
instr=open(sys.argv[2]).read(); step=sys.argv[3]
baseco=sys.argv[4] if len(sys.argv)>4 else ""
added="\n".join(l[1:] for l in cfg.get("patch","").splitlines()
                if l.startswith("+") and not l.startswith("+++"))
syms=set()
for pat in (r'^\s*def\s+([a-zA-Z_]\w*)', r'^\s*class\s+(\w+)',
            r'^\s*func\s+(?:\([^)]*\)\s*)?([A-Z]\w*)', r'^\s*(?:pub\s+)?fn\s+(\w+)',
            r'^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)'):
    syms.update(re.findall(pat, added, re.M))
syms={s for s in syms if not s.startswith("_") and len(s) > 3}

# The CONTRACT is only what the grading test actually touches. Internal helpers
# the solver is free to name differently are not contract and must NOT be in the
# instruction — naming them would be a how-to-solve hint.
graded=cfg.get("test_patch","") + "\n" + "\n".join(cfg.get("fail_to_pass",[]))
contract={s for s in syms if re.search(r'\b'+re.escape(s)+r'\b', graded)}
internal=syms-contract
missing=sorted(s for s in contract if not re.search(r'\b'+re.escape(s)+r'\b', instr))
leaked=sorted(s for s in internal if re.search(r'\b'+re.escape(s)+r'\b', instr))

# A symbol the oracle adds may ALREADY EXIST in the repo -- adding a method whose
# name matches an existing one is routine. Only symbols absent from the base tree
# are genuinely new, and only those need naming under D1.
inbase=set()
if baseco and os.path.isdir(baseco) and missing:
    for sym in list(missing):
        try:
            r=subprocess.run(["grep","-rqw",sym,baseco],capture_output=True,timeout=60)
            if r.returncode==0: inbase.add(sym)
        except Exception: pass
    missing=[m for m in missing if m not in inbase]
if inbase:
    print(f"  \033[32mPASS\033[0m  contract: {len(inbase)} graded symbol(s) already exist at base, "
          f"no naming required: {sorted(inbase)[:4]}")

if missing and not baseco:
    print(f"  \033[33mWARN\033[0m  grader may depend on NEW symbols: {missing[:6]}")
    print( "        No base checkout found, so 'new' is UNVERIFIED — a symbol the oracle")
    print( "        adds may already exist in the repo. Re-run with a base clone present,")
    print( "        or run instruction-lint.py, before trusting this.")
elif missing:
    print(f"  \033[31mFAIL\033[0m  grader pins NEW symbols the contract never states: {missing[:6]}")
    print( "        D1: a new name the graded tests PIN must be named in the contract.")
    print( "        Silent contract + pinning test is the illegal configuration -- it produced")
    print( "        BAD_GRADING_WRONG on 4 of 4 peer tasks. Two fixes:")
    print( "        1. re-shape so the behaviour is observable through EXISTING public API")
    print( "        2. have MUSE (mc2.sh) name them in instruction.md (never Claude, never Codex)")
    sys.exit(3)
elif contract:
    print(f"  \033[32mPASS\033[0m  contract: {step} names all {len(contract)} graded symbols")
if leaked:
    print(f"  \033[36mADV \033[0m  contract: {step} names internals the test never grades: {leaked[:6]}")
    print( "        possible how-to-solve hint rather than contract")
PY
  # The heredoc's exit status was previously discarded, so a FAIL printed but the
  # RESULT block still said "safe to push" and preflight exited 0. A blocking
  # finding must block.
  [ $? -eq 3 ] && FAIL=1
done

#############################################################################
# PROPOSED ADDITION 1 — TIER 3, BLOCKING, zero cost (no Docker, ~50ms).
# Insert anywhere in the TIER 3 block of preflight.sh.
#############################################################################

# --- verifier idempotency (server runs each step's verifier TWICE) ----------
# The server's multi-turn runner calls _maybe_run_step_baseline_precheck: for
# the oracle agent it runs the step's verifier ONCE BEFORE solve.sh (eval-GT
# no-op guard) and again after. `codimango bench run` uses codimango-bench.par,
# whose bundled harbor/trial/multi_step.py has no such pass — so a test.sh that
# is not idempotent scores 3/3 locally and 0/3 on the server.
# spire-workload-api-delivery-readiness died exactly this way, 2026-09-18.
if [ -d "$T/steps" ]; then
python3 - "$T" <<'PY'
import json, os, re, sys, glob
task = sys.argv[1]
def pfiles(p):
    out=[];cur=None
    for l in p.split("\n"):
        m=re.match(r'^diff --git a/(\S+) b/(\S+)',l)
        if m: cur={"p":m.group(2),"new":False};out.append(cur)
        elif cur and l.startswith("new file mode"): cur["new"]=True
    return out
created={}; bad=[]
for cfgp in sorted(glob.glob(os.path.join(task,"steps","*","tests","config.json"))):
    step=cfgp.split("/steps/")[1].split("/")[0]
    cfg=json.load(open(cfgp))
    tp=cfg.get("test_patch") or cfg.get("TEST_PATCH") or ""
    if not tp.strip():
        continue
    sh=os.path.join(os.path.dirname(cfgp),"test.sh")
    s=open(sh).read() if os.path.exists(sh) else ""
    # Private-tree graders (ssort-import-time-semantics-preservation, 2026-10-17):
    # test.sh never applies anything; its runner copies the repo into a mkdtemp
    # tree, applies test_patch THERE, and the EXIT trap deletes that tree. The
    # test-patch files never reach /app, so nothing can collide on a re-run
    # (TIER 4b replay PASSED while this read as FAIL). Skip only that exact shape.
    rsp=os.path.join(os.path.dirname(cfgp),"run_script.sh")
    rs=open(rsp).read() if os.path.exists(rsp) else ""
    applies=[l for l in rs.split("\n") if '"apply"' in l and "--numstat" not in l]
    if (s and not re.search(r'\bapply\b', s) and re.search(r'^tree\s*=.*mkdtemp', rs, re.M)
            and applies and all("str(tree)" in l for l in applies)):
        continue
    # Map every `name() { ... \n}` body. The cleanup function is NOT always
    # literally named `cleanup` (rustcrypto ships `cleanup_and_reward`) and may
    # delegate the purge to a helper it calls. Matching only "cleanup() {" read
    # an empty body and reported a false FAIL on a task whose cleanup was
    # correct all along, so match any cleanup-ish name and inline one level of
    # the helpers it calls.
    funcs={}
    for m in re.finditer(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{', s, re.M):
        funcs[m.group(1)]=s[m.end():].split("\n}",1)[0]
    # The name heuristic is still not enough: a MetaCode-authored verifier called
    # its EXIT handler `remove_leftovers`, which contains no "cleanup" at all, so
    # the body came back empty and a correct purge read as FAIL while TIER 4b's
    # real double-invocation replay PASSED. Whatever `trap ... EXIT` names IS the
    # cleanup, by definition, so take that too.
    trapped={m.group(1) for m in re.finditer(r'\btrap\s+[\'"]?([A-Za-z_]\w*)[\'"]?[^\n]*\bEXIT\b', s)}
    picked={n for n in funcs if "cleanup" in n} | (trapped & set(funcs))
    body="".join(funcs[n] for n in picked)
    for n in list(picked):
        for callee in funcs:
            if callee!=n and re.search(r'(^|[\s;&|(])'+re.escape(callee)+r'\b',funcs[n],re.M):
                body+=funcs[callee]
    # a cleanup that undoes the test patch makes every invocation independent
    # Known purge idioms, plus the general form: a cleanup that DERIVES the paths
    # from the test patch at runtime and removes them. That last form is stronger
    # than the named idioms (it cannot drift from config.json) but matched none of
    # them, so a correct fix still read as FAIL. Require BOTH a reference to the
    # patch and an actual removal, so this stays tight.
    # Third form: the list is DERIVED outside the cleanup (so the body carries no
    # TEST_PATCH/--numstat reference) and the body restores per path by asking
    # whether it existed at HEAD. `git cat-file -e HEAD:<path>` inside a cleanup is
    # unambiguously that test, and it must be paired with an actual restore or
    # delete. A MetaCode-authored verifier that named its list PATCHED_LIST read as
    # FAIL here while TIER 4b's real double-invocation replay PASSED.
    purges = (any(k in body for k in ("APPLIED_TEST_FILES", "purge_path", "apply --reverse"))
              or (re.search(r'\brm\s+-f\b', body)
                  and re.search(r'TEST_PATCH|test_patch|--numstat', body))
              or (re.search(r'cat-file\s+-e\s+"?HEAD:', body)
                  and re.search(r'checkout\s+HEAD\s+--|\brm\s+-f\b', body)))
    fs=pfiles(tp)
    new={f["p"] for f in fs if f["new"]}
    mod={f["p"] for f in fs if not f["new"]}
    brs=(cfg.get("before_repo_set_cmd") or "").strip()
    restored=set()
    for line in brs.split("\n"):
        line=line.strip()
        if line.startswith("git checkout") and " -- " in line:
            restored |= set(line.split(" -- ",1)[1].split())
    for line in s.split("\n"):                      # some tasks restore inside test.sh
        m=re.search(r'git (?:-C \S+ )?checkout .*? -- (.+)$', line.strip())
        if m and not line.strip().startswith("#"):
            restored |= {x for x in m.group(1).split() if "/" in x}
    apply_blk=re.search(r'Applying (?:held-out )?test[_ ]patch.*?(?=git\s+(?:-C \S+\s+)?apply)',s,re.S)
    prerm=set()
    if apply_blk:
        rm=re.search(r'rm -f((?:[^\n]|\\\n)*)',apply_blk.group(0))
        if rm: prerm={x for x in re.split(r'[\s\\]+',rm.group(1)) if x}
    collide = {p for p in new if p in created}
    for p in new: created[p]=step
    if purges:                                  continue   # strongest guarantee
    if new <= prerm and mod <= restored:        continue
    if not new and mod and mod <= restored:     continue
    why=[]
    if mod & restored and new:
        why.append("before_repo_set_cmd reverts %s while the new file(s) %s survive "
                   "the first pass -> neither apply nor --reverse --check nor --3way "
                   "can succeed on the second" % (sorted(mod&restored), sorted(new)))
    if collide:
        why.append("re-creates %s that an earlier step already left in the tree" % sorted(collide))
    bad.append((step, why))                      # why == [] -> advisory only
blocking=[b for b in bad if b[1]]
for step,why in bad:
    if why:
        print("  \033[31mFAIL\033[0m  idempotency: %s test.sh cannot be run twice" % step)
        for w in why: print("        " + w)
        print("        fix: purge the test-patch paths in cleanup(), AFTER the reward is final")
    else:
        print("  \033[36mADV \033[0m  idempotency: %s leans on the `--reverse --check` "
              "'already present' branch" % step)
        print("        works today; breaks the moment anything reverts part of the patch")
if not bad:
    print("  \033[32mPASS\033[0m  idempotency: every step's test.sh survives a repeat invocation")
sys.exit(1 if blocking else 0)
PY
[ $? -ne 0 ] && FAIL=1
fi

#############################################################################
# PROPOSED ADDITION 2 — TIER 4b, BLOCKING, only under --with-oracle.
# Insert immediately after the existing TIER 4 oracle block.
# ~90s on a warm Docker layer cache; the image tag is stable so it caches.
#############################################################################

hdr "TIER 4b — server sequence replay (baseline verifier -> solve.sh -> graded verifier)"
if [ "$WITH_ORACLE" = "--with-oracle" ] && [ -d "$T/steps" ]; then
  IMG="preflight-idem-$T"
  if docker build -q -t "$IMG" -f "$T/environment/Dockerfile" "$T/environment" >/dev/null 2>&1; then
    CID=$(docker run -d --rm "$IMG" sleep infinity)
    RC=0
    for SD in "$T"/steps/*/; do
      SN=$(basename "$SD")
      docker exec "$CID" rm -rf /tests >/dev/null 2>&1
      docker exec "$CID" mkdir -p /tests /logs/verifier >/dev/null 2>&1
      docker cp "$SD/tests/." "$CID:/tests/" >/dev/null
      docker exec "$CID" bash /tests/test.sh >/dev/null 2>&1        # baseline pass
      B=$(docker exec "$CID" cat /logs/verifier/reward.txt 2>/dev/null)
      docker cp "$SD/solution/solve.sh" "$CID:/tmp/solve.sh" >/dev/null
      docker exec "$CID" bash /tmp/solve.sh >/dev/null 2>&1
      G=$(docker exec "$CID" bash -c 'bash /tests/test.sh >/dev/null 2>&1; cat /logs/verifier/reward.txt')
      [ "$B" = "1" ] && { fail "replay: $SN passes BEFORE solve.sh — no-op step (eval-GT defect)"; RC=1; }
      [ "$G" = "1" ] || { fail "replay: $SN graded reward=$G after a prior verifier pass in the same tree"; RC=1; }
    done
    docker rm -f "$CID" >/dev/null 2>&1
    [ "$RC" = 0 ] && pass "replay: every step scores 1 under the server's double-invocation"
  else
    warn "replay skipped — image build failed"
  fi
else
  warn "server-sequence replay not run (needs --with-oracle and a steps/ dir)"
fi


# 15/16. grading-correctness detectors (R08 / BAD_GRADING) — see grader-lint.py
python3 ~/.claude/skills/swebench-mt/grader-lint.py "$T" || FAIL=1


# 17. does instruction.md give away the answer? (policy 2026-09-22)
#     A symbol the instruction names that the repo does NOT contain at base is,
#     by definition, the answer handed over. Validated: open62541 (passing 1/5)
#     clean; graphiti (5/5) flagged for `include_decisions`/`not_allowlisted`.
if [ -n "$LIC_SRC" ]; then
  python3 ~/.claude/skills/swebench-mt/instruction-lint.py "$T" "$LIC_SRC" || FAIL=1
else
  warn "instruction-lint skipped — upstream clone not located"
fi

hdr "TIER 4 — oracle"
if [ "$WITH_ORACLE" = "--with-oracle" ]; then
  O=$(timeout 1800 codimango bench run -p "$T" -a oracle -k 3 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -aoE "Solved: [0-9]+/[0-9]+" | tail -1)
  case "$O" in *"3/3"*) pass "oracle $O";; "") fail "oracle run produced no result";; *) fail "oracle $O — must be 3/3 or calibration is SKIPPED entirely";; esac
else
  warn "oracle not run (pass --with-oracle). It MUST be 3/3 or the server skips calibration."
fi

hdr "RESULT"
echo "  lifecycle: $LIFE"
[ "$ADVN" -gt 0 ] && echo "  $ADVN advisory item(s) — quality suggestions, NOT requirements. Ignore freely."
if [ "$FAIL" = 0 ]; then
  echo "  safe to push. Remember: calibration is NOT predictable locally —"
  echo "  in-band is 1-3 of 5 on Avocado and LOWER IS BETTER. 4/5 is over the
  ceiling. Avocado 0/5 is NOT a failure by itself — the gate needs one pass
  and one fail ON THE SAME MODEL, and that model may be Opus or GPT."
  exit 0
else
  echo "  DO NOT PUSH — fix the FAILs above first (advisories are not FAILs)."
  exit 1
fi

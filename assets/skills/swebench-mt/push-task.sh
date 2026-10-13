#!/usr/bin/env bash
# push-task.sh — commit and push ONE task without touching anything else.
#
#   ./push-task.sh <task-dir> [--dry-run]
#
# The shared repo routinely holds dozens of unrelated uncommitted files: other
# agents' in-progress task dirs, another session's remediation, old sweeps. A
# careless `git add -u` or `git commit -a` ships all of it.
#
# `git add -u -- <path>` scopes what it ADDS, not what is already staged — that
# distinction has silently shipped unreviewed work twice. So: reset first,
# stage one path, VERIFY the staged set, only then commit.
set -uo pipefail
REPO="${REPO:-$HOME/swe-bench-pro-agvidit}"
T="${1:?usage: push-task.sh <task-dir> [--dry-run]}"; T="${T%/}"
DRY=""; [ "${2:-}" = "--dry-run" ] && DRY=1
cd "$REPO" || exit 2
[ -d "$T" ] || { echo "no such task dir: $T"; exit 2; }

echo "== 0. revision-gate stamp (precheck, Vidit 2026-10-13)"
# One command before ANY push: ~/swebench-playbook/tools/revision-gate/gate.py <task>
# It runs preflight, presubmit, provenance, step carry-forward, fake-pass probes, the
# reviewer agent and k2n x2, and stamps the exact task files it passed.
# PROVISIONAL until 3 independent agents verify the gate (ledger/VERIFY-revision-gate.md):
# while provisional, GATE_OVERRIDE="<reason>" pushes without a stamp and logs the reason.
GATE=~/swebench-playbook/tools/revision-gate/gate.py
if [ -f "$GATE" ] && python3 "$GATE" "$T" --repo "$REPO" --check-stamp; then :
elif [ -n "${GATE_OVERRIDE:-}" ]; then
  mkdir -p ~/swebench/gate-stamps
  printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$(hostname -s)" "$T" "$GATE_OVERRIDE" >> ~/swebench/gate-stamps/overrides.log
  echo "  GATE_OVERRIDE used: $GATE_OVERRIDE (logged to ~/swebench/gate-stamps/overrides.log)"
else
  [ -f "$GATE" ] || echo "  gate not installed: cd ~/swebench-playbook && git pull"
  echo "  run first:  python3 $GATE $T --repo $REPO"
  echo "  (or, while the gate is provisional: GATE_OVERRIDE=\"<reason>\" push-task.sh $T)"
  exit 1
fi

echo; echo "== 1. preflight (must exit 0)"
# Take the Docker mutex. Without it this oracle run races any other container
# work on the host: measured 2026-09-23, a concurrent oracle turned a stable
# 3/3 into 2/3, which reads as a golden defect (R13) and is really contention.
# Re-entrancy: a caller may ALREADY hold the docker mutex. Taking it again here
# deadlocks -- measured 2026-09-24, a push wrapped in flock hung at this line until
# its timeout and silently pushed nothing. Acquire only if we are the outermost.
if [ -n "${SWEBENCH_DOCKER_LOCK_HELD:-}" ]; then PF_LOCK=""; else
  PF_LOCK="flock /tmp/swebench-docker.lock"; export SWEBENCH_DOCKER_LOCK_HELD=1; fi
$PF_LOCK bash ~/.claude/skills/swebench-mt/preflight.sh "$T" --with-oracle || {
  echo "PREFLIGHT FAILED — not pushing."; exit 1; }

echo; echo "== 2. isolate the index"
# A PRIVATE index. The checkout is shared with other live sessions -- on 2026-09-23
# another session committed and pushed one pair's 12 in-progress files mid-build.
# `git reset` alone does not protect against a concurrent writer to .git/index.
# BEFORE isolating: the SHARED index may already hold stale staged content from a
# crashed run. A private index protects OUR commit and leaves that poison in place
# for the next session to sweep into theirs -- measured 2026-09-24, a peer's scoped
# `git add` picked up our pre-fix state and reverted a landed fix.
if [ -n "$(git diff --cached --name-only 2>/dev/null)" ]; then
  echo "  shared index is DIRTY before we start. Clearing it so the next session"
  echo "  does not inherit it. Staged paths were:"
  git diff --cached --name-only | sed 's/^/    /'
  git reset -q
fi
export GIT_INDEX_FILE="$(mktemp -t swebench-index.XXXXXX)"
# ${VAR:-} -- the success path unsets GIT_INDEX_FILE, and under `set -u` a bare
# "$GIT_INDEX_FILE" here made every SUCCESSFUL push exit with
# "GIT_INDEX_FILE: unbound variable". A success that looks like a failure is the
# worst kind of bug in a push tool.
trap 'rm -f "${GIT_INDEX_FILE:-}"' EXIT
git read-tree HEAD
git reset -q
git add -A -- "$T/"

# 251 untracked files / 22 MB of trial evidence were once sitting inside a task
# bundle, and `git add -A -- <task>/` would have committed every one of them.
UNTRACKED=$(git ls-files --others --exclude-standard -- "$T/" | wc -l)
if [ "$UNTRACKED" -gt 25 ]; then
  echo "  REFUSING: $UNTRACKED untracked files under $T/ -- that is evidence or scratch,"
  echo "  not task content. Move it out (R9: evidence lives outside the bundle) and retry."
  git ls-files --others --exclude-standard -- "$T/" | head -5 | sed 's/^/    /'
  git reset -q; exit 1
fi

echo; echo "== 3. VERIFY what is staged — must be $T/ and nothing else"
STAGED=$(git diff --cached --name-only)
OUTSIDE=$(echo "$STAGED" | grep -v "^$T/" || true)
echo "$STAGED" | sed 's/^/     /'
if [ -n "$OUTSIDE" ]; then
  echo; echo "ABORT: files staged OUTSIDE $T/:"; echo "$OUTSIDE" | sed 's/^/     /'
  git reset -q; exit 1
fi
[ -z "$STAGED" ] && { echo "ABORT: nothing staged"; exit 1; }
echo "     ($(echo "$STAGED" | wc -l) files, all inside $T/)"

UNREL=$(git status --porcelain | grep -v "^[AMD]" | wc -l)
echo; echo "== 4. $UNREL unrelated uncommitted files left alone (expected, not an error)"

if [ -n "$DRY" ]; then echo; echo "DRY RUN — resetting index, nothing committed."; git reset -q; exit 0; fi

echo; echo "== 5. commit + push"
git commit -q -m "${COMMIT_MSG:?set COMMIT_MSG to an accurate one-line summary}" || { echo "commit failed"; exit 1; }
# explicit :22 — a global insteadOf rewrite forces HTTPS and 403s
git push ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git HEAD:main || {
  echo "PUSH FAILED — commit is local, retry the push only."; exit 1; }
# Leave the shared index exactly as a clean checkout would: empty. A private index
# protects OUR commit but leaves anything already staged for the NEXT session to
# sweep into theirs. Measured 2026-09-24: that reverted a landed fix.
unset GIT_INDEX_FILE
git reset -q
echo; echo "pushed. verify with:  codimango task errors $T"
echo "shared index left clean: $(git diff --cached --name-only | wc -l) staged"

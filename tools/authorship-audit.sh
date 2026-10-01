#!/usr/bin/env bash
# authorship-audit.sh — did Claude write ANYTHING inside this task directory?
#
#   ./authorship-audit.sh <task-name> [--since YYYY-MM-DD]
#
# --since gates only writes at or after that date. REMEDIATION MODE: a task already
# contaminated has a permanent transcript record, so a bare run blocks it forever and the
# gate becomes useless exactly when you are trying to fix it. Use --since to prove no NEW
# Claude write happened during the repair, and record the historical violation in the
# ledger instead of pretending it is gone.
#
# WHY THIS EXISTS. Two tasks came back CONTAMINATED with `agentModified: true`:
#
#   rustcrypto-x509      steps/1_*/tests/run_script.sh   claude_code  matchScore 0.982
#   dropshot-websocket   steps/1_*/tests/parser.py       claude_code  matchScore 0.061
#
# Read that second score. 0.061 means the file barely resembles what was logged any more --
# and it STILL failed. **The gate fires on the agent WRITE LOG, not on current content.**
# Rewriting, renaming or having Avocado re-author afterwards does not erase the write. The
# only winning move is never to write the file.
#
# instruction.md was CLEAN on both. D2 held. The hole was tests/, where our ownership rule
# says "Codex, never Claude" -- and the team-aai guard that enforces it fires on Edit/Write
# ONLY, so a Bash heredoc walks straight through (feedback_tests_guard_bypass_via_bash).
#
# Claude Code session transcripts record the full text of every tool call, Bash included.
# That is a local audit trail for the exact bypass the guard misses.
#
# BLIND SPOT, stated so a PASS is not misread: this sees only CLAUDE CODE transcripts. Writes
# made by MetaCode/Avocado through mc.sh never appear in one, so this tool can say nothing
# about who authored instruction.md. A PASS here means "no Claude write", never "authorship is
# clean". Measured 2026-09-30: 297 transcripts, 20 writes into a task dir, zero to
# instruction.md -- on a file that was 100% model-written.
#
# SCOPE, 2026-09-29: Claude writes NOTHING inside a task directory. Codex makes every change
# except instruction.md, which is Avocado/human only. The single carve-out is <task>/audit/**,
# which is author-side evidence rather than task content -- reported as ALLOWED but still
# listed, because we do not actually know the server's full scan set and an unlisted
# exception is how the last two got through.

set -uo pipefail
TASK="${1:?usage: authorship-audit.sh <task-name>}"
TASK="$(basename "${TASK%/}")"
SINCE=""
[ "${2:-}" = "--since" ] && SINCE="${3:?--since needs YYYY-MM-DD}"
SESSIONS="$HOME/.claude/projects"

# Scan EVERY project dir, not just -home-agvidit. Measured 2026-09-29: the first version of
# this script scanned one dir, missed BOTH known-contaminated tasks, and reported PASS. There
# are 13 project dirs and the writes that mattered were not in the one I guessed. A detector
# that misses its known positives is worse than no detector -- it manufactures confidence.
[ -d "$SESSIONS" ] || { echo "authorship-audit: no session dir at $SESSIONS" >&2; exit 2; }
# RECURSIVE, and this is load-bearing: 226 of 237 transcripts on this box are SUBAGENT
# transcripts at <project>/<session>/subagents/agent-*.jsonl. A depth-2 glob sees 11 of 237
# and misses exactly the agents that do the writing. Delegated work is where the write happens.
shopt -s nullglob
mapfile -t FILES < <(find "$SESSIONS" -name '*.jsonl' -type f 2>/dev/null)
[ "${#FILES[@]}" -gt 0 ] || { echo "authorship-audit: no transcripts found" >&2; exit 2; }

echo "task:     $TASK${SINCE:+   (only writes on/after $SINCE)}"
echo "scanning: ${#FILES[@]} transcripts (main sessions + subagents) across $(ls -1d "$SESSIONS"/*/ 2>/dev/null | wc -l) project dirs"
echo

python3 - "$TASK" "$SINCE" "${FILES[@]}" <<'PY'
import json, re, sys, os

task  = sys.argv[1]
since = sys.argv[2] or None
paths = sys.argv[3:]

# A write is any of: Write/Edit/NotebookEdit naming a tests/ path, or a Bash command that
# redirects, copies, moves or edits in place into one. Reading is fine and must not fire.
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
# Any write verb aimed at a path containing the task name. Deliberately broad: a false
# positive costs one look, a false negative costs a task. cp INTO the tree is the one that
# actually bit us on concourse and it is not an Edit/Write, which is why the guard missed it.
BASH_WRITE_TEMPLATE = (
    # The write TARGET must itself contain the task name. Matching "a write verb somewhere
    # in a command that mentions the task" over-fires badly: it flagged this very script
    # writing a brief to /tmp that merely quoted the task name. A guard that cries wolf is
    # ignored, which is the same end state as a guard that is too narrow.
    #
    # 2026-09-30 REGRESSION FIX. The narrowing above did not hold, because `[^|;&]*` is a
    # NEGATED CHARACTER CLASS and therefore matches newlines. Every alternative using it could
    # span the whole command text, so `patch\s+[^|;&]*\S*TASKNAME\S*` fired on a Bash heredoc
    # whose FIRST LINE was the prose title "# B1 scaffold patch — <taskname>" while the write
    # target was /tmp/enc-task/b1-brief.md, entirely outside the task tree. A shell write verb
    # and its target live on one line, so pin every gap to a single line with [^|;&\n]*.
    # Without this the audit reports BLOCKED on any run whose briefs mention the task name
    # near the words patch / sed / dd / rsync / git checkout — which is every run.
    r">{1,2}\s*(?:\S*/)?TASKNAME\S*"
    r"|tee\s+(?:-a\s+)?(?:\S*/)?TASKNAME\S*"
    # Between a write verb and its target there are only option flags and other path
    # arguments -- never prose. `[^|;&]*` allowed prose, so "# B1 scaffold patch — <taskname>"
    # in a heredoc body matched the `patch` alternative and the audit reported BLOCKED on a
    # brief written to /tmp. Restrict the gap to flag-or-path tokens.
    r"|sed\s+-i\S*\s+(?:-\S+\s+|'[^']*'\s+|\"[^\"]*\"\s+)*\S*TASKNAME\S*"
    r"|truncate\s+(?:-\S+\s+)*\S*TASKNAME\S*"
    r"|dd\s+(?:\S+=\S+\s+)*of=\S*TASKNAME\S*"
    r"|\bpatch\s+(?:-\S+\s+)*\S*TASKNAME\S*"
    r"|git\s+(?:apply|checkout|restore)\s+(?:-\S+\s+|HEAD\s+|--\s+)*\S*TASKNAME\S*"
    r"|open\(\s*['\"][^'\"]*TASKNAME[^'\"]*['\"]\s*,\s*['\"][wa]"
)

BASH_WRITE = re.compile(BASH_WRITE_TEMPLATE.replace("TASKNAME", re.escape(task)))
# pathlib writes: only when a literal path containing the task name is being written
def copies_into_task(cmd):
    """cp/mv/rsync write only to their LAST path argument. Matching the task name anywhere in
    the command flags copy-OUT as a write: a reviewer sandboxing `cp -a <task>/tests/. /tmp/rr/`
    read as a violation and blocked a clean task three times. A blocking gate that cries wolf
    gets switched off, which is the same end state as no gate."""
    for seg in re.split(r"[|;&]+|\n", cmd):
        toks = seg.split()
        verb = next((t for t in toks if t in ("cp", "mv", "rsync")), None)
        if not verb:
            continue
        args = [t for t in toks[toks.index(verb)+1:] if not t.startswith("-")]
        if args and task in args[-1]:          # destination only
            return True
    return False

PATHLIB_WRITE = re.compile(
    r"Path\(\s*['\"][^'\"]*" + re.escape(task) + r"[^'\"]*['\"]\s*\)[^\n]{0,80}?\.write_",
)

def classify(text):
    """audit/ is author-side evidence, not task content. Everything else is a violation."""
    return "ALLOWED(audit)" if f"{task}/audit/" in text and "/tests/" not in text \
                               and "/solution/" not in text else "VIOLATION"

hits = []
for p in paths:
    parent = os.path.basename(os.path.dirname(p))
    sess = ("sub:" if parent == "subagents" else "") + os.path.basename(p)[:20]
    try:
        with open(p, errors="replace") as fh:
            for ln, line in enumerate(fh, 1):
                if task not in line or "tests/" not in line:
                    continue
                try: rec = json.loads(line)
                except Exception: continue
                if since:
                    ts = str(rec.get("timestamp") or "")[:10]
                    if ts and ts < since:
                        continue
                for blk in (rec.get("message") or {}).get("content") or []:
                    if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                        continue
                    name = blk.get("name"); inp = blk.get("input") or {}
                    if name in WRITE_TOOLS:
                        fp = str(inp.get("file_path", ""))
                        if task in fp:
                            hits.append((sess, ln, name, fp, classify(fp)))
                    elif name == "Bash":
                        cmd = str(inp.get("command", ""))
                        # Self-reference: running this audit, or preflight which wraps it, puts
                        # the task name and the words it greps for into the transcript. Without
                        # this, every diagnostic run manufactures the finding it is looking for
                        # and the count grows on each invocation. Measured 2026-09-30: 1 -> 4
                        # hits across three consecutive audit runs, all of them the audit itself.
                        # Narrow: skip only a BARE invocation of the auditor itself, not any
                        # command that happens to mention it. The wide form let a real write
                        # hide behind a comment naming the tool.
                        if re.match(r"^\s*\S*(authorship-audit|preflight)\.sh\b[^|;&]*$", cmd):
                            continue
                        if task in cmd and (BASH_WRITE.search(cmd) or PATHLIB_WRITE.search(cmd) or copies_into_task(cmd)):
                            one = " ".join(cmd.split())[:150]
                            hits.append((sess, ln, "Bash", one, classify(cmd)))
    except Exception as e:
        print(f"  (skipped {sess}: {e})", file=sys.stderr)

violations = [h for h in hits if h[4] == "VIOLATION"]
allowed    = [h for h in hits if h[4] != "VIOLATION"]

if allowed:
    print(f"note: {len(allowed)} write(s) to <task>/audit/ — permitted carve-out, not counted\n")

if not violations:
    print("PASS — no Claude write inside the task directory (outside audit/).")
    print()
    print("This is an EARLY WARNING, not a clearance. The server's agent write log is")
    print("authoritative and covers sessions this scan cannot see. A clean result here")
    print("means 'no evidence locally', never 'provenance will pass'.")
    sys.exit(0)

print(f"BLOCKED — {len(violations)} Claude write(s) inside this task directory:\n")
for sess, ln, how, what, _ in violations:
    print(f"  [{sess} :{ln}] {how}")
    print(f"      {what}")
print()
print("The write is already logged server-side. Rewriting the file does NOT clear it --")
print("dropshot failed at matchScore 0.061, meaning the content had almost entirely")
print("changed and the record still stood. Treat this task as provenance-blocked and")
print("route the file to a permitted author for a clean re-creation.")
sys.exit(1)
PY

#!/usr/bin/env bash
# frozen-sessions.sh — flag Claude Code sessions on THIS host that look frozen.
#
#   tools/frozen-sessions.sh [--minutes N] [--quiet]
#
# Exit 0 = nothing frozen, 1 = at least one suspected frozen session.
#
# Why this exists: session agvidit-06 (c49cbf17) sat in "busy" for ~35 hours
# (2026-10-05 09:36 -> 10-06) after reading a probe result. Its main loop had
# stopped, its tool children were zombies that were never reaped, and nobody
# noticed until Vidit saw the terminal spinner hadn't moved.
#
# Signature checked, all of which must hold to report FROZEN:
#   - the registry (~/.claude/sessions/<pid>.json) says status=busy
#   - the process is still alive
#   - BOTH the registry's updatedAt AND the session transcript's mtime are older
#     than the threshold (a busy session that is genuinely working keeps
#     appending to its transcript; a long backgrounded tool returns immediately)
# Zombie children are reported as supporting evidence, not required.
set -uo pipefail
MIN=60; QUIET=0
while [ $# -gt 0 ]; do
  case "$1" in
    --minutes) MIN="$2"; shift 2;;
    --quiet) QUIET=1; shift;;
    *) echo "usage: $0 [--minutes N] [--quiet]" >&2; exit 2;;
  esac
done

python3 - "$MIN" "$QUIET" <<'PY'
import glob, json, os, sys, time
mins, quiet = int(sys.argv[1]), sys.argv[2] == "1"
now = time.time()
home = os.path.expanduser("~")
frozen, checked = [], 0
for f in sorted(glob.glob(f"{home}/.claude/sessions/*.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    pid, sid, name = d.get("pid"), d.get("sessionId", ""), d.get("name", "?")
    if not pid or not os.path.exists(f"/proc/{pid}"):
        continue                       # dead process: not frozen, just stale registry
    checked += 1
    if d.get("status") != "busy":
        continue
    reg_age = (now - d.get("updatedAt", 0) / 1000) / 60
    proj = (d.get("cwd") or home).replace("/", "-")
    tr = f"{home}/.claude/projects/{proj}/{sid}.jsonl"
    # Activity = the newest write among the session transcript AND its subagents'
    # transcripts. A coordinator waiting on a long-running subagent stays "busy" while
    # its own transcript goes quiet; on 2026-10-09 this session was falsely flagged
    # that way (own transcript idle 1.5h, subagent writing the whole time).
    cands = [tr] + glob.glob(f"{home}/.claude/projects/{proj}/{sid}/subagents/*.jsonl")
    mts = [os.path.getmtime(x) for x in cands if os.path.exists(x)]
    tr_age = (now - max(mts)) / 60 if mts else float("inf")
    if reg_age < mins or tr_age < mins:
        continue
    zombies = 0
    try:
        for c in open(f"/proc/{pid}/task/{pid}/children").read().split():
            st = open(f"/proc/{c}/stat").read().rsplit(")", 1)[1].split()[0]
            zombies += st == "Z"
    except Exception:
        pass
    frozen.append((name, pid, sid, reg_age, tr_age, zombies))

stamp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
if frozen:
    print(f"[{stamp}] FROZEN sessions (busy, no activity > {mins} min):")
    for name, pid, sid, ra, ta, z in frozen:
        print(f"  {name:22} pid={pid:<8} session={sid[:8]}  registry idle {ra/60:.1f}h, "
              f"transcript idle {ta/60:.1f}h, zombie children={z}")
    print("  -> close the session (its work is in the transcript); hand over any open claims in "
          "~/swebench-playbook/ledger/CLAIMS.md")
    sys.exit(1)
if not quiet:
    print(f"[{stamp}] ok: {checked} live sessions checked, none frozen (threshold {mins} min)")
sys.exit(0)
PY

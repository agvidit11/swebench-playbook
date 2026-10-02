#!/usr/bin/env bash
# watch.sh — the 2-hour lane watcher. Read-only. Prints the state of every lane on THIS machine.
#
#   ./watch.sh            # full report
#
# Run it from the Watch lane (00-LANES.md, Lane W) under /loop 2h. It never fixes anything —
# it reports, appends infra failures to ledger/ISSUES.md, and leaves decisions to the lane owner.

set -uo pipefail
PB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${SWEBENCH_REPO:-$HOME/swe-bench-pro-agvidit}"
HOST="$(hostname -s)"
NOW="$(date '+%Y-%m-%d %H:%M')"
STALE_MIN="${STALE_MIN:-120}"

echo "════ LANE WATCH  $HOST  $NOW ════"

echo; echo "── running workers on this machine ──"
ps -eo pid,etime,args 2>/dev/null | grep -E "codex exec|muse exec|bench run" | grep -v grep \
  | awk '{pid=$1; et=$2; $1=$2=""; printf "  %-8s %-12s %s\n", pid, et, substr($0,1,110)}' || true
[ -z "$(pgrep -f 'codex exec|muse exec|bench run' 2>/dev/null)" ] && echo "  (none)"

echo; echo "── local bench jobs, last 6h: per-trial rewards ──"
find "$REPO/jobs" -maxdepth 1 -mindepth 1 -type d -mmin -360 2>/dev/null | sort | while read -r j; do
  task=$(python3 -c "import json,sys;c=json.load(open(sys.argv[1]));t=c.get('tasks') or [{}];print((t[0].get('path') or '').rsplit('/',1)[-1])" "$j/config.json" 2>/dev/null)
  agent=$(python3 -c "import json,sys;c=json.load(open(sys.argv[1]));a=c.get('agents') or [{}];print(a[0].get('name',''))" "$j/config.json" 2>/dev/null)
  rw=$(find "$j" -name reward.txt -exec cat {} \; 2>/dev/null | tr -d '\n')
  exc=$(grep -rhoE '"exception_type": *"[A-Za-z]+"' "$j" 2>/dev/null | sort | uniq -c | tr -s ' ' | tr '\n' ' ')
  printf "  %-34s %-9s rewards=%-14s %s\n" "${task:0:34}" "$agent" "${rw:-none}" "${exc}"
done

echo; echo "── task dirs with no write in ${STALE_MIN}m but a lane claim (possibly stuck) ──"
if [ -f "$PB/ledger/CLAIMS.md" ]; then
  grep -E "^\| .*\| ACTIVE" "$PB/ledger/CLAIMS.md" 2>/dev/null | awk -F'|' '{gsub(/ /,"",$3); print $3}' | while read -r t; do
    [ -d "$REPO/$t" ] || continue
    recent=$(find "$REPO/$t" -type f -mmin -"$STALE_MIN" 2>/dev/null | head -1)
    [ -z "$recent" ] && echo "  STALE  $t"
  done
fi

echo; echo "── server state of claimed tasks ──"
if [ -f "$PB/ledger/CLAIMS.md" ]; then
  grep -E "^\| .*\| (ACTIVE|READY|PUSHED)" "$PB/ledger/CLAIMS.md" | awk -F'|' '{gsub(/ /,"",$3); print $3}' | sort -u | while read -r t; do
    timeout 60 codimango task show "$t" --json 2>/dev/null | sed -n '/^[[:space:]]*[{[]/,$p' \
      | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: print('  %-44s (not on server)' % '$t'[:44]); raise SystemExit
bad=[v['label'] for v in d.get('validationDetails') or [] if v.get('status')=='failed']
print('  %-44s review=%-14s val=%-8s %s' % (d.get('name','')[:44], d.get('reviewStatus'), d.get('validationStatus'), ('FAIL: '+', '.join(bad)) if bad else ''))"
  done
fi

echo; echo "── infra signatures in the last 2h of local jobs (append to ledger/ISSUES.md if new) ──"
find "$REPO/jobs" -mmin -120 \( -name '*.txt' -o -name '*.json' -o -name '*.log' \) 2>/dev/null \
  | xargs grep -hoE "AgentInstallError|FailedToOpenSocket|MetaModelCatalogError|AgentTimeoutError|flagged for possible cybersecurity|\[\[: not found" 2>/dev/null \
  | sort | uniq -c | sed 's/^/  /' || true

echo; echo "── open issues (last 10) ──"; tail -10 "$PB/ledger/ISSUES.md" 2>/dev/null | sed 's/^/  /'

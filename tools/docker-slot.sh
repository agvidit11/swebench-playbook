#!/usr/bin/env bash
# docker-slot.sh <cmd...> — run a Docker-spawning command in one of N host-wide slots.
# 00-ROUTER.md §6. Slot 0 is the legacy /tmp/swebench-docker.lock, so tools that still take
# that lock directly occupy slot 0 and stay mutually exclusive with this helper.
# The ceiling is Docker's bridge-network pool (~15 networks; one k=5 job creates 5), not RAM.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: docker-slot.sh <cmd...>" >&2; exit 2; }

SLOTS=${DOCKER_SLOTS:-2}
WAIT=${DOCKER_SLOT_WAIT:-0}            # seconds; 0 = wait forever
MIN_DISK_GB=${DOCKER_SLOT_MIN_DISK_GB:-60}
MIN_MEM_GB=${DOCKER_SLOT_MIN_MEM_GB:-48}

lockfile() { [ "$1" -eq 0 ] && echo /tmp/swebench-docker.lock || echo "/tmp/swebench-docker.lock.$1"; }

capacity_ok() {
  local disk mem
  disk=$(df -BG --output=avail / | tail -1 | tr -dc 0-9)
  mem=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo)
  [ "$disk" -ge "$MIN_DISK_GB" ] && [ "$mem" -ge "$MIN_MEM_GB" ]
}

start=$(date +%s)
while :; do
  if capacity_ok; then
    for ((i = 0; i < SLOTS; i++)); do
      f=$(lockfile "$i")
      exec {fd}>>"$f"
      if flock -n "$fd"; then
        echo "$$ $*" > "/tmp/swebench-docker.holder.$i"
        trap ': > /tmp/swebench-docker.holder.'"$i" EXIT
        "$@"
        exit $?
      fi
      exec {fd}>&-
    done
  fi
  if [ "$WAIT" -gt 0 ] && [ $(( $(date +%s) - start )) -ge "$WAIT" ]; then
    echo "docker-slot: no free slot (or capacity guard) after ${WAIT}s; holders:" >&2
    cat /tmp/swebench-docker.holder.* 2>/dev/null >&2 || true
    exit 75
  fi
  sleep 10
done

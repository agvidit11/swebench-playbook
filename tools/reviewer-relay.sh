#!/usr/bin/env bash
# reviewer-relay.sh <pair-name> — keep a Codex reviewer alive across its own timeout.
#
# A single `codex exec` dies at its timeout and takes its context with it. This
# supervisor runs a CHAIN of reviewers: each one is given a hard deadline 5 minutes
# short of its own wall, told to write RELAY-STATE.md before that deadline, and the
# next link in the chain starts by reading it. Nothing is lost at a handover.
#
# Stops when the engineer writes DONE at the run root (then runs one final link to
# produce PERFORMANCE-REVIEW.md), or after MAX_LINKS.

set -uo pipefail

PAIR="${1:?usage: reviewer-relay.sh <pair-name>}"
ROOT="$HOME/swebench-playbook/.e2e/$PAIR"
BRIEF="/tmp/pipeline-compare/REV-${PAIR#pair-}.md"
RELAY="$ROOT/review/RELAY-STATE.md"
LOG="/tmp/pipeline-compare/relay-$PAIR.log"

BUDGET=3400          # codex wall per link
MARGIN=300           # write RELAY-STATE this many seconds before the wall
MAX_LINKS=10

mkdir -p "$ROOT/review"
: > "$LOG"

for ((link = 1; link <= MAX_LINKS; link++)); do
  FINAL=no
  [[ -f "$ROOT/DONE" ]] && FINAL=yes

  DEADLINE=$(date -u -d "+$((BUDGET - MARGIN)) seconds" +%Y-%m-%dT%H:%M:%SZ)
  PROMPT="/tmp/pipeline-compare/relay-$PAIR-link$link.md"

  {
    cat "$BRIEF"
    echo
    echo "## RELAY PROTOCOL — you are link $link of a reviewer chain. READ THIS."
    echo
    echo "You run under a hard wall. **Your relay deadline is \`$DEADLINE\` (UTC).**"
    echo "Check \`date -u\` at every poll. The moment you pass that deadline, STOP reviewing"
    echo "and immediately write \`$RELAY\`, then exit. Do not start new analysis after it."
    echo
    echo "\`RELAY-STATE.md\` is the ONLY thing that survives you. Write it so your successor"
    echo "loses nothing. It must contain, in full and in specifics, not summary:"
    echo
    echo "- **Handoffs reviewed so far** — filename, verdict, and the one-line reason."
    echo "- **Handoffs present but NOT yet reviewed** — so the successor starts there."
    echo "- **Running findings** — every defect found so far, with file:line. Verbatim, not condensed."
    echo "- **Claims you took on trust** and still intend to verify."
    echo "- **Your current read on the engineer's trajectory** — is this task going to be any good?"
    echo "- **Your current answer to the autonomy question**, and what would change it."
    echo "- **Anything you would tell yourself if you could only send one paragraph.**"
    echo
    echo "If \`$RELAY\` already exists, it is from your predecessor: **read it first**, adopt its"
    echo "findings as your own starting state, and continue the numbering. Then overwrite it"
    echo "when your own deadline arrives. Never re-review a handoff your predecessor covered"
    echo "unless you have a specific reason to doubt its verdict — say so if you do."
    if [[ "$FINAL" == yes ]]; then
      echo
      echo "## THIS IS THE FINAL LINK"
      echo
      echo "The engineer has finished (\`DONE\` exists). Do not poll. Review every handoff not"
      echo "yet covered, then write \`$ROOT/PERFORMANCE-REVIEW.md\` as specified in the brief."
      echo "That file is the deliverable this whole chain exists to produce."
    fi
  } > "$PROMPT"

  echo "=== link $link  final=$FINAL  deadline=$DEADLINE  $(date -u +%H:%M:%SZ)" >> "$LOG"

  START=$(date +%s)
  timeout $BUDGET codex --ask-for-approval never --sandbox workspace-write \
    exec --skip-git-repo-check --model gpt-5.6-sol \
    --config model_reasoning_effort="xhigh" \
    --output-last-message "/tmp/pipeline-compare/relay-$PAIR-link$link-out.txt" \
    "$(cat "$PROMPT")" >> "$LOG" 2>&1

  RC=$?
  ELAPSED=$(( $(date +%s) - START ))
  echo "=== link $link exited rc=$RC after ${ELAPSED}s at $(date -u +%H:%M:%SZ)" >> "$LOG"

  # A link that dies in seconds is a launch fault, not a completed review cycle.
  # Burning the whole chain on a bad argument is how 10 links vanished in 2 minutes.
  if [[ $ELAPSED -lt 60 && $RC -ne 0 ]]; then
    echo "=== ABORT: link died in ${ELAPSED}s rc=$RC — launch fault, not a cycle." >> "$LOG"
    echo "=== last codex output follows; fix and relaunch." >> "$LOG"
    exit 3
  fi

  if [[ "$FINAL" == yes ]]; then
    echo "=== chain complete for $PAIR" >> "$LOG"
    break
  fi
  sleep 10
done

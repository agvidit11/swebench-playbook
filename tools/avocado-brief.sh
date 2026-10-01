#!/usr/bin/env bash
# avocado-brief.sh — assemble an Avocado prompt from a template, and refuse to send prose.
#
#   ./avocado-brief.sh <initial|gapfill|retry|clarity> <task-or-step-dir> <requirements-file> [out]
#
# Requirements files hold OBLIGATIONS — what the reader must come away knowing. They must not
# hold sentences for Avocado to reword. Writing the sentence and asking 1P to rephrase it is
# laundered authorship, and it is what flipped django's provenance from pass to fail. This
# script lints for that and exits 1 rather than sending it.
#
# The word cap is computed, never chosen:
#   initial  clamp(45 * obligations, 250, 600)
#   gapfill  current words + 40 * obligations
#   retry    the SAME cap as the attempt it replaces — caps never ratchet upward on retry,
#            which is how an instruction grows until every model passes it
#
# Output is a prompt file. Send it with mc.sh; only Avocado writes the instruction.

set -uo pipefail
MODE="${1:?usage: avocado-brief.sh <initial|gapfill|retry|clarity> <dir> <requirements-file> [out]}"
DIR="${2:?need the task or step dir}"; DIR="${DIR%/}"
REQ="${3:?need a requirements file}"
OUT="${4:-$DIR/audit/avocado-prompt-$MODE-$(date +%H%M%S).txt}"
ASSETS="$(cd "$(dirname "${BASH_SOURCE[0]}")/../assets/avocado" && pwd)"

[ -d "$DIR" ] || { echo "avocado-brief: no such dir: $DIR" >&2; exit 2; }
[ -s "$REQ" ] || { echo "avocado-brief: requirements file empty or missing: $REQ" >&2; exit 2; }
case "$MODE" in initial|gapfill|retry|clarity) ;; *) echo "avocado-brief: bad mode: $MODE" >&2; exit 2;; esac
TPL="$ASSETS/$MODE.txt"; [ "$MODE" = clarity ] && TPL="$ASSETS/clarity-restart.txt"
[ -f "$TPL" ] || { echo "avocado-brief: missing template $TPL" >&2; exit 2; }

# ── the lint. This is the reason the script exists. ────────────────────────────
python3 - "$REQ" <<'PY' || exit 1
import re, sys
txt = open(sys.argv[1]).read()
fail = []

# 1. Explicit hand-off of wording.
for pat, why in [
    (r"\bwrite:\s*\S",              "'write:' followed by text — that is you drafting"),
    (r"\bword(ing|ed) (it|as|like)", "prescribing wording"),
    (r"\bphrase (it|this|as)\b",    "prescribing phrasing"),
    (r"\bsomething like\b",         "'something like' — a draft with deniability"),
    (r"\buse this (sentence|text|line)\b", "supplying the sentence"),
    (r"\bverbatim\b",               "asking for verbatim text"),
    (r"\bsay:\s*\S",                "'say:' followed by text"),
]:
    m = re.search(pat, txt, re.I)
    if m: fail.append(f"{why}  ->  {m.group(0)[:60]!r}")

# 2. A first-person quoted sentence. Our instructions are first-person; a REQUIREMENT is not.
#    A long first-person quote in a requirements file is a drafted instruction sentence.
for q in re.findall(r"[\"“']([^\"”']{40,})[\"”']", txt):
    if len(q.split()) >= 10 and re.search(r"\b(I|I'm|I've|my|me)\b", q):
        fail.append(f"first-person drafted sentence in quotes ({len(q.split())} words)  ->  {q[:70]!r}")

# 3. Bare first-person prose outside quotes, in a file that should be third-person obligations.
fp = [l.strip() for l in txt.splitlines()
      if re.match(r"^\s*[-*]?\s*(I|I'm|I've|My)\b", l) and len(l.split()) >= 8]
for l in fp[:3]:
    fail.append(f"first-person requirement line — write the obligation, not the sentence  ->  {l[:70]!r}")

if fail:
    print("avocado-brief: BLOCKED — the requirements file contains drafted prose:\n")
    for f in fail: print("  *", f)
    print("\nA requirement says what the reader must come away KNOWING. It does not supply the")
    print("words. Handing Avocado a sentence to reword is laundered authorship and it has")
    print("already cost us one provenance failure. Rewrite as obligations and rerun.")
    sys.exit(1)
PY

# ── word cap ───────────────────────────────────────────────────────────────────
# Count only ADDITIVE obligations toward the cap. A "must not" line asks for a removal and
# should not buy words -- counting it inflates the budget in the wrong direction.
N=$(grep -cE '^\s*[-*0-9]' "$REQ"); [ "$N" -lt 1 ] && N=1
NEG=$(grep -cEi '^\s*[-*0-9].*(must not|never|remove|drop|stop) ' "$REQ" || true)
ADD=$((N - NEG)); [ "$ADD" -lt 1 ] && ADD=1
TARGET="$DIR/instruction.md"
CUR=0; [ -f "$TARGET" ] && CUR=$(wc -w < "$TARGET")
case "$MODE" in
  initial|clarity) CAP=$((45*N)); [ "$CAP" -lt 250 ] && CAP=250; [ "$CAP" -gt 600 ] && CAP=600
                   # AVOCADO_CAP overrides. The formula scales words with obligation COUNT,
                   # which is wrong when you deliberately give few, high-level obligations and
                   # want the model to derive detail from the repo -- the provenance-safest
                   # brief is the shortest one, and it should not also buy the shortest cap.
                   [ -n "${AVOCADO_CAP:-}" ] && CAP=$AVOCADO_CAP ;;
  gapfill)         CAP=$((CUR + 40*ADD))
                   # Absolute ceiling. The reference portfolio's median shipped instruction is
                   # 393 words and our accepted ones are 154-230; a brief that invites 900+ is
                   # asking for the over-specification failure, not preventing it.
                   [ "$CAP" -gt 700 ] && CAP=700 ;;
  retry)           CAP=${AVOCADO_CAP:-$CUR}
                   [ "$CAP" -lt 1 ] && { echo "avocado-brief: retry needs AVOCADO_CAP=<the cap of the attempt being replaced>" >&2; exit 2; } ;;
esac

# ── assemble ───────────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUT")"
python3 - "$TPL" "$ASSETS/_INVARIANTS.txt" "$REQ" "$TARGET" "$CAP" "${GENRE:-bug-report}" "$OUT" <<'PY'
import sys
tpl, inv, req, target, cap, genre, out = sys.argv[1:8]
body = open(tpl).read()
body = body.replace("{INVARIANTS}", open(inv).read().replace("{WORDCAP}", cap).strip())
body = body.replace("{REQUIREMENTS}", open(req).read().strip())
body = body.replace("{TARGET}", target).replace("{WORDCAP}", cap).replace("{GENRE}", genre)
if "{PREVIOUS}" in body or "{DEFECTS}" in body:
    import os
    prev = open(target).read() if os.path.exists(target) else "(no previous attempt on disk)"
    body = body.replace("{PREVIOUS}", prev)
    body = body.replace("{DEFECTS}", os.environ.get("AVOCADO_DEFECTS", "(paste the verbatim validation output here before sending)"))
open(out, "w").write(body)
PY

echo "mode:        $MODE"
echo "target:      $TARGET"
echo "obligations: $N  (additive $ADD, removals $NEG)"
echo "word cap:    $CAP$([ "$MODE" = retry ] && echo '  (unchanged — caps do not ratchet on retry)')"
echo "genre:       ${GENRE:-bug-report}"
echo "prompt:      $OUT  ($(wc -w < "$OUT") words)"
echo
echo "send with:   ~/.claude/skills/swebench-mt/mc.sh $OUT $DIR"

#!/usr/bin/env python3
"""probe-lint.py <card.md> <probeA.txt> <probeB.txt> [--outputs DIR]

Validate a fork probe BEFORE its verdict is allowed to kill a candidate.

WHY THIS EXISTS — measured 2026-09-22, two of four kills were invalid:

  * frostdb C1: the card required "both uploads start before serialization
    completes". The probe prompts OMITTED that condition and the assertion never
    observed it. All five implementations fully buffered — which are the card's own
    WRONG-PATH shapes. Under A3's own mapping, >=4/5 on the non-desired path is
    evidence of a STRONG fork. It was scored "10/10 desired" and killed.
  * santuario C3: the probe prompt omitted the fail-fast step-2 constraint, so the
    "5/5 desired path" claim could not be derived from the outputs at all.

Both failures share one root cause: nothing checked that the probe actually asked
about the thing the card cared about. This does.

The card must declare, verbatim, three fields:

    CONSTRAINT: <the requirement, worded as instruction.md would word it>
    DESIRED:    <the target design — what you believe is hard to reach>
    NON-DESIRED:<the plausible shapes you expect instead, one per line or ';'>

Exit 1 blocks the probe from counting.
"""
import os, re, sys, glob

FIELDS = ("CONSTRAINT", "DESIRED", "NON-DESIRED")
STOPWORDS = set("""the a an and or of to in on for with that this it is are be as by from at
must should will can may not no if then when what which any all each per its their there
step steps task code implementation implement return returns value values case cases""".split())


def field(text, name):
    m = re.search(rf"^\s*{re.escape(name)}\s*:\s*(.+?)(?=^\s*[A-Z][A-Z -]{{2,}}\s*:|\Z)",
                  text, re.M | re.S)
    return " ".join(m.group(1).split()) if m else None


def content_tokens(s):
    toks = {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", s)}
    return {t for t in toks if t not in STOPWORDS}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    outdir = None
    if "--outputs" in sys.argv:
        outdir = sys.argv[sys.argv.index("--outputs") + 1]
    if len(args) < 3:
        print(__doc__)
        return 2
    card_p, probes = args[0], args[1:]
    card = open(card_p).read()
    fails, warns = [], []

    # ---- 1. the card must declare the three fields, before any probe runs ----
    vals = {}
    for f in FIELDS:
        v = field(card, f)
        if not v:
            fails.append(f"card does not declare {f}: — direction must be fixed BEFORE probing, "
                         f"never read off the outputs afterwards")
        vals[f] = v
    if fails:
        for f in fails:
            print(f"  \033[31mFAIL\033[0m  {f}")
        return 1

    constraint_toks = content_tokens(vals["CONSTRAINT"])
    desired_toks = content_tokens(vals["DESIRED"])

    # ---- 2. each probe prompt must actually state the constraint ----
    for p in probes:
        if not os.path.exists(p):
            fails.append(f"probe prompt missing: {p}")
            continue
        body = open(p).read()
        btoks = content_tokens(body)
        missing = sorted(constraint_toks - btoks)
        covered = 1 - (len(missing) / max(len(constraint_toks), 1))
        if covered < 0.6:
            fails.append(f"{os.path.basename(p)}: states only {covered:.0%} of the CONSTRAINT's "
                         f"content words. Missing: {missing[:10]}\n"
                         f"        A probe that does not state the constraint measures nothing. "
                         f"This is the frostdb/santuario failure exactly.")
        elif missing:
            warns.append(f"{os.path.basename(p)}: {covered:.0%} constraint coverage, missing "
                         f"{missing[:8]}")

        # ---- 3. and must NOT hand over the desired design (leading the witness) ----
        leaked = sorted((desired_toks - constraint_toks) & btoks)
        if len(leaked) >= 3:
            fails.append(f"{os.path.basename(p)}: names {len(leaked)} DESIRED-design words the "
                         f"constraint does not: {leaked[:8]}\n"
                         f"        You are leading the witness; a 5/5 here proves nothing.")

    # ---- 4. two materially different phrasings ----
    if len(probes) < 2:
        fails.append("only one phrasing supplied — one cannot separate 'the model prefers this' "
                     "from 'I led the witness'. Two are required.")
    else:
        a, b = (content_tokens(open(x).read()) for x in probes[:2] if os.path.exists(x))
        jac = len(a & b) / max(len(a | b), 1)
        if jac > 0.85:
            fails.append(f"the two phrasings are {jac:.0%} identical — that is one phrasing typed "
                         f"twice, not a second instrument.")

    # ---- 5. if outputs exist, force the direction to be applied explicitly ----
    if outdir:
        outs = sorted(glob.glob(os.path.join(outdir, "*")))
        if not outs:
            warns.append(f"--outputs {outdir} is empty; verdict cannot be derived")
        else:
            print(f"  NOTE  {len(outs)} probe outputs found. The verdict is:")
            print(f"        n producing DESIRED  >= 4 of 5  -> candidate is DEAD (fork ~1)")
            print(f"        n producing NON-DESIRED >= 4 of 5 -> **STRONG FORK**, candidate LIVES")
            print( "        Classify each output against the card's own DESIRED/NON-DESIRED text,")
            print( "        quote the line that decided it, and state the direction you applied.")
            print( "        Reversing this mapping killed a live candidate on 2026-09-22.")

    for f in fails:
        print(f"  \033[31mFAIL\033[0m  {f}")
    for w in warns:
        print(f"  \033[33mWARN\033[0m  {w}")
    if not fails:
        print("  \033[32mPASS\033[0m  probe states the constraint, does not leak the design, "
              "two distinct phrasings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

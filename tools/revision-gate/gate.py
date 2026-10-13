#!/usr/bin/env python3
"""revision-gate: one command to run before ANY push of a SWE-bench task (first push or revision).

  PROVISIONAL (2026-10-13): built by agvidit-ee and not yet verified by 3 independent agents.
  Treat a FAIL as "look at this", not as proof. See ledger/VERIFY-revision-gate.md.

Stages (cheapest first; each prints PASS / FAIL / WARN / SKIP / BLOCKED):
  1 preflight     swebench-mt preflight.sh --with-oracle      structure, server-only checks, oracle 3/3
  2 presubmit     review/presubmit-2026-10-08/presubmit.py    mechanical reviewer findings (README, metadata, config)
  3 provenance    ~/swebench/prov_predict.py                  logged Claude writes that still survive
  4 carry         carry_forward.py                            later steps re-run earlier steps' graded tests
  5 forge         forge_probe.py                              grader cannot be made to pay without a solution
  6 review        codimango bench ai-review review-task-swebench-v2   the reviewer's own agent
  7 calibrate     codimango bench run --k2n, twice            every step 1-3/5 on both runs

Usage:
  gate.py <task> [--repo DIR] [--fast] [--only s1,s2] [--skip s1,s2] [--k2n-agent metacode]
    --fast   stages 1-5 only (minutes). A push stamp is only issued for a full run.
Exit: 0 all clear, 1 a FAIL, 2 usage/infra, 4 BLOCKED (e.g. another bench owns the host).
Writes nothing inside the task directory. Logs: /tmp/revision-gate/<task>-<utc>/. Stamp:
~/swebench/gate-stamps/<task>.json, keyed by a hash of the task's files (push-task.sh checks it).
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYBOOK = os.environ.get("SWEBENCH_PLAYBOOK", os.path.expanduser("~/swebench-playbook"))  # for presubmit.py
SKILL = os.path.expanduser("~/.claude/skills/swebench-mt")
STAMPS = os.path.expanduser("~/swebench/gate-stamps")
ORDER = ["preflight", "presubmit", "provenance", "carry", "forge", "review", "calibrate"]
FAST = ORDER[:5]


def task_hash(task_dir, at=None):
    """Hash exactly what git would push for this task: tracked + untracked-not-ignored files (or the
    files in commit `at`), excluding audit/, including each file's git mode (exec bit, symlink).
    The same content hashes the same on disk and in a commit."""
    repo, task = os.path.dirname(task_dir), os.path.basename(task_dir)
    g = lambda *c: subprocess.run(["git", "-C", repo, *c], capture_output=True).stdout
    entries = {}  # path -> (mode, content-bytes)
    if at:
        for line in g("ls-tree", "-r", at, "--", task + "/").decode().split("\n"):
            if not line:
                continue
            meta, path = line.split("\t", 1)
            mode, _, sha = meta.split()
            entries[path] = (mode, g("cat-file", "blob", sha))
    else:
        for path in g("ls-files", "-co", "--exclude-standard", "--", task + "/").decode().split("\n"):
            full = os.path.join(repo, path)
            if not path or not os.path.lexists(full):
                continue
            if os.path.islink(full):
                entries[path] = ("120000", os.readlink(full).encode())
            elif os.path.isfile(full):
                mode = "100755" if os.stat(full).st_mode & 0o111 else "100644"
                entries[path] = (mode, open(full, "rb").read())
    h = hashlib.sha256()
    for path in sorted(entries):
        rel = path[len(task) + 1:]
        if rel.split("/", 1)[0] == "audit":
            continue
        mode, data = entries[path]
        h.update(rel.encode() + b"\0" + mode.encode() + b"\0")
        h.update(hashlib.sha256(data).digest())
    return h.hexdigest()


def run(cmd, log, cwd=None, timeout=None):
    with open(log, "w") as f:
        f.write("$ " + " ".join(cmd) + "\n")
        f.flush()
        try:
            p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=cwd, timeout=timeout, text=True)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            f.write("\nTIMEOUT\n")
            rc = 124
    return rc, open(log).read()


def tail(text, n=6):
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("$ ")]
    return "\n".join("      " + l[:200] for l in lines[-n:])


def bench_busy():
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if "codimango-bench" in l and " bench run" in l]


def k2n_split(manifest):
    m = json.load(open(manifest))
    per = {}
    for c in m.get("cells", []):
        cur = next((a for a in c.get("attempts", []) if a.get("attempt_id") == c.get("current_attempt_id")), None)
        v = (cur or {}).get("outcome", {}).get("verdict")
        s = per.setdefault(c["step_index"] + 1, {"pass": 0, "fail": 0, "error": 0})
        s[v if v in s else "error"] += 1
    return per


# ---------------------------------------------------------------- stages
def st_preflight(ctx):
    rc, out = run([os.path.join(SKILL, "preflight.sh"), ctx["task"], "--with-oracle"], ctx["log"]("preflight"),
                  cwd=ctx["repo"], timeout=5400)
    return ("PASS" if rc == 0 else "FAIL"), ("preflight exit 0, oracle 3/3" if rc == 0 else tail(out))


def st_presubmit(ctx):
    rc, out = run([sys.executable, os.path.join(PLAYBOOK, "review/presubmit-2026-10-08/presubmit.py"), ctx["task"],
                   "--repo", ctx["repo"], "--local-only", "--worktree", "--color", "never"],
                  ctx["log"]("presubmit"), cwd=ctx["repo"], timeout=900)
    fails = [l for l in out.splitlines() if re.match(r"\s*FAIL", l)]
    if rc == 2:
        return "BLOCKED", tail(out)
    warns = [l for l in out.splitlines() if re.match(r"\s*WARN", l)]
    if rc == 0:
        return "PASS", f"0 FAIL, {len(warns)} WARN" + ("".join("\n      " + l.strip()[:200] for l in warns[:5]))
    return "FAIL", "\n".join("      " + l.strip()[:200] for l in fails[:8])


def st_provenance(ctx):
    tool = os.path.expanduser("~/swebench/prov_predict.py")
    if not os.path.exists(tool):
        return "BLOCKED", "~/swebench/prov_predict.py missing: run ~/swebench-playbook/tools/bootstrap-swebench-home.sh"
    rc, out = run([sys.executable, tool, ctx["task"]], ctx["log"]("provenance"), cwd=ctx["repo"], timeout=600)
    if "PREDICTED CONTAMINATED" in out:
        return "FAIL", tail(out, 8)
    if rc != 0:
        return "BLOCKED", tail(out)
    home = os.path.realpath(os.path.expanduser("~/swe-bench-pro-agvidit"))
    if os.path.realpath(ctx["repo"]) != home:
        return "WARN", f"prov_predict.py always reads {home}, not {ctx['repo']}; re-run there if the files differ"
    return "PASS", ("no surviving flagged blocks" if "PREDICTED CLEAR" in out else "no provenance evidence on the server for this task")


def st_carry(ctx):
    log = ctx["log"]("carry")
    rc, out = run([sys.executable, os.path.join(HERE, "carry_forward.py"), ctx["dir"], "--json"], log, timeout=120)
    try:
        r = json.loads(out[out.index("{"):])
    except ValueError:
        return "BLOCKED", tail(out)
    if not r["applicable"]:
        return "SKIP", "single-turn"
    lines = [f"      {p['to']}: {p['graded'] - p['missing']}/{p['graded']} earlier graded tests re-run"
             + "".join(f"\n        not re-run: {t}" for t in p["missing_sample"][:3]) for p in r["pairs"]]
    return ("PASS" if rc == 0 and r["ok"] else "FAIL"), "\n".join(lines)


def st_forge(ctx):
    rc, out = run([sys.executable, os.path.join(HERE, "forge_probe.py"), ctx["dir"], "--jobs", "3"],
                  ctx["log"]("forge"), timeout=4 * 3600)
    bad = [l for l in out.splitlines() if l.startswith(("FAIL", "UNVERIFIED", "WARN", "INFRA"))]
    level = {0: "PASS", 1: "FAIL", 3: "WARN"}.get(rc, "BLOCKED")
    return level, ("\n".join("      " + l[:220] for l in bad[:10]) or "no forge paid out, controls behaved")


def st_review(ctx):
    rc, out = run(["codimango", "bench", "ai-review", "review-task-swebench-v2", "-p", ctx["dir"]],
                  ctx["log"]("review"), cwd=ctx["repo"], timeout=3 * 3600)
    if rc != 0:
        return "BLOCKED", tail(out)
    # The skill ends with "**Final verdict:** Accept|Revise|Reject" and a decision-matrix row "C = n, H = n, M ...".
    m = re.search(r"final verdict:\**\s*\**\s*(accept|revise|reject)", out, re.I) or \
        re.search(r"recommended decision:\**\s*\**\s*(accept|revise|reject)", out, re.I)
    verdict = m.group(1).lower() if m else None
    mx = re.search(r"C\s*=\s*(\d+)\s*,\s*H\s*=\s*(\d+)\s*,\s*M\s*(=|≥|>=)\s*(\d+)", out)
    counts = f" (Critical {mx.group(1)}, High {mx.group(2)}, Medium {mx.group(3)}{mx.group(4)})" if mx else ""
    if verdict is None:
        return "WARN", "could not read the reviewer agent's verdict; read the log:\n" + tail(out)
    if verdict == "accept":
        return "PASS", "reviewer agent: Accept" + counts
    return "FAIL", (f"reviewer agent: {verdict.title()}{counts}. Fix every finding (rule R-026); full report in the log.\n"
                    "      PROVENANCE: the report may suggest instruction.md wording. Never paste it; route the\n"
                    "      requirement to Muse (mc2.sh). Test/plumbing fixes go to Codex.")


def st_calibrate(ctx):
    busy = bench_busy()
    if busy:
        return "BLOCKED", "another `bench run` owns this host (one per host, gateway 400 otherwise):\n" + \
            "\n".join("      " + l[:160] for l in busy[:3])
    splits = []
    for i in (1, 2):
        jobs = os.path.join(ctx["logdir"], f"k2n-{i}")
        rc, out = run(["codimango", "bench", "run", "-p", ctx["task"], "-a", ctx["k2n_agent"], "--k2n", "-o", jobs],
                      ctx["log"](f"calibrate-{i}"), cwd=ctx["repo"], timeout=14 * 3600)
        mans = sorted(glob.glob(os.path.join(jobs, "**", "manifest.json"), recursive=True), key=os.path.getmtime)
        if not mans:
            return "BLOCKED", f"k2n run {i} produced no manifest (exit {rc}):\n" + tail(out)
        splits.append(k2n_split(mans[-1]))
    lines, ok = [], True
    for step in sorted(splits[0]):
        cells = []
        for i, sp in enumerate(splits):
            s = sp.get(step, {"pass": 0, "fail": 0, "error": 0})
            n = s["pass"] + s["fail"]
            band = n > 0 and 1 <= s["pass"] <= 3 and s["pass"] < n
            ok &= band
            cells.append(f"run{i + 1} {s['pass']}/{n}" + (f" (+{s['error']} infra)" if s["error"] else "") + ("" if band else " OUT"))
        lines.append(f"      step {step}: " + ", ".join(cells))
    return ("PASS" if ok else "FAIL"), "\n".join(lines) + ("" if ok else "\n      target: 1-3 passes of 5 on every step, in both runs")


STAGES = {"preflight": st_preflight, "presubmit": st_presubmit, "provenance": st_provenance, "carry": st_carry,
          "forge": st_forge, "review": st_review, "calibrate": st_calibrate}


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        print(__doc__)
        sys.exit(2)
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    repo = os.path.abspath(opt("--repo", os.getcwd()))
    task = a[0].rstrip("/").split("/")[-1]
    tdir = os.path.join(repo, task)
    if not os.path.isdir(tdir) and not ("--check-stamp" in a and opt("--at")):
        print(f"no task directory {tdir} (run from the task repo or pass --repo)")
        sys.exit(2)
    if "--check-stamp" in a:  # push-task.sh / pre-push hook: clean full run for these exact files? (--at <commit>)
        p = os.path.join(STAMPS, f"{task}.json")
        s = json.load(open(p)) if os.path.exists(p) else None
        why = ("no gate run recorded" if not s else
               "task files changed since the last gate run" if s["hash"] != task_hash(tdir, opt("--at")) else
               "last gate run was not a full run" if not s.get("full_run") else
               f"last gate verdict was {s['verdict']}" if s["verdict"] != "PASS" else "")
        print(f"gate stamp OK ({s['utc']})" if not why else f"gate stamp missing: {why}")
        sys.exit(0 if not why else 1)
    stages = FAST if "--fast" in a else ORDER
    if opt("--only"):
        stages = [s for s in ORDER if s in opt("--only").split(",")]
    if opt("--skip"):
        stages = [s for s in stages if s not in opt("--skip").split(",")]
    logdir = f"/tmp/revision-gate/{task}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    os.makedirs(logdir, exist_ok=True)
    ctx = {"repo": repo, "task": task, "dir": tdir, "logdir": logdir, "k2n_agent": opt("--k2n-agent", "metacode"),
           "log": lambda n: os.path.join(logdir, n + ".log")}
    before = task_hash(tdir)
    print(f"revision-gate  {task}  (PROVISIONAL: see ledger/VERIFY-revision-gate.md)\nlogs: {logdir}\n")
    results = {}
    for s in stages:
        t0 = time.time()
        try:
            level, msg = STAGES[s](ctx)
        except Exception as e:  # a broken stage must not look like a pass
            level, msg = "BLOCKED", f"stage crashed: {e!r}"
        results[s] = level
        print(f"{level:<8} {s:<11} ({time.time() - t0:5.0f}s)\n{msg}\n", flush=True)
    after = task_hash(tdir)
    if after != before:
        print("WARNING  task files changed while the gate ran; results apply to neither version. Re-run.")
        results["integrity"] = "FAIL"
    levels = set(results.values())
    verdict = "FAIL" if "FAIL" in levels else "BLOCKED" if "BLOCKED" in levels else "PASS"
    full = all(s in results for s in ORDER)  # every stage ran (pass or fail): this run decides the push stamp
    os.makedirs(STAMPS, exist_ok=True)
    stamp = {"task": task, "hash": after, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "results": results, "verdict": verdict, "full_run": full, "provisional": True, "logs": logdir}
    # Only a full run writes <task>.json (the push stamp); partial runs go to <task>.partial.json so a
    # quick diagnostic never revokes a valid push stamp for unchanged files.
    json.dump(stamp, open(os.path.join(STAMPS, f"{task}.json" if full else f"{task}.partial.json"), "w"), indent=1)
    print(f"VERDICT  {verdict}" + ("  (push stamp issued)" if full and verdict == "PASS" else
                                  "  (no push stamp: needs a full run with every stage clear)"))
    sys.exit({"PASS": 0, "FAIL": 1, "BLOCKED": 4}[verdict])


main()

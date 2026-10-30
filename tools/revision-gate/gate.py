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
  7 calibrate     codimango bench run --k2n, once             every step 1-3/5; skipped when nothing that moves
                                                              difficulty changed since the server-validated commit

Documentation-only mode (README.md and audit/** only):
  D1 server-evidence  exact validated commit; all server gates green; review ledger closed
  D2 presubmit        README sections/counts and all mechanical checks

Usage:
  gate.py <task> [--repo DIR] [--fast] [--only s1,s2] [--skip s1,s2] [--k2n-agent metacode]
          [--accept-uncovered "<what you checked by hand>"]   when no forge applies to a step's language
          [--calibrate-runs N]   force N local k2n runs (default: 1 run, and only if difficulty can have moved)
          [--accept-zero "<third-party gradient evidence>"]  when a 0/5 Avocado step is server-carried
          [--calibrate-first]  reserve the scarce host-wide bench slot before the remaining stages
  gate.py <task> --documentation-only [--repo DIR]           reuse server evidence; never run Docker/k2n
  gate.py --version                                           build id (also printed and stamped)
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
def gate_version():
    h = hashlib.sha256()
    for f in ("gate.py", "carry_forward.py", "forge_probe.py", "forge_payloads/plant.sh", "pre-push"):
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:12]


ORDER = ["preflight", "presubmit", "provenance", "carry", "forge", "review", "calibrate"]
FAST = ORDER[:5]
DOC_ORDER = ["server-evidence", "presubmit"]


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


def git_output(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def changed_task_paths(repo, task, validated_sha):
    """Return task-relative paths changed from the validated commit, including untracked files."""
    tracked = git_output(repo, "diff", "--name-only", validated_sha, "--", task + "/")
    if tracked.returncode != 0:
        raise RuntimeError(tracked.stderr.strip() or f"cannot diff validated commit {validated_sha}")
    untracked = git_output(repo, "ls-files", "--others", "--exclude-standard", "--", task + "/")
    prefix = task + "/"
    names = set(tracked.stdout.splitlines()) | set(untracked.stdout.splitlines())
    return sorted(n[len(prefix):] for n in names if n.startswith(prefix))


def codimango_json(ctx, subcommand, log_name):
    cmd = ["codimango", "task", subcommand, ctx["task"], "--json"]
    p = subprocess.run(cmd, cwd=ctx["repo"], capture_output=True, text=True, timeout=120)
    with open(ctx["log"](log_name), "w") as f:
        f.write("$ " + " ".join(cmd) + "\n")
        if p.stderr:
            f.write(p.stderr + "\n")
        f.write(p.stdout)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed ({p.returncode}): {p.stderr.strip()}")
    return json.loads(p.stdout)


def tail(text, n=6):
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("$ ")]
    return "\n".join("      " + l[:200] for l in lines[-n:])


def bench_busy():
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if "codimango-bench" in l and " bench run" in l]


def k2n_manifest(jobs_dir):
    """The k2n RUN manifest: newest manifest.json under jobs_dir whose JSON is an object with a `cells`
    list. Trial artifacts can contain other manifest.json files (some are JSON lists); never pick those."""
    best = None
    # os.walk, not glob("**"): glob skips dot-dirs, and k2n writes its run manifest under .k2n/
    for p in (os.path.join(r, "manifest.json") for r, _, fs in os.walk(jobs_dir) if "manifest.json" in fs):
        try:
            m = json.load(open(p))
        except (ValueError, OSError):
            continue
        if isinstance(m, dict) and isinstance(m.get("cells"), list):
            if best is None or os.path.getmtime(p) > os.path.getmtime(best[0]):
                best = (p, m)
    return best


def k2n_split(m):
    per = {}
    for c in m.get("cells", []):
        cur = next((a for a in c.get("attempts", []) if a.get("attempt_id") == c.get("current_attempt_id")), None)
        v = ((cur or {}).get("outcome") or {}).get("verdict")
        s = per.setdefault(c["step_index"] + 1, {"pass": 0, "fail": 0, "error": 0})
        s[v if v in ("pass", "fail") else "error"] += 1
    return per


LOCK = "/tmp/swebench-docker.lock"


def docker_lock(cmd):
    """Run a SHORT container stage (preflight, forge) under the host-wide docker mutex push-task.sh uses,
    unless the caller already holds it. Long stages (calibration) must not hold it: a whole-gate or
    k2n-long hold starved other lanes' preflight for ~2 h (verifier 3, 2026-10-16)."""
    if os.environ.get("SWEBENCH_DOCKER_LOCK_HELD"):
        return cmd
    busy = subprocess.run(["flock", "-n", LOCK, "true"], capture_output=True).returncode != 0
    if busy:  # queue visibility: say who holds it before waiting
        holders = subprocess.run(["bash", "-c", f"for p in $(fuser {LOCK} 2>/dev/null); do ps -o pid=,etime=,args= -p $p; done"],
                                 capture_output=True, text=True).stdout.strip()
        print(f"         waiting for {LOCK}; held by:\n" + "\n".join("           " + l[:150] for l in holders.splitlines()[:4]),
              flush=True)
    return ["flock", "-w", "7200", LOCK, "env", "SWEBENCH_DOCKER_LOCK_HELD=1", *cmd]


# ---------------------------------------------------------------- stages
def st_preflight(ctx):
    rc, out = run(docker_lock([os.path.join(SKILL, "preflight.sh"), ctx["task"], "--with-oracle"]), ctx["log"]("preflight"),
                  cwd=ctx["repo"], timeout=5400)
    return ("PASS" if rc == 0 else "FAIL"), ("preflight exit 0, oracle 3/3" if rc == 0 else tail(out))


def st_server_evidence(ctx):
    """Reuse authoritative server evidence only when every non-document task byte is unchanged."""
    task = codimango_json(ctx, "show", "server-task")
    reviews = codimango_json(ctx, "reviews", "server-reviews")
    comments = codimango_json(ctx, "comments", "server-comments")
    sha = task.get("validationCommitSha")
    if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
        return "BLOCKED", f"server has no full validationCommitSha: {sha!r}"
    exists = git_output(ctx["repo"], "cat-file", "-e", sha + "^{commit}")
    if exists.returncode != 0:
        return "BLOCKED", f"validated commit {sha} is not in the local clone; fetch it and retry"

    changed = changed_task_paths(ctx["repo"], ctx["task"], sha)
    disallowed = [p for p in changed if p != "README.md" and not p.startswith("audit/")]
    if not changed:
        return "FAIL", "no documentation change relative to the server-validated commit"
    if disallowed:
        return "FAIL", "documentation-only mode refused non-document changes:\n" + \
            "\n".join("      " + p for p in disallowed)

    details = task.get("validationDetails") or []
    bad_details = [d for d in details if d.get("status") != "passed"]
    required_labels = {
        "Structural checks", "Oracle validation", "Metacode or Opus pass/fail balance",
        "Agentic trial-output review", "Contamination check",
    }
    missing = sorted(required_labels - {d.get("label") for d in details})
    problems = []
    if task.get("validationStatus") != "passing":
        problems.append(f"validationStatus={task.get('validationStatus')!r}")
    if task.get("tbdReviewStatus") != "pass":
        problems.append(f"tbdReviewStatus={task.get('tbdReviewStatus')!r}")
    if task.get("oraclePassCount") != 3 or task.get("oracleTotalCount") != 3:
        problems.append(f"oracle={task.get('oraclePassCount')}/{task.get('oracleTotalCount')}")
    if bad_details:
        problems.extend(f"{d.get('label')}: {d.get('status')}" for d in bad_details)
    if missing:
        problems.append("missing server gates: " + ", ".join(missing))
    if problems:
        return "FAIL", "server evidence is not reusable:\n" + "\n".join("      " + p for p in problems)

    readme_path = os.path.join(ctx["dir"], "README.md")
    readme = open(readme_path, errors="replace").read() if os.path.exists(readme_path) else ""
    headings = ["# Description", "# Completion Rates", "# Model Analysis", "# Anti-Cheating Analysis"]
    readme_problems = [f"README missing {h}" for h in headings if h not in readme]
    if sha[:7] not in readme and sha[:8] not in readme:
        readme_problems.append(f"README does not name validated commit {sha[:8]}")
    if not re.search(r"Oracle:\s*3/3", readme, re.I):
        readme_problems.append("README does not record Oracle: 3/3")

    balance = next((d.get("detail", "") for d in details if d.get("label") == "Metacode or Opus pass/fail balance"), "")
    rates = re.search(r"avocado\s*\[[^]]+\]\s*([0-9.]+)\|([0-9.]+)\|([0-9.]+)", balance, re.I)
    step_dirs = sorted(glob.glob(os.path.join(ctx["dir"], "steps", "*")))
    if rates and len(step_dirs) == 3:
        expected = [int(round(float(x) * 5)) for x in rates.groups()]
        for step_dir, passed in zip(step_dirs, expected):
            step = os.path.basename(step_dir)
            if not re.search(rf"`?{re.escape(step)}`?\s*:\s*{passed}/5", readme):
                readme_problems.append(f"README does not record current {step}: {passed}/5")
    else:
        readme_problems.append("could not derive the three current Avocado rates from server evidence")
    if readme_problems:
        return "FAIL", "README/server mismatch:\n" + "\n".join("      " + p for p in readme_problems)

    review_decisions = [r.get("decision") for r in reviews.get("reviews", []) if r.get("decision")]
    if task.get("reviewStatus") == "needs_revision" or "revision" in review_decisions:
        ledger_path = os.path.join(ctx["dir"], "audit", "REVIEW-LEDGER.md")
        ledger = open(ledger_path, errors="replace").read() if os.path.exists(ledger_path) else ""
        if "OPEN count: 0" not in ledger:
            return "FAIL", "task needs revision, but audit/REVIEW-LEDGER.md does not state OPEN count: 0"
        if re.search(r"\|\s*OPEN\s*\|", ledger, re.I):
            return "FAIL", "audit/REVIEW-LEDGER.md still contains an OPEN finding"

    return "PASS", (f"reused {sha[:8]}: validation passing, oracle 3/3, all {len(details)} server gates passed; "
                    f"{len(reviews.get('reviews', []))} review(s), {len(comments.get('comments', []))} comment(s), "
                    f"documentation diff only ({', '.join(changed)})")


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
    src = open(tool).read()
    pat = r'^ROOT\s*=.*$'
    if not re.search(pat, src, re.M):
        return "BLOCKED", "prov_predict.py no longer defines ROOT; cannot point it at --repo"
    patched = os.path.join(ctx["logdir"], "prov_predict_repo.py")
    open(patched, "w").write(re.sub(pat, f"ROOT = {ctx['repo']!r}  # revision-gate: --repo", src, count=1, flags=re.M))
    rc, out = run([sys.executable, patched, ctx["task"]], ctx["log"]("provenance"), cwd=ctx["repo"], timeout=600)
    if "PREDICTED CONTAMINATED" in out:
        return "FAIL", tail(out, 8)
    if rc != 0:
        return "BLOCKED", tail(out)
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
    rc, out = run(docker_lock([sys.executable, os.path.join(HERE, "forge_probe.py"), ctx["dir"], "--jobs", "2"]),
                  ctx["log"]("forge"), timeout=4 * 3600)
    shown = [l for l in out.splitlines() if l.startswith(("FAIL", "UNVERIFIED", "UNCOVERED", "WARN", "SKIP", "INFRA"))]
    msg = "\n".join("      " + l[:220] for l in shown[:12]) or "      every applicable forge ran and none paid out; controls behaved"
    if rc == 1:
        return "FAIL", msg
    if rc not in (0, 3):
        return "BLOCKED", msg
    if any(l.startswith("UNVERIFIED") for l in shown):
        return "BLOCKED", msg + "\n      the reference solution did not score 1 in the probe container, so nothing about fake-pass"\
            "\n      was verified for that step. Fix the probe environment (or the oracle) and re-run."
    if any(l.startswith("UNCOVERED") for l in shown):
        why = ctx.get("accept_uncovered")
        if not why:
            return "FAIL", msg + ("\n      No effective forge ran for at least one step, so fake-pass was NOT checked. Review the"
                                  "\n      grader by hand, then re-run with --accept-uncovered \"<what you checked>\" (recorded in the stamp).")
        return "WARN", msg + f"\n      uncovered steps accepted by hand: {why}"
    return "PASS", msg


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


DIFFICULTY_PATHS = re.compile(r"(^|/)(instruction\.md$|tests/|solution/|environment/)")


def difficulty_change(ctx):
    """Why calibration must run, or None when nothing that moves difficulty changed since the commit the
    server last validated (its calibration of that commit stands). Difficulty moves with an instruction,
    a test, the reference solution, the environment, or an agent/verifier timeout in task.toml."""
    r = subprocess.run(["codimango", "task", "show", ctx["task"], "--json"], capture_output=True, text=True)
    try:
        sha = json.loads(r.stdout).get("validationCommitSha")
    except ValueError:
        sha = None
    if not sha:
        return "no server-validated commit for this task yet"
    g = lambda *c: subprocess.run(["git", "-C", ctx["repo"], *c], capture_output=True, text=True)
    if g("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        g("fetch", "-q", "origin")
        if g("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
            return f"server-validated commit {sha[:8]} is not available locally"
    t = ctx["task"] + "/"
    changed = g("diff", "--name-only", sha, "--", t).stdout.split() + \
        g("ls-files", "-o", "--exclude-standard", "--", t).stdout.split()
    hits = [f for f in changed if DIFFICULTY_PATHS.search(f[len(t):])]
    if t + "task.toml" in changed and re.search(r"^[-+].*timeout", g("diff", sha, "--", t + "task.toml").stdout, re.M):
        hits.append(t + "task.toml (timeout)")
    ctx["validated_sha"] = sha
    return (f"{len(hits)} difficulty-affecting file(s) changed since server-validated {sha[:8]}, e.g. "
            + ", ".join(h[len(t):] for h in hits[:3])) if hits else None


def st_calibrate(ctx):
    # Run only when difficulty can have moved, and once: the server's own calibration after the push is the
    # second sample. Two local k2n runs per gate (~2 h each, one bench per host) queued ~16 h of benching
    # with four revisions in flight (2026-10-16), which defeated the point of the gate.
    why = None if ctx.get("calibrate_runs_forced") else difficulty_change(ctx)
    if why is None and not ctx.get("calibrate_runs_forced"):
        return "SKIP", (f"no instruction/test/solution/environment/timeout change since server-validated "
                        f"{ctx.get('validated_sha', '?')[:8]}; the server's calibration of that commit stands")
    # One `bench run` per host (gateway 400 otherwise): wait for the slot instead of failing at once.
    deadline = time.time() + float(ctx.get("bench_wait_h", 6)) * 3600
    while bench_busy():
        if time.time() > deadline:
            return "BLOCKED", "another `bench run` held this host for the whole wait window:\n" + \
                "\n".join("      " + l[:160] for l in bench_busy()[:3])
        time.sleep(120)
    splits = []
    for i in range(1, ctx["calibrate_runs"] + 1):
        jobs = os.path.join(ctx["logdir"], f"k2n-{i}")
        rc, out = run(["codimango", "bench", "run", "-p", ctx["task"], "-a", ctx["k2n_agent"], "--k2n", "-o", jobs],
                      ctx["log"](f"calibrate-{i}"), cwd=ctx["repo"], timeout=14 * 3600)
        found = k2n_manifest(jobs)
        if not found:
            return "BLOCKED", f"k2n run {i} produced no run manifest (exit {rc}):\n" + tail(out)
        splits.append(k2n_split(found[1]))
    steps = sorted(set().union(*splits))
    last = steps[-1] if steps else None
    lines, ok, incomplete, exempt_used = [], True, False, None
    for step in steps:
        cells, saturated = [], True
        for i, sp in enumerate(splits):
            s = sp.get(step, {"pass": 0, "fail": 0, "error": 0})
            n = s["pass"] + s["fail"]
            if n < 5:
                incomplete = True
            saturated &= n >= 5 and s["pass"] == n
            band = n >= 5 and 1 <= s["pass"] <= 3
            # RUNBOOK phase-1 band: 0/5 is acceptable only with a third-party gradient and legit failures.
            zero = n >= 5 and s["pass"] == 0 and bool(ctx.get("accept_zero"))
            cells.append((i, s, n, band, zero))
        # Server rule: one non-final step may sit at 1.0 when the task declares 3+ steps (single-1.0 exemption).
        exempt = saturated and len(steps) >= 3 and step != last and exempt_used is None
        if exempt:
            exempt_used = step
        txt = []
        for i, s, n, band, zero in cells:
            good = band or exempt or zero
            ok &= good or n < 5
            txt.append(f"run{i + 1} {s['pass']}/{n}" + (f" (+{s['error']} infra)" if s["error"] else "")
                       + (" exempt" if exempt else "" if band else " ZERO-ACCEPTED" if zero
                          else " OUT" if n >= 5 else " INCOMPLETE"))
        lines.append(f"      step {step}: " + ", ".join(txt))
    msg = "\n".join(lines) or "      no cells"
    if not steps or incomplete:
        return "BLOCKED", msg + "\n      fewer than 5 countable (pass/fail) cells on some step: infra errors or an unfinished run. Re-run."
    head = f"      calibrated because: {why}\n" if why else ""
    if ok:
        return "PASS", head + msg + (f"\n      step {exempt_used} used the single-1.0 exemption (3+ steps, not the last)" if exempt_used else "") + \
            ("\n      one local run; the server's calibration after the push is the second sample" if len(splits) == 1 else "")
    return "FAIL", head + msg + "\n      target: 1-3 passes of 5 on every step in every run (one non-final 5/5 allowed when the task has 3+ steps;"\
        "\n      0/5 only with --accept-zero \"<third-party gradient evidence>\")"


STAGES = {"server-evidence": st_server_evidence, "preflight": st_preflight, "presubmit": st_presubmit, "provenance": st_provenance, "carry": st_carry,
          "forge": st_forge, "review": st_review, "calibrate": st_calibrate}


def main():
    a = sys.argv[1:]
    if a[:1] == ["--version"]:
        print(f"revision-gate build {gate_version()}  ({HERE})")
        sys.exit(0)
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
    documentation_only = "--documentation-only" in a
    stages = DOC_ORDER if documentation_only else FAST if "--fast" in a else ORDER
    if opt("--only"):
        stages = [s for s in ORDER if s in opt("--only").split(",")]
    if opt("--skip"):
        stages = [s for s in stages if s not in opt("--skip").split(",")]
    if "--calibrate-first" in a and "calibrate" in stages:
        stages = ["calibrate"] + [s for s in stages if s != "calibrate"]
    logdir = f"/tmp/revision-gate/{task}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    os.makedirs(logdir, exist_ok=True)
    ctx = {"repo": repo, "task": task, "dir": tdir, "logdir": logdir, "k2n_agent": opt("--k2n-agent", "metacode"),
           "accept_uncovered": opt("--accept-uncovered"), "accept_zero": opt("--accept-zero"),
           "calibrate_runs": int(opt("--calibrate-runs", "1")), "calibrate_runs_forced": "--calibrate-runs" in a,
           "log": lambda n: os.path.join(logdir, n + ".log")}
    before = task_hash(tdir)
    print(f"revision-gate  {task}  build {gate_version()}  (PROVISIONAL: see ledger/VERIFY-revision-gate.md)\nlogs: {logdir}\n")
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
    required = DOC_ORDER if documentation_only else ORDER
    full = all(s in results for s in required)  # every required stage ran: this run decides the push stamp
    os.makedirs(STAMPS, exist_ok=True)
    stamp = {"task": task, "hash": after, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "build": gate_version(), "accepted_uncovered": opt("--accept-uncovered"),
             "accepted_zero": opt("--accept-zero"), "mode": "documentation-only" if documentation_only else "full",
             "results": results, "verdict": verdict, "full_run": full, "provisional": True, "logs": logdir}
    # Only a full run writes <task>.json (the push stamp); partial runs go to <task>.partial.json so a
    # quick diagnostic never revokes a valid push stamp for unchanged files.
    json.dump(stamp, open(os.path.join(STAMPS, f"{task}.json" if full else f"{task}.partial.json"), "w"), indent=1)
    print(f"VERDICT  {verdict}" + ("  (push stamp issued)" if full and verdict == "PASS" else
                                  "  (no push stamp: needs a full run with every stage clear)"))
    sys.exit({"PASS": 0, "FAIL": 1, "BLOCKED": 4}[verdict])


main()

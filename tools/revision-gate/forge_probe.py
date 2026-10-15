#!/usr/bin/env python3
"""Fake-pass ("forge") probes: can a step's grader be made to pay out with no solution?

Reviewers reject any task whose grader pays reward 1 without a real solution (django
fieldtracker: planted pytest.ini; vobject: planted forges + readable gold; reversion: root
can swap the interpreter). This reproduces grading in a plain container, outside the task dir:

  for each step N:
    seed     = task image + reference solve.sh of steps 1..N-1   (what an agent starts from)
    control  = seed + step N solve.sh  -> verifier must pay 1     (else the probe is UNVERIFIED)
    null     = seed, nothing planted   -> verifier must pay 0
    forge_*  = seed + one planted forge, no solution -> verifier must pay 0
    gold     = (python) a hook running during grading must not be able to read the gold patch
    leak     = after the control run, the step's hidden test files must be gone from the repo (WARN)

Usage: forge_probe.py <task-dir> [--steps 1,3] [--jobs 2] [--keep-images] [--json]
Exit: 0 = no FAIL, 1 = a forge paid out / null paid out / gold readable, 2 = usage or infra error,
      3 = nothing failed but some step could not be verified (control did not pay 1) or no forge applied
      to it (UNCOVERED).
Never writes inside the task directory. Containers run with --network none.
"""
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOADS = os.path.join(HERE, "forge_payloads")


def sh(cmd, timeout=None, check=False, input=None):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=input)
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}... failed: {p.stderr[-800:]}")
    return p


def layout(task):
    sd = os.path.join(task, "steps")
    if os.path.isdir(sd):
        def num(d):
            m = re.match(r"(\d+)_", d)
            return int(m.group(1)) if m else 10**9
        names = sorted((d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d, "tests"))), key=num)
        return [{"name": n, "dir": os.path.join(sd, n)} for n in names]
    return [{"name": "single", "dir": task}]


def verifier_timeout(task, step_name):
    try:
        t = tomllib.load(open(os.path.join(task, "task.toml"), "rb"))
    except Exception:
        return 1800
    for s in t.get("steps", []):
        if s.get("name") == step_name:
            return int(s.get("verifier", {}).get("timeout_sec", 1800))
    return int(t.get("verifier", {}).get("timeout_sec", 1800))


def languages(steps):
    exts = {".py": "python", ".go": "go", ".rb": "ruby", ".ts": "js", ".js": "js", ".mjs": "js",
            ".rs": "rust", ".java": "java", ".kt": "java", ".php": "php"}
    found = set()
    for s in steps:
        cfg = json.load(open(os.path.join(s["dir"], "tests", "config.json")))
        for path in re.findall(r"^\+\+\+ b/(\S+)", cfg.get("test_patch", ""), re.M):
            ext = os.path.splitext(path)[1]
            if ext in exts:
                found.add(exts[ext])
    return found


def required_ids(step):
    cfg = json.load(open(os.path.join(step["dir"], "tests", "config.json")))
    return list(cfg.get("fail_to_pass") or cfg.get("FAIL_TO_PASS") or []) + \
        list(cfg.get("pass_to_pass") or cfg.get("PASS_TO_PASS") or [])


def new_test_files(step):
    cfg = json.load(open(os.path.join(step["dir"], "tests", "config.json")))
    tp = cfg.get("test_patch", "")
    return re.findall(r"^--- /dev/null\n\+\+\+ b/(\S+)", tp, re.M)


class Box:
    """One throwaway container."""

    def __init__(self, image, tag):
        self.name = f"gate-forge-{tag}-{os.getpid()}"
        sh(["docker", "rm", "-f", self.name])
        sh(["docker", "run", "-d", "--name", self.name, "--network", "none",
            "--entrypoint", "sleep", image, "infinity"], check=True)

    def exec(self, script, timeout=900):
        return sh(["docker", "exec", "-i", self.name, "bash", "-s"], timeout=timeout, input=script)

    def cp_in(self, src, dst):
        sh(["docker", "cp", src, f"{self.name}:{dst}"], check=True)

    def commit(self, image):
        sh(["docker", "commit", self.name, image], check=True)

    def close(self):
        sh(["docker", "rm", "-f", self.name])


def run_solve(box, step):
    box.exec("rm -rf /solution && mkdir -p /solution")
    box.cp_in(os.path.join(step["dir"], "solution") + "/.", "/solution")
    r = box.exec("cd /app 2>/dev/null || cd /testbed; bash /solution/solve.sh; echo SOLVE_RC=$?", timeout=1800)
    box.exec("rm -rf /solution")
    return "SOLVE_RC=0" in r.stdout, r.stdout[-400:] + r.stderr[-400:]


def run_verifier(box, step, timeout):
    box.exec("rm -rf /tests && mkdir -p /tests /logs/verifier && rm -f /logs/verifier/*")
    box.cp_in(os.path.join(step["dir"], "tests") + "/.", "/tests")
    try:
        box.exec("cd /app 2>/dev/null || cd /testbed; bash /tests/test.sh > /tmp/zz_gate_verifier.log 2>&1", timeout=timeout + 120)
    except subprocess.TimeoutExpired:
        return None, "verifier timed out"
    r = box.exec("cat /logs/verifier/reward.txt 2>/dev/null; echo")
    val = r.stdout.strip()
    tail = box.exec("tail -c 600 /tmp/zz_gate_verifier.log").stdout
    try:
        return float(val.split()[0]) if val else None, tail
    except ValueError:
        return None, tail


def plant(box, forge, ids):
    """Copy forge payloads into the container and run its plant script with the required test IDs."""
    box.exec("rm -rf /tmp/zz_gate && mkdir -p /tmp/zz_gate")
    box.cp_in(PAYLOADS + "/.", "/tmp/zz_gate")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(ids) + "\n")
    box.cp_in(f.name, "/tmp/zz_gate/required_ids.txt")
    os.unlink(f.name)
    r = box.exec(f"bash /tmp/zz_gate/plant.sh {forge}")
    return "PLANTED" in r.stdout, (r.stdout + r.stderr)[-400:]


FORGES = {
    "python": ["py_conftest", "py_ini_plugin", "py_sitecustomize", "py_pytest11"],
    "go": ["go_exec_wrapper"],
    "ruby": ["rb_dotrspec", "rb_rubygems_defaults"],
    "js": ["js_npmrc_require"],
    "rust": ["rs_cargo_runner", "rs_cargo_home_runner"],
    "java": ["java_surefire_reports"],
    "php": ["php_phpunit_xml", "php_conf_d_prepend"],
}
GENERIC = ["any_interpreter_swap"]  # (a pre-planted reward.txt is moot: the harness clears /logs/verifier first)
STATIC = {"java_surefire_reports"}  # no code runs; its files are the forge, so it counts as loaded


def probe_step(task, step, prev, base_image, jobs, last=None):
    res = {"step": step["name"], "checks": []}
    add = lambda name, level, msg: res["checks"].append({"check": name, "level": level, "msg": msg})
    tmo = verifier_timeout(task, step["name"])
    seed_image = f"{base_image}-seed-{step['name'].lower()}"
    box = Box(base_image, "seed")
    try:
        for p in prev:
            ok, log = run_solve(box, p)
            if not ok:
                add("seed", "UNVERIFIED", f"reference solve.sh of {p['name']} failed while seeding: {log}")
                return res
        box.exec("cd /app 2>/dev/null || cd /testbed; git add -A >/dev/null 2>&1; true")
        box.commit(seed_image)
    finally:
        box.close()

    ids = required_ids(step)
    langs = languages([step])
    forges = GENERIC + [f for lang in sorted(langs) for f in FORGES.get(lang, [])]

    def one(kind):
        b = Box(seed_image, kind.replace("_", "-"))
        try:
            if kind == "control":
                ok, log = run_solve(b, step)
                if not ok:
                    return kind, None, f"step solve.sh failed: {log}", []
                r, tail = run_verifier(b, step, tmo)
                left = b.exec("cd /app 2>/dev/null || cd /testbed; for f in " +
                              " ".join(f"'{x}'" for x in new_test_files(step)) +
                              "; do [ -e \"$f\" ] && echo \"$f\"; done; true").stdout.split()
                return kind, r, tail, left
            if kind == "null":
                r, tail = run_verifier(b, step, tmo)
                return kind, r, tail, []
            ok, log = plant(b, kind, ids)
            if not ok:
                return kind, "NA", log, []
            b.exec("rm -f /tmp/zz_gate_loaded /tmp/zz_gate_gold_readable")
            r, tail = run_verifier(b, step, tmo)
            flags = b.exec("test -e /tmp/zz_gate_gold_readable && echo GOLD; test -e /tmp/zz_gate_loaded && echo LOADED").stdout.split()
            if kind in STATIC:
                flags.append("LOADED")
            return kind, r, tail, flags
        finally:
            b.close()

    with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
        out = {k: (r, t, x) for k, r, t, x in ex.map(one, ["control", "null"] + forges)}

    r, tail, left = out["control"]
    if r != 1:
        add("control", "UNVERIFIED", f"reference solution scored {r} in the probe container, so the forge "
            f"results for this step cannot be trusted. Verifier tail: {tail[-300:]}")
    else:
        add("control", "PASS", "reference solution scores 1 in the probe container")
    if left and step is not last:  # only matters when a later step's agent inherits this container
        add("leak", "WARN", f"hidden test files still in the repo after grading (next step's agent can read "
            f"them): {', '.join(left[:4])}")
    r, tail, _ = out["null"]
    add("null", "FAIL" if r == 1 else "PASS",
        "verifier pays 1 with NO solution" if r == 1 else f"no solution scores {r}")
    for f in forges:
        r, tail, extra = out[f]
        if r == "NA":
            add(f, "SKIP", f"not applicable here: {tail.strip()[-160:]}")
        elif r == 1:
            hint = (" Fix pattern (vobject): compute the reward in a private dir and copy it into place; never let the"
                    " python the agent can reach write /logs/verifier/reward.txt directly. Root in the container can"
                    " always defeat a smart enough wrapper; this probe checks the attack reviewers flag."
                    if f == "any_interpreter_swap" else "")
            add(f, "FAIL", f"forge paid reward 1 with no solution.{hint} Verifier tail: {tail[-200:]}")
        elif "LOADED" not in extra:
            out[f] = ("NOTLOADED",) + out[f][1:]
            add(f, "SKIP", "planted but its code never ran during grading (the verifier isolates it), so this proves nothing")
        else:
            add(f, "PASS", f"forge loaded during grading and scored {r}")
        if "GOLD" in extra:
            add("gold_readable", "FAIL", f"code running inside a test ({f}) could read the gold patch in "
                "/tests/config.json")
    effective = [f for f in forges if out[f][0] not in ("NA", "NOTLOADED")]
    if not effective:
        add("coverage", "UNCOVERED", f"no forge could be planted for {sorted(langs) or 'unknown language'}"
            + (f" (tried: {', '.join(forges)})" if forges else "") + "; fake-pass was not checked for this step")
    sh(["docker", "rmi", "-f", seed_image])
    return res


def main():
    argv = sys.argv[1:]
    if not argv or not os.path.isdir(argv[0]):
        print("usage: forge_probe.py <task-dir> [--steps 1,3] [--jobs 2] [--keep-images] [--json]", file=sys.stderr)
        sys.exit(2)
    task = os.path.abspath(argv[0])
    pick = None
    jobs = 2
    if "--steps" in argv:
        pick = {int(x) for x in argv[argv.index("--steps") + 1].split(",")}
    if "--jobs" in argv:
        jobs = int(argv[argv.index("--jobs") + 1])
    steps = layout(task)
    slug = re.sub(r"[^a-z0-9-]", "-", os.path.basename(task).lower())[:60]
    base_image = f"gate-forge-{slug}"
    b = sh(["docker", "build", "-q", "-t", base_image, "-f", os.path.join(task, "environment", "Dockerfile"),
            os.path.join(task, "environment")], timeout=3600)
    if b.returncode != 0:
        print(f"INFRA  docker build failed: {b.stderr[-600:]}")
        sys.exit(2)
    results = []
    for i, s in enumerate(steps):
        if pick and (i + 1) not in pick:
            continue
        results.append(probe_step(task, s, steps[:i], base_image, jobs, last=steps[-1]))
    if "--keep-images" not in argv:
        sh(["docker", "rmi", "-f", base_image])
    levels = [c["level"] for r in results for c in r["checks"]]
    if "--json" in argv:
        print(json.dumps(results, indent=1))
    else:
        for r in results:
            print(f"== {r['step']}")
            for c in r["checks"]:
                print(f"{c['level']:<10} {c['check']:<22} {c['msg']}")
    sys.exit(1 if "FAIL" in levels else 3 if ("UNVERIFIED" in levels or "UNCOVERED" in levels) else 0)


main()

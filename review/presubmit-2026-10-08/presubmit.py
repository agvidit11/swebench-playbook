#!/usr/bin/env python3
"""presubmit.py — mechanical first-submission checks for a codimango SWE-bench task.

READ-ONLY. Reads the task directory and the codimango server; writes nothing anywhere.
Encodes groups A (mechanical) and D (trial-status census) of
~/swebench/reviews-2026-10-08/FIRST-PASS-CHECKLIST.md — the checks that, by reading all 28
"Request changes" reviews on 2026-10-08, would have prevented the bulk of bounces.

Usage:
  presubmit.py <task-name> [--repo DIR] [--local-only] [--server-only]
Exit code: 0 = no FAIL (WARNs allowed), 1 = at least one FAIL, 2 = usage/infra error.

What it does NOT do (needs judgement or a container — see the checklist groups B, C, E, F):
forge attempts, per-assertion "is this stated?" quoting, golden-vs-standard validation,
collision/idempotency replay, MT step-dependency replay, public-issue sweep.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys
import tomllib
from urllib.parse import quote

REPO_URL = "https://github.com/codimango/swe-bench-pro-agvidit"
CLIENT_PATH = "/home/agvidit/.local/share/uv/tools/codimango/lib/python3.12/site-packages"
README_SECTIONS = ["Description", "Completion Rates", "Model Analysis", "Anti-Cheating"]
STAGE_MODEL = {"metacode": "avocado", "codex": "gpt", "agent": "claude", "opus": "claude"}

results = []  # (level, check, message)
SERVER_FMT = "?"


def record(level, check, msg):
    results.append((level, check, msg))


def ok(c, m):
    record("PASS", c, m)


def warn(c, m):
    record("WARN", c, m)


def fail(c, m):
    record("FAIL", c, m)


def sh(args, timeout=300):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except Exception as e:  # noqa: BLE001
        return f"__ERROR__ {e}"


def load_json_loose(text):
    # stderr banner ("Need help ... codimango feedback") may follow the JSON; decode only the document
    i = min([p for p in (text.find("{"), text.find("[")) if p >= 0], default=-1)
    return json.JSONDecoder().raw_decode(text[i:])[0] if i >= 0 else None


# ───────────────────────────── local checks ─────────────────────────────
# Files are read through SRC so checks can run against a git ref (default origin/main) instead of a
# working tree that may be stale. Measured 2026-10-08: the shared checkout was 141 commits behind and
# the tool failed 22/26 ACCEPTED tasks on README sections that origin/main already had.
class Source:
    def __init__(self, repo, task, ref):
        self.repo, self.task, self.ref = repo, task, ref
        self.root = os.path.join(repo, task)

    def _git(self, *a):
        r = subprocess.run(["git", "-C", self.repo, *a], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None

    def read(self, rel):
        if self.ref is None:
            p = os.path.join(self.root, rel)
            return open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else None
        return self._git("show", f"{self.ref}:{self.task}/{rel}")

    def exists(self, rel):
        return self.read(rel) is not None

    def files(self):
        if self.ref is None:
            out = []
            for root, _, fs in os.walk(self.root):
                if "/.git" not in root:
                    out += [os.path.relpath(os.path.join(root, f), self.root) for f in fs]
            return out
        t = self._git("ls-tree", "-r", "--name-only", self.ref, "--", self.task) or ""
        return [l[len(self.task) + 1:] for l in t.splitlines() if l.startswith(self.task + "/")]


SRC = None

def configs(task_dir):
    out = []
    if SRC.exists("tests/config.json"):
        out.append(("task", "tests/config.json"))
    steps = sorted({f.split("/")[1] for f in SRC.files()
                    if f.startswith("steps/") and f.endswith("/tests/config.json")})
    for st in steps:
        out.append((st, f"steps/{st}/tests/config.json"))
    return out


def check_readme(task_dir, cfgs):
    text = SRC.read("README.md")
    if text is None:
        fail("README", "README.md missing")
        return
    heads = [h.strip().lower() for h in re.findall(r"(?m)^#{1,3}\s+(.+)$", text)]
    missing = [s for s in README_SECTIONS if not any(s.lower() in h for h in heads)]
    if missing:
        fail("README sections", f"missing required section(s): {missing} "
             f"(spec: Description, Completion Rates, Model Analysis, Anti-Cheating Analysis). Intentionally "
             f"FAIL: some reviewers accept without them, but 5 tasks were bounced for exactly this; minutes to fix")
    else:
        ok("README sections", "all 4 required sections present")
    stale = re.findall(r"(?i)\b(TBD|not yet run|to be (?:filled|measured)|placeholder|"
                       r"complete (?:this|it) before)\b", text)
    if stale:
        fail("README completeness", f"placeholder text present: {sorted(set(s if isinstance(s,str) else s[0] for s in stale))}")
    else:
        ok("README completeness", "no TBD / 'not yet run' placeholders")
    internal = re.findall(r"(internalmeta\.com|internalfb\.com|workplace\.com|fburl\.com|"
                          r"fb\.workplace|our\.internmc)", text)
    if internal:
        warn("README internal URLs", f"internal links in README: {sorted(set(internal))}")
    else:
        ok("README internal URLs", "none")
    # graded-count claims vs config (single-turn / task-level only; MT counts vary per step)
    if cfgs and cfgs[0][0] == "task" and len(cfgs) == 1:
        c = json.loads(SRC.read(cfgs[0][1]))
        nf, np_ = len(c.get("fail_to_pass") or []), len(c.get("pass_to_pass") or [])
        claims = re.findall(r"(\d+)\s*`?(fail_to_pass|pass_to_pass|graded)", text)
        bad = []
        for n, kind in claims:
            n = int(n)
            want = {"fail_to_pass": nf, "pass_to_pass": np_, "graded": nf + np_}[kind]
            if n != want and not (kind == "graded" and n in (nf, np_)):
                bad.append(f"{n} {kind} (config: {want})")
        if bad:
            fail("README counts", "README count(s) disagree with tests/config.json: " + "; ".join(bad[:4]))
        elif claims:
            ok("README counts", f"match config ({nf} f2p / {np_} p2p)")


def check_task_toml(task_dir, name):
    raw = SRC.read("task.toml")
    if raw is None:
        fail("task.toml", "missing")
        return
    try:
        d = tomllib.loads(raw)
    except Exception as e:  # noqa: BLE001
        fail("task.toml", f"does not parse: {e}")
        return
    t, m = d.get("task", {}), d.get("metadata", {})
    want = f"codimango/{name}"
    if t.get("name") != want:
        warn("task.toml name", f"[task].name = {t.get('name')!r}, expected {want!r}")
    else:
        ok("task.toml name", want)
    for k in ("format", "workstream", "track_assignment"):
        if not t.get(k):
            fail("task.toml fields", f"[task].{k} missing")
    if not m.get("reward_type"):
        fail("task.toml metadata", "[metadata].reward_type missing (structural check)")
    soft = [k for k in ("difficulty", "category", "tags", "category_subdomain", "category_usecase") if not m.get(k)]
    if soft:
        warn("task.toml metadata", f"[metadata] missing (reviewers flag): {soft}")
    if "artifacts" in m and "artifacts" not in t:
        warn("task.toml artifacts", "artifacts declared under [metadata] — silently ignored; belongs in [task]")
    emails = [a.get("email", "") for a in t.get("authors", []) if isinstance(a, dict)]
    git_emails = set(sh(["git", "-C", task_dir, "log", "--format=%ae", "--", "."]).split())
    if emails and git_emails and not any(e in git_emails for e in emails):
        warn("task.toml author", f"author email {emails} not among commit authors {sorted(git_emails)[:3]}")
    return d


def check_configs(cfgs, fmt):
    if not cfgs:
        fail("config.json", "no tests/config.json found")
        return
    per_step = []
    for label, p in cfgs:
        try:
            c = json.loads(SRC.read(p))
        except Exception as e:  # noqa: BLE001
            fail(f"config {label}", f"does not parse: {e}")
            continue
        upper = [k for k in c if k.isupper()]
        if upper:
            warn(f"config {label}", f"uppercase duplicate keys {upper} — reviewers flag them as unused; "
                 f"remove ONLY if test.sh/parser.py don't read them as a fallback")
        for k in ("repo", "base_commit"):
            v = str(c.get(k, ""))
            if not v or "<" in v:
                fail(f"config {label}", f"{k} missing or placeholder: {v!r}")
        f2p, p2p = set(c.get("fail_to_pass") or []), set(c.get("pass_to_pass") or [])
        if label != "task" or len(cfgs) == 1:
            if not f2p:
                fail(f"config {label}", "fail_to_pass is empty")
            if f2p & p2p:
                fail(f"config {label}", f"{len(f2p & p2p)} id(s) in BOTH fail_to_pass and pass_to_pass")
        if label != "task":
            per_step.append((label, f2p, p2p))
        if f2p:
            ok(f"config {label}", f"{len(f2p)} f2p / {len(p2p)} p2p, clean keys")
    # MT: later steps must re-test earlier steps' f2p (reviewers: configupdater, net-imap, vobject)
    for i in range(1, len(per_step)):
        prev_f2p = per_step[i - 1][1]
        cur = per_step[i][1] | per_step[i][2]
        missing = prev_f2p - cur
        if missing:
            warn("MT re-test", f"{per_step[i][0]} does not re-run {len(missing)} of "
                 f"{len(prev_f2p)} f2p from {per_step[i-1][0]} (regressions invisible)")
        elif prev_f2p:
            ok("MT re-test", f"{per_step[i][0]} re-runs all f2p of {per_step[i-1][0]}")
    if len(cfgs) > 1 and cfgs[0][0] == "task":
        top = json.loads(SRC.read(cfgs[0][1]))
        top_f2p = set(top.get("fail_to_pass") or [])
        all_steps = set().union(*[s[1] for s in per_step]) if per_step else set()
        extra = top_f2p - all_steps
        if extra:
            warn("MT task-level config", f"task-level fail_to_pass has {len(extra)} id(s) no step grades")


def check_harness(task_dir):
    scripts = [f for f in SRC.files() if f.split("/")[-1] in ("test.sh", "run_script.sh")]
    for rel in scripts:
        s = SRC.read(rel) or ""
        if re.search(r"git apply --check[^\n]*\|\|[^\n]*exit 1", s) or \
           (re.search(r"git apply --check", s) and re.search(r"exit 1", s) and "--reverse" not in s):
            warn("harness collision", f"{rel}: `git apply --check … || exit 1` — a solver-created test "
                 f"file makes reward 0 (smoltcp review). Prefer direct write + idempotent mod/import line.")
        if re.search(r"(/usr/local/bin/(python3?|php|ruby|node|go))", s) and re.search(r"if \[ -[xef]", s):
            warn("harness interpreter", f"{rel}: conditionally uses a /usr/local/bin interpreter — "
                 f"root agent can plant it (vobject review). Use a fixed root-owned path.")
        if "--exclude-standard" in s:
            warn("harness ignore-escape", f"{rel}: uses --exclude-standard — agent-added ignore rules "
                 f"hide files from the stray-file check (spire review).")
        if re.search(r"bash -lc", s):
            warn("harness login shell", f"{rel}: `bash -lc` can drop toolchain PATH (cargo/go)")
    if any(os.sep + "steps" + os.sep in p for p in scripts):
        tests = [p for p in scripts if p.endswith("test.sh") and os.sep + "steps" + os.sep in p]
        traps = {p: bool(re.search(r"trap\b", SRC.read(p) or "")) for p in tests}
        if len(set(traps.values())) > 1:
            warn("MT EXIT trap", f"EXIT trap present in some step test.sh but not others: {traps} "
                 f"(graded files leak into the next step — net-imap review)")


# ───────────────────────────── server checks ─────────────────────────────

def api_task(name):
    sys.path.insert(0, CLIENT_PATH)
    from cli.api_client import CodimangoClient  # noqa: E402
    d = CodimangoClient()._request("GET", f"/api/v1/aai/tasks/{quote(name, safe='')}",
                                   params={"sourceRepo": REPO_URL}, cacheable=False)
    return d.get("task", d)


def check_server(name, task_dir):
    try:
        t = api_task(name)
    except Exception as e:  # noqa: BLE001
        fail("server", f"cannot read task from codimango: {str(e)[:120]}")
        return
    global SERVER_FMT
    SERVER_FMT = t.get("format") or "?"
    sha = str(t.get("commitSha") or "")
    vsha = str(t.get("validationCommitSha") or "")
    local = sh(["git", "-C", task_dir, "log", "-1", "--format=%H", "origin/main", "--", "."]).strip()
    if local and len(local) == 40 and sha and local != sha:
        fail("server freshness", f"server task is at {sha[:8]} but origin/main last touched this task at "
             f"{local[:8]} — stale import: run `codimango task rerun {name}` (free)")
    elif vsha and sha and vsha != sha:
        warn("server freshness", f"validation ran at {vsha[:8]} but task is at {sha[:8]}")
    else:
        ok("server freshness", f"server at {sha[:8]}")

    # validation rows
    for row in t.get("validationDetails") or []:
        st, lab, det = row.get("status"), row.get("label"), (row.get("detail") or "")[:140]
        if st == "passed":
            ok(f"validation: {lab}", det)
        elif st == "pending":
            fail(f"validation: {lab}", f"PENDING — never submit mid-validation: {det}")
        else:
            fail(f"validation: {lab}", f"{st}: {det} — fix, or write an override justification")
    if t.get("validationStatus") != "passing":
        fail("validation overall", f"validationStatus = {t.get('validationStatus')}")

    # engine stages (agentic-review / build-verification / evalgt) — text only in `task show`
    show = sh(["codimango", "task", "show", name])
    for st_name, st_val in re.findall(r"-\s+([a-z\-]+):\s+([a-z_]+)\s+@", show):
        if st_val == "passed":
            ok(f"stage {st_name}", "passed")
        else:
            fail(f"stage {st_name}", f"{st_val} — reviewers block on red engine stages "
                 f"(go-zero-goctl: 'Eval GT errors are hard blocking')")
    if t.get("evalGtNotFinalized"):
        fail("stage evalgt", "evalGt not finalized")

    # TBR
    tbr = t.get("tbdReviewStatus")
    if tbr != "pass":
        fail("TBR", f"tbdReviewStatus = {tbr} — re-run TBR at this commit before requesting review")
    else:
        d = t.get("tbdReviewDetails") or {}
        weak = {k.replace("_rating_value", ""): v for k, v in d.items()
                if k.endswith("_rating_value") and str(v).lower() in ("poor", "bad", "high", "no", "fail")}
        if weak:
            warn("TBR ratings", f"weak ratings reviewers will cite: {weak}")
        else:
            ok("TBR", "pass")

    # agentic verdict
    rv = sh(["codimango", "job", "review", name])
    m = re.search(r"\*\*Verdict:\*\*\s*([A-Z_]+)", rv)
    if not m:
        warn("agentic verdict", "no agentic review found at this commit")
    elif m.group(1) != "GOOD":
        fail("agentic verdict", f"{m.group(1)} — fix the named rubric items or justify each")
    else:
        ok("agentic verdict", "GOOD")

    check_trials(name, sha)

    # human review history
    hr = sh(["codimango", "task", "reviews", name, "--full"])
    decs = re.findall(r"REVIEW by [^\n]*@ ([0-9\- :]+) UTC.*?\*\*Decision:\*\*\s*([^\n]+)", hr, re.S)
    if decs:
        d0 = decs[0]
        lvl = warn if not d0[1].lower().startswith("accept") else ok
        lvl("human review", f"latest decision {d0[1].strip()} @ {d0[0][:16]} — make sure every point is addressed")


def check_trials(name, sha):
    jl = sh(["codimango", "job", "list", name])
    jobs = re.findall(r"^\s*(\d+)\s+status=(\w+)\s+progress=(\d+)/(\d+)\s+commit=([0-9a-f]+)", jl, re.M)
    cur = [j for j in jobs if sha.startswith(j[4])]
    if not cur:
        fail("trials", f"no validation jobs at {sha[:8]} — run `codimango task rerun {name}`")
        return
    running = [j for j in cur if j[1] in ("running", "queued", "pending", "scheduled")]
    if running:
        fail("trials", f"{len(running)} job(s) still {running[0][1]} at {sha[:8]} — wait for a complete verdict")
    cur = [j for j in cur if j[1] == "completed"]  # cancelled/error jobs at this SHA are superseded attempts
    by_model = collections.defaultdict(lambda: {"pass": 0, "fail": 0, "error": 0})
    fail_tests = collections.Counter()
    failed_trials = 0
    for jid, *_ in cur:
        raw = sh(["codimango", "trial", "list", jid, "--json"])
        try:
            d = load_json_loose(raw)
        except Exception:  # noqa: BLE001
            continue
        trials = d if isinstance(d, list) else (d or {}).get("trials", (d or {}).get("items", []))
        for tr in trials or []:
            stage = tr.get("stage") or "?"
            if stage not in STAGE_MODEL:  # oracle, agentic-review, test-patch[-validation] are not solvers
                continue
            model = STAGE_MODEL[stage]
            exc = json.dumps(tr.get("exceptionInfo") or "")
            if tr.get("status") != "completed" or "Error" in exc:
                by_model[model]["error"] += 1
                continue
            if (tr.get("reward") or 0) >= 1:
                by_model[model]["pass"] += 1
            else:
                by_model[model]["fail"] += 1
                failed_trials += 1
                tests = ((tr.get("ctrfResults") or {}).get("tests") or [])
                for tname in {x.get("name") for x in tests if x.get("status") not in ("passed", "skipped")}:
                    fail_tests[tname] += 1
    if not by_model:
        warn("trials", "no non-oracle trials parsed")
        return
    summary = ", ".join(f"{m}: {v['pass']}P/{v['fail']}F/{v['error']}E" for m, v in sorted(by_model.items()))
    errs = sum(v["error"] for v in by_model.values())
    swamped = [m for m, v in by_model.items() if v["error"] and v["error"] >= v["pass"] + v["fail"]]
    if swamped:
        fail("trial census", f"crashes swamp {swamped}: their measurement is hollow — {summary}. "
             f"Reviewers reject difficulty resting on crashes (mlx). `codimango task rerun {name}` first.")
    elif errs:
        warn("trial census", f"{errs} errored/crashed trial(s) — {summary}. Crashes are not difficulty "
             f"(mlx review). `codimango task rerun {name}` and re-check before submitting.")
    else:
        ok("trial census", f"all counted trials completed — {summary}")
    solvers = [m for m, v in by_model.items() if v["pass"] > 0]
    if len(solvers) == 0:
        fail("solvers", "no model solved it")
    elif len(solvers) == 1:
        warn("solvers", f"only {solvers[0]} solved it — reviewers ask for a second model (concourse review)")
    else:
        ok("solvers", f"solved by {solvers}")
    if failed_trials >= 2 and fail_tests:
        top, n = fail_tests.most_common(1)[0]
        if n / failed_trials >= 0.8:
            warn("single-test dominance", f"{n}/{failed_trials} failed trials fail `{top}` — that test carries "
                 f"the difficulty: prove it is STATED in instruction.md and fair (crossplane/spire-workload/redb)")


# ───────────────────────────── main ─────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task")
    ap.add_argument("--repo", default="/home/agvidit/swe-bench-pro-agvidit")
    ap.add_argument("--local-only", action="store_true")
    ap.add_argument("--server-only", action="store_true")
    ap.add_argument("--ref", default="origin/main",
                    help="git ref to read task files from (default origin/main); use --worktree for uncommitted edits")
    ap.add_argument("--worktree", action="store_true", help="read the working tree instead of a git ref")
    a = ap.parse_args()
    task_dir = os.path.join(a.repo, a.task)
    if not os.path.isdir(task_dir) and not a.server_only:
        print(f"task dir not found: {task_dir}", file=sys.stderr)
        return 2
    global SRC
    SRC = Source(a.repo, a.task, None if a.worktree else a.ref)
    if not a.worktree:
        # HTTPS fetch 403s on this repo (needs SSH cert); the :22 SSH URL works. A failed fetch must
        # not pass silently — a stale origin/main judged 22 accepted tasks wrong on 2026-10-08.
        r = subprocess.run(["git", "-C", a.repo, "fetch", "-q",
                            "ssh://git@github.com:22/codimango/swe-bench-pro-agvidit.git",
                            "+refs/heads/main:refs/remotes/origin/main"], capture_output=True, text=True)
        if r.returncode != 0:
            warn("git fetch", f"could not refresh origin/main ({r.stderr.strip()[:80]}) — local checks may be stale")
    fmt = "?"
    if not a.server_only:
        cfgs = configs(task_dir)
        d = check_task_toml(task_dir, a.task) or {}
        fmt = (d.get("task") or {}).get("format", "?")
        check_readme(task_dir, cfgs)
        check_configs(cfgs, fmt)
        check_harness(task_dir)
    if not a.local_only:
        check_server(a.task, task_dir)
        if fmt == "?":
            fmt = SERVER_FMT

    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    color = {"FAIL": "\033[31m", "WARN": "\033[33m", "PASS": "\033[32m"}
    print(f"\npresubmit: {a.task}  (format={fmt})")
    for lvl, check, msg in sorted(results, key=lambda r: order[r[0]]):
        print(f"  {color[lvl]}{lvl}\033[0m  {check}: {msg}")
    n = collections.Counter(r[0] for r in results)
    print(f"\n  {n['FAIL']} FAIL · {n['WARN']} WARN · {n['PASS']} PASS")
    print("  Not covered (judgement/container): forge attempts, per-assertion stated-check, golden vs "
          "real standard, collision/idempotency replay, MT step-dependency replay, public-issue sweep.")
    return 1 if n["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

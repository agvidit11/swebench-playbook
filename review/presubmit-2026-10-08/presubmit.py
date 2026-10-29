#!/usr/bin/env python3
"""presubmit.py — mechanical first-submission checks for a codimango SWE-bench task.

READ-ONLY BY DEFAULT. Reads the task repository and the codimango server. It never edits task
files or Git refs; refresh the selected Git ref yourself before running it.
Encodes groups A (mechanical) and D (trial-status census) of
evidence/FIRST-PASS-CHECKLIST.md — the checks that, by reading all 28
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
import shlex
import subprocess
import sys
import tomllib

README_SECTIONS = ["Description", "Completion Rates", "Model Analysis", "Anti-Cheating"]
STAGE_MODEL = {"metacode": "avocado", "codex": "gpt", "agent": "claude", "opus": "claude"}

results = []  # (level, check, message)
infra_failures = []
SERVER_FMT = "?"
SERVER_REVIEW_STATUS = None


class CommandError(RuntimeError):
    def __init__(self, kind, message):
        super().__init__(f"{kind}: {message}")
        self.kind = kind


def record(level, check, msg):
    results.append((level, check, msg))


def ok(c, m):
    record("PASS", c, m)


def warn(c, m):
    record("WARN", c, m)


def fail(c, m):
    record("FAIL", c, m)


def infra(c, m):
    infra_failures.append((c, m))
    fail(c, f"infrastructure error: {m}")


def sh(args, timeout=300):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except Exception as e:  # noqa: BLE001
        return f"__ERROR__ {e}"


def load_json_loose(text):
    """Decode the first JSON document, tolerating CLI banners before or after it."""
    decoder = json.JSONDecoder()
    for i, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            return decoder.raw_decode(text[i:])[0]
        except json.JSONDecodeError:
            pass
    return None


def command_json(args, timeout=300):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(str(e)) from e
    if r.returncode != 0:
        error_data = load_json_loose(r.stdout)
        if isinstance(error_data, dict) and isinstance(error_data.get("error"), dict):
            error = error_data["error"]
            raise CommandError(error.get("kind", "error"), error.get("message", "unknown error"))
        raise CommandError("command_failed", (r.stdout or r.stderr or f"exit {r.returncode}").strip())
    data = load_json_loose(r.stdout)
    if data is None:
        raise RuntimeError("command returned no JSON document")
    return data


def command_text(args, timeout=300):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        raise CommandError("command_failed", str(e)) from e
    if r.returncode != 0:
        raise CommandError("command_failed", (r.stdout or r.stderr or f"exit {r.returncode}").strip())
    return r.stdout


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

    def task_exists(self):
        if self.ref is None:
            return os.path.isdir(self.root)
        return bool(self.files())

    def last_commit(self):
        ref = self.ref or "HEAD"
        value = self._git("log", "-1", "--format=%H", ref, "--", self.task)
        return value.strip() if value else None

    def author_emails(self):
        ref = self.ref or "HEAD"
        value = self._git("log", "--format=%ae", ref, "--", self.task) or ""
        return set(value.split())


SRC = None

def natural_step_key(value):
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", value)]


def configs(task_dir):
    out = []
    if SRC.exists("tests/config.json"):
        out.append(("task", "tests/config.json"))
    steps = sorted({f.split("/")[1] for f in SRC.files()
                    if f.startswith("steps/") and f.endswith("/tests/config.json")},
                   key=natural_step_key)
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
        fail("README internal URLs", f"internal links in README: {sorted(set(internal))} -- remove them. "
             f"Intentionally FAIL (Vidit 2026-10-16): trivial to fix, and a reviewer bounce for it costs a revision round")
    else:
        ok("README internal URLs", "none")
    # Stale status text left by calibration loops ("not reached", "not calibrated", "RELEASE", ...) contradicts
    # the submitted bundle; commonmark d711592 shipped a 4/5,0/5,not-reached table and a "not calibrated" sentence.
    status = re.findall(r"(?i)(not calibrat\w*|not (?:yet )?ready to (?:push|submit)|DO NOT PUSH|WAITING-[A-Z-]+|"
                        r"out of (?:the )?band|outside the (?:required )?band)", text)
    status += re.findall(r"\b(RELEASE|NOT READY)\b", text)   # upper-case worker verdict words only
    if status:
        fail("README status freshness", f"stale/negative calibration status text: {sorted(set(status))} -- "
             f"rewrite Completion Rates / Model Analysis from the numbers for THIS commit")
    else:
        ok("README status freshness", "no 'not calibrated' / RELEASE / WAITING text")
    if re.search(r"(?i)not reached", text):
        warn("README status freshness", "'not reached' in README -- confirm the Completion Rates table reflects THIS commit")
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
    git_emails = SRC.author_emails()
    if emails and git_emails and not any(e in git_emails for e in emails):
        warn("task.toml author", f"author email {emails} not among commit authors {sorted(git_emails)[:3]}")
    return d


def check_configs(cfgs, fmt):
    if not cfgs:
        fail("config.json", "no tests/config.json found")
        return
    # Multi-turn: the task-level config must hold only repo/instance_id/base_commit (MT Reviewer Guide +
    # Task Quality Q&A). pact-broker 7324c8f was sent back for step-level patch/test_patch/F2P/P2P at the root.
    step_cfgs = [c for c in cfgs if c[0] != "task"]
    root = [c for c in cfgs if c[0] == "task"]
    if step_cfgs and root:
        try:
            rk = set(json.loads(SRC.read(root[0][1])).keys())
            extra = sorted(rk - {"repo", "instance_id", "base_commit"})
            if extra:
                fail("MT root config", f"root tests/config.json must hold only repo, instance_id, base_commit; "
                     f"move/remove: {extra}")
            else:
                ok("MT root config", "root tests/config.json holds only repo/instance_id/base_commit")
        except Exception as e:  # noqa: BLE001
            fail("MT root config", f"unreadable root tests/config.json: {e}")
    # Every graded id must be defined in the inline test_patch: TBR grades only test_patch, so ids whose
    # bodies live in an auxiliary file copied by test.sh are never created (typeprof 9490fd1 BAD_GRADING_WRONG).
    for label, p in step_cfgs:
        try:
            c = json.loads(SRC.read(p))
        except Exception:  # noqa: BLE001
            continue
        tp = c.get("test_patch") or ""
        ids = list(c.get("fail_to_pass") or [])  # pass_to_pass may name existing upstream tests
        missing = []
        for tid in ids:
            tok = re.split(r"::|\s|#|/|\.", str(tid).strip())[-1].strip("()[]")
            if len(tok) >= 8 and tok not in tp:
                missing.append(tok)
        if missing:
            fail(f"config {label} ids", f"{len(missing)} graded id(s) not defined in inline test_patch "
                 f"(TBR never creates them): {missing[:4]}")
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
    if any(p.startswith("steps/") for p in scripts):
        tests = [p for p in scripts if p.endswith("test.sh") and p.startswith("steps/")]
        traps = {p: has_exit_trap(SRC.read(p) or "") for p in tests}
        if len(set(traps.values())) > 1:
            warn("MT EXIT trap", f"EXIT trap present in some step test.sh but not others: {traps} "
                 f"(graded files leak into the next step — net-imap review)")


def has_exit_trap(script):
    for line in script.splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lexer.whitespace_split = True
            lexer.commenters = "#"
            tokens = list(lexer)
        except ValueError:
            continue
        boundaries = {";", "&&", "||", "|", "then", "do", "{"}
        for index, token in enumerate(tokens):
            if token != "trap" or (index and tokens[index - 1] not in boundaries):
                continue
            signals = []
            for candidate in tokens[index + 1:]:
                if candidate in boundaries:
                    break
                signals.append(candidate)
            if "EXIT" in signals or "0" in signals:
                return True
    return False


# ───────────────────────────── server checks ─────────────────────────────

def api_task(name):
    d = command_json(["codimango", "task", "show", name, "--json"])
    if isinstance(d, list):
        if len(d) != 1:
            raise RuntimeError(f"expected one task, got {len(d)}")
        d = d[0]
    if not isinstance(d, dict):
        raise RuntimeError(f"unexpected task payload type: {type(d).__name__}")
    return d.get("task", d)


def check_server(name, task_dir):
    global SERVER_FMT, SERVER_REVIEW_STATUS
    SERVER_REVIEW_STATUS = "unavailable"
    try:
        t = api_task(name)
    except CommandError as e:
        if e.kind == "not_found":
            fail("server", f"cannot read task from codimango: {str(e)[:120]}")
        else:
            SERVER_REVIEW_STATUS = None
            infra("server", str(e)[:160])
        return
    except Exception as e:  # noqa: BLE001
        SERVER_REVIEW_STATUS = None
        infra("server", str(e)[:160])
        return
    SERVER_FMT = t.get("format") or "?"
    SERVER_REVIEW_STATUS = t.get("reviewStatus") or "?"
    sha = str(t.get("commitSha") or "")
    vsha = str(t.get("validationCommitSha") or "")
    local = SRC.last_commit() if SRC is not None else None
    readme_only = False
    if local and len(local) == 40 and sha and local != sha and SRC is not None:
        # Vidit 2026-10-18: a README-only push after validation is expected (README refreshed
        # with server numbers); it needs no rerun, so it must not FAIL freshness.
        changed = SRC._git("diff", "--name-only", sha, local, "--", SRC.task)
        if changed is not None:
            files = [f for f in changed.splitlines() if f.strip()]
            readme_only = bool(files) and all(f == f"{SRC.task}/README.md" for f in files)
    if readme_only:
        ok("server freshness", f"server at {sha[:8]}; only README.md changed since (at {local[:8]}) — expected, no rerun needed")
    elif local and len(local) == 40 and sha and local != sha:
        fail("server freshness", f"server task is at {sha[:8]} but origin/main last touched this task at "
             f"{local[:8]} — stale import: run `codimango task rerun {name}` (free)")
    elif vsha and sha and vsha != sha:
        warn("server freshness", f"validation ran at {vsha[:8]} but task is at {sha[:8]}")
    elif local:
        ok("server freshness", f"server at {sha[:8]}")
    else:
        warn("server freshness", "not checked (run with --repo to compare the selected ref)")

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
    try:
        show = command_text(["codimango", "task", "show", name])
    except CommandError as e:
        infra("engine stages", str(e)[:160])
        show = ""
    stages = re.findall(r"-\s+([a-z\-]+):\s+([a-z_]+)\s+@", show)
    for st_name, st_val in stages:
        if st_val == "passed":
            ok(f"stage {st_name}", "passed")
        else:
            fail(f"stage {st_name}", f"{st_val} — reviewers block on red engine stages "
                 f"(go-zero-goctl: 'Eval GT errors are hard blocking')")
    if not stages:
        warn("engine stages", "no stage rows parsed from `codimango task show`; inspect manually")
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

    # fairness gate: non-blocking server-side, but reviewers send tasks back on it
    # (paperjs 0be72c8, pact b81cb46 — Vidit 2026-10-22)
    try:
        sj = json.loads(command_text(["codimango", "task", "show", name, "--json"]))
        found = False
        def _walk(o):
            nonlocal found
            if isinstance(o, dict):
                if o.get("name") == "multi-turn-post-runs" and (not sha or str(o.get("commitSha", "")) == sha):
                    found = True
                    crit = [f.get("title", "")[:110] for f in o.get("findings") or []
                            if f.get("severity") == "blocking"]
                    bad = [p.get("label") for p in o.get("policies") or [] if p.get("status") == "FAIL"]
                    if crit or bad:
                        fail("fairness gate", f"{bad or ''} {len(crit)} Critical finding(s): {crit} — "
                             "every flagged test must trace to the step wording or be dropped")
                    else:
                        ok("fairness gate", "no Critical findings")
                # a red signal (e.g. reward_hack_detector_gate) hides under a stage that reads "passed"
                # (pact 09e87f8)
                if o.get("name") == "configerable-signals" and (not sha or str(o.get("commitSha", "")) == sha):
                    red = [(p.get("label") or "?", p.get("status")) for p in o.get("policies") or []
                           if p.get("status") in ("FAIL", "ERROR")]
                    if red:
                        fail("configurable signals", f"{red} — fix each, or write an override justification")
                    else:
                        ok("configurable signals", "no FAIL/ERROR policy")
                for v in o.values():
                    _walk(v)
            elif isinstance(o, list):
                for v in o:
                    _walk(v)
        _walk(sj)
        if not found:
            warn("fairness gate", "no multi-turn-post-runs result at this commit; inspect manually")
    except Exception as e:  # noqa: BLE001
        infra("fairness gate", str(e)[:160])

    # agentic verdict
    try:
        rv = command_text(["codimango", "job", "review", name])
    except CommandError as e:
        if "has not run" not in str(e):
            infra("agentic verdict", str(e)[:160])
        rv = ""
    m = re.search(r"\*\*Verdict:\*\*\s*([A-Z_]+)", rv)
    if not m:
        warn("agentic verdict", "no agentic review found at this commit")
    elif m.group(1) != "GOOD":
        fail("agentic verdict", f"{m.group(1)} — fix the named rubric items or justify each")
    else:
        ok("agentic verdict", "GOOD")

    check_trials(name, sha)
    check_failure_legitimacy(name, sha, failed_trial_count=LAST_FAILED.get(name))

    # human review history
    try:
        hr = command_text(["codimango", "task", "reviews", name, "--full"])
    except CommandError as e:
        infra("human review", str(e)[:160])
        return
    decs = re.findall(r"REVIEW by [^\n]*@ ([0-9\- :]+) UTC.*?\*\*Decision:\*\*\s*([^\n]+)", hr, re.S)
    if decs:
        d0 = decs[0]
        lvl = warn if not d0[1].lower().startswith("accept") else ok
        lvl("human review", f"latest decision {d0[1].strip()} @ {d0[0][:16]} — make sure every point is addressed")


LAST_FAILED = {}


def check_trials(name, sha):
    try:
        jl = command_text(["codimango", "job", "list", name])
    except CommandError as e:
        infra("trials", str(e)[:160])
        return
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
        try:
            d = command_json(["codimango", "trial", "list", jid, "--json"])
        except (CommandError, RuntimeError) as e:
            infra("trials", str(e)[:160])
            return
        if isinstance(d, list):
            trials = d
        elif isinstance(d, dict):
            trials = d.get("trials", d.get("items", []))
        else:
            infra("trials", f"unexpected trial payload type: {type(d).__name__}")
            return
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
    LAST_FAILED[name] = failed_trials
    if failed_trials >= 2 and fail_tests:
        top, n = fail_tests.most_common(1)[0]
        if n / failed_trials >= 0.8:
            warn("single-test dominance", f"{n}/{failed_trials} failed trials fail `{top}` — that test carries "
                 f"the difficulty: prove it is STATED in instruction.md and fair (crossplane/spire-workload/redb)")


# ───────────────────────────── main ─────────────────────────────

LEGIT = {"FAIL_REASONING", "PASSED", "PASS"}


def check_failure_legitimacy(name, sha, failed_trial_count=None):
    """Are the FAILURES real model mistakes, or grader/infra false negatives? (gson stale report,
    jsondiffpatch vite cache, isogit fixture: all looked like ordinary 0-reward trials to the census.)
    Source: the server's agentic full-task review, which reads each attempt's trajectory and verifier
    output and classifies it (FAIL_REASONING = legit miss; GRADING_FAILURE / INFRA / etc. = not)."""
    if not sha:
        return
    try:
        d = command_json(["codimango", "job", "review", name, "--commit", sha, "--json"])
    except (CommandError, RuntimeError) as e:
        infra("failure legitimacy", str(e)[:160])
        return
    attempts = ((d or {}).get("review") or {}).get("attemptResults") or []
    if not attempts:
        warn("failure legitimacy", f"no per-attempt classification in the agentic review at {sha[:8]} — "
             "read failing trajectories by hand (trial artifacts: verifier/test-stdout.txt) before submitting")
        return
    bad = [a for a in attempts if str(a.get("result", "")).upper() not in LEGIT]
    fails = [a for a in attempts if str(a.get("result", "")).upper() == "FAIL_REASONING"]
    if bad:
        ex = "; ".join(f"{a.get('attemptId','?').split('/')[-1]}={a.get('result')}: "
                       f"{(a.get('explanation') or '')[:120]}" for a in bad[:3])
        fail("failure legitimacy", f"{len(bad)}/{len(attempts)} attempt(s) are NOT legitimate model failures "
             f"({ex}). Fix the grader/harness (C2) before submitting; a false negative is not difficulty.")
        return
    note = ""
    if failed_trial_count is not None and len(fails) < failed_trial_count:
        note = (f" — but the review classified only {len(fails)} of {failed_trial_count} failed trials; "
                "replay or read the rest (verifier/test-stdout.txt) before claiming every failure is legit")
        warn("failure legitimacy", f"{len(fails)} FAIL_REASONING, 0 grader/infra{note}")
    else:
        ok("failure legitimacy", f"all {len(fails)} classified failures are FAIL_REASONING (legit model misses), "
           f"0 grader/infra, from {len(attempts)} reviewed attempts")


def check_ref_freshness(repo, ref):
    """Check a remote-tracking ref without updating it."""
    if ref != "origin/main":
        return
    local = sh(["git", "-C", repo, "rev-parse", ref]).strip()
    remote = sh(["git", "-C", repo, "remote", "get-url", "origin"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", local) or not remote or remote.startswith("__ERROR__"):
        warn("git ref freshness", f"could not resolve {ref} and origin; local checks may be stale")
        return
    advertised = sh(["git", "ls-remote", remote, "refs/heads/main"]).split()
    if not advertised or not re.fullmatch(r"[0-9a-f]{40}", advertised[0]):
        warn("git ref freshness", "could not read origin/main without mutating refs; local checks may be stale")
    elif advertised[0] != local:
        fail("git ref freshness", f"{ref} is stale ({local[:8]} vs remote {advertised[0][:8]}); run git fetch")
    else:
        ok("git ref freshness", f"{ref} is current at {local[:8]}")


def main():
    global SERVER_REVIEW_STATUS
    results.clear()
    infra_failures.clear()
    SERVER_REVIEW_STATUS = None
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task")
    ap.add_argument("--repo", default=os.environ.get("SWEBENCH_REPO"),
                    help="task-repository checkout (or set SWEBENCH_REPO); required except with --server-only")
    ap.add_argument("--local-only", action="store_true")
    ap.add_argument("--server-only", action="store_true")
    ap.add_argument("--ref", default="origin/main",
                    help="git ref to read task files from (default origin/main); use --worktree for uncommitted edits")
    ap.add_argument("--worktree", action="store_true", help="read the working tree instead of a git ref")
    ap.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    a = ap.parse_args()
    if a.local_only and a.server_only:
        print("--local-only and --server-only are mutually exclusive", file=sys.stderr)
        return 2
    if not a.server_only and not a.repo:
        print("--repo DIR (or SWEBENCH_REPO) is required for local checks", file=sys.stderr)
        return 2
    repo = os.path.abspath(a.repo) if a.repo else None
    task_dir = os.path.join(repo, a.task) if repo else None
    global SRC
    SRC = Source(repo, a.task, None if a.worktree else a.ref) if repo else None
    if not a.server_only:
        inside = sh(["git", "-C", repo, "rev-parse", "--is-inside-work-tree"]).strip() \
            if repo and os.path.isdir(repo) else ""
        if inside != "true":
            print("--repo must name a Git checkout", file=sys.stderr)
            return 2
        if not SRC.task_exists():
            where = "the worktree" if a.worktree else a.ref
            print(f"task {a.task!r} not found in {where}", file=sys.stderr)
            return 2
        if not a.worktree:
            check_ref_freshness(repo, a.ref)
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
    use_color = a.color == "always" or (a.color == "auto" and sys.stdout.isatty())
    color = {"FAIL": "\033[31m", "WARN": "\033[33m", "PASS": "\033[32m"} if use_color else {}
    reset = "\033[0m" if use_color else ""
    print(f"\npresubmit: {a.task}  (format={fmt})")
    for lvl, check, msg in sorted(results, key=lambda r: order[r[0]]):
        print(f"  {color.get(lvl, '')}{lvl}{reset}  {check}: {msg}")
    n = collections.Counter(r[0] for r in results)
    print(f"\n  {n['FAIL']} FAIL · {n['WARN']} WARN · {n['PASS']} PASS")
    if SERVER_REVIEW_STATUS is not None:
        print(f"  Review status: {SERVER_REVIEW_STATUS}")
    print("  Not covered (judgement/container): forge attempts, per-assertion stated-check, golden vs "
          "real standard, collision/idempotency replay, MT step-dependency replay, public-issue sweep.")
    return 2 if infra_failures else (1 if n["FAIL"] else 0)


if __name__ == "__main__":
    sys.exit(main())

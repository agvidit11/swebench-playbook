#!/usr/bin/env python3
"""failure-audit.py — HARD presubmit check: every failed model trial must be a genuine reasoning failure.

Vidit 2026-10-21 (cancancan returned: 4/5 Avocado trials were timeouts that every gate scored as fails).

Usage:
  failure-audit.py <task> [--commit SHA] [--repo DIR] [--judge] [--out DIR]

For the server-validated commit (or --commit), every Avocado / GPT / Opus trial that failed or ended with
any exception is pulled (result.json, exception, verifier output, agent/trajectory.json) and classified:

  TIMEOUT       agent hit its time cap (AgentTimeoutError or timed_out) — pass OR fail, never genuine
  INFRA         any other exception / status=error / missing verifier reward
  GRADER-ABORT  verifier reports a grader failure or missing configured ids (hidden suite aborted) — the
                remaining cases were never observed; needs a human look before it can count
  INCOMPLETE    trajectory ends without the agent concluding (no final message) and no exception recorded
  CANDIDATE     agent finished normally and specific graded tests failed -> genuine only after --judge

With --judge (requires --repo, a checkout of the task repo), each CANDIDATE gets an evidence bundle
(instruction text, failing test ids + messages, failing test source, the agent's last messages and its final
diff file list) and a sandboxed Codex judge decides GENUINE (misses a stated or clearly inferable requirement)
vs UNFAIR-TEST (asserts something the instruction does not state) vs HARNESS.

Exit 0 only if no TIMEOUT / INFRA / GRADER-ABORT / INCOMPLETE trials exist and (with --judge) every CANDIDATE is
GENUINE. Anything else blocks submit.
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

MODEL_STAGES = ("metacode", "codex", "opus", "gpt", "claude")


def sh(*args):
    return subprocess.run(list(args), capture_output=True, text=True).stdout


def artifact(tid, key):
    out = sh("codimango", "trial", "artifacts", "--key", key, tid)
    i = min([p for p in (out.find("{"), out.find("[")) if p >= 0], default=-1)
    return out, (out[i:] if i >= 0 else "")


def server_commit(task):
    m = re.search(r"Commit SHA:\s+(\w+)", sh("codimango", "task", "show", task))
    return m.group(1) if m else ""


def trials_at(task, commit8):
    rows = []
    jobs = sh("codimango", "job", "list", task)
    for line in jobs.splitlines():
        if f"commit={commit8}" not in line or ("[current]" in jobs and "[current]" not in line):
            continue  # only the current validation generation counts
        jid = line.split()[0]
        for tl in sh("codimango", "trial", "list", jid).splitlines():
            st = re.search(r"stage=(\S+)", tl)
            if not st or not any(s in st.group(1) for s in MODEL_STAGES):
                continue
            rows.append({
                "job": jid, "trial": tl.split()[0], "stage": st.group(1),
                "status": (re.search(r"status=(\S+)", tl) or [None, ""])[1] if re.search(r"status=(\S+)", tl) else "",
                "reward": (re.search(r"reward=(\S+)", tl).group(1) if re.search(r"reward=(\S+)", tl) else "?"),
                "exc": (re.search(r"exc=(\S+)", tl).group(1) if re.search(r"exc=(\S+)", tl) else ""),
                "dur": (re.search(r"dur=(\S+)", tl).group(1) if re.search(r"dur=(\S+)", tl) else ""),
            })
    return rows


def failing_tests(text):
    names = set()
    for m in re.finditer(r"(?m)^\{", text):
        if True:
            try:
                d, _ = json.JSONDecoder().raw_decode(text[m.start():])
                tests = d.get("tests") or d.get("results", {}).get("tests")
                if isinstance(tests, dict):
                    names |= {k.split("::")[-1] for k, v in tests.items() if str(v.get("status", "")).upper() != "PASSED"}
                elif isinstance(tests, list):
                    names |= {t.get("name", "").split("::")[-1] for t in tests if str(t.get("status", "")).lower() not in ("passed", "skipped")}
            except Exception:
                pass
    names |= set(x.split("::")[-1] for x in re.findall(r"FAILED (\S+)", text))
    for grp in re.findall(r"non-passing configured ids: \[([^\]]*)\]", text):
        names |= {x.strip().strip("'\"").split("::")[-1] for x in grp.split(",") if x.strip()}
    if not names and "{" in text:
        try:
            d = json.loads(text[text.index("{"):])
            tests = d.get("tests") or d.get("results", {}).get("tests")
            if isinstance(tests, dict):
                names = {k for k, v in tests.items() if str(v.get("status", "")).upper() != "PASSED"}
            elif isinstance(tests, list):
                names = {t.get("name", "") for t in tests if str(t.get("status", "")).lower() not in ("passed", "skipped")}
        except Exception:
            pass
    return sorted(names)


def classify(t):
    tid = t["trial"]
    ev = {"trial": tid, "stage": t["stage"], "reward": t["reward"], "exc": t["exc"], "dur": t["dur"]}
    _, rj = artifact(tid, "result.json")
    try:
        res = json.loads(rj) if rj else {}
    except Exception:
        res = {}
    exc = (res.get("exception_info") or {}) if isinstance(res, dict) else {}
    timed_out = False
    try:
        md = res.get("agent_result", {}).get("metadata", {}) or {}
        timed_out = any(isinstance(v, dict) and v.get("timed_out") for v in md.values())
    except Exception:
        pass
    keys = sh("codimango", "trial", "artifacts", tid)
    vkeys = re.findall(r"(\S*verifier/(?:output\.json|ctrf\.json|test-stdout\.txt|run-script-stdout\.txt))", keys)
    vkey = vkeys[0] if vkeys else ""
    vtext = "\n".join(artifact(tid, k)[0] for k in vkeys)
    stderr_key = next(iter(re.findall(r"(\S*verifier/run-script-stderr\.txt)", keys)), "")
    stderr = artifact(tid, stderr_key)[0] if stderr_key else ""
    ev["failing_tests"] = failing_tests(vtext)[:40]
    traj_key = next(iter(re.findall(r"(\S*agent/trajectory\.json)", keys)), "")
    last_msgs, concluded, nsteps = [], None, 0
    if traj_key:
        try:
            d = json.loads(artifact(tid, traj_key)[1])
            steps = [s for s in d.get("steps", []) if s.get("source") == "agent"]
            nsteps = len(steps)
            last_msgs = [(s.get("message") or s.get("reasoning_content") or "")[:600] for s in steps[-3:]]
            concluded = bool(steps) and bool((steps[-1].get("message") or "").strip()) and not steps[-1].get("tool_calls")
        except Exception:
            pass
    if not traj_key:
        nsteps = res.get("n_tool_calls") or 0 if isinstance(res, dict) else 0
        concluded = None
        last_msgs = ["(no trajectory.json exported; agent made %s tool calls per result.json)" % nsteps]
    ev.update({"agent_steps": nsteps, "last_agent_messages": last_msgs, "concluded": concluded,
               "exception_type": exc.get("exception_type", ""), "exception_message": (exc.get("exception_message") or "")[:300]})
    blob = vtext + "\n" + stderr
    if t["exc"].startswith("AgentTimeout") or exc.get("exception_type", "").startswith("AgentTimeout") or timed_out:
        ev["class"] = "TIMEOUT"
    elif t["exc"] or exc.get("exception_type") or t["status"] == "error":
        ev["class"] = "INFRA"
    elif not vkey or re.search(r"missing configured id|could not be installed", blob) or (not ev["failing_tests"] and not t["reward"].startswith("1")):
        ev["class"] = "GRADER-ABORT"
    elif concluded is False:
        ev["class"] = "INCOMPLETE"
    elif t["reward"].startswith("1"):
        ev["class"] = "PASS"
    else:
        ev["class"] = "CANDIDATE"
    return ev


def judge(task, repo, cands, out):
    bundle = out / "judge"
    bundle.mkdir(parents=True, exist_ok=True)
    tdir = Path(repo) / task
    instr = ""
    for p in sorted(tdir.glob("**/instruction.md")):
        instr += f"\n===== {p.relative_to(tdir)} =====\n" + p.read_text()
    (bundle / "instructions.txt").write_text(instr)
    cfgs = ""
    for p in sorted(tdir.glob("**/tests/config.json")):
        try:
            d = json.loads(p.read_text())
            cfgs += f"\n===== {p.relative_to(tdir)} test_patch =====\n" + d.get("test_patch", "")[:200000]
        except Exception:
            pass
    (bundle / "test_patches.txt").write_text(cfgs)
    (bundle / "candidates.json").write_text(json.dumps(cands, indent=1))
    prompt = f"""You are the genuine-failure judge for SWE-bench task {task}. Files in this directory:
instructions.txt (every step's instruction), test_patches.txt (hidden tests), candidates.json (failed model trials:
failing test ids, the agent's last messages, step count).
For EACH trial in candidates.json decide one verdict:
- GENUINE: the agent finished, and every failing test checks behaviour the instruction states or that a careful
  engineer would clearly infer from it; the agent's code simply got it wrong.
- UNFAIR-TEST: at least one failing test asserts behaviour the instruction does not state and that is not clearly
  inferable (cite the test and the missing sentence).
- HARNESS: the failure looks caused by the grader/environment (crash, missing results, unrelated breakage).
Write judge.json: a list of {{"trial":..., "verdict":..., "reason": one or two sentences citing test names and the
instruction sentence}}. Then print a one-line summary per trial."""
    (bundle / "PROMPT.txt").write_text(prompt)
    subprocess.run(["codex", "exec", "--full-auto", "--skip-git-repo-check", "-C", str(bundle), prompt],
                   stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3600)
    try:
        return json.loads((bundle / "judge.json").read_text())
    except Exception:
        return [{"trial": c["trial"], "verdict": "NO-JUDGE", "reason": "judge did not produce judge.json"} for c in cands]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task"); ap.add_argument("--commit"); ap.add_argument("--repo")
    ap.add_argument("--judge", action="store_true"); ap.add_argument("--out")
    a = ap.parse_args()
    commit = a.commit or server_commit(a.task)
    out = Path(a.out or f"/home/agvidit/scratch/failure-audit/{a.task}-{commit[:7]}")
    out.mkdir(parents=True, exist_ok=True)
    trials = trials_at(a.task, commit[:8])
    audited = [classify(t) for t in trials if not t["reward"].startswith("1") or t["exc"] or t["status"] == "error"]
    (out / "trials.json").write_text(json.dumps(audited, indent=1))
    blocking = [e for e in audited if e["class"] in ("TIMEOUT", "INFRA", "GRADER-ABORT", "INCOMPLETE")]
    cands = [e for e in audited if e["class"] == "CANDIDATE"]
    verdicts = []
    if a.judge and cands:
        if not a.repo:
            sys.exit("--judge needs --repo")
        verdicts = judge(a.task, a.repo, cands, out)
    bad_j = [v for v in verdicts if v.get("verdict") != "GENUINE"]
    print(f"{'FAIL' if blocking or bad_j or (cands and not a.judge) else 'PASS'}  {a.task}  commit {commit[:7]}  "
          f"model trials {len(trials)}, audited {len(audited)}")
    for e in audited:
        print(f"   {e['class']:12} {e['trial']} {e['stage']:9} reward={e['reward']} dur={e['dur']} {e['exc'] or e['exception_type']}"
              f"{'  fails: ' + ', '.join(e['failing_tests'][:4]) if e['failing_tests'] else ''}")
    for v in verdicts:
        print(f"   JUDGE {v.get('verdict'):12} {v.get('trial')}  {v.get('reason','')[:300]}")
    if cands and not a.judge:
        print("   NOTE: CANDIDATE failures are not yet judged genuine — re-run with --judge --repo <checkout>")
    print(f"   evidence: {out}")
    sys.exit(1 if blocking or bad_j or (cands and not a.judge) else 0)


if __name__ == "__main__":
    main()

"""check run (wraps the pre-submit gate, unchanged) and agent-session reviews, both bound to a commit."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from . import coord, gitutil

VERDICTS = ("ready", "changes", "comment")


def task_head(cfg, task: str) -> str | None:
    """Last commit touching <task>/ on the fetched branch (falls back to origin/<branch>)."""
    for repo in cfg.repositories:
        path = Path(repo.path).expanduser()
        for ref in (f"refs/workboard/{repo.branch}", f"origin/{repo.branch}"):
            p = gitutil.run(path, "log", "-1", "--format=%H", ref, "--", f"{task}/", timeout=20)
            if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", p.stdout.strip()):
                return p.stdout.strip()
    return None


def parse_summary(text: str, pattern: str) -> dict | None:
    m = None
    for m in re.finditer(pattern, text):
        pass                                    # last summary line wins
    if not m:
        return None
    fail, warn, ok = (int(x) for x in m.groups()[:3])
    return {"fail": fail, "warn": warn, "pass": ok}


def run_check(cfg, task: str, *, state_dir, actor=None, runner=subprocess.run, out=sys.stdout, err=sys.stderr) -> int:
    """Run the configured gate, pass its output and exit code through, then record the result."""
    if not cfg.checks.presubmit:
        print("check run: set [checks] presubmit in your config", file=err)
        return 2
    argv = [a.replace("{task}", task) for a in cfg.checks.presubmit]
    commit = task_head(cfg, task)
    try:
        proc = runner(argv, capture_output=True, text=True, timeout=cfg.checks.timeout_seconds)
    except subprocess.TimeoutExpired:
        print(f"check run: gate timed out after {cfg.checks.timeout_seconds}s", file=err)
        return 124
    except OSError as exc:
        print(f"check run: cannot start gate: {exc}", file=err)
        return 127
    out.write(proc.stdout or "")
    err.write(proc.stderr or "")
    counts = parse_summary((proc.stdout or "") + (proc.stderr or ""), cfg.checks.summary_regex)
    payload = dict(counts or {}, exit=proc.returncode, parsed=bool(counts))
    actor = actor or coord.actor_for(cfg)
    if not coord.record(state_dir, "check", task, actor, payload, commit=commit):
        print("check run: warning: result could not be recorded in the ledger", file=err)
    elif not commit:
        print("check run: warning: task commit unknown; result recorded without a commit (shows as stale)", file=err)
    return proc.returncode


def add_review(cfg, task: str, verdict: str, confidence: int | None, note: str, *, state_dir, actor=None) -> tuple[bool, str]:
    if verdict not in VERDICTS:
        return False, f"verdict must be one of {', '.join(VERDICTS)}"
    if confidence is not None and not 1 <= confidence <= 5:
        return False, "confidence must be 1-5"
    commit = task_head(cfg, task)
    if not commit:
        return False, "cannot find the task's current commit; a review must be bound to one"
    actor = actor or coord.actor_for(cfg)
    payload = {"verdict": verdict, "note": note[:500]}
    if confidence is not None:
        payload["confidence"] = confidence
    if not coord.record(state_dir, "review", task, actor, payload, commit=commit):
        return False, "review could not be recorded"
    return True, commit

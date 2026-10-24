"""check run (wraps the pre-submit gate, unchanged) and agent-session reviews, both bound to a commit."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from . import coord, gitutil

VERDICTS = ("ready", "changes", "comment")


def task_head(cfg, task: str) -> str | None:
    """Commit only; see task_head_repo for (repo id, commit)."""
    found = task_head_repo(cfg, task)
    return found[1] if found else None


def task_head_repo(cfg, task: str) -> tuple[str, str] | None:
    """Last commit touching <task>/ on the fetched branch (falls back to origin/<branch>)."""
    for repo in cfg.repositories:
        path = Path(repo.path).expanduser()
        for ref in (f"refs/workboard/{repo.branch}", f"origin/{repo.branch}"):
            p = gitutil.run(path, "log", "-1", "--format=%H", ref, "--", f"{task}/", timeout=20)
            if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", p.stdout.strip()):
                return repo.id, p.stdout.strip()
    return None


def parse_summary(text: str, pattern: str) -> dict | None:
    try:
        matches = list(re.finditer(pattern, text))
    except re.error:
        return None
    if not matches:
        return None
    try:
        fail, warn, ok = (int(x) for x in matches[-1].groups()[:3])   # last summary line wins
    except (TypeError, ValueError):
        return None
    return {"fail": fail, "warn": warn, "pass": ok}


TAIL_BYTES = 65536


class BoundedTail:
    """Keeps only the last `limit` characters written to it."""

    def __init__(self, limit: int = TAIL_BYTES):
        self.limit, self.parts, self.size = limit, [], 0

    def add(self, text: str) -> None:
        self.parts.append(text)
        self.size += len(text)
        while self.size > self.limit and len(self.parts) > 1:
            self.size -= len(self.parts.pop(0))
        if self.size > self.limit:                 # one huge chunk: trim it
            self.parts[0] = self.parts[0][-self.limit:]
            self.size = len(self.parts[0])

    def text(self) -> str:
        return "".join(self.parts)


def _stream(argv, timeout, out, err):
    """Run argv, copying stdout/stderr to out/err as they arrive (one incremental UTF-8 decoder per stream).
    Returns (exit code, bounded stdout tail); exit 124 on timeout (whole process group killed)."""
    import codecs
    import os
    import signal
    import threading
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_tail = BoundedTail()

    def pump(src, dest, tail):
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        for chunk in iter(lambda: src.read1(4096), b""):
            text = decoder.decode(chunk)
            if text:
                dest.write(text)
                dest.flush()
                if tail is not None:
                    tail.add(text)
        rest = decoder.decode(b"", final=True)
        if rest:
            dest.write(rest)
            dest.flush()
            if tail is not None:
                tail.add(rest)
        src.close()

    threads = [threading.Thread(target=pump, args=(proc.stdout, out, stdout_tail), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, err, None), daemon=True)]
    for t in threads:
        t.start()
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        code = 124
    for t in threads:
        t.join(5)
    return code, stdout_tail.text()


def run_check(cfg, task: str, *, state_dir, actor=None, out=sys.stdout, err=sys.stderr) -> int:
    """Run the configured gate with live output, keep its exit code, then record the result.
    Anything other than a clean, parsed run is recorded as failing (fail >= 1)."""
    if not cfg.checks.presubmit:
        print("check run: set [checks] presubmit in your config", file=err)
        return 2
    argv = [a.replace("{task}", task) for a in cfg.checks.presubmit]
    commit = task_head(cfg, task)
    note = ""
    try:
        code, tail = _stream(argv, cfg.checks.timeout_seconds, out, err)
        if code == 124:
            note = f"timed out after {cfg.checks.timeout_seconds}s"
    except OSError as exc:
        code, tail, note = 127, "", f"cannot start gate: {exc}"
    if note:
        print(f"check run: {note}", file=err)
    counts = parse_summary(tail, cfg.checks.summary_regex) if not note else None
    payload = dict(counts or {"pass": 0, "warn": 0, "fail": 0}, exit=code, parsed=bool(counts))
    if note:
        payload["note"] = note
    if code != 0 or not counts:
        payload["fail"] = max(1, payload["fail"])      # never a green check without a clean, parsed run
    actor = actor or coord.actor_for(cfg)
    if not coord.record(state_dir, "check", task, actor, payload, commit=commit):
        print("check run: warning: result could not be recorded in the ledger", file=err)
    elif not commit:
        print("check run: warning: task commit unknown; result recorded without a commit (shows as stale)", file=err)
    return code


def record_check(cfg, task: str, *, passed: int, warn: int, fail: int, summary: str = "", state_dir,
                 actor=None, commit: str | None = None, source: str = "manual") -> tuple[bool, str]:
    """Record a presubmit result run elsewhere (another session, a batch run). Bound to the task's current commit."""
    commit = commit or task_head(cfg, task)
    payload = {"pass": passed, "warn": warn, "fail": max(fail, 0), "parsed": True, "exit": 1 if fail else 0,
               "summary": summary[:300], "imported_from": source}
    actor = actor or coord.actor_for(cfg)
    if not coord.record(state_dir, "check", task, actor, payload, commit=commit):
        return False, "could not queue the result"
    return True, commit or "no commit (shows as stale)"


def import_dir(cfg, directory: Path, *, state_dir, known: set[str] | None = None, actor=None) -> list[tuple[str, str]]:
    """Import presubmit outputs: one `<task>.txt` per task containing the gate's summary line."""
    out = []
    for f in sorted(Path(directory).expanduser().glob("*.txt")):
        task = f.stem
        if known is not None and task not in known:
            out.append((task, "skipped: unknown task"))
            continue
        text = f.read_text(errors="replace")
        counts = parse_summary(text, cfg.checks.summary_regex)
        if not counts:
            out.append((task, "skipped: no summary line"))
            continue
        fails = [l.strip() for l in text.splitlines() if "FAIL" in l and "·" not in l][:3]
        ok, detail = record_check(cfg, task, passed=counts["pass"], warn=counts["warn"], fail=counts["fail"],
                                  summary="; ".join(fails), state_dir=state_dir, actor=actor, source=f"import {f.name}")
        out.append((task, f"P{counts['pass']} W{counts['warn']} F{counts['fail']}" if ok else detail))
    return out


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

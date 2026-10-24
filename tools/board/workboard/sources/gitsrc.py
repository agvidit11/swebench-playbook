"""Git source: per task directory, the last commit touching it and all its commit times.

Fetches the configured branch into a private ref (refs/workboard/<branch>) so the user's checkout is never
modified; on fetch failure it falls back to the last fetched ref and reports SYNC_FAILED.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .. import gitutil
from ..model import FetchResult, Finding, Observation, SourceHealth

NAME = "git"


class GitSource:
    name = NAME

    def __init__(self, cfg, *, since_days: int = 200, timeout: float = 90):
        self.cfg, self.since_days, self.timeout = cfg, since_days, timeout

    def fetch(self, *, since=None, timeout_seconds=None) -> FetchResult:
        obs, findings, ok, details = [], [], True, []
        now = datetime.now(timezone.utc)
        for repo in self.cfg.repositories:
            path = Path(repo.path).expanduser()
            ref = f"refs/workboard/{repo.branch}"
            if repo.remote_url:
                p = gitutil.run(path, "fetch", "-q", repo.remote_url, f"+{repo.branch}:{ref}", timeout=timeout_seconds or self.timeout)
                if p.returncode != 0:
                    ok = False
                    details.append(f"{repo.id}: fetch failed ({gitutil.err(p)})")
                    findings.append(Finding("SYNC_FAILED", "warn", f"git fetch of {repo.id} failed: {gitutil.err(p)}",
                                            f"check access to {repo.id}; showing last fetched commits"))
            if gitutil.run(path, "rev-parse", "-q", "--verify", ref).returncode != 0:
                ref = f"origin/{repo.branch}"     # never fetched privately yet
            log = gitutil.run(path, "log", ref, f"--since={self.since_days}.days", "--format=@%H %cI", "--name-only",
                              timeout=self.timeout)
            if log.returncode != 0:
                ok = False
                details.append(f"{repo.id}: log failed ({gitutil.err(log)})")
                continue
            per_task: dict[str, list[tuple[str, str]]] = {}
            sha = when = None
            for line in log.stdout.splitlines():
                if line.startswith("@"):
                    sha, when = line[1:].split(" ", 1)
                    seen_in_commit = set()
                elif line and "/" in line and sha:
                    task = line.split("/", 1)[0]
                    if task.startswith(".") or task in seen_in_commit:
                        continue
                    seen_in_commit.add(task)
                    per_task.setdefault(task, []).append((sha, when))
            for task, commits in per_task.items():   # log is newest first
                fields = {
                    "git.task_head": commits[0][0],
                    "git.task_head_time": commits[0][1],
                    "git.commit_times": [w for _, w in commits],
                    "git.repo": repo.id,
                }
                obs.append(Observation(NAME, task, now, fields, {k: "authoritative" for k in fields}))
        health = SourceHealth(NAME, ok, now, 900, "; ".join(details) or "ok")
        return FetchResult(obs, health, findings)

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

    def __init__(self, cfg, *, since_days: int | None = None, timeout: float = 90, fetch_remote: bool = True):
        self.cfg, self.since_days, self.timeout, self.fetch_remote = cfg, since_days, timeout, fetch_remote

    def fetch(self, *, since=None, timeout_seconds=None) -> FetchResult:
        obs, findings, ok, details = [], [], True, []
        now = datetime.now(timezone.utc)
        timeout = timeout_seconds or self.timeout
        for repo in self.cfg.repositories:
            path = Path(repo.path).expanduser()
            ref = f"refs/workboard/{repo.branch}"
            if repo.remote_url and self.fetch_remote:
                p = gitutil.run(path, "fetch", "-q", repo.remote_url, f"+{repo.branch}:{ref}", timeout=timeout)
                if p.returncode != 0:
                    ok = False
                    details.append(f"{repo.id}: fetch failed ({gitutil.err(p)})")
                    findings.append(Finding("SYNC_FAILED", "warn", f"git fetch of {repo.id} failed: {gitutil.err(p)}",
                                            f"check access to {repo.id}; showing last fetched commits"))
            if gitutil.run(path, "rev-parse", "-q", "--verify", ref).returncode != 0:
                ref = f"origin/{repo.branch}"     # never fetched privately yet
            window = [f"--since={self.since_days}.days"] if self.since_days else []
            log = gitutil.run(path, "log", ref, *window, "--format=@%H %cI", "--name-only", timeout=timeout)
            if log.returncode != 0:
                ok = False
                details.append(f"{repo.id}: log failed ({gitutil.err(log)})")
                continue
            per_task: dict[str, list[tuple[str, str]]] = {}
            time_by_sha: dict[str, str] = {}
            sha = when = None
            for line in log.stdout.splitlines():
                if line.startswith("@"):
                    sha, when = line[1:].split(" ", 1)
                    time_by_sha[sha] = when
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
            # repo-level map so the projection can compare a task head with the server's (repo-wide) commit
            obs.append(Observation(NAME, f"__repo__:{repo.id}", now, {"git.commit_time_by_sha": time_by_sha},
                                   {"git.commit_time_by_sha": "authoritative"}))
        health = SourceHealth(NAME, ok, now, 900, "; ".join(details) or "ok")
        return FetchResult(obs, health, findings)


def changed_files(cfg, repo_id: str, task: str, old: str, new: str, timeout: float = 20) -> list[str] | None:
    """Files under <task>/ that differ between two commits; None if git can't tell (e.g. commit unknown)."""
    repo = next((r for r in cfg.repositories if r.id == repo_id), None)
    if not repo:
        return None
    p = gitutil.run(Path(repo.path).expanduser(), "diff", "--name-only", old, new, "--", f"{task}/", timeout=timeout)
    if p.returncode != 0:
        return None
    return [l for l in p.stdout.splitlines() if l]

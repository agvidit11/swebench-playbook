"""Codimango adapter: the only code that calls the codimango CLI.

Contract (DESIGN §4): argv-based subprocess, timeout, checked exit status, captured stderr, envelope
validation, atomic last-known-good cache, prior good cache kept on any failure. Renderers and hooks never
call codimango directly.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ..model import FetchResult, Finding, Observation, SourceHealth

NAME = "codimango"
CACHE_FILE = "codimango-last-good.json"
# Task fields kept (camelCase -> snake). Everything else (report prose, metadata blobs) is dropped.
KEEP = {
    "id": "id", "status": "status", "validationStatus": "validation_status", "reviewedAt": "reviewed_at",
    "enteredPoolAt": "entered_pool_at", "createdAt": "created_at", "archivedAt": "archived_at",
    "commitSha": "commit_sha", "headCommitSha": "head_commit_sha", "validationCommitSha": "validation_commit_sha",
    "trackAssignment": "track", "format": "format", "sourceRepo": "source_repo", "reviewStatus": "review_status",
    "tbdReviewStatus": "tbr_status", "reviewerName": "reviewer", "updatedAt": "updated_at",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _snake_validation(details) -> list:
    out = []
    for d in details or []:
        if isinstance(d, dict):
            out.append({"name": str(d.get("name", ""))[:80], "status": str(d.get("status", ""))[:20]})
    return out


def normalise(task: dict, *, archived: bool) -> dict:
    row = {snake: task.get(camel) for camel, snake in KEEP.items()}
    row["name"] = task.get("name")
    row["validation"] = _snake_validation(task.get("validationDetails"))
    if archived:
        row["status_before_archive"] = row["status"]
        row["status"] = "archived"
    return row


def _parse_envelope(text: str) -> dict:
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        raise ValueError("no JSON in output")
    data, _ = json.JSONDecoder().raw_decode(text[start:])
    if isinstance(data, list):        # tolerate an older bare-list shape
        data = {"tasks": data, "totalExact": True}
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise ValueError("unexpected envelope (no tasks array)")
    return data


class CodimangoSource:
    name = NAME

    def __init__(self, cfg, *, runner=subprocess.run, cache_dir: Path | None = None):
        self.cfg = cfg
        self.runner = runner
        self.cache_dir = Path(cache_dir or os.environ.get("WORKBOARD_CACHE", "~/.cache/workboard")).expanduser()

    # -- cache -----------------------------------------------------------------------------------
    def _cache_path(self) -> Path:
        return self.cache_dir / CACHE_FILE

    def _read_cache(self) -> dict | None:
        try:
            data = json.loads(self._cache_path().read_text())
            return data if isinstance(data.get("rows"), list) else None
        except (OSError, ValueError, AttributeError):
            return None

    def _write_cache(self, payload: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.cache_dir, prefix=".cm-", suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(payload, fh)
        os.replace(tmp, self._cache_path())

    # -- fetch -----------------------------------------------------------------------------------
    def _run(self, extra: list[str], timeout: float) -> dict:
        argv = [self.cfg.codimango.command, "task", "list", *extra, "--json"]
        try:
            proc = self.runner(argv, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"timeout after {int(timeout)}s")
        except OSError as exc:
            raise RuntimeError(f"cannot run {argv[0]}: {exc}")
        if proc.returncode != 0:
            err = re.sub(r"\s+", " ", (proc.stderr or "").strip())[-200:]
            raise RuntimeError(f"exit {proc.returncode}: {err or 'no stderr'}")
        try:
            return _parse_envelope(proc.stdout or "")
        except ValueError as exc:
            raise RuntimeError(f"bad output: {exc}")

    def fetch(self, *, since=None, timeout_seconds: float | None = None, max_age_seconds: float = 0) -> FetchResult:
        timeout = timeout_seconds or self.cfg.codimango.timeout_seconds
        cached = self._read_cache()
        if cached and max_age_seconds:
            age = (_now() - datetime.fromisoformat(cached["fetched_at"])).total_seconds()
            if 0 <= age <= max_age_seconds:
                return self._result(cached, ok=True, detail="cache", findings=[])
        try:
            active = self._run([], timeout)
            archived = self._run(["--archived"], timeout)
        except RuntimeError as exc:
            return self._failed(cached, str(exc))
        rows = [normalise(t, archived=False) for t in active["tasks"]]
        rows += [normalise(t, archived=True) for t in archived["tasks"]]
        payload = {
            "fetched_at": _now().isoformat(timespec="seconds"),
            "total_exact": bool(active.get("totalExact", True)) and bool(archived.get("totalExact", True)),
            "training_degraded": bool(active.get("trainingStatusDegraded", False)),
            "rows": rows,
        }
        try:
            self._write_cache(payload)
        except OSError:
            pass   # serving fresh data matters more than caching it
        return self._result(payload, ok=True, detail="live", findings=[])

    def _failed(self, cached: dict | None, why: str) -> FetchResult:
        findings = [Finding("SYNC_FAILED", "warn", f"codimango fetch failed: {why}",
                            "check `codimango task list` works in this shell")]
        if cached:
            findings.append(Finding("CACHE_STALE", "warn", f"showing codimango cache from {cached['fetched_at']}",
                                    "fix the fetch, then rerun"))
            return self._result(cached, ok=False, detail=why, findings=findings)
        health = SourceHealth(NAME, False, None, self.cfg.codimango.max_stale_seconds, why)
        return FetchResult([], health, findings)

    def _result(self, payload: dict, *, ok: bool, detail: str, findings: list) -> FetchResult:
        at = datetime.fromisoformat(payload["fetched_at"])
        if not payload.get("total_exact", True):
            findings.append(Finding("INCOMPLETE", "warn", "codimango returned a partial task list",
                                    "rerun later; counts may be low"))
        if payload.get("training_degraded"):
            findings.append(Finding("DEGRADED", "info", "codimango training status is degraded",
                                    "used_in_training may lag"))
        obs = []
        for row in payload["rows"]:
            if not row.get("name"):
                continue
            fields = {f"codimango.{k}": v for k, v in row.items() if k != "name"}
            obs.append(Observation(NAME, row["name"], at, fields, {k: "authoritative" for k in fields}))
        health = SourceHealth(NAME, ok, at, self.cfg.codimango.max_stale_seconds, detail)
        return FetchResult(obs, health, findings)

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
    "trackAssignment": "track", "format": "format", "reviewStatus": "review_status",
    "tbdReviewStatus": "tbr_status", "updatedAt": "updated_at", "githubUrl": "github_url",
    "oraclePassCount": "oracle_pass", "oracleTotalCount": "oracle_total", "avocadoPassCount": "avocado_pass",
    "avocadoTotalCount": "avocado_total", "codexPassCount": "codex_pass", "codexTotalCount": "codex_total",
    "category": "category", "categorySubdomain": "subdomain", "categoryUsecase": "usecase", "difficulty": "difficulty",
    "programmingLanguages": "languages", "currentValidationGenerationId": "validation_generation",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _snake_validation(details) -> list:
    out = []
    for d in details or []:
        if isinstance(d, dict):
            out.append({"name": str(d.get("label") or d.get("name") or "")[:80], "status": str(d.get("status", ""))[:20],
                        "detail": str(d.get("detail") or "")[:300]})
    return out


def normalise(task: dict, *, archived: bool) -> dict:
    row = {snake: task.get(camel) for camel, snake in KEEP.items()}
    row["name"] = task.get("name")
    dom = task.get("domainContext")
    if isinstance(dom, list) and dom and isinstance(dom[0], dict):
        row["domain"] = " / ".join(str(dom[0].get(k)) for k in ("domain", "subCategory") if dom[0].get(k))
    row["validation"] = _snake_validation(task.get("validationDetails"))
    if archived:
        row["status_before_archive"] = row["status"]
        row["status"] = "archived"
    return row


def _parse_envelope(text: str) -> dict:
    """Strict envelope check (DESIGN §4). Raises ValueError on anything unexpected."""
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in output")
    data, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise ValueError("unexpected envelope (no tasks array)")
    for flag in ("totalExact", "trainingStatusDegraded"):
        if not isinstance(data.get(flag), bool):
            raise ValueError(f"envelope flag {flag} missing or not a boolean")
    for i, t in enumerate(data["tasks"]):
        if not (isinstance(t, dict) and isinstance(t.get("name"), str) and t["name"]):
            raise ValueError(f"task #{i} is not an object with a name")
    return data


def _aware_ts(value) -> datetime | None:
    try:
        ts = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return ts if ts.tzinfo else None


def _valid_cache(data) -> bool:
    return (
        isinstance(data, dict)
        and _aware_ts(data.get("fetched_at")) is not None
        and isinstance(data.get("total_exact"), bool)
        and isinstance(data.get("training_degraded"), bool)
        and isinstance(data.get("rows"), list)
        and all(isinstance(r, dict) and isinstance(r.get("name"), str) and r["name"] for r in data["rows"])
    )


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
        """The last complete snapshot, or None if missing or not in the expected shape."""
        try:
            data = json.loads(self._cache_path().read_text())
        except (OSError, ValueError):
            return None
        return data if _valid_cache(data) else None

    def _write_cache(self, payload: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.cache_dir, prefix=".cm-", suffix=".json")
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump(payload, fh)
            os.replace(tmp, self._cache_path())
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

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
            try:                                          # the CLI reports structured errors on stdout
                j = json.loads((proc.stdout or "").strip() or "{}").get("error") or {}
            except ValueError:
                j = {}
            if j.get("kind") == "authentication":
                raise RuntimeError(f"codimango login expired — run `{j.get('fix') or 'codimango auth setup'}`")
            if j.get("message"):
                raise RuntimeError(f"{j.get('kind', 'error')}: {str(j['message']).splitlines()[0][:120]}"
                                   + (f" — try `{j['fix']}`" if j.get("fix") else ""))
            err = re.sub(r"\s+", " ", (proc.stderr or "").strip())
            err = re.sub(r"(https?://\S+|malink/\S+|Need help\?.*$|=+)", "", err).strip(" .:")[-160:]
            raise RuntimeError(f"exit {proc.returncode}: {err or 'no stderr'}")
        try:
            return _parse_envelope(proc.stdout or "")
        except ValueError as exc:
            raise RuntimeError(f"bad output: {exc}") from None

    def fetch(self, *, since=None, timeout_seconds: float | None = None, max_age_seconds: float = 0) -> FetchResult:
        timeout = timeout_seconds or self.cfg.codimango.timeout_seconds
        cached = self._read_cache()
        if cached and max_age_seconds:
            age = (_now() - _aware_ts(cached["fetched_at"])).total_seconds()
            if 0 <= age <= max_age_seconds:
                return self._result(cached, ok=True, detail="cache", findings=[])
        try:
            active = self._run([], timeout)
            archived = self._run(["--archived"], timeout)
        except (RuntimeError, ValueError) as exc:
            return self._failed(cached, str(exc))
        rows = [normalise(t, archived=False) for t in active["tasks"]]
        rows += [normalise(t, archived=True) for t in archived["tasks"]]
        payload = {
            "fetched_at": _now().isoformat(timespec="seconds"),
            "total_exact": active["totalExact"] and archived["totalExact"],
            "training_degraded": active["trainingStatusDegraded"],
            "rows": rows,
        }
        if not payload["total_exact"]:
            # never let a partial list replace the last complete one
            why = "codimango returned a partial task list"
            if cached:
                return self._result(cached, ok=False, detail=why, findings=[
                    Finding("INCOMPLETE", "warn", why + f"; showing last complete list from {cached['fetched_at']}",
                            "rerun later")])
            return self._result(payload, ok=False, detail=why, findings=[])
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
        at = _aware_ts(payload["fetched_at"])
        if not payload["total_exact"] and not any(f.code == "INCOMPLETE" for f in findings):
            findings.append(Finding("INCOMPLETE", "warn", "codimango returned a partial task list",
                                    "rerun later; counts may be low"))
        if payload["training_degraded"]:
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

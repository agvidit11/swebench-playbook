"""Private, optional price estimates and lazy read-only Codimango run counts."""
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import tempfile
import time
from datetime import date
from pathlib import Path

ONLINE_CACHE = "online-usage-v1.json"


def matching_rate(model: str, cfg, *, on: date | None = None):
    on = on or date.today()
    matches = []
    for rate in getattr(getattr(cfg, "pricing", None), "models", []) or []:
        if not rate.pattern or not fnmatch.fnmatchcase(model, rate.pattern):
            continue
        try:
            effective = date.fromisoformat(rate.effective_from) if rate.effective_from else date.min
        except ValueError:
            continue
        if effective <= on:
            matches.append((effective, rate))
    return max(matches, key=lambda item: item[0])[1] if matches else None


def estimate(model: str | None, counters: dict, cfg, *, kind: str | None = None) -> dict:
    rate = matching_rate(str(model), cfg) if model else None
    if rate is None:
        return {"available": False, "label": "cost unavailable", "reason": "no matching private price"}
    inp = max(0, int(counters.get("input") or 0))
    cached = max(0, int(counters.get("cache_read") or 0))
    # Codex/Muse report cached input as a subset of input. Claude reports
    # cache fields separately from input.
    billable_input = max(0, inp - cached) if kind in ("codex", "muse") else inp
    amount = (billable_input * rate.input_per_million +
              max(0, int(counters.get("output") or 0)) * rate.output_per_million +
              cached * rate.cache_read_per_million +
              max(0, int(counters.get("cache_write") or 0)) * rate.cache_write_per_million +
              max(0, int(counters.get("reasoning") or 0)) * rate.reasoning_per_million) / 1_000_000
    version = f"{rate.pattern}@{rate.effective_from or 'all-time'}"
    return {"available": True, "kind": "estimate", "amount": round(amount, 6),
            "currency": rate.currency, "label": f"estimated {rate.currency} {amount:.2f}",
            "rate_version": version, "model": model}


def _atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _jobs(value) -> list[dict]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if not isinstance(value, dict):
        return []
    for key in ("jobs", "data", "items", "results"):
        if isinstance(value.get(key), list):
            return [x for x in value[key] if isinstance(x, dict)]
    return []


def _trial_count(job: dict) -> int:
    for key in ("trial_count", "trialCount", "trials_count", "num_trials"):
        if isinstance(job.get(key), int) and not isinstance(job.get(key), bool):
            return max(0, job[key])
    return len(job.get("trials") or []) if isinstance(job.get("trials"), list) else 0


def _job_usage(job: dict) -> tuple[str | None, dict | None, str | None]:
    config = job.get("config") if isinstance(job.get("config"), dict) else {}
    model = job.get("model") or job.get("model_name") or job.get("modelName") or config.get("model")
    kind = str(job.get("agent") or job.get("stage") or config.get("agent") or "").lower()
    kind = "codex" if "codex" in kind or "gpt" in str(model).lower() else \
        "muse" if "muse" in kind or "avocado" in kind else "claude" if "claude" in kind else None
    value = next((job.get(key) for key in ("usage", "token_usage", "tokenUsage")
                  if isinstance(job.get(key), dict)), None)
    if not value:
        return str(model) if model else None, None, kind
    counters = {"input": int(value.get("input_tokens") or value.get("inputTokens") or 0),
                "output": int(value.get("output_tokens") or value.get("outputTokens") or 0),
                "cache_read": int(value.get("cache_read_tokens") or value.get("cached_input_tokens") or 0),
                "cache_write": int(value.get("cache_write_tokens") or 0),
                "reasoning": int(value.get("reasoning_tokens") or value.get("reasoning_output_tokens") or 0)}
    return str(model) if model else None, counters, kind


def online_usage(task: str, cfg, cache_dir: Path, *, baseline: dict | None = None,
                 runner=subprocess.run, timeout: float = 3.0, max_age_s: int = 900) -> dict:
    """Fetch bounded job counts. No remote mutation and no raw response persistence."""
    path = Path(cache_dir) / ONLINE_CACHE
    cache = _load(path)
    entry = (cache.get("tasks") or {}).get(task) if isinstance(cache.get("tasks"), dict) else None
    if isinstance(entry, dict) and time.time() - float(entry.get("fetched_unix") or 0) < max_age_s:
        return {k: v for k, v in entry.items() if k != "fetched_unix"}
    baseline = baseline or {}
    trial_kinds = {key: max(0, int(value or 0)) for key, value in baseline.items()
                   if key in ("oracle", "avocado", "codex") and isinstance(value, (int, float))}
    result = {"source": "codimango read-only CLI", "run_count": None,
              "trial_count": sum(trial_kinds.values()) if trial_kinds else None,
              "trials_by_kind": trial_kinds, "cost": {"available": False, "label": "cost unavailable",
                                                       "reason": "authoritative tokens/model are unavailable"}}
    try:
        proc = runner([cfg.codimango.command, "job", "list", task, "--limit", "20", "--json"],
                      capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError("codimango job list failed")
        value = json.loads(proc.stdout)
        jobs = _jobs(value)
        reported_total = next((value.get(key) for key in ("total", "total_count", "totalCount")
                               if isinstance(value, dict) and isinstance(value.get(key), int)
                               and not isinstance(value.get(key), bool)), None)
        result["run_count"] = max(0, reported_total) if reported_total is not None else len(jobs)
        result["run_count_bounded"] = reported_total is None and (len(jobs) >= 20 or
                                       bool(value.get("has_more") if isinstance(value, dict) else False) or
                                       bool(value.get("remaining") if isinstance(value, dict) else False))
        counted = sum(_trial_count(job) for job in jobs)
        if counted:
            result["trial_count"] = counted
            result["trial_count_bounded"] = bool(result["run_count_bounded"])
        billed = [job.get("billed_amount") for job in jobs]
        currencies = {str(job.get("currency")) for job in jobs if job.get("currency")}
        if jobs and all(isinstance(amount, (int, float)) and not isinstance(amount, bool) for amount in billed) \
                and len(currencies) == 1:
            amount = sum(float(x) for x in billed)
            currency = next(iter(currencies))
            result["cost"] = {"available": True, "kind": "actual", "amount": round(amount, 6),
                              "currency": currency, "label": f"actual {currency} {amount:.2f}"}
        else:
            estimates = [estimate(model, counters, cfg, kind=kind) for model, counters, kind in
                         (_job_usage(job) for job in jobs) if counters]
            if estimates and len(estimates) == len(jobs) and all(item.get("available") for item in estimates):
                currencies = {item.get("currency") for item in estimates}
                if len(currencies) == 1:
                    amount = sum(float(item["amount"]) for item in estimates)
                    currency = next(iter(currencies))
                    result["cost"] = {"available": True, "kind": "estimate", "amount": round(amount, 6),
                                      "currency": currency, "label": f"estimated {currency} {amount:.2f}",
                                      "rate_versions": sorted({item.get("rate_version") for item in estimates})}
        result["observed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
        result["error"] = f"{exc.__class__.__name__}: {exc}"[:160]
        result["observed_at"] = None
    stored = dict(result, fetched_unix=time.time())
    tasks = cache.get("tasks") if isinstance(cache.get("tasks"), dict) else {}
    tasks[task] = stored
    if len(tasks) > 100:
        tasks = dict(sorted(tasks.items(), key=lambda item: item[1].get("fetched_unix", 0), reverse=True)[:100])
    _atomic(path, {"schema_version": 1, "tasks": tasks})
    return result

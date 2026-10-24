"""Human review history per task (decision kinds + times + short reason), fetched a few tasks at a time by
`board sync` and cached by the task's updatedAt. Reviewer names are not kept."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

CACHE = "reviews-detail.json"
DECISION = re.compile(r"^\s*(REVISION|ACCEPT\w*|REJECT\w*|APPROVE\w*)\b.*?@\s*(\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d)", re.M)


def parse(text: str) -> list[dict]:
    out = []
    blocks = list(DECISION.finditer(text))
    for i, m in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(text)
        body = text[m.end():end]
        reason = re.search(r"Decision reason:\s*(.+)", body)
        kind = "accept" if m.group(1).startswith(("ACCEPT", "APPROVE")) else \
            "reject" if m.group(1).startswith("REJECT") else "revision"
        out.append({"kind": kind, "at": m.group(2).replace(" ", "T") + "+00:00",
                    "reason": re.sub(r"\s+", " ", reason.group(1)).strip()[:180] if reason else ""})
    return sorted(out, key=lambda d: d["at"])


def load(cache_dir: Path) -> dict:
    try:
        data = json.loads((Path(cache_dir) / CACHE).read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def refresh(cfg, cache_dir: Path, tasks: list[tuple[str, str]], *, limit: int = 8, runner=subprocess.run) -> int:
    """tasks: [(name, updated_at)] of submitted tasks. Fetches up to `limit` whose cache key is stale."""
    cache = load(cache_dir)
    n = 0
    for name, updated in tasks:
        key = f"{updated}"
        if cache.get(name, {}).get("key") == key:
            continue
        if n >= limit:
            break
        try:
            p = runner([cfg.codimango.command, "task", "reviews", name, "--full"], capture_output=True, text=True,
                       timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if p.returncode != 0:
            continue
        cache[name] = {"key": key, "decisions": parse(p.stdout)}
        n += 1
    if n:
        fd, tmp = tempfile.mkstemp(dir=cache_dir, prefix=".revd-")
        with os.fdopen(fd, "w") as fh:
            json.dump(cache, fh)
        os.replace(tmp, Path(cache_dir) / CACHE)
    return n


def versions(commit_times: list[str], decisions: list[dict]) -> list[dict]:
    """Split commits into rounds by human decisions: V1 ends at the first decision, ... 'now' after the last."""
    from .projection import ts
    times = sorted(t for t in (ts(x) for x in commit_times) if t)
    bounds = [(ts(d["at"]), d) for d in decisions if ts(d["at"])]
    out, start = [], None
    for i, (at, d) in enumerate(bounds):
        n = sum(1 for t in times if (start is None or t > start) and t <= at)
        out.append({"label": f"V{i + 1}", "commits": n, "ended": d["kind"], "at": d["at"], "reason": d["reason"]})
        start = at
    out.append({"label": "now", "commits": sum(1 for t in times if start is None or t > start), "ended": None, "at": None,
                "reason": ""})
    return out

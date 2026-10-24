"""Rank: where you stand on your track/team/org, from a saved DaiQuery query (or an imported result).

`workboard rank` runs `meta daiquery.query execute --id=<rank.daiquery_id> --output=json` from your shell and
caches rows with their snapshot date. Agent sessions are often denied that table; then it prints the one
manual step, and `workboard rank import <file>` loads a pasted CSV/markdown result. Any query returning a
`scope` and `win` column works; other columns are shown as they come.
"""
from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CACHE = "rank-cache.json"


def _save(cache_dir: Path, rows: list[dict], source: str) -> dict:
    data = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": source, "rows": rows}
    fd, tmp = tempfile.mkstemp(dir=cache_dir, prefix=".rank-")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, cache_dir / CACHE)
    return data


def valid_rows(rows) -> bool:
    return isinstance(rows, list) and bool(rows) and all(isinstance(r, dict) for r in rows)


def load(cache_dir: Path) -> dict | None:
    try:
        data = json.loads((cache_dir / CACHE).read_text())
    except (OSError, ValueError):
        return None
    if not (isinstance(data, dict) and valid_rows(data.get("rows")) and isinstance(data.get("fetched_at"), str)):
        return None
    return data


def _clean(v):
    v = v.strip() if isinstance(v, str) else v
    if isinstance(v, str) and len(v) >= 2 and v[0] == v[-1] == '"':
        v = v[1:-1]
    return None if v in ("*NULL*", "NULL", "") else v


def parse_table(text: str) -> list[dict]:
    """Parse a markdown table (as daiquery copies it) or CSV into row dicts."""
    lines = [l for l in text.strip().splitlines() if l.strip()]
    if lines and lines[0].lstrip().startswith("|"):
        rows = [[c for c in l.strip().strip("|").split("|")] for l in lines]
        header = [_clean(h) for h in rows[0]]
        body = [r for r in rows[1:] if not set("".join(r).strip()) <= set("-: ")]
        return [dict(zip(header, (_clean(c) for c in r))) for r in body]
    reader = csv.DictReader(io.StringIO(text.strip()))
    return [{_clean(k): _clean(v) for k, v in row.items()} for row in reader]


def refresh(cfg, cache_dir: Path, *, runner=subprocess.run) -> tuple[dict | None, str]:
    if not cfg.rank.daiquery_id:
        return None, "set [rank] daiquery_id in your config (save rank-query.sql in DaiQuery and use its id)"
    argv = [cfg.rank.command, "daiquery.query", "execute", f"--id={cfg.rank.daiquery_id}", "--output=json", "--limit=500"]
    try:
        p = runner(argv, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"could not run {argv[0]}: {exc}"
    text = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0 or "AGENT_ROLE" in text or "denied" in text.lower():
        return None, ("the saved query could not run here (agent sessions are usually denied that table). "
                      f"Run it in DaiQuery (id {cfg.rank.daiquery_id}), copy the result, then: workboard rank import <file>")
    try:
        start = text.index("[") if "[" in text else text.index("{")
        data, _ = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return None, "unexpected output from the query runner"
    rows = data if isinstance(data, list) else (data.get("rows") or data.get("data")) if isinstance(data, dict) else None
    if not valid_rows(rows):
        return None, "the query returned no rows (or an unexpected shape)"
    return _save(cache_dir, rows, f"daiquery {cfg.rank.daiquery_id}"), "ok"


def import_file(path: Path, cache_dir: Path) -> dict:
    rows = parse_table(Path(path).read_text())
    if not valid_rows(rows) or "scope" not in rows[0]:
        raise ValueError("no table with a 'scope' column found in that file")
    return _save(cache_dir, rows, f"import {Path(path).name}")

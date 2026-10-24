"""Rank: where you stand on your track/team/org, from a saved DaiQuery query (or an imported result).

`workboard rank` runs `meta daiquery.query execute --id=<rank.daiquery_id> --output=json` from your shell and
caches rows with their snapshot date. Agent sessions are often denied that table; then it prints the one
manual step, and `workboard rank import <file>` loads a pasted CSV/markdown result. Any query returning a
canonical (scope, window, metric, value, rank, of) table, or the wide rank-query.sql shape, is normalized.
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
    rows = normalize(rows)
    data = {"fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": source, "rows": rows}
    fd, tmp = tempfile.mkstemp(dir=cache_dir, prefix=".rank-")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, cache_dir / CACHE)
    return data


CANON = ("scope", "window", "metric", "value", "rank", "of")
WIDE = {"acc": "accepted", "sub": "submitted", "work": "worked_on"}


def valid_rows(rows) -> bool:
    """Normalized rank rows: every row has the canonical keys with sane types."""
    if not (isinstance(rows, list) and rows):
        return False
    for r in rows:
        if not (isinstance(r, dict) and all(k in r for k in CANON) and isinstance(r["scope"], str)
                and isinstance(r["window"], str) and isinstance(r["metric"], str)):
            return False
    return True


def _num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def normalize(rows) -> list[dict]:
    """Accept canonical long rows, or the wide rank-query.sql shape (scope, win, acc, acc_rank "r/n", ...).
    Raises ValueError if a row has neither shape."""
    if not (isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows)):
        raise ValueError("expected a non-empty list of rows")
    out = []
    for i, r in enumerate(rows):
        if all(k in r for k in CANON):
            out.append({k: r[k] for k in CANON})
            continue
        scope, window = r.get("scope"), r.get("win") or r.get("window")
        if not (isinstance(scope, str) and isinstance(window, str)):
            raise ValueError(f"row {i}: needs scope and win/window")
        found = False
        for short, metric in WIDE.items():
            if short not in r:
                continue
            found = True
            rank_text = str(r.get(f"{short}_rank") or "")
            rk, _, of = rank_text.partition("/")
            out.append({"scope": scope, "window": window, "metric": metric, "value": _num(r.get(short)),
                        "rank": _num(rk), "of": _num(of)})
        if not found:
            raise ValueError(f"row {i}: no acc/sub/work or metric/value columns")
    return out


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
    if not (isinstance(rows, list) and rows):
        return None, "the query returned no rows"
    try:
        return _save(cache_dir, rows, f"daiquery {cfg.rank.daiquery_id}"), "ok"
    except ValueError as exc:
        return None, f"the query returned an unexpected shape: {exc}"


def import_file(path: Path, cache_dir: Path) -> dict:
    rows = parse_table(Path(path).read_text())
    if not rows:
        raise ValueError("no table found in that file")
    return _save(cache_dir, rows, f"import {Path(path).name}")


def pivot(rows) -> list[dict]:
    """scope/window -> {accepted, submitted, worked_on} as "value (rank/of)" strings for display."""
    table = {}
    for r in rows:
        key = (r["scope"], r["window"])
        cell = "" if r["value"] is None else str(r["value"])
        if r["rank"] is not None and r["of"]:
            cell += f" (#{r['rank']}/{r['of']})"
        table.setdefault(key, {"scope": r["scope"], "window": r["window"]})[r["metric"]] = cell
    return list(table.values())

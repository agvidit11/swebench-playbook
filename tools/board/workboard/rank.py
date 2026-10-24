"""Rank: where you stand on your track/team/org, from a saved DaiQuery query (or an imported result).

`workboard rank` runs `meta daiquery.query execute --id=<rank.daiquery_id> --output=json` from your shell and
caches rows with their snapshot date. Agent sessions are often denied that table; then it prints the one
manual step, and `workboard rank import <file>` loads a pasted CSV/markdown result. Any query returning a
canonical (scope, window, metric, value, rank, of) table, or the wide shape (scope, win, acc, acc_rank "r/n",
sub, sub_rank, work, work_rank), is normalized.
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


METRICS = set(WIDE.values())


def _row_ok(r) -> bool:
    if not (isinstance(r, dict) and all(k in r for k in CANON)):
        return False
    if not (isinstance(r["scope"], str) and r["scope"].strip() and isinstance(r["window"], str) and r["window"].strip()):
        return False
    if r["metric"] not in METRICS:
        return False
    for k in ("value", "rank", "of"):
        if r[k] is not None and not (isinstance(r[k], int) and not isinstance(r[k], bool) and r[k] >= 0):
            return False
    if (r["rank"] is None) != (r["of"] is None):
        return False
    return r["rank"] is None or (r["of"] >= 1 and 1 <= r["rank"] <= r["of"])


def valid_rows(rows) -> bool:
    """Normalized rank rows: canonical keys, allowed metric, ints or null, consistent rank/of."""
    return isinstance(rows, list) and bool(rows) and all(_row_ok(r) for r in rows)


class _Bad(Exception):
    pass


def _num(v):
    """Integer, integer string, or explicit null; anything else is invalid."""
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    if isinstance(v, bool):
        raise _Bad(v)
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().lstrip("-").isdigit():
        return int(v.strip())
    raise _Bad(v)


def normalize(rows) -> list[dict]:
    """Accept canonical long rows, or the wide shape (scope, win, acc, acc_rank "r/n", ...).
    Raises ValueError if a row has neither shape."""
    if not (isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows)):
        raise ValueError("expected a non-empty list of rows")
    out = []
    for i, r in enumerate(rows):
        if all(k in r for k in CANON):
            try:
                row = {"scope": r["scope"], "window": r["window"], "metric": r["metric"],
                       "value": _num(r["value"]), "rank": _num(r["rank"]), "of": _num(r["of"])}
            except _Bad:
                raise ValueError(f"row {i}: values must be integers or empty") from None
            if not _row_ok(row):
                raise ValueError(f"row {i}: invalid canonical row")
            out.append(row)
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
            try:
                row = {"scope": scope, "window": window, "metric": metric, "value": _num(r.get(short)),
                       "rank": _num(rk), "of": _num(of)}
            except _Bad:
                raise ValueError(f"row {i}: {metric} values must be integers or empty") from None
            if not _row_ok(row):
                raise ValueError(f"row {i}: invalid {metric} values")
            out.append(row)
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
        return None, "set [rank] daiquery_id in your config (the id of your saved DaiQuery rank query)"
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

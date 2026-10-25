"""Discover recent Codex and Muse runs and link jobs to their launching session."""
from __future__ import annotations

import json
import os
import re
import shlex
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .claude_sessions import session_key

CODEX = Path(os.environ.get("CODEX_SESSIONS_DIR", "~/.codex/sessions")).expanduser()
MUSE_DB = Path(os.environ.get("MUSE_SESSION_INDEX", "~/.local/share/muse/session-index.db")).expanduser()
CLAUDE_PROJECTS = Path(os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser()
_CODEX_ENV = re.compile(rb"(?:^|\x00)CODEX_(?:THREAD|SESSION)_ID=([^\x00]+)")


def _seconds(value) -> float | None:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = float(value)
        return value / 1_000_000 if value > 10_000_000_000_000 else value / 1000 if value > 10_000_000_000 else value
    return None


def _iso(value) -> str | None:
    value = _seconds(value)
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def _task_from_cwd(cwd: str | None, cfg) -> str | None:
    if not cwd:
        return None
    path = Path(cwd)
    for repo in cfg.repositories:
        try:
            rel = path.relative_to(Path(repo.path).expanduser())
        except ValueError:
            continue
        return rel.parts[0] if rel.parts else None
    return None


def _recent_codex_paths(root: Path, now: float, days: int = 7) -> list[Path]:
    out = []
    for offset in range(days):
        day = datetime.fromtimestamp(now - offset * 86400, timezone.utc)
        out.extend((root / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}").glob("*.jsonl"))
    return out


def discover_codex(cfg, host_id: str, *, root: Path | None = None, now: float | None = None,
                   paths: list[Path] | None = None, max_files: int = 200) -> list[dict]:
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    root = Path(root or CODEX).expanduser()
    candidates = paths if paths is not None else _recent_codex_paths(root, now)
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:max_files]
    out = []
    for path in candidates:
        try:
            mtime = path.stat().st_mtime
            with open(path, "rb") as fh:
                head = fh.read(256 * 1024)
        except OSError:
            continue
        meta = context = None
        for raw in head.splitlines():
            try:
                row = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                continue
            if row.get("type") == "session_meta" and isinstance(row.get("payload"), dict):
                meta = row["payload"]
            elif row.get("type") == "turn_context" and isinstance(row.get("payload"), dict):
                context = row["payload"]
            if meta and context:
                break
        if not meta:
            continue
        native_id = str(meta.get("id") or meta.get("session_id") or path.stem)
        cwd = meta.get("cwd") if isinstance(meta.get("cwd"), str) else None
        task = _task_from_cwd(cwd, cfg)
        started = _seconds(meta.get("timestamp")) or mtime
        age = max(0, now - mtime)
        state = "busy" if age <= 30 else "idle" if age <= 2 * 3600 else "historical"
        out.append({
            "session_key": session_key("codex", host_id, os.getuid(), "local", native_id),
            "native_id": native_id, "kind": "codex", "kind_icon": "🟢", "host": host_id,
            "name": f"Codex {native_id[:8]}" + (f" · {task}" if task else ""),
            "started_at": _iso(started), "age_s": int(max(0, now - started)), "last_activity_at": _iso(mtime),
            "status": state, "status_since": _iso(mtime), "live": state in ("busy", "idle"),
            "cwd": cwd, "cwd_task": task, "model": (context or {}).get("model"),
            "effort": (context or {}).get("effort"),
            "source": meta.get("source"), "originator": meta.get("originator"),
            "transport": {"available": False, "kind": "unavailable", "reason": "route to its parent session"},
            "parent_session_key": None, "parent_confidence": None,
        })
    return out


def live_codex_ids(proc_root: Path = Path("/proc"), uid: int | None = None) -> set[str]:
    """Codex ids proven live by a same-uid process environment, not log mtime."""
    uid = os.getuid() if uid is None else uid
    out = set()
    try:
        paths = list(Path(proc_root).iterdir())
    except OSError:
        return out
    for path in paths:
        if not path.name.isdigit():
            continue
        try:
            if path.stat().st_uid != uid:
                continue
            data = (path / "environ").read_bytes()
        except OSError:
            continue
        out.update(x.decode("utf-8", "replace") for x in _CODEX_ENV.findall(data) if x)
    return out


def _parent_id(path: Path) -> str:
    parts = path.parts
    if "subagents" in parts:
        i = parts.index("subagents")
        if i:
            return parts[i - 1]
    return path.stem


def _expanded(value: str, variables: dict[str, str], cwd: str | None) -> str | None:
    value = value.strip().strip("'\"")
    for key, val in variables.items():
        value = value.replace("${" + key + "}", val).replace("$" + key, val)
    value = os.path.expanduser(value)
    if "$" in value or "$(" in value or not value:
        return None
    path = Path(value)
    if not path.is_absolute() and cwd:
        path = Path(cwd) / path
    try:
        return str(path.resolve(strict=False))
    except OSError:
        return str(path)


def _launch_commands(command: str, cwd: str | None) -> list[tuple[str, list[str]]]:
    """Extract agent kind + declared workspaces without executing shell text."""
    variables = {"HOME": str(Path.home())}
    for name, double, single, bare in re.findall(
            r"(?:^|[;\s])([A-Za-z_][A-Za-z0-9_]*)=(?:\"([^\"]+)\"|'([^']+)'|([^;\s]+))", command):
        value = double or single or bare
        if value:
            variables[name] = value.replace("$HOME", variables["HOME"])
    out = []
    for kind, rx, opts in (
            ("codex", re.compile(r"\bcodex\s+exec\b"), ("-C", "--cd", "--add-dir")),
            ("muse", re.compile(r"\bmuse\s+exec\b"), ("--workspace",))):
        for hit in rx.finditer(command):
            # One shell command is enough context for its options, without consuming a
            # later heredoc/prose mention of another invocation.
            segment = command[hit.start():hit.start() + 8000].split("\n", 1)[0]
            try:
                tokens = shlex.split(segment, comments=False, posix=True)
            except ValueError:
                tokens = segment.replace("=", " ").split()
            workspaces = []
            for i, token in enumerate(tokens):
                value = None
                for opt in opts:
                    if token == opt and i + 1 < len(tokens):
                        value = tokens[i + 1]
                    elif token.startswith(opt + "="):
                        value = token.split("=", 1)[1]
                    if value is not None:
                        break
                if value is not None:
                    expanded = _expanded(value, variables, cwd)
                    if expanded:
                        workspaces.append(expanded)
            if workspaces:
                out.append((kind, sorted(set(workspaces))))
    return out


def transcript_launches(parents: list[dict], *, root: Path | None = None,
                        now: float | None = None, max_age_s: int = 7 * 86400) -> list[dict]:
    """Sanitized launch windows from live parents' tool-use records.

    Only timestamps, agent kind, and workspace paths are returned in memory; no
    prompt/response or command text enters the board payload or cache.
    """
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    root = Path(root or CLAUDE_PROJECTS).expanduser()
    by_id = {p.get("native_id"): p for p in parents if p.get("native_id")}
    if not by_id or not root.is_dir():
        return []
    paths = []
    for native in by_id:
        paths.extend(root.glob(f"*/{native}.jsonl"))
        paths.extend(root.glob(f"*/{native}/subagents/*.jsonl"))
    out = []
    for path in sorted(set(paths)):
        parent = by_id.get(_parent_id(path))
        if not parent:
            continue
        uses, results = [], {}
        try:
            with open(path, "rb") as fh:
                for raw in fh:
                    if b'"tool_use"' not in raw and b'"tool_result"' not in raw:
                        continue
                    try:
                        row = json.loads(raw)
                    except (ValueError, UnicodeDecodeError):
                        continue
                    at = _seconds(row.get("timestamp"))
                    if at is None or not 0 <= now - at <= max_age_s:
                        continue
                    message = row.get("message") if isinstance(row.get("message"), dict) else {}
                    content = message.get("content") if isinstance(message.get("content"), list) else []
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get("type") == "tool_result" and isinstance(part.get("tool_use_id"), str):
                            results[part["tool_use_id"]] = max(at, results.get(part["tool_use_id"], 0))
                        if part.get("type") != "tool_use" or not isinstance(part.get("input"), dict):
                            continue
                        commands = []
                        for key in ("command", "cmd"):
                            if isinstance(part["input"].get(key), str):
                                commands.append(part["input"][key])
                        for command in commands:
                            for kind, workspaces in _launch_commands(command, parent.get("cwd")):
                                uses.append((str(part.get("id") or ""), at, kind, workspaces))
        except OSError:
            continue
        for tool_id, start, kind, workspaces in uses:
            end = results.get(tool_id, start + 3600)
            out.append({"kind": kind, "workspaces": workspaces, "start": start - 120,
                        "end": max(start, end) + 120, "parent": parent})
    return out


def discover_muse(cfg, host_id: str, *, db_path: Path | None = None, now: float | None = None,
                  limit: int = 100) -> list[dict]:
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    db_path = Path(db_path or MUSE_DB).expanduser()
    if not db_path.exists():
        return []
    sql = ("SELECT session_id, workspace_root, provider_id, model_id, created_at_us, updated_at_us, status, "
           "msp_parent_session_id FROM sessions ORDER BY updated_at_us DESC LIMIT ?")
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.2)
        try:
            rows = con.execute(sql, (limit,)).fetchall()
        finally:
            con.close()
    except (sqlite3.Error, OSError):
        return []
    out = []
    for native_id, cwd, provider, model, created, updated, status, muse_parent in rows:
        if not native_id:
            continue
        updated_s = _seconds(updated)
        created_s = _seconds(created) or updated_s
        age = max(0, now - updated_s) if updated_s is not None else None
        state = str(status or ("busy" if age is not None and age <= 30 else "historical"))
        task = _task_from_cwd(cwd, cfg)
        out.append({
            "session_key": session_key("muse", host_id, os.getuid(), "local", str(native_id)),
            "native_id": str(native_id), "kind": "muse", "kind_icon": "🟠", "host": host_id,
            "name": f"Muse {str(native_id)[:8]}" + (f" · {task}" if task else ""),
            "started_at": _iso(created_s), "age_s": int(max(0, now - created_s)) if created_s is not None else None,
            "last_activity_at": _iso(updated_s), "status": state, "status_since": _iso(updated_s),
            "live": state.lower() in ("busy", "running", "active"), "cwd": cwd, "cwd_task": task,
            "model": model, "provider": provider, "muse_parent_id": muse_parent,
            "transport": {"available": False, "kind": "unavailable", "reason": "route to its parent session"},
            "parent_session_key": None, "parent_confidence": None,
        })
    return out


def _workspace(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(Path(value).expanduser().resolve(strict=False))
    except OSError:
        return str(Path(value).expanduser())


def link_parents(runs: list[dict], parents: list[dict], evs: list[dict], *, now: float | None = None,
                 launches: list[dict] | None = None) -> list[dict]:
    """Link runs by kind + workspace + start inside a parent's tool-use window."""
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    by_native = {p.get("native_id"): p for p in parents}
    event_launches = []
    for e in evs:
        if e.get("type") != "build_action":
            continue
        at = _seconds(e.get("occurred_at"))
        kind = str((e.get("payload") or {}).get("model") or "").lower()
        kind = "codex" if "codex" in kind else "muse" if "muse" in kind else kind
        parent = by_native.get((e.get("actor") or {}).get("session_id"))
        task = (e.get("entity") or {}).get("id")
        if parent and at is not None:
            event_launches.append((kind, task, at, parent))
    presence = []
    for e in evs:
        payload = e.get("payload") or {}
        parent = by_native.get((e.get("actor") or {}).get("session_id"))
        seen = _seconds(payload.get("last_seen")) or _seconds(e.get("occurred_at"))
        task = (e.get("entity") or {}).get("id")
        if parent and task and seen is not None:
            for kind in payload.get("agents") or []:
                if kind in ("codex", "muse"):
                    presence.append((kind, task, seen, parent))
    for run in runs:
        run_at = _seconds(run.get("started_at")) or _seconds(run.get("last_activity_at")) or now
        run_workspace = _workspace(run.get("cwd"))
        choices = []
        for hint in launches or []:
            if hint.get("kind") != run.get("kind") or not hint.get("start") <= run_at <= hint.get("end"):
                continue
            if run_workspace and run_workspace in {_workspace(x) for x in hint.get("workspaces") or []}:
                choices.append((abs(run_at - (hint["start"] + 120)), hint["parent"]))
        choices += [(1 + abs(run_at - at), parent) for kind, task, at, parent in event_launches
                   if kind == run.get("kind") and (not run.get("cwd_task") or task == run.get("cwd_task"))
                   and -120 <= run_at - at <= 900]
        confidence = None
        parent = min(choices, key=lambda x: x[0])[1] if choices else None
        if parent:
            confidence = "high"
        if not parent and run.get("cwd_task"):
            seen = [(abs(run_at - at), p) for kind, task, at, p in presence
                    if kind == run.get("kind") and task == run.get("cwd_task") and 0 <= at - run_at <= 6 * 3600]
            unique = {p["session_key"]: p for _, p in seen}
            if len(unique) == 1:
                parent, confidence = next(iter(unique.values())), "medium"
        if parent:
            run["parent_session_key"] = parent["session_key"]
            run["parent_confidence"] = confidence
            run["transport"] = {"available": bool(parent.get("transport", {}).get("available")),
                                "kind": "parent", "reason": f"route to {parent['name']}"}
            parent.setdefault("child_runs", []).append(run)
    return runs

"""Incremental, privacy-minimal usage indexing for Claude, Codex, and Muse.

Only numeric counters, opaque IDs/hashes, timestamps, task slugs, and model names
are persisted.  Prompt, response, tool, command, cwd, and message text are never
written to the workboard cache.
"""
from __future__ import annotations

import hashlib
import json
import os
import fcntl
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from .sources import agent_runs

SCHEMA_VERSION = 1
CACHE_NAME = "usage-v1.json"
COUNTERS = ("input", "output", "cache_read", "cache_write", "reasoning", "total")
MAX_SEEN_PER_SESSION = 20000


def _seconds(value) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = float(value)
        return value / 1_000_000 if value > 10_000_000_000_000 else value / 1000 if value > 10_000_000_000 else value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _iso(value: float | None) -> str | None:
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def _number(value) -> int:
    return max(0, int(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _blank() -> dict[str, int]:
    return {key: 0 for key in COUNTERS}


def _add(into: dict, counters: dict) -> None:
    for key in COUNTERS:
        into[key] = _number(into.get(key)) + _number(counters.get(key))


def _fp(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:32]


def _record_id(*values) -> str:
    return _fp("\x1f".join(str(value) for value in values))


def _usage_key(kind: str, native_id: str) -> str:
    return f"{kind}:{native_id}"


def _fresh_state() -> dict:
    return {"schema_version": SCHEMA_VERSION, "updated_at": None, "cursors": {}, "sessions": {},
            "samples": [], "seen": {}, "last_cycle": {}}


def load(cache_dir: Path) -> dict:
    try:
        value = json.loads((Path(cache_dir) / CACHE_NAME).read_text())
    except (OSError, ValueError, TypeError):
        return _fresh_state()
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        return _fresh_state()
    for key, default in (("cursors", {}), ("sessions", {}), ("samples", []), ("seen", {}),
                         ("last_cycle", {})):
        if not isinstance(value.get(key), type(default)):
            value[key] = default
    return value


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _task_from_cwd(cwd: str | None, cfg) -> str | None:
    if not isinstance(cwd, str) or not cwd:
        return None
    path = Path(cwd).expanduser()
    for repo in cfg.repositories:
        try:
            rel = path.relative_to(Path(repo.path).expanduser())
        except ValueError:
            continue
        return rel.parts[0] if rel.parts else None
    return None


def _claude_paths(root: Path, cutoff: float, live_ids: set[str], limit: int = 4096) -> list[tuple]:
    """Shallow metadata scan; file bodies remain bounded by the byte cursor."""
    out = []
    if not root.is_dir():
        return out
    try:
        projects = list(root.iterdir())
    except OSError:
        return out
    for project in projects:
        if not project.is_dir():
            continue
        candidates = list(project.glob("*.jsonl"))
        candidates += list(project.glob("*/subagents/*.jsonl"))
        for path in candidates:
            try:
                st = path.stat()
            except OSError:
                continue
            native = path.parent.parent.name if path.parent.name == "subagents" else path.stem
            if st.st_mtime >= cutoff or native in live_ids:
                out.append(("claude", path, native, {}))
                if len(out) >= limit:
                    return out
    return out


def _codex_paths(root: Path, now: float, days: int = 14, limit: int = 4096) -> list[tuple]:
    out = []
    for offset in range(days + 1):
        day = datetime.fromtimestamp(now - offset * 86400, timezone.utc)
        folder = root / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}"
        try:
            paths = folder.glob("*.jsonl")
            for path in paths:
                out.append(("codex", path, path.stem, {}))
                if len(out) >= limit:
                    return out
        except OSError:
            continue
    return out


def _muse_paths(db_path: Path, cutoff: float, limit: int = 5000) -> list[tuple]:
    if not db_path.exists():
        return []
    columns = ("session_id,session_dir,session_log_path,workspace_root,provider_id,model_id,"
               "created_at_us,updated_at_us,status")
    sql = (f"SELECT {columns} FROM sessions WHERE updated_at_us >= ? OR lower(status) IN "
           "('busy','running','active') ORDER BY updated_at_us DESC LIMIT ?")
    try:
        # immutable prevents journal/WAL/shm creation in the vendor-owned directory.
        con = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True, timeout=0.2)
        try:
            rows = con.execute(sql, (int(cutoff * 1_000_000), limit)).fetchall()
        finally:
            con.close()
    except (sqlite3.Error, OSError):
        return []
    out = []
    for native, directory, log_path, cwd, provider, model, created, updated, status in rows:
        if not native:
            continue
        path = Path(log_path or "")
        if not path.is_absolute():
            path = Path(directory or "") / (log_path or "session.jsonl")
        if path.is_file():
            out.append(("muse", path, str(native), {"cwd_task": cwd, "provider": provider,
                                                     "model": model, "status": status,
                                                     "created_at": created, "updated_at": updated}))
    return out


def _tail(path: Path, cursor: dict, budget: int, deadline: float) -> tuple[list[bytes], int, dict]:
    """Read complete JSONL records after a cursor, skipping sparse holes."""
    try:
        before = path.stat()
    except OSError:
        return [], 0, cursor
    identity = f"{before.st_dev}:{before.st_ino}"
    old_identity = cursor.get("inode")
    offset = _number(cursor.get("offset"))
    rotated = old_identity is not None and (old_identity != identity or before.st_size < offset)
    if rotated:
        offset = 0
        cursor = {"generation": _number(cursor.get("generation")) + 1}
    cursor.update({"fingerprint": _fp(str(path.resolve(strict=False))), "inode": identity,
                   "size": before.st_size})
    if offset >= before.st_size or budget <= 0 or time.monotonic() >= deadline:
        cursor["offset"] = min(offset, before.st_size)
        return [], 0, cursor
    records, read_bytes, safe = [], 0, offset
    carry = b""
    discarding = bool(cursor.pop("discarding", False))
    try:
        fd = os.open(path, os.O_RDONLY)
        try:
            pos, size = offset, before.st_size
            while pos < size and read_bytes < budget and time.monotonic() < deadline:
                try:
                    data_pos = os.lseek(fd, pos, os.SEEK_DATA)
                except OSError:
                    data_pos = pos
                if data_pos > pos:
                    carry = b""
                    discarding = False
                    safe = data_pos
                    pos = data_pos
                try:
                    hole = min(size, os.lseek(fd, pos, os.SEEK_HOLE))
                except OSError:
                    hole = size
                os.lseek(fd, pos, os.SEEK_SET)
                chunk = os.read(fd, min(65536, hole - pos, budget - read_bytes))
                if not chunk:
                    if hole > pos:
                        pos = hole
                        safe = hole
                        carry = b""
                        continue
                    break
                pos += len(chunk)
                read_bytes += len(chunk)
                data = carry + chunk
                pieces = data.split(b"\n")
                complete, carry = pieces[:-1], pieces[-1]
                consumed = pos - len(carry)
                for raw in complete:
                    if discarding:
                        discarding = False
                    elif raw.strip():
                        records.append(raw)
                safe = consumed
                if len(carry) > 512 * 1024:
                    # Never persist a possibly private partial line.  Skip an
                    # exceptional oversized record rather than pinning a cursor.
                    carry = b""
                    discarding = True
                    safe = pos
                if pos >= hole and hole < size:
                    carry = b""
                    discarding = False
                    safe = hole
                    pos = hole
        finally:
            os.close(fd)
    except OSError:
        return [], read_bytes, cursor
    cursor["offset"] = safe
    if discarding:
        cursor["discarding"] = True
    cursor["size"] = before.st_size
    return records, read_bytes, cursor


def _session(state: dict, kind: str, native: str) -> tuple[str, dict]:
    key = _usage_key(kind, native)
    value = state["sessions"].setdefault(key, {"kind": kind, "native_id": native,
                                                "counters": _blank(), "observed_at": None})
    return key, value


def _seen(state: dict, key: str, record: str) -> bool:
    digest = _fp(record)
    values = state["seen"].setdefault(key, [])
    if digest in values:
        return True
    values.append(digest)
    if len(values) > MAX_SEEN_PER_SESSION:
        del values[:-MAX_SEEN_PER_SESSION]
    return False


def _sample(state: dict, key: str, record: str, at: float | None, counters: dict, *, model=None,
            effort=None, context_tokens=None, context_window=None, source_task=None, source_confidence=None) -> None:
    if not any(_number(counters.get(k)) for k in COUNTERS):
        return
    session = state["sessions"][key]
    _add(session["counters"], counters)
    session["observed_at"] = _iso(at)
    if model:
        session["model"] = str(model)[:160]
    if effort:
        session["effort"] = str(effort)[:40]
    if context_tokens is not None:
        session["context_tokens"] = _number(context_tokens)
    if context_window is not None:
        session["context_window"] = _number(context_window)
    state["samples"].append({"id": _fp(record), "session": key, "kind": session["kind"],
                             "at": _iso(at), "counters": {k: _number(counters.get(k)) for k in COUNTERS},
                             "model": str(model)[:160] if model else None,
                             "task": source_task, "source_confidence": source_confidence})


def _claude_record(raw: bytes, state: dict, cfg, native_hint: str) -> None:
    if b'"usage"' not in raw or b'"assistant"' not in raw:
        return
    try:
        row = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return
    if row.get("type") != "assistant" or not isinstance(row.get("message"), dict):
        return
    message = row["message"]
    usage = message.get("usage") if isinstance(message.get("usage"), dict) else None
    if not usage:
        return
    native = str(row.get("sessionId") or row.get("session_id") or native_hint)
    key, _ = _session(state, "claude", native)
    message_id = str(message.get("id") or row.get("uuid") or
                     _record_id(row.get("timestamp"), *(usage.get(k) for k in sorted(usage))))
    if _seen(state, key, message_id):
        return
    counters = {"input": _number(usage.get("input_tokens")), "output": _number(usage.get("output_tokens")),
                "cache_read": _number(usage.get("cache_read_input_tokens")),
                "cache_write": _number(usage.get("cache_creation_input_tokens")), "reasoning": 0}
    counters["total"] = sum(counters[k] for k in ("input", "output", "cache_read", "cache_write"))
    context = counters["input"] + counters["cache_read"] + counters["cache_write"]
    model = message.get("model")
    _sample(state, key, message_id, _seconds(row.get("timestamp")), counters, model=model,
            context_tokens=context, source_task=_task_from_cwd(row.get("cwd"), cfg), source_confidence="medium")


def _codex_record(raw: bytes, state: dict, cfg, native_hint: str, cursor: dict) -> None:
    try:
        row = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    typ = row.get("type")
    if typ == "session_meta":
        native = str(payload.get("id") or payload.get("session_id") or native_hint)
        cursor["native_id"] = native
        cursor["context_window"] = _number(payload.get("context_window")) or cursor.get("context_window")
        cursor["cwd_task"] = _task_from_cwd(payload.get("cwd"), cfg)
        _session(state, "codex", native)
        return
    if typ == "turn_context":
        if isinstance(payload.get("model"), str):
            cursor["model"] = payload["model"][:160]
        if isinstance(payload.get("effort"), str):
            cursor["effort"] = payload["effort"][:40]
        cursor["cwd_task"] = _task_from_cwd(payload.get("cwd"), cfg) or cursor.get("cwd_task")
        return
    if typ != "token_count" and not (typ == "event_msg" and payload.get("type") == "token_count"):
        return
    info = payload.get("info") if isinstance(payload.get("info"), dict) else payload
    total = info.get("total_token_usage") if isinstance(info.get("total_token_usage"), dict) else None
    if not total:
        return
    native = str(cursor.get("native_id") or native_hint)
    key, session = _session(state, "codex", native)
    record = str(row.get("id") or row.get("uuid") or _record_id(row.get("timestamp"), json.dumps(total, sort_keys=True)))
    if _seen(state, key, record):
        return
    current = {"input": _number(total.get("input_tokens")), "output": _number(total.get("output_tokens")),
               "cache_read": _number(total.get("cached_input_tokens")),
               "cache_write": _number(total.get("cache_write_input_tokens")),
               "reasoning": _number(total.get("reasoning_output_tokens")),
               "total": _number(total.get("total_tokens"))}
    previous = cursor.get("cumulative") if isinstance(cursor.get("cumulative"), dict) else session.get("codex_cumulative")
    previous = previous if isinstance(previous, dict) else {}
    reset = bool(previous) and current["total"] < _number(previous.get("total"))
    delta = {k: current[k] if reset or not previous else max(0, current[k] - _number(previous.get(k))) for k in COUNTERS}
    cursor["cumulative"] = current
    session["codex_cumulative"] = current
    last = info.get("last_token_usage") if isinstance(info.get("last_token_usage"), dict) else {}
    context = _number(last.get("input_tokens")) or current["input"]
    window = _number(info.get("model_context_window")) or _number(cursor.get("context_window"))
    _sample(state, key, record, _seconds(row.get("timestamp")), delta, model=cursor.get("model"),
            effort=cursor.get("effort"), context_tokens=context, context_window=window,
            source_task=cursor.get("cwd_task"), source_confidence="medium")


def _muse_record(raw: bytes, state: dict, native: str, meta: dict) -> None:
    if b'"usage"' not in raw:
        return
    try:
        row = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    event = payload.get("event") if isinstance(payload.get("event"), dict) else {}
    usage = event.get("usage") if isinstance(event.get("usage"), dict) else None
    if not usage:
        return
    key, _ = _session(state, "muse", native)
    record = str(row.get("id") or _record_id(row.get("recorded_at"), row.get("sequence"), json.dumps(usage, sort_keys=True)))
    if _seen(state, key, record):
        return
    counters = {"input": _number(usage.get("input_tokens")), "output": _number(usage.get("output_tokens")),
                "cache_read": _number(usage.get("cache_read_tokens") or usage.get("cached_tokens")),
                "cache_write": _number(usage.get("cache_write_tokens")),
                "reasoning": _number(usage.get("reasoning_tokens"))}
    # Muse's input total includes cached input; keep cache as a breakdown, not
    # an additional unit in the total.
    counters["total"] = counters["input"] + counters["output"]
    _sample(state, key, record, _seconds(row.get("recorded_at")), counters,
            model=event.get("model") or meta.get("model"), context_tokens=counters["input"],
            source_task=meta.get("task"),
            source_confidence="medium")


def _collect(cfg, evs: list[dict] | None, host_id: str, *, sessions: list[dict] | None = None,
             cache_dir: Path | None = None, claude_root: Path | None = None, codex_root: Path | None = None,
             muse_db: Path | None = None, now: float | None = None, recent_days: int = 14,
             byte_budget: int = 768 * 1024, time_budget_s: float = 0.8) -> dict:
    """Advance every source best-effort within one shared byte/time budget."""
    now = time.time() if now is None else now
    cache_dir = Path(cache_dir or os.environ.get("WORKBOARD_CACHE", "~/.cache/workboard")).expanduser()
    state = load(cache_dir)
    start, deadline = time.monotonic(), time.monotonic() + max(0.05, time_budget_s)
    cutoff = now - recent_days * 86400
    live_ids = {str(s.get("native_id")) for s in sessions or [] if s.get("live") and s.get("kind") == "claude"}
    roots = (Path(claude_root or os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects")).expanduser(),
             Path(codex_root or os.environ.get("CODEX_SESSIONS_DIR", "~/.codex/sessions")).expanduser(),
             Path(muse_db or os.environ.get("MUSE_SESSION_INDEX", "~/.local/share/muse/session-index.db")).expanduser())
    errors, candidates = [], []
    for label, fn in (("claude", lambda: _claude_paths(roots[0], cutoff, live_ids)),
                      ("codex", lambda: _codex_paths(roots[1], now, recent_days)),
                      ("muse", lambda: _muse_paths(roots[2], cutoff))):
        try:
            candidates.extend(fn())
        except Exception as exc:
            errors.append(f"{label}: {exc.__class__.__name__}")
    # Resolve Muse workspaces in memory to a task slug, never persist the path.
    normalized = []
    for kind, path, native, meta in candidates:
        meta = dict(meta)
        if kind == "muse":
            meta["task"] = _task_from_cwd(meta.pop("cwd_task", None), cfg)
        normalized.append((kind, path, native, meta))
    candidates = normalized
    # Files with unread bytes first, but cap each turn so one large transcript
    # cannot starve the other sessions.
    def lag(item):
        _, path, _, _ = item
        cursor = state["cursors"].get(_fp(str(path.resolve(strict=False))), {})
        try:
            return path.stat().st_size - _number(cursor.get("offset"))
        except OSError:
            return -1
    candidates.sort(key=lambda item: (lag(item) <= 0, -lag(item), str(item[1])))
    total_read = files_read = records_seen = 0
    for kind, path, native, meta in candidates:
        if total_read >= byte_budget or time.monotonic() >= deadline:
            break
        fingerprint = _fp(str(path.resolve(strict=False)))
        existed = fingerprint in state["cursors"]
        cursor = state["cursors"].get(fingerprint, {"fingerprint": fingerprint, "offset": 0, "generation": 0})
        records, used, cursor = _tail(path, cursor, min(256 * 1024, byte_budget - total_read), deadline)
        total_read += used
        files_read += bool(used)
        records_seen += len(records)
        try:
            for raw in records:
                if kind == "claude":
                    _claude_record(raw, state, cfg, native)
                elif kind == "codex":
                    _codex_record(raw, state, cfg, native, cursor)
                else:
                    _muse_record(raw, state, native, meta)
        except Exception as exc:
            errors.append(f"{kind} parse: {exc.__class__.__name__}")
        cursor.update({"kind": kind, "native_id": str(cursor.get("native_id") or native)})
        if used or not existed:
            cursor["updated_at"] = _iso(now)
        state["cursors"][fingerprint] = cursor
    backlog_files = backlog_bytes = 0
    for _, path, _, _ in candidates:
        fingerprint = _fp(str(path.resolve(strict=False)))
        cursor = state["cursors"].get(fingerprint) or {}
        try:
            remaining = max(0, path.stat().st_size - _number(cursor.get("offset")))
        except OSError:
            continue
        if remaining:
            backlog_files += 1
            backlog_bytes += remaining
    cache_path = cache_dir / CACHE_NAME
    changed = bool(total_read or errors or not cache_path.exists())
    if changed:
        state["updated_at"] = _iso(now)
    state["last_cycle"] = {"at": _iso(now), "bytes_read": total_read, "files_read": files_read,
                           "records_seen": records_seen, "candidate_files": len(candidates),
                           "backlog_files": backlog_files, "backlog_bytes": backlog_bytes,
                           "index_complete": backlog_files == 0,
                           "duration_ms": round((time.monotonic() - start) * 1000, 2), "errors": errors[:12]}
    if changed:
        _atomic_json(cache_path, state)
    return aggregate(state, cfg, evs or [], now=now)


def collect(cfg, evs: list[dict] | None, host_id: str, **kwargs) -> dict:
    """Serialize cron/server collectors so atomic replacement cannot lose deltas."""
    cache_dir = Path(kwargs.get("cache_dir") or
                     os.environ.get("WORKBOARD_CACHE", "~/.cache/workboard")).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    kwargs["cache_dir"] = cache_dir
    lock = open(cache_dir / "usage.lock", "a+")
    try:
        os.fchmod(lock.fileno(), 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _collect(cfg, evs, host_id, **kwargs)
    finally:
        lock.close()


def _actor_ids(event: dict) -> set[str]:
    actor = event.get("actor") or {}
    sid = actor.get("session_id")
    return {str(sid)} if sid else set()


def _attribution(sample: dict, evs: list[dict], at: float) -> tuple[str | None, str]:
    key = sample.get("session", "")
    native = key.split(":", 1)[1] if ":" in key else key
    relevant = []
    for event in evs:
        if native not in _actor_ids(event) and key not in _actor_ids(event):
            continue
        when = _seconds(event.get("occurred_at"))
        if when is not None and when <= at:
            relevant.append((when, event))
    checkins = [(when, event) for when, event in relevant if event.get("type") == "checkin"
                and 0 <= at - when <= 24 * 3600]
    if checkins:
        _, latest = max(checkins, key=lambda item: item[0])
        payload = latest.get("payload") or {}
        if payload.get("status") == "idle":
            return None, "unattributed"
        tasks = sorted({str(x) for x in payload.get("tasks") or [] if x})
        if len(tasks) == 1:
            return tasks[0], "exact"
        if len(tasks) > 1:
            return None, "ambiguous"
    tools = []
    for when, event in relevant:
        task = (event.get("entity") or {}).get("id")
        if task and event.get("type") in ("touch", "check", "review") and 0 <= at - when <= 15 * 60:
            tools.append(str(task))
    tools = sorted(set(tools))
    if len(tools) == 1:
        return tools[0], "exact"
    if len(tools) > 1:
        return None, "ambiguous"
    if sample.get("task"):
        return str(sample["task"]), "medium"
    return None, "unattributed"


def aggregate(state: dict, cfg, evs: list[dict], *, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    sessions = {}
    for key, raw in state.get("sessions", {}).items():
        counters = {k: _number((raw.get("counters") or {}).get(k)) for k in COUNTERS}
        window = _number(raw.get("context_window")) or context_window(raw.get("model"), cfg)
        context = _number(raw.get("context_tokens"))
        if context and window and context > window and window <= 200000 and "claude" in str(raw.get("model") or "claude"):
            window = 1_000_000                            # observed context proves a 1M-context model
        sessions[key] = {"kind": raw.get("kind"), "native_id": raw.get("native_id"), "model": raw.get("model"),
                         "effort": raw.get("effort"), "counters": counters, "total": counters["total"],
                         "last_hour": 0, "observed_at": raw.get("observed_at"),
                         "index_complete": bool((state.get("last_cycle") or {}).get("index_complete")),
                         "context": {"tokens": context or None, "window": window or None,
                                     "pressure_pct": round(100 * context / window) if context and window else None}}
        from .costs import estimate
        sessions[key]["spend"] = estimate(raw.get("model"), counters, cfg, kind=raw.get("kind"))
    tasks, accounting = {}, {"exact": 0, "medium": 0, "ambiguous": 0, "unattributed": 0}
    daily = {}
    for sample in state.get("samples", []):
        at = _seconds(sample.get("at"))
        if at is None:
            continue
        total = _number((sample.get("counters") or {}).get("total"))
        key = sample.get("session")
        if key in sessions and 0 <= now - at <= 3600:
            sessions[key]["last_hour"] += total
        task, confidence = _attribution(sample, evs, at)
        accounting[confidence] += total
        kind = str(sample.get("kind") or "unknown")
        day = datetime.fromtimestamp(at, timezone.utc).date().isoformat()
        drow = daily.setdefault(day, {}).setdefault(kind, {"total": 0, "attributed": 0})
        drow["total"] += total
        if confidence in ("exact", "medium"):
            drow["attributed"] += total
            row = tasks.setdefault(task, {"by_kind": {"claude": 0, "codex": 0, "muse": 0},
                                          "exact": 0, "medium": 0, "total": 0, "_models": {}})
            row["by_kind"][kind] = row["by_kind"].get(kind, 0) + total
            row[confidence] += total
            row["total"] += total
            model = str(sample.get("model") or "")
            model_key = f"{kind}\x1f{model}"
            model_row = row["_models"].setdefault(model_key, {"kind": kind, "model": model,
                                                               "counters": _blank()})
            _add(model_row["counters"], sample.get("counters") or {})
    indexed = sum(accounting.values())
    attributed = accounting["exact"] + accounting["medium"]
    coverage = round(100 * attributed / indexed) if indexed else None
    for row in tasks.values():
        row["coverage_pct"] = coverage
        row["approximate"] = bool(row["medium"] or (coverage is not None and coverage < 100) or
                                  not (state.get("last_cycle") or {}).get("index_complete"))
    days = []
    for offset in range(13, -1, -1):
        day = datetime.fromtimestamp(now - offset * 86400, timezone.utc).date().isoformat()
        kinds = daily.get(day, {})
        total = sum(x["total"] for x in kinds.values())
        attr = sum(x["attributed"] for x in kinds.values())
        days.append({"day": day, "kinds": kinds, "total": total,
                     "coverage_pct": round(100 * attr / total) if total else None})
    return {"updated_at": state.get("updated_at"), "sessions": sessions, "tasks": tasks,
            "accounting": dict(accounting, total=indexed, attributed=attributed, coverage_pct=coverage),
            "daily": days, "collector": state.get("last_cycle") or {}}


def context_window(model: str | None, cfg) -> int:
    if model:
        from .costs import matching_rate
        rate = matching_rate(str(model), cfg)
        if rate and _number(getattr(rate, "context_window", 0)):
            return _number(rate.context_window)
        lower = str(model).lower()
        if "claude" in lower:
            return 200000
    return 0


def decorate_sessions(rows: list[dict], summary: dict) -> None:
    by_native = {(v.get("kind"), str(v.get("native_id"))): v for v in summary.get("sessions", {}).values()}
    for row in rows:
        usage = by_native.get((row.get("kind"), str(row.get("native_id"))))
        if usage:
            row["tokens"] = usage
        for child in row.get("child_runs") or []:
            child_usage = by_native.get((child.get("kind"), str(child.get("native_id"))))
            if child_usage:
                child["tokens"] = child_usage


def apply_task_usage(views, summary: dict, cfg) -> None:
    for view in views:
        local = summary.get("tasks", {}).get(view.entity_id)
        if local:
            view.fields["local_usage"] = {k: v for k, v in local.items() if not k.startswith("_")}
            models = list((local.get("_models") or {}).values())
            view.fields["local_spend"] = estimate_many(models, cfg)
        else:
            view.fields["local_usage"] = {"by_kind": {"claude": 0, "codex": 0, "muse": 0},
                                           "total": 0, "coverage_pct": summary.get("accounting", {}).get("coverage_pct"),
                                           "approximate": True}
            view.fields["local_spend"] = {"available": False, "label": "cost unavailable",
                                            "reason": "no attributable local usage"}


def estimate_many(rows: list[dict], cfg) -> dict:
    from .costs import estimate
    estimates = [estimate(row.get("model"), row.get("counters") or {}, cfg, kind=row.get("kind")) for row in rows]
    known = [row for row in estimates if row.get("available")]
    if not known or len(known) != len(estimates):
        return {"available": False, "label": "cost unavailable",
                "reason": "one or more model rates are not configured"}
    currencies = {row.get("currency") for row in known}
    if len(currencies) != 1:
        return {"available": False, "label": "cost unavailable", "reason": "rates use mixed currencies"}
    amount = sum(float(row["amount"]) for row in known)
    return {"available": True, "kind": "estimate", "amount": round(amount, 6),
            "currency": next(iter(currencies)), "label": f"estimated {next(iter(currencies))} {amount:.2f}",
            "rate_versions": sorted({row.get("rate_version") for row in known})}


def apply_advice(rows: list[dict], views, *, now: float | None = None) -> None:
    now = time.time() if now is None else now
    by_task = {view.entity_id: view for view in views}
    for row in rows:
        if row.get("is_summary") or row.get("is_actor"):
            continue
        native, stable = row.get("native_id"), row.get("session_key")
        owned = [v.entity_id for v in views if v.fields.get("group") != "DONE" and
                 v.fields.get("owner_session") in (native, stable)]
        focused = [by_task[t] for t in row.get("tasks") or [] if t in by_task]
        syncs = {v.fields.get("sync") for v in focused}
        unpushed = True if syncs & {"HEAD≠SERVER", "IMPORTING", "STALE_VALID"} else \
            False if syncs and syncs <= {"OK", "OK·doc"} else None
        last = _seconds(row.get("last_activity_at")) or _seconds(row.get("status_since"))
        idle = max(0, now - last) if last is not None else None
        pressure = ((row.get("tokens") or {}).get("context") or {}).get("pressure_pct")
        status = str(row.get("status") or "unknown").lower()
        restart = row.get("restart") or {}
        thresholds = {"watch_context_pct": 75, "rotate_context_pct": 90,
                      "watch_idle_minutes": 60, "rotate_idle_minutes": 180,
                      "permission_minutes": 15}
        if status.startswith("waiting") and idle is not None and idle >= 15 * 60:
            advice = {"state": "unblock", "reason": f"waiting for permission {round(idle / 3600, 1):g}h",
                      "action": "answer the permission request; never rotate while input is pending"}
        elif unpushed is True:
            advice = {"state": "keep", "reason": "focus task has local/server drift to preserve",
                      "action": "push or hand off the work before rotating"}
        elif restart.get("needed"):
            advice = {"state": "watch", "reason": str(restart.get("reason") or "hooks are missing"),
                      "action": str(restart.get("command") or "resume the session to load hooks")}
        elif pressure is not None and pressure >= 90 and not owned:
            task = (row.get("tasks") or ["<task>"])[0]
            idle_text = f", idle {round(idle / 3600, 1):g}h" if idle is not None and idle >= 3600 else ""
            safe = ", nothing unpushed" if unpushed is False else ""
            advice = {"state": "rotate", "reason": f"{pressure}% context{idle_text}{safe}",
                      "action": f"start a fresh session and hand over with `board claim {task} --to`"}
        elif pressure is not None and pressure >= 75:
            advice = {"state": "watch", "reason": f"{pressure}% context" +
                      (f", owns {len(owned)} active task(s)" if owned else ""),
                      "action": "finish a checkpoint and prepare a handoff before 90%"}
        elif idle is not None and idle >= 3 * 3600 and not owned and unpushed is False:
            task = (row.get("tasks") or ["<task>"])[0]
            advice = {"state": "rotate", "reason": f"idle {round(idle / 3600, 1):g}h, nothing unpushed",
                      "action": f"start a fresh session and hand over with `board claim {task} --to`"}
        elif idle is not None and idle >= 3600:
            advice = {"state": "watch", "reason": f"idle {round(idle / 3600, 1):g}h" +
                      (f", owns {len(owned)} active task(s)" if owned else ""),
                      "action": "keep if its context is still useful; otherwise hand off safely"}
        else:
            context = f"{pressure}% context" if pressure is not None else "context unavailable"
            advice = {"state": "keep", "reason": context +
                      (f", owns {len(owned)} active task(s)" if owned else ", recently active"),
                      "action": "continue; no automatic action will be taken"}
        advice["thresholds"] = thresholds
        row["advice"] = advice

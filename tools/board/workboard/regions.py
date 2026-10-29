"""Canonical dashboard regions and source-generation fingerprints.

The live server keeps these documents in memory.  Region bodies deliberately do
not contain a build timestamp: a strong ETag is the SHA-256 of the exact
canonical JSON bytes returned to the browser.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote


NAMES = ("summary", "board", "team", "activity", "stats")

# Inputs which can change each region.  A changed input permits a rebuild; the
# canonical-content comparison still keeps the old document and ETag when the
# resulting bytes are identical.
REGION_INPUTS = {
    "summary": ("codimango", "git", "ledger", "presence"),
    "board": ("codimango", "git", "ledger", "presence", "usage"),
    "team": ("ledger", "registry_runs", "presence", "usage"),
    "activity": ("ledger", "presence"),
    "stats": ("codimango", "git", "ledger", "usage", "facts", "registry_runs", "presence"),
}

DETAIL_KEYS = {
    "validation", "decisions", "versions", "changed", "gates", "agent_reviews",
    "legacy", "findings", "steps", "checks", "last_check", "online_usage", "local_spend",
}

ROW_KEYS = {
    "task", "group", "next", "age_level", "owner", "valid", "sync", "tag", "status_raw", "validated",
    "age_label", "ownership_state", "owner_last_at", "kind", "vp", "vsum", "older_results",
    "entered_pool_at", "review_history_stale",
    "local_usage", "primary", "category",
}

WIRE_KEYS = {
    "group": "g", "next": "n", "age_level": "al", "owner": "o", "valid": "v",
    "sync": "s", "tag": "tg", "status_raw": "sr", "validated": "vd",
    "age_label": "ag", "ownership_state": "os", "owner_last_at": "oa",
    "kind": "k", "vp": "vp", "vsum": "vs", "older_results": "old",
    "entered_pool_at": "ep", "review_history_stale": "rhs", "state_since": "ss", "assignment": "ax",
    "activity": "ac", "pipeline": "pp", "last_push": "lp", "gate_summary": "gs", "rsum": "rs", "primary": "pa", "category": "cat",
    "revision_count": "rc", "latest_decision": "ld", "finding_codes": "fc", "sync_summary": "sy",
    "tags": "ta", "legacy_summary": "lg", "kind_line": "kl", "detail_version": "dv", "row_version": "rv",
    "local_usage": "lu",
}
WIRE_KEYS_REVERSE = {short: long for long, short in WIRE_KEYS.items()}


def canonical_bytes(value) -> bytes:
    """The one wire representation used for hashing and HTTP responses."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      default=str).encode("utf-8")


def strong_etag(body: bytes) -> str:
    return '"' + hashlib.sha256(body).hexdigest() + '"'


def _hash(value) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _stat(path: Path):
    try:
        st = path.stat()
        return (str(path), st.st_mtime_ns, st.st_size)
    except OSError:
        return (str(path), None, None)


def _tree_stamp(paths) -> str:
    return _hash(sorted(_stat(Path(path)) for path in paths))


def _git_head(path: Path) -> str:
    """Read a normal Git HEAD without invoking Git; fall back to its stat."""
    dot = path / ".git"
    try:
        raw = (dot / "HEAD").read_text().strip()
        if raw.startswith("ref: "):
            ref = dot / raw[5:]
            try:
                return ref.read_text().strip()
            except OSError:
                packed = dot / "packed-refs"
                for line in packed.read_text().splitlines():
                    if line and not line.startswith(("#", "^")) and line.split(" ", 1)[-1] == raw[5:]:
                        return line.split(" ", 1)[0]
        return raw
    except OSError:
        return _hash(_stat(dot / "HEAD"))


def _recent_codex_files(root: Path, limit: int = 240) -> list[Path]:
    """Bounded metadata scan; discovery only runs when this generation changes."""
    if not root.is_dir():
        return []
    # Day directories are shallow and bounded in normal Codex layouts.  Avoid a
    # recursive walk over historical rollouts.
    days = []
    try:
        for year in root.iterdir():
            if year.is_dir() and year.name.isdigit():
                for month in year.iterdir():
                    if month.is_dir():
                        days.extend(day for day in month.iterdir() if day.is_dir())
    except OSError:
        return []
    out = []
    for day in sorted(days, reverse=True)[:8]:
        try:
            out.extend(day.glob("*.jsonl"))
        except OSError:
            continue
    return sorted(out, key=lambda p: _stat(p)[1] or 0, reverse=True)[:limit]


def source_generations(cfg, *, cache: Path | None = None, state: Path | None = None) -> dict[str, str]:
    """Cheap, read-only generations for every input used by live regions."""
    from . import app as app_mod, sync as sync_mod
    from .sources import agent_runs, claude_sessions

    cache = Path(cache or os.environ.get("WORKBOARD_CACHE", "~/.cache/workboard")).expanduser()
    state = Path(state or os.environ.get("WORKBOARD_STATE", "~/.local/share/workboard")).expanduser()
    ledger = Path(cfg.ledger.path).expanduser()

    codimango = _tree_stamp([cache / "codimango-last-good.json"])
    git = _tree_stamp([cache / app_mod.GIT_STAMP])
    ledger_gen = _git_head(ledger) if ledger.is_dir() else _hash(_stat(ledger))

    registry = []
    try:
        registry = list(Path(claude_sessions.REGISTRY).glob("*.json"))
    except OSError:
        pass
    runs = _recent_codex_files(Path(agent_runs.CODEX).expanduser())
    runs += [Path(agent_runs.MUSE_DB).expanduser()]
    # Parent-link evidence changes when an active Claude transcript changes.  We
    # inspect only transcripts named by registry records rather than the whole tree.
    projects = Path(agent_runs.CLAUDE_PROJECTS).expanduser()
    native_ids = []
    for path in registry:
        try:
            row = json.loads(path.read_text())
            if isinstance(row.get("sessionId"), str):
                native_ids.append(row["sessionId"])
        except (OSError, ValueError, AttributeError):
            continue
    if projects.is_dir():
        for native_id in native_ids:
            runs.extend(projects.glob(f"*/{native_id}.jsonl"))
            runs.extend(projects.glob(f"*/{native_id}/subagents/*.jsonl"))
    registry_runs = _tree_stamp(registry + runs)

    event_files = app_mod.ledger_event_files(cfg)
    presence = _tree_stamp(event_files + [state / "spool.jsonl"])
    usage = _tree_stamp([cache / "usage-v1.json"])
    facts = _tree_stamp([cache / "facts" / "facts-v1.jsonl", cache / "facts" / "facts-state.json"])
    return {"codimango": codimango, "git": git, "ledger": ledger_gen,
            "registry_runs": registry_runs, "presence": presence, "usage": usage, "facts": facts}


def _state_since(task: dict, now) -> str | None:
    seconds = task.get("state_age_s")
    if seconds is None or now is None:
        return None
    try:
        return (now - timedelta(seconds=max(0, int(seconds)))).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError):
        return None


def _compact_gate(gate: dict) -> dict:
    out = {}
    for role in ("author", "independent"):
        value = gate.get(role) or {}
        check = value.get("check") or {"state": "none"}
        review = value.get("review") or {"state": "none"}
        out[role] = {
            "check": {k: check.get(k) for k in ("state", "fail", "warn", "at", "summary", "older_run", "provisional")
                      if check.get(k) is not None},
            "review": {k: review.get(k) for k in ("state",)
                       if review.get(k) is not None},
        }
    return out


def compact_task(task: dict, *, now=None, detail_version: str | None = None) -> dict:
    """Board row + hover facts, without drawer-sized arrays."""
    row = {k: v for k, v in task.items() if k in ROW_KEYS and v is not None}
    row.pop("state_age_s", None)
    row["state_since"] = _state_since(task, now)
    assignment, activity, pipeline, last_push = (task.get("assignment") or {}, task.get("activity") or {},
                                                 task.get("pipeline") or {}, task.get("last_push") or {})
    row["assignment"] = {k: assignment.get(k) for k in ("state", "owner", "reason") if assignment.get(k) is not None}
    row["activity"] = {k: activity.get(k) for k in ("state", "last_at", "reason", "aliases") if activity.get(k) is not None}
    row["pipeline"] = {k: pipeline.get(k) for k in ("state", "since", "reason") if pipeline.get(k) is not None}
    row["last_push"] = {k: last_push.get(k) for k in ("at", "time_kind", "session_alias") if last_push.get(k) is not None}
    row["gate_summary"] = _compact_gate((task.get("rsum") or {}).get("gates") or task.get("gates") or {})
    summary = task.get("rsum") or {}
    row["rsum"] = {k: summary.get(k) for k in ("agent", "agent_current", "agent_green", "human")
                   if summary.get(k) is not None}
    decisions = task.get("decisions") or []
    row["revision_count"] = sum(d.get("kind") == "revision" for d in decisions)
    latest = decisions[-1] if decisions else None
    row["latest_decision"] = ({k: latest.get(k) for k in ("kind", "at", "reason") if latest.get(k) is not None}
                              if latest else None)
    row["finding_codes"] = [f.get("code") for f in (task.get("findings") or []) if f.get("code")]
    sync_finding = next((f for f in (task.get("findings") or []) if f.get("code") == "HEAD≠SERVER"), None)
    row["sync_summary"] = (sync_finding or {}).get("summary")
    category = task.get("category") or {}
    track = "multi-turn" if "multi" in (task.get("track") or "") else "single-turn" if task.get("track") else ""
    row["kind_line"] = " · ".join(filter(None, [f"SWE-bench {track}" if track else "",
        str(category.get("category") or "").replace("_", " "),
        str(category.get("subdomain") or "").replace("_", " "),
        "/".join(category.get("languages") or []), category.get("difficulty")]))
    row["tags"] = [{k: tag.get(k) for k in ("k", "label", "why") if tag.get(k) is not None}
                   for tag in (task.get("tags") or [])]
    legacy = task.get("legacy") or {}
    if legacy:
        row["legacy_summary"] = {k: legacy.get(k) for k in ("legacy_owner", "status", "updated")
                                 if legacy.get(k) is not None}
    # Drawer-only changes must invalidate an open drawer, but the detail hash
    # itself is not useful row/hover content and need not cross the wire.
    if detail_version:
        row["_detail_version"] = detail_version[:16]
    raw = canonical_bytes(row)
    row.pop("_detail_version", None)
    row["row_version"] = hashlib.sha256(raw).hexdigest()[:16]
    return {WIRE_KEYS.get(key, key): _encode_nested(key, value) for key, value in row.items() if value is not None}


def _encode_nested(key: str, value):
    if key == "vsum":
        return [value.get("passed", 0), value.get("total", 0),
                [[i.get("severity"), i.get("check"), i.get("why")] for i in value.get("issues") or []],
                value.get("skipped") or [], [[i.get("check"), i.get("why")] for i in value.get("info") or []]]
    if key == "gate_summary":
        return {role[0]: [(value.get(role) or {}).get("check", {}).get(k) for k in ("state", "fail", "warn")] +
                         [(value.get(role) or {}).get("review", {}).get("state")] +
                         [(value.get(role) or {}).get("check", {}).get(k) for k in ("at", "summary")]
                for role in ("author", "independent")}
    if key == "tags":
        return [[item.get("k"), item.get("label"), item.get("why")] for item in value]
    if key == "assignment":
        return [value.get("state"), value.get("owner"), value.get("reason")]
    if key in ("activity", "pipeline"):
        return [value.get("state"), value.get("last_at") if key == "activity" else value.get("since"),
                value.get("reason")]
    if key == "last_push":
        return [value.get("at"), value.get("session_alias"), value.get("time_kind")]
    if key == "rsum":
        return [value.get("agent"), value.get("agent_current"), value.get("agent_green"), value.get("human")]
    if key == "latest_decision" and value:
        return [value.get("kind"), value.get("at"), (value.get("reason") or "")[:140]]
    if key == "local_usage":
        kinds = value.get("by_kind") or {}
        return [kinds.get("claude", 0), kinds.get("codex", 0), kinds.get("muse", 0),
                value.get("total", 0), value.get("coverage_pct"), bool(value.get("approximate"))]
    return value


def expand_task(row: dict) -> dict:
    out = {WIRE_KEYS_REVERSE.get(key, key): value for key, value in row.items()}
    if isinstance(out.get("vsum"), list):
        passed, total, issues, skipped, info = out["vsum"]
        out["vsum"] = {"passed": passed, "total": total,
                       "issues": [{"severity": x[0], "check": x[1], "why": x[2]} for x in issues],
                       "skipped": skipped, "info": [{"check": x[0], "why": x[1]} for x in info]}
    if isinstance(out.get("gate_summary"), dict) and "a" in out["gate_summary"]:
        out["gate_summary"] = {role: {"check": {"state": values[0], "fail": values[1], "warn": values[2],
                                                      "at": values[4], "summary": values[5]},
                                             "review": {"state": values[3]}}
                               for role, values in (("author", out["gate_summary"].get("a", [])),
                                                    ("independent", out["gate_summary"].get("i", [])))}
    if isinstance(out.get("tags"), list):
        out["tags"] = [{"k": x[0], "label": x[1], "why": x[2]} for x in out["tags"]]
    if isinstance(out.get("assignment"), list):
        out["assignment"] = dict(zip(("state", "owner", "reason"), out["assignment"]))
    elif isinstance(out.get("assignment"), str):
        out["assignment"] = {"state": out["assignment"]}
    for key, stamp in (("activity", "last_at"), ("pipeline", "since")):
        if isinstance(out.get(key), list):
            out[key] = {"state": out[key][0], stamp: out[key][1], "reason": out[key][2]}
    if isinstance(out.get("last_push"), list):
        out["last_push"] = dict(zip(("at", "session_alias", "time_kind"), out["last_push"]))
    if isinstance(out.get("rsum"), list):
        out["rsum"] = dict(zip(("agent", "agent_current", "agent_green", "human"), out["rsum"]))
    if isinstance(out.get("latest_decision"), list):
        out["latest_decision"] = dict(zip(("kind", "at", "reason"), out["latest_decision"]))
    if isinstance(out.get("local_usage"), list):
        values = out["local_usage"]
        out["local_usage"] = {"by_kind": {"claude": values[0], "codex": values[1], "muse": values[2]},
                              "total": values[3], "coverage_pct": values[4], "approximate": values[5]}
    return out


def pack_board(rows: list[dict]) -> dict:
    preferred = ["task", *WIRE_KEYS.values()]
    present = {key for row in rows for key in row}
    fields = [key for key in preferred if key in present]
    fields += sorted(present - set(fields))
    return {"fields": fields, "rows": [[row.get(key) for key in fields] for row in rows]}


def unpack_board(data: dict) -> list[dict]:
    if "tasks" in data:                       # transitional/tests and static compatibility
        return list(data.get("tasks") or [])
    fields = data.get("fields") or []
    return [dict(zip(fields, values)) for values in (data.get("rows") or [])]


def task_detail(task: dict) -> dict:
    """Full lazy drawer representation.  Additive row fields aid old clients."""
    detail = dict(task)
    detail["findings_detail"] = detail.get("findings") or []
    detail["gates_detail"] = detail.get("gates") or {}
    return detail


def _without_relative_ages(value):
    if isinstance(value, list):
        return [_without_relative_ages(item) for item in value]
    if not isinstance(value, dict):
        return value
    volatile = {"age_s", "ago_s", "status_ago_s", "last_sync_ago_s", "last_activity_ago_s",
                "checkin_ago_s", "snapshot_age_s"}
    return {key: _without_relative_ages(item) for key, item in value.items() if key not in volatile}


def compact_region(name: str, data: dict) -> dict:
    """Normalize region content so elapsed clocks cannot churn its ETag."""
    return _without_relative_ages(data) if name == "team" else data


def split_payload(full: dict, *, now=None, names=None) -> tuple[dict[str, dict], dict[str, dict]]:
    wanted = set(NAMES if names is None else names)
    details = {}
    rows = []
    if "board" in wanted:
        for task in full.get("tasks") or []:
            detail = task_detail(task)
            detail_body = canonical_bytes(detail)
            version = hashlib.sha256(detail_body).hexdigest()
            detail["detail_version"] = version
            details[task["task"]] = detail
            rows.append(compact_task(task, now=now, detail_version=version))
    regions = {}
    if "summary" in wanted:
        regions["summary"] = {k: full.get(k) for k in
                              ("codimango_at", "health", "ledger_ok", "ledger_at", "week",
                               "codimango_detail", "refresh_error")}
    if "board" in wanted:
        regions["board"] = pack_board(rows)
    if "team" in wanted:
        regions["team"] = compact_region("team", {k: full.get(k) for k in
                                                   ("servers", "messages", "sessions", "session_targets", "task_targets")})
    if "activity" in wanted:
        regions["activity"] = {"items": full.get("feed") or []}
    if "stats" in wanted:
        regions["stats"] = {k: full.get(k) for k in ("s2", "weekly", "funnel", "flow", "ages", "load",
                                                              "token_daily", "token_accounting", "usage_collector")}
    return regions, details


@dataclass(frozen=True)
class Document:
    data: dict
    body: bytes
    etag: str
    basis: tuple

    @classmethod
    def make(cls, data: dict, basis=()):
        body = canonical_bytes(data)
        return cls(data, body, strong_etag(body), tuple(basis))


class RegionCache:
    """Atomically replace coherent region/detail snapshots."""

    def __init__(self, full: dict, *, now=None, generations=None):
        self._lock = threading.RLock()
        self._docs: dict[str, Document] = {}
        self._details: dict[str, Document] = {}
        self._generations = dict(generations or {})
        self._builds = {name: 0 for name in NAMES}
        self.replace(full, now=now, generations=self._generations, force=True)

    @staticmethod
    def _basis(name: str, generations: dict) -> tuple:
        return tuple((key, generations.get(key)) for key in REGION_INPUTS[name])

    def replace(self, full: dict, *, now=None, generations=None, force: bool = False):
        generations = dict(generations or {})
        with self._lock:
            dirty = [name for name in NAMES if force or name not in self._docs or
                     self._docs[name].basis != self._basis(name, generations)]
            if not dirty:
                self._generations = generations
                return
            region_data, details = split_payload(full, now=now, names=dirty)
            docs = dict(self._docs)
            for name in dirty:
                basis = self._basis(name, generations)
                old = docs.get(name)
                candidate = Document.make(region_data[name], basis)
                self._builds[name] += 1
                docs[name] = old if old is not None and old.body == candidate.body else candidate
                if docs[name] is old and old.basis != basis:
                    docs[name] = Document(old.data, old.body, old.etag, basis)
            detail_docs = self._details
            if "board" in dirty:
                detail_docs = {}
                for task, detail in details.items():
                    candidate = Document.make(detail, self._basis("board", generations))
                    old = self._details.get(task)
                    detail_docs[task] = old if old is not None and old.body == candidate.body else candidate
            self._docs, self._details, self._generations = docs, detail_docs, generations

    def replace_selected(self, data: dict[str, dict], *, generations: dict, force: bool = False):
        """Atomically update fast regions (Team/activity) without rebuilding task projections."""
        with self._lock:
            docs = dict(self._docs)
            for name, value in data.items():
                if name not in NAMES:
                    continue
                basis = self._basis(name, generations)
                old = docs.get(name)
                if not force and old is not None and old.basis == basis:
                    continue
                candidate = Document.make(compact_region(name, value), basis)
                self._builds[name] += 1
                docs[name] = old if old is not None and old.body == candidate.body else candidate
                if docs[name] is old and old.basis != basis:
                    docs[name] = Document(old.data, old.body, old.etag, basis)
            self._docs, self._generations = docs, dict(generations)

    def region(self, name: str) -> Document | None:
        with self._lock:
            return self._docs.get(name)

    def detail(self, task: str) -> Document | None:
        with self._lock:
            return self._details.get(task)

    def etags(self) -> dict[str, str]:
        with self._lock:
            return {name: doc.etag for name, doc in self._docs.items()}

    def bootstrap(self) -> dict:
        with self._lock:
            out = dict(self._docs["summary"].data)
            out.update(self._docs["board"].data)
            out.update({"servers": [], "messages": [], "sessions": [], "session_targets": [],
                        "task_targets": {}, "feed": [], "weekly": [], "funnel": {}, "flow": {},
                        "ages": {}, "load": {}, "token_daily": [], "token_accounting": {},
                        "usage_collector": {},
                        # Only preloaded regions may be conditionally fetched.  Lazy regions
                        # need one 200 response before their ETag is useful to the page.
                        "_etags": {name: self._docs[name].etag for name in ("summary", "board")}})
            return out

    def compatibility(self) -> dict:
        """Assemble the historical /data.json shape from one locked region snapshot."""
        with self._lock:
            out = {}
            for name in NAMES:
                data = self._docs[name].data
                if name == "activity":
                    out["feed"] = data.get("items") or []
                else:
                    out.update(data)
            out["tasks"] = [dict(expand_task(row), **(self._details[row["task"]].data
                                                       if row["task"] in self._details else {}))
                            for row in unpack_board(self._docs["board"].data)]
            return out

    @property
    def build_counts(self):
        with self._lock:
            return dict(self._builds)


def quoted_task(task: str) -> str:
    return quote(task, safe="")

"""Facts: an append-only, local history of task transitions, so Stats survives what Codimango overwrites.

One JSON line per observed fact in ~/.cache/workboard/facts/facts-v1.jsonl. A deterministic id makes a repeated
observation a no-op. Sources:
- the Codimango snapshot (status / validation / generation / commit changes, observed on each sync),
- the personal October snapshots (~/swebench/task-snapshots, interval-censored: "changed between A and B"),
- structured human reviews (`task reviews --full --all-pages --json`): every decision with its exact time, so an
  acceptance stays counted after the task is archived,
- comment system events (`task comments --json`): "Task was submitted for review (vN.0)" gives every submission
  and resubmission exactly; "Reviewer claimed" gives review start. Other events are not transitions.
`occurred_at` is when it happened (null when only an interval is known); `observed_at` is when the board saw it.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
FILE = "facts-v1.jsonl"
STATE = "facts-state.json"
SNAP_KEYS = ("status", "validation_status", "validation_generation", "commit_sha")
SUBMIT = re.compile(r"^\s*Task was submitted for review \(v(\d+)(?:\.\d+)?\)", re.I)
CLAIMED = re.compile(r"^\s*Reviewer claimed\b", re.I)
SUBMIT_RULES = "submit-events-v1"
DECISIONS = {"accept": "accept", "accepted": "accept", "approve": "accept", "revision": "revision",
             "reject": "reject", "rejected": "reject"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fact_id(*parts) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:32]


def make(task, kind, value, source, source_id, *, occurred_at=None, interval=None, commit=None, generation=None,
         confidence="exact", parser="", evidence=None, observed_at=None) -> dict:
    return {"schema": SCHEMA, "id": fact_id(source, source_id, task, kind, occurred_at or interval, value),
            "task": task, "kind": kind, "value": value, "source": source, "source_id": source_id,
            "occurred_at": occurred_at, "observed_at": observed_at or _now(), "interval": interval,
            "commit": commit, "generation": generation, "confidence": confidence, "parser": parser,
            "evidence": evidence or {}}


class Store:
    """Append-only JSONL with an in-memory id index; a torn last line is skipped, never fatal."""

    def __init__(self, cache_dir: Path):
        self.dir = Path(cache_dir) / "facts"
        self.path = self.dir / FILE
        self._ids: set[str] | None = None

    def read(self) -> list[dict]:
        out = []
        try:
            with open(self.path, "rb") as fh:
                for raw in fh:
                    try:
                        row = json.loads(raw)
                    except ValueError:
                        continue
                    if isinstance(row, dict) and row.get("schema") == SCHEMA and row.get("task"):
                        out.append(row)
        except OSError:
            pass
        return out

    def ids(self) -> set[str]:
        if self._ids is None:
            self._ids = {r["id"] for r in self.read()}
        return self._ids

    def append(self, facts: list[dict]) -> int:
        new = [f for f in facts if f["id"] not in self.ids()]
        if not new:
            return 0
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.dir / (FILE + ".lock"), "a") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            self._ids = None                                  # another writer may have appended meanwhile
            new = [f for f in new if f["id"] not in self.ids()]
            if new:
                with open(self.path, "ab") as fh:
                    if fh.tell() and not self._ends_with_newline():
                        fh.write(b"\n")                        # repair a torn tail before appending
                    fh.write("".join(json.dumps(f, sort_keys=True) + "\n" for f in new).encode())
                    fh.flush()
                    os.fsync(fh.fileno())
                self._ids |= {f["id"] for f in new}
        return len(new)

    def _ends_with_newline(self) -> bool:
        try:
            with open(self.path, "rb") as fh:
                fh.seek(-1, os.SEEK_END)
                return fh.read(1) == b"\n"
        except OSError:
            return True


def _load_state(store: Store) -> dict:
    try:
        return json.loads((store.dir / STATE).read_text())
    except (OSError, ValueError):
        return {}


def _save_state(store: Store, state: dict) -> None:
    store.dir.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=store.dir, prefix=".state-")
    with os.fdopen(fd, "w") as fh:
        json.dump(state, fh)
    os.replace(tmp, store.dir / STATE)


# ------------------------------------------------------------------------------------------------ snapshot
def observe_snapshot(store: Store, rows: list[dict], fetched_at: str | None = None) -> int:
    """Append one fact per changed field of each Codimango row since the last observation."""
    state = _load_state(store)
    last = state.setdefault("snapshot", {})
    at = fetched_at or _now()
    out = []
    for r in rows:
        name = r.get("name")
        if not name:
            continue
        prev = last.get(name, {})
        cur = {k: r.get(k) for k in SNAP_KEYS}
        if r.get("archived_at") or r.get("status") == "archived":
            cur["status"] = "archived"
        for k in SNAP_KEYS:
            if cur[k] is not None and cur[k] != prev.get(k):
                kind = {"status": "status", "validation_status": "validation", "validation_generation": "generation",
                        "commit_sha": "commit"}[k]
                exact = None
                if k == "status" and not prev:                  # first sight: the source timestamp, when it has one
                    exact = r.get("reviewed_at") if cur[k] in ("accepted", "used_in_training", "needs_revision") else None
                out.append(make(name, kind, {kind: cur[k]}, "codimango_snapshot", f"{name}|{k}|{cur[k]}|{at}",
                                occurred_at=exact, interval=None if exact else {"after": prev.get("_at"), "at_or_before": at},
                                commit=r.get("commit_sha"), generation=r.get("validation_generation"),
                                confidence="exact" if exact else "interval_censored", parser="snapshot-v1",
                                evidence={"updated_at": r.get("updated_at")}, observed_at=at))
        cur["_at"] = at
        last[name] = cur
    n = store.append(out)
    _save_state(store, state)
    return n


def seed_personal_snapshots(store: Store, folder: Path) -> int:
    """One-time import of the irregular personal snapshots as interval-censored status/validation facts."""
    state = _load_state(store)
    done = set(state.get("seeded", []))
    files = sorted(p for p in Path(folder).expanduser().glob("????-??-??.json") if p.name not in done)
    if not files:
        return 0
    prev_obs: dict[str, dict] = state.get("seed_prev", {})
    out = []
    for p in files:
        try:
            data = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        at = p.stem + "T23:59:59+00:00"
        for name, row in (data.items() if isinstance(data, dict) else []):
            if not isinstance(row, dict):
                continue
            before = prev_obs.get(name, {})
            for key, kind in (("status", "status"), ("valid", "validation")):
                val = row.get(key)
                if val and val != before.get(key):
                    out.append(make(name, kind, {kind: val}, "personal_snapshot", f"{p.name}|{name}|{key}",
                                    interval={"after": before.get("_at"), "at_or_before": at},
                                    commit=row.get("sha"), confidence="interval_censored", parser="snapshot-v1",
                                    evidence={"file": p.name}, observed_at=at))
            prev_obs[name] = {"status": row.get("status"), "valid": row.get("valid"), "_at": at}
        done.add(p.name)
    n = store.append(out)
    state["seeded"], state["seed_prev"] = sorted(done), prev_obs
    _save_state(store, state)
    return n


# --------------------------------------------------------------------------------------- reviews + comments
def parse_reviews(task: str, doc: dict) -> list[dict]:
    out = []
    complete = bool(doc.get("complete")) and not doc.get("hasMore")
    for rv in doc.get("reviews") or []:
        kind = DECISIONS.get(str(rv.get("decision") or "").lower(), "other")
        if rv.get("autoAccepted") or rv.get("isAutoAccepted"):
            kind = "atr_accept" if kind == "accept" else kind
        at = rv.get("reviewedAt")
        if not at:
            continue
        reason = re.sub(r"\s+", " ", str(rv.get("decisionReason") or "")).strip()[:180] or None
        out.append(make(task, "review_decision", {"decision": kind, "reason": reason}, "codimango_reviews",
                        str(rv.get("id") or at), occurred_at=at, commit=rv.get("commitSha"), parser="reviews-v1",
                        evidence={"page_complete": complete}))
    out.sort(key=lambda f: f["occurred_at"])
    for i, f in enumerate([f for f in out if f["value"]["decision"] in ("revision", "accept", "atr_accept", "reject")]):
        f["value"]["round"] = i + 1
        f["id"] = fact_id(f["source"], f["source_id"], task, f["kind"], f["occurred_at"], f["value"])
    return out


def parse_comments(task: str, doc: dict) -> list[dict]:
    out = []
    for c in doc.get("comments") or []:
        if not c.get("isSystemEvent") or c.get("deletedAt"):
            continue
        body, at = str(c.get("body") or ""), c.get("createdAt")
        if not at:
            continue
        m = SUBMIT.match(body)
        if m:
            v = int(m.group(1))
            out.append(make(task, "submission", {"event": "first_submit" if v == 1 else "resubmit", "version": v,
                                                 "rule": "submitted-vN"}, "codimango_comments", str(c.get("id")),
                            occurred_at=at, commit=c.get("commitSha"), parser=SUBMIT_RULES))
        elif CLAIMED.match(body):
            out.append(make(task, "submission", {"event": "review_claimed", "rule": "reviewer-claimed"},
                            "codimango_comments", str(c.get("id")), occurred_at=at, parser=SUBMIT_RULES))
    return out


def _cli_json(cfg, args, runner, timeout=60):
    try:
        p = runner([cfg.codimango.command, *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout)
    except ValueError:
        return None


def hydrate(cfg, store: Store, rows: list[dict], *, max_tasks: int = 4, wall_s: float = 12.0,
            runner=subprocess.run) -> dict:
    """Fetch structured reviews and comment events for tasks whose updatedAt moved, oldest-stale first.
    Returns {"fetched": n, "pending": m}. Tasks never submitted need no review/comment history."""
    state = _load_state(store)
    keys = state.setdefault("hydrated", {})
    want = [(r["name"], str(r.get("updated_at") or "")) for r in rows
            if r.get("name") and (r.get("entered_pool_at") or r.get("reviewed_at") or r.get("status") in
                                  ("being_reviewed", "needs_reviewers_assigned", "needs_revision", "accepted",
                                   "used_in_training"))]
    stale = [(n, k) for n, k in want if keys.get(n, {}).get("key") != f"{k}|{SUBMIT_RULES}"]
    stale.sort(key=lambda x: keys.get(x[0], {}).get("at", ""))
    start, fetched = time.monotonic(), 0
    for name, key in stale:
        if fetched >= max_tasks or time.monotonic() - start > wall_s:
            break
        rv = _cli_json(cfg, ["task", "reviews", name, "--full", "--all-pages", "--json"], runner)
        cm = _cli_json(cfg, ["task", "comments", name, "--json"], runner)
        if rv is None or cm is None:
            keys[name] = dict(keys.get(name, {}), at=_now(), error=True)
            fetched += 1
            continue
        store.append(parse_reviews(name, rv) + parse_comments(name, cm))
        keys[name] = {"key": f"{key}|{SUBMIT_RULES}", "at": _now(),
                      "complete": bool(rv.get("complete")) and not rv.get("hasMore")}
        fetched += 1
    _save_state(store, state)
    pending = sum(1 for n, k in want if keys.get(n, {}).get("key") != f"{k}|{SUBMIT_RULES}")
    return {"fetched": fetched, "pending": pending, "eligible": len(want),
            "complete": sum(1 for n, _ in want if keys.get(n, {}).get("complete"))}


def coverage(store: Store) -> dict:
    return {k: v for k, v in _load_state(store).items() if k == "hydrated"}

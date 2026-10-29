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

import contextlib
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
STABLE_SOURCES = {"codimango_reviews", "codimango_comments"}   # one source event = one identity; latest version wins
DECISIONS = {"accept": "accept", "accepted": "accept", "approve": "accept", "revision": "revision",
             "reject": "reject", "rejected": "reject"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fact_id(*parts) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:32]


def make(task, kind, value, source, source_id, *, occurred_at=None, interval=None, commit=None, generation=None,
         confidence="exact", parser="", evidence=None, observed_at=None) -> dict:
    ident = (source, source_id, task, kind) if source in STABLE_SOURCES else \
        (source, source_id, task, kind, occurred_at or interval, value)
    return {"schema": SCHEMA, "id": fact_id(*ident, json.dumps(value, sort_keys=True) if source in STABLE_SOURCES else ""),
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
        self._held = False

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

    @contextlib.contextmanager
    def locked(self):
        """One writer at a time for the JSONL and its state file (re-entrant within this Store)."""
        if self._held:
            yield
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.dir / (FILE + ".lock"), "a") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            self._held, self._ids = True, None            # another writer may have appended meanwhile
            try:
                yield
            finally:
                self._held = False

    def append(self, facts: list[dict]) -> int:
        batch = list({f["id"]: f for f in facts}.values())   # duplicates inside one batch count once
        if not batch:
            return 0
        with self.locked():
            new = [f for f in batch if f["id"] not in self.ids()]
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
SNAP_KIND = {"status": "status", "validation_status": "validation", "validation_generation": "generation",
             "commit_sha": "commit"}


def _last_values(rows: list[dict]) -> dict[str, dict]:
    """task -> {kind: (value, observed_at)} from the facts themselves (crash-safe: no separate snapshot state)."""
    out: dict[str, dict] = {}
    for f in rows:
        if f["source"] not in ("codimango_snapshot", "personal_snapshot") or f["kind"] not in SNAP_KIND.values():
            continue
        cur = out.setdefault(f["task"], {}).get(f["kind"])
        if cur is None or f["observed_at"] >= cur[1]:
            out[f["task"]][f["kind"]] = (f["value"].get(f["kind"]), f["observed_at"])
    return out


def observe_snapshot(store: Store, rows: list[dict], fetched_at: str | None = None) -> int:
    """Append one fact per changed field of each Codimango row since the last observation."""
    at = fetched_at or _now()
    with store.locked():
        last = _last_values(store.read())
        state = _load_state(store)
        seen = state.setdefault("seen", {})             # last time each row was observed (only narrows intervals)
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
                kind = SNAP_KIND[k]
                before = prev.get(kind)
                if cur[k] is None or (before and before[0] == cur[k]):
                    continue
                exact = None
                if k == "status" and not before and cur[k] in ("accepted", "used_in_training", "needs_revision"):
                    exact = r.get("reviewed_at")              # first sight: the source's own timestamp
                out.append(make(name, kind, {kind: cur[k]}, "codimango_snapshot", f"{name}|{k}|{cur[k]}|{at}",
                                occurred_at=exact,
                                interval=None if exact else {"after": max(filter(None, (before[1] if before else None,
                                                                                         seen.get(name)))) if (before or seen.get(name)) else None,
                                                             "at_or_before": at},
                                commit=r.get("commit_sha"), generation=r.get("validation_generation"),
                                confidence="exact" if exact else "interval_censored", parser="snapshot-v1",
                                evidence={"updated_at": r.get("updated_at")}, observed_at=at))
            seen[name] = at
        n = store.append(out)
        _save_state(store, state)
        return n


def seed_personal_snapshots(store: Store, folder: Path) -> int:
    """One-time import of the irregular personal snapshots as interval-censored status/validation facts,
    timed by each file's write time (its real capture time), not a guessed end of day."""
    with store.locked():
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
                at = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
            except (OSError, ValueError):
                continue
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
    """One fact per review id; rounds are computed when the history is read (never part of the identity)."""
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
    return sorted(out, key=lambda f: f["occurred_at"])


def parse_comments(task: str, doc: dict) -> list[dict]:
    """Submission transitions from system events. Unmatched system events are kept as `unclassified` (never a
    submission); a deleted event becomes a tombstone so a later read drops the earlier version."""
    out = []
    for c in doc.get("comments") or []:
        if not c.get("isSystemEvent"):
            continue
        body, at, cid = str(c.get("body") or ""), c.get("createdAt"), str(c.get("id"))
        if not at:
            continue
        if c.get("deletedAt"):
            out.append(make(task, "submission", {"event": "deleted"}, "codimango_comments", cid, occurred_at=at,
                            parser=SUBMIT_RULES))
            continue
        m = SUBMIT.match(body)
        if m:
            v = int(m.group(1))
            value = {"event": "first_submit" if v == 1 else "resubmit", "version": v, "rule": "submitted-vN"}
        elif CLAIMED.match(body):
            value = {"event": "review_claimed", "rule": "reviewer-claimed"}
        else:
            value = {"event": "unclassified", "raw_kind": re.sub(r"\s*\([0-9a-f]{6,}\)", "", body)[:60]}
        out.append(make(task, "submission", value, "codimango_comments", cid, occurred_at=at,
                        commit=c.get("commitSha"), parser=SUBMIT_RULES))
    return out


def latest(rows: list[dict], kind: str) -> list[dict]:
    """The current version of each source event of `kind` (edits supersede, tombstones delete)."""
    best: dict[tuple, dict] = {}
    for f in rows:
        if f["kind"] != kind:
            continue
        key = (f["source"], f["source_id"])
        if key not in best or f["observed_at"] >= best[key]["observed_at"]:
            best[key] = f
    return sorted((f for f in best.values() if f["value"].get("event") != "deleted"),
                  key=lambda f: f["occurred_at"] or "")


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


def _wanted(rows: list[dict]) -> list[tuple[str, str]]:
    return [(r["name"], str(r.get("updated_at") or "")) for r in rows
            if r.get("name") and (r.get("entered_pool_at") or r.get("reviewed_at") or r.get("status") in
                                  ("being_reviewed", "needs_reviewers_assigned", "needs_revision", "accepted",
                                   "used_in_training"))]


def hydrate(cfg, store: Store, rows: list[dict], *, max_tasks: int = 4, wall_s: float = 12.0,
            runner=subprocess.run) -> dict:
    """Fetch structured reviews and comment events for tasks whose updatedAt moved, oldest-stale first.
    A task counts as covered only when its last fetch matches the current updatedAt, was complete and did not
    fail; a failed refresh keeps the old facts but marks the task stale."""
    want = _wanted(rows)
    with store.locked():
        state = _load_state(store)
        keys = state.setdefault("hydrated", {})
        stale = [(n, k) for n, k in want if keys.get(n, {}).get("key") != f"{k}|{SUBMIT_RULES}"]
        stale.sort(key=lambda x: (keys.get(x[0], {}).get("at", ""), x[0]))
        start, fetched = time.monotonic(), 0
        for name, key in stale:
            if fetched >= max_tasks or time.monotonic() - start > wall_s:
                break
            rv = _cli_json(cfg, ["task", "reviews", name, "--full", "--all-pages", "--json"], runner)
            cm = _cli_json(cfg, ["task", "comments", name, "--json"], runner)
            fetched += 1
            if rv is None or cm is None:
                keys[name] = dict(keys.get(name, {}), at=_now(), error=True, error_at=_now())
                continue
            store.append(parse_reviews(name, rv) + parse_comments(name, cm))
            keys[name] = {"key": f"{key}|{SUBMIT_RULES}", "at": _now(), "error": False,
                          "complete": bool(rv.get("complete")) and not rv.get("hasMore")}
        _save_state(store, state)
    return coverage(store, rows) | {"fetched": fetched}


def coverage(store: Store, rows: list[dict] | None = None) -> dict:
    """Per-task review/submission history status against the current Codimango rows."""
    keys = _load_state(store).get("hydrated", {})
    want = _wanted(rows or [])
    per = {}
    for name, upd in want:
        k = keys.get(name, {})
        per[name] = {"current": k.get("key") == f"{upd}|{SUBMIT_RULES}", "complete": bool(k.get("complete")),
                     "error": bool(k.get("error"))}
    ok = [n for n, v in per.items() if v["current"] and v["complete"] and not v["error"]]
    return {"eligible": len(want), "covered": len(ok), "pending": sum(1 for v in per.values() if not v["current"]),
            "errors": sum(1 for v in per.values() if v["error"]), "tasks": per}

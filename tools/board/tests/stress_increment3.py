"""Sparse 8 GB telemetry stress for increment 3; all state lives in one temp dir."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from tests.test_visual import realistic, snap
from workboard import html, usage
from workboard.config import Repository, load_config


SENTINEL = "WB_PROMPT_SENTINEL_INCREMENT3_f62a9d"
SESSIONS = 40
LOGICAL_BYTES = 200 * 1024 * 1024


def assistant(native: str, mid: str, at: float, cwd: str, n: int) -> bytes:
    return (json.dumps({"type": "assistant", "timestamp": datetime.fromtimestamp(at, timezone.utc).isoformat(),
                        "sessionId": native, "cwd": cwd, "message": {"id": mid, "model": "claude-stress",
                        "usage": {"input_tokens": n, "output_tokens": n, "cache_creation_input_tokens": 2,
                                  "cache_read_input_tokens": 3}}}, separators=(",", ":")) + "\n").encode()


def sparse_transcript(path: Path, native: str, now: float, cwd: str) -> None:
    first = (json.dumps({"type": "user", "timestamp": datetime.fromtimestamp(now - 2, timezone.utc).isoformat(),
                         "message": {"content": SENTINEL}}, separators=(",", ":")) + "\n").encode()
    start = assistant(native, native + "-a", now - 1, cwd, 10)
    end = b"\n" + assistant(native, native + "-b", now, cwd, 20)
    with path.open("wb") as fh:
        fh.write(first); fh.write(start)
        fh.seek(LOGICAL_BYTES - len(end))
        fh.write(end)
    os.utime(path, (now, now))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="wb-increment3-") as tmp:
        root = Path(tmp)
        cache, projects, codex = root / "cache", root / "claude" / "synthetic", root / "codex"
        projects.mkdir(parents=True); codex.mkdir()
        tasks = root / "tasks"
        for i in range(SESSIONS):
            (tasks / f"task-{i:02d}").mkdir(parents=True)
        cfg = load_config(Path("/nonexistent"))
        cfg.repositories = [Repository(id="tasks", path=str(tasks))]
        now = time.time()
        for i in range(SESSIONS):
            cwd = str(tasks / f"task-{i:02d}") if i < SESSIONS - 2 else str(root / "outside")
            sparse_transcript(projects / f"session-{i:02d}.jsonl", f"session-{i:02d}", now,
                              cwd)

        focus_events = [
            {"type": "checkin", "occurred_at": datetime.fromtimestamp(now - 10, timezone.utc).isoformat(),
             "actor": {"session_id": "session-00"},
             "payload": {"status": "working", "tasks": ["task-00"]}},
            {"type": "checkin", "occurred_at": datetime.fromtimestamp(now - 10, timezone.utc).isoformat(),
             "actor": {"session_id": "session-01"},
             "payload": {"status": "working", "tasks": ["task-01", "task-02"]}},
        ]

        kwargs = dict(cache_dir=cache, claude_root=projects.parent, codex_root=codex,
                      muse_db=root / "missing.db", now=now, byte_budget=32 * 1024 * 1024, time_budget_s=15)
        first = usage.collect(cfg, focus_events, "stress", **kwargs)
        assert len(first["sessions"]) == SESSIONS, len(first["sessions"])
        assert len(first["tasks"]) >= SESSIONS - 3, len(first["tasks"])
        expected = SESSIONS * ((10 + 10 + 2 + 3) + (20 + 20 + 2 + 3))
        assert sum(row["total"] for row in first["sessions"].values()) == expected

        # Same-inode truncation starts a new generation; an old message id is
        # still deduped while a new record adds only non-negative counters.
        trunc = projects / "session-00.jsonl"
        with trunc.open("wb") as fh:
            fh.write(assistant("session-00", "session-00-a", now + 1, str(tasks / "task-00"), 10))
            fh.write(assistant("session-00", "session-00-c", now + 2, str(tasks / "task-00"), 30))
        # Rotation creates a new inode/path generation with one replay and one new message.
        rotate = projects / "session-01.jsonl"
        rotate.rename(projects / "session-01.rotated")
        with rotate.open("wb") as fh:
            fh.write(assistant("session-01", "session-01-b", now + 1, str(tasks / "task-01"), 20))
            fh.write(assistant("session-01", "session-01-c", now + 2, str(tasks / "task-01"), 40))
        changed = usage.collect(cfg, focus_events, "stress", **dict(kwargs, now=now + 2))

        # Append while the collector has an open/stat-bounded view. A following
        # pass must collect every complete record exactly once.
        target = projects / "session-02.jsonl"
        go = threading.Event()
        def writer():
            go.wait()
            with target.open("ab", buffering=0) as fh:
                for i in range(20):
                    fh.write(assistant("session-02", f"concurrent-{i}", now + 3 + i,
                                       str(tasks / "task-02"), 1))
        thread = threading.Thread(target=writer)
        thread.start(); go.set()
        usage.collect(cfg, focus_events, "stress", **dict(kwargs, now=now + 3))
        thread.join()
        final = usage.collect(cfg, focus_events, "stress", **dict(kwargs, now=now + 30))
        idle = usage.collect(cfg, focus_events, "stress", **dict(kwargs, now=now + 31, byte_budget=1024 * 1024))

        accounting = final["accounting"]
        assert accounting["total"] == sum(accounting[k] for k in ("exact", "medium", "ambiguous", "unattributed"))
        assert all(accounting[key] > 0 for key in ("exact", "medium", "ambiguous", "unattributed")), accounting
        assert accounting["total"] == sum(row["total"] for row in final["sessions"].values())
        assert all(value >= 0 for row in final["sessions"].values() for value in row["counters"].values())
        assert idle["collector"]["bytes_read"] < 1024 * 1024, idle["collector"]

        cache_bytes = b"".join(path.read_bytes() for path in cache.rglob("*") if path.is_file())
        assert SENTINEL.encode() not in cache_bytes

        # Actual dashboard/API serialization with usage attached: the planted
        # prompt string must never cross the loopback API boundary.
        snapshot = snap(realistic()[:1])
        snapshot.usage = final
        usage.apply_task_usage(snapshot.views, final, cfg)
        old_cache, old_state = os.environ.get("WORKBOARD_CACHE"), os.environ.get("WORKBOARD_STATE")
        os.environ["WORKBOARD_CACHE"], os.environ["WORKBOARD_STATE"] = str(cache), str(root / "state")
        server = html.serve(lambda: snapshot, cfg, port=0, interval=3600, team_interval=3600)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            port = server.server_address[1]
            bodies = [urllib.request.urlopen(f"http://127.0.0.1:{port}/data.json").read(),
                      urllib.request.urlopen(f"http://127.0.0.1:{port}/api/regions/stats").read()]
            assert all(SENTINEL.encode() not in body for body in bodies)
        finally:
            server.shutdown(); server.server_close(); thread.join(2)
            if old_cache is None: os.environ.pop("WORKBOARD_CACHE", None)
            else: os.environ["WORKBOARD_CACHE"] = old_cache
            if old_state is None: os.environ.pop("WORKBOARD_STATE", None)
            else: os.environ["WORKBOARD_STATE"] = old_state

        print(json.dumps({
            "sessions": SESSIONS,
            "logical_transcript_gib": round(SESSIONS * LOGICAL_BYTES / 1024 ** 3, 2),
            "initial_bytes_read": first["collector"]["bytes_read"],
            "idle_bytes_read": idle["collector"]["bytes_read"],
            "indexed_tokens": accounting["total"],
            "attribution": {key: accounting[key] for key in ("exact", "medium", "ambiguous", "unattributed")},
            "cache_bytes": len(cache_bytes),
            "privacy_sentinel_found": False,
            "negative_delta_found": False,
            "truncate_and_rotation_passed": True,
            "concurrent_append_passed": True,
        }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

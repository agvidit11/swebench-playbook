import json
import os
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workboard import costs, events, usage
from workboard.config import PricingModel, Repository, load_config


NOW = 1_792_920_000.0


def iso(seconds=NOW):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def claude_row(mid, *, value=10, cwd=None, prompt=None):
    row = {"type": "assistant", "timestamp": iso(), "sessionId": "claude-one", "cwd": cwd,
           "message": {"id": mid, "model": "claude-test", "usage": {
               "input_tokens": value, "output_tokens": value // 2,
               "cache_creation_input_tokens": 2, "cache_read_input_tokens": 3}}}
    if prompt:
        row["prompt"] = prompt
    return row


def token(total, *, at=NOW, input_tokens=None):
    inp = total - 2 if input_tokens is None else input_tokens
    return {"timestamp": iso(at), "type": "event_msg", "payload": {"type": "token_count", "info": {
        "total_token_usage": {"input_tokens": inp, "cached_input_tokens": 2,
                              "cache_write_input_tokens": 0, "output_tokens": 2,
                              "reasoning_output_tokens": 1, "total_tokens": total},
        "last_token_usage": {"input_tokens": inp}, "model_context_window": 100}}}


class UsageCollectorTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(prefix="wb-usage-")
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.cache = self.root / "cache"
        self.projects = self.root / "claude" / "project"
        self.projects.mkdir(parents=True)
        self.codex = self.root / "codex"
        day = datetime.fromtimestamp(NOW, timezone.utc)
        self.codex_day = self.codex / f"{day.year:04d}" / f"{day.month:02d}" / f"{day.day:02d}"
        self.codex_day.mkdir(parents=True)
        self.tasks = self.root / "tasks"
        (self.tasks / "alpha").mkdir(parents=True)
        self.cfg = load_config(Path("/nonexistent"))
        self.cfg.repositories = [Repository(id="tasks", path=str(self.tasks))]

    def collect(self, evs=None, **kw):
        return usage.collect(self.cfg, evs or [], "h1", cache_dir=self.cache,
                             claude_root=self.projects.parent, codex_root=self.codex,
                             muse_db=kw.pop("muse_db", self.root / "missing.db"), now=NOW,
                             byte_budget=20 * 1024 * 1024, time_budget_s=4, **kw)

    def test_claude_incremental_dedupe_truncate_rotate_and_privacy(self):
        sentinel = "WB_PRIVATE_PROMPT_91b4f3"
        path = self.projects / "claude-one.jsonl"
        user = {"type": "user", "timestamp": iso(), "message": {"content": sentinel}}
        path.write_text(json.dumps(user) + "\n" + json.dumps(claude_row("m1", cwd=str(self.tasks / "alpha"))) + "\n")
        os.utime(path, (NOW, NOW))
        first = self.collect()
        self.assertEqual(first["sessions"]["claude:claude-one"]["total"], 20)
        self.assertEqual(first["tasks"]["alpha"]["medium"], 20)
        idle = self.collect()
        self.assertEqual(idle["collector"]["bytes_read"], 0)

        with path.open("a") as fh:
            fh.write(json.dumps(claude_row("m1", value=10, prompt=sentinel)) + "\n")
            fh.write(json.dumps(claude_row("m2", value=20, cwd=str(self.tasks / "alpha"))) + "\n")
        second = self.collect()
        self.assertEqual(second["sessions"]["claude:claude-one"]["total"], 55)

        path.write_text(json.dumps(claude_row("m3", value=30, cwd=str(self.tasks / "alpha"))) + "\n")
        os.utime(path, (NOW, NOW))
        third = self.collect()
        self.assertEqual(third["sessions"]["claude:claude-one"]["total"], 105)
        rotated = path.with_suffix(".old")
        path.rename(rotated)
        path.write_text(json.dumps(claude_row("m3", value=30)) + "\n" +
                        json.dumps(claude_row("m4", value=40, cwd=str(self.tasks / "alpha"))) + "\n")
        os.utime(path, (NOW, NOW))
        fourth = self.collect()
        self.assertEqual(fourth["sessions"]["claude:claude-one"]["total"], 170)
        cache_text = (self.cache / usage.CACHE_NAME).read_text()
        self.assertNotIn(sentinel, cache_text)
        self.assertNotIn(sentinel, json.dumps(fourth))
        saved = json.loads(cache_text)
        self.assertTrue(all({"fingerprint", "inode", "offset"} <= set(c) for c in saved["cursors"].values()))
        self.assertNotIn(str(self.root), cache_text)

    def test_codex_cumulative_deltas_context_model_effort_and_reset(self):
        path = self.codex_day / "rollout-codex-one.jsonl"
        rows = [
            {"timestamp": iso(), "type": "session_meta", "payload": {
                "id": "codex-one", "cwd": str(self.tasks / "alpha"), "context_window": 100}},
            {"timestamp": iso(), "type": "turn_context", "payload": {
                "model": "gpt-test", "effort": "high", "cwd": str(self.tasks / "alpha")}},
            token(10), token(25, at=NOW + 1),
        ]
        path.write_text("".join(json.dumps(x) + "\n" for x in rows)); os.utime(path, (NOW, NOW))
        got = self.collect()
        session = got["sessions"]["codex:codex-one"]
        self.assertEqual(session["total"], 25)
        self.assertEqual((session["model"], session["effort"]), ("gpt-test", "high"))
        self.assertEqual(session["context"], {"tokens": 23, "window": 100, "pressure_pct": 23})

        rows[-1] = token(5, at=NOW + 2, input_tokens=3)
        path.write_text("".join(json.dumps(x) + "\n" for x in rows)); os.utime(path, (NOW, NOW))
        reset = self.collect()
        self.assertEqual(reset["sessions"]["codex:codex-one"]["total"], 30)
        self.assertTrue(all(value >= 0 for value in reset["sessions"]["codex:codex-one"]["counters"].values()))

    def test_muse_read_only_usage_and_accounting_invariant(self):
        log = self.root / "muse-session.jsonl"
        row = {"id": "record-1", "recorded_at": iso(), "payload": {"event": {
            "model": "muse-test", "usage": {"input_tokens": 30, "output_tokens": 5,
            "cache_read_tokens": 10, "cache_write_tokens": 1, "reasoning_tokens": 2}}}}
        log.write_text(json.dumps(row) + "\n")
        db = self.root / "session-index.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE sessions (session_id,session_dir,session_log_path,workspace_root,provider_id,"
                    "model_id,created_at_us,updated_at_us,status)")
        con.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)", ("muse-one", str(self.root), log.name,
                    str(self.tasks / "alpha"), "test", "muse-test", int(NOW * 1e6), int(NOW * 1e6), "valid"))
        con.commit(); con.close()
        before = (db.stat().st_mtime_ns, log.stat().st_mtime_ns)
        got = self.collect(muse_db=db)
        after = (db.stat().st_mtime_ns, log.stat().st_mtime_ns)
        self.assertEqual(before, after)
        self.assertEqual(got["sessions"]["muse:muse-one"]["total"], 35)
        acct = got["accounting"]
        self.assertEqual(acct["total"], acct["exact"] + acct["medium"] + acct["ambiguous"] + acct["unattributed"])

    def test_exact_ambiguous_and_unattributed_focus_buckets(self):
        path = self.projects / "claude-one.jsonl"
        rows = [claude_row("one", value=10), claude_row("two", value=20), claude_row("three", value=30)]
        rows[0]["timestamp"], rows[1]["timestamp"], rows[2]["timestamp"] = iso(NOW - 30), iso(NOW), iso(NOW + 30)
        path.write_text("".join(json.dumps(x) + "\n" for x in rows)); os.utime(path, (NOW, NOW))
        exact = events.new_event("checkin", None, {"status": "working", "tasks": ["alpha"]},
                                 actor={"session_id": "claude-one", "alias": "test", "kind": "claude"},
                                 commit=None, source="test")
        exact["occurred_at"] = iso(NOW - 60)
        ambiguous = events.new_event("checkin", None, {"status": "working", "tasks": ["alpha", "beta"]},
                                     actor={"session_id": "claude-one", "alias": "test", "kind": "claude"},
                                     commit=None, source="test")
        ambiguous["occurred_at"] = iso(NOW + 10)
        got = self.collect([exact, ambiguous])
        self.assertGreater(got["accounting"]["exact"], 0)
        self.assertGreater(got["accounting"]["ambiguous"], 0)
        self.assertEqual(got["accounting"]["total"], sum(got["accounting"][k] for k in
                                                         ("exact", "medium", "ambiguous", "unattributed")))

    def test_concurrent_collectors_serialize_without_double_counting(self):
        path = self.projects / "claude-one.jsonl"
        path.write_text(json.dumps(claude_row("once", cwd=str(self.tasks / "alpha"))) + "\n")
        os.utime(path, (NOW, NOW))
        barrier = threading.Barrier(2)
        results = []
        def run():
            barrier.wait()
            results.append(self.collect())
        threads = [threading.Thread(target=run) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(5)
        self.assertEqual(len(results), 2)
        final = self.collect()
        self.assertEqual(final["sessions"]["claude:claude-one"]["total"], 20)


class PricingAdviceTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))

    def test_unknown_cost_is_unavailable_and_configured_rate_is_estimate(self):
        counters = {"input": 1_000_000, "output": 500_000, "cache_read": 0, "cache_write": 0, "reasoning": 0}
        self.assertEqual(costs.estimate("gpt-test", counters, self.cfg)["label"], "cost unavailable")
        self.cfg.pricing.models = [PricingModel(pattern="gpt-*", effective_from="2026-01-01",
                                                input_per_million=2, output_per_million=4, currency="USD")]
        got = costs.estimate("gpt-test", counters, self.cfg, kind="codex")
        self.assertEqual((got["available"], got["amount"], got["kind"]), (True, 4.0, "estimate"))

    def test_advice_wait_watch_rotate_and_keep(self):
        class View:
            def __init__(self, task, owner=None, sync="OK"):
                self.entity_id = task
                self.fields = {"group": "ATTENTION", "owner_session": owner, "sync": sync}
        base = {"session_key": "claude:h:1:d:s", "native_id": "s", "kind": "claude",
                "tasks": ["alpha"], "last_activity_at": iso(NOW - 4 * 3600), "restart": {"needed": False},
                "tokens": {"context": {"pressure_pct": 91}}}
        rows = [dict(base, status="idle")]
        usage.apply_advice(rows, [View("alpha")], now=NOW)
        self.assertEqual(rows[0]["advice"]["state"], "rotate")
        self.assertIn("nothing unpushed", rows[0]["advice"]["reason"])
        rows = [dict(base, status="waiting-for-permission")]
        usage.apply_advice(rows, [View("alpha")], now=NOW)
        self.assertEqual(rows[0]["advice"]["state"], "unblock")
        rows = [dict(base, status="busy")]
        usage.apply_advice(rows, [View("alpha", owner="s")], now=NOW)
        self.assertEqual(rows[0]["advice"]["state"], "watch")


class OnlineUsageTest(unittest.TestCase):
    def test_bounded_sanitized_job_counts_and_cache(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        cfg = load_config(Path("/nonexistent"))
        calls = []
        class Result:
            returncode = 0
            stdout = json.dumps({"jobs": [{"id": "j1", "trialCount": 3, "reportMarkdown": "PRIVATE"},
                                            {"id": "j2", "trial_count": 2}]})
        def runner(argv, **kwargs):
            calls.append((argv, kwargs)); return Result()
        got = costs.online_usage("alpha", cfg, Path(td.name), baseline={"oracle": 1}, runner=runner)
        self.assertEqual((got["run_count"], got["trial_count"]), (2, 5))
        self.assertNotIn("PRIVATE", (Path(td.name) / costs.ONLINE_CACHE).read_text())
        again = costs.online_usage("alpha", cfg, Path(td.name), runner=lambda *a, **k: self.fail("not cached"))
        self.assertEqual(again["run_count"], 2)
        self.assertEqual(calls[0][0][-3:], ["--limit", "20", "--json"])


if __name__ == "__main__":
    unittest.main()

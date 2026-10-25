import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from workboard import events, session_inventory
from workboard.config import Repository, load_config
from workboard.ownership import reduce_focus
from workboard.sources import agent_runs, claude_sessions


NOW = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc).timestamp()


def proc(root: Path, pid: int, start: str):
    p = root / str(pid)
    p.mkdir()
    fields = ["S"] + ["0"] * 18 + [start, "0"]
    (p / "stat").write_text(f"{pid} (claude) " + " ".join(fields))


def registry(root: Path, name: str, *, pid=101, domain="local-domain", start="111", uid=None, **extra):
    uid = os.getuid() if uid is None else uid
    data = {"sessionId": name, "pid": pid, "pidDomain": domain, "procStart": start,
            "startedAt": int((NOW - 600) * 1000), "messagingSocketPath": f"/run/user/{uid}/cc-socks/{pid}.sock",
            "name": f"Synthetic {name}", "cwd": "/synthetic/tasks/alpha"}
    data.update(extra)
    (root / f"{name}.json").write_text(json.dumps(data))


class ClaudeRegistryTest(unittest.TestCase):
    def test_classifies_live_foreign_stale_reused_and_malformed(self):
        with tempfile.TemporaryDirectory() as d:
            root, procs = Path(d) / "registry", Path(d) / "proc"
            root.mkdir(); procs.mkdir()
            proc(procs, 101, "111")
            proc(procs, 104, "999")
            registry(root, "live", pid=101)
            registry(root, "foreign-uid", pid=102, uid=os.getuid() + 1)
            registry(root, "foreign-domain", pid=103, domain="other-domain")
            registry(root, "stale", pid=105)
            registry(root, "reused", pid=104, start="111")
            (root / "broken.json").write_text("{")
            rows, diag = claude_sessions.discover("h1", root=root, proc_root=procs,
                                                   pid_domain="local-domain", now=NOW)
        self.assertEqual({r["native_id"] for r in rows}, {"live"})
        by_id = {r["native_id"]: r for r in rows}
        self.assertEqual(by_id["live"]["classification"], "local-live")
        self.assertIn("claude:h1", by_id["live"]["session_key"])
        classes = {x["classification"] for x in diag}
        self.assertTrue({"invalid", "foreign-uid", "foreign-domain", "local-stale", "pid-reused"} <= classes)
        self.assertTrue(all(set(x) <= {"file", "classification", "reason"} for x in diag))


class FocusReducerTest(unittest.TestCase):
    def event(self, kind, task, at, payload=None):
        e = events.new_event(kind, task, payload or {},
                             actor={"session_id": "s1", "alias": "h1·synthetic", "kind": "claude"},
                             commit=None, source="test")
        e["occurred_at"] = datetime.fromtimestamp(at, timezone.utc).isoformat()
        return events.stamp(e, "h1", int(at) % 10000)

    def test_rank_and_ambiguity(self):
        session = {"native_id": "s1", "cwd_task": "cwd-task"}
        weak = self.event("presence", "mentioned-task", NOW - 60, {"last_seen": NOW - 60})
        tool = self.event("touch", "tool-task", NOW - 30)
        explicit = self.event("checkin", None, NOW - 10, {"status": "working", "tasks": ["here-task"]})
        focus = reduce_focus(session, [weak, tool, explicit], now=NOW)
        self.assertEqual((focus["primary"], focus["evidence"]), ("here-task", ["explicit here"]))
        two = self.event("checkin", None, NOW - 5, {"status": "working", "tasks": ["here-task", "other-task"]})
        focus = reduce_focus(session, [two], now=NOW)
        self.assertEqual((focus["state"], focus["tasks"]), ("ambiguous", ["here-task", "other-task"]))

    def test_real_shaped_today_events_match_registry_session_id(self):
        native = "f361693d-8424-412e-849a-7697da674f32"
        session = {"native_id": native, "session_key": f"claude:h1:1:d:{native}", "kind": "claude"}
        presence = events.new_event("presence", "archaius-config-hierarchy-edit-coherence",
                                    {"last_seen": NOW - 3600, "agents": ["codex"]},
                                    actor={"session_id": native, "alias": "h1·lane", "kind": "claude"},
                                    commit=None, source="presence")
        presence["occurred_at"] = datetime.fromtimestamp(NOW - 3500, timezone.utc).isoformat()
        claim = events.new_event("claim", "cancancan-limited-ability-common-permission", {},
                                 actor={"session_id": native, "alias": "h1·lane", "kind": "claude"},
                                 commit=None, source="workboard")
        claim["occurred_at"] = datetime.fromtimestamp(NOW - 120, timezone.utc).isoformat()
        focus = reduce_focus(session, [presence, claim], now=NOW)
        self.assertEqual(focus["tasks"], ["cancancan-limited-ability-common-permission"])
        self.assertEqual(focus["evidence"], ["ledger activity"])


class ChildRunTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.cfg = load_config(Path("/nonexistent"))
        self.cfg.repositories = [Repository(id="tasks", path=str(self.root / "tasks"))]
        self.cfg.ledger.path = str(self.root / "ledger")
        (self.root / "tasks" / "alpha").mkdir(parents=True)
        self.parent = {"session_key": "claude:h1:u:d:parent", "native_id": "parent", "name": "Parent",
                       "focus": {"tasks": ["alpha"]}, "transport": {"available": True}, "child_runs": []}

    def launch(self, model, seq):
        e = events.new_event("build_action", "alpha", {"model": model},
                             actor={"session_id": "parent", "alias": "h1·Parent", "kind": "claude"},
                             commit=None, source="test")
        e["occurred_at"] = datetime.fromtimestamp(NOW - 60, timezone.utc).isoformat()
        return events.stamp(e, "h1", seq)

    def test_codex_and_muse_parent_linkage(self):
        codex = self.root / "codex.jsonl"
        meta = {"type": "session_meta", "payload": {"id": "codex-child", "cwd": str(self.root / "tasks" / "alpha"),
                                                        "timestamp": datetime.fromtimestamp(NOW, timezone.utc).isoformat()}}
        codex.write_text(json.dumps(meta) + "\n")
        os.utime(codex, (NOW, NOW))
        codex_runs = agent_runs.discover_codex(self.cfg, "h1", paths=[codex], now=NOW)

        db = self.root / "muse.db"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE sessions (session_id, workspace_root, provider_id, model_id, created_at_us, "
                    "updated_at_us, status, msp_parent_session_id)")
        con.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)",
                    ("muse-child", str(self.root / "tasks" / "alpha"), "synthetic", "model", int(NOW * 1e6),
                     int(NOW * 1e6), "running", None))
        con.commit(); con.close()
        muse_runs = agent_runs.discover_muse(self.cfg, "h1", db_path=db, now=NOW)
        agent_runs.link_parents(codex_runs + muse_runs, [self.parent],
                                [self.launch("codex", 1), self.launch("muse", 2)], now=NOW)
        self.assertEqual({r["parent_session_key"] for r in codex_runs + muse_runs}, {self.parent["session_key"]})
        self.assertEqual({r["parent_confidence"] for r in codex_runs + muse_runs}, {"high"})
        self.assertEqual({r["kind"] for r in self.parent["child_runs"]}, {"codex", "muse"})

    def test_transcript_workspace_and_tool_window_linkage(self):
        projects = self.root / "projects" / "synthetic-project"
        projects.mkdir(parents=True)
        parent_id = self.parent["native_id"]
        self.parent["cwd"] = str(self.root)
        path = projects / f"{parent_id}.jsonl"
        tool_id = "tool-1"
        rows = [
            {"timestamp": datetime.fromtimestamp(NOW - 30, timezone.utc).isoformat(),
             "message": {"content": [{"type": "tool_use", "id": tool_id,
                                         "input": {"command": f"codex exec -C {self.root / 'tasks' / 'alpha'} prompt"}}]}},
            {"timestamp": datetime.fromtimestamp(NOW + 30, timezone.utc).isoformat(),
             "message": {"content": [{"type": "tool_result", "tool_use_id": tool_id, "content": "done"}]}}
        ]
        path.write_text("".join(json.dumps(x) + "\n" for x in rows))
        launches = agent_runs.transcript_launches([self.parent], root=self.root / "projects", now=NOW + 60)
        run = {"kind": "codex", "cwd": str(self.root / "tasks" / "alpha"), "cwd_task": "alpha",
               "started_at": datetime.fromtimestamp(NOW, timezone.utc).isoformat(), "parent_session_key": None,
               "transport": {"available": False}}
        agent_runs.link_parents([run], [self.parent], [], now=NOW + 60, launches=launches)
        self.assertEqual(run["parent_session_key"], self.parent["session_key"])
        self.assertEqual(run["parent_confidence"], "high")

    def test_unlinked_runs_are_one_bounded_summary_not_sessions(self):
        run = {"session_key": "codex:h1:1:local:solo", "native_id": "solo", "kind": "codex",
               "kind_icon": "🟢", "host": "h1", "name": "Codex solo", "status": "idle", "live": True,
               "cwd_task": "alpha", "started_at": datetime.fromtimestamp(NOW - 60, timezone.utc).isoformat(),
               "transport": {"available": False, "kind": "unavailable",
                                                       "reason": "route to its parent session"},
               "parent_session_key": None}
        with patch("workboard.session_inventory.claude_sessions.discover", return_value=([], [])), \
             patch("workboard.session_inventory.agent_runs.discover_codex", return_value=[run]), \
             patch("workboard.session_inventory.agent_runs.discover_muse", return_value=[]), \
             patch("workboard.session_inventory.agent_runs.live_codex_ids", return_value=set()), \
             patch("workboard.session_inventory.agent_runs.transcript_launches", return_value=[]):
            rows, _ = session_inventory.discover(self.cfg, [], "h1", now=NOW)
        self.assertEqual([row["session_key"] for row in rows], ["unlinked:h1"])
        self.assertTrue(rows[0]["is_summary"])
        self.assertFalse(rows[0]["transport"]["available"])
        self.assertEqual(rows[0]["tasks"], ["alpha"])
        self.assertEqual([r["native_id"] for r in rows[0]["child_runs"]], ["solo"])

    def test_live_exec_is_still_a_run_but_live_tui_is_top_level(self):
        def row(native, source):
            return {"session_key": f"codex:h1:1:local:{native}", "native_id": native, "kind": "codex",
                    "kind_icon": "🟢", "host": "h1", "name": f"Codex {native}", "status": "busy",
                    "status_since": datetime.fromtimestamp(NOW - 10, timezone.utc).isoformat(), "live": True,
                    "cwd_task": "alpha", "cwd": str(self.root / "tasks" / "alpha"), "source": source,
                    "started_at": datetime.fromtimestamp(NOW - 30, timezone.utc).isoformat(),
                    "transport": {"available": False}, "parent_session_key": None}
        runs = [row("exec-job", "exec"), row("tui", "cli")]
        with patch("workboard.session_inventory.claude_sessions.discover", return_value=([], [])), \
             patch("workboard.session_inventory.agent_runs.discover_codex", return_value=runs), \
             patch("workboard.session_inventory.agent_runs.discover_muse", return_value=[]), \
             patch("workboard.session_inventory.agent_runs.live_codex_ids", return_value={"exec-job", "tui"}), \
             patch("workboard.session_inventory.agent_runs.transcript_launches", return_value=[]):
            rows, _ = session_inventory.discover(self.cfg, [], "h1", now=NOW)
        tui = next(r for r in rows if r["native_id"] == "tui")
        self.assertFalse(tui.get("is_summary", False))
        self.assertEqual(tui["child_runs"], [])
        summary = next(r for r in rows if r.get("is_summary"))
        self.assertEqual([r["native_id"] for r in summary["child_runs"]], ["exec-job"])

    def test_every_optional_source_failure_is_contained(self):
        boom = RuntimeError("synthetic")
        with patch("workboard.session_inventory.claude_sessions.discover", side_effect=boom), \
             patch("workboard.session_inventory.agent_runs.discover_codex", side_effect=boom), \
             patch("workboard.session_inventory.agent_runs.discover_muse", side_effect=boom), \
             patch("workboard.session_inventory.agent_runs.live_codex_ids", side_effect=boom), \
             patch("workboard.session_inventory.agent_runs.transcript_launches", side_effect=boom), \
             patch("workboard.session_inventory.agent_runs.link_parents", side_effect=boom):
            rows, diagnostics = session_inventory.discover(self.cfg, [], "h1", now=NOW)
        self.assertEqual(rows, [])
        reasons = " ".join(x["reason"] for x in diagnostics if x["classification"] == "source-error")
        for source in ("Claude registry", "Codex runs", "Muse runs", "Codex liveness", "launch evidence", "parent linkage"):
            self.assertIn(source, reasons)


class HookEvidenceTest(unittest.TestCase):
    def test_hook_event_loaded_probable_missing_and_idle_unknown(self):
        parent = {"session_key": "claude:h1:1:d:s1", "native_id": "s1", "name": "Synthetic",
                  "kind": "claude", "kind_icon": "🟣", "host": "h1", "status": "busy",
                  "status_since": datetime.fromtimestamp(NOW - 60, timezone.utc).isoformat(), "live": True,
                  "classification": "local-live", "liveness_reason": "process identity matches", "cwd": None,
                  "transport": {"available": True}, "child_runs": []}
        hook = events.new_event("touch", "alpha", {}, actor={"session_id": "s1", "alias": "h1·Synthetic",
                                                               "kind": "claude"}, commit=None, source="hook")
        hook["occurred_at"] = datetime.fromtimestamp(NOW - 120, timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); settings = root / "settings.json"
            settings.write_text(json.dumps({"hooks": {"PostToolUse": [{"hooks": [{"command": "/x/board hook post-tool"}]}]}}))
            cfg = load_config(Path("/nonexistent")); cfg.ledger.path = str(root / "ledger")
            common = (patch("workboard.session_inventory.claude_sessions.discover",
                            side_effect=lambda *a, **k: ([dict(parent, child_runs=[])], [])),
                      patch("workboard.session_inventory.agent_runs.discover_codex", return_value=[]),
                      patch("workboard.session_inventory.agent_runs.discover_muse", return_value=[]),
                      patch("workboard.session_inventory.agent_runs.live_codex_ids", return_value=set()),
                      patch("workboard.session_inventory.agent_runs.transcript_launches", return_value=[]),
                      patch.dict(os.environ, {"CLAUDE_SETTINGS": str(settings)}))
            for p in common: p.start()
            try:
                loaded, _ = session_inventory.discover(cfg, [hook], "h1", now=NOW)
                missing, _ = session_inventory.discover(cfg, [], "h1", now=NOW)
                parent["status"] = "idle"
                unknown, _ = session_inventory.discover(cfg, [], "h1", now=NOW)
            finally:
                for p in reversed(common): p.stop()
        self.assertEqual(loaded[0]["restart"]["state"], "loaded")
        self.assertIsNone(loaded[0]["restart"]["command"])
        self.assertEqual(missing[0]["restart"]["state"], "probably-missing")
        self.assertIn("claude --resume s1", missing[0]["restart"]["command"])
        self.assertEqual(unknown[0]["restart"]["state"], "unknown")
        self.assertIsNone(unknown[0]["restart"]["command"])


if __name__ == "__main__":
    unittest.main()

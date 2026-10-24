import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from workboard import events, hooks
from workboard.config import Repository, load_config

BOARD = Path(__file__).resolve().parent.parent


class HookTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.repo = self.tmp / "tasks"
        (self.repo / "alpha-task").mkdir(parents=True)
        self.state = self.tmp / "state"
        self.cfg = load_config(Path("/nonexistent"))
        self.cfg.repositories = [Repository(id="tasks", path=str(self.repo))]
        self.transcript = self.tmp / "s1.jsonl"
        self.transcript.write_text(json.dumps({"type": "ai-title", "aiTitle": "Lane orchestrator loop"}) + "\n")

    def payload(self, event, tool="Edit", **tool_input):
        return {"session_id": "s1", "transcript_path": str(self.transcript), "cwd": str(self.tmp),
                "hook_event_name": event, "tool_name": tool, "tool_input": tool_input}

    def spool(self):
        p = self.state / events.SPOOL_NAME
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    def run_hook(self, kind, data, host="h1"):
        return hooks.handle(kind, data, cfg=self.cfg, state_dir=self.state, host_id=host)

    def test_post_tool_edit_records_touch_once_per_window(self):
        data = self.payload("PostToolUse", file_path=str(self.repo / "alpha-task" / "tests" / "test.sh"))
        self.assertEqual(self.run_hook("post-tool", data).code, 0)
        self.run_hook("post-tool", data)
        touches = [e for e in self.spool() if e["type"] == "touch"]
        self.assertEqual(len(touches), 1)
        self.assertEqual(touches[0]["entity"]["id"], "alpha-task")
        self.assertEqual(touches[0]["actor"]["alias"], "h1·Lane orchestrator loop")

    def test_bash_cwd_inside_task_and_codex_build_action(self):
        data = self.payload("PostToolUse", tool="Bash", command="codex exec -s workspace-write -C alpha-task 'fix'")
        data["cwd"] = str(self.repo / "alpha-task")
        self.run_hook("post-tool", data)
        types = [e["type"] for e in self.spool()]
        self.assertIn("touch", types)
        builds = [e for e in self.spool() if e["type"] == "build_action"]
        self.assertEqual(builds[0]["payload"]["model"], "codex")

    def test_outside_task_paths_ignored(self):
        self.run_hook("post-tool", self.payload("PostToolUse", file_path="/etc/hosts"))
        self.run_hook("post-tool", self.payload("PostToolUse", file_path=str(self.repo / "README.md")))
        self.assertEqual([e for e in self.spool() if e["type"] == "touch"], [])

    def test_alias_from_customTitle_then_aiTitle(self):
        self.run_hook("session-start", self.payload("SessionStart"))
        self.assertEqual(self.spool()[-1]["payload"]["alias"], "h1·Lane orchestrator loop")
        with open(self.transcript, "a") as fh:
            fh.write(json.dumps({"type": "custom-title", "customTitle": "dropshot fixer"}) + "\n")
        self.run_hook("session-start", self.payload("SessionStart"))
        self.assertEqual(self.spool()[-1]["payload"]["alias"], "h1·dropshot fixer")

    def write_claims_cache(self, owner_session, age_s=10, renewed_age_h=1):
        now = datetime.now(timezone.utc)
        hooks.save_claims_cache(self.state, {
            "fetched_at": (now - timedelta(seconds=age_s)).isoformat(),
            "claims": {"alpha-task": {"session_id": owner_session, "alias": "h2·harness loop",
                                      "renewed_at": (now - timedelta(hours=renewed_age_h)).isoformat()}}})

    def test_pre_tool_blocks_only_with_healthy_foreign_claim(self):
        data = self.payload("PreToolUse", file_path=str(self.repo / "alpha-task" / "x.py"))
        self.write_claims_cache("s9")
        r = self.run_hook("pre-tool", data)
        self.assertEqual(r.code, 2)
        self.assertIn("h2·harness loop", r.stderr)
        self.assertIn("workboard show alpha-task", r.stderr)
        self.write_claims_cache("s1")                       # own claim
        self.assertEqual(self.run_hook("pre-tool", data).code, 0)
        self.write_claims_cache("s9", age_s=600)            # stale cache -> advisory, never block
        self.assertEqual(self.run_hook("pre-tool", data).code, 0)
        self.write_claims_cache("s9", renewed_age_h=30)     # expired claim
        self.assertEqual(self.run_hook("pre-tool", data).code, 0)

    def test_hook_bad_input_exit0(self):
        for bad in (None, {}, {"tool_input": "x"}, {"session_id": "s1", "transcript_path": "/nope", "tool_input": {}}):
            self.assertEqual(self.run_hook("post-tool", bad).code, 0)
        self.assertEqual(self.run_hook("pre-tool", {"tool_input": {"file_path": 3}}).code, 0)

    def test_hook_fast_in_process(self):
        data = self.payload("PostToolUse", file_path=str(self.repo / "alpha-task" / "f"))
        t = time.perf_counter()
        for _ in range(20):
            self.run_hook("post-tool", data)
        self.assertLess((time.perf_counter() - t) / 20, 0.05)

    def test_hook_cli_subprocess_exit0_on_garbage(self):
        env = {**os.environ, "PYTHONPATH": str(BOARD), "WORKBOARD_CONFIG": "/nonexistent", "WORKBOARD_STATE": str(self.state)}
        t = time.perf_counter()
        p = subprocess.run([sys.executable, "-m", "workboard", "hook", "post-tool"], input="not json", text=True,
                           capture_output=True, env=env, timeout=10)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, "")
        self.assertLess(time.perf_counter() - t, 1.0)


class InstallTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.settings = Path(td.name) / "settings.json"
        self.settings.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": "other-tool check"}]}]}, "permissions": {"allow": ["Read"]}}))

    def test_install_idempotent_and_backup(self):
        hooks.install(self.settings, "/opt/board")
        hooks.install(self.settings, "/opt/board")
        data = json.loads(self.settings.read_text())
        self.assertEqual(data["permissions"], {"allow": ["Read"]})          # untouched
        pre = data["hooks"]["PreToolUse"]
        self.assertIn("other-tool check", json.dumps(pre))                   # existing hook kept
        self.assertEqual(json.dumps(data).count("/opt/board hook pre-tool"), 1)
        self.assertTrue(list(self.settings.parent.glob("settings.json.workboard-backup-*")))

    def test_dry_run_writes_nothing(self):
        before = self.settings.read_text()
        out = hooks.install(self.settings, "/opt/board", dry_run=True)
        self.assertEqual(self.settings.read_text(), before)
        self.assertIn("/opt/board hook post-tool", out)

    def test_uninstall_removes_only_ours(self):
        hooks.install(self.settings, "/opt/board")
        hooks.uninstall(self.settings)
        data = json.loads(self.settings.read_text())
        self.assertNotIn("/opt/board", json.dumps(data))
        self.assertIn("other-tool check", json.dumps(data))

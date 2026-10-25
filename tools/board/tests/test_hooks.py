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


class HookHardeningTest(HookTest):
    def env(self):
        cfgfile = self.tmp / "config.toml"
        cfgfile.write_text(f'config_version = 1\n[[repositories]]\nid = "tasks"\npath = "{self.repo}"\n')
        return {**os.environ, "PYTHONPATH": str(BOARD), "WORKBOARD_CONFIG": str(cfgfile),
                "WORKBOARD_STATE": str(self.state)}

    def cli(self, kind, data):
        t = time.perf_counter()
        p = subprocess.run([sys.executable, "-m", "workboard", "hook", kind], input=json.dumps(data), text=True,
                           capture_output=True, env=self.env(), timeout=10)
        return p, time.perf_counter() - t

    def hold_lock(self, name):
        import fcntl as f
        self.state.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.state / name, os.O_RDWR | os.O_CREAT)
        f.flock(fd, f.LOCK_EX)
        self.addCleanup(os.close, fd)

    def test_held_locks_do_not_stall(self):
        data = self.payload("PostToolUse", file_path=str(self.repo / "alpha-task" / "f"))
        for lock in (hooks.HOOK_STATE + ".lock", events.SPOOL_LOCK):
            t = time.perf_counter()
            self.assertEqual(self.run_hook("post-tool", data).code, 0)
            self.hold_lock(lock)
            t = time.perf_counter()
            self.assertEqual(self.run_hook("post-tool", data).code, 0)
            self.assertLess(time.perf_counter() - t, 0.1)

    def test_cold_process_latency(self):
        # Codex asked for <100 ms end to end; bare interpreter start here is ~75-85 ms, so the hook's own
        # work is held to <100 ms in-process (test_hook_fast_in_process) and a cold process to <250 ms.
        p, dt = self.cli("post-tool", self.payload("PostToolUse", file_path=str(self.repo / "alpha-task" / "f")))
        self.assertEqual((p.returncode, p.stdout), (0, ""))
        self.assertLess(dt, 0.25)

    def test_internal_error_leaves_warning(self):
        with mock.patch.object(hooks, "task_of", side_effect=RuntimeError("boom")):
            r = self.run_hook("post-tool", self.payload("PostToolUse", file_path="x"))
        self.assertEqual(r.code, 0)
        warn = [e for e in self.spool() if e["type"] == "warning"]
        self.assertIn("boom", warn[-1]["payload"]["error"])

    def test_build_target_from_repo_root_and_cross_task(self):
        (self.repo / "beta-task").mkdir()
        data = self.payload("PostToolUse", tool="Bash", command="codex exec -s workspace-write -C alpha-task 'x'")
        data["cwd"] = str(self.repo)
        self.run_hook("post-tool", data)
        data = self.payload("PostToolUse", tool="Bash", command="muse exec --workspace ../beta-task --prompt-file p")
        data["cwd"] = str(self.repo / "alpha-task")
        self.run_hook("post-tool", data)
        builds = [(e["entity"]["id"], e["payload"]["model"]) for e in self.spool() if e["type"] == "build_action"]
        self.assertEqual(builds, [("alpha-task", "codex"), ("beta-task", "muse")])

    def test_block_message_through_cli(self):
        self.write_claims_cache("s9")
        p, _ = self.cli("pre-tool", self.payload("PreToolUse", file_path=str(self.repo / "alpha-task" / "x.py")))
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertEqual(p.stderr.strip(), "owned by h2·harness loop — run: workboard show alpha-task")

    def test_concurrent_cache_writers(self):
        import threading
        def w(i):
            hooks.save_claims_cache(self.state, {"fetched_at": "x", "claims": {f"t{i}": {}}})
        ts = [threading.Thread(target=w, args=(i,)) for i in range(20)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        path = self.state / hooks.CLAIMS_CACHE
        json.loads(path.read_text())
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual([p.name for p in self.state.glob(".claims-cache.json.*")], [])


class InstallHardeningTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.dir = Path(td.name)

    def test_mode_preserved_and_backups_unique(self):
        s = self.dir / "settings.json"
        s.write_text("{}")
        os.chmod(s, 0o600)
        hooks.install(s, "/opt/board")
        hooks.install(s, "/opt/board")
        self.assertEqual(s.stat().st_mode & 0o777, 0o600)
        backups = sorted(self.dir.glob("settings.json.workboard-backup-*"))
        self.assertEqual(len(backups), 2)
        self.assertEqual(json.loads(backups[0].read_text()), {})       # first backup is the original

    def test_missing_parent_created_and_new_file_private(self):
        s = self.dir / "nested" / "settings.json"
        hooks.install(s, "/opt/my board")
        self.assertEqual(s.stat().st_mode & 0o777, 0o600)
        self.assertIn("'/opt/my board' hook pre-tool", s.read_text())
        hooks.install(s, "/opt/my board")
        self.assertEqual(s.read_text().count("hook pre-tool"), 1)      # quoted form recognised as ours


class HookToProjectionTest(HookTest):
    def test_foreign_edit_end_to_end(self):
        from datetime import datetime, timezone
        from workboard.projection import project
        from workboard.model import Observation
        from workboard import events as ev
        self.run_hook("post-tool", dict(self.payload("PostToolUse", file_path=str(self.repo / "alpha-task" / "x")),
                                        session_id="intruder"))
        touch = [x for x in self.spool() if x["type"] == "touch"][0]
        stamped = ev.stamp(touch, "h1", 2)
        owner = ev.stamp(ev.new_event("claim", "alpha-task", {}, actor={"session_id": "owner", "alias": "h2·o",
                                                                       "kind": "claude"}, commit=None, source="t"), "h2", 1)
        owner["occurred_at"] = "2000-01-01T00:00:00+00:00"
        now = datetime.now(timezone.utc)
        self.cfg.claims.expire_after_hours = 10 ** 6
        obs = [Observation("codimango", "alpha-task", now, {"codimango.status": "draft",
                                                            "codimango.validation_status": "passing"})]
        v = project(obs, [owner, stamped], self.cfg, now)[0]
        self.assertIn("NONOWNER_EDIT", [f.code for f in v.findings])


class PresubmitAutoRecordTest(unittest.TestCase):
    def test_parses_direct_presubmit_run(self):
        from workboard import hooks
        from workboard.config import Config
        cfg = Config()
        out = "  PASS  a\n  FAIL  README cites old sha\n  FAIL  step 2 too easy\n\n  2 FAIL · 1 WARN · 9 PASS\n"
        data = {"tool_name": "Bash", "session_id": "s1",
                "tool_input": {"command": "python3 ~/x/presubmit.py my-task --repo ~/r --ref origin/main --color never"},
                "tool_response": {"stdout": out}}
        r = hooks.presubmit_result(data, cfg)
        self.assertEqual((r["task"], r["fail"], r["warn"], r["pass"]), ("my-task", 2, 1, 9))
        self.assertIn("README cites old sha", r["summary"])
        self.assertIsNone(r["commit"])
        data["tool_input"]["command"] = "board check run my-task"            # recorded by board itself
        self.assertIsNone(hooks.presubmit_result(data, cfg))
        data["tool_input"]["command"] = "python3 presubmit.py --repo ~/r my-task"
        self.assertEqual(hooks.presubmit_result(data, cfg)["task"], "my-task")
        data["tool_input"]["command"] = "python3 presubmit.py my-task | tail -3"         # filtered output: skip
        self.assertIsNone(hooks.presubmit_result(data, cfg))
        data["tool_input"]["command"] = "python3 presubmit.py a && python3 presubmit.py b"  # two runs: skip
        self.assertIsNone(hooks.presubmit_result(data, cfg))
        data["tool_input"]["command"] = "python3 presubmit.py my-task 2>&1 | tee /tmp/x.txt"
        self.assertEqual(hooks.presubmit_result(data, cfg)["task"], "my-task")
        data["tool_response"] = {"stdout": "usage: presubmit.py"}
        self.assertIsNone(hooks.presubmit_result(data, cfg))


class BareTaskNameTest(unittest.TestCase):
    def test_bare_name_counts_only_if_task_dir_exists(self):
        import tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pgmem-null-aggregate").mkdir()
            cfg = SimpleNamespace(repositories=[SimpleNamespace(path=d)])
            data = {"tool_name": "Bash", "cwd": "/tmp", "tool_input": {"command": "codex exec --x pgmem-null-aggregate fix it"}}
            self.assertEqual(hooks.task_of(data, cfg), "pgmem-null-aggregate")
            data["tool_input"]["command"] = "echo some-other-long-name"
            self.assertIsNone(hooks.task_of(data, cfg))

    def test_session_start_intro(self):
        res = hooks._with_inbox(hooks.HookResult(0), {"session_id": "s"}, Path(tempfile.mkdtemp()), "h", "SessionStart", intro=True)
        self.assertIn("board here", json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"])

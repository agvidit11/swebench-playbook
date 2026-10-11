#!/usr/bin/env python3
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("presubmit", HERE / "presubmit.py")
presubmit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(presubmit)


class FakeSource:
    def __init__(self, files):
        self._files = files

    def files(self):
        return list(self._files)

    def read(self, rel):
        return self._files.get(rel)


class PresubmitTests(unittest.TestCase):
    def setUp(self):
        presubmit.results.clear()
        presubmit.infra_failures.clear()
        presubmit.SERVER_REVIEW_STATUS = None

    def test_json_decoder_skips_non_json_brackets_in_banner(self):
        text = "notice [not json]\nmore noise\n{\"ok\": true}\ntrailer"
        self.assertEqual(presubmit.load_json_loose(text), {"ok": True})

    def test_step_sort_is_natural(self):
        values = ["10_last", "2_middle", "1_first"]
        self.assertEqual(sorted(values, key=presubmit.natural_step_key),
                         ["1_first", "2_middle", "10_last"])

    def test_exit_trap_mismatch_is_detected_for_relative_step_paths(self):
        presubmit.SRC = FakeSource({
            "steps/1_first/tests/test.sh": "trap cleanup EXIT\n",
            "steps/2_second/tests/test.sh": "echo run\n",
        })
        presubmit.check_harness("unused")
        self.assertTrue(any(level == "WARN" and check == "MT EXIT trap"
                            for level, check, _ in presubmit.results))

    def test_err_trap_does_not_count_as_exit_trap(self):
        presubmit.SRC = FakeSource({
            "steps/1_first/tests/test.sh": "trap cleanup EXIT\n",
            "steps/2_second/tests/test.sh": "trap cleanup ERR\n",
        })
        presubmit.check_harness("unused")
        self.assertTrue(any(level == "WARN" and check == "MT EXIT trap"
                            for level, check, _ in presubmit.results))

    def test_comments_do_not_count_as_exit_traps(self):
        self.assertFalse(presubmit.has_exit_trap("# trap cleanup EXIT\necho ok\n"))
        self.assertFalse(presubmit.has_exit_trap("echo ok # trap cleanup EXIT\n"))

    def test_numeric_exit_trap_before_semicolon_is_detected(self):
        self.assertTrue(presubmit.has_exit_trap("trap cleanup 0; echo ok\n"))

    def test_api_uses_public_cli_json(self):
        payload = {"name": "demo", "format": "swe_bench"}
        with mock.patch.object(presubmit, "command_json", return_value=payload) as call:
            self.assertEqual(presubmit.api_task("demo"), payload)
        call.assert_called_once_with(["codimango", "task", "show", "demo", "--json"])

    def test_server_infrastructure_failure_is_exit_two(self):
        with mock.patch.object(presubmit, "api_task",
                               side_effect=presubmit.CommandError("network", "offline")):
            presubmit.check_server("demo", None)
        self.assertTrue(presubmit.infra_failures)
        self.assertIsNone(presubmit.SERVER_REVIEW_STATUS)

    def test_missing_server_task_is_semantic_failure(self):
        with mock.patch.object(presubmit, "api_task",
                               side_effect=presubmit.CommandError("not_found", "missing")):
            presubmit.check_server("demo", None)
        self.assertFalse(presubmit.infra_failures)
        self.assertEqual(presubmit.SERVER_REVIEW_STATUS, "unavailable")

    def test_malformed_trial_json_is_infrastructure_failure(self):
        jobs = "  123 status=completed progress=1/1 commit=abcdef12\n"
        with mock.patch.object(presubmit, "command_text", return_value=jobs), \
             mock.patch.object(presubmit, "command_json", side_effect=RuntimeError("no JSON")):
            presubmit.check_trials("demo", "abcdef123456")
        self.assertTrue(presubmit.infra_failures)

    def test_ref_source_does_not_require_checked_out_task_directory(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            task = repo / "demo-task"
            task.mkdir()
            (task / "task.toml").write_text("[task]\nname='codimango/demo-task'\n")
            subprocess.run(["git", "-C", str(repo), "add", "demo-task/task.toml"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "add task"], check=True)
            os.remove(task / "task.toml")
            task.rmdir()
            source = presubmit.Source(str(repo), "demo-task", "HEAD")
            self.assertTrue(source.task_exists())
            self.assertIn("task.toml", source.files())


if __name__ == "__main__":
    unittest.main()

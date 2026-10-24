import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from workboard import checks, events, projection
from workboard.config import load_config

ACTOR = {"session_id": "s1", "alias": "h1·lane", "kind": "claude", "host": "h1"}
HEAD = "d" * 40


def script(tmp: Path, body: str) -> list[str]:
    p = tmp / "gate.py"
    p.write_text(textwrap.dedent(body))
    return [sys.executable, str(p), "{task}"]


class ChecksTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.state = self.tmp / "state"
        self.cfg = load_config(Path("/nonexistent"))
        p = mock.patch.object(checks, "task_head", return_value=HEAD)
        p.start()
        self.addCleanup(p.stop)

    def spool(self):
        return [json.loads(l) for l in (self.state / events.SPOOL_NAME).read_text().splitlines()]

    def run_gate(self, body, timeout=30):
        self.cfg.checks.presubmit = script(self.tmp, body)
        self.cfg.checks.timeout_seconds = timeout
        out, err = io.StringIO(), io.StringIO()
        code = checks.run_check(self.cfg, "alpha", state_dir=self.state, actor=ACTOR, out=out, err=err)
        return code, out.getvalue(), err.getvalue(), self.spool()[-1]["payload"]

    def assert_not_green(self, payload):
        ev = {"type": "check", "commit": HEAD, "payload": payload}
        text, stale, p = projection._check([ev], HEAD)
        self.assertGreaterEqual(p["fail"], 1)

    def test_clean_parsed_run_recorded(self):
        code, out, err, p = self.run_gate('print("0 FAIL · 3 WARN · 23 PASS")\n')
        self.assertEqual(code, 0)
        self.assertEqual((p["fail"], p["warn"], p["pass"], p["parsed"]), (0, 3, 23, True))
        self.assertEqual(self.spool()[-1]["commit"], HEAD)

    def test_exit_and_output_preserved(self):
        code, out, err, p = self.run_gate('import sys\nprint("1 FAIL · 2 WARN · 21 PASS")\nprint("note", file=sys.stderr)\nsys.exit(1)\n')
        self.assertEqual(code, 1)
        self.assertIn("1 FAIL · 2 WARN · 21 PASS", out)
        self.assertIn("note", err)

    def test_unparsed_nonzero_is_failing(self):
        code, _, _, p = self.run_gate('import sys\nprint("boom")\nsys.exit(2)\n')
        self.assertEqual((code, p["parsed"]), (2, False))
        self.assert_not_green(p)

    def test_unparsed_zero_is_failing(self):
        code, _, _, p = self.run_gate('print("all good, trust me")\n')
        self.assertEqual(code, 0)
        self.assert_not_green(p)

    def test_timeout_recorded_as_failing(self):
        code, _, err, p = self.run_gate('import time\nprint("starting", flush=True)\ntime.sleep(30)\n', timeout=1)
        self.assertEqual(code, 124)
        self.assertIn("timed out", err)
        self.assert_not_green(p)

    def test_start_failure_recorded_as_failing(self):
        self.cfg.checks.presubmit = [str(self.tmp / "no-such-gate"), "{task}"]
        out, err = io.StringIO(), io.StringIO()
        code = checks.run_check(self.cfg, "alpha", state_dir=self.state, actor=ACTOR, out=out, err=err)
        self.assertEqual(code, 127)
        self.assert_not_green(self.spool()[-1]["payload"])

    def test_output_streams_before_exit(self):
        self.cfg.checks.presubmit = script(self.tmp, 'import time\nprint("first line", flush=True)\ntime.sleep(2)\nprint("0 FAIL · 0 WARN · 1 PASS")\n')
        seen = {}

        class Watch(io.StringIO):
            def write(self, s):
                if "first line" in s and "t" not in seen:
                    seen["t"] = time.monotonic()
                return super().write(s)

        start = time.monotonic()
        checks.run_check(self.cfg, "alpha", state_dir=self.state, actor=ACTOR, out=Watch(), err=io.StringIO())
        self.assertLess(seen["t"] - start, 1.5)

    def test_tail_is_bounded(self):
        code, out, _, p = self.run_gate('print("x" * 500000)\nprint("0 FAIL · 0 WARN · 2 PASS")\n')
        self.assertTrue(p["parsed"])
        self.assertGreater(len(out), 500000)          # everything passed through

    def test_multibyte_across_chunk_boundary(self):
        body = 'import sys\ns = "x" * 4095 + "·" + "y" * 10\nsys.stdout.write(s)\nprint("\\n0 FAIL · 0 WARN · 1 PASS")\n'
        code, out, _, p = self.run_gate(body)
        self.assertIn("x" * 4095 + "·" + "y" * 10, out)
        self.assertNotIn("\ufffd", out)
        self.assertTrue(p["parsed"])

    def test_stderr_flood_does_not_evict_stdout_summary(self):
        body = 'import sys\nprint("0 FAIL · 1 WARN · 9 PASS", flush=True)\nsys.stderr.write("e" * 200000)\n'
        code, _, err, p = self.run_gate(body)
        self.assertTrue(p["parsed"])
        self.assertEqual((p["warn"], p["pass"]), (1, 9))
        self.assertGreaterEqual(len(err), 200000)

    def test_parse_input_is_bounded(self):
        seen = {}
        orig = checks.parse_summary

        def spy(text, pattern):
            seen["n"] = len(text)
            return orig(text, pattern)

        with mock.patch.object(checks, "parse_summary", spy):
            self.run_gate('print("x" * 500000)\nprint("0 FAIL · 0 WARN · 2 PASS")\n')
        self.assertLessEqual(seen["n"], checks.TAIL_BYTES)

    def test_no_gate_configured(self):
        self.cfg.checks.presubmit = []
        self.assertEqual(checks.run_check(self.cfg, "alpha", state_dir=self.state, err=io.StringIO()), 2)

    def test_bad_summary_regex_is_config_error(self):
        f = self.tmp / "c.toml"
        f.write_text('[checks]\nsummary_regex = "(unclosed"\n')
        with self.assertRaises(ValueError):
            load_config(f)

    def test_review_requires_verdict_and_commit(self):
        self.assertFalse(checks.add_review(self.cfg, "alpha", "lgtm", 4, "", state_dir=self.state, actor=ACTOR)[0])
        self.assertFalse(checks.add_review(self.cfg, "alpha", "ready", 9, "", state_dir=self.state, actor=ACTOR)[0])
        with mock.patch.object(checks, "task_head", return_value=None):
            ok, why = checks.add_review(self.cfg, "alpha", "ready", 4, "", state_dir=self.state, actor=ACTOR)
        self.assertFalse(ok)
        ok, commit = checks.add_review(self.cfg, "alpha", "ready", 4, "looks good", state_dir=self.state, actor=ACTOR)
        self.assertTrue(ok)
        ev = self.spool()[-1]
        self.assertEqual((ev["type"], ev["commit"], ev["payload"]["confidence"]), ("review", HEAD, 4))


class RecordImportTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.dir = Path(td.name)
        self.cfg = load_config(Path("/nonexistent"))
        p = mock.patch.object(checks, "task_head", return_value=HEAD)
        p.start()
        self.addCleanup(p.stop)

    def test_record_and_import(self):
        ok, commit = checks.record_check(self.cfg, "alpha", passed=20, warn=1, fail=0, summary="clean",
                                         state_dir=self.dir / "s", actor=ACTOR)
        self.assertTrue(ok)
        runs = self.dir / "runs"
        runs.mkdir()
        (runs / "alpha.txt").write_text("  FAIL stage x: pending\n  1 FAIL · 2 WARN · 21 PASS\n")
        (runs / "beta.txt").write_text("no summary here\n")
        (runs / "ghost.txt").write_text("0 FAIL · 0 WARN · 1 PASS\n")
        res = dict(checks.import_dir(self.cfg, runs, state_dir=self.dir / "s", known={"alpha", "beta"}, actor=ACTOR))
        self.assertEqual(res["alpha"], "P21 W2 F1")
        self.assertIn("no summary", res["beta"])
        self.assertIn("unknown", res["ghost"])
        evs = [json.loads(l) for l in (self.dir / "s" / events.SPOOL_NAME).read_text().splitlines()]
        self.assertEqual([e["payload"].get("imported_from", "")[:6] for e in evs], ["manual", "import"])
        self.assertEqual(evs[-1]["payload"]["summary"], "FAIL stage x: pending")

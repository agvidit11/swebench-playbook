import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workboard import checks, events
from workboard.config import load_config

ACTOR = {"session_id": "s1", "alias": "h1·lane", "kind": "claude", "host": "h1"}
HEAD = "d" * 40


class ChecksTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.state = Path(td.name)
        self.cfg = load_config(Path("/nonexistent"))
        self.cfg.checks.presubmit = ["gate", "{task}"]
        p = mock.patch.object(checks, "task_head", return_value=HEAD)
        p.start()
        self.addCleanup(p.stop)

    def spool(self):
        return [json.loads(l) for l in (self.state / events.SPOOL_NAME).read_text().splitlines()]

    def runner(self, rc, stdout):
        calls = []

        def run(argv, **kw):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, rc, stdout, "note on stderr\n")
        run.calls = calls
        return run

    def test_check_run_preserves_exit_and_output(self):
        out, err = io.StringIO(), io.StringIO()
        r = self.runner(1, "  FAIL stage x\n  1 FAIL · 2 WARN · 21 PASS\n")
        code = checks.run_check(self.cfg, "alpha", state_dir=self.state, actor=ACTOR, runner=r, out=out, err=err)
        self.assertEqual(code, 1)
        self.assertIn("1 FAIL · 2 WARN · 21 PASS", out.getvalue())
        self.assertIn("note on stderr", err.getvalue())
        self.assertEqual(r.calls[0], ["gate", "alpha"])

    def test_check_recorded_with_commit_counts(self):
        checks.run_check(self.cfg, "alpha", state_dir=self.state, actor=ACTOR,
                         runner=self.runner(0, "0 FAIL · 3 WARN · 23 PASS\n"), out=io.StringIO(), err=io.StringIO())
        ev = self.spool()[-1]
        self.assertEqual(ev["type"], "check")
        self.assertEqual(ev["commit"], HEAD)
        self.assertEqual((ev["payload"]["fail"], ev["payload"]["warn"], ev["payload"]["pass"]), (0, 3, 23))

    def test_unparsed_output_still_recorded_with_exit(self):
        checks.run_check(self.cfg, "alpha", state_dir=self.state, actor=ACTOR, runner=self.runner(2, "boom\n"),
                         out=io.StringIO(), err=io.StringIO())
        p = self.spool()[-1]["payload"]
        self.assertEqual((p["exit"], p["parsed"]), (2, False))

    def test_no_gate_configured(self):
        self.cfg.checks.presubmit = []
        self.assertEqual(checks.run_check(self.cfg, "alpha", state_dir=self.state, err=io.StringIO()), 2)

    def test_review_requires_verdict_and_commit(self):
        self.assertFalse(checks.add_review(self.cfg, "alpha", "lgtm", 4, "", state_dir=self.state, actor=ACTOR)[0])
        self.assertFalse(checks.add_review(self.cfg, "alpha", "ready", 9, "", state_dir=self.state, actor=ACTOR)[0])
        with mock.patch.object(checks, "task_head", return_value=None):
            ok, why = checks.add_review(self.cfg, "alpha", "ready", 4, "", state_dir=self.state, actor=ACTOR)
        self.assertFalse(ok)
        self.assertIn("commit", why)
        ok, commit = checks.add_review(self.cfg, "alpha", "ready", 4, "looks good", state_dir=self.state, actor=ACTOR)
        self.assertTrue(ok)
        ev = self.spool()[-1]
        self.assertEqual((ev["type"], ev["commit"], ev["payload"]["confidence"]), ("review", HEAD, 4))

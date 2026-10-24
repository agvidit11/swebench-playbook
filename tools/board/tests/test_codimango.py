import json, subprocess, tempfile, unittest
from pathlib import Path
from workboard.config import load_config
from workboard.sources.codimango import CodimangoSource

FIX = Path(__file__).parent / "fixtures"


class FakeRunner:
    """Stands in for subprocess.run; maps the presence of --archived to a canned result."""
    def __init__(self, active, archived=None, rc=0, timeout=False, stderr="Need help? Run `codimango feedback`.\n"):
        self.active, self.archived, self.rc, self.timeout, self.stderr = active, archived, rc, timeout, stderr
        self.calls = []

    def __call__(self, argv, **kw):
        self.calls.append(argv)
        if self.timeout:
            raise subprocess.TimeoutExpired(argv, kw.get("timeout"))
        body = self.archived if "--archived" in argv else self.active
        out = (FIX / body).read_text() if body else '{"tasks": [], "totalExact": true, "trainingStatusDegraded": false}'
        return subprocess.CompletedProcess(argv, self.rc, out, self.stderr)


class CodimangoTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.cache = Path(td.name)
        self.cfg = load_config(Path("/nonexistent"))

    def src(self, runner):
        return CodimangoSource(self.cfg, runner=runner, cache_dir=self.cache)

    def test_ok_fields_namespaced_and_prose_dropped(self):
        res = self.src(FakeRunner("codimango_ok.json", "codimango_archived.json")).fetch()
        self.assertTrue(res.health.ok)
        obs = {o.entity_id: o for o in res.observations}
        self.assertEqual(obs["beta-task"].fields["codimango.status"], "accepted")
        self.assertEqual(obs["delta-task"].fields["codimango.status"], "archived")
        self.assertEqual(obs["delta-task"].fields["codimango.status_before_archive"], "needs_revision")
        self.assertNotIn("codimango.metadata", obs["alpha-task"].fields)
        self.assertNotIn("codimango.qualitative_result", obs["alpha-task"].fields)
        self.assertEqual(obs["alpha-task"].authority["codimango.status"], "authoritative")
        raw = (self.cache / "codimango-last-good.json").read_text()
        self.assertNotIn("x" * 1000, raw)   # cache keeps only normalised fields

    def test_nonzero_exit_keeps_last_good_and_unhealthy(self):
        self.src(FakeRunner("codimango_ok.json")).fetch()
        res = self.src(FakeRunner("codimango_ok.json", rc=1, stderr="error: auth expired")).fetch()
        self.assertFalse(res.health.ok)
        self.assertIn("auth expired", res.health.detail)
        self.assertEqual(len(res.observations), 3)          # served from last-good cache
        self.assertIn("SYNC_FAILED", [f.code for f in res.findings])

    def test_timeout_marks_stale(self):
        self.src(FakeRunner("codimango_ok.json")).fetch()
        res = self.src(FakeRunner(None, timeout=True)).fetch()
        self.assertFalse(res.health.ok)
        self.assertIn("timeout", res.health.detail)
        self.assertIn("CACHE_STALE", [f.code for f in res.findings])

    def test_no_cache_and_failure_is_empty_unhealthy(self):
        res = self.src(FakeRunner("codimango_garbage.txt")).fetch()
        self.assertFalse(res.health.ok)
        self.assertEqual(res.observations, [])
        self.assertIn("SYNC_FAILED", [f.code for f in res.findings])

    def test_incomplete_total_finding(self):
        res = self.src(FakeRunner("codimango_incomplete.json")).fetch()
        self.assertIn("INCOMPLETE", [f.code for f in res.findings])

    def test_argv_not_shell(self):
        runner = FakeRunner("codimango_ok.json")
        self.src(runner).fetch()
        self.assertEqual(runner.calls[0], ["codimango", "task", "list", "--json"])
        self.assertIn(["codimango", "task", "list", "--archived", "--json"], runner.calls)

    def test_fresh_cache_skips_network(self):
        r1 = FakeRunner("codimango_ok.json")
        self.src(r1).fetch()
        r2 = FakeRunner("codimango_ok.json")
        res = self.src(r2).fetch(max_age_seconds=300)
        self.assertEqual(r2.calls, [])
        self.assertTrue(res.health.ok)


class CodimangoStrictTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.cache = Path(td.name)
        self.cfg = load_config(Path("/nonexistent"))
        self.fix = Path(td.name) / "fx"; self.fix.mkdir()

    def runner_text(self, active_text, archived_text='{"tasks": [], "totalExact": true, "trainingStatusDegraded": false}'):
        def run(argv, **kw):
            return subprocess.CompletedProcess(argv, 0, archived_text if "--archived" in argv else active_text, "")
        return run

    def src(self, runner):
        return CodimangoSource(self.cfg, runner=runner, cache_dir=self.cache)

    def test_incomplete_keeps_previous_complete_cache(self):
        two = json.dumps({"tasks": [{"name": "a", "status": "draft"}, {"name": "b", "status": "draft"}],
                          "totalExact": True, "trainingStatusDegraded": False})
        one = json.dumps({"tasks": [{"name": "a", "status": "draft"}], "totalExact": False, "trainingStatusDegraded": False})
        self.src(self.runner_text(two)).fetch()
        res = self.src(self.runner_text(one)).fetch()
        self.assertFalse(res.health.ok)
        self.assertEqual({o.entity_id for o in res.observations}, {"a", "b"})
        self.assertIn("INCOMPLETE", [f.code for f in res.findings])
        cached = json.loads((self.cache / "codimango-last-good.json").read_text())
        self.assertEqual(len(cached["rows"]), 2)

    def test_missing_flags_rejected(self):
        res = self.src(self.runner_text('{"tasks": []}')).fetch()
        self.assertFalse(res.health.ok)
        self.assertIn("SYNC_FAILED", [f.code for f in res.findings])

    def test_string_flags_rejected(self):
        res = self.src(self.runner_text('{"tasks": [], "totalExact": "false", "trainingStatusDegraded": "false"}')).fetch()
        self.assertFalse(res.health.ok)

    def test_scalar_task_entry_rejected(self):
        res = self.src(self.runner_text('{"tasks": [3], "totalExact": true, "trainingStatusDegraded": false}')).fetch()
        self.assertFalse(res.health.ok)
        self.assertEqual(res.observations, [])

    def test_invalid_cache_treated_as_absent(self):
        for bad in ({"rows": []}, {"fetched_at": "2026-10-23T00:00:00+00:00", "total_exact": True,
                                    "training_degraded": False, "rows": [3]}):
            (self.cache / "codimango-last-good.json").write_text(json.dumps(bad))
            res = self.src(FakeRunner(None, rc=2)).fetch()
            self.assertFalse(res.health.ok)
            self.assertEqual(res.observations, [])


class AuthErrorTest(unittest.TestCase):
    def test_expired_login_names_the_fix(self):
        import tempfile
        cfg = load_config(Path("/nonexistent"))
        out = '{"error":{"fix":"codimango auth setup","kind":"authentication","message":"Unauthorized"}}'
        runner = lambda argv, **kw: subprocess.CompletedProcess(argv, 9, out, "Need help?")
        with tempfile.TemporaryDirectory() as d:
            res = CodimangoSource(cfg, runner=runner, cache_dir=Path(d)).fetch()
        self.assertFalse(res.health.ok)
        self.assertIn("codimango auth setup", res.health.detail)

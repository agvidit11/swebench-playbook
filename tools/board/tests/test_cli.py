import contextlib, io, json, os, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from workboard import __main__ as cli, app
from workboard.model import Finding, SourceHealth, TaskView
from workboard.sync import SyncState

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)


def view(name, **f):
    base = {"group": "READY", "next": "RUN check", "state": "DRAFT", "state_age_s": 3600, "age_level": "ok",
            "owner": "", "claim_health": "FREE", "valid": "PASS", "review": "R0", "confidence": None,
            "confidence_stale": False, "sync": "OK", "check": "NONE", "check_stale": False, "pushes": "1+0",
            "pushes_before_submit": 1, "pushes_after_submit": 0, "round": None, "track": "", "dissent": 0}
    base.update(f)
    return TaskView(name, base, [])


def snap(healthy=True):
    h = SourceHealth("codimango", healthy, NOW, 900, "live" if healthy else "timeout after 60s")
    views = [view("alpha-task"), view("beta-task", claim_health="EXPIRED", owner="h2·x"),
             view("gamma-task", group="DONE", state="ACCEPTED", next="—")]
    return app.Snapshot(views, [], [], {"codimango": h},
                        [] if healthy else [Finding("SYNC_FAILED", "warn", "codimango fetch failed", "fix")],
                        SyncState(last_pull_ok=True, last_push_ok=True), NOW)


class CliTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.env = mock.patch.dict(os.environ, {"WORKBOARD_CACHE": td.name, "WORKBOARD_CONFIG": "/nonexistent",
                                                 "NO_COLOR": "1"})
        self.env.start(); self.addCleanup(self.env.stop)

    def run_cli(self, argv, healthy=True):
        out = io.StringIO()
        with mock.patch.object(cli, "_gather", lambda args, cfg: snap(healthy)), \
             mock.patch.object(cli, "_reviews_text", lambda cfg, t: None), \
             contextlib.redirect_stdout(out):
            code = cli.main(argv)
        return code, out.getvalue()

    def test_parser_accepts_documented_grammar(self):
        p = cli.build_parser()
        for argv in (["list", "--group", "state"], ["show", "x", "--history", "--sources"],
                     ["available", "--reason", "expired"], ["plugins", "list"], ["changes", "--since", "2h"],
                     ["list", "--wide", "--all", "--strict", "--json"]):
            p.parse_args(argv)

    def test_every_read_command_prints_banner(self):
        for argv in (["list"], ["show", "alpha", "--no-reviews"], ["explain", "alpha"], ["available"], ["changes"]):
            code, out = self.run_cli(argv)
            self.assertTrue(out.splitlines()[0].startswith("codimango"), (argv, out[:80]))

    def test_strict_nonzero_when_unhealthy(self):
        for argv in (["list"], ["show", "alpha", "--no-reviews"], ["explain", "alpha"], ["available"], ["changes"]):
            code, out = self.run_cli(argv + ["--strict"], healthy=False)
            self.assertEqual(code, 1, argv)
            self.assertIn("SYNC FAILED", out)
            code, _ = self.run_cli(argv + ["--strict"], healthy=True)
            self.assertEqual(code, 0, argv)

    def test_json_envelope(self):
        for argv in (["list"], ["show", "alpha", "--no-reviews"], ["explain", "alpha"], ["available"], ["changes"]):
            code, out = self.run_cli(argv + ["--json"], healthy=False)
            data = json.loads(out)
            for key in ("health", "sync_state", "findings", "result"):
                self.assertIn(key, data, argv)
            self.assertFalse(data["health"]["codimango"]["ok"])

    def test_review_fetch_failure_is_visible(self):
        code, out = self.run_cli(["show", "alpha"])
        self.assertIn("reviews unavailable", out)
        code, _ = self.run_cli(["show", "alpha", "--strict"])
        self.assertEqual(code, 1)
        code, out = self.run_cli(["show", "alpha", "--json"])
        data = json.loads(out)
        self.assertFalse(data["health"]["reviews"]["ok"])
        self.assertIn("REVIEWS_UNAVAILABLE", [f["code"] for f in data["findings"]])

    def test_show_history_opt_in(self):
        code, out = self.run_cli(["show", "alpha", "--json"])
        self.assertNotIn("history", json.loads(out)["result"])
        code, out = self.run_cli(["show", "alpha", "--json", "--history"])
        self.assertIn("history", json.loads(out)["result"])

    def test_changes_since_timestamp(self):
        code, out = self.run_cli(["changes", "--since", "2026-10-23T09:00:00-07:00", "--json"])
        self.assertEqual(json.loads(out)["result"], [])
        with self.assertRaises(SystemExit):
            self.run_cli(["changes", "--since", "2026-10-23T09:00:00"])

    def test_config_json_parseable(self):
        for action in ("show", "validate"):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cli.main(["config", action, "--json"])
            json.loads(out.getvalue())

    def test_plugins_doctor_reports_failures(self):
        out = io.StringIO()
        with mock.patch.object(cli, "load_config", lambda: self._cfg_with_plugin()), contextlib.redirect_stdout(out):
            code = cli.main(["plugins", "doctor", "--json"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out.getvalue())["ok"])

    def _cfg_with_plugin(self):
        from workboard.config import load_config
        cfg = load_config(Path("/nonexistent"))
        cfg.plugins.enabled = ["no_such_plugin_abc"]
        return cfg

    def test_available_reason_filter(self):
        code, out = self.run_cli(["available", "--reason", "expired", "--json"])
        names = [r["task"] for r in json.loads(out)["result"]]
        self.assertEqual(names, ["beta-task"])

    def test_default_command_is_list(self):
        code, out = self.run_cli(["--plain"])
        self.assertIn("TASK", out)
        self.assertIn("Done: 1", out)

    def test_changes_after_look(self):
        self.run_cli(["list"])
        code, out = self.run_cli(["changes"])
        self.assertIn("nothing changed", out)


class ClaimCommandTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        p = mock.patch.dict(os.environ, {"WORKBOARD_CACHE": td.name, "WORKBOARD_STATE": td.name,
                                         "WORKBOARD_CONFIG": "/nonexistent", "NO_COLOR": "1"})
        p.start()
        self.addCleanup(p.stop)

    def snap_with_sessions(self):
        s = snap()
        from workboard import events as ev
        for sid, alias, kind in (("s1", "h1·lane orchestrator loop", "claude"), ("s2", "h2·harness loop", "claude"),
                                 ("s3", "h2·NWR history", "claude")):
            e = ev.stamp(ev.new_event("alias", None, {"alias": alias},
                                      actor={"session_id": sid, "alias": alias, "kind": kind, "host": alias[:2]},
                                      commit=None, source="hook"), alias[:2], 1)
            s.events.append(e)
        return s

    def drive(self, argv, fresh=(True, ""), claim_status="ACQUIRED"):
        from workboard import coord, claims
        out, err = io.StringIO(), io.StringIO()
        captured = {}

        def fake_claim(cfg, task, **kw):
            captured.update(kw, task=task)
            return claims.ClaimResult(claim_status, "a" * 40, "", {"alias": "h1·me"})

        with mock.patch.object(cli, "_gather", lambda a, c: self.snap_with_sessions()), \
             mock.patch.object(coord, "ledger_fresh", return_value=fresh), \
             mock.patch.object(coord, "claim", fake_claim), \
             mock.patch("workboard.sync.sync"), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(argv)
            except SystemExit as exc:
                code = exc.code
        if isinstance(code, str):           # SystemExit("message"): Python prints it to stderr and exits 1
            err.write(code)
            code = 1
        return code, out.getvalue() + err.getvalue(), captured

    def test_claim_by_task_fragment(self):
        code, out, cap = self.drive(["claim", "alpha"])
        self.assertEqual(code, 0)
        self.assertEqual(cap["task"], "alpha-task")
        self.assertIn("claimed alpha-task", out)

    def test_claim_to_unique_alias_keeps_kind_and_host(self):
        code, out, cap = self.drive(["claim", "alpha", "--to", "harness"])
        self.assertEqual(code, 0)
        self.assertEqual(cap["to_actor"]["session_id"], "s2")
        self.assertEqual((cap["to_actor"]["kind"], cap["to_actor"]["host"]), ("claude", "h2"))

    def test_claim_to_missing_or_ambiguous_alias(self):
        code, out, _ = self.drive(["claim", "alpha", "--to", "nobody"])
        self.assertNotEqual(code, 0)
        self.assertIn("no known session", out)
        code, out, _ = self.drive(["claim", "alpha", "--to", "loop"])
        self.assertIn("ambiguous", out)

    def test_claim_lost_exit_1(self):
        code, out, _ = self.drive(["claim", "alpha"], claim_status="LOST")
        self.assertEqual(code, 1)
        self.assertIn("already owned", out)

    def test_claim_and_release_refuse_when_ledger_stale(self):
        for argv in (["claim", "alpha"], ["release", "alpha-task", "--reason", "x"]):
            code, out, _ = self.drive(argv, fresh=(False, "push failed"))
            self.assertEqual(code, 2, argv)
            self.assertIn("refusing", out)


class SyncCommandTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        p = mock.patch.dict(os.environ, {"WORKBOARD_STATE": td.name, "WORKBOARD_CACHE": td.name,
                                         "WORKBOARD_CONFIG": "/nonexistent"})
        p.start()
        self.addCleanup(p.stop)

    def code_for(self, state):
        with mock.patch("workboard.sync.sync", return_value=state), mock.patch("workboard.app.refresh_claims_cache"), \
             contextlib.redirect_stdout(io.StringIO()):
            return cli.main(["sync"])

    def test_exit_codes(self):
        self.assertEqual(self.code_for(SyncState(last_pull_ok=False)), 1)
        self.assertEqual(self.code_for(SyncState(last_pull_ok=True, last_push_ok=False, pending=3)), 1)
        self.assertEqual(self.code_for(SyncState(last_pull_ok=True, last_push_ok=False, pending=0)), 0)
        self.assertEqual(self.code_for(SyncState(last_pull_ok=True, last_push_ok=True)), 0)


class StealEvidenceCommandTest(ClaimCommandTest):
    def test_steal_passes_unhealthy_evidence(self):
        s = self.snap_with_sessions()
        s.health["claims"] = SourceHealth("claims", False, NOW, 0, "fetch failed")
        captured = {}
        from workboard import coord, claims

        def fake_claim(cfg, task, **kw):
            captured.update(kw)
            return claims.ClaimResult("REFUSED", None, "steal needs a healthy claim source and clock")

        with mock.patch.object(cli, "_gather", lambda a, c: s), \
             mock.patch.object(coord, "ledger_fresh", return_value=(True, "")), \
             mock.patch.object(coord, "claim", fake_claim), mock.patch("workboard.sync.sync"), \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["claim", "alpha", "--steal"])
        self.assertEqual(code, 1)
        self.assertFalse(captured["source_healthy"])

    def test_steal_with_clock_skew_finding(self):
        s = self.snap_with_sessions()
        s.health["claims"] = SourceHealth("claims", True, NOW, 0, "ok")
        s.findings.append(Finding("CLOCK_SKEW", "warn", "future events", "fix clock"))
        captured = {}
        from workboard import coord, claims

        def fake_claim(cfg, task, **kw):
            captured.update(kw)
            return claims.ClaimResult("REFUSED", None, "x")

        with mock.patch.object(cli, "_gather", lambda a, c: s), \
             mock.patch.object(coord, "ledger_fresh", return_value=(True, "")), \
             mock.patch.object(coord, "claim", fake_claim), mock.patch("workboard.sync.sync"), \
             contextlib.redirect_stdout(io.StringIO()):
            cli.main(["claim", "alpha", "--steal"])
        self.assertTrue(captured["source_healthy"])
        self.assertFalse(captured["clock_healthy"])


class ReviewAddCommandTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        p = mock.patch.dict(os.environ, {"WORKBOARD_STATE": td.name, "WORKBOARD_CACHE": td.name,
                                         "WORKBOARD_CONFIG": "/nonexistent"})
        p.start()
        self.addCleanup(p.stop)

    def code(self, fresh, after):
        from workboard import checks, coord
        with mock.patch.object(coord, "ledger_fresh", return_value=fresh), \
             mock.patch.object(checks, "add_review", return_value=(True, "e" * 40)), \
             mock.patch("workboard.sync.sync", return_value=after), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            return cli.main(["review", "add", "alpha-task", "--verdict", "ready", "--confidence", "4"]), err.getvalue()

    def test_busy_or_failed_pull_refused(self):
        for why in ("another sync is running", "pull failed: x"):
            code, err = self.code((False, why), SyncState(last_pull_ok=True, last_push_ok=True))
            self.assertEqual(code, 2)
            self.assertIn("refusing", err)

    def test_push_left_pending_reports_queued(self):
        code, err = self.code((True, ""), SyncState(last_pull_ok=True, last_push_ok=False, pending=1, error="push failed"))
        self.assertEqual(code, 1)
        self.assertIn("queued locally", err)

    def test_success(self):
        code, err = self.code((True, ""), SyncState(last_pull_ok=True, last_push_ok=True, pending=0))
        self.assertEqual(code, 0)


class StatsCommandTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        p = mock.patch.dict(os.environ, {"WORKBOARD_CACHE": td.name, "WORKBOARD_CONFIG": "/nonexistent", "NO_COLOR": "1"})
        p.start()
        self.addCleanup(p.stop)

    def out(self, argv):
        buf = io.StringIO()
        with mock.patch.object(cli, "_gather", lambda a, c: snap()), contextlib.redirect_stdout(buf):
            code = cli.main(argv)
        return code, buf.getvalue()

    def test_narrow_plain_keeps_full_definitions(self):
        from workboard import stats as st
        code, text = self.out(["stats", "--plain", "--width", "60"])
        for line in text.splitlines():
            self.assertLessEqual(len(line), 60, line)
        joined = " ".join(l.strip() for l in text[text.index("Definitions:"):].splitlines())
        self.assertIn(st.DEFINITIONS.format(tz="America/Los_Angeles"), joined.replace("Definitions: ", ""))

    def test_json_has_definitions_and_window(self):
        code, text = self.out(["stats", "--json", "--from", "2026-10-01", "--to", "2026-10-21"])
        data = json.loads(text)["result"]
        self.assertIn("definitions", data)
        self.assertEqual(data["window"]["from"][:10], "2026-10-01")
        for key in ("flow", "funnel", "weekly", "pipeline_age"):
            self.assertIn(key, data)

    def test_reversed_range_rejected(self):
        with self.assertRaises(SystemExit):
            self.out(["stats", "--from", "2026-10-21", "--to", "2026-10-01"])
        with self.assertRaises(SystemExit):
            self.out(["stats", "--weeks", "0"])

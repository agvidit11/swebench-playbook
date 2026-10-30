import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workboard import facts, stats2
from workboard.model import Observation


def snap(obs, events=()):
    return SimpleNamespace(observations=obs, events=list(events), sessions=[], usage={},
                           health={}, now=datetime(2026, 10, 29, 12, tzinfo=timezone.utc))


class Stats2Test(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.dir = Path(td.name)
        self.cfg = SimpleNamespace(repositories=[], user=SimpleNamespace(timezone="America/Los_Angeles"))
        p = mock.patch.object(stats2, "_git_commits", return_value={"t": [
            {"sha": "a", "at": "2026-10-01T10:00:00+00:00", "subject": "draft", "paths": ["instruction.md", "tests/x.py"]},
            {"sha": "b", "at": "2026-10-03T10:00:00+00:00", "subject": "tighten step 2 (avocado 0/5)", "paths": ["tests/x.py"]},
            {"sha": "c", "at": "2026-10-12T10:00:00+00:00", "subject": "address review", "paths": ["tests/x.py"]}]})
        p.start()
        self.addCleanup(p.stop)

    def build(self, rows, events=()):
        obs = [Observation("codimango", "t", datetime.now(timezone.utc),
                           {"codimango.status": "accepted", "codimango.format": "swe_bench_multi_turn",
                            "codimango.created_at": "2026-10-01T00:00:00Z",
                            "codimango.entered_pool_at": "2026-10-15T00:00:00Z",
                            "codimango.reviewed_at": "2026-10-20T00:00:00Z"}, {})]
        return stats2.build(snap(obs, events), self.cfg, self.dir, facts_rows=rows)["tasks"][0]

    def test_submissions_and_accepts_come_from_facts(self):
        rows = facts.parse_comments("t", {"comments": [
            {"id": "1", "isSystemEvent": True, "body": "Task was submitted for review (v1.0)", "createdAt": "2026-10-05T00:00:00Z"},
            {"id": "2", "isSystemEvent": True, "body": "Task was submitted for review (v2.0)", "createdAt": "2026-10-15T00:00:00Z"}]})
        rows += facts.parse_reviews("t", {"complete": True, "reviews": [
            {"id": "r1", "decision": "revision", "reviewedAt": "2026-10-10T00:00:00Z"},
            {"id": "r2", "decision": "accept", "reviewedAt": "2026-10-20T00:00:00Z"}]})
        t = self.build(rows)
        self.assertEqual([s[1] for s in t["sub"]], [1, 2])
        self.assertFalse(t["subfb"])
        self.assertEqual([d[1] for d in t["dec"]], ["revision", "accept"])
        phases = {a[1] for a in t["act"]}
        self.assertIn("drafting", phases)
        self.assertIn("calibration", phases)
        self.assertIn("revision", phases)          # the commit after the revision decision

    def test_fallbacks_are_flagged(self):
        t = self.build([])
        self.assertTrue(t["subfb"])
        self.assertEqual(t["sub"][0][0], "2026-10-15T00:00:00Z")
        self.assertEqual(t["dec"][0][1], "accept_fb")   # never a synthesized human accept
        self.assertFalse(t["rc"])

    def test_self_report_is_high_confidence_attribution(self):
        ev = {"type": "report", "occurred_at": "2026-10-12T11:00:00+00:00", "entity": {"kind": "task", "id": "t"},
              "actor": {"kind": "claude", "session_id": "s1"}, "host_id": "h", "seq": 1,
              "payload": {"phase": "revision", "model": "gpt-5.6-sol", "kind": "codex", "summary": "x"}}
        t = self.build([], [ev])
        rep = [a for a in t["act"] if "report" in a[6]]
        self.assertEqual([(a[1], a[2], a[3], a[5], a[8]) for a in rep], [("revision", "codex", "gpt-5.6-sol", "high", "high")])

    def test_model_name_normalised(self):
        self.assertEqual(stats2._model_name("{'model_id': 'muse-spark-1.4', 'provider_id': 'meta'}"), "muse-spark-1.4")
        self.assertEqual(stats2._model_name("gpt-5.6-sol"), "gpt-5.6-sol")
        self.assertEqual(stats2._model_name(None), "unknown")


if __name__ == "__main__":
    unittest.main()

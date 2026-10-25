import itertools
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from workboard.config import load_config
from workboard.model import Observation
from workboard.ownership import reduce_ownership
from workboard.projection import project


NOW = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)


class OwnershipReducerTest(unittest.TestCase):
    def test_every_axis_combination_and_free_only_when_free(self):
        for assignment, active, pipeline, recent, done in itertools.product(
                ("unassigned", "claimed", "legacy", "conflict"), (False, True), (False, True), (False, True), (False, True)):
            result = reduce_ownership(
                {"state": assignment},
                {"state": "active" if active else "inactive", "last_at": NOW.timestamp() if active else None},
                {"state": "validating" if pipeline else "none"},
                {"at": (NOW - timedelta(hours=1)).isoformat() if recent else (NOW - timedelta(days=5)).isoformat()},
                done=done, actionable=True, sources_fresh=True, now=NOW.timestamp())
            state = result["availability"]["state"]
            self.assertEqual(result["availability"]["free"], state == "available")
            if state == "available":
                self.assertEqual(assignment, "unassigned")
                self.assertFalse(active); self.assertFalse(pipeline); self.assertFalse(recent); self.assertFalse(done)

    def test_precedence_and_unknown(self):
        clear = ({"state": "unassigned"}, {"state": "inactive", "last_at": None},
                 {"state": "none"}, {"at": None})
        self.assertEqual(reduce_ownership(*clear, done=False, actionable=False, sources_fresh=False,
                                          now=NOW.timestamp())["availability"]["state"], "never_seen")
        self.assertEqual(reduce_ownership(*clear, done=False, actionable=True, sources_fresh=True,
                                          now=NOW.timestamp())["availability"]["state"], "available")


class ProjectionOwnershipDisplayTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))

    def cm(self, task, status="draft", valid="passing", observed=NOW):
        return Observation("codimango", task, observed, {"codimango.status": status,
                           "codimango.validation_status": valid, "codimango.created_at": NOW.isoformat()})

    def test_pipeline_and_recent_change_are_not_free(self):
        queue = project([self.cm("queue", "being_reviewed")], [], self.cfg, NOW)[0]
        self.assertEqual((queue.fields["ownership_state"], queue.fields["claim_health"]), ("in_pipeline", "PIPELINE"))
        git = Observation("git", "recent", NOW, {"git.task_head": "a" * 40,
                          "git.task_head_time": (NOW - timedelta(hours=2)).isoformat(), "git.commit_times": []})
        recent = project([git], [], self.cfg, NOW)[0]
        self.assertEqual((recent.fields["ownership_state"], recent.fields["claim_health"]), ("worked_recently", "RECENT"))
        free = project([self.cm("free")], [], self.cfg, NOW)[0]
        self.assertEqual((free.fields["ownership_state"], free.fields["availability"]["free"]), ("available", True))
        stale = project([self.cm("stale", observed=NOW - timedelta(hours=2))], [], self.cfg, NOW)[0]
        self.assertEqual(stale.fields["ownership_state"], "never_seen")


if __name__ == "__main__":
    unittest.main()



class IdleCheckinClearsFocusTest(unittest.TestCase):
    def test_idle_checkin_clears_earlier_focus(self):
        from workboard.ownership import reduce_focus
        now = 1_800_000_000.0
        from datetime import datetime, timezone
        iso = lambda dt: datetime.fromtimestamp(now - dt, timezone.utc).isoformat()
        evs = [{"type": "check", "entity": {"kind": "task", "id": "t1"}, "actor": {"session_id": "s"}, "occurred_at": iso(3600), "payload": {}},
               {"type": "checkin", "entity": None, "actor": {"session_id": "s"}, "occurred_at": iso(600), "payload": {"status": "idle", "tasks": []}}]
        self.assertEqual(reduce_focus({"native_id": "s", "kind": "claude"}, evs, now=now)["tasks"], [])
        evs.append({"type": "touch", "entity": {"kind": "task", "id": "t2"}, "actor": {"session_id": "s"}, "occurred_at": iso(60), "payload": {}})
        self.assertEqual(reduce_focus({"native_id": "s", "kind": "claude"}, evs, now=now)["tasks"], ["t2"])

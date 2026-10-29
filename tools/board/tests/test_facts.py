import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from workboard import facts


class FactsTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.dir = Path(td.name)
        self.store = facts.Store(self.dir)

    def test_append_is_idempotent_and_survives_torn_tail(self):
        f = facts.make("t", "status", {"status": "draft"}, "x", "1", occurred_at="2026-10-01T00:00:00Z")
        self.assertEqual(self.store.append([f]), 1)
        self.assertEqual(facts.Store(self.dir).append([f]), 0)
        with open(self.store.path, "ab") as fh:
            fh.write(b'{"schema":1,"id":"torn')
        g = facts.make("t", "status", {"status": "accepted"}, "x", "2", occurred_at="2026-10-02T00:00:00Z")
        self.assertEqual(facts.Store(self.dir).append([g]), 1)
        self.assertEqual([r["value"]["status"] for r in facts.Store(self.dir).read()], ["draft", "accepted"])

    def test_snapshot_appends_only_changed_fields(self):
        row = {"name": "t", "status": "draft", "validation_status": "passing", "commit_sha": "a" * 40}
        self.assertEqual(facts.observe_snapshot(self.store, [row], "2026-10-01T00:00:00Z"), 3)
        self.assertEqual(facts.observe_snapshot(self.store, [row], "2026-10-01T01:00:00Z"), 0)
        n = facts.observe_snapshot(self.store, [dict(row, status="being_reviewed")], "2026-10-01T02:00:00Z")
        self.assertEqual(n, 1)
        last = [r for r in self.store.read() if r["kind"] == "status"][-1]
        self.assertIsNone(last["occurred_at"])
        self.assertEqual(last["interval"], {"after": "2026-10-01T01:00:00Z", "at_or_before": "2026-10-01T02:00:00Z"})

    def test_submissions_from_system_events(self):
        doc = {"comments": [
            {"id": "1", "isSystemEvent": True, "body": "Task was submitted for review (v1.0)", "createdAt": "2026-10-07T10:00:00Z"},
            {"id": "2", "isSystemEvent": True, "body": "Reviewer claimed", "createdAt": "2026-10-07T12:00:00Z"},
            {"id": "3", "isSystemEvent": True, "body": "QRA (task) signal updated (abc)", "createdAt": "2026-10-08T00:00:00Z"},
            {"id": "4", "isSystemEvent": True, "body": "Task was submitted for review (v2.0)", "createdAt": "2026-10-10T10:00:00Z"},
            {"id": "5", "isSystemEvent": False, "body": "Task was submitted for review (v9.0)", "createdAt": "2026-10-11T10:00:00Z"}]}
        evs = [(f["value"]["event"], f["value"].get("version")) for f in facts.parse_comments("t", doc)]
        self.assertEqual(evs, [("first_submit", 1), ("review_claimed", None), ("unclassified", None), ("resubmit", 2)])

    def test_review_decisions_have_stable_identity(self):
        doc = {"complete": True, "hasMore": False, "reviews": [
            {"id": "b", "decision": "accept", "reviewedAt": "2026-10-20T00:00:00Z"},
            {"id": "a", "decision": "revision", "reviewedAt": "2026-10-10T00:00:00Z", "decisionReason": "fix  step 2"}]}
        out = facts.parse_reviews("t", doc)
        self.assertEqual([f["value"]["decision"] for f in out], ["revision", "accept"])
        self.assertEqual(out[0]["value"]["reason"], "fix step 2")
        older = {"complete": True, "reviews": [{"id": "z", "decision": "revision", "reviewedAt": "2026-10-01T00:00:00Z"}] + doc["reviews"]}
        self.store.append(out)
        self.assertEqual(self.store.append(facts.parse_reviews("t", older)), 1)   # backfill adds only the new review

    def test_edits_supersede_and_deletes_tombstone(self):
        c = {"id": "1", "isSystemEvent": True, "body": "Task was submitted for review (v1.0)", "createdAt": "2026-10-07T10:00:00Z"}
        self.store.append(facts.parse_comments("t", {"comments": [c]}))
        self.assertEqual(len(facts.latest(self.store.read(), "submission")), 1)
        later = facts.parse_comments("t", {"comments": [dict(c, deletedAt="2026-10-08T00:00:00Z")]})
        later[0]["observed_at"] = "2099-01-01T00:00:00+00:00"
        self.store.append(later)
        self.assertEqual(facts.latest(self.store.read(), "submission"), [])

    def test_batch_duplicates_written_once(self):
        f = facts.make("t", "status", {"status": "draft"}, "x", "1", occurred_at="2026-10-01T00:00:00Z")
        self.assertEqual(self.store.append([f, f]), 1)
        self.assertEqual(len(self.store.read()), 1)

    def test_hydrate_fetches_stale_submitted_tasks_within_budget(self):
        calls = []

        def runner(argv, **kw):
            calls.append(argv[1:4])
            body = {"reviews": [], "complete": True} if argv[2] == "reviews" else {"comments": []}
            return SimpleNamespace(returncode=0, stdout=json.dumps(body))
        cfg = SimpleNamespace(codimango=SimpleNamespace(command="codimango"))
        rows = [{"name": f"t{i}", "entered_pool_at": "x", "updated_at": "u"} for i in range(6)] + \
               [{"name": "draft-only", "status": "draft", "updated_at": "u"}]
        res = facts.hydrate(cfg, self.store, rows, max_tasks=4, runner=runner)
        self.assertEqual((res["fetched"], res["pending"], res["eligible"], res["covered"]), (4, 2, 6, 4))
        self.assertEqual(facts.hydrate(cfg, self.store, rows, max_tasks=4, runner=runner)["pending"], 0)
        self.assertEqual(facts.hydrate(cfg, self.store, rows, max_tasks=4, runner=runner)["fetched"], 0)

    def test_failed_refresh_is_not_coverage(self):
        ok = lambda argv, **kw: SimpleNamespace(returncode=0, stdout=json.dumps({"reviews": [], "complete": True, "comments": []}))
        bad = lambda argv, **kw: SimpleNamespace(returncode=1, stdout="")
        cfg = SimpleNamespace(codimango=SimpleNamespace(command="codimango"))
        rows = [{"name": "t", "entered_pool_at": "x", "updated_at": "u1"}]
        self.assertEqual(facts.hydrate(cfg, self.store, rows, runner=ok)["covered"], 1)
        rows[0]["updated_at"] = "u2"                   # task changed on the server, refresh fails
        res = facts.hydrate(cfg, self.store, rows, runner=bad)
        self.assertEqual((res["covered"], res["errors"]), (0, 1))


if __name__ == "__main__":
    unittest.main()

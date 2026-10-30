import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workboard import slack


class FakeTransport(slack.Transport):
    def __init__(self):
        super().__init__("C1", dry=False)
        self.posts, self.reply_rows, self.reaction_rows, self.n = [], {}, {}, 0

    def post(self, markdown, thread_ts=None, context=None, buttons=()):
        self.n += 1
        ts = f"100.{self.n:03d}"
        self.posts.append({"ts": ts, "thread": thread_ts, "text": markdown, "context": context})
        return ts

    def replies(self, root, oldest):
        return [r for r in self.reply_rows.get(root, []) if not oldest or r["message_ts"] > oldest]

    def reactions(self, ts):
        return self.reaction_rows.get(ts, [])


def ev(type_, task, payload, at="2026-10-30T17:00:00+00:00", actor=None, eid="e1"):
    return {"type": type_, "entity": {"kind": "task", "id": task} if task else None, "payload": payload,
            "occurred_at": at, "host_id": "h1", "seq": 1, "event_id": eid,
            "actor": actor or {"session_id": "s1", "alias": "h1·lane", "kind": "claude"}}


def view(name, **f):
    base = {"next": "SUBMIT", "valid": "PASS", "validation": [], "equiv_commits": ["abc12345ff"],
            "gates": {r: {"check": {"state": "ok"}, "review": {"state": "ok"}} for r in ("author", "independent")},
            "links": {"codimango": "https://x/1"}}
    base.update(f)
    return SimpleNamespace(entity_id=name, fields=base, findings=[])


class SlackTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        d = Path(td.name)
        (d / "slack.local.toml").write_text('channel_id = "C1"\nowner_slack_user_id = "UOWNER"\nhost = "h1"\n'
                                            'quiet_hours = "02:00-08:00"\n')
        for p in (mock.patch.dict(os.environ, {"WORKBOARD_CACHE": td.name, "WORKBOARD_STATE": td.name}),
                  mock.patch.object(slack, "CONFIG", d / "slack.local.toml"),
                  mock.patch("workboard.sync.host_id_for", return_value="h1"),
                  mock.patch("workboard.sync.sync"),
                  mock.patch("workboard.stats.week_numbers", return_value={"week": 44, "this_week": 9, "same_point_last_week": 12})):
            p.start()
            self.addCleanup(p.stop)
        self.cfg = SimpleNamespace(servers=[SimpleNamespace(id="h1")], user=SimpleNamespace(timezone="America/Los_Angeles"))
        self.noon = datetime(2026, 10, 30, 19, 0, tzinfo=timezone.utc)        # 12:00 PT

    def snap(self, views=(), evs=()):
        return SimpleNamespace(views=list(views), events=list(evs), observations=[], sessions=[], session_diagnostics=[])

    def tick(self, tr, snap, now=None):
        return slack.tick(self.cfg, transport=tr, snap=snap, now=now or self.noon)

    def test_brief_ready_and_decision_share_threads_and_dedupe(self):
        tr = FakeTransport()
        ask = ev("decision", "wiremock", {"id": "D-ab12", "action": "ask", "question": "S2 type rule?",
                                          "options": ["state it", "relax test"], "recommend": "1"})
        snap = self.snap([view("php-fixer"), view("wiremock", next="WAIT validation", valid="RUN")], [ask])
        self.tick(tr, snap)
        texts = [p["text"] for p in tr.posts]
        self.assertIn("Good morning", texts[0])                        # first post of the day is the brief
        self.assertTrue(any("D-ab12" in t and "1️⃣ state it" in t and "recommended" in t for t in texts))
        self.assertTrue(any("SUBMIT-READY" in t and "php-fixer" in t for t in texts))
        n = len(tr.posts)
        self.tick(tr, snap)                                             # nothing changed: nothing new
        self.assertEqual(len(tr.posts), n)
        st = slack.load_state()
        self.assertIn("task:wiremock", st["threads"])
        self.assertIn("task:php-fixer", st["threads"])

    def test_owner_reply_answers_decision_and_others_do_not(self):
        tr = FakeTransport()
        ask = ev("decision", "wiremock", {"id": "D-ab12", "action": "ask", "question": "S2?", "options": ["a", "b"]})
        snap = self.snap([], [ask])
        self.tick(tr, snap)
        root = slack.load_state()["threads"]["task:wiremock"]
        tr.reply_rows[root] = [
            {"message_ts": "200.1", "author_user_id": "USOMEONE", "content": "D-ab12 1"},              # not the owner
            {"message_ts": "200.2", "author_user_id": "UOWNER", "content": "D-ab12 2\n_Sent via Claude_"},  # agent post
            {"message_ts": "200.3", "author_user_id": "UOWNER", "content": "2 the test is wrong"}]       # the real one
        with mock.patch("workboard.coord.record") as rec, mock.patch("workboard.events.spool_append") as spool:
            res = self.tick(tr, snap)
        self.assertEqual(res["applied"], ["D-ab12:2"])
        self.assertEqual(rec.call_args[0][4]["label"], "b")
        self.assertEqual(rec.call_args[0][4]["reason"], "the test is wrong")
        self.assertTrue(spool.called)                                   # the asker hears it via the courier
        self.assertTrue(any("Ignored" in p["text"] for p in tr.posts))
        self.assertTrue(any("D-ab12 → b" in p["text"] for p in tr.posts))

    def test_tripwire_refuses_answers_near_an_agent_slack_write(self):
        tr = FakeTransport()
        ask = ev("decision", "t", {"id": "D-0001", "action": "ask", "question": "go?"})
        self.tick(tr, self.snap([], [ask]))
        root = slack.load_state()["threads"]["task:t"]
        at = 1793300000.0
        tr.reply_rows[root] = [{"message_ts": f"{at:.6f}", "author_user_id": "UOWNER", "content": "yes"}]
        wire = ev("slack_write", None, {"command": "meta slack.reaction add ..."},
                  at=datetime.fromtimestamp(at + 60, timezone.utc).isoformat(), eid="e2")
        with mock.patch("workboard.coord.record") as rec:
            res = self.tick(tr, self.snap([], [ask, wire]))
        self.assertEqual(res["applied"], [])
        self.assertFalse(rec.called)
        self.assertTrue(any("Not applied" in p["text"] for p in tr.posts))

    def test_quiet_hours_post_nothing(self):
        tr = FakeTransport()
        quiet = datetime(2026, 10, 30, 10, 0, tzinfo=timezone.utc)      # 03:00 PT
        res = self.tick(tr, self.snap([view("php-fixer")]), now=quiet)
        self.assertTrue(res.get("quiet"))
        self.assertEqual(tr.posts, [])

    def test_strict_ready_needs_every_gate(self):
        self.assertTrue(slack.strict_ready(view("t")))
        g = {"author": {"check": {"state": "ok"}, "review": {"state": "ok"}},
             "independent": {"check": {"state": "ok"}, "review": {"state": "none"}}}
        self.assertIsNone(slack.strict_ready(view("t", gates=g)))      # the board's relaxed READY is not enough
        self.assertIsNone(slack.strict_ready(view("t", valid="RUN")))

    def test_parse_answer(self):
        one = [{"id": "D-ab12"}]
        self.assertEqual(slack.parse_answer("D-AB12 2 because", []), ("D-ab12", "2", "because"))
        self.assertEqual(slack.parse_answer("undo D-ab12", []), ("D-ab12", "undo", ""))
        self.assertEqual(slack.parse_answer("yes", one), ("D-ab12", "yes", ""))
        self.assertIsNone(slack.parse_answer("yes", one + [{"id": "D-cd34"}]))   # two open here: must name one
        self.assertIsNone(slack.parse_answer("please also check the README", one))

    def test_wrong_host_or_missing_config_does_nothing(self):
        tr = FakeTransport()
        with mock.patch("workboard.sync.host_id_for", return_value="h2"):
            self.assertIn("skipped", self.tick(tr, self.snap()))
        self.assertEqual(tr.posts, [])

    def test_transport_never_targets_another_channel_or_posts_as_owner(self):
        calls = []
        runner = lambda argv, **kw: (calls.append(argv), SimpleNamespace(returncode=0, stdout='{"message_ts":"1.2"}'))[1]
        t = slack.Transport("C1", runner=runner)
        t.post("hi", thread_ts="1.0")
        self.assertEqual(calls[0][1:3], ["agents.notification", "send-slack"])     # the Metamate app, never slack.message send
        self.assertIn("--channel-id=C1", calls[0])


if __name__ == "__main__":
    unittest.main()

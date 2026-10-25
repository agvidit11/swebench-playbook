import json
import tempfile
import unittest
from pathlib import Path

from workboard import comms, events, hooks
from workboard.config import load_config


def stamp(ev, host="h1", seq=1):
    return events.stamp(ev, host, seq)


A = {"session_id": "s1", "alias": "h1·lane loop", "kind": "claude"}
B = {"session_id": "s2", "alias": "h2·harness", "kind": "claude"}


class CommsTest(unittest.TestCase):
    def test_targets(self):
        aliases = {"s1": "h1·lane loop", "s2": "h2·harness loop"}
        self.assertEqual(comms.target_for("all", aliases, ["h1", "h2"])["to"], "all")
        self.assertEqual(comms.target_for("h2", aliases, ["h1", "h2"])["to"], "host:h2")
        self.assertEqual(comms.target_for("harness", aliases, ["h1", "h2"])["to"], "session:s2")
        with self.assertRaises(ValueError):
            comms.target_for("loop", aliases, ["h1", "h2"])
        with self.assertRaises(ValueError):
            comms.target_for("nobody", aliases, ["h1"])

    def test_inbox_and_ack(self):
        m = stamp(comms.new_message("pick up pgmem", {"to": "session:s2", "to_label": "h2·harness"}, A, task="pgmem"))
        allm = stamp(comms.new_message("standup", {"to": "all", "to_label": "everyone"}, A), seq=2)
        evs = [m, allm]
        self.assertEqual([x["text"] for x in comms.inbox(evs, "s2", "h2")], ["pick up pgmem", "standup"])
        self.assertEqual(comms.inbox(evs, "s1", "h1"), [])                      # sender does not get own messages
        evs.append(stamp(comms.ack_event(m["event_id"], B), "h2", 1))
        self.assertEqual([x["text"] for x in comms.inbox(evs, "s2", "h2")], ["standup"])

    def test_hook_delivers_once_into_session(self):
        with tempfile.TemporaryDirectory() as d:
            st = Path(d)
            evs = [stamp(comms.new_message("hello from server 1", {"to": "host:h2", "to_label": "server h2"}, A))]
            comms.write_inbox_cache(st, evs)
            cfg = load_config(Path("/nonexistent"))
            payload = {"session_id": "s2", "transcript_path": "/nope", "tool_name": "Bash", "tool_input": {"command": "ls"}}
            r = hooks.handle("post-tool", payload, cfg=cfg, state_dir=st, host_id="h2")
            out = json.loads(r.stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "PostToolUse")
            self.assertIn("hello from server 1", out["additionalContext"])
            again = hooks.handle("post-tool", payload, cfg=cfg, state_dir=st, host_id="h2")
            self.assertEqual(again.stdout, "")                                  # delivered once
            other = hooks.handle("post-tool", dict(payload, session_id="s9"), cfg=cfg, state_dir=st, host_id="h1")
            self.assertEqual(other.stdout, "")                                  # wrong host

    def test_feed_and_servers(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        evs = []
        for i, (t, p) in enumerate((("claim", {}), ("check", {"pass": 3, "warn": 1, "fail": 0}), ("presence", {"last_seen": 1}),
                                    ("presence", {"last_seen": 2}))):
            e = stamp(events.new_event(t, "task-x", p, actor=A, commit=None, source="t"), seq=i + 1)
            e["occurred_at"] = now.isoformat()
            evs.append(e)
        f = comms.feed(evs, now=now.timestamp())
        self.assertEqual([x["type"] for x in f].count("presence"), 1)
        self.assertTrue(any("P3 W1 F0" in x["what"] for x in f))
        cfg = load_config(Path("/nonexistent"))
        s = comms.servers(evs, [], cfg, now=now.timestamp())
        self.assertEqual(s[0]["id"], "h1")
        self.assertEqual(len(s[0]["sessions"]), 1)


class CheckinTest(unittest.TestCase):
    def test_checkin_view_and_feed(self):
        from workboard import comms
        now = 1_800_000_000.0
        from datetime import datetime, timezone
        at = datetime.fromtimestamp(now - 120, timezone.utc).isoformat()
        e = {"type": "checkin", "occurred_at": at, "payload": {"status": "working", "tasks": ["t1"]},
             "actor": {"session_id": "s", "alias": "h·x", "kind": "claude"}, "host_id": "h", "entity": None}
        v = comms._checkin_view(e, now)
        self.assertEqual((v["status"], v["tasks"], v["checkin_ago_s"]), ("working", ["t1"], 120))
        f = comms.feed([e], now=now)
        self.assertIn("checked in: t1", f[0]["what"])

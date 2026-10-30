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

    def test_session_id_with_old_ledger_alias_is_one_session(self):
        sid = "ed539f4f-a5cc-4cf5-bb29-f7eff0820de3"
        key = f"claude:6971:20504:linux:abc:pid:[1]:{sid}"
        aliases = {sid: "6971·Multi-turn harness loop"}
        sessions = [{"session_key": key, "native_id": sid, "name": "agvidit-d9", "host": "6971"}]
        t = comms.target_for(f"session:{sid}", aliases, ["6971"], sessions=sessions)
        self.assertEqual((t["to"], t["to_label"]), (f"session:{key}", "agvidit-d9"))

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

    def test_local_server_card_carries_sync_reason_queue_and_counts(self):
        from datetime import datetime, timezone
        from workboard.sync import SyncState
        now = datetime.now(timezone.utc)
        cfg = load_config(Path("/nonexistent"))
        native = [{"session_key": "claude:h1:1:d:s", "native_id": "s", "host": "h1", "name": "lane",
                   "kind": "claude", "kind_icon": "🟣", "status": "waiting", "status_since": now.isoformat(),
                   "live": True, "classification": "local-live", "tasks": [], "child_runs": []}]
        state = SyncState(last_pull_ok=False, last_push_ok=False, pending=4, error="pull failed: synthetic",
                          at=now.isoformat())
        server = next(x for x in comms.servers([], [], cfg, native, [], now=now.timestamp(),
                                               sync_state=state, local_host="h1") if x["id"] == "h1")
        self.assertEqual(server["status_counts"]["waiting"], 1)
        self.assertEqual((server["queue"], server["sync_error"]), (4, "pull failed: synthetic"))


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

    def test_shell_checkin_is_a_human_actor_without_resume(self):
        from datetime import datetime, timezone
        from workboard.config import load_config
        now = 1_800_000_000.0
        e = {"type": "checkin", "occurred_at": datetime.fromtimestamp(now - 60, timezone.utc).isoformat(),
             "recorded_at": datetime.fromtimestamp(now - 60, timezone.utc).isoformat(),
             "payload": {"status": "working", "tasks": ["alpha"]},
             "actor": {"session_id": "human:agvidit@h1", "alias": "h1·agvidit (shell)", "kind": "human"},
             "host_id": "h1", "entity": None}
        server = next(x for x in comms.servers([e], [], load_config(Path("/nonexistent")), now=now)
                      if x["id"] == "h1")
        actor = next(x for x in server["sessions"] if x.get("is_actor"))
        self.assertEqual((actor["kind_icon"], actor["classification"], actor["tasks"]),
                         ("👤", "human-shell", ["alpha"]))
        self.assertEqual(actor["restart"]["state"], "not-applicable")
        self.assertIsNone(actor["restart"]["command"])


class SessionIdAddressTest(unittest.TestCase):
    def test_history_id_resolves(self):
        from workboard import comms
        t = comms.target_for("session:3b403eb5-5715-42e6-8a68-bed6f2d1ea56", {"3b403eb5-5715-42e6-8a68-bed6f2d1ea56": "h·x"}, ["h"])
        self.assertEqual(t["to"], "session:3b403eb5-5715-42e6-8a68-bed6f2d1ea56")
        t = comms.target_for("3b403eb5", {"3b403eb5-5715-42e6-8a68-bed6f2d1ea56": "h·x"}, ["h"])
        self.assertEqual(t["to_label"], "h·x")


class SupervisorTest(unittest.TestCase):
    def ev(self, action, sid, at, host="h1", **pl):
        return {"type": "supervisor", "host_id": host, "seq": 1, "occurred_at": at,
                "actor": {"session_id": sid, "alias": f"{host}·{sid}", "kind": "claude"}, "payload": {"action": action, **pl}}

    def test_latest_claim_wins_and_release_clears(self):
        from workboard import comms
        evs = [self.ev("claim", "a", "2026-10-29T01:00:00+00:00"),
               self.ev("status", "a", "2026-10-29T02:00:00+00:00", text="all good", disk={"used_pct": 70}),
               self.ev("claim", "b", "2026-10-29T03:00:00+00:00"),
               self.ev("status", "a", "2026-10-29T04:00:00+00:00", text="stale supervisor")]
        sup = comms.supervisor(evs, "h1")
        self.assertEqual((sup["session_id"], sup["status"]), ("b", None))     # a's later status is ignored
        self.assertIsNone(comms.supervisor(evs + [self.ev("release", "b", "2026-10-29T05:00:00+00:00")], "h1"))
        self.assertIsNone(comms.supervisor(evs, "h2"))

    def test_supervisor_message_target(self):
        from workboard import comms
        evs = [self.ev("claim", "a", "2026-10-29T01:00:00+00:00")]
        t = comms.supervisor_target(evs, "supervisor", ["h1", "h2"], "h1")
        self.assertEqual(t["to"], "session:a")
        self.assertIsNone(comms.supervisor_target(evs, "board-4e", ["h1"], "h1"))
        with self.assertRaises(ValueError):
            comms.supervisor_target(evs, "supervisor:h2", ["h1", "h2"], "h1")


class AttentionTest(unittest.TestCase):
    def test_flags_blocked_sessions(self):
        from workboard import comms
        rows = [{"name": "a", "status": "waiting for permission", "status_ago_s": 1200},
                {"name": "b", "status": "busy", "status_ago_s": 60},
                {"name": "c", "kind": "codex", "status": "quiet", "status_ago_s": 4000, "tasks": ["t1"]},
                {"name": "d", "status": "idle", "status_ago_s": 4 * 3600, "tasks": ["t2"]},
                {"name": "e", "status": "idle", "status_ago_s": 4 * 3600, "tasks": []}]
        self.assertEqual([f["name"] for f in comms.attention(rows)], ["a", "c", "d"])


class AgentRowsTest(unittest.TestCase):
    def test_codex_actor_listed_beside_registry_sessions(self):
        import time
        from datetime import datetime, timezone
        from types import SimpleNamespace
        from workboard import comms
        at = datetime.fromtimestamp(time.time() - 600, timezone.utc).isoformat()
        ev = {"type": "presence", "host_id": "h1", "seq": 1, "occurred_at": at, "recorded_at": at,
              "entity": {"kind": "task", "id": "t1"}, "payload": {},
              "actor": {"session_id": "codex:h1:1:2", "alias": "h1·Codex rev", "kind": "codex", "parent_session": "p1"}}
        native = [{"host": "h1", "native_id": "p1", "session_key": "k1", "name": "agvidit-90", "title": "Lane", "kind": "claude",
                   "live": True, "status": "busy"}]
        cfg = SimpleNamespace(servers=[SimpleNamespace(id="h1")])
        rows = comms.servers([ev], [], cfg, native, [])[0]["sessions"]
        cx = [r for r in rows if r.get("kind") == "codex"]
        self.assertEqual((len(cx), cx[0]["tasks"], cx[0]["parent_name"], cx[0]["status"]), (1, ["t1"], "Lane", "active"))

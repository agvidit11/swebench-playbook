import json, tempfile, threading, unittest
from pathlib import Path
from unittest import mock
from workboard import claims, coord, events, sync
from tests.helpers import bare_remote, cfg_for

A1 = {"session_id": "s1", "alias": "h1·lane loop", "kind": "claude", "host": "h1"}
A2 = {"session_id": "s2", "alias": "h2·harness", "kind": "claude", "host": "h2"}


class ClaimCliTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.remote = bare_remote(self.tmp)
        self.c1, self.c2 = cfg_for(self.tmp, "h1", self.remote), cfg_for(self.tmp, "h2", self.remote)
        self.s1, self.s2 = self.tmp / "st1", self.tmp / "st2"
        self.s1.mkdir(); self.s2.mkdir()
        for cfg, st in ((self.c1, self.s1), (self.c2, self.s2)):
            claims.probe(cfg, state_dir=st)

    def test_claim_records_event_and_local_state(self):
        res = coord.claim(self.c1, "task-a", state_dir=self.s1, actor=A1)
        self.assertEqual(res.status, "ACQUIRED")
        spool = [json.loads(l) for l in (self.s1 / events.SPOOL_NAME).read_text().splitlines()]
        self.assertEqual(spool[-1]["type"], "claim")
        self.assertIn("task-a", json.loads((self.s1 / coord.LOCAL_CLAIMS).read_text()))

    def test_claim_to_other_session(self):
        res = coord.claim(self.c1, "task-b", state_dir=self.s1, actor=A1, to_actor=A2)
        self.assertEqual(res.status, "ACQUIRED")
        self.assertEqual(claims.read(self.c1, "task-b", state_dir=self.s1).owner["session_id"], "s2")
        types = [json.loads(l)["type"] for l in (self.s1 / events.SPOOL_NAME).read_text().splitlines()]
        self.assertEqual(types[-2:], ["claim", "assign"])

    def test_two_servers_same_second_one_owner(self):
        out = {}
        bar = threading.Barrier(2)
        def go(cfg, st, actor, key):
            bar.wait()
            out[key] = coord.claim(cfg, "task-r", state_dir=st, actor=actor).status
        ts = [threading.Thread(target=go, args=(self.c1, self.s1, A1, 1)),
              threading.Thread(target=go, args=(self.c2, self.s2, A2, 2))]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(sorted(out.values()), ["ACQUIRED", "LOST"])

    def test_release_by_non_owner_refused_owner_ok(self):
        coord.claim(self.c1, "task-c", state_dir=self.s1, actor=A1)
        self.assertEqual(coord.release(self.c2, "task-c", "x", state_dir=self.s2, actor=A2).status, "REFUSED")
        self.assertEqual(coord.release(self.c1, "task-c", "done", state_dir=self.s1, actor=A1).status, "RELEASED")
        self.assertEqual(claims.read(self.c1, "task-c", state_dir=self.s1).status, "FREE")

    def test_auto_claim_from_touch_event(self):
        events.spool_append(self.s1, events.new_event("touch", "task-d", {}, actor=A1, commit=None, source="hook"))
        st = sync.sync(self.c1, host_id="h1", state_dir=self.s1)
        self.assertTrue(st.last_push_ok, st.error)
        self.assertEqual(claims.read(self.c1, "task-d", state_dir=self.s1).owner["session_id"], "s1")

    def test_auto_claim_skips_task_owned_elsewhere(self):
        coord.claim(self.c2, "task-e", state_dir=self.s2, actor=A2)
        events.spool_append(self.s1, events.new_event("touch", "task-e", {}, actor=A1, commit=None, source="hook"))
        sync.sync(self.c1, host_id="h1", state_dir=self.s1)
        self.assertEqual(claims.read(self.c1, "task-e", state_dir=self.s1).owner["session_id"], "s2")

    def test_mutation_fails_closed_when_ledger_stale(self):
        self.c1.ledger.remote = str(self.tmp / "missing.git")
        ok, err = coord.ledger_fresh(self.c1, self.s1)
        self.assertFalse(ok)
        self.assertTrue(err)

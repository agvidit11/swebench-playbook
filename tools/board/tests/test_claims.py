import tempfile, threading, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from workboard import claims
from tests.helpers import bare_remote, cfg_for, git

ACTOR1 = {"session_id": "s1", "alias": "h1·lane", "kind": "claude", "host": "h1"}
ACTOR2 = {"session_id": "s2", "alias": "h2·loop", "kind": "claude", "host": "h2"}


class ClaimsTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.remote = bare_remote(self.tmp)
        self.c1 = cfg_for(self.tmp, "h1", self.remote)
        self.c2 = cfg_for(self.tmp, "h2", self.remote)
        self.s1, self.s2 = self.tmp / "st1", self.tmp / "st2"

    def test_ref_name_hashed(self):
        ref = claims.ref_for("weird task/with spaces")
        self.assertRegex(ref, r"^refs/claims/[0-9a-f]{16}$")
        self.assertNotEqual(claims.ref_for("a"), claims.ref_for("a/b"))

    def test_probe_passes_on_plain_git(self):
        res = claims.probe(self.c1, state_dir=self.s1)
        self.assertTrue(res.ok, res.detail)
        self.assertEqual(res.prefix, "refs/claims")

    def test_acquire_then_second_loses(self):
        a = claims.acquire(self.c1, "task-x", ACTOR1, state_dir=self.s1)
        self.assertEqual(a.status, "ACQUIRED", a.detail)
        b = claims.acquire(self.c2, "task-x", ACTOR2, state_dir=self.s2)
        self.assertEqual(b.status, "LOST")
        self.assertEqual(b.owner["session_id"], "s1")

    def test_concurrent_acquire_one_wins(self):
        results = {}
        barrier = threading.Barrier(2)

        def go(cfg, actor, st, key):
            barrier.wait()
            results[key] = claims.acquire(cfg, "task-race", actor, state_dir=st)

        ts = [threading.Thread(target=go, args=(self.c1, ACTOR1, self.s1, 1)),
              threading.Thread(target=go, args=(self.c2, ACTOR2, self.s2, 2))]
        [t.start() for t in ts]; [t.join() for t in ts]
        statuses = sorted(r.status for r in results.values())
        self.assertEqual(statuses, ["ACQUIRED", "LOST"], [r.detail for r in results.values()])
        owner = claims.read(self.c1, "task-race", state_dir=self.s1)
        winner = [k for k, r in results.items() if r.status == "ACQUIRED"][0]
        self.assertEqual(owner.owner["session_id"], {1: "s1", 2: "s2"}[winner])

    def test_uncertain_push_resolved_by_ref_read(self):
        orig = claims._push
        def lying(cfg, led, args, timeout):
            res = orig(cfg, led, args, timeout)
            res.returncode, res.stderr = 128, "Connection reset by peer"
            return res
        with mock.patch.object(claims, "_push", lying):
            a = claims.acquire(self.c1, "task-u", ACTOR1, state_dir=self.s1)
        self.assertEqual(a.status, "ACQUIRED", a.detail)

    def test_heartbeat_moves_tip_and_keeps_owner(self):
        a = claims.acquire(self.c1, "task-h", ACTOR1, state_dir=self.s1)
        h = claims.heartbeat(self.c1, "task-h", ACTOR1, a.oid, state_dir=self.s1)
        self.assertEqual(h.status, "ACQUIRED", h.detail)
        self.assertNotEqual(h.oid, a.oid)
        stale = claims.heartbeat(self.c1, "task-h", ACTOR1, a.oid, state_dir=self.s1)   # old tip
        self.assertEqual(stale.status, "LOST")

    def test_release_wrong_oid_refused(self):
        a = claims.acquire(self.c1, "task-r", ACTOR1, state_dir=self.s1)
        bad = claims.release(self.c1, "task-r", ACTOR1, "0" * 40, state_dir=self.s1)
        self.assertEqual(bad.status, "REFUSED")
        ok = claims.release(self.c1, "task-r", ACTOR1, a.oid, state_dir=self.s1)
        self.assertEqual(ok.status, "RELEASED", ok.detail)
        self.assertIsNone(claims.read(self.c1, "task-r", state_dir=self.s1).oid)

    def test_steal_requires_expiry_and_grace(self):
        a = claims.acquire(self.c1, "task-s", ACTOR1, state_dir=self.s1)
        not_expired = claims.steal(self.c2, "task-s", ACTOR2, state_dir=self.s2)
        self.assertEqual(not_expired.status, "REFUSED")
        later = datetime.now(timezone.utc) + timedelta(hours=30)
        first = claims.steal(self.c2, "task-s", ACTOR2, state_dir=self.s2, now=later, monotonic=1000.0)
        self.assertEqual(first.status, "REFUSED")            # starts the grace timer
        self.assertIn("grace", first.detail)
        early = claims.steal(self.c2, "task-s", ACTOR2, state_dir=self.s2, now=later, monotonic=1000.0 + 60)
        self.assertEqual(early.status, "REFUSED")
        grace = 2 * self.c2.claims.heartbeat_interval_minutes * 60
        done = claims.steal(self.c2, "task-s", ACTOR2, state_dir=self.s2, now=later, monotonic=1000.0 + grace + 1)
        self.assertEqual(done.status, "ACQUIRED", done.detail)
        self.assertEqual(claims.read(self.c1, "task-s", state_dir=self.s1).owner["session_id"], "s2")

    def test_steal_loses_if_owner_renews_during_grace(self):
        a = claims.acquire(self.c1, "task-g", ACTOR1, state_dir=self.s1)
        later = datetime.now(timezone.utc) + timedelta(hours=30)
        claims.steal(self.c2, "task-g", ACTOR2, state_dir=self.s2, now=later, monotonic=0.0)
        claims.heartbeat(self.c1, "task-g", ACTOR1, a.oid, state_dir=self.s1)          # owner comes back
        res = claims.steal(self.c2, "task-g", ACTOR2, state_dir=self.s2, now=later, monotonic=10_000.0)
        self.assertEqual(res.status, "REFUSED")              # tip changed: grace restarts
        self.assertEqual(claims.read(self.c1, "task-g", state_dir=self.s1).owner["session_id"], "s1")

    def test_offline_acquire_pending(self):
        self.c1.ledger.remote = str(self.tmp / "missing.git")
        res = claims.acquire(self.c1, "task-o", ACTOR1, state_dir=self.s1)
        self.assertEqual(res.status, "PENDING")

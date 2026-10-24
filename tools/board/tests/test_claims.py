import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from workboard import claims
from tests.helpers import bare_remote, cfg_for, git

ACTOR1 = {"session_id": "s1", "alias": "h1·lane", "kind": "claude", "host": "h1"}
ACTOR2 = {"session_id": "s2", "alias": "h2·loop", "kind": "claude", "host": "h2"}
LATER = datetime.now(timezone.utc) + timedelta(hours=30)


class ClaimsTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.remote = bare_remote(self.tmp)
        self.c1 = cfg_for(self.tmp, "h1", self.remote)
        self.c2 = cfg_for(self.tmp, "h2", self.remote)
        self.s1, self.s2 = self.tmp / "st1", self.tmp / "st2"
        for cfg, st in ((self.c1, self.s1), (self.c2, self.s2)):
            self.assertTrue(claims.probe(cfg, state_dir=st).ok)

    def steal(self, **kw):
        kw.setdefault("source_healthy", True)
        kw.setdefault("clock_healthy", True)
        kw.setdefault("boot", "boot-1")
        return claims.steal(self.c2, kw.pop("task"), ACTOR2, state_dir=self.s2, **kw)

    # -- probe gating --------------------------------------------------------------------------
    def test_ref_name_hashed(self):
        self.assertRegex(claims.ref_for("weird task/with spaces"), r"^refs/claims/[0-9a-f]{16}$")
        self.assertNotEqual(claims.ref_for("a"), claims.ref_for("a/b"))

    def test_acquire_before_probe_refused(self):
        fresh = self.tmp / "st-fresh"
        self.assertEqual(claims.acquire(self.c1, "t", ACTOR1, state_dir=fresh).status, "REFUSED")

    def test_remote_change_requires_new_probe(self):
        other = bare_remote(self.tmp, "other.git")
        self.c1.ledger.remote = str(other)
        res = claims.acquire(self.c1, "t", ACTOR1, state_dir=self.s1)
        self.assertEqual(res.status, "REFUSED")
        self.assertIn("probe", res.detail)

    def test_failed_probe_disables(self):
        fresh = self.tmp / "st-x"
        self.c1.ledger.remote = str(self.tmp / "missing.git")
        self.assertFalse(claims.probe(self.c1, state_dir=fresh).ok)
        self.assertIsNone(claims.probed_prefix(self.c1, fresh))

    def test_fallback_prefix_when_claims_namespace_rejected(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text('#!/bin/sh\nwhile read old new ref; do case "$ref" in refs/claims/*) exit 1;; esac; done\nexit 0\n')
        hook.chmod(0o755)
        fresh = self.tmp / "st-fb"
        res = claims.probe(self.c1, state_dir=fresh)
        self.assertTrue(res.ok, res.detail)
        self.assertEqual(res.prefix, claims.FALLBACK_PREFIX)
        leftovers = git(self.remote, "for-each-ref", "--format=%(refname)").stdout
        self.assertNotIn("probe-", leftovers)

    # -- acquire -------------------------------------------------------------------------------
    def test_acquire_then_second_loses(self):
        self.assertEqual(claims.acquire(self.c1, "task-x", ACTOR1, state_dir=self.s1).status, "ACQUIRED")
        b = claims.acquire(self.c2, "task-x", ACTOR2, state_dir=self.s2)
        self.assertEqual(b.status, "LOST")
        self.assertEqual(b.owner["session_id"], "s1")

    def test_concurrent_acquire_one_wins(self):
        results, barrier = {}, threading.Barrier(2)

        def go(cfg, actor, st, key):
            barrier.wait()
            results[key] = claims.acquire(cfg, "task-race", actor, state_dir=st)

        ts = [threading.Thread(target=go, args=(self.c1, ACTOR1, self.s1, 1)),
              threading.Thread(target=go, args=(self.c2, ACTOR2, self.s2, 2))]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(sorted(r.status for r in results.values()), ["ACQUIRED", "LOST"])

    def test_uncertain_push_resolved_by_ref_read(self):
        orig = claims._push

        def lying(cfg, repo, args, timeout):
            res = orig(cfg, repo, args, timeout)
            res.returncode, res.stderr = 128, "Connection reset by peer"
            return res

        with mock.patch.object(claims, "_push", lying):
            self.assertEqual(claims.acquire(self.c1, "task-u", ACTOR1, state_dir=self.s1).status, "ACQUIRED")

    def test_live_claim_limit(self):
        self.c1.claims.max_live_claims = 2
        self.assertEqual(claims.acquire(self.c1, "a", ACTOR1, state_dir=self.s1).status, "ACQUIRED")
        self.assertEqual(claims.acquire(self.c1, "b", ACTOR1, state_dir=self.s1).status, "ACQUIRED")
        over = claims.acquire(self.c1, "c", ACTOR1, state_dir=self.s1)
        self.assertEqual(over.status, "REFUSED")
        self.assertIn("limit", over.detail)

    # -- renew / release -----------------------------------------------------------------------
    def test_heartbeat_moves_tip_and_keeps_owner(self):
        a = claims.acquire(self.c1, "task-h", ACTOR1, state_dir=self.s1)
        h = claims.heartbeat(self.c1, "task-h", ACTOR1, expected_oid=a.oid, state_dir=self.s1)
        self.assertEqual(h.status, "ACQUIRED", h.detail)
        self.assertNotEqual(h.oid, a.oid)
        self.assertEqual(claims.heartbeat(self.c1, "task-h", ACTOR1, expected_oid=a.oid, state_dir=self.s1).status, "LOST")

    def test_foreign_heartbeat_and_release_refused(self):
        a = claims.acquire(self.c1, "task-f", ACTOR1, state_dir=self.s1)
        self.assertEqual(claims.heartbeat(self.c2, "task-f", ACTOR2, expected_oid=a.oid, state_dir=self.s2).status, "REFUSED")
        self.assertEqual(claims.release(self.c2, "task-f", ACTOR2, expected_oid=a.oid, state_dir=self.s2).status, "REFUSED")
        self.assertEqual(claims.read(self.c1, "task-f", state_dir=self.s1).owner["session_id"], "s1")

    def test_wrong_entity_payload_refused(self):
        a = claims.acquire(self.c1, "task-one", ACTOR1, state_dir=self.s1)
        # point task-two's ref at task-one's claim commit
        git(self.remote, "update-ref", claims.ref_for("task-two"), a.oid)
        res = claims.release(self.c1, "task-two", ACTOR1, expected_oid=a.oid, state_dir=self.s1)
        self.assertEqual(res.status, "REFUSED")

    def test_release_wrong_oid_refused(self):
        a = claims.acquire(self.c1, "task-r", ACTOR1, state_dir=self.s1)
        self.assertEqual(claims.release(self.c1, "task-r", ACTOR1, expected_oid="0" * 40, state_dir=self.s1).status, "REFUSED")
        self.assertEqual(claims.release(self.c1, "task-r", ACTOR1, expected_oid=a.oid, state_dir=self.s1).status, "RELEASED")
        self.assertEqual(claims.read(self.c1, "task-r", state_dir=self.s1).status, "FREE")

    # -- steal ---------------------------------------------------------------------------------
    def test_steal_requires_health(self):
        claims.acquire(self.c1, "task-s", ACTOR1, state_dir=self.s1)
        self.assertEqual(self.steal(task="task-s", now=LATER, source_healthy=False).status, "REFUSED")
        self.assertEqual(self.steal(task="task-s", now=LATER, clock_healthy=False).status, "REFUSED")

    def test_steal_requires_expiry_and_grace(self):
        claims.acquire(self.c1, "task-s", ACTOR1, state_dir=self.s1)
        self.assertEqual(self.steal(task="task-s").status, "REFUSED")
        first = self.steal(task="task-s", now=LATER, monotonic=1000.0)
        self.assertIn("grace", first.detail)
        self.assertEqual(self.steal(task="task-s", now=LATER, monotonic=1060.0).status, "REFUSED")
        need = 2 * self.c2.claims.heartbeat_interval_minutes * 60
        done = self.steal(task="task-s", now=LATER, monotonic=1000.0 + need + 1)
        self.assertEqual(done.status, "ACQUIRED", done.detail)
        self.assertEqual(claims.read(self.c1, "task-s", state_dir=self.s1).owner["session_id"], "s2")

    def test_steal_grace_restarts_after_reboot(self):
        claims.acquire(self.c1, "task-b", ACTOR1, state_dir=self.s1)
        self.steal(task="task-b", now=LATER, monotonic=10.0, boot="boot-1")
        res = self.steal(task="task-b", now=LATER, monotonic=99_999.0, boot="boot-2")
        self.assertEqual(res.status, "REFUSED")
        self.assertIn("grace period started", res.detail)

    def test_steal_loses_if_owner_renews_during_grace(self):
        a = claims.acquire(self.c1, "task-g", ACTOR1, state_dir=self.s1)
        self.steal(task="task-g", now=LATER, monotonic=0.0)
        claims.heartbeat(self.c1, "task-g", ACTOR1, expected_oid=a.oid, state_dir=self.s1)
        self.assertEqual(self.steal(task="task-g", now=LATER, monotonic=10_000.0).status, "REFUSED")
        self.assertEqual(claims.read(self.c1, "task-g", state_dir=self.s1).owner["session_id"], "s1")

    def test_steal_refuses_future_dated_claim(self):
        future = datetime.now(timezone.utc) + timedelta(days=3)
        claims.acquire(self.c1, "task-fut", ACTOR1, state_dir=self.s1, now=future)
        res = self.steal(task="task-fut", now=LATER - timedelta(hours=29))
        self.assertEqual(res.status, "REFUSED")
        self.assertIn("future", res.detail)

    def test_offline_acquire_pending(self):
        with mock.patch.object(claims, "_live_count", side_effect=claims.Offline("down")):
            self.assertEqual(claims.acquire(self.c1, "task-o", ACTOR1, state_dir=self.s1).status, "PENDING")

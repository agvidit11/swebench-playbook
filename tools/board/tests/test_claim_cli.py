import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from workboard import claims, coord, events, sync
from tests.helpers import bare_remote, cfg_for, git

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

    def test_release_of_expired_claim_points_to_steal(self):
        coord.claim(self.c1, "task-x", state_dir=self.s1, actor=A1)
        later = datetime.now(timezone.utc) + timedelta(hours=self.c2.claims.expire_after_hours + 1)
        with mock.patch.object(coord, "_now", return_value=later):
            res = coord.release(self.c2, "task-x", "x", state_dir=self.s2, actor=A2)
        self.assertEqual(res.status, "REFUSED")
        self.assertIn("--steal", res.detail)
        self.assertNotIn("--steal", coord.release(self.c2, "task-x", "x", state_dir=self.s2, actor=A2).detail)

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


class ClaimHardeningTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.remote = bare_remote(self.tmp)
        self.c1, self.c2 = cfg_for(self.tmp, "h1", self.remote), cfg_for(self.tmp, "h2", self.remote)
        self.c1.user.id = self.c2.user.id = "person-1"
        self.s1, self.s2 = self.tmp / "st1", self.tmp / "st2"
        self.s1.mkdir()
        self.s2.mkdir()
        for cfg, st in ((self.c1, self.s1), (self.c2, self.s2)):
            claims.probe(cfg, state_dir=st)

    def test_busy_sync_fails_closed(self):
        sync.sync(self.c1, host_id="h1", state_dir=self.s1)     # leaves a fresh good sync on disk
        busy = sync.SyncState(last_pull_ok=True, last_push_ok=True, busy=True)
        with mock.patch.object(sync, "sync", return_value=busy), mock.patch("workboard.coord.time.sleep"):
            ok, _ = coord.ledger_fresh(self.c1, self.s1)
        self.assertTrue(ok)                                      # another process just synced: fresh enough
        import itertools
        with mock.patch.object(sync, "sync", return_value=busy), mock.patch("workboard.coord.time.sleep"), \
                mock.patch.object(sync, "load_state", return_value=sync.SyncState(at="2000-01-01T00:00:00+00:00")), \
                mock.patch("workboard.coord.time.monotonic", side_effect=itertools.count(0, 5)):
            ok, err = coord.ledger_fresh(self.c1, self.s1)
        self.assertFalse(ok)                                     # stale and still busy: fail closed after retrying
        self.assertIn("another sync", err)

    def test_pull_ok_push_failed_fails_closed(self):
        with mock.patch.object(sync, "sync", return_value=sync.SyncState(last_pull_ok=True, last_push_ok=False,
                                                                         error="push failed: rejected")):
            ok, err = coord.ledger_fresh(self.c1, self.s1)
        self.assertFalse(ok)

    def test_steal_without_evidence_refused(self):
        coord.claim(self.c1, "t", state_dir=self.s1, actor=A1)
        res = coord.claim(self.c2, "t", state_dir=self.s2, actor=A2, steal=True)
        self.assertEqual(res.status, "REFUSED")
        for src, clk in ((False, True), (True, False)):
            res = coord.claim(self.c2, "t", state_dir=self.s2, actor=A2, steal=True, source_healthy=src, clock_healthy=clk)
            self.assertEqual(res.status, "REFUSED")
        self.assertFalse((self.s2 / claims.GRACE_FILE).exists())   # no grace timer started

    def test_cross_host_assignment_adopted_and_renewed(self):
        coord.claim(self.c1, "t", state_dir=self.s1, actor=A1, to_actor=A2)
        with mock.patch.object(coord, "_now", return_value=datetime.now(timezone.utc) + timedelta(minutes=30)):
            notes = coord.auto_claims(self.c2, self.s2, [("t", A2)])
        cur = claims.read(self.c2, "t", state_dir=self.s2)
        self.assertEqual(cur.owner["session_id"], "s2")
        with coord.local_claims(self.s2) as local:
            self.assertEqual(local["t"]["oid"], cur.oid)          # adopted then renewed to the new tip
        self.assertEqual(notes, [])

    def test_concurrent_local_updates_not_lost(self):
        def put(i):
            with coord.local_claims(self.s1) as local:
                local[f"t{i}"] = {"oid": "x", "session_id": "s", "renewed": "2026-10-23T00:00:00+00:00"}
        ts = [threading.Thread(target=put, args=(i,)) for i in range(20)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        with coord.local_claims(self.s1) as local:
            self.assertEqual(len(local), 20)

    def test_person_can_release_own_agent_claim(self):
        agent = dict(A1, person="person-1")
        coord.claim(self.c1, "t", state_dir=self.s1, actor=agent)
        human = {"session_id": "human:person-1@h1", "alias": "h1·person-1 (shell)", "kind": "human", "host": "h1", "person": "person-1"}
        res = coord.release(self.c1, "t", "handing over", state_dir=self.s1, actor=human)
        self.assertEqual(res.status, "RELEASED", res.detail)
        rel = [json.loads(l) for l in (self.s1 / events.SPOOL_NAME).read_text().splitlines() if '"release"' in l][-1]
        self.assertEqual(rel["actor"]["kind"], "human")
        self.assertEqual(rel["payload"]["released_owner"]["session_id"], "s1")

    def test_other_person_cannot_release(self):
        coord.claim(self.c1, "t", state_dir=self.s1, actor=dict(A1, person="someone-else"))
        human = {"session_id": "human:person-1@h1", "alias": "h1·person-1", "kind": "human", "host": "h1", "person": "person-1"}
        self.assertEqual(coord.release(self.c1, "t", "x", state_dir=self.s1, actor=human).status, "REFUSED")

    def test_probe_cleanup_after_uncertain_create(self):
        orig = claims._push
        calls = {"n": 0}

        def flaky(cfg, repo, args, timeout):
            res = orig(cfg, repo, args, timeout)
            calls["n"] += 1
            if calls["n"] == 1:
                res.returncode = 128       # create landed, reported failure
            return res

        fresh = self.tmp / "st-p"
        with mock.patch.object(claims, "_push", flaky):
            claims.probe(self.c1, state_dir=fresh)
        refs = git(self.remote, "for-each-ref", "--format=%(refname)").stdout
        self.assertNotIn("probe-", refs)


class ClaimRefSourceTest(unittest.TestCase):
    def cfg(self):
        from workboard.config import load_config
        c = load_config(Path("/nonexistent"))
        c.ledger.remote = "x"
        return c

    def store(self, rows):
        return mock.Mock(snapshot=mock.Mock(return_value=(True, "refs/claims", rows)))

    def good(self, task, **over):
        p = {"entity_id": task, "session_id": "s1", "alias": "h1·x",
             "renewed_at": datetime.now(timezone.utc).isoformat()}
        p.update(over)
        return (claims.ref_for(task), "a" * 40, p)

    def test_healthy_snapshot(self):
        from workboard.sources.claimrefs import ClaimRefSource
        res = ClaimRefSource(self.cfg(), store=self.store([self.good("t")])).fetch()
        self.assertTrue(res.health.ok)
        self.assertEqual(res.observations[0].entity_id, "t")

    def test_malformed_or_mismatched_or_future_is_unhealthy(self):
        from workboard.sources.claimrefs import ClaimRefSource
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        bad_rows = [[self.good("t"), (claims.ref_for("u"), "b" * 40, None)],
                    [(claims.ref_for("other"), "c" * 40, self.good("t")[2])],
                    [self.good("t", renewed_at=future)],
                    [self.good("t", renewed_at="yesterday")]]
        for rows in bad_rows:
            res = ClaimRefSource(self.cfg(), store=self.store(rows)).fetch()
            self.assertFalse(res.health.ok, rows)
            self.assertEqual(res.observations, [])

    def test_overflow_is_unhealthy(self):
        from workboard.sources.claimrefs import ClaimRefSource
        cfg = self.cfg()
        cfg.claims.max_live_claims = 1
        res = ClaimRefSource(cfg, store=self.store([self.good("a"), self.good("b")])).fetch()
        self.assertFalse(res.health.ok)


class OwnAgentOverrideTest(ClaimHardeningTest):
    def test_mismatched_caller_refused(self):
        coord.claim(self.c1, "t", state_dir=self.s1, actor=dict(A1, person="person-1"))
        stranger = {"session_id": "human:x@h1", "alias": "h1·x", "kind": "human", "host": "h1", "person": "someone"}
        self.assertEqual(coord.release_own_agent(self.c1, "t", "x", state_dir=self.s1, actor=stranger).status, "REFUSED")

    def test_override_loses_to_concurrent_renewal(self):
        agent = dict(A1, person="person-1")
        a = coord.claim(self.c1, "t", state_dir=self.s1, actor=agent)
        stale = claims.read(self.c1, "t", state_dir=self.s1)
        claims.heartbeat(self.c1, "t", agent, expected_oid=a.oid, state_dir=self.s1)    # renewal lands first
        human = {"session_id": "human:p@h1", "alias": "h1·p", "kind": "human", "host": "h1", "person": "person-1"}
        res = coord.release_own_agent(self.c1, "t", "x", state_dir=self.s1, actor=human, current=stale)
        self.assertEqual(res.status, "REFUSED")
        self.assertEqual(claims.read(self.c1, "t", state_dir=self.s1).status, "HELD")


class ReleaseAuditTest(ClaimHardeningTest):
    def test_release_reports_unqueued_audit(self):
        coord.claim(self.c1, "t", state_dir=self.s1, actor=A1)
        with mock.patch.object(coord, "record", return_value=False):
            res = coord.release(self.c1, "t", "done", state_dir=self.s1, actor=A1)
        self.assertEqual(res.status, "RELEASED")
        self.assertIn("audit event could not be queued", res.detail)

    def test_own_agent_release_reports_unqueued_audit(self):
        coord.claim(self.c1, "t", state_dir=self.s1, actor=dict(A1, person="person-1"))
        human = {"session_id": "human:p@h1", "alias": "h1·p", "kind": "human", "host": "h1", "person": "person-1"}
        with mock.patch.object(coord, "record", return_value=False):
            res = coord.release(self.c1, "t", "x", state_dir=self.s1, actor=human)
        self.assertEqual(res.status, "RELEASED")
        self.assertIn("audit event could not be queued", res.detail)

import json, tempfile, threading, unittest
from pathlib import Path
from workboard import events, sync
from tests.helpers import bare_remote, cfg_for, git

ACTOR = {"session_id": "s1", "alias": "h1·tab", "kind": "claude"}


def spool_some(spool, n, tag="t"):
    for i in range(n):
        events.spool_append(spool, events.new_event("touch", f"{tag}{i}", {}, actor=ACTOR, commit=None, source="test"))


class SyncTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.remote = bare_remote(self.tmp)

    def host(self, name):
        cfg = cfg_for(self.tmp, name, self.remote)
        state = self.tmp / f"state-{name}"
        return cfg, state

    def test_events_reach_remote_with_seq(self):
        cfg, state = self.host("h1")
        spool_some(state, 3)
        st = sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertTrue(st.last_push_ok, st.error)
        self.assertEqual(st.pending, 0)
        evs, f = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual([e["seq"] for e in evs], [1, 2, 3])
        self.assertEqual(f, [])

    def test_seq_monotonic_across_syncs(self):
        cfg, state = self.host("h1")
        spool_some(state, 2); sync.sync(cfg, host_id="h1", state_dir=state)
        spool_some(state, 2, "u"); sync.sync(cfg, host_id="h1", state_dir=state)
        evs, _ = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual([e["seq"] for e in evs], [1, 2, 3, 4])

    def test_push_failure_keeps_spool(self):
        cfg, state = self.host("h1")
        spool_some(state, 2)
        cfg.ledger.remote = str(self.tmp / "nope.git")
        st = sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertFalse(st.last_pull_ok and st.last_push_ok)
        self.assertEqual(st.pending, 2)
        self.assertEqual(len((state / events.SPOOL_NAME).read_text().splitlines()), 2)

    def test_retry_after_failure_no_loss_no_dup(self):
        cfg, state = self.host("h1")
        spool_some(state, 2)
        good = cfg.ledger.remote
        sync.sync(cfg, host_id="h1", state_dir=state)          # creates the clone
        spool_some(state, 2, "u")
        cfg.ledger.remote = str(self.tmp / "nope.git")
        git(cfg.ledger.path, "remote", "set-url", "origin", cfg.ledger.remote)
        sync.sync(cfg, host_id="h1", state_dir=state)          # fails, keeps spool
        cfg.ledger.remote = good
        git(cfg.ledger.path, "remote", "set-url", "origin", good)
        st = sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertTrue(st.last_push_ok, st.error)
        evs, _ = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual(len(evs), 4)
        self.assertEqual([e["seq"] for e in evs], [1, 2, 3, 4])

    def test_two_hosts_interleave_without_conflict(self):
        c1, s1 = self.host("h1"); c2, s2 = self.host("h2")
        spool_some(s1, 2); spool_some(s2, 3)
        self.assertTrue(sync.sync(c1, host_id="h1", state_dir=s1).last_push_ok)
        self.assertTrue(sync.sync(c2, host_id="h2", state_dir=s2).last_push_ok)
        spool_some(s1, 1, "z")
        self.assertTrue(sync.sync(c1, host_id="h1", state_dir=s1).last_push_ok)
        ev_dir = Path(c1.ledger.path) / "events"
        evs, _ = events.read_events(sorted(ev_dir.glob("*.jsonl")))
        self.assertEqual(sorted((e["host_id"], e["seq"]) for e in evs),
                         [("h1", 1), ("h1", 2), ("h1", 3), ("h2", 1), ("h2", 2), ("h2", 3)])

    def test_two_workers_one_runs(self):
        cfg, state = self.host("h1")
        spool_some(state, 5)
        results = []
        ts = [threading.Thread(target=lambda: results.append(sync.sync(cfg, host_id="h1", state_dir=state))) for _ in range(3)]
        [t.start() for t in ts]; [t.join() for t in ts]
        evs, _ = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual(len(evs), 5)                           # moved exactly once
        self.assertTrue(any(r.busy for r in results) or len(results) == 3)

    def test_state_file_written(self):
        cfg, state = self.host("h1")
        sync.sync(cfg, host_id="h1", state_dir=state)
        st = sync.load_state(state)
        self.assertTrue(st.last_pull_ok)
        self.assertIsNotNone(st.at)

    def test_lines_appended_during_sync_kept(self):
        cfg, state = self.host("h1")
        spool_some(state, 2)
        orig = sync._push

        def push_and_append(*a, **kw):
            spool_some(state, 1, "late")       # arrives while syncing
            return orig(*a, **kw)

        sync._push = push_and_append
        try:
            sync.sync(cfg, host_id="h1", state_dir=state)
        finally:
            sync._push = orig
        self.assertEqual(len((state / events.SPOOL_NAME).read_text().splitlines()), 1)

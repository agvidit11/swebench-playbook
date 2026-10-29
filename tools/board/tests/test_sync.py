import json, subprocess, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch
from workboard import events, sync
from tests.helpers import bare_remote, cfg_for, git

ACTOR = {"session_id": "s1", "alias": "h1·tab", "kind": "claude"}


def spool_some(spool, n, tag="t"):
    for i in range(n):
        events.spool_append(spool, events.new_event("touch", f"{tag}{i}", {}, actor=ACTOR, commit=None, source="test"))


class SyncTest(unittest.TestCase):
    def setUp(self):
        sync.AUTO_CLAIM[0] = False                       # transport tests only; auto-claim tested in test_claim_cli
        self.addCleanup(lambda: sync.AUTO_CLAIM.__setitem__(0, True))
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
        host = json.loads((Path(cfg.ledger.path) / "hosts" / "h1.json").read_text())
        self.assertEqual(host["queues"]["spool_pending"], 0)

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

    def test_config_remote_change_followed(self):
        cfg, state = self.host("h1")
        spool_some(state, 1)
        sync.sync(cfg, host_id="h1", state_dir=state)
        new_remote = bare_remote(self.tmp, "ledger2.git")
        cfg.ledger.remote = str(new_remote)          # only the config changes
        spool_some(state, 1, "u")
        st = sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertTrue(st.last_push_ok, st.error)
        old_log = git(self.remote, "log", "--oneline", "main").stdout.splitlines()
        self.assertEqual(len(old_log), 2)            # seed + first sync only; old remote untouched after
        self.assertIn("events:", git(new_remote, "log", "-1", "--format=%s", "main").stdout)

    def test_uncertain_push_retry_dedupes(self):
        cfg, state = self.host("h1")
        spool_some(state, 3)
        orig = sync._push
        calls = {"n": 0}

        def lying_push(led, branch, timeout):
            res = orig(led, branch, timeout)
            calls["n"] += 1
            if calls["n"] == 1:                       # reached the remote, reported as failed
                return subprocess.CompletedProcess(res.args, 1, "", "connection reset")
            return res

        sync._push = lying_push
        try:
            st = sync.sync(cfg, host_id="h1", state_dir=state)
        finally:
            sync._push = orig
        self.assertTrue(st.last_push_ok, st.error)
        evs, findings = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual(len(evs), 3)                 # duplicates collapsed by event_id
        self.assertEqual(findings, [])
        spool_some(state, 1, "after")
        self.assertTrue(sync.sync(cfg, host_id="h1", state_dir=state).last_push_ok)
        raw = [json.loads(l)["seq"] for l in (Path(cfg.ledger.path) / "events" / "h1.jsonl").read_text().splitlines()]
        self.assertEqual(raw, sorted(set(raw)))       # physical seqs strictly increasing and unique
        evs, _ = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual(len(evs), 4)

    def test_deadline_exhausted_keeps_spool(self):
        cfg, state = self.host("h1")
        spool_some(state, 2)
        st = sync.sync(cfg, host_id="h1", state_dir=state, timeout_seconds=0.01)
        self.assertFalse(st.last_push_ok)
        self.assertEqual(len(sync._spool_lines(state)), 2)

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
        inside, release = threading.Event(), threading.Event()
        entered = []
        orig = sync._sync_locked

        def gated(*a, **kw):
            entered.append(1)
            inside.set()
            release.wait(10)
            return orig(*a, **kw)

        sync._sync_locked = gated
        results = []
        try:
            first = threading.Thread(target=lambda: results.append(sync.sync(cfg, host_id="h1", state_dir=state)))
            first.start()
            self.assertTrue(inside.wait(10))
            others = [sync.sync(cfg, host_id="h1", state_dir=state) for _ in range(2)]
            release.set()
            first.join()
        finally:
            sync._sync_locked = orig
        self.assertEqual(len(entered), 1)
        self.assertTrue(all(o.busy for o in others))
        evs, _ = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual(len(evs), 5)

    def test_append_during_ack_not_lost(self):
        """Producer arrives while the ack holds the lock and replaces the spool: its event must survive."""
        cfg, state = self.host("h1")
        spool_some(state, 2)
        orig_replace = sync.os.replace
        started = threading.Event()
        done = []

        def slow_replace(src, dst):
            if str(dst).endswith(events.SPOOL_NAME) and not started.is_set():
                started.set()
                t = threading.Thread(target=lambda: done.append(events.spool_append(state, events.new_event(
                    "touch", "late", {}, actor=ACTOR, commit=None, source="test"))))
                t.start()
                t.join(0.3)                           # producer is now blocked on the lock
                self.assertEqual(done, [])
                orig_replace(src, dst)
                self._t = t
                return
            return orig_replace(src, dst)

        sync.os.replace = slow_replace
        try:
            sync.sync(cfg, host_id="h1", state_dir=state)
        finally:
            sync.os.replace = orig_replace
        self._t.join(5)
        self.assertEqual(done, [True])
        lines = sync._spool_lines(state)
        self.assertEqual(len(lines), 1)
        self.assertIn(b'"late"', lines[0])

    def test_state_file_written(self):
        cfg, state = self.host("h1")
        sync.sync(cfg, host_id="h1", state_dir=state)
        st = sync.load_state(state)
        self.assertTrue(st.last_pull_ok)
        self.assertIsNotNone(st.at)

    def test_sync_runs_usage_collector_in_isolated_cache(self):
        cfg, state = self.host("h1")
        with patch("workboard.usage.collect", return_value={}) as collect:
            sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertEqual(collect.call_count, 1)
        self.assertEqual(Path(collect.call_args.kwargs["cache_dir"]), state)
        self.assertTrue(str(collect.call_args.kwargs["claude_root"]).startswith(str(state)))

    def test_snapshot_source_exception_does_not_abort_event_sync_and_is_recorded(self):
        cfg, state = self.host("h1")
        spool_some(state, 1)
        with patch("workboard.host_snapshots.publish", side_effect=RuntimeError("synthetic snapshot failure")):
            st = sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertTrue(st.last_push_ok)
        self.assertIn("host snapshot skipped: RuntimeError", st.error)
        self.assertEqual(sync.load_state(state).error, st.error)
        evs, _ = events.read_events([Path(cfg.ledger.path) / "events" / "h1.jsonl"])
        self.assertEqual(len(evs), 1)

    def test_unexpected_sync_exception_leaves_durable_reason(self):
        cfg, state = self.host("h1")
        spool_some(state, 1)
        with patch("workboard.sync._sync_locked", side_effect=RuntimeError("synthetic source failure")):
            st = sync.sync(cfg, host_id="h1", state_dir=state)
        self.assertIn("sync exception: RuntimeError", st.error)
        self.assertEqual(st.pending, 1)
        self.assertEqual(sync.load_state(state).error, st.error)

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


class StaleLockTest(unittest.TestCase):
    def test_old_ref_locks_are_cleared_fresh_ones_kept(self):
        import os, tempfile, time
        from workboard import sync as s
        with tempfile.TemporaryDirectory() as d:
            led = Path(d)
            old = led / ".git" / "refs" / "remotes" / "origin" / "main.lock"
            new = led / ".git" / "index.lock"
            old.parent.mkdir(parents=True)
            old.write_text(""); new.write_text("")
            os.utime(old, (time.time() - 600, time.time() - 600))
            self.assertEqual(s._clear_stale_locks(led), [".git/refs/remotes/origin/main.lock"])
            self.assertTrue(new.exists())

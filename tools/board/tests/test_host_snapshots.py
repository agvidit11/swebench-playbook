import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workboard import host_snapshots


class HostSnapshotsTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.state = self.root / "state"
        self.ledger = self.root / "ledger"

    def test_publish_and_load_peer_are_redacted(self):
        now = datetime.now(timezone.utc)
        session = {
            "session_key": "claude:h2:100:domain:s1", "native_id": "s1", "kind": "claude",
            "kind_icon": "🟣", "host": "h2", "name": "synthetic", "status": "idle", "live": True,
            "cwd": "/private/repository", "pid": 42, "transport": {"available": True, "kind": "courier"},
            "child_runs": [{"session_key": "codex:h2:100:local:c1", "native_id": "c1", "kind": "codex",
                            "host": "h2", "cwd": "/private/child", "status": "idle"}],
        }
        host_snapshots.cache_local(self.state, "h2", [session], [], at=now.isoformat())
        host_snapshots.publish(self.ledger, self.state, "h2", at=now.isoformat(), spool_pending=3)
        raw = (self.ledger / "hosts" / "h2.json").read_text()
        self.assertNotIn("/private", raw)
        self.assertNotIn('"pid"', raw)
        rows, diagnostics = host_snapshots.load_peers(self.ledger, "h1", now=now.timestamp())
        self.assertEqual([r["session_key"] for r in rows], ["claude:h2:100:domain:s1"])
        self.assertTrue(rows[0]["remote"])
        self.assertTrue(rows[0]["transport"]["available"])
        state = next(d for d in diagnostics if d["classification"] == "host-state")
        self.assertEqual((state["queue"], state["sync_error"]), (3, ""))

    def test_stale_peer_is_not_reported_live_or_reachable(self):
        old = "2024-01-01T00:00:00+00:00"
        session = {"session_key": "claude:h2:1:d:s", "native_id": "s", "kind": "claude", "host": "h2",
                   "name": "old", "status": "busy", "live": True,
                   "transport": {"available": True, "kind": "courier"}}
        host_snapshots.cache_local(self.state, "h2", [session], [], at=old)
        host_snapshots.publish(self.ledger, self.state, "h2", at=old, spool_pending=0)
        rows, diagnostics = host_snapshots.load_peers(
            self.ledger, "h1", now=datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp())
        self.assertFalse(rows[0]["live"])
        self.assertFalse(rows[0]["transport"]["available"])
        self.assertEqual(rows[0]["status"], "unknown")
        self.assertIn("peer-stale", {d["classification"] for d in diagnostics})


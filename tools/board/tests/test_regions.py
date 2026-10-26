import hashlib
import http.client
import json
import os
import re
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from tests.test_visual import realistic, snap
from workboard import html, regions
from workboard.config import load_config


class RegionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wb-regions-")
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.patch.dict(os.environ, {
            "WORKBOARD_CACHE": str(Path(self.tmp.name) / "cache"),
            "WORKBOARD_STATE": str(Path(self.tmp.name) / "state"),
        })
        self.env.start(); self.addCleanup(self.env.stop)
        self.cfg = load_config(Path("/nonexistent"))
        self.snapshot = snap(realistic())
        self.full = html.payload(self.snapshot, self.cfg)

    def test_compact_board_moves_drawer_arrays_to_detail(self):
        data, details = regions.split_payload(self.full, now=self.snapshot.now)
        row = regions.expand_task(regions.unpack_board(data["board"])[0])
        detail = details[row["task"]]
        for key in regions.DETAIL_KEYS:
            self.assertNotIn(key, row)
        for key in ("validation", "decisions", "versions", "changed", "gates", "agent_reviews",
                    "legacy", "findings", "steps"):
            self.assertIn(key, detail)
        self.assertIn("row_version", row)
        self.assertNotIn("detail_version", row)
        self.assertIn("gate_summary", row)  # compact states used by row hovers, not full gate objects

    def test_strong_etag_is_exact_canonical_content_not_generation_time(self):
        gens = {key: "one" for key in ("codimango", "git", "ledger", "registry_runs", "presence")}
        cache = regions.RegionCache(self.full, now=self.snapshot.now, generations=gens)
        before = cache.region("board")
        changed = dict(self.full, generated_at="2099-01-01T00:00:00+00:00")
        cache.replace(changed, now=self.snapshot.now, generations=dict(gens, git="two"))
        after = cache.region("board")
        self.assertEqual(before.etag, after.etag)
        self.assertFalse(after.etag.startswith("W/"))
        self.assertEqual(after.etag.strip('"'), hashlib.sha256(after.body).hexdigest())

    def test_only_regions_whose_input_generation_changed_are_rebuilt(self):
        gens = {key: "one" for key in ("codimango", "git", "ledger", "registry_runs", "presence")}
        cache = regions.RegionCache(self.full, now=self.snapshot.now, generations=gens)
        before = cache.build_counts
        with mock.patch("workboard.regions.compact_task", wraps=regions.compact_task) as board_builder:
            cache.replace(self.full, now=self.snapshot.now, generations=dict(gens, registry_runs="two"))
        board_builder.assert_not_called()
        delta = {key: cache.build_counts[key] - before[key] for key in regions.NAMES}
        self.assertEqual(delta, {"summary": 0, "board": 0, "team": 1, "activity": 0, "stats": 0})

    def test_compatibility_view_reassembles_full_tasks(self):
        gens = {key: "one" for key in ("codimango", "git", "ledger", "registry_runs", "presence")}
        cache = regions.RegionCache(self.full, now=self.snapshot.now, generations=gens)
        task = cache.compatibility()["tasks"][0]
        self.assertIn("validation", task)
        self.assertIn("steps", task)
        self.assertEqual(task["task"], self.full["tasks"][0]["task"])


class RegionHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wb-http-")
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.patch.dict(os.environ, {
            "WORKBOARD_CACHE": str(Path(self.tmp.name) / "cache"),
            "WORKBOARD_STATE": str(Path(self.tmp.name) / "state"),
        })
        self.env.start(); self.addCleanup(self.env.stop)
        self.cfg = load_config(Path("/nonexistent"))
        self.snapshot = snap(realistic())
        self.server = html.serve(lambda: self.snapshot, self.cfg, port=0, interval=3600, team_interval=3600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop)
        self.port = self.server.server_address[1]

    def _stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(2)

    def request(self, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", path, headers=headers or {})
        response = conn.getresponse(); body = response.read(); result = response.status, dict(response.headers), body
        conn.close(); return result

    def test_all_regions_have_strong_etags_and_304_has_no_body(self):
        for name in regions.NAMES:
            status, headers, body = self.request("/api/regions/" + name)
            self.assertEqual(status, 200)
            self.assertEqual(body, regions.canonical_bytes(json.loads(body)))
            etag = headers["ETag"]
            self.assertTrue(etag.startswith('"') and etag.endswith('"'))
            status, headers2, body2 = self.request("/api/regions/" + name,
                                                   {"If-None-Match": etag})
            self.assertEqual((status, body2, headers2.get("Content-Length")), (304, b"", "0"))
            self.assertEqual(headers2["ETag"], etag)

    def test_lazy_task_and_compatibility_endpoints(self):
        task = self.snapshot.views[0].entity_id
        status, headers, body = self.request("/api/task/" + urllib.parse.quote(task, safe=""))
        self.assertEqual(status, 200)
        detail = json.loads(body)
        for key in ("validation", "decisions", "versions", "changed", "gates", "agent_reviews",
                    "legacy", "findings_detail", "steps"):
            self.assertIn(key, detail)
        status, _, full_body = self.request("/data.json")
        full = json.loads(full_body)
        self.assertEqual(status, 200)
        self.assertIn("validation", full["tasks"][0])
        status, _, root = self.request("/")
        self.assertEqual(status, 200)
        blob = re.search(rb'<script id="data" type="application/json">(.*?)</script>', root, re.S).group(1)
        bootstrap = json.loads(blob.replace(b"<\\/", b"</"))
        self.assertNotIn("validation", regions.expand_task(regions.unpack_board(bootstrap)[0]))
        self.assertEqual(set(bootstrap["_etags"]), {"summary", "board"})

    def test_health_identifies_workboard(self):
        status, _, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["service"], "workboard")

    def test_lazy_online_usage_endpoint_is_numeric_and_sanitized(self):
        task = self.snapshot.views[0].entity_id
        value = {"source": "codimango read-only CLI", "run_count": 2, "trial_count": 7,
                 "trials_by_kind": {"oracle": 3, "codex": 4},
                 "cost": {"available": False, "label": "cost unavailable"}}
        with mock.patch("workboard.costs.online_usage", return_value=value):
            status, _, body = self.request("/api/spend/" + urllib.parse.quote(task, safe=""))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), value)
        self.assertNotIn(b"prompt", body.lower())


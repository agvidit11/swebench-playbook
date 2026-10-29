import json
import re
import threading
import unittest
import urllib.request
from pathlib import Path

from workboard import html
from workboard.config import load_config
from tests.test_visual import realistic, snap


class HtmlTest(unittest.TestCase):
    def setUp(self):
        import os, tempfile
        from unittest import mock
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        env = mock.patch.dict(os.environ, {"WORKBOARD_CACHE": td.name})   # never read the real facts store
        env.start()
        self.addCleanup(env.stop)
        self.cfg = load_config(Path("/nonexistent"))

    def test_page_embeds_valid_json_and_escapes(self):
        views = realistic()
        views[0].fields["owner"] = "</script><b>x"
        page = html.page(html.payload(snap(views), self.cfg))
        blob = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S).group(1)
        data = json.loads(blob.replace("<\\/", "</"))
        self.assertEqual(len(data["tasks"]), len(views))
        self.assertNotIn("</script><b>", blob)
        for key in ("week", "weekly", "funnel", "flow", "ages", "health"):
            self.assertIn(key, data)
        self.assertNotIn("http://", page.replace("http://localhost", ""))     # no external assets
        self.assertNotIn("https://", page)

    def test_serve_index_and_data(self):
        srv = html.serve(lambda: snap(realistic()), self.cfg, port=0, interval=3600)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            body = urllib.request.urlopen(f"http://127.0.0.1:{port}/").read().decode()
            self.assertIn("workboard", body)
            self.assertIn("const LIVE = true", body)
            data = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/data.json").read())
            self.assertEqual(len(data["tasks"]), len(realistic()))
            with self.assertRaises(Exception):
                urllib.request.urlopen(f"http://127.0.0.1:{port}/etc/passwd")
        finally:
            srv.shutdown()

    def test_team_and_owner_contract_is_in_the_inline_page(self):
        from workboard.html_page import PAGE
        for text in ("server-grid", "session-table", "status · for", "focus tasks", "hooks / transport",
                     "data-session", "openSession", "MESSAGE THIS SESSION", "claude:'C'", "board status</code> there"):
            self.assertIn(text, PAGE)
        for text in ("✍ working", "💤 assigned idle", "⏳ in pipeline", "🛠 pushed", "🔓 free", "🔓 free"):
            self.assertIn(text, PAGE)
        self.assertNotIn("predates the current board hooks", PAGE)

    def test_region_cadences_and_no_full_snapshot_poll(self):
        from workboard.html_page import PAGE
        for text in ("pollRegion('summary')", "pollRegion('board')", "pollRegion('team')",
                     "pollRegion('activity')", "pollRegion('stats')", "60000", "15000", "30000", "300000"):
            self.assertIn(text, PAGE)
        self.assertNotIn("fetch('data.json'", PAGE)

    def test_busy_user_keyboard_and_token_contract(self):
        from workboard.html_page import PAGE
        for text in ("Primary action", "local tokens: Claude", "last hour", "% context",
                     "e.key.toLowerCase()==='t'", "e.key.toLowerCase()==='b'", "e.key==='Escape'",
                     "No tasks match these filters", "No live sessions were discovered"):
            self.assertIn(text, PAGE)

    def test_inline_page_uses_no_multi_codepoint_emoji_sequences(self):
        from workboard.html_page import PAGE
        self.assertNotIn("\ufe0f", PAGE)
        self.assertNotIn("\u200d", PAGE)


class LinksTest(unittest.TestCase):
    def test_links_projected_and_rendered(self):
        from datetime import datetime, timezone
        from workboard.config import Repository
        from workboard.model import Observation
        from workboard.projection import project
        cfg = load_config(Path("/nonexistent"))
        cfg.codimango.web_task_url = "https://example.test/tasks/{task}"
        cfg.repositories = [Repository(id="tasks", path="/x", remote_url="ssh://git@github.com:22/org/tasks.git", branch="main")]
        now = datetime.now(timezone.utc)
        obs = [Observation("codimango", "t1", now, {"codimango.status": "draft", "codimango.validation_status": "passing",
                                                     "codimango.github_url": "https://github.com/org/tasks/tree/abc/t1"}),
               Observation("git", "t1", now, {"git.repo": "tasks", "git.task_head": "a" * 40})]
        v = project(obs, [], cfg, now)[0]
        self.assertEqual(v.fields["links"], {"codimango": "https://example.test/tasks/t1",
                                             "github": "https://github.com/org/tasks/tree/abc/t1",
                                             "latest": "https://github.com/org/tasks/tree/main/t1"})
        page = html.page(html.payload(snap([v]), cfg))
        self.assertIn("https://example.test/tasks/t1", page)

    def test_osc8_ignored_by_width(self):
        from workboard import tui
        self.assertEqual(tui.dwidth(tui.link("abc", "https://x.test/y")), 3)

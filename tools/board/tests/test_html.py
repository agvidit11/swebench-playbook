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

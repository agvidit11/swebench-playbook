import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workboard import completion
from workboard.__main__ import build_parser


class CompletionTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        d = Path(td.name)
        (d / "codimango-last-good.json").write_text(json.dumps({"rows": [
            {"name": "alpha-task", "status": "draft"}, {"name": "beta-task", "status": "accepted"},
            {"name": "gone-task", "status": "archived"}]}))
        (d / "hook-state.json").write_text(json.dumps({"aliases": {"s1": {"alias": "h1·Lane orchestrator loop"}}}))
        p = mock.patch.dict(os.environ, {"WORKBOARD_CACHE": td.name})
        p.start()
        self.addCleanup(p.stop)
        self.parser = build_parser()

    def c(self, *words):
        words = ["board", *words]
        return completion.candidates(self.parser, words, len(words) - 1)

    def test_subcommands(self):
        self.assertIn("show", self.c(""))
        self.assertEqual(self.c("sta"), ["stats", "status"])
        self.assertNotIn("hook", self.c(""))

    def test_task_names_skip_archived(self):
        self.assertEqual(self.c("show", ""), ["alpha-task", "beta-task"])
        self.assertEqual(self.c("show", "alp"), ["alpha-task"])
        self.assertEqual(self.c("review", "add", "bet"), ["beta-task"])

    def test_flags_and_values(self):
        self.assertIn("--wide", self.c("list", "--w"))
        self.assertEqual(self.c("review", "add", "alpha-task", "--verdict", "r"), ["ready"])
        self.assertEqual(self.c("claim", "alpha-task", "--to", "lane"), ["Lane orchestrator loop"])

    def test_action_words(self):
        self.assertEqual(self.c("check", ""), ["run"])
        self.assertEqual(self.c("rank", ""), ["show", "import"])

import io
import re
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workboard import tui
from workboard.app import Snapshot
from workboard.config import load_config
from workboard.model import SourceHealth, TaskView
from workboard.sync import SyncState

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def tv(name, group="READY", **f):
    base = {"group": group, "next": "SUBMIT", "state": "DRAFT", "state_age_s": 7200, "age_level": "ok", "owner": "h1·lane",
            "claim_health": "OWNED", "valid": "PASS", "review": "R2", "confidence": 4, "confidence_stale": False,
            "sync": "OK", "check": "P20 W1 F0", "check_stale": False, "check_fail": False}
    base.update(f)
    return TaskView(name, base, [])


def snap(views):
    return Snapshot(views, [], [], {"codimango": SourceHealth("codimango", True, NOW, 900, "live")}, [],
                    SyncState(last_pull_ok=True, last_push_ok=True), NOW)


class TuiTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))
        self.views = [tv("sbdiff-unified-patch-squash", "ATTENTION", next="RERUN server", sync="STALE_VALID", review="R~"),
                      tv("pgmem-null-aggregate-conformance", "ATTENTION", next="FIX validation", valid="FAIL",
                         claim_health="FREE", owner=""),
                      tv("aato-tag-copy-bulk-retag", "REVIEWING", next="WAIT reviewer", review="R1", confidence=3),
                      tv("a" * 70, "READY"), tv("done-task", "DONE", next="—", state="ACCEPTED")]

    def table_lines(self, text):
        return [ANSI.sub("", l) for l in text.splitlines() if ANSI.sub("", l).lstrip().startswith(("│", "╭", "├", "╰"))]

    def test_box_rows_align_with_emoji(self):
        for width in (100, 140, 200):
            text = tui.render(snap(self.views), self.cfg, width=width, changed={"aato-tag-copy-bulk-retag"})
            widths = {tui.dwidth(l) for l in self.table_lines(text)}
            self.assertEqual(len(widths), 1, (width, widths))
            self.assertLessEqual(widths.pop(), width)

    def test_ticks_and_markers(self):
        text = ANSI.sub("", tui.render(snap(self.views), self.cfg, width=180, changed={"aato-tag-copy-bulk-retag"}))
        self.assertIn("✓✓", text.split("╰")[1])            # legend
        self.assertIn("↻✓", text)
        self.assertIn("✦", text)
        self.assertIn("🔓 free", text)
        self.assertIn("🔁 RERUN server", text)
        self.assertIn("1 done", text)

    def test_dwidth(self):
        self.assertEqual(tui.dwidth("🔥"), 2)
        self.assertEqual(tui.dwidth("🛠️ x"), 4)
        self.assertEqual(tui.dwidth("\x1b[31mab\x1b[0m"), 2)
        self.assertEqual(tui.dwidth(tui.clip("x" * 50, 10)), 10)

    def test_empty(self):
        text = tui.render(snap([tv("d", "DONE")]), self.cfg, width=120)
        self.assertIn("nothing needs you", text)

    def test_changed_since(self):
        prev = {"aato-tag-copy-bulk-retag": {"state": "QUEUE", "valid": "PASS", "next": "WAIT reviewer",
                                             "review": "R1", "owner": "h1·lane"}}
        self.assertIn("aato-tag-copy-bulk-retag", tui._changed_since(prev, snap(self.views)))
        self.assertEqual(tui._changed_since(None, snap(self.views)), set())

    def test_watch_once_no_tty(self):
        out = io.StringIO()
        tui.watch(lambda: snap(self.views), self.cfg, interval=1, once=True, out=out)
        self.assertIn("workboard", out.getvalue())
        self.assertTrue(out.getvalue().endswith("\x1b[?25h\x1b[?1049l"))

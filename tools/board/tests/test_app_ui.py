import unittest
from pathlib import Path

from workboard import app_ui
from workboard.config import load_config
from tests.test_visual import VisualContract, WIDTHS, realistic, snap, plain


class AppUITest(unittest.TestCase, VisualContract):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))

    def screen(self, st, width=140, height=60):
        return app_ui.screen(snap(realistic()), self.cfg, st, width=width, height=height,
                             changed={"mst-patch-log-atomic-json-interop"}, host_tag="23237", status="🕐 status")

    def test_tabs_render_cleanly_at_all_widths(self):
        for tab in ("board", "stats", "help"):
            for w in WIDTHS:
                st = app_ui.UIState(tab=tab, detail=True)
                self.assert_screen_ok(self.screen(st, width=w, height=200), w)

    def test_filters(self):
        views = realistic()
        st = app_ui.UIState()
        self.assertEqual(len(app_ui.visible(views, st)), 10)
        st.owner = "free"
        self.assertEqual([v.entity_id for v in app_ui.visible(views, st)], ["openspout-transactional-sheet-replacement",
                                                                           "aato-tag-copy-bulk-retag"])
        st.owner, st.groups = "all", {"REVIEWING", "VALIDATING"}
        self.assertEqual(len(app_ui.visible(views, st)), 2)
        st.groups, st.query = {"ATTENTION", "READY", "VALIDATING", "REVIEWING"}, "bigtree"
        self.assertEqual(app_ui.visible(views, st), [])
        st.query, st.owner = "", "mine"
        self.assertEqual([v.entity_id for v in app_ui.visible(views, st, "23237")], ["removestar-star-import-binding-fidelity"])

    def test_keys(self):
        st = app_ui.UIState()
        self.assertIsNone(app_ui.handle_key(st, "j", 5))
        self.assertEqual(st.sel, 1)
        app_ui.handle_key(st, "G", 5)
        self.assertEqual(st.sel, 4)
        app_ui.handle_key(st, "a", 5)
        self.assertNotIn("ATTENTION", st.groups)
        app_ui.handle_key(st, "f", 5)
        self.assertEqual(st.owner, "free")
        for k in "/ope":
            app_ui.handle_key(st, k, 5)
        self.assertEqual((st.typing, st.query), (True, "ope"))
        app_ui.handle_key(st, "ESC", 5)
        self.assertEqual((st.typing, st.query), (False, ""))
        app_ui.handle_key(st, "2", 5)
        self.assertEqual(st.tab, "stats")
        self.assertEqual(app_ui.handle_key(st, "q", 5), "quit")

    def test_selection_marker_and_detail(self):
        st = app_ui.UIState(sel=1, detail=True)
        text = "\n".join(plain(self.screen(st)))
        self.assertIn("▶", text)
        self.assertIn("🔎 details", text)
        self.assertIn("board explain", text)

    def test_tall_list_keeps_selection_visible(self):
        st = app_ui.UIState(sel=9)
        text = "\n".join(plain(self.screen(st, height=20)))
        self.assertLessEqual(len(text.splitlines()), 20)
        self.assertIn("▶", text)

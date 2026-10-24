import re, unittest
from datetime import datetime, timezone
from workboard.model import Finding, SourceHealth, TaskView
from workboard import render

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def tv(name, group="READY", next="SUBMIT", state="DRAFT", age=7200, owner="h1·lane loop", claim_health="OWNED",
       valid="PASS", review="R2", conf=4, sync="OK", findings=(), check="P20 W1 F0", check_stale=False, conf_stale=False):
    return TaskView(name, {"group": group, "next": next, "state": state, "state_age_s": age, "age_level": "ok",
                           "owner": owner, "claim_health": claim_health, "valid": valid, "review": review,
                           "confidence": conf, "confidence_stale": conf_stale, "sync": sync, "check": check,
                           "check_stale": check_stale, "pushes": "2+1", "pushes_before_submit": 2, "pushes_after_submit": 1, "round": None,
                           "track": "swe-bench-multi-turn", "dissent": 0}, list(findings))


HEALTH_OK = {"codimango": SourceHealth("codimango", True, NOW, 900, "live"), "git": SourceHealth("git", True, NOW, 900, "ok")}


class RenderTest(unittest.TestCase):
    def out(self, views, width=120, color=False, unicode=True, health=HEALTH_OK, wide=False, **kw):
        style = render.Style(color=color, unicode=unicode)
        return render._render_list(views, health, now=NOW, width=width, style=style, wide=wide, **kw)

    def test_groups_in_order_and_done_collapsed(self):
        views = [tv("a", "WAITING", "WAIT reviewer"), tv("b", "ATTENTION", "FIX validation", valid="FAIL"),
                 tv("c", "DONE", "—", state="ACCEPTED"), tv("d")]
        text = self.out(views)
        self.assertLess(text.index("ATTENTION"), text.index("READY"))
        self.assertLess(text.index("READY"), text.index("WAITING"))
        self.assertIn("Done: 1 (use --all)", text)
        self.assertNotIn(" c ", text)

    def test_compact_columns_and_wide_adds(self):
        compact = self.out([tv("alpha-task")])
        for col in ("TASK", "NEXT", "STATE/AGE", "OWNER", "VALID", "REVIEW", "SYNC"):
            self.assertIn(col, compact)
        self.assertNotIn("PUSHES", compact)
        wide = self.out([tv("alpha-task")], width=200, wide=True)
        for col in ("ROUND", "PUSHES", "CHECK", "TRACK"):
            self.assertIn(col, wide)

    def test_80_cols_drops_columns_keeps_next(self):
        text = self.out([tv("a-very-long-task-name-that-goes-on-and-on-forever", next="FIX validation")], width=80)
        for line in text.splitlines():
            self.assertLessEqual(len(line), 80, line)
        self.assertIn("FIX validation", text)
        self.assertIn("NEXT", text)

    def test_every_line_fits_width(self):
        failed = dict(HEALTH_OK, codimango=SourceHealth("codimango", False, NOW, 900, "timeout after 60s " * 6))
        views = [tv("a-very-long-task-name-that-goes-on-and-on-forever", next="FIX validation", review="R~",
                    conf_stale=True, sync="HEAD≠SERVER", owner="", claim_health="FREE"),
                 tv("b", claim_health="EXPIRED", owner="h2·x", valid="RUN"), tv("c", claim_health="CONFLICT", valid="FAIL")]
        header = "W43: 13 accepted  ·  last week at this point 10  ·  4-week median 8.5  (accepted incl. used_in_training, by acceptance date)"
        for width, wide in ((80, False), (120, False), (200, True)):
            text = self.out(views, width=width, wide=wide, health=failed, header=header,
                            warnings=["a fairly long warning message that keeps going " * 3], color=True)
            for line in ANSI.sub("", text).splitlines():
                self.assertLessEqual(len(line), width, f"{width}: {line!r}")
            self.assertIn("FIX validation", ANSI.sub("", text))

    def test_group_by_state(self):
        text = self.out([tv("a", state="DRAFT"), tv("b", state="REVIEW", group="WAITING")], group="state")
        self.assertIn("DRAFT (1)", text)
        self.assertIn("REVIEW (1)", text)

    def test_public_render_list_signature(self):
        text = render.render_list([tv("a")], HEALTH_OK, None, width=100, color="never", unicode="never")
        self.assertIn("TASK", text)
        self.assertIsNone(ANSI.search(text))

    def test_task_name_middle_truncated(self):
        name = "a-very-long-task-name-that-goes-on-and-on-forever-and-ever"
        text = self.out([tv(name)], width=90)
        self.assertNotIn(name, text)
        self.assertIn("a-very", text)
        self.assertIn("ever", text)

    def test_pipe_no_ansi_stable(self):
        text = self.out([tv("a")], color=False, unicode=False)
        self.assertIsNone(ANSI.search(text))
        self.assertNotIn("✓", text)

    def test_color_repeats_words(self):
        text = self.out([tv("a", valid="FAIL")], color=True)
        self.assertIsNotNone(ANSI.search(text))
        self.assertIn("FAIL", ANSI.sub("", text))

    def test_banner_sync_failed(self):
        health = dict(HEALTH_OK, codimango=SourceHealth("codimango", False, NOW, 900, "timeout after 60s"))
        text = self.out([tv("a")], health=health)
        self.assertIn("SYNC FAILED", text.splitlines()[0])
        self.assertIn("timeout", text.splitlines()[0])

    def test_legend_only_present_symbols(self):
        text = self.out([tv("a", review="R~", conf_stale=True)])
        legend = text[text.index("Legend"):]
        self.assertIn("R~", legend)
        self.assertNotIn("CONFLICT", legend)

    def test_stale_check_marked_in_wide(self):
        text = self.out([tv("a", check_stale=True)], width=200, wide=True, color=False, unicode=False)
        self.assertIn("~P20", text)

    def test_owner_free_and_expired(self):
        text = self.out([tv("a", owner="", claim_health="FREE"), tv("b", owner="h2·x", claim_health="EXPIRED")], width=140)
        self.assertIn("FREE", text)
        self.assertIn("EXPIRED", text)

    def test_age_format(self):
        self.assertEqual(render.fmt_age(59), "<1m")
        self.assertEqual(render.fmt_age(7200), "2h")
        self.assertEqual(render.fmt_age(3 * 86400 + 5), "3d")

    def test_empty_list(self):
        self.assertIn("No tasks", self.out([]))


class StyleTest(unittest.TestCase):
    def test_no_color_env(self):
        s = render.Style.detect("auto", "auto", isatty=True, env={"NO_COLOR": "1", "TERM": "xterm", "LANG": "en_US.UTF-8"})
        self.assertFalse(s.color)

    def test_dumb_term_ascii(self):
        s = render.Style.detect("auto", "auto", isatty=True, env={"TERM": "dumb"})
        self.assertFalse(s.color)
        self.assertFalse(s.unicode)

    def test_non_tty_plain(self):
        s = render.Style.detect("auto", "auto", isatty=False, env={"TERM": "xterm", "LANG": "en_US.UTF-8"})
        self.assertFalse(s.color)

    def test_always_overrides_tty(self):
        s = render.Style.detect("always", "always", isatty=False, env={})
        self.assertTrue(s.color and s.unicode)

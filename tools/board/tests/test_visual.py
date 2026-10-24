"""Structural visual tests for the pretty views: no line overflows, boxes are rectangular, styles are closed,
and only emoji with a stable two-cell width are used. Run at several terminal widths with realistic data."""
import re
import unicodedata
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workboard import tui
from workboard.app import Snapshot
from workboard.config import load_config
from workboard.model import Observation, SourceHealth, TaskView
from workboard.sync import SyncState

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
ANSI = re.compile(r"\x1b\[[0-9;]*m")
WIDTHS = (80, 100, 120, 160, 200)
BOX_CHARS = "╭╮╰╯│├┤"


def tv(name, group, **f):
    base = {"group": group, "next": "SUBMIT", "state": "DRAFT", "state_age_s": 7200, "age_level": "ok",
            "owner": "6971·SWE-bench lane orchestrator loop", "claim_health": "OWNED", "valid": "PASS",
            "review": "R2", "confidence": 4, "confidence_stale": False, "sync": "OK", "check": "P20 W1 F0",
            "check_stale": False, "check_fail": False, "active": []}
    base.update(f)
    return TaskView(name, base, [])


def realistic():
    return [
        tv("sbdiff-unified-patch-squash", "ATTENTION", next="RERUN server", state="NEEDS_REV", sync="STALE_VALID",
           review="R0", confidence=5),
        tv("openspout-transactional-sheet-replacement", "ATTENTION", next="FIX validation", valid="FAIL",
           claim_health="FREE", owner="", age_level="warn", state_age_s=4 * 86400),
        tv("cancancan-limited-ability-common-permission", "ATTENTION", next="FIX validation", valid="FAIL",
           claim_health="LEGACY", owner="23237 (CLAIMS.md)", state="NEEDS_REV", age_level="block"),
        tv("x-conflict-task", "ATTENTION", next="RESOLVE CONFLICT", claim_health="CONFLICT", owner="6971·a / 23237·b"),
        tv("django-model-utils-fieldtracker-db-truth", "READY", next="RUN check", claim_health="ACTIVE",
           owner="6971·Codex run", active=[{"alias": "6971·Codex run", "ago_s": 720}], sync="OK·doc", check="NONE"),
        tv("mst-patch-log-atomic-json-interop", "READY", next="ADDRESS review", state="NEEDS_REV", review="R1",
           confidence=3),
        tv("trickster-authoritative-refresh-reconciliation", "READY", next="GET R2", review="R~", confidence_stale=True,
           check_stale=True),
        tv("hello-world", "READY", next="IMPORT task", state="NOT_IMPORTED", valid="—", sync="—", state_age_s=None),
        tv("aato-tag-copy-bulk-retag", "WAITING", next="WAIT reviewer", state="REVIEW", claim_health="EXPIRED",
           owner="23237·harness loop"),
        tv("removestar-star-import-binding-fidelity", "WAITING", next="WAIT validation", valid="RUN",
           owner="23237·agvidit (shell)", sync="HEAD≠SERVER"),
        tv("done-one", "DONE", next="—", state="ACCEPTED"),
    ]


def snap(views, healthy=True):
    h = SourceHealth("codimango", healthy, NOW, 900, "live" if healthy else "exit 1: auth expired")
    obs = [Observation("codimango", f"a{i}", NOW, {"codimango.status": "accepted",
                                                   "codimango.reviewed_at": "2026-10-20T18:00:00Z",
                                                   "codimango.entered_pool_at": "2026-10-18T18:00:00Z",
                                                   "codimango.created_at": "2026-10-15T18:00:00Z",
                                                   "codimango.track": "swe-bench-multi-turn"}) for i in range(14)]
    return Snapshot(views, obs, [], {"codimango": h, "git": SourceHealth("git", True, NOW, 900, "ok")}, [],
                    SyncState(last_pull_ok=True, last_push_ok=True), NOW)


def plain(text):
    return [ANSI.sub("", l) for l in text.splitlines()]


class VisualContract:
    """Mixin: assertions every pretty screen must satisfy."""

    def assert_screen_ok(self, text, width):
        lines = plain(text)
        for l in lines:
            self.assertLessEqual(tui.dwidth(l), width, f"[{width}] overflow: {l!r}")
        # styles closed on every line that opens one
        for raw in text.splitlines():
            codes = ANSI.findall(raw)
            if codes:
                self.assertEqual(codes[-1], "\x1b[0m", f"[{width}] style left open at end of line: {raw!r}")
        # every box (consecutive lines between ╭ and ╰) is a rectangle with aligned borders
        box, start_col = [], None
        for l in lines:
            s = l.lstrip()
            if s.startswith("╭"):
                box, start_col = [l], len(l) - len(s)
            elif box:
                box.append(l)
                if s.startswith("╰"):
                    widths = {tui.dwidth(x.rstrip()) for x in box}
                    self.assertEqual(len(widths), 1, f"[{width}] ragged box: {sorted(widths)}\n" + "\n".join(box))
                    for x in box:
                        self.assertEqual(len(x) - len(x.lstrip()), start_col, f"[{width}] left border moved: {x!r}")
                        self.assertIn(x.rstrip()[-1], "╮│┤╯", f"[{width}] right border missing: {x!r}")
                    box = []
        self.assertEqual(box, [], f"[{width}] unterminated box")
        # emoji inventory: only single-codepoint wide emoji (no VS16 / ZWJ sequences)
        joined = "".join(lines)
        self.assertNotIn("‍", joined, "ZWJ emoji sequence")
        self.assertNotIn("️", joined, "emoji variation selector")
        for ch in set(joined):
            if 0x1F000 <= ord(ch) <= 0x1FAFF:
                self.assertIn(unicodedata.east_asian_width(ch), "WF", f"emoji {ch!r} has unstable width")


class BoardVisualTest(unittest.TestCase, VisualContract):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))

    def test_board_all_widths(self):
        for w in WIDTHS:
            self.assert_screen_ok(tui.render(snap(realistic()), self.cfg, width=w, changed={"mst-patch-log-atomic-json-interop"}), w)

    def test_board_unhealthy_and_all(self):
        for w in WIDTHS:
            self.assert_screen_ok(tui.render(snap(realistic(), healthy=False), self.cfg, width=w, show_all=True), w)

    def test_board_empty(self):
        for w in WIDTHS:
            self.assert_screen_ok(tui.render(snap([tv("d", "DONE")]), self.cfg, width=w), w)

    def test_next_column_never_truncated(self):
        for w in WIDTHS:
            text = "\n".join(plain(tui.render(snap(realistic()), self.cfg, width=w)))
            for n in ("RERUN server", "FIX validation", "RESOLVE CONFLICT", "WAIT validation"):
                self.assertIn(n, text, f"[{w}] NEXT truncated: {n}")

    def test_every_task_visible(self):
        for w in WIDTHS:
            text = "\n".join(plain(tui.render(snap(realistic()), self.cfg, width=w)))
            for v in realistic()[:-1]:
                head = v.entity_id[:6]
                self.assertIn(head, text, f"[{w}] task missing: {v.entity_id}")


class StatsVisualTest(unittest.TestCase, VisualContract):
    def test_stats_all_widths(self):
        cfg = load_config(Path("/nonexistent"))
        rank_data = {"source": "import r.md", "fetched_at": "2026-10-23T00:00:00",
                     "rows": [{"scope": "1 SWE multi-turn track", "window": "This quarter Q4 (from 2026-10-01)",
                               "metric": "accepted", "value": 27, "rank": 2, "of": 209},
                              {"scope": "5 Team", "window": "Last 30 days", "metric": "accepted", "value": 38, "rank": 2,
                               "of": 11}]}
        per_repo = {"available": True, "by_repo": {"org/ruby-auth0": 4, "org/dropshot": 4}, "coverage": "8/8", "reason": ""}
        for w in WIDTHS:
            self.assert_screen_ok(tui.render_stats(snap(realistic()), cfg, width=w, rank_data=rank_data, per_repo=per_repo), w)

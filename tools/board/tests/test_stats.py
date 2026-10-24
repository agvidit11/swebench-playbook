import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workboard import rank, stats
from workboard.config import load_config
from workboard.model import Observation

NOW = datetime(2026, 10, 21, 23, 22, tzinfo=timezone.utc)   # Wed 16:22 PT


def cm(name, status, reviewed=None, pool=None, created="2026-09-01T00:00:00Z", track="swe-bench-multi-turn", before=None):
    f = {"codimango.status": status, "codimango.reviewed_at": reviewed, "codimango.entered_pool_at": pool,
         "codimango.created_at": created, "codimango.track": track, "codimango.updated_at": "u"}
    if before:
        f["codimango.status_before_archive"] = before
    return Observation("codimango", name, NOW, f)


class StatsTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(Path("/nonexistent"))
        obs = []
        # W43 (Mon Oct 19 PT): 8 MT + 2 ST accepted; W42: 12; W41: 19
        for i in range(8):
            obs.append(cm(f"a{i}", "accepted", "2026-10-20T18:00:00Z"))
        for i in range(2):
            obs.append(cm(f"b{i}", "used_in_training", "2026-10-21T18:00:00Z", track="swe-bench-external-repos"))
        for i in range(12):
            obs.append(cm(f"c{i}", "accepted", "2026-10-14T18:00:00Z"))
        for i in range(19):
            obs.append(cm(f"d{i}", "accepted", "2026-10-07T18:00:00Z"))
        obs.append(cm("e", "archived", "2026-10-07T18:00:00Z", before="accepted"))
        obs.append(cm("f", "needs_revision", "2026-10-20T10:00:00Z", pool="2026-10-15T00:00:00Z"))
        obs.append(cm("g", "draft", created="2026-10-20T00:00:00Z"))
        obs.append(Observation("git", "g", NOW, {"git.task_head": "x"}))
        obs.append(Observation("git", "__repo__:tasks", NOW, {}))
        self.obs = obs

    def test_weekly_matches_hand_count(self):
        rows = {r["week"].date().isoformat(): r for r in stats.weekly(self.obs, self.cfg, NOW, 4)}
        self.assertEqual(rows["2026-10-19"]["accepted"], 10)
        self.assertEqual((rows["2026-10-19"]["accepted_mt"], rows["2026-10-19"]["accepted_st"]), (8, 2))
        self.assertEqual(rows["2026-10-12"]["accepted"], 12)
        self.assertEqual(rows["2026-10-05"]["accepted"], 19)      # archived-after-acceptance not counted

    def test_this_week_vs_same_point_and_median(self):
        n = stats.week_numbers(self.obs, self.cfg, NOW)
        self.assertEqual(n["this_week"], 10)
        self.assertEqual(n["same_point_last_week"], 12)          # Oct 14 18:00Z is before Wed 16:22 PT
        self.assertEqual(n["median_4wk"], 6)                     # [12, 19, 0, 0] -> median 6

    def test_funnel_uses_codimango_archived(self):
        f = stats.funnel(self.obs)
        self.assertEqual(f["archived"], 1)
        self.assertEqual(f["archived_after_accept"], 1)
        self.assertEqual(f["built"], 1)                          # __repo__ entity excluded
        self.assertEqual(f["accepted"], 41)

    def test_first_submission_rate_by_cohort(self):
        rounds = {"f": 1}
        obs = self.obs + [cm("h", "accepted", "2026-10-20T00:00:00Z", pool="2026-10-15T00:00:00Z")]
        rounds["h"] = 0
        cohorts = stats.first_pass_by_cohort(obs, rounds, self.cfg)
        self.assertEqual((cohorts[-1]["decided"], cohorts[-1]["first_pass"], cohorts[-1]["rate"]), (2, 1, 50))

    def test_revision_rounds_cached_and_coverage(self):
        import subprocess
        calls = []

        def runner(argv, **kw):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "  REVISION by X\n  REVISION by Y\n", "")

        with tempfile.TemporaryDirectory() as d:
            r = stats.revision_rounds(self.cfg, self.obs, Path(d), runner=runner)
            self.assertEqual(r["rounds"]["f"], 2)
            self.assertEqual((r["covered"], r["eligible"]), (1, 1))
            stats.revision_rounds(self.cfg, self.obs, Path(d), runner=runner)
            self.assertEqual(len(calls), 1)                      # second run served from cache

    def test_submitted_is_entered_pool_only(self):
        obs = [cm("p", "draft", pool="2026-10-20T00:00:00Z"), cm("q", "needs_revision")]
        rows = {r["week"].date().isoformat(): r for r in stats.weekly(obs, self.cfg, NOW, 1)}
        self.assertEqual(rows["2026-10-19"]["submitted"], 1)      # bounced back to draft still counts its submission
        self.assertEqual(stats.funnel(obs)["submitted"], 1)

    def test_window_bounds_pt_weeks(self):
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        start = datetime(2026, 10, 12, tzinfo=tz)
        end = datetime(2026, 10, 19, tzinfo=tz)
        rows = stats.weekly(self.obs, self.cfg, NOW, start=start, end=end)
        self.assertEqual([r["week"].date().isoformat() for r in rows], ["2026-10-12"])
        self.assertEqual(rows[0]["accepted"], 12)

    def test_future_timestamps_ignored(self):
        obs = self.obs + [cm("z", "accepted", "2026-11-30T00:00:00Z")]
        self.assertEqual(stats.week_numbers(obs, self.cfg, NOW)["total"], 41)

    def test_cycle_and_wait(self):
        obs = [cm("a", "accepted", "2026-10-03T00:00:00Z", pool="2026-10-01T00:00:00Z"),
               cm("b", "accepted", "2026-10-05T00:00:00Z", pool="2026-10-01T00:00:00Z"),
               cm("c", "needs_revision", "2026-10-02T00:00:00Z", pool="2026-10-01T00:00:00Z"),
               cm("d", "accepted", "2026-10-02T00:00:00Z")]
        f = stats.cycle_and_wait(obs, NOW)
        self.assertEqual((f["latest_round_cycle_p50_h"], f["latest_round_cycle_coverage"]), (72.0, "2/3"))
        self.assertEqual(f["wait_coverage"], "3/4")
        self.assertFalse(f["first_submission_cycle"]["available"])
        empty = stats.cycle_and_wait([], NOW)
        self.assertIsNone(empty["latest_round_cycle_p50_h"])

    def test_ascii_chart_fallback(self):
        self.assertEqual(stats.bar(5, 10, 10, unicode=False), "#####")
        self.assertTrue(stats.bar(5, 10, 10, unicode=True).startswith("█████"))
        self.assertEqual(len(stats.spark([1, 2, 3], unicode=False)), 3)


class RankTest(unittest.TestCase):
    MD = '''| scope | win | acc | acc_rank |
| -----| -----| -----| ----- |
| "1 SWE multi-turn track" | "Q4 (from Oct 1)" | 27 | "2/209" |
| "6 Team: SWE multi-turn" | "W-5 2026-09-07" | 0 | *NULL* |
'''

    def test_rank_import_md_and_csv(self):
        rows = rank.parse_table(self.MD)
        self.assertEqual(rows[0]["scope"], "1 SWE multi-turn track")
        self.assertEqual(rows[0]["acc_rank"], "2/209")
        self.assertIsNone(rows[1]["acc_rank"])
        csv_rows = rank.parse_table("scope,win,acc\nSWE MT,Q4,27\n")
        self.assertEqual(csv_rows[0]["acc"], "27")

    def test_import_file_caches(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "r.md"
            f.write_text(self.MD)
            rank.import_file(f, Path(d))
            self.assertEqual(len(rank.load(Path(d))["rows"]), 2)

    def test_rank_query_denied_prints_manual_step(self):
        import subprocess
        cfg = load_config(Path("/nonexistent"))
        cfg.rank.daiquery_id = "123"

        def runner(argv, **kw):
            return subprocess.CompletedProcess(argv, 1, "", "AGENT_ROLE_ACCESS denied")

        with tempfile.TemporaryDirectory() as d:
            data, why = rank.refresh(cfg, Path(d), runner=runner)
        self.assertIsNone(data)
        self.assertIn("rank import", why)

    def test_bad_shapes_rejected(self):
        import subprocess
        cfg = load_config(Path("/nonexistent"))
        cfg.rank.daiquery_id = "1"
        for out in ("42", '{"rows": {}}', "[]", "[1, 2]"):
            with tempfile.TemporaryDirectory() as d:
                data, why = rank.refresh(cfg, Path(d), runner=lambda a, **k: subprocess.CompletedProcess(a, 0, out, ""))
                self.assertIsNone(data, out)
        with tempfile.TemporaryDirectory() as d:
            for bad in ('{"rows": []}', '{"rows": [1]}', "7"):
                (Path(d) / rank.CACHE).write_text(bad)
                self.assertIsNone(rank.load(Path(d)))

    def test_no_query_id(self):
        data, why = rank.refresh(load_config(Path("/nonexistent")), Path("/tmp"))
        self.assertIn("daiquery_id", why)


class WindowAndRankShapeTest(StatsTest):
    def test_from_only_and_to_only(self):
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        t = stats.range_totals(self.obs, NOW, start=datetime(2026, 10, 19, tzinfo=tz))
        self.assertEqual(t["accepted"], 10)
        t = stats.range_totals(self.obs, NOW, end=datetime(2026, 10, 12, tzinfo=tz))
        self.assertEqual(t["accepted"], 19)

    def test_exact_midnight_end_excluded(self):
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        midnight = datetime(2026, 10, 20, tzinfo=tz)
        obs = [cm("m", "accepted", midnight.astimezone(timezone.utc).isoformat())]
        self.assertEqual(stats.range_totals(obs, NOW, end=midnight)["accepted"], 0)
        self.assertEqual(stats.range_totals(obs, NOW, start=midnight)["accepted"], 1)

    def test_flow_respects_window(self):
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("America/Los_Angeles")
        obs = [cm("a", "accepted", "2026-10-03T00:00:00Z", pool="2026-10-01T00:00:00Z"),
               cm("b", "accepted", "2026-10-20T00:00:00Z", pool="2026-10-19T12:00:00Z")]
        f = stats.cycle_and_wait(obs, NOW, start=datetime(2026, 10, 15, tzinfo=tz))
        self.assertEqual((f["latest_round_cycle_coverage"], f["latest_round_cycle_p50_h"]), ("1/1", 12.0))

    def test_tasks_per_repo_unavailable(self):
        cfg = load_config(Path("/nonexistent"))
        r = stats.tasks_per_repo(cfg, ["a", "b"])
        self.assertEqual((r["available"], r["coverage"]), (False, "0/2"))
        self.assertTrue(r["reason"])

    def test_rank_normalized_from_wide_rows(self):
        rows = rank.normalize([{"scope": "SWE MT", "win": "Q4", "acc": "27", "acc_rank": "2/209", "sub": "39",
                                "sub_rank": "2/260"}])
        self.assertIn({"scope": "SWE MT", "window": "Q4", "metric": "accepted", "value": 27, "rank": 2, "of": 209}, rows)
        self.assertTrue(rank.valid_rows(rows))

    def test_rank_canonical_rows_validated(self):
        ok = rank.parse_table("scope,window,metric,value,rank,of\nOrg,H2,accepted,43,286,4999\n")
        self.assertEqual(rank.normalize(ok)[0]["value"], 43)               # CSV strings coerced
        for bad in ("scope,window,metric,value,rank,of\nOrg,H2,karma,1,1,2\n",       # unknown metric
                    "scope,window,metric,value,rank,of\nOrg,H2,accepted,1,5,\n",     # rank without of
                    "scope,window,metric,value,rank,of\n,H2,accepted,1,1,2\n"):      # empty scope
            with self.assertRaises(ValueError):
                rank.normalize(rank.parse_table(bad))

    def test_rank_canonical_and_bad_rows(self):
        canon = rank.parse_table("scope,window,metric,value,rank,of\nOrg,H2,accepted,43,286,4999\n")
        self.assertEqual(rank.normalize(canon)[0]["metric"], "accepted")
        with self.assertRaises(ValueError):
            rank.normalize([{"scope": "x"}])                    # no window
        with self.assertRaises(ValueError):
            rank.normalize([{"scope": "x", "win": "y", "other": 1}])   # no metrics
        self.assertFalse(rank.valid_rows([{"scope": "x", "window": "y"}]))


class StrictRankValuesTest(unittest.TestCase):
    def test_rejected_shapes(self):
        head = "scope,window,metric,value,rank,of\n"
        for body in ("Org,H2,accepted,1.5,1,2\n", "Org,H2,accepted,x,1,2\n", "  ,H2,accepted,1,1,2\n",
                     "Org,H2,accepted,0,5,2\n", "Org,H2,accepted,1,1,0\n"):
            with self.assertRaises(ValueError, msg=body):
                rank.normalize(rank.parse_table(head + body))
        for wide in ({"scope": "S", "win": "W", "acc": "1.5", "acc_rank": "1/2"},
                     {"scope": "S", "win": "W", "acc": "1", "acc_rank": "9/2"},
                     {"scope": "S", "win": "W", "acc": True, "acc_rank": "1/2"}):
            with self.assertRaises(ValueError, msg=str(wide)):
                rank.normalize([wide])

    def test_null_allowed(self):
        rows = rank.normalize([{"scope": "S", "win": "W", "acc": "0", "acc_rank": None}])
        self.assertEqual((rows[0]["value"], rows[0]["rank"], rows[0]["of"]), (0, None, None))


class RankLabelTest(unittest.TestCase):
    def test_labels_stripped(self):
        c = rank.normalize([{"scope": " Org ", "window": " H2 ", "metric": "accepted", "value": 1, "rank": 1, "of": 2}])
        w = rank.normalize([{"scope": " Org ", "win": " H2 ", "acc": "1", "acc_rank": "1/2"}])
        self.assertEqual((c[0]["scope"], c[0]["window"]), ("Org", "H2"))
        self.assertEqual((w[0]["scope"], w[0]["window"]), ("Org", "H2"))
        with self.assertRaises(ValueError):
            rank.normalize([{"scope": "Org", "window": "H2", "metric": "accepted", "value": "  x ", "rank": None, "of": None}])

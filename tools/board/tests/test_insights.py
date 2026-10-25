import unittest
from workboard import insights


class InsightsTest(unittest.TestCase):
    def test_only_problems_summarized(self):
        items = [{"name": "Structural checks", "status": "passed", "detail": "All 21/21 checks pass/warn"},
                 {"name": "Metacode or Opus pass/fail balance", "status": "failed",
                  "detail": 'Step gate failed — "2_aggregate_modifiers" too hard — no model passed it (avocado 0.8|0)'},
                 {"name": "Agentic trial-output review", "status": "warn",
                  "detail": 'Agentic full-task review: step "2_x" too easy per trials'}]
        v = insights.validation_summary(items)
        self.assertEqual((v["passed"], v["total"]), (1, 3))
        self.assertEqual(v["issues"][0], {"check": "calibration", "why": "step 2 too hard",
                                          "fix": "loosen step 2 or state the hidden rule", "severity": "fail"})
        self.assertEqual(v["issues"][1]["check"], "agentic review")
        self.assertNotIn("make step", v["issues"][1]["fix"])

    def test_infra_errors_are_not_task_defects(self):
        v = insights.validation_summary([{"name": "Oracle validation", "status": "failed",
                                          "detail": "No oracle trials produced a usable result (9 errored). This is an infrastructure error, not a task defect"}])
        self.assertEqual(v["issues"][0]["severity"], "warn")
        self.assertIn("rerun", v["issues"][0]["fix"])

    def test_next_steps_have_eta(self):
        t = {"next": "WAIT reviewer", "state_age_s": 10 * 3600, "vsum": {"issues": []}}
        steps = insights.next_steps(t, {"wait_p50_h": 40})
        self.assertEqual(steps[0]["eta"], "~30h")
        ok = {"state": "ok"}
        t = {"next": "GET R2", "vsum": {"issues": []},
             "gates": {"author": {"check": ok, "review": ok}, "independent": {"check": {"state": "none"}, "review": {"state": "none"}}}}
        do = [s["do"] for s in insights.next_steps(t, {})]
        self.assertFalse(any("building session" in x for x in do))       # builder already ran presubmit + approved
        self.assertTrue(any("independent agent" in x for x in do))

    def test_findings_from_presubmit_and_review_lead_the_plan(self):
        none = {"check": {"state": "none"}, "review": {"state": "none"}}
        ind = {"check": {"state": "bad", "fail": 2, "summary": "§5d: add no-injection test", "session": "x"},
               "review": {"state": "bad", "note": "README stale", "session": "x"}}
        t = {"next": "ADDRESS agent review", "task": "t", "vsum": {"issues": []}, "status_raw": "draft",
             "gates": {"author": none, "independent": ind}}
        do = [s["do"] for s in insights.next_steps(t, {})]
        self.assertIn("§5d: add no-injection test", do[0])
        self.assertFalse(any("README stale" in x for x in do))          # same session's presubmit already covers it
        other = dict(t, gates={"author": none, "independent": dict(ind, review=dict(ind["review"], session="y"))})
        self.assertTrue(any("README stale" in x for x in [s["do"] for s in insights.next_steps(other, {})]))
        val = dict(t, next="FIX validation", vsum={"issues": [{"check": "oracle", "why": "x", "fix": "y", "severity": "fail"}]})
        self.assertIn("§5d", insights.next_steps(val, {})[0]["do"])      # findings show while validation is also red

    def test_not_run_detail_is_info(self):
        vs = insights.validation_summary([{"name": "embedding dedup", "status": "passed",
                                           "detail": "engine stopped waiting after 175m; the check has not run"}])
        self.assertEqual(vs["issues"], [])
        self.assertEqual(len(vs["info"]), 1)

    def test_wait_reviewer_wording(self):
        s = insights.next_steps({"next": "WAIT reviewer", "status_raw": "being_reviewed", "vsum": {"issues": []}}, {})
        self.assertIn("in progress", s[0]["do"])


class TagsAndVersionsTest(unittest.TestCase):
    def test_vp(self):
        from workboard.html import _vp
        o = {"git.commit_times": ["2026-10-18T00:00:00+00:00", "2026-10-20T00:00:00+00:00", "2026-10-22T00:00:00+00:00"]}
        self.assertEqual(_vp(o, []), "0.3")
        decs = [{"kind": "revision", "at": "2026-10-19T00:00:00+00:00"}, {"kind": "revision", "at": "2026-10-21T00:00:00+00:00"}]
        self.assertEqual(_vp(o, decs), "2.1")
        self.assertEqual(_vp(dict(o, **{"codimango.status": "needs_revision", "codimango.reviewed_at": "2026-10-21T00:00:00Z"}), []), "1.1")

    def test_tags(self):
        from workboard.html import task_tags
        t = {"workers": ["claude", "codex"], "kind": "multi-turn", "next": "SUBMIT", "vp": "2.1", "infra_only": False,
             "gates": {"independent": {"review": {"note": "§5d: retire this, dedup vs own task"}, "check": {}}}}
        labels = [x["label"] for x in task_tags(t)]
        self.assertEqual(labels, ["Claude", "Codex", "MT", "ready", "retire?", "2 rounds"])

    def test_routine_steps_greyed_and_last(self):
        steps = insights.rank_steps([{"do": "resubmit for human review"}, {"do": "fix the README"}])
        self.assertEqual([s["do"] for s in steps], ["fix the README", "resubmit for human review"])
        self.assertTrue(steps[1]["routine"])

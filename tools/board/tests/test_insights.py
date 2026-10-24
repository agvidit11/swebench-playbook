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

    def test_next_steps_have_eta(self):
        t = {"next": "WAIT reviewer", "state_age_s": 10 * 3600, "vsum": {"issues": []}}
        steps = insights.next_steps(t, {"wait_p50_h": 40})
        self.assertEqual(steps[0]["eta"], "~30h")
        t = {"next": "GET R2", "review": "R1", "vsum": {"issues": []}}
        self.assertTrue(any("1 agent-session review" in s["do"] for s in insights.next_steps(t, {})))

    def test_assignee(self):
        self.assertTrue(insights.assignee({"claim_health": "OWNED", "owner": "h1·x", "task": "t"}, {}).startswith("keep with"))
        self.assertIn("h2", insights.assignee({"claim_health": "FREE", "group": "ATTENTION", "task": "t"}, {"h1": 3, "h2": 1}))

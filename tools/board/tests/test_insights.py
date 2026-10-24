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
        t = {"next": "GET R2", "review": "R1", "vsum": {"issues": []}}
        self.assertTrue(any("1 agent-session review" in s["do"] for s in insights.next_steps(t, {})))

    def test_assignee(self):
        self.assertTrue(insights.assignee({"claim_health": "OWNED", "owner": "h1·x", "task": "t"}, {}).startswith("keep with"))
        self.assertIn("h2", insights.assignee({"claim_health": "FREE", "group": "ATTENTION", "task": "t"}, {"h1": 3, "h2": 1}))


class InfraStepTest(unittest.TestCase):
    def test_infra_failure_gives_rerun_step(self):
        vs = insights.validation_summary([{"name": "Oracle validation", "status": "failed",
                                           "detail": "No oracle trials produced a usable result (9 errored). infrastructure error, not a task defect"}])
        steps = insights.next_steps({"next": "FIX validation", "vsum": vs}, {})
        self.assertTrue(any("rerun" in s["do"] for s in steps))
        self.assertFalse(any(s["do"].startswith("push") for s in steps))


class AuditValidationTest(unittest.TestCase):
    def test_semantics(self):
        items = [
            {"name": "Metacode or Opus pass/fail balance", "status": "failed", "detail": '"2_x" too hard — no model passed it'},
            {"name": "Agentic trial-output review", "status": "pending", "detail": "Not run because Solvability & difficulty failed"},
            {"name": "Provenance check", "status": "warn", "detail": "Provenance CLEAN (not third-party authorship)"},
            {"name": "TBR", "status": "warn", "detail": "Canonical Codimango TBR review pass"},
            {"name": "Provenance check", "status": "passed", "detail": "Verdict: SUSPECT — review recommended"},
            {"name": "VALIDATION_ENGINE::test_patch_validation", "status": "error",
             "detail": "finished without a usable result — click Revalidate"},
        ]
        v = insights.validation_summary(items, tbr_status="fail")
        checks = [(i["check"], i["severity"]) for i in v["issues"]]
        self.assertIn(("calibration", "fail"), checks)
        self.assertIn(("provenance", "warn"), checks)               # the SUSPECT one, not the CLEAN one
        self.assertEqual(sum(1 for c, _ in checks if c == "provenance"), 1)
        self.assertIn(("test-patch", "warn"), checks)              # infra, not a task failure
        self.assertIn(("TBR", "warn"), checks)                     # from tbr_status=fail
        self.assertEqual(v["skipped"], ["agentic review"])
        self.assertFalse(any("third-party" in i["why"] for i in v["issues"]))

    def test_waiting_tasks_need_nobody_and_dead_hosts_skipped(self):
        self.assertEqual(insights.assignee({"group": "REVIEWING", "claim_health": "LEGACY", "owner": "x", "task": "t"}, {}),
                         "nobody needed right now")
        a = insights.assignee({"group": "ATTENTION", "claim_health": "FREE", "task": "t"}, {"a": 0, "b": 3}, live_hosts={"b"})
        self.assertIn("on b", a)

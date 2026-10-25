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

    def test_steps_exclusive_and_warnings_first(self):
        # agent dissent on a draft: one address step, no human-review step, ends with submit (not resubmit)
        s = [x["do"] for x in insights.next_steps({"next": "ADDRESS agent review", "status_raw": "draft",
                                                   "review": "R0", "vsum": {"issues": []}}, {})]
        self.assertEqual(sum("address" in x for x in s), 1)
        self.assertEqual(s[-1], "submit for human review")
        # infra-only rerun: one rerun, one wait
        vs = insights.validation_summary([{"name": "oracle", "status": "error",
                                           "detail": "infrastructure error, not a task defect"}])
        s = [x["do"] for x in insights.next_steps({"next": "RERUN validation", "task": "t", "vsum": vs}, {})]
        self.assertEqual(sum("codimango task rerun" in x for x in s), 1)
        self.assertEqual(sum(x.startswith("wait") for x in s), 1)
        # action-required warning comes before the submit ladder
        vs = insights.validation_summary([{"name": "balance", "status": "passed",
                                           "detail": "passed, WITH REVIEWER ACTION REQUIRED"}], "fail")
        s = [x["do"] for x in insights.next_steps({"next": "RUN check", "task": "t", "review": "R0", "vsum": vs}, {})]
        self.assertTrue(s[0].startswith("calibration") or "reviewer action" in s[0])
        self.assertTrue(any("TBR" in x for x in s[:2]))
        self.assertEqual(s[-1], "submit for human review")

    def test_not_run_detail_is_info(self):
        vs = insights.validation_summary([{"name": "embedding dedup", "status": "passed",
                                           "detail": "engine stopped waiting after 175m; the check has not run"}])
        self.assertEqual(vs["issues"], [])
        self.assertEqual(len(vs["info"]), 1)

    def test_wait_reviewer_wording(self):
        s = insights.next_steps({"next": "WAIT reviewer", "status_raw": "being_reviewed", "vsum": {"issues": []}}, {})
        self.assertIn("in progress", s[0]["do"])

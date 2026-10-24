import unittest
from workboard.model import Finding, TaskView


class ModelTest(unittest.TestCase):
    def test_finding_requires_next_action(self):
        with self.assertRaises(TypeError):
            Finding("X", "warn", "summary")
        self.assertEqual(Finding("X", "warn", "s", "do y").next_action, "do y")

    def test_finding_bad_severity(self):
        with self.assertRaises(ValueError):
            Finding("X", "fatal", "s", "do y")

    def test_taskview_defaults_isolated(self):
        a, b = TaskView("a"), TaskView("b")
        a.fields["x"] = 1
        a.health["codimango"] = None
        self.assertEqual(b.fields, {})
        self.assertEqual(b.health, {})

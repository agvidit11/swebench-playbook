import unittest
from datetime import datetime, timezone
from workboard import legacy

MD = """| machine | task-or-card | repo | seam | lane | status | updated | note |
|---|---|---|---|---|---|---|---|
| devvm1 | alpha-task | org/a | x | B | RELEASED | 2026-10-20 | done |
| devvm2 | alpha-task | org/a | x | B | ACTIVE | 2026-10-22 | building step 2 |
| devvm1 | beta-task | org/b | y | B | BUILDING | 2026-10-01 | old |
| devvm1 | gamma-task | org/c | z | B | PARKED | 2026-10-22 | parked |
| devvm2 | card-xyz | org/d | z | A | CLAIMED | 2026-10-22 | not a task |
"""
NOW = datetime(2026, 10, 23, tzinfo=timezone.utc)


class LegacyTest(unittest.TestCase):
    def test_claims_md_import_live_rows_only(self):
        rows = legacy.parse_claims_md(MD)
        live = legacy.live_rows(rows, {"alpha-task", "beta-task", "gamma-task"}, NOW)
        self.assertEqual([(r["task"], r["machine"], r["status"]) for r in live], [("alpha-task", "devvm2", "ACTIVE")])

import unittest
from datetime import datetime, timezone
from workboard import legacy

MD = """| machine | task-or-card | repo | seam | lane | status | updated | note |
|---|---|---|---|---|---|---|---|
| host-1 | alpha-task | org/a | x | B | RELEASED | 2026-10-20 | done |
| host-2 | alpha-task | org/a | x | B | ACTIVE | 2026-10-22 | building step 2 |
| host-1 | beta-task | org/b | y | B | BUILDING | 2026-10-01 | old |
| host-1 | gamma-task | org/c | z | B | PARKED | 2026-10-22 | parked |
| host-2 | card-xyz | org/d | z | A | CLAIMED | 2026-10-22 | not a task |
"""
NOW = datetime(2026, 10, 23, tzinfo=timezone.utc)


class LegacyTest(unittest.TestCase):
    def test_claims_md_import_live_rows_only(self):
        rows = legacy.parse_claims_md(MD)
        live = legacy.live_rows(rows, {"alpha-task", "beta-task", "gamma-task"}, NOW)
        self.assertEqual([(r["task"], r["machine"], r["status"]) for r in live], [("alpha-task", "host-2", "ACTIVE")])


class TolerantLedgerTest(unittest.TestCase):
    KNOWN = {"trickster-authoritative-refresh-reconciliation", "mst-patch-log-atomic-json-interop", "abjad-score-edit"}
    MD = """| machine | task-or-card | repo | seam | lane | status | updated | note |
|---|---|---|---|---|---|---|---|
| host-b | trickster-authoritative-refresh-reconciliation (MT3) | org/t | s | B | ACTIVE-REVISION | 2026-10-23 | fixing |
| host-b | mst-patch-log-atomic-json-interop-review-audit | org/m | s | B | FIXING | 2026-10-22 | a | b | c |
| host-a | abjad-score-edit (MT3, slug tentative) | org/a | s | B | ACTIVE | 2026-10-20 | x |
| host-a | abjad-score-edit (MT3) | org/a | s | B | PARKED-TOO-EASY | 2026-10-23 | done |
| host-b | weird | row | with | pipe | in | seam | CLAIMED | 2026-10-23 | y |
"""

    def test_suffixes_pipes_and_vocabulary(self):
        rows = legacy.parse_claims_md(self.MD)
        latest = legacy.latest_rows(rows, self.KNOWN)
        self.assertEqual(latest["trickster-authoritative-refresh-reconciliation"]["status"], "ACTIVE-REVISION")
        self.assertEqual(latest["mst-patch-log-atomic-json-interop"]["status"], "FIXING")
        self.assertEqual(latest["abjad-score-edit"]["status"], "PARKED-TOO-EASY")
        now = datetime(2026, 10, 24, tzinfo=timezone.utc)
        live = {r["task"] for r in legacy.live_rows(rows, self.KNOWN, now)}
        self.assertEqual(live, {"trickster-authoritative-refresh-reconciliation", "mst-patch-log-atomic-json-interop"})
        weird = [r for r in rows if r["task"] == "weird"][0]
        self.assertEqual((weird["status"], weird["updated"]), ("CLAIMED", "2026-10-23"))


class ClaimsMdSyncTest(unittest.TestCase):
    def test_changes_only_and_dead_row_clears(self):
        import json, tempfile
        from pathlib import Path
        from workboard import claims_md_sync, events
        with tempfile.TemporaryDirectory() as d:
            st = Path(d)
            known = {"alpha-task-name"}
            now = datetime(2026, 10, 24, tzinfo=timezone.utc)
            live = "| m | t | r | s | l | st | updated | n |\n| host-b | alpha-task-name | r | s | B | FIXING | 2026-10-23 | x |\n"
            self.assertEqual(claims_md_sync.sync(None, st, "h1", known, now=now, text=live), 1)
            self.assertEqual(claims_md_sync.sync(None, st, "h1", known, now=now, text=live), 0)      # unchanged
            dead = live.replace("FIXING", "RELEASED")
            self.assertEqual(claims_md_sync.sync(None, st, "h1", known, now=now, text=dead), 1)
            evs = [json.loads(l) for l in (st / events.SPOOL_NAME).read_text().splitlines()]
            self.assertEqual([e["payload"]["live"] for e in evs], [True, False])

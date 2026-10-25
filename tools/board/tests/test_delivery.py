import unittest
from datetime import datetime, timezone

from workboard import comms, events
from workboard.model import TaskView


A = {"session_id": "sender", "alias": "h1·sender", "kind": "claude"}
COURIER = {"session_id": "courier", "alias": "h1·courier", "kind": "claude"}
SESSION = {"session_key": "claude:h1:1:d:target", "native_id": "target", "host": "h1", "kind": "claude",
           "name": "Target", "transport": {"available": True}}


def stamp(e, seq):
    e["occurred_at"] = datetime(2026, 10, 25, 20, 0, seq % 60, tzinfo=timezone.utc).isoformat()
    return events.stamp(e, "h1", seq)


class RoutingTest(unittest.TestCase):
    def test_compose_by_task_pins_owner(self):
        view = TaskView("alpha", {"owner_session": "target", "owner": "h1·Target",
                                   "activity": {"session_keys": []}})
        target = comms.target_for("alpha", {}, ["h1"], views=[view], sessions=[SESSION])
        self.assertEqual(target["to"], f"session:{SESSION['session_key']}")
        ev = comms.new_message("do it", target, A)
        self.assertEqual(ev["entity"]["id"], "alpha")
        self.assertEqual(ev["payload"]["resolved_recipients"][0]["native_id"], "target")

    def test_unowned_task_is_honest(self):
        view = TaskView("alpha", {"owner_session": None, "owner": "", "activity": {"session_keys": []}})
        with self.assertRaisesRegex(ValueError, "no resolved owner"):
            comms.target_for_task("alpha", [view], [SESSION])


class ReceiptStateMachineTest(unittest.TestCase):
    def message(self):
        target = {"to": f"session:{SESSION['session_key']}", "to_label": "Target",
                  "resolved_recipients": [{k: SESSION[k] for k in ("session_key", "native_id", "host", "name")}]}
        return stamp(comms.new_message("synthetic body", target, A), 1)

    def test_receipts_are_monotonic_and_duplicate_safe(self):
        msg = self.message()
        delivered = stamp(comms.receipt_event(msg["event_id"], SESSION["session_key"], "delivered", COURIER), 2)
        duplicate = stamp(comms.receipt_event(msg["event_id"], SESSION["session_key"], "delivered", COURIER), 3)
        late_failure = stamp(comms.receipt_event(msg["event_id"], SESSION["session_key"], "failed", COURIER), 4)
        row = comms.messages([msg, delivered, duplicate, late_failure])[0]
        self.assertEqual(row["delivery"]["state"], "delivered")
        self.assertEqual(len(row["delivery"]["recipients"]), 1)
        ack = stamp(comms.ack_event(msg["event_id"], {"session_id": "target", "alias": "h1·Target", "kind": "claude"}), 5)
        self.assertEqual(comms.messages([msg, delivered, ack])[0]["delivery"]["state"], "acked")

    def test_courier_wait_is_replay_safe(self):
        msg = self.message()
        self.assertEqual(len(comms.courier_jobs([msg], [SESSION], "h1")), 1)
        rec = stamp(comms.receipt_event(msg["event_id"], SESSION["session_key"], "delivered", COURIER), 2)
        self.assertEqual(comms.courier_jobs([msg, rec, rec], [SESSION], "h1"), [])


if __name__ == "__main__":
    unittest.main()

import json, multiprocessing, tempfile, unittest
from pathlib import Path
from workboard import events

ACTOR = {"session_id": "s1", "alias": "h·tab", "kind": "claude", "host_id": "h"}


def _writer(spool, n, tag):
    for i in range(n):
        ev = events.new_event("touch", f"task-{tag}", {"i": i, "pad": "x" * 300}, actor=ACTOR, commit=None, source="test")
        events.spool_append(Path(spool), ev)


class EventsTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_new_event_schema(self):
        ev = events.new_event("claim", "t1", {}, actor=ACTOR, commit="a" * 40, source="cli")
        for k in ("schema_version", "event_id", "occurred_at", "actor", "entity", "type", "commit", "source", "payload"):
            self.assertIn(k, ev)
        self.assertEqual(ev["schema_version"], 1)
        self.assertEqual(ev["entity"], {"kind": "task", "id": "t1"})

    def test_append_concurrent_writers_no_interleave(self):
        procs = [multiprocessing.Process(target=_writer, args=(str(self.dir), 200, t)) for t in range(8)]
        [p.start() for p in procs]
        [p.join() for p in procs]
        lines = (self.dir / events.SPOOL_NAME).read_text().splitlines()
        self.assertEqual(len(lines), 1600)
        for line in lines:
            json.loads(line)  # every line intact

    def test_truncated_last_line_quarantined(self):
        f = self.dir / "h.jsonl"
        good = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        good["host_id"], good["seq"] = "h", 1
        f.write_text(json.dumps(good) + "\n" + '{"schema_version": 1, "event_id": "abc", "ty')
        evs, findings = events.read_events([f])
        self.assertEqual(len(evs), 1)
        self.assertEqual(findings[0].code, "MALFORMED_EVENTS")

    def test_duplicate_event_id_deduped(self):
        f = self.dir / "h.jsonl"
        ev = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        ev["host_id"], ev["seq"] = "h", 1
        f.write_text((json.dumps(ev) + "\n") * 3)
        evs, findings = events.read_events([f])
        self.assertEqual(len(evs), 1)
        self.assertEqual(findings, [])

    def test_oversize_line_rejected(self):
        ev = events.new_event("note", "t1", {"x": "y" * 40000}, actor=ACTOR, commit=None, source="t")
        self.assertFalse(events.spool_append(self.dir, ev))
        self.assertFalse((self.dir / events.SPOOL_NAME).exists())

    def test_append_never_raises_on_bad_dir(self):
        ev = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        self.assertFalse(events.spool_append(Path("/proc/definitely/not/writable"), ev))

    def test_order_by_host_then_seq(self):
        a, b = self.dir / "a.jsonl", self.dir / "b.jsonl"
        rows = []
        for host, path in (("a", a), ("b", b)):
            lines = []
            for seq in (3, 1, 2):
                ev = events.new_event("touch", "t", {}, actor=ACTOR, commit=None, source="t")
                ev["host_id"], ev["seq"] = host, seq
                lines.append(json.dumps(ev))
            path.write_text("\n".join(lines) + "\n")
        evs, _ = events.read_events([a, b])
        self.assertEqual([(e["host_id"], e["seq"]) for e in evs], [("a", 1), ("a", 2), ("a", 3), ("b", 1), ("b", 2), ("b", 3)])

    def test_latest_alias_wins_history_kept(self):
        f = self.dir / "h.jsonl"
        lines = []
        for seq, title in ((1, "old title"), (2, "new title")):
            ev = events.new_event("alias", None, {"alias": f"h·{title}"}, actor=ACTOR, commit=None, source="hook")
            ev["host_id"], ev["seq"] = "h", seq
            lines.append(json.dumps(ev))
        f.write_text("\n".join(lines) + "\n")
        evs, _ = events.read_events([f])
        self.assertEqual(len([e for e in evs if e["type"] == "alias"]), 2)
        self.assertEqual(events.latest_aliases(evs)["s1"], "h·new title")

import json, multiprocessing, os, tempfile, unittest, uuid
from datetime import datetime
from pathlib import Path
from workboard import events

ACTOR = {"session_id": "s1", "alias": "h·tab", "kind": "claude"}


def ev(type="touch", entity="t1", payload=None, host="h", seq=1, **over):
    e = events.stamp(events.new_event(type, entity, payload or {}, actor=ACTOR, commit=None, source="test"), host, seq)
    e.update(over)
    return e


def write_lines(path, rows):
    path.write_text("".join((r if isinstance(r, str) else json.dumps(r)) + "\n" for r in rows))


def _writer(spool, n, tag):
    for i in range(n):
        e = events.new_event("touch", f"task-{tag}", {"i": i, "pad": "x" * 300}, actor=ACTOR, commit=None, source="t")
        if not events.spool_append(Path(spool), e):
            raise SystemExit(3)


class EventsTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.dir = Path(td.name)

    def test_new_event_schema(self):
        e = events.new_event("claim", "t1", {}, actor=ACTOR, commit="a" * 40, source="cli")
        self.assertEqual(e["schema_version"], 1)
        self.assertEqual(uuid.UUID(e["event_id"]).version, 4)
        self.assertIsNotNone(datetime.fromisoformat(e["occurred_at"]).tzinfo)
        self.assertEqual(e["entity"], {"kind": "task", "id": "t1"})

    def test_stamped_event_validates(self):
        self.assertIsNone(events.validate_committed(ev()))

    def test_append_concurrent_writers_no_interleave(self):
        procs = [multiprocessing.Process(target=_writer, args=(str(self.dir), 200, t)) for t in range(8)]
        [p.start() for p in procs]
        [p.join() for p in procs]
        self.assertEqual([p.exitcode for p in procs], [0] * 8)
        lines = (self.dir / events.SPOOL_NAME).read_text().splitlines()
        self.assertEqual(len(lines), 1600)
        for line in lines:
            json.loads(line)

    def test_queue_limit_counts_events(self):
        e = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        self.assertTrue(events.spool_append(self.dir, e, max_queue=1))
        self.assertFalse(events.spool_append(self.dir, e, max_queue=1))

    def test_short_write_never_reported_success(self):
        calls = {"n": 0}

        def flaky(fd, view):
            calls["n"] += 1
            if calls["n"] == 1:
                return os.write(fd, bytes(view[:10]))   # partial
            raise OSError(5, "disk gone")

        e = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        self.assertFalse(events.spool_append(self.dir, e, _write=flaky))
        self.assertEqual((self.dir / events.SPOOL_NAME).read_bytes(), b"")   # partial line rolled back

    def test_short_writes_completed_by_loop(self):
        def tiny(fd, view):
            return os.write(fd, bytes(view[:7]))

        e = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        self.assertTrue(events.spool_append(self.dir, e, _write=tiny))
        json.loads((self.dir / events.SPOOL_NAME).read_text())

    def test_truncated_last_line_quarantined(self):
        f = self.dir / "h.jsonl"
        write_lines(f, [ev(), '{"schema_version": 1, "event_id": "abc", "ty'])
        evs, findings = events.read_events([f])
        self.assertEqual(len(evs), 1)
        self.assertEqual(findings[0].code, "MALFORMED_EVENTS")

    def test_bad_fields_skip_only_that_line(self):
        f = self.dir / "h.jsonl"
        bad_seq = ev(seq=2); bad_seq["seq"] = "bad"
        no_ts = ev(seq=3); del no_ts["recorded_at"]
        bad_payload = ev(seq=4, payload=None); bad_payload["payload"] = "x"
        write_lines(f, [ev(seq=1), bad_seq, no_ts, bad_payload, ev(seq=5)])
        evs, findings = events.read_events([f])
        self.assertEqual([e["seq"] for e in evs], [1, 5])
        self.assertIn("3 ledger line(s)", findings[0].summary)

    def test_empty_actor_rejected(self):
        f = self.dir / "h.jsonl"
        bad = ev(seq=2); bad["actor"] = {}
        write_lines(f, [ev(seq=1), bad, ev(seq=3)])
        evs, findings = events.read_events([f])
        self.assertEqual([e["seq"] for e in evs], [1, 3])
        self.assertIn("bad actor", findings[0].summary)

    def test_line_exactly_over_limit_with_newline_is_oversize(self):
        f = self.dir / "h.jsonl"
        pad = "y" * (events.MAX_LINE - 10)
        big = json.dumps({"x": pad})          # > MAX_LINE once newline is added? make sure
        while len(big.encode()) + 1 != events.MAX_LINE + 1:
            pad = pad[:-1] if len(big.encode()) + 1 > events.MAX_LINE + 1 else pad + "y"
            big = json.dumps({"x": pad})
        write_lines(f, [ev(seq=1), big, ev(seq=3)])
        evs, findings = events.read_events([f])
        self.assertEqual([e["seq"] for e in evs], [1, 3])
        self.assertIn("oversize", findings[0].summary)

    def test_duplicate_event_id_deduped(self):
        f = self.dir / "h.jsonl"
        e = ev()
        write_lines(f, [e, e, e])
        evs, findings = events.read_events([f])
        self.assertEqual(len(evs), 1)
        self.assertEqual(findings, [])

    def test_oversize_spool_line_rejected(self):
        e = events.new_event("note", "t1", {"x": "y" * 40000}, actor=ACTOR, commit=None, source="t")
        self.assertFalse(events.spool_append(self.dir, e))
        self.assertFalse((self.dir / events.SPOOL_NAME).exists())

    def test_oversize_ledger_line_skipped_neighbours_kept(self):
        f = self.dir / "h.jsonl"
        write_lines(f, [ev(seq=1), "{" + '"x":"' + "y" * 100000 + '"}', ev(seq=3)])
        evs, findings = events.read_events([f])
        self.assertEqual([e["seq"] for e in evs], [1, 3])
        self.assertEqual(len(findings), 1)
        self.assertIn("oversize", findings[0].summary)

    def test_append_never_raises_on_bad_dir(self):
        e = events.new_event("touch", "t1", {}, actor=ACTOR, commit=None, source="t")
        self.assertFalse(events.spool_append(Path("/proc/definitely/not/writable"), e))

    def test_order_by_host_then_seq(self):
        a, b = self.dir / "a.jsonl", self.dir / "b.jsonl"
        write_lines(a, [ev(host="a", seq=s) for s in (3, 1, 2)])
        write_lines(b, [ev(host="b", seq=s) for s in (3, 1, 2)])
        evs, _ = events.read_events([a, b])
        self.assertEqual([(e["host_id"], e["seq"]) for e in evs],
                         [("a", 1), ("a", 2), ("a", 3), ("b", 1), ("b", 2), ("b", 3)])

    def test_latest_alias_wins_history_kept(self):
        f = self.dir / "h.jsonl"
        write_lines(f, [ev("alias", None, {"alias": "h·old title"}, seq=1), ev("alias", None, {"alias": "h·new title"}, seq=2),
                        ev("alias", None, {"alias": 7}, seq=3)])
        evs, _ = events.read_events([f])
        self.assertEqual(len([e for e in evs if e["type"] == "alias"]), 3)
        self.assertEqual(events.latest_aliases(evs)["s1"], "h·new title")

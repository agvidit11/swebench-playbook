import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from workboard import events, presence
from workboard.config import load_config
from workboard.model import Observation
from workboard.projection import project


def tool_line(cmd=None, path=None, cwd="/home/u"):
    inp = {"command": cmd} if cmd else {"file_path": path}
    return json.dumps({"cwd": cwd, "message": {"content": [{"type": "tool_use", "name": "Bash", "input": inp}]}})


class PresenceTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        (self.root / "claude" / "proj").mkdir(parents=True)
        (self.root / "codex" / "2026" / "10" / "24").mkdir(parents=True)
        for attr, sub in (("CLAUDE", "claude"), ("CODEX", "codex")):
            p = mock.patch.object(presence, attr, self.root / sub)
            p.start()
            self.addCleanup(p.stop)
        self.tasks = {"alpha-task-one", "beta-task-two", "gamma-task-three"}

    def transcript(self, name, lines, age_s=60):
        p = self.root / "claude" / "proj" / f"{name}.jsonl"
        p.write_text("\n".join([json.dumps({"type": "ai-title", "aiTitle": "Lane loop"})] + lines) + "\n")
        t = time.time() - age_s
        os.utime(p, (t, t))

    def test_path_touch_counts_plain_mention_does_not(self):
        self.transcript("s1", [tool_line(path="/home/u/repo/alpha-task-one/tests/test.sh"),
                               json.dumps({"message": {"content": [{"type": "text", "text": "beta-task-two is ready"}]}})])
        found = presence.scan(self.tasks)
        self.assertEqual({f["task"] for f in found}, {"alpha-task-one"})
        self.assertEqual(found[0]["title"], "Lane loop")

    def test_codex_dash_c_and_cwd(self):
        self.transcript("s2", [tool_line(cmd="codex exec -s workspace-write -C gamma-task-three 'fix'"),
                               tool_line(cmd="ls", cwd="/home/u/repo/beta-task-two")])
        self.assertEqual({f["task"] for f in presence.scan(self.tasks)}, {"gamma-task-three", "beta-task-two"})
        cx = self.root / "codex" / "2026" / "10" / "24" / "rollout-abc.jsonl"
        cx.write_text(json.dumps({"type": "session_meta", "payload": {"cwd": "/home/u/repo/alpha-task-one"}}) + "\n")
        self.assertIn(("alpha-task-one", "codex"), {(f["task"], f["kind"]) for f in presence.scan(self.tasks)})

    def test_scratch_dir_containing_task_name(self):
        self.transcript("s3", [tool_line(cmd="cd /tmp/rev-gamma-task-three && git status")])
        self.assertIn("gamma-task-three", {f["task"] for f in presence.scan(self.tasks)})

    def test_old_transcripts_ignored(self):
        self.transcript("old", [tool_line(path="/r/alpha-task-one/x")], age_s=7 * 3600 * 2)
        self.assertEqual(presence.scan(self.tasks), [])

    def test_emit_rate_limited(self):
        self.transcript("s1", [tool_line(path="/r/alpha-task-one/x")])
        st = self.root / "state"
        self.assertEqual(presence.emit(None, st, "h1", self.tasks), 1)
        self.assertEqual(presence.emit(None, st, "h1", self.tasks), 0)
        ev = json.loads((st / events.SPOOL_NAME).read_text().splitlines()[0])
        self.assertEqual((ev["type"], ev["entity"]["id"], ev["actor"]["alias"]), ("presence", "alpha-task-one", "h1·Lane loop"))

    def test_projection_active_not_free(self):
        cfg = load_config(Path("/nonexistent"))
        now = datetime.now(timezone.utc)
        ev = events.stamp(events.new_event("presence", "t", {"last_seen": now.timestamp() - 600},
                                           actor={"session_id": "s1", "alias": "h1·Lane loop", "kind": "claude"},
                                           commit=None, source="presence"), "h1", 1)
        obs = [Observation("codimango", "t", now, {"codimango.status": "draft", "codimango.validation_status": "passing"})]
        v = project(obs, [ev], cfg, now)[0]
        self.assertEqual((v.fields["claim_health"], v.fields["owner"]), ("ACTIVE", "h1·Lane loop"))
        old = dict(ev, payload={"last_seen": now.timestamp() - 3 * 3600})
        self.assertEqual(project(obs, [old], cfg, now)[0].fields["claim_health"], "FREE")

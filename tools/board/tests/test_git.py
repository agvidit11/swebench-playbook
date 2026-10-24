import tempfile, unittest
from pathlib import Path
from workboard.config import Repository
from workboard.sources.gitsrc import GitSource
from tests.helpers import bare_remote, git
from workboard.config import load_config


class GitSourceTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.tmp = Path(td.name)
        self.remote = bare_remote(self.tmp, "tasks.git")
        work = self.tmp / "work"
        git(self.tmp, "clone", "-q", str(self.remote), str(work))
        git(work, "config", "user.email", "t@example.com"); git(work, "config", "user.name", "t")
        for i, task in enumerate(["alpha-task", "alpha-task", "beta-task"]):
            d = work / task; d.mkdir(exist_ok=True)
            (d / f"f{i}").write_text(str(i))
            git(work, "add", "."); git(work, "commit", "-q", "-m", f"c{i}")
        git(work, "push", "-q", "origin", "main")
        self.local = self.tmp / "local"
        git(self.tmp, "clone", "-q", str(self.remote), str(self.local))
        self.cfg = load_config(Path("/nonexistent"))
        self.cfg.repositories = [Repository(id="tasks", path=str(self.local), remote_url=str(self.remote), branch="main")]

    def test_task_heads_and_commit_times(self):
        res = GitSource(self.cfg).fetch()
        self.assertTrue(res.health.ok, res.health.detail)
        obs = {o.entity_id: o for o in res.observations}
        self.assertEqual(len(obs["alpha-task"].fields["git.commit_times"]), 2)
        self.assertEqual(len(obs["alpha-task"].fields["git.task_head"]), 40)
        self.assertNotIn("README", obs)                     # top-level files are not tasks

    def test_fetch_failure_uses_local_and_flags(self):
        self.cfg.repositories[0].remote_url = str(self.tmp / "missing.git")
        res = GitSource(self.cfg).fetch()
        self.assertFalse(res.health.ok)
        self.assertIn("SYNC_FAILED", [f.code for f in res.findings])
        self.assertIn("alpha-task", {o.entity_id for o in res.observations})

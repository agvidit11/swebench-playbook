import tempfile, unittest
from pathlib import Path
from workboard.config import load_config


def write(text):
    d = tempfile.mkdtemp()
    p = Path(d) / "config.toml"
    p.write_text(text)
    return p


class ConfigTest(unittest.TestCase):
    def test_defaults_when_missing(self):
        cfg = load_config(Path("/nonexistent/workboard.toml"))
        self.assertEqual(cfg.config_version, 1)
        self.assertTrue(any("not found" in w for w in cfg.warnings))

    def test_timezone_default_pt(self):
        cfg = load_config(Path("/nonexistent/workboard.toml"))
        self.assertEqual(cfg.user.timezone, "America/Los_Angeles")
        self.assertEqual(cfg.user.week_start, "monday")

    def test_unknown_key_warns(self):
        cfg = load_config(write('config_version = 1\nbogus = 3\n[ui]\ncolour = "x"\n'))
        self.assertIn("unknown key: bogus", cfg.warnings)
        self.assertIn("unknown key: ui.colour", cfg.warnings)

    def test_values_loaded(self):
        cfg = load_config(write(
            'config_version = 1\n[user]\nid = "me"\n[[servers]]\nid = "a"\nhost_alias = "h1"\n'
            '[claims]\nexpire_after_hours = 12\n[ledger]\npath = "/tmp/l"\nremote = "git@x:y.git"\n'))
        self.assertEqual(cfg.user.id, "me")
        self.assertEqual(cfg.servers[0].host_alias, "h1")
        self.assertEqual(cfg.claims.expire_after_hours, 12)
        self.assertEqual(cfg.ledger.remote, "git@x:y.git")

    def test_bad_version_is_error(self):
        with self.assertRaises(ValueError):
            load_config(write("config_version = 99\n"))

    def test_bad_type_is_error(self):
        with self.assertRaises(ValueError):
            load_config(write('[claims]\nexpire_after_hours = "soon"\n'))


class ConfigShapesTest(unittest.TestCase):
    def test_example_config_loads_without_warnings(self):
        cfg = load_config(Path(__file__).resolve().parent.parent / "config.example.toml")
        self.assertEqual(cfg.warnings, [])
        self.assertEqual(cfg.repositories[0].path, "~/your-task-repo")
        self.assertEqual(cfg.ledger.path, "~/.local/share/workboard/ledger")

    def test_reports_default_and_override(self):
        self.assertFalse(load_config(Path("/nonexistent")).reports.include_contribution)
        self.assertTrue(load_config(write("[reports]\ninclude_contribution = true\n")).reports.include_contribution)

    def test_bool_rejected_for_int(self):
        with self.assertRaises(ValueError):
            load_config(write("[claims]\nexpire_after_hours = true\n"))

    def test_plugin_ids_must_be_strings(self):
        with self.assertRaises(ValueError):
            load_config(write("[plugins]\nenabled = [1]\n"))

    def test_threshold_values_must_be_int(self):
        with self.assertRaises(ValueError):
            load_config(write('[thresholds]\nwarn_hours = {review = "x"}\n'))

    def test_scalar_server_entry_is_value_error(self):
        with self.assertRaises(ValueError):
            load_config(write('servers = ["a"]\n'))

    def test_root_path_key_in_file_is_unknown(self):
        cfg = load_config(write('path = "/x"\n'))
        self.assertIn("unknown key: path", cfg.warnings)

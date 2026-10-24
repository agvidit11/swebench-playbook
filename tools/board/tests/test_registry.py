import sys, types, unittest
from workboard.registry import Registry, load_plugins
from workboard.config import load_config
from pathlib import Path


def fake_module(name, api, register):
    m = types.ModuleType(name)
    m.PLUGIN_API_VERSION = api
    m.register = register
    sys.modules[name] = m
    return m


class Col:
    name = "codimango.status"
    def render(self, task, *, width):
        return None


class CoreCol:
    name = "core.state"
    def render(self, task, *, width):
        return None


class RegistryTest(unittest.TestCase):
    def tearDown(self):
        for name in [n for n in sys.modules if n.startswith("wb_")]:
            del sys.modules[name]

    def test_duplicate_across_plugins_warns(self):
        fake_module("wb_a", 1, lambda r: r.register_column(Col()))
        fake_module("wb_b", 1, lambda r: r.register_column(Col()))
        reg = load_plugins(self.cfg(["wb_a", "wb_b"]))
        self.assertIn("codimango.status", reg.columns)
        self.assertTrue(any("duplicate" in w for w in reg.warnings))

    def cfg(self, enabled):
        cfg = load_config(Path("/nonexistent"))
        cfg.plugins.enabled = enabled
        return cfg

    def test_plugin_registers_column(self):
        fake_module("wb_ok", 1, lambda r: r.register_column(Col()))
        reg = load_plugins(self.cfg(["wb_ok"]))
        self.assertIn("codimango.status", reg.columns)
        self.assertEqual(reg.warnings, [])

    def test_plugin_api_mismatch_disabled(self):
        fake_module("wb_old", 0, lambda r: r.register_column(Col()))
        reg = load_plugins(self.cfg(["wb_old"]))
        self.assertNotIn("codimango.status", reg.columns)
        self.assertTrue(any("wb_old" in w and "API" in w for w in reg.warnings))

    def test_plugin_cannot_register_core_field(self):
        fake_module("wb_core", 1, lambda r: r.register_column(CoreCol()))
        reg = load_plugins(self.cfg(["wb_core"]))
        self.assertNotIn("core.state", reg.columns)
        self.assertTrue(any("core." in w for w in reg.warnings))

    def test_plugin_import_error_isolated(self):
        reg = load_plugins(self.cfg(["no_such_plugin_xyz"]))
        self.assertTrue(any("no_such_plugin_xyz" in w for w in reg.warnings))

    def test_builtin_registry_allows_core(self):
        reg = Registry(builtin=True)
        reg.register_column(CoreCol())
        self.assertIn("core.state", reg.columns)

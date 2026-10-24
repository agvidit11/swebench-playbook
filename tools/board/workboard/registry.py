"""Plugin registry. Plugins are trusted Python modules, loaded only when explicitly enabled in config."""
from __future__ import annotations

import importlib

from . import PLUGIN_API_VERSION

KINDS = ("sources", "columns", "checks", "stats")


class Registry:
    def __init__(self, builtin: bool = False):
        self.builtin = builtin          # built-in code may own core.* names; plugins may not
        self.sources, self.columns, self.checks, self.stats = {}, {}, {}, {}
        self.warnings: list[str] = []

    def _add(self, kind: str, obj) -> None:
        name = getattr(obj, "name", "")
        if not name:
            raise ValueError(f"{kind} plugin has no name")
        if name.startswith("core.") and not self.builtin:
            raise PermissionError(f"plugins cannot register core.* names ({name})")
        table = getattr(self, kind)
        if name in table:
            raise ValueError(f"duplicate {kind[:-1]} name {name!r}")
        table[name] = obj

    def register_source(self, obj):
        self._add("sources", obj)

    def register_column(self, obj):
        self._add("columns", obj)

    def register_check(self, obj):
        self._add("checks", obj)

    def register_stat(self, obj):
        self._add("stats", obj)

    def merge(self, other: "Registry", origin: str = "") -> None:
        for kind in KINDS:
            mine = getattr(self, kind)
            for name, obj in getattr(other, kind).items():
                if name in mine:
                    self.warnings.append(f"plugin {origin}: duplicate {kind[:-1]} {name!r} ignored")
                else:
                    mine[name] = obj
        self.warnings.extend(other.warnings)


def load_plugins(cfg) -> Registry:
    """Load explicitly enabled plugin modules. A failing plugin is disabled with a warning, never fatal."""
    reg = Registry()
    for modname in cfg.plugins.enabled:
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:  # isolate: a broken plugin must not break the board
            reg.warnings.append(f"plugin {modname}: import failed ({exc.__class__.__name__}: {exc})")
            continue
        api = getattr(mod, "PLUGIN_API_VERSION", None)
        if api != PLUGIN_API_VERSION:
            reg.warnings.append(f"plugin {modname}: API version {api} != {PLUGIN_API_VERSION}; disabled")
            continue
        scratch = Registry()
        try:
            mod.register(scratch)
        except Exception as exc:
            reg.warnings.append(f"plugin {modname}: register failed ({exc}); disabled")
            continue
        reg.merge(scratch, modname)
    return reg

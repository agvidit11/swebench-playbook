"""Load and validate ~/.config/workboard/config.toml. Personal values live only there, never in code."""
from __future__ import annotations

import os
import re
import tomllib
import typing
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path

CONFIG_VERSION = 1
def default_path() -> Path:
    """Read at call time so WORKBOARD_CONFIG set later (tests, wrappers) is honoured."""
    return Path(os.environ.get("WORKBOARD_CONFIG", "~/.config/workboard/config.toml")).expanduser()


@dataclass
class User:
    id: str = ""
    display_name: str = ""
    timezone: str = "America/Los_Angeles"
    week_start: str = "monday"
    match_ids: list[str] = field(default_factory=list)     # importer ids that mean "me" (unixname, numeric id)


@dataclass
class UI:
    color: str = "auto"          # auto | always | never
    unicode: str = "auto"        # auto | always | never
    default_group: str = "attention"
    style: str = "pretty"        # pretty (boxed, emoji, live-ready) | classic (compact words); plain/pipes use classic


@dataclass
class Codimango:
    command: str = "codimango"
    timeout_seconds: int = 60
    cache_ttl_seconds: int = 120
    max_stale_seconds: int = 900
    web_task_url: str = ""        # e.g. "https://<codimango-web>/submissions/{id}" ({id} or {task}); personal config only


@dataclass
class Server:
    id: str = ""
    host_alias: str = ""
    display_name: str = ""


@dataclass
class Repository:
    id: str = "tasks"
    path: str = ""
    remote_url: str = ""
    branch: str = "main"


@dataclass
class Ledger:
    path: str = "~/.local/share/workboard/ledger"
    remote: str = ""
    branch: str = "main"


@dataclass
class Claims:
    mode: str = "atomic"          # atomic | advisory
    expire_after_hours: int = 24
    heartbeat_interval_minutes: int = 10
    healthy_ttl_seconds: int = 120
    clock_skew_warn_seconds: int = 120
    max_live_claims: int = 200
    active_window_minutes: int = 120     # presence (recent work in a session) counts as ACTIVE for this long


@dataclass
class Thresholds:
    # hours in a state before the age turns warn / block, per state; "default" for the rest
    warn_hours: dict[str, int] = field(default_factory=lambda: {"default": 48, "review": 72, "needs_revision": 24})
    block_hours: dict[str, int] = field(default_factory=lambda: {"default": 120, "review": 168, "needs_revision": 72})


@dataclass
class Checks:
    # argv template for the pre-submit gate; "{task}" is replaced. Empty = `check run` disabled.
    presubmit: list[str] = field(default_factory=list)
    summary_regex: str = r"(\d+)\s+FAIL\s+·\s+(\d+)\s+WARN\s+·\s+(\d+)\s+PASS"
    timeout_seconds: int = 900


@dataclass
class Rank:
    daiquery_id: str = ""
    command: str = "meta"


@dataclass
class Reports:
    include_contribution: bool = False    # contribution stats (per session/host/model) in exports


@dataclass
class PricingModel:
    """Optional private pricing.  Token facts never depend on these rates."""
    pattern: str = ""
    effective_from: str = ""
    input_per_million: float = 0.0
    output_per_million: float = 0.0
    cache_read_per_million: float = 0.0
    cache_write_per_million: float = 0.0
    reasoning_per_million: float = 0.0
    currency: str = "USD"
    context_window: int = 0


@dataclass
class Pricing:
    models: list[PricingModel] = field(default_factory=list)


@dataclass
class Legacy:
    claims_md: str = ""        # path to a free-text claims ledger for `workboard import-claims`


@dataclass
class Plugins:
    api_version: int = 1
    enabled: list[str] = field(default_factory=list)


@dataclass
class Config:
    config_version: int = CONFIG_VERSION
    profile: str = "default"          # deployments set e.g. "swebench-codimango" in their config
    user: User = field(default_factory=User)
    ui: UI = field(default_factory=UI)
    codimango: Codimango = field(default_factory=Codimango)
    servers: list[Server] = field(default_factory=list)
    repositories: list[Repository] = field(default_factory=list)
    ledger: Ledger = field(default_factory=Ledger)
    claims: Claims = field(default_factory=Claims)
    thresholds: Thresholds = field(default_factory=Thresholds)
    checks: Checks = field(default_factory=Checks)
    rank: Rank = field(default_factory=Rank)
    reports: Reports = field(default_factory=Reports)
    pricing: Pricing = field(default_factory=Pricing)
    legacy: Legacy = field(default_factory=Legacy)
    plugins: Plugins = field(default_factory=Plugins)
    path: str = ""                     # internal: where this config was loaded from
    warnings: list[str] = field(default_factory=list)


_ROOT_INTERNAL = {"path", "warnings"}   # root-only fields set by the loader, not by the file


def _check(value, tp, dotted: str, warnings: list):
    """Validate value against a declared type; return the (possibly converted) value."""
    origin = typing.get_origin(tp)
    if is_dataclass(tp):
        if not isinstance(value, dict):
            raise ValueError(f"{dotted} must be a table")
        inst = tp()
        _fill(inst, value, f"{dotted}.", warnings)
        return inst
    if origin is list:
        (item_tp,) = typing.get_args(tp)
        if not isinstance(value, list):
            raise ValueError(f"{dotted} must be an array")
        return [_check(v, item_tp, f"{dotted}[{i}]", warnings) for i, v in enumerate(value)]
    if origin is dict:
        key_tp, val_tp = typing.get_args(tp)
        if not isinstance(value, dict):
            raise ValueError(f"{dotted} must be a table")
        return {_check(k, key_tp, f"{dotted}.<key>", warnings): _check(v, val_tp, f"{dotted}.{k}", warnings)
                for k, v in value.items()}
    if tp is bool:
        ok = isinstance(value, bool)
    elif tp is int:
        ok = isinstance(value, int) and not isinstance(value, bool)
    elif tp is float:
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    else:
        ok = isinstance(value, tp)
    if not ok:
        raise ValueError(f"{dotted}: expected {getattr(tp, '__name__', tp)}, got {type(value).__name__}")
    return value


def _fill(obj, data: dict, prefix: str, warnings: list) -> None:
    hints = typing.get_type_hints(type(obj))
    skip = _ROOT_INTERNAL if isinstance(obj, Config) else set()
    known = {f.name for f in fields(obj) if f.name not in skip}
    for key, value in data.items():
        dotted = f"{prefix}{key}"
        if key not in known:
            warnings.append(f"unknown key: {dotted}")
            continue
        setattr(obj, key, _check(value, hints[key], dotted, warnings))


def load_config(path: Path | None = None) -> Config:
    path = Path(path) if path else default_path()
    cfg = Config(path=str(path))
    if not path.exists():
        cfg.warnings.append(f"config not found at {path}; using defaults (copy config.example.toml)")
        return cfg
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    version = data.get("config_version", CONFIG_VERSION)
    if version != CONFIG_VERSION:
        raise ValueError(f"config_version {version} not supported (expected {CONFIG_VERSION})")
    _fill(cfg, data, "", cfg.warnings)
    try:
        if re.compile(cfg.checks.summary_regex).groups < 3:
            raise ValueError("checks.summary_regex needs 3 groups: fail, warn, pass")
    except re.error as exc:
        raise ValueError(f"checks.summary_regex is not a valid regex: {exc}") from None
    return cfg

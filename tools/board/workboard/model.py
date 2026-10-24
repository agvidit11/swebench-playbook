"""Shared value types. Sources produce observations; the projection produces TaskViews and findings."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence

SEVERITIES = ("info", "warn", "block")


@dataclass(frozen=True)
class Observation:
    source: str
    entity_id: str
    observed_at: datetime
    fields: Mapping[str, object]          # namespaced, e.g. "codimango.validation_status"
    authority: Mapping[str, str] = field(default_factory=dict)  # field -> authoritative|advisory|derived


@dataclass(frozen=True)
class SourceHealth:
    source: str
    ok: bool
    observed_at: datetime | None
    stale_after_seconds: int
    detail: str = ""


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str                          # info | warn | block
    summary: str
    next_action: str                       # what to do about it; every finding must say

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError(f"bad severity {self.severity!r}")


@dataclass(frozen=True)
class FetchResult:
    observations: Sequence[Observation]
    health: SourceHealth
    findings: Sequence[Finding] = ()


@dataclass(frozen=True)
class Cell:
    text: str                              # semantic text; the renderer adds style
    sort_key: object = None
    full_text: str | None = None


@dataclass
class TaskView:
    entity_id: str
    fields: dict[str, object] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    health: dict[str, SourceHealth] = field(default_factory=dict)

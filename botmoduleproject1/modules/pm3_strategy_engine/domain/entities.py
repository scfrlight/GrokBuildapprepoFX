"""Mutable catalog entities stored behind repository ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from botmoduleproject1.contracts.v1.strategy_engine import (
    ProfileStatus,
    StrategyTemplateType,
)
from botmoduleproject1.contracts.v1.tuning import ParameterSchema


@dataclass
class StrategyPreset:
    name: str
    template_type: StrategyTemplateType
    parameters: dict[str, Any]


@dataclass
class StrategyProfile:
    profile_id: str
    name: str
    template_type: StrategyTemplateType
    status: ProfileStatus
    active_version_id: str | None
    created_at: datetime
    schema: tuple[ParameterSchema, ...] = ()
    presets: tuple[StrategyPreset, ...] = ()


@dataclass
class ProfileVersion:
    version_id: str
    profile_id: str
    status: ProfileStatus
    parameters: dict[str, Any]
    fingerprint: str
    created_at: datetime
    parent_version_id: str | None = None
    immutable: bool = False
    notes: str = ""


@dataclass
class StrategyDraft:
    draft_id: str
    profile_id: str
    source_version_id: str
    parameters: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class SymbolStrategyBinding:
    binding_id: str
    symbol: str
    profile_id: str
    version_id: str
    template_type: StrategyTemplateType
    active: bool
    created_at: datetime
    previous_version_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

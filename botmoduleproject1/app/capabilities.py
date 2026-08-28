"""Capability model declared by every registered module."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Capability(str, Enum):
    MARKET_DATA = "market_data"
    REGIME_DETECTION = "regime_detection"
    SIGNALS = "signals"
    FORECASTING = "forecasting"
    RISK_GATING = "risk_gating"
    EXECUTION = "execution"
    STORAGE = "storage"
    NOTIFICATIONS = "notifications"
    TELEMETRY = "telemetry"
    DIAGNOSTICS = "diagnostics"
    PLATFORM = "platform"


class ModuleMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version: str
    capabilities: tuple[Capability, ...]
    api_version: str = "v1"
    critical: bool = False
    dependencies: tuple[str, ...] = ()
    health_support: bool = True
    readiness_required: bool = False
    liveness_required: bool = False
    enabled: bool = True
    description: str = ""

    @property
    def capability_set(self) -> frozenset[Capability]:
        return frozenset(self.capabilities)


PLATFORM_CORE = ModuleMetadata(
    name="pm1_platform",
    version="0.1.0",
    capabilities=(Capability.PLATFORM, Capability.DIAGNOSTICS, Capability.TELEMETRY),
    critical=True,
    health_support=True,
    readiness_required=True,
    liveness_required=True,
    description="Composition root and integration kernel.",
)

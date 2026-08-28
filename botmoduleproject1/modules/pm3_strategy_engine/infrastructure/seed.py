"""Deterministic in-memory catalog seed. Shadow activation only."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from botmoduleproject1.contracts.v1.strategy_engine import ProfileStatus, StrategyTemplateType
from botmoduleproject1.contracts.v1.tuning import ParameterSchema
from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import (
    ProfileVersion,
    StrategyPreset,
    StrategyProfile,
    SymbolStrategyBinding,
)
from botmoduleproject1.modules.pm3_strategy_engine.domain.enums import FIRST_PHASE

SCHEMA = (
    ParameterSchema(
        name="historical_reliability",
        display_name="Historical reliability",
        group="weights",
        type="float",
        default=0.55,
        min=0.0,
        max=1.0,
        step=0.05,
        ui_mode="slider",
        description="H_i input to consensus weight.",
    ),
    ParameterSchema(
        name="recent_live_health",
        display_name="Recent live health",
        group="weights",
        type="float",
        default=0.50,
        min=0.0,
        max=1.0,
        step=0.05,
        ui_mode="slider",
        description="L_i input. Not a claim of live edge.",
    ),
    ParameterSchema(
        name="lookback",
        display_name="Lookback bars",
        group="structure",
        type="int",
        default=20,
        min=5,
        max=80,
        step=1,
        ui_mode="input",
        description="Template lookback hint.",
    ),
)

DEFAULT_PARAMS = {
    "historical_reliability": 0.55,
    "recent_live_health": 0.50,
    "lookback": 20,
}


def fingerprint(params: dict) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seed_catalog(
    *,
    as_of: datetime,
    universe: tuple[str, ...],
    profiles,
    versions,
    bindings,
) -> None:
    for template in FIRST_PHASE:
        profile_id = f"profile:{template.value}"
        version_id = f"version:{template.value}:v1"
        params = dict(DEFAULT_PARAMS)
        profile = StrategyProfile(
            profile_id=profile_id,
            name=template.value.replace("_", " "),
            template_type=template,
            status=ProfileStatus.ACTIVE,
            active_version_id=version_id,
            created_at=as_of,
            schema=SCHEMA,
            presets=(
                StrategyPreset(name="balanced", template_type=template, parameters=dict(params)),
            ),
        )
        version = ProfileVersion(
            version_id=version_id,
            profile_id=profile_id,
            status=ProfileStatus.ACTIVE,
            parameters=params,
            fingerprint=fingerprint(params),
            created_at=as_of,
            immutable=True,
            notes="seed tested→active (shadow only)",
        )
        profiles.save(profile)
        versions.save(version)
        for symbol in universe:
            bindings.save(
                SymbolStrategyBinding(
                    binding_id=f"bind:{symbol}:{template.value}",
                    symbol=symbol,
                    profile_id=profile_id,
                    version_id=version_id,
                    template_type=template,
                    active=True,
                    created_at=as_of,
                )
            )

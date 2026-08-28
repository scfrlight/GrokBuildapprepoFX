"""Typed feature flags. Dangerous flags are default-off and env-only."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.app.exceptions import FeatureFlagError, LiveTradingDisabledError
from botmoduleproject1.app.profiles import ProfileName


class SafetyClassification(str, Enum):
    SAFE = "safe"
    REQUIRES_REVIEW = "requires-review"
    DANGEROUS = "dangerous"


class FeatureFlagSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    field: str
    description: str
    default: bool = False
    allowed_profiles: tuple[ProfileName, ...]
    safety: SafetyClassification
    env_key: str


# Nested env path is BOTMODULEPROJECT1_FEATURE_FLAGS__<FIELD>
def _env_key(field: str) -> str:
    return f"BOTMODULEPROJECT1_FEATURE_FLAGS__{field.upper()}"


# Alias env keys used in the Sequence 02 spec (enable_* names).
_ALIAS_ENV = {
    "market_data": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM2_MARKET_DATA",
    "strategy_engine": "BOTMODULEPROJECT1_FEATURE__ENABLE_STRATEGY_ENGINE",
    "forecasting": "BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING",
    "risk_engine": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE",
    "execution": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_EXECUTION",
    "telegram": "BOTMODULEPROJECT1_FEATURE__ENABLE_TELEGRAM_CONTROL",
    "fine_tune_studio": "BOTMODULEPROJECT1_FEATURE__ENABLE_FINE_TUNE_STUDIO",
    "live_trading": "BOTMODULEPROJECT1_FEATURE__ENABLE_LIVE_TRADING",
}

_ALL_PROFILES = tuple(ProfileName)
_NON_LIVE = (
    ProfileName.DEMO,
    ProfileName.TEST,
    ProfileName.BACKTEST,
    ProfileName.RESEARCH,
)

FEATURE_FLAG_CATALOG: tuple[FeatureFlagSpec, ...] = (
    FeatureFlagSpec(
        name="enable_pm2_market_data",
        field="market_data",
        description="PM2 market data / session / regime (not implemented).",
        allowed_profiles=_NON_LIVE,
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["market_data"],
    ),
    FeatureFlagSpec(
        name="enable_strategy_engine",
        field="strategy_engine",
        description="PM3-Strategy Engine. Not implemented.",
        allowed_profiles=_NON_LIVE,
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["strategy_engine"],
    ),
    FeatureFlagSpec(
        name="enable_forecasting",
        field="forecasting",
        description="PM3 forecasting / QRF. Not implemented.",
        allowed_profiles=(ProfileName.DEMO, ProfileName.RESEARCH, ProfileName.TEST),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["forecasting"],
    ),
    FeatureFlagSpec(
        name="enable_pm4_risk_gate",
        field="risk_engine",
        description="PM4 exclusive risk engine. Placeholder remains DENY until PM4 ships.",
        allowed_profiles=_NON_LIVE,
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["risk_engine"],
    ),
    FeatureFlagSpec(
        name="enable_pm5_execution",
        field="execution",
        description="PM5 order send. Dangerous. Env opt-in only. Kernel still refuses orders.",
        allowed_profiles=(ProfileName.DEMO,),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["execution"],
    ),
    FeatureFlagSpec(
        name="enable_telegram_control",
        field="telegram",
        description="PM9 Telegram transport. Dangerous. Env opt-in only.",
        allowed_profiles=(ProfileName.DEMO, ProfileName.RESEARCH),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["telegram"],
    ),
    FeatureFlagSpec(
        name="enable_fine_tune_studio",
        field="fine_tune_studio",
        description="PM9a studio. Research only. Never auto-promotes to live.",
        allowed_profiles=(ProfileName.RESEARCH, ProfileName.TEST),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["fine_tune_studio"],
    ),
    FeatureFlagSpec(
        name="enable_live_trading",
        field="live_trading",
        description="Reserved. No override exists in this build. Always fail-closed.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["live_trading"],
    ),
)

CATALOG_BY_FIELD = {spec.field: spec for spec in FEATURE_FLAG_CATALOG}


class FeatureFlag(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    default: bool
    allowed_profiles: tuple[str, ...]
    safety: SafetyClassification
    enabled: bool
    source: str = "default"


class FeatureFlags(BaseModel):
    model_config = ConfigDict(extra="ignore")

    strategy_engine: bool = False
    forecasting: bool = False
    risk_engine: bool = False
    execution: bool = False
    telegram: bool = False
    fine_tune_studio: bool = False
    market_data: bool = False
    live_trading: bool = False
    env_opt_in: tuple[str, ...] = Field(default=())

    def enabled_map(self) -> dict[str, bool]:
        return {
            spec.name: bool(getattr(self, spec.field)) for spec in FEATURE_FLAG_CATALOG
        }

    def catalog(self, profile: ProfileName) -> tuple[FeatureFlag, ...]:
        opted = set(self.env_opt_in)
        flags: list[FeatureFlag] = []
        for spec in FEATURE_FLAG_CATALOG:
            enabled = bool(getattr(self, spec.field))
            source = "default"
            if enabled and spec.field in opted:
                source = "env"
            elif enabled:
                source = "yaml"
            flags.append(
                FeatureFlag(
                    name=spec.name,
                    description=spec.description,
                    default=spec.default,
                    allowed_profiles=tuple(p.value for p in spec.allowed_profiles),
                    safety=spec.safety,
                    enabled=enabled,
                    source=source,
                )
            )
        return tuple(flags)


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_opt_in_fields(environ: Mapping[str, str]) -> dict[str, bool]:
    """Fields explicitly set via allowlisted feature-flag env keys."""
    found: dict[str, bool] = {}
    for spec in FEATURE_FLAG_CATALOG:
        keys = (_env_key(spec.field), spec.env_key)
        for key in keys:
            if key in environ and str(environ[key]).strip() != "":
                found[spec.field] = _parse_bool(str(environ[key]))
                break
    return found


def feature_flags_from_environ(environ: Mapping[str, str]) -> dict[str, Any]:
    opted = env_opt_in_fields(environ)
    if not opted:
        return {}
    payload: dict[str, Any] = dict(opted)
    payload["env_opt_in"] = tuple(opted.keys())
    return {"feature_flags": payload}


def validate_feature_flags(flags: FeatureFlags, profile: ProfileName) -> None:
    opted = set(flags.env_opt_in)
    for spec in FEATURE_FLAG_CATALOG:
        enabled = bool(getattr(flags, spec.field))
        if not enabled:
            continue
        if spec.safety is SafetyClassification.DANGEROUS and spec.field not in opted:
            raise FeatureFlagError(
                f"dangerous feature flag {spec.name} is default-disabled and "
                f"requires explicit env opt-in ({spec.env_key}=true); YAML cannot enable it"
            )
        if spec.field == "live_trading":
            raise LiveTradingDisabledError("feature flag enable_live_trading")
        if profile not in spec.allowed_profiles:
            raise FeatureFlagError(
                f"feature flag {spec.name} is not allowed in profile {profile.value}"
            )

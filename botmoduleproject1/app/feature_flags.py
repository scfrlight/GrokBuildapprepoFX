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
    "strategy_engine": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM3_STRATEGY_ENGINE",
    "forecasting": "BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING",
    "risk_engine": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE",
    "execution": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_EXECUTION",
    "pm5_simulation": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_SIMULATION",
    "pm5_broker_adapter": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_BROKER_ADAPTER",
    "mt5_demo_execution": "BOTMODULEPROJECT1_FEATURE__ENABLE_MT5_DEMO_EXECUTION",
    "live_execution": "BOTMODULEPROJECT1_FEATURE__ENABLE_LIVE_EXECUTION",
    "telegram": "BOTMODULEPROJECT1_FEATURE__ENABLE_TELEGRAM_CONTROL",
    "fine_tune_studio": "BOTMODULEPROJECT1_FEATURE__ENABLE_FINE_TUNE_STUDIO",
    "live_trading": "BOTMODULEPROJECT1_FEATURE__ENABLE_LIVE_TRADING",
    "pm6_post_trade": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_POST_TRADE",
    "pm6_surveillance": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_SURVEILLANCE",
    "pm6_incident_response": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_INCIDENT_RESPONSE",
    "pm6_governance": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_GOVERNANCE_INTELLIGENCE",
    "pm6_withdrawal": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM6_WITHDRAWAL_PLANNER",
    "pm7_persistence": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_PERSISTENCE",
    "pm7_journal": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_JOURNAL",
    "pm7_replay": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_REPLAY",
    "pm7_integrity": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_INTEGRITY",
    "pm7_retention": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_RETENTION",
    "pm7_reporting": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_REPORTING",
    "pm8_operator": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_OPERATOR",
    "pm8_hitl": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_HITL",
    "pm8_command_audit": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_COMMAND_AUDIT",
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
        description="PM2 market context / regime / ranking. Env opt-in; test and research only.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["market_data"],
    ),
    FeatureFlagSpec(
        name="enable_pm3_strategy_engine",
        field="strategy_engine",
        description="PM3-Strategy Engine. Env opt-in; test and research only. TradeIntent only, never orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["strategy_engine"],
    ),
    FeatureFlagSpec(
        name="enable_forecasting",
        field="forecasting",
        description="PM3 forecasting / QRF residual quantile envelope. Env opt-in; demo/test/research. Enriches uncertainty only; never orders, never mutates side.",
        allowed_profiles=(ProfileName.DEMO, ProfileName.RESEARCH, ProfileName.TEST),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["forecasting"],
    ),
    FeatureFlagSpec(
        name="enable_pm4_risk_gate",
        field="risk_engine",
        description="PM4 exclusive risk engine. Authoritative deny-by-default gate. Env opt-in; test and research only. ALLOW is not an order; PM5 stays closed.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["risk_engine"],
    ),
    FeatureFlagSpec(
        name="enable_pm5_simulation",
        field="pm5_simulation",
        description=(
            "PM5 OMS/EMS simulation. Env opt-in; test and research only. "
            "Records simulated lifecycle. Does not send to a broker. Tickets are SIM-*."
        ),
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm5_simulation"],
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
        name="enable_pm5_broker_adapter",
        field="pm5_broker_adapter",
        description="PM5 real broker adapter. Refused in Sequence 07.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["pm5_broker_adapter"],
    ),
    FeatureFlagSpec(
        name="enable_mt5_demo_execution",
        field="mt5_demo_execution",
        description="MT5 demo execution. Future-controlled. Refused in Sequence 07.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["mt5_demo_execution"],
    ),
    FeatureFlagSpec(
        name="enable_live_execution",
        field="live_execution",
        description="Live execution. Always fail-closed in Sequence 07.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["live_execution"],
    ),
    FeatureFlagSpec(
        name="enable_telegram_control",
        field="telegram",
        description="Real Telegram Bot API. Refused in Sequence 10. Use enable_pm8_operator (simulated transport).",
        allowed_profiles=(),
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
    FeatureFlagSpec(
        name="enable_pm6_post_trade",
        field="pm6_post_trade",
        description="PM6 post-trade controls. Env opt-in; test and research only. Observes PM4/PM5. Never orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_post_trade"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_surveillance",
        field="pm6_surveillance",
        description="PM6 automated surveillance detectors. Test/research. Does not send orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_surveillance"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_incident_response",
        field="pm6_incident_response",
        description="PM6 incident orchestration. Test/research. No auto-rearm, no broker commands.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_incident_response"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_governance_intelligence",
        field="pm6_governance",
        description="PM6 governance/validation packets. Test/research. Headless DTOs only.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_governance"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_withdrawal_planner",
        field="pm6_withdrawal",
        description="PM6 orderly withdrawal planner. Test/research. Requests PM5 control; never a venue send.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_withdrawal"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_persistence",
        field="pm7_persistence",
        description="PM7 append-only journal. Env opt-in; test and research only. Never orders. Not production durability.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_persistence"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_journal",
        field="pm7_journal",
        description="PM7 journal writer. Test/research. Append-only. No historical mutation.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_journal"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_replay",
        field="pm7_replay",
        description="PM7 deterministic replay. Test/research. Never mutates source history.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_replay"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_integrity",
        field="pm7_integrity",
        description="PM7 hash-chain verification. Test/research. Tamper detection, not tamper-proof.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_integrity"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_retention",
        field="pm7_retention",
        description="PM7 retention/archive. Test/research. Freeze blocks purge. No silent deletion.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_retention"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_reporting",
        field="pm7_reporting",
        description="PM7 lineage-aware reports. Test/research. insufficient_data when empty.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_reporting"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_operator",
        field="pm8_operator",
        description="PM8 operator control plane. Env opt-in; test and research only. Simulated transport. Commands are not orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_operator"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_hitl",
        field="pm8_hitl",
        description="PM8 human-in-the-loop approval queue. Test/research. Approvals do not skip PM4.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_hitl"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_command_audit",
        field="pm8_command_audit",
        description="PM8 command audit trail. Test/research. Not a durable ledger.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_command_audit"],
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
    pm5_simulation: bool = False
    pm5_broker_adapter: bool = False
    mt5_demo_execution: bool = False
    live_execution: bool = False
    telegram: bool = False
    fine_tune_studio: bool = False
    market_data: bool = False
    live_trading: bool = False
    pm6_post_trade: bool = False
    pm6_surveillance: bool = False
    pm6_incident_response: bool = False
    pm6_governance: bool = False
    pm6_withdrawal: bool = False
    pm7_persistence: bool = False
    pm7_journal: bool = False
    pm7_replay: bool = False
    pm7_integrity: bool = False
    pm7_retention: bool = False
    pm7_reporting: bool = False
    pm8_operator: bool = False
    pm8_hitl: bool = False
    pm8_command_audit: bool = False
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
        if spec.field == "strategy_engine":
            keys = keys + ("BOTMODULEPROJECT1_FEATURE__ENABLE_STRATEGY_ENGINE",)
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
        if spec.field in {"live_trading", "live_execution"}:
            raise LiveTradingDisabledError(f"feature flag {spec.name}")
        if spec.field in {"pm5_broker_adapter", "mt5_demo_execution"}:
            raise FeatureFlagError(
                f"feature flag {spec.name} is refused in Sequence 07; "
                "no broker adapter and no MT5 demo execution"
            )
        if spec.field == "telegram":
            raise FeatureFlagError(
                f"feature flag {spec.name} is refused in Sequence 10; "
                "no Telegram Bot API. Use enable_pm8_operator with SimulatedTransport"
            )
        if profile not in spec.allowed_profiles:
            raise FeatureFlagError(
                f"feature flag {spec.name} is not allowed in profile {profile.value}"
            )

"""Typed feature flags. Dangerous flags default-off, env-only."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.app.exceptions import FeatureFlagError, LiveTradingDisabledError
from botmoduleproject1.app.profiles import ProfileName
from botmoduleproject1.app.sequence_gate import assert_operator_not_frozen

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
    "pm8_persistence": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_PERSISTENCE",
    "pm8_outbox": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_OUTBOX",
    "pm8_projections": "BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_PROJECTIONS",
    "mt5_demo_adapter": "BOTMODULEPROJECT1_FEATURE__ENABLE_MT5_DEMO_ADAPTER",
    "exit_engine": "BOTMODULEPROJECT1_FEATURE__ENABLE_EXIT_ENGINE",
    "unified_runtime": "BOTMODULEPROJECT1_FEATURE__ENABLE_UNIFIED_RUNTIME",
    "demo_trading_readiness": "BOTMODULEPROJECT1_FEATURE__ENABLE_DEMO_TRADING_READINESS",
}

FEATURE_FLAG_CATALOG: tuple[FeatureFlagSpec, ...] = (
    FeatureFlagSpec(
        name="enable_pm2_market_data",
        field="market_data",
        description="PM2 market context / regime / ranking. Env opt-in; test/research.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["market_data"],
    ),
    FeatureFlagSpec(
        name="enable_pm3_strategy_engine",
        field="strategy_engine",
        description="PM3-Strategy Engine. Env opt-in; test/research. TradeIntent only, never orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["strategy_engine"],
    ),
    FeatureFlagSpec(
        name="enable_forecasting",
        field="forecasting",
        description="PM3 forecasting / QRF envelope. Env opt-in; demo/test/research. Never orders.",
        allowed_profiles=(ProfileName.DEMO, ProfileName.RESEARCH, ProfileName.TEST),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["forecasting"],
    ),
    FeatureFlagSpec(
        name="enable_pm4_risk_gate",
        field="risk_engine",
        description="PM4 exclusive risk engine. Env opt-in; test/research. ALLOW is not an order.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["risk_engine"],
    ),
    FeatureFlagSpec(
        name="enable_pm5_simulation",
        field="pm5_simulation",
        description="PM5 OMS/EMS simulation. Env opt-in; test/research. SIM-* only; no broker send.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm5_simulation"],
    ),
    FeatureFlagSpec(
        name="enable_pm5_execution",
        field="execution",
        description="PM5 order send. Dangerous. Env opt-in. Kernel refuses orders.",
        allowed_profiles=(ProfileName.DEMO,),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["execution"],
    ),
    FeatureFlagSpec(
        name="enable_pm5_broker_adapter",
        field="pm5_broker_adapter",
        description="PM5 real broker adapter. Refused in Seq07.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["pm5_broker_adapter"],
    ),
    FeatureFlagSpec(
        name="enable_mt5_demo_execution",
        field="mt5_demo_execution",
        description="MT5 demo execution. Refused in Seq07.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["mt5_demo_execution"],
    ),
    FeatureFlagSpec(
        name="enable_live_execution",
        field="live_execution",
        description="Live execution. Always fail-closed.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["live_execution"],
    ),
    FeatureFlagSpec(
        name="enable_telegram_control",
        field="telegram",
        description="Real Telegram Bot API. Refused. Canonical operator plane is Sequence 13.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["telegram"],
    ),
    FeatureFlagSpec(
        name="enable_fine_tune_studio",
        field="fine_tune_studio",
        description="PM9a studio. Research/test. Never auto-promotes to live.",
        allowed_profiles=(ProfileName.RESEARCH, ProfileName.TEST),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["fine_tune_studio"],
    ),
    FeatureFlagSpec(
        name="enable_live_trading",
        field="live_trading",
        description="Reserved. Always fail-closed in this build.",
        allowed_profiles=(),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["live_trading"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_post_trade",
        field="pm6_post_trade",
        description="PM6 post-trade controls. Env opt-in; test/research. Observes PM4/PM5. Never orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_post_trade"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_surveillance",
        field="pm6_surveillance",
        description="PM6 surveillance detectors. Test/research. No orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_surveillance"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_incident_response",
        field="pm6_incident_response",
        description="PM6 incidents. Test/research. No auto-rearm/broker cmds.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_incident_response"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_governance_intelligence",
        field="pm6_governance",
        description="PM6 governance packets. Test/research. Headless DTOs.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_governance"],
    ),
    FeatureFlagSpec(
        name="enable_pm6_withdrawal_planner",
        field="pm6_withdrawal",
        description="PM6 withdrawal planner. Test/research. Never a venue send.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm6_withdrawal"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_persistence",
        field="pm7_persistence",
        description="PM7 append-only journal. Env opt-in; test/research. Never orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_persistence"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_journal",
        field="pm7_journal",
        description="PM7 journal writer. Test/research. Append-only.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_journal"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_replay",
        field="pm7_replay",
        description="PM7 deterministic replay. Test/research.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_replay"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_integrity",
        field="pm7_integrity",
        description="PM7 hash-chain verification. Test/research.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_integrity"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_retention",
        field="pm7_retention",
        description="PM7 retention/archive. Test/research. Freeze blocks purge.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_retention"],
    ),
    FeatureFlagSpec(
        name="enable_pm7_reporting",
        field="pm7_reporting",
        description="PM7 lineage-aware reports. Test/research.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm7_reporting"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_operator",
        field="pm8_operator",
        description="PM8 operator control plane. Seq13. Commands are not orders.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_operator"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_hitl",
        field="pm8_hitl",
        description="PM8 HITL approval queue. Test/research. Does not skip PM4.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_hitl"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_command_audit",
        field="pm8_command_audit",
        description="PM8 command audit. Seq13. Test/research. Not durable ledger.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_command_audit"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_persistence",
        field="pm8_persistence",
        description="Seq09 PM8 persistence API. Test/research. Never orders. Not production_durable.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_persistence"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_outbox",
        field="pm8_outbox",
        description="Seq09 outbox dispatcher. Test/research.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_outbox"],
    ),
    FeatureFlagSpec(
        name="enable_pm8_projections",
        field="pm8_projections",
        description="Seq09 projection rebuild. Test/research.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["pm8_projections"],
    ),
    FeatureFlagSpec(
        name="enable_mt5_demo_adapter",
        field="mt5_demo_adapter",
        description="Seq11 Demo-only MT5 adapter (mt5_execution_engine). Test/research. Live refused.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["mt5_demo_adapter"],
    ),
    FeatureFlagSpec(
        name="enable_exit_engine",
        field="exit_engine",
        description="Seq11 exit engine SL/TP/breakeven/time stops. Test/research. Never bypasses PM4.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["exit_engine"],
    ),
    FeatureFlagSpec(
        name="enable_unified_runtime",
        field="unified_runtime",
        description="Seq12 unified orchestrator. Test/research. No live path.",
        allowed_profiles=(ProfileName.TEST, ProfileName.RESEARCH),
        safety=SafetyClassification.REQUIRES_REVIEW,
        env_key=_ALIAS_ENV["unified_runtime"],
    ),
    FeatureFlagSpec(
        name="enable_demo_trading_readiness",
        field="demo_trading_readiness",
        description="Seq15 DEMO readiness allowlist. Env opt-in; demo only. Not live/MT5. PM4 exclusive.",
        allowed_profiles=(ProfileName.DEMO,),
        safety=SafetyClassification.DANGEROUS,
        env_key=_ALIAS_ENV["demo_trading_readiness"],
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
    pm8_persistence: bool = False
    pm8_outbox: bool = False
    pm8_projections: bool = False
    mt5_demo_adapter: bool = False
    exit_engine: bool = False
    unified_runtime: bool = False
    demo_trading_readiness: bool = False
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
        assert_operator_not_frozen(spec.field, spec.name)
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
                f"feature flag {spec.name} is refused; "
                "Telegram Bot API is never bound. Canonical operator plane is Sequence 13 "
                "and stays frozen until Sequences 09–12 complete. Use SimulatedTransport later."
            )
        if profile not in spec.allowed_profiles:
            raise FeatureFlagError(
                f"feature flag {spec.name} is not allowed in profile {profile.value}"
            )

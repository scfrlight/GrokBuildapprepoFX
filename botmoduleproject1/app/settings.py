"""Typed settings via pydantic-settings.

Sources, highest priority first:
1. explicit init / CLI kwargs
2. BOTMODULEPROJECT1_* prefixed env (nested via __)
3. secret allowlist env (MT5_*, TELEGRAM_*, BOTMODULEPROJECT1_DATABASE_URL)
4. optional .env file (allowlisted keys only)
5. YAML config (and ``extends`` parents)

Unprefixed ambient env (DATABASE_URL, TRADING_MODE, DEFAULT_SYMBOL, …) is ignored.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from botmoduleproject1.app.exceptions import LiveTradingDisabledError, SettingsError
from botmoduleproject1.app.feature_flags import (
    FeatureFlag,
    FeatureFlags,
    feature_flags_from_environ,
    validate_feature_flags,
)
from botmoduleproject1.app.profiles import ProfileName, ProfilePolicy, parse_profile, policy_for
from botmoduleproject1.app.python_version import assert_python_version
from botmoduleproject1.app.secrets import redact_node, secrets_from_environ

ENV_PREFIX = "BOTMODULEPROJECT1_"

CliMode = str
TradingMode = str

_CLI_MODES = (
    "test",
    "doctor",
    "paper",
    "live",
    "backfill",
    "demo",
    "observe-only",
    "observe",
    "health",
    "research",
    "backtest",
    "live-disabled",
)

_TRADING_MODES = (
    "test",
    "doctor",
    "backtest",
    "research",
    "demo",
    "paper",
    "observe-only",
    "live-disabled",
    "live",
)


class AppSection(BaseModel):
    name: str = "BotModuleProject1"
    environment: str = "local"
    timezone: str = "UTC"
    default_symbol: str = "EURUSD"

    @field_validator("timezone")
    @classmethod
    def _tz(cls, value: str) -> str:
        if value != "UTC":
            raise ValueError("timezone must be UTC (ADR-003)")
        return value


class SafetySection(BaseModel):
    trading_mode: str = "demo"
    live_trading_enabled: bool = False
    fail_closed: bool = True
    on_unknown_state: str = "observe-only"
    on_stale_data: str = "observe-only"
    on_incomplete_recovery: str = "halt"
    on_ledger_inconsistency: str = "halt"
    require_preflight: bool = True
    require_readiness: bool = True
    require_recovery: bool = True
    require_risk_ready_before_orders: bool = True

    @field_validator("trading_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value not in _TRADING_MODES:
            raise ValueError(f"unknown trading_mode {value!r}")
        return value


class LoggingSection(BaseModel):
    model_config = {"populate_by_name": True, "extra": "ignore"}

    level: str = "INFO"
    json_output: bool = Field(default=True, alias="json")
    redact_secrets: bool = True


class ClockSection(BaseModel):
    source: str = "system"
    aware: bool = True
    utc_only: bool = True


class IdentitySection(BaseModel):
    require_event_id: bool = True
    require_correlation_id: bool = True
    require_causation_id: bool = True
    require_idempotency_key_on_commands: bool = True


class Mt5Section(BaseModel):
    enabled: bool = False
    account_kind: str = "demo"
    terminal_path_env: str = "MT5_TERMINAL_PATH"
    login_env: str = "MT5_LOGIN"
    password_env: str = "MT5_PASSWORD"
    server_env: str = "MT5_SERVER"
    login: str | None = None
    password: SecretStr | None = None
    server: str | None = None
    terminal_path: str | None = None


class PersistenceSection(BaseModel):
    enabled: bool = False
    dsn_env: str = "BOTMODULEPROJECT1_DATABASE_URL"
    dsn: SecretStr | None = None
    api_is_sole_durable_path: bool = True


class TelegramSection(BaseModel):
    enabled: bool = False
    token_env: str = "TELEGRAM_BOT_TOKEN"
    chat_id_env: str = "TELEGRAM_CHAT_ID"
    allowed_user_ids_env: str = "TELEGRAM_ALLOWED_USER_IDS"
    token: SecretStr | None = None
    chat_id: str | None = None
    allowed_user_ids: str | None = None


class ModelRegistrySection(BaseModel):
    enabled: bool = False
    uri_env: str = "BOTMODULEPROJECT1_MODEL_REGISTRY_URI"
    uri: str | None = None


class NotificationsSection(BaseModel):
    enabled: bool = False


class ModulesSection(BaseModel):
    load_policy: str = "manual"
    allowlist: tuple[str, ...] = ()
    denylist: tuple[str, ...] = ()


class HealthSection(BaseModel):
    fail_on_critical: bool = True
    include_non_critical_in_ready: bool = False


class DiagnosticsSection(BaseModel):
    enabled: bool = True
    heartbeat_seconds: float = Field(default=5.0, gt=0)


class PathsSection(BaseModel):
    log_dir: str = "logs"
    data_dir: str = "data/local"


class Pm2Section(BaseModel):
    """Public PM2 knobs. Enabling the engine is a feature flag, not this block."""

    universe: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
    timeframes: tuple[str, ...] = ("M15", "H1", "H4")
    decision_timeframe: str = "H1"
    lookback_bars: int = 64
    operating_mode: str = "shadow"
    ranking_mode: str = "deterministic"
    one_per_cluster: bool = True
    ghost_tracking: bool = True
    telemetry: bool = True



class Pm3StrategySection(BaseModel):
    """Public PM3-Strategy Engine knobs. Enabling is a feature flag, not this block."""

    operating_mode: str = "shadow"
    max_active_branches: int = Field(default=3, ge=1, le=3)
    require_handoff_eligibility: bool = True
    universe: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
    enabled_templates: tuple[str, ...] = (
        "trend_pullback",
        "orb_session_breakout",
        "mean_reversion",
    )
    go_threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    edge_margin: float = Field(default=0.10, ge=0.0, le=1.0)
    min_selected_votes: int = Field(default=1, ge=1, le=3)
    conflict_no_trade: float = Field(default=0.35, ge=0.0, le=1.0)
    stale_ttl_hours: int = Field(default=4, ge=1, le=48)


class Pm3ForecastingSection(BaseModel):
    """Public PM3 forecasting / QRF knobs. Enabling is a feature flag, not this block."""

    horizon_bars: int = Field(default=4, ge=1, le=48)
    lookback_bars: int = Field(default=64, ge=16, le=512)
    min_samples: int = Field(default=20, ge=1, le=512)
    embargo_bars: int = Field(default=1, ge=1, le=16)
    timeframe: str = "H1"
    operating_mode: str = "shadow"
    observe_only: bool = True


class Pm4RiskGateSection(BaseModel):
    """Public PM4 knobs. Enabling the gate is a feature flag, not this block."""

    operating_mode: str = "shadow"
    observe_only: bool = True
    account_equity: str = "100000"
    account_currency: str = "USD"
    contract_size: str = "100000"
    lot_step: str = "0.01"
    min_lots: str = "0.01"
    max_lots: str = "5.0"
    account_risk_pct: str = "0.020"
    sleeve_risk_pct: str = "0.010"
    regime_risk_pct: str = "0.008"
    symbol_risk_pct: str = "0.005"
    cluster_risk_pct: str = "0.010"
    candidate_risk_pct: str = "0.005"
    max_per_trade_risk_pct: str = "0.005"
    max_open_risk_pct: str = "0.020"
    max_intraday_loss_pct: str = "0.015"
    max_daily_loss_pct: str = "0.020"
    heat_warm: str = "0.008"
    heat_hot: str = "0.014"
    heat_critical: str = "0.018"
    max_effective_heat: str = "0.020"
    dd_mild: str = "0.020"
    dd_reduced: str = "0.040"
    dd_restricted: str = "0.060"
    dd_freeze: str = "0.080"
    dd_kill: str = "0.100"
    losing_streak_throttle: int = Field(default=4, ge=1)
    cluster_cap: str = "0.012"
    usd_concentration_cap: str = "0.015"
    european_basket_cap: str = "0.012"
    crowding_block: str = "0.80"
    one_per_cluster: bool = True
    stale_ttl_seconds: int = Field(default=14400, ge=60)
    min_forecast_samples: int = Field(default=20, ge=1)
    wide_interval_pct: str = "0.008"
    min_liquidity_score: float = 40.0
    min_stop_distance: str = "0.00010"
    max_stop_distance: str = "0.05000"
    price_collar_bps: str = "50"
    max_notional: str = "500000"
    burst_limit: int = Field(default=8, ge=1)
    burst_window_seconds: int = Field(default=60, ge=1)
    duplicate_ttl_seconds: int = Field(default=86400, ge=1)
    verdict_ttl_seconds: int = Field(default=3600, ge=60)
    session_allow: tuple[str, ...] = ("london", "new_york", "overlap", "asia")
    risk_reducing_only_on_kill: bool = True
    recovery_cooldown_seconds: int = Field(default=300, ge=1)
    require_manual_recovery_after_kill: bool = True
    auto_rearm: bool = False
    telemetry_verbose: bool = True
    cancel_on_disconnect: bool = True
    route_name: str = "pm5_pending"

    @field_validator("auto_rearm")
    @classmethod
    def _no_auto_rearm(cls, value: bool) -> bool:
        if value:
            raise ValueError("pm4_risk_gate.auto_rearm must stay false")
        return value


class Pm5ExecutionSection(BaseModel):
    """Public PM5 knobs. Enabling is a feature flag, not this block. No live mode."""

    operating_mode: str = "disabled"
    observe_only: bool = True
    allowed_order_types: tuple[str, ...] = ("market", "limit")
    symbol_allowlist: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
    execution_policy: str = "simulation_only"
    stale_ttl_seconds: int = Field(default=14400, ge=60)
    idempotency_ttl_seconds: int = Field(default=86400, ge=1)
    submit_timeout_ms: int = Field(default=5000, ge=1)
    max_retries: int = Field(default=2, ge=0, le=5)
    submit_burst: int = Field(default=8, ge=1)
    reject_burst: int = Field(default=6, ge=1)
    cancel_burst: int = Field(default=12, ge=1)
    modify_burst: int = Field(default=8, ge=1)
    burst_window_seconds: int = Field(default=60, ge=1)
    recovery_cooldown_seconds: int = Field(default=300, ge=1)
    require_manual_recovery: bool = True
    auto_rearm: bool = False
    broker_adapter_enabled: bool = False
    mt5_enabled: bool = False
    simulation_auto_fill: bool = True
    slippage_limit: str = "0.00050"
    cancel_on_disconnect: bool = True
    telemetry_verbose: bool = True

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value not in {"disabled", "shadow", "simulation"}:
            raise ValueError("pm5_execution.operating_mode must be disabled|shadow|simulation")
        return value

    @field_validator("auto_rearm")
    @classmethod
    def _no_auto_rearm(cls, value: bool) -> bool:
        if value:
            raise ValueError("pm5_execution.auto_rearm must stay false")
        return value

    @field_validator("broker_adapter_enabled", "mt5_enabled")
    @classmethod
    def _no_broker(cls, value: bool) -> bool:
        if value:
            raise ValueError("pm5 broker/mt5 cannot be enabled in Sequence 07")
        return value


class Pm6PostTradeSection(BaseModel):
    """Public PM6 knobs. Enabling is a feature flag, not this block."""

    operating_mode: str = "shadow"
    observe_only: bool = True
    freshness_ttl_seconds: int = Field(default=300, ge=1)
    stale_ttl_seconds: int = Field(default=14400, ge=60)
    alert_dedup_seconds: int = Field(default=60, ge=1)
    incident_correlation_seconds: int = Field(default=300, ge=1)
    submit_burst: int = Field(default=8, ge=1)
    reject_burst: int = Field(default=6, ge=1)
    burst_window_seconds: int = Field(default=60, ge=1)
    silence_seconds: int = Field(default=600, ge=1)
    require_withdrawal_approval: bool = True
    require_withdrawal_confirmation: bool = True
    auto_rearm: bool = False
    auto_complete_withdrawal: bool = False
    mt5_enabled: bool = False
    broker_commands: bool = False
    durable: bool = False
    telemetry_verbose: bool = True

    @field_validator("auto_rearm")
    @classmethod
    def _no_auto_rearm(cls, value: bool) -> bool:
        if value:
            raise ValueError("pm6_post_trade.auto_rearm must stay false")
        return value

    @field_validator("mt5_enabled", "broker_commands", "durable", "auto_complete_withdrawal")
    @classmethod
    def _no_unsafe(cls, value: bool) -> bool:
        if value:
            raise ValueError("PM6 cannot enable MT5, broker commands, durable store, or auto-complete withdrawal")
        return value


class Pm7PersistenceSection(BaseModel):
    """Public PM7 knobs. Enabling is a feature flag, not this block."""

    operating_mode: str = "memory"
    observe_only: bool = True
    storage_path: str = "data/local/pm7"
    schema_version: int = Field(default=1, ge=1)
    query_limit: int = Field(default=50, ge=1, le=500)
    snapshot_cadence_events: int = Field(default=10, ge=1)
    replay_event_limit: int = Field(default=1000, ge=1)
    simulate_archive: bool = True
    allow_purge: bool = False
    hash_algorithm: str = "sha256"
    mt5_enabled: bool = False
    broker_commands: bool = False
    production_durable: bool = False
    auto_rearm: bool = False
    telemetry_verbose: bool = True

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value == "production_durable":
            raise ValueError("production_durable is refused in Sequence 09")
        if value not in {"disabled", "memory", "file_backed", "sqlite_local", "durable_candidate"}:
            raise ValueError("pm7_persistence.operating_mode must be disabled|memory|file_backed|sqlite_local|durable_candidate")
        return value

    @field_validator("auto_rearm")
    @classmethod
    def _no_auto_rearm(cls, value: bool) -> bool:
        if value:
            raise ValueError("pm7_persistence.auto_rearm must stay false")
        return value

    @field_validator("mt5_enabled", "broker_commands", "production_durable")
    @classmethod
    def _no_unsafe(cls, value: bool) -> bool:
        if value:
            raise ValueError("PM7 cannot enable MT5, broker commands, or production_durable")
        return value



class Pm8OperatorSection(BaseModel):
    """Public PM8 knobs. Enabling is a feature flag, not this block. No Telegram API."""

    operating_mode: str = "simulated"
    observe_only: bool = True
    approval_ttl_seconds: int = Field(default=900, ge=30, le=86400)
    halt_requires_dual_control: bool = False
    mt5_enabled: bool = False
    broker_commands: bool = False
    telegram_api: bool = False
    auto_rearm: bool = False
    auto_promote_to_live: bool = False
    telemetry_verbose: bool = True

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value == "telegram_api":
            raise ValueError("telegram_api transport is refused")
        if value not in {"disabled", "simulated"}:
            raise ValueError("pm8_operator.operating_mode must be disabled|simulated")
        return value

    @field_validator("auto_rearm", "mt5_enabled", "broker_commands", "telegram_api", "auto_promote_to_live")
    @classmethod
    def _no_unsafe(cls, value: bool) -> bool:
        if value:
            raise ValueError("PM8 cannot enable MT5, broker commands, telegram API, auto-rearm, or auto-promote")
        return value


class Pm8PersistenceSection(BaseModel):
    """Public PM8 persistence knobs. Enabling is a feature flag. Sequence 09/10."""

    operating_mode: str = "memory"
    storage_path: str = "data/local/pm8"
    schema_version: int = Field(default=2, ge=1, le=2)
    query_limit: int = Field(default=50, ge=1, le=500)
    max_outbox_attempts: int = Field(default=3, ge=1, le=10)
    production_durable: bool = False
    mt5_enabled: bool = False
    broker_commands: bool = False

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        if value not in {"disabled", "memory", "sqlite_local"}:
            raise ValueError("pm8_persistence.operating_mode must be disabled|memory|sqlite_local")
        return value

    @field_validator("production_durable", "mt5_enabled", "broker_commands")
    @classmethod
    def _no_unsafe(cls, value: bool) -> bool:
        if value:
            raise ValueError("PM8 persistence cannot enable MT5, broker commands, or production_durable")
        return value


class MappingSource(PydanticBaseSettingsSource):
    """Inject a precomputed nested mapping as a settings source."""

    def __init__(self, settings_cls: type[BaseSettings], data: dict[str, Any]) -> None:
        super().__init__(settings_cls)
        self._data = data

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        if field_name in self._data:
            return self._data[field_name], field_name, False
        return None, field_name, False

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        return dict(self._data)


def _coerce_scalar(raw: str) -> Any:
    text = raw.strip()
    lowered = text.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none", ""}:
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def nested_from_prefixed_env(environ: Mapping[str, str], *, prefix: str = ENV_PREFIX) -> dict[str, Any]:
    """Parse BOTMODULEPROJECT1_FOO__BAR into {foo: {bar: value}}. Ignores other keys."""
    root: dict[str, Any] = {}
    for key, raw in environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :].split("__")
        if not path or not path[0]:
            continue
        cursor: dict[str, Any] = root
        for part in path[:-1]:
            name = part.lower()
            nxt = cursor.get(name)
            if not isinstance(nxt, dict):
                nxt = {}
                cursor[name] = nxt
            cursor = nxt
        cursor[path[-1].lower()] = _coerce_scalar(str(raw))
    return root


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SettingsError(f"cannot read config file {path}: {exc}") from exc
    loaded = yaml.safe_load(raw) or {}
    if not isinstance(loaded, dict):
        raise SettingsError(f"config file {path} must be a mapping")
    return loaded


def load_composed_yaml(path: Path, *, _seen: frozenset[Path] | None = None) -> dict[str, Any]:
    resolved = path.resolve()
    seen = _seen or frozenset()
    if resolved in seen:
        raise SettingsError(f"config extends cycle at {resolved}")
    data = load_yaml(resolved)
    extends = data.pop("extends", None)
    if not extends:
        return data
    parent_path = Path(str(extends))
    if not parent_path.is_absolute():
        parent_path = resolved.parent / parent_path
    parent = load_composed_yaml(parent_path, _seen=seen | {resolved})
    return deep_merge(parent, data)


def load_dotenv_allowlisted(path: Path) -> dict[str, str]:
    from dotenv import dotenv_values

    from botmoduleproject1.app.secrets import SECRET_ALLOWLIST

    if not path.is_file():
        raise SettingsError(f"env file not found: {path}")
    raw = dotenv_values(path)
    out: dict[str, str] = {}
    for key, value in raw.items():
        if not key or value is None or str(value).strip() == "":
            continue
        if key.startswith(ENV_PREFIX) or key in SECRET_ALLOWLIST:
            out[str(key)] = str(value)
    return out


class Settings(BaseSettings):
    """Composition-root settings. Not a trading configuration surface."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,
        env_ignore_empty=True,
        nested_model_default_partial_update=True,
        env_file=None,
        # Default env source is replaced in settings_customise_sources so
        # unprefixed process env cannot leak in.
        enable_decoding=True,
    )

    app: AppSection = Field(default_factory=AppSection)
    safety: SafetySection = Field(default_factory=SafetySection)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    logging: LoggingSection = Field(default_factory=LoggingSection)
    clock: ClockSection = Field(default_factory=ClockSection)
    identity: IdentitySection = Field(default_factory=IdentitySection)
    mt5: Mt5Section = Field(default_factory=Mt5Section)
    persistence: PersistenceSection = Field(default_factory=PersistenceSection)
    telegram: TelegramSection = Field(default_factory=TelegramSection)
    model_registry: ModelRegistrySection = Field(default_factory=ModelRegistrySection)
    notifications: NotificationsSection = Field(default_factory=NotificationsSection)
    modules: ModulesSection = Field(default_factory=ModulesSection)
    health: HealthSection = Field(default_factory=HealthSection)
    diagnostics: DiagnosticsSection = Field(default_factory=DiagnosticsSection)
    paths: PathsSection = Field(default_factory=PathsSection)
    pm2: Pm2Section = Field(default_factory=Pm2Section)
    pm3_strategy_engine: Pm3StrategySection = Field(default_factory=Pm3StrategySection)
    pm3_forecasting: Pm3ForecastingSection = Field(default_factory=Pm3ForecastingSection)
    pm4_risk_gate: Pm4RiskGateSection = Field(default_factory=Pm4RiskGateSection)
    pm5_execution: Pm5ExecutionSection = Field(default_factory=Pm5ExecutionSection)
    pm6_post_trade: Pm6PostTradeSection = Field(default_factory=Pm6PostTradeSection)
    pm7_persistence: Pm7PersistenceSection = Field(default_factory=Pm7PersistenceSection)
    pm8_operator: Pm8OperatorSection = Field(default_factory=Pm8OperatorSection)
    pm8_persistence: Pm8PersistenceSection = Field(default_factory=Pm8PersistenceSection)
    profile: ProfileName = ProfileName.DEMO
    cli_mode: str = "doctor"
    config_path: str | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Drop default env_settings / dotenv_settings: they would scan os.environ
        # and dotenv without an allowlist. load_settings binds explicit sources.
        return (init_settings, file_secret_settings)

    @field_validator("cli_mode")
    @classmethod
    def _cli(cls, value: str) -> str:
        if value not in _CLI_MODES:
            raise ValueError(f"unknown cli_mode {value!r}")
        return value

    @field_validator("profile", mode="before")
    @classmethod
    def _profile(cls, value: Any) -> Any:
        if value is None or value == "":
            return ProfileName.DEMO
        return parse_profile(value)

    @model_validator(mode="after")
    def _refuse_live_and_missing_secrets(self) -> Settings:
        if self.safety.live_trading_enabled:
            raise LiveTradingDisabledError("LIVE_TRADING_ENABLED=true")
        if self.safety.trading_mode == "live":
            raise LiveTradingDisabledError("TRADING_MODE=live")
        if self.cli_mode == "live":
            raise LiveTradingDisabledError("CLI mode=live")
        if self.profile is ProfileName.LIVE:
            raise LiveTradingDisabledError("profile=live")
        if self.mt5.enabled and self.mt5.account_kind != "demo":
            raise SettingsError("MT5 account_kind must be demo")
        if self.mt5.enabled and not self.mt5.password:
            raise SettingsError("MT5 is enabled but password secret is missing")
        if self.telegram.enabled:
            raise SettingsError("Telegram Bot API is refused; telegram.enabled cannot be true")
        if self.telegram.enabled and not self.telegram.token:
            raise SettingsError("Telegram is enabled but token secret is missing")
        if self.persistence.enabled and not self.persistence.dsn:
            raise SettingsError("Persistence is enabled but BOTMODULEPROJECT1_DATABASE_URL is missing")
        policy = self.profile_policy
        if self.mt5.enabled and not policy.allows_mt5_demo_network:
            raise SettingsError(
                f"profile {self.profile.value} forbids MT5 network operations"
            )
        validate_feature_flags(self.feature_flags, self.profile)
        return self

    @property
    def profile_policy(self) -> ProfilePolicy:
        return policy_for(self.profile)

    def feature_catalog(self) -> tuple[FeatureFlag, ...]:
        return self.feature_flags.catalog(self.profile)

    def public_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data.pop("feature_flags", None)
        data["feature_flags"] = self.feature_flags.enabled_map()
        return redact_node(data)

    def fingerprint(self) -> str:
        payload = json.dumps(self.public_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _bound_settings_class(
    *,
    yaml_data: dict[str, Any],
    prefix_env: dict[str, Any],
    secret_data: dict[str, Any],
    flag_data: dict[str, Any],
) -> type[Settings]:
    class BoundSettings(Settings):
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                MappingSource(settings_cls, flag_data),
                MappingSource(settings_cls, prefix_env),
                MappingSource(settings_cls, secret_data),
                MappingSource(settings_cls, yaml_data),
            )

    return BoundSettings


def load_settings(
    *,
    config_path: str | Path | None = None,
    environ: dict[str, str] | None = None,
    cli_mode: str = "doctor",
    extra: dict[str, Any] | None = None,
    profile: str | ProfileName | None = None,
    env_file: str | Path | None = None,
    enforce_python: bool = True,
) -> Settings:
    """Load YAML + allowlisted env + optional dotenv, then validate."""
    if enforce_python:
        assert_python_version()

    env: dict[str, str] = dict(environ if environ is not None else os.environ)
    if env_file is not None:
        env = {**load_dotenv_allowlisted(Path(env_file)), **env}

    yaml_data: dict[str, Any] = {}
    path: Path | None = Path(config_path) if config_path else None
    if path is not None:
        yaml_data = load_composed_yaml(path)
        yaml_data["config_path"] = str(path)

    prefix_env = nested_from_prefixed_env(env)
    # feature_flags from prefixed nested env already sit in prefix_env; dedicated
    # source still records env_opt_in and enable_* aliases.
    secret_data = secrets_from_environ(env)
    flag_data = feature_flags_from_environ(env)

    init_kwargs: dict[str, Any] = {"cli_mode": cli_mode}
    if path is not None:
        init_kwargs["config_path"] = str(path)
    if profile is not None:
        init_kwargs["profile"] = parse_profile(profile)
    if extra:
        init_kwargs = deep_merge(init_kwargs, extra)

    bound = _bound_settings_class(
        yaml_data=yaml_data,
        prefix_env=prefix_env,
        secret_data=secret_data,
        flag_data=flag_data,
    )
    try:
        return bound(**init_kwargs)
    except (LiveTradingDisabledError, SettingsError):
        raise
    except Exception as exc:
        from pydantic import ValidationError

        if isinstance(exc, ValidationError):
            raise SettingsError(str(exc)) from exc
        raise SettingsError(str(exc)) from exc

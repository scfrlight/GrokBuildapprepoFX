"""Typed settings. Secrets are SecretStr; live trading fails closed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

from botmoduleproject1.app.exceptions import LiveTradingDisabledError, SettingsError

CliMode = Literal[
    "test",
    "doctor",
    "paper",
    "live",
    "backfill",
    "demo",
    "observe-only",
    "research",
    "backtest",
    "live-disabled",
]

TradingMode = Literal[
    "test",
    "doctor",
    "backtest",
    "research",
    "demo",
    "paper",
    "observe-only",
    "live-disabled",
    "live",
]


class AppSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = "BotModuleProject1"
    environment: str = "local"
    timezone: Literal["UTC"] = "UTC"
    default_symbol: str = "EURUSD"


class SafetySection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trading_mode: TradingMode = "demo"
    live_trading_enabled: bool = False
    fail_closed: bool = True
    on_unknown_state: Literal["observe-only", "halt"] = "observe-only"
    on_stale_data: Literal["observe-only", "halt"] = "observe-only"
    on_incomplete_recovery: Literal["halt"] = "halt"
    on_ledger_inconsistency: Literal["halt"] = "halt"
    require_preflight: bool = True
    require_readiness: bool = True
    require_recovery: bool = True
    require_risk_ready_before_orders: bool = True


class FeatureFlags(BaseModel):
    model_config = ConfigDict(extra="ignore")

    strategy_engine: bool = False
    forecasting: bool = False
    risk_engine: bool = False
    execution: bool = False
    telegram: bool = False
    fine_tune_studio: bool = False


class LoggingSection(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_output: bool = Field(default=True, alias="json")
    redact_secrets: bool = True


class ClockSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: Literal["system", "fake"] = "system"
    aware: bool = True
    utc_only: bool = True


class IdentitySection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    require_event_id: bool = True
    require_correlation_id: bool = True
    require_causation_id: bool = True
    require_idempotency_key_on_commands: bool = True


class Mt5Section(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    account_kind: Literal["demo"] = "demo"
    terminal_path_env: str = "MT5_TERMINAL_PATH"
    login_env: str = "MT5_LOGIN"
    password_env: str = "MT5_PASSWORD"
    server_env: str = "MT5_SERVER"
    login: str | None = None
    password: SecretStr | None = None
    server: str | None = None
    terminal_path: str | None = None


class PersistenceSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    dsn_env: str = "DATABASE_URL"
    dsn: SecretStr | None = None
    api_is_sole_durable_path: bool = True


class TelegramSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    token_env: str = "TELEGRAM_BOT_TOKEN"
    chat_id_env: str = "TELEGRAM_CHAT_ID"
    allowed_user_ids_env: str = "TELEGRAM_ALLOWED_USER_IDS"
    token: SecretStr | None = None
    chat_id: str | None = None


class ModelRegistrySection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    uri_env: str = "MODEL_REGISTRY_URI"
    uri: str | None = None


class NotificationsSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = False


class ModulesSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    load_policy: Literal["manual", "discover"] = "manual"
    allowlist: tuple[str, ...] = ()
    denylist: tuple[str, ...] = ()


class HealthSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fail_on_critical: bool = True
    include_non_critical_in_ready: bool = False


class DiagnosticsSection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool = True
    heartbeat_seconds: float = Field(default=5.0, gt=0)


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

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
    cli_mode: CliMode = "doctor"
    config_path: str | None = None

    @field_validator("app")
    @classmethod
    def _tz(cls, value: AppSection) -> AppSection:
        if value.timezone != "UTC":
            raise ValueError("timezone must be UTC (ADR-003)")
        return value

    @model_validator(mode="after")
    def _refuse_live(self) -> Settings:
        if self.safety.live_trading_enabled:
            raise LiveTradingDisabledError("LIVE_TRADING_ENABLED=true")
        if self.safety.trading_mode == "live":
            raise LiveTradingDisabledError("TRADING_MODE=live")
        if self.cli_mode == "live":
            raise LiveTradingDisabledError("CLI mode=live")
        if self.mt5.enabled and self.mt5.account_kind != "demo":
            raise SettingsError("MT5 account_kind must be demo")
        if self.mt5.enabled and not self.mt5.password:
            raise SettingsError("MT5 is enabled but password secret is missing")
        if self.telegram.enabled and not self.telegram.token:
            raise SettingsError("Telegram is enabled but token secret is missing")
        if self.persistence.enabled and not self.persistence.dsn:
            raise SettingsError("Persistence is enabled but DATABASE_URL is missing")
        return self

    def public_dict(self) -> dict[str, Any]:
        """Redacted snapshot: secrets become present/absent, never values."""
        data = self.model_dump(mode="json")
        _redact(data)
        return data

    def fingerprint(self) -> str:
        payload = json.dumps(self.public_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _redact(node: Any) -> None:
    secret_keys = {"password", "token", "dsn", "secret"}
    if isinstance(node, dict):
        for key, value in list(node.items()):
            lowered = str(key).lower()
            if any(s in lowered for s in secret_keys):
                node[key] = "present" if value not in (None, "", {}) else "absent"
            else:
                _redact(value)
    elif isinstance(node, list):
        for item in node:
            _redact(item)


def _bind_secrets(data: dict[str, Any], environ: dict[str, str]) -> None:
    mt5 = data.setdefault("mt5", {})
    if isinstance(mt5, dict):
        mt5["login"] = environ.get(str(mt5.get("login_env", "MT5_LOGIN"))) or mt5.get("login")
        raw_pw = environ.get(str(mt5.get("password_env", "MT5_PASSWORD")))
        if raw_pw:
            mt5["password"] = raw_pw
        mt5["server"] = environ.get(str(mt5.get("server_env", "MT5_SERVER"))) or mt5.get("server")
        mt5["terminal_path"] = (
            environ.get(str(mt5.get("terminal_path_env", "MT5_TERMINAL_PATH")))
            or mt5.get("terminal_path")
        )
    persistence = data.setdefault("persistence", {})
    if isinstance(persistence, dict):
        dsn = environ.get(str(persistence.get("dsn_env", "DATABASE_URL")))
        if dsn:
            persistence["dsn"] = dsn
    telegram = data.setdefault("telegram", {})
    if isinstance(telegram, dict):
        token = environ.get(str(telegram.get("token_env", "TELEGRAM_BOT_TOKEN")))
        if token:
            telegram["token"] = token
        chat = environ.get(str(telegram.get("chat_id_env", "TELEGRAM_CHAT_ID")))
        if chat:
            telegram["chat_id"] = chat


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SettingsError(f"cannot read config file {path}: {exc}") from exc
    loaded = yaml.safe_load(raw) or {}
    if not isinstance(loaded, dict):
        raise SettingsError(f"config file {path} must be a mapping")
    return loaded


def load_settings(
    *,
    config_path: str | Path | None = None,
    environ: dict[str, str] | None = None,
    cli_mode: CliMode = "doctor",
    extra: dict[str, Any] | None = None,
) -> Settings:
    """Load YAML, overlay process env aliases, then validate."""
    import os

    env = dict(environ if environ is not None else os.environ)
    data: dict[str, Any] = {}
    path: Path | None = Path(config_path) if config_path else None
    if path is not None:
        data.update(load_yaml(path))
        data["config_path"] = str(path)

    safety = data.setdefault("safety", {})
    if isinstance(safety, dict):
        if "TRADING_MODE" in env:
            safety["trading_mode"] = env["TRADING_MODE"]
        if "LIVE_TRADING_ENABLED" in env:
            safety["live_trading_enabled"] = env["LIVE_TRADING_ENABLED"].lower() in {
                "1",
                "true",
                "yes",
            }
    app = data.setdefault("app", {})
    if isinstance(app, dict):
        if "APP_NAME" in env:
            app["name"] = env["APP_NAME"]
        if "ENVIRONMENT" in env:
            app["environment"] = env["ENVIRONMENT"]
        if "DEFAULT_SYMBOL" in env:
            app["default_symbol"] = env["DEFAULT_SYMBOL"]
    logging = data.setdefault("logging", {})
    if isinstance(logging, dict) and "LOG_LEVEL" in env:
        logging["level"] = env["LOG_LEVEL"].upper()

    _bind_secrets(data, env)
    data["cli_mode"] = cli_mode
    if extra:
        data.update(extra)

    try:
        return Settings.model_validate(data)
    except LiveTradingDisabledError:
        raise
    except Exception as exc:  # pydantic ValidationError among others
        if isinstance(exc, SettingsError):
            raise
        raise SettingsError(str(exc)) from exc

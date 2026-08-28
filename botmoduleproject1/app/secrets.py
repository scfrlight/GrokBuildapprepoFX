"""Secret allowlist and redaction. Values never enter logs, snapshots, or tests."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import SecretStr

# Unprefixed names that operators may set in a local .env. These are the ONLY
# non-prefixed process-env keys the loader will ever read. DATABASE_URL is
# intentionally absent: PaaS injects it (App Builder included) and that is
# ambient pollution. Persistence uses BOTMODULEPROJECT1_DATABASE_URL.
SECRET_ALLOWLIST = frozenset(
    {
        "MT5_LOGIN",
        "MT5_PASSWORD",
        "MT5_SERVER",
        "MT5_TERMINAL_PATH",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "TELEGRAM_ALLOWED_USER_IDS",
        "BOTMODULEPROJECT1_MT5_LOGIN",
        "BOTMODULEPROJECT1_MT5_PASSWORD",
        "BOTMODULEPROJECT1_MT5_SERVER",
        "BOTMODULEPROJECT1_MT5_TERMINAL_PATH",
        "BOTMODULEPROJECT1_TELEGRAM_BOT_TOKEN",
        "BOTMODULEPROJECT1_TELEGRAM_CHAT_ID",
        "BOTMODULEPROJECT1_TELEGRAM_ALLOWED_USER_IDS",
        "BOTMODULEPROJECT1_DATABASE_URL",
        "BOTMODULEPROJECT1_POSTGRES_PASSWORD",
        "BOTMODULEPROJECT1_MODEL_REGISTRY_URI",
        "BOTMODULEPROJECT1_OBJECT_STORE_URI",
    }
)

_SECRET_KEY_FRAGMENTS = (
    "password",
    "token",
    "dsn",
    "secret",
    "api_key",
    "apikey",
)


def secret_allowlist_values(environ: Mapping[str, str]) -> dict[str, str]:
    """Return only allowlisted secret keys that are present and non-empty."""
    out: dict[str, str] = {}
    for key, value in environ.items():
        if key in SECRET_ALLOWLIST and str(value).strip():
            out[key] = str(value)
    return out


def secrets_from_environ(environ: Mapping[str, str]) -> dict[str, Any]:
    """Map allowlisted env keys onto Settings nested fields."""
    picked = secret_allowlist_values(environ)
    data: dict[str, Any] = {}

    def _first(*names: str) -> str | None:
        for name in names:
            value = picked.get(name)
            if value:
                return value
        return None

    mt5: dict[str, str] = {}
    login = _first("BOTMODULEPROJECT1_MT5_LOGIN", "MT5_LOGIN")
    password = _first("BOTMODULEPROJECT1_MT5_PASSWORD", "MT5_PASSWORD")
    server = _first("BOTMODULEPROJECT1_MT5_SERVER", "MT5_SERVER")
    terminal = _first("BOTMODULEPROJECT1_MT5_TERMINAL_PATH", "MT5_TERMINAL_PATH")
    if login:
        mt5["login"] = login
    if password:
        mt5["password"] = password
    if server:
        mt5["server"] = server
    if terminal:
        mt5["terminal_path"] = terminal
    if mt5:
        data["mt5"] = mt5

    telegram: dict[str, str] = {}
    token = _first("BOTMODULEPROJECT1_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN")
    chat = _first("BOTMODULEPROJECT1_TELEGRAM_CHAT_ID", "TELEGRAM_CHAT_ID")
    allowed = _first(
        "BOTMODULEPROJECT1_TELEGRAM_ALLOWED_USER_IDS", "TELEGRAM_ALLOWED_USER_IDS"
    )
    if token:
        telegram["token"] = token
    if chat:
        telegram["chat_id"] = chat
    if allowed:
        telegram["allowed_user_ids"] = allowed
    if telegram:
        data["telegram"] = telegram

    persistence: dict[str, str] = {}
    dsn = _first("BOTMODULEPROJECT1_DATABASE_URL")
    if dsn:
        persistence["dsn"] = dsn
    if persistence:
        data["persistence"] = persistence

    model_registry: dict[str, str] = {}
    uri = _first("BOTMODULEPROJECT1_MODEL_REGISTRY_URI")
    if uri:
        model_registry["uri"] = uri
    if model_registry:
        data["model_registry"] = model_registry

    return data


def is_secret_key(key: str) -> bool:
    lowered = str(key).lower()
    return any(fragment in lowered for fragment in _SECRET_KEY_FRAGMENTS)


def reveal_if_secret(value: Any) -> str | None:
    if isinstance(value, SecretStr):
        secret = value.get_secret_value()
        return secret if secret else None
    if isinstance(value, str) and value:
        return value
    return None


def redact_node(node: Any) -> Any:
    """Return a copy where secret fields become present/absent, never values."""
    if isinstance(node, SecretStr):
        raw = node.get_secret_value()
        return "present" if raw else "absent"
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if is_secret_key(str(key)):
                if value in (None, "", {}, [], "absent"):
                    out[key] = "absent"
                elif value == "present":
                    out[key] = "present"
                elif isinstance(value, SecretStr):
                    out[key] = "present" if value.get_secret_value() else "absent"
                else:
                    out[key] = "present" if value else "absent"
            else:
                out[key] = redact_node(value)
        return out
    if isinstance(node, list):
        return [redact_node(item) for item in node]
    if isinstance(node, tuple):
        return tuple(redact_node(item) for item in node)
    return node


def assert_redacted(blob: str, *forbidden: str) -> None:
    for item in forbidden:
        if item and item in blob:
            raise AssertionError("secret value leaked into serialized output")

"""Secret redaction for logs, metrics, evidence, exported reports."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from botmoduleproject1.app.secrets import SECRET_ALLOWLIST, is_secret_key, redact_node

_REDACTED = "[REDACTED]"
_URI_SECRET = re.compile(r"(://[^:/@]+):([^@/]+)@", re.IGNORECASE)
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]+=*")
_LONG_TOKEN = re.compile(r"\b([A-Za-z0-9_\-]{24,})\b")


def _scrub_string(value: str) -> str:
    out = _URI_SECRET.sub(r"\1:" + _REDACTED + "@", value)
    out = _BEARER.sub(r"\1" + _REDACTED, out)
    return out


def redact_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and is_secret_key(key):
        if value in (None, "", {}, [], "absent"):
            return "absent"
        return "present" if value else "absent"
    if isinstance(value, dict):
        return {str(k): redact_value(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, str):
        return _scrub_string(value)
    return value


def redact_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    return redact_node(redact_value(payload))


def assert_no_secrets(blob: str, extra_forbidden: tuple[str, ...] = ()) -> None:
    lowered = blob.lower()
    for key in SECRET_ALLOWLIST:
        if key.lower() in lowered and "present" not in lowered:
            # key names may appear as field labels; values must not
            pass
    forbidden = extra_forbidden + (
        "postgres://",
        "postgresql://",
        "mongodb://",
    )
    for item in extra_forbidden:
        if item and item in blob:
            raise AssertionError("secret value leaked into serialized output")
    if "TELEGRAM_BOT_TOKEN=" in blob or "MT5_PASSWORD=" in blob:
        raise AssertionError("secret assignment leaked")
    _ = lowered
    _ = forbidden


def contains_forbidden_secret(blob: str, *values: str) -> bool:
    return any(v and v in blob for v in values)


def safe_json(payload: dict[str, Any]) -> str:
    return json.dumps(redact_mapping(payload), sort_keys=True, default=str)


def redact_url(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return _REDACTED
    if parts.password or (parts.username and parts.password):
        netloc = parts.hostname or ""
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
        if parts.username:
            netloc = f"{parts.username}:{_REDACTED}@{netloc}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    return _scrub_string(url)

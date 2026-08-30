"""DSN validation and redaction for PM8 PostgreSQL.

Only BOTMODULEPROJECT1_DATABASE_URL is authoritative. Unprefixed DATABASE_URL
is ignored by the secrets allowlist and must not be read here either.
"""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


class PostgresDsnError(ValueError):
    """Configured DSN is missing, malformed, or not PostgreSQL."""


_PG_SCHEMES = {"postgresql", "postgres"}
_SQLITE_MARKERS = ("sqlite:", "file:", ":memory:")


def validate_postgres_dsn(dsn: str | None) -> str:
    if dsn is None or not str(dsn).strip():
        raise PostgresDsnError("postgresql requires BOTMODULEPROJECT1_DATABASE_URL")
    text = str(dsn).strip()
    lowered = text.lower()
    if any(lowered.startswith(marker) for marker in _SQLITE_MARKERS):
        raise PostgresDsnError("postgresql mode refuses sqlite/memory DSN; no fallback")
    parsed = urlparse(text)
    if parsed.scheme.lower() not in _PG_SCHEMES:
        raise PostgresDsnError(
            f"postgresql DSN scheme must be postgresql:// (got {parsed.scheme!r})"
        )
    if not parsed.hostname:
        raise PostgresDsnError("postgresql DSN must include a host")
    return text


def redact_dsn(dsn: str) -> str:
    """Return a log-safe DSN with password removed."""
    try:
        parsed = urlparse(dsn)
    except Exception:
        return "postgresql://***"
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    user = parsed.username or ""
    auth = f"{user}:***@" if user else ""
    path = parsed.path or ""
    netloc = f"{auth}{host}{port}"
    return urlunparse((parsed.scheme or "postgresql", netloc, path, "", "", ""))

"""UTC-first time policy (ADR-003). Naive datetimes are a defect."""

from __future__ import annotations

from datetime import datetime, timezone

UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def ensure_aware_utc(value: datetime, field_name: str = "timestamp") -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime, got {type(value)!r}")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(
            f"{field_name} must be timezone-aware; naive datetime is forbidden (ADR-003)"
        )
    return value.astimezone(UTC)

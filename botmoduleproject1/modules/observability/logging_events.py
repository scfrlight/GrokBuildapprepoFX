"""Structured log events. UTC. Redacted metadata. Correlation fields required."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from botmoduleproject1.contracts.v1.observability import (
    ALLOWED_LOG_SYMBOLS,
    REQUIRED_LOG_FIELDS,
    ErrorCode,
    LogLevel,
    StructuredLogEvent,
)
from botmoduleproject1.contracts.v1.time import UTC, ensure_aware_utc, utc_now
from botmoduleproject1.modules.observability.redaction import redact_mapping


class LogSchemaError(ValueError):
    pass


def emit_event(
    *,
    event_name: str,
    module: str,
    sequence: int,
    profile: str,
    status: str,
    level: LogLevel = LogLevel.INFO,
    actor: str = "system",
    symbol: str | None = None,
    error_code: ErrorCode | None = None,
    correlation_id: UUID | None = None,
    causation_id: UUID | None = None,
    trace_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> StructuredLogEvent:
    if symbol is not None and symbol not in ALLOWED_LOG_SYMBOLS:
        raise LogSchemaError(f"symbol {symbol!r} is not on the allowlist")
    stamp = timestamp or utc_now()
    ensure_aware_utc(stamp, "timestamp")
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise LogSchemaError("timestamp must be timezone-aware UTC")
    if stamp.tzinfo != UTC and stamp.utcoffset() != stamp.astimezone(UTC).utcoffset():
        stamp = stamp.astimezone(UTC)
    event = StructuredLogEvent(
        timestamp=stamp.astimezone(UTC),
        level=level,
        event_name=event_name,
        module=module,
        sequence=sequence,
        correlation_id=correlation_id or uuid4(),
        causation_id=causation_id,
        trace_id=trace_id or uuid4(),
        actor=actor,
        profile=profile,
        symbol=symbol,
        status=status,
        error_code=error_code,
        metadata=redact_mapping(metadata or {}),
    )
    missing = [name for name in REQUIRED_LOG_FIELDS if not hasattr(event, name)]
    if missing:
        raise LogSchemaError(f"missing fields: {missing}")
    return event


def event_as_log_dict(event: StructuredLogEvent) -> dict[str, Any]:
    payload = event.model_dump(mode="json")
    payload["metadata"] = redact_mapping(payload.get("metadata") or {})
    return payload

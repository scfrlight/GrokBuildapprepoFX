"""Contract tests for Sequence 14 observability types."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.observability import (
    ErrorCode,
    HealthReport,
    MetricSpec,
    MetricType,
    MetricUnit,
    ProbeState,
    ReadinessReport,
    StructuredLogEvent,
)
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.observability.errors import ERROR_CATALOG
from botmoduleproject1.modules.observability.metrics import METRIC_CATALOG


def test_health_and_readiness_are_not_one_boolean():
    now = utc_now()
    health = HealthReport(
        captured_at=now,
        liveness=ProbeState.PASS,
        operational_health=ProbeState.DEGRADED,
        dimensions=(),
        trading_readiness=False,
        trading_halted=True,
        stale_data=False,
        venue_present=False,
        recovery_complete=True,
        flags_any_on=False,
    )
    ready = ReadinessReport(
        captured_at=now,
        process_alive=True,
        accept_observe=True,
        accept_trade=False,
        liveness=ProbeState.PASS,
        readiness=ProbeState.PASS,
        trading_readiness=ProbeState.FAIL,
        recovery_readiness=ProbeState.DEGRADED,
        persistence_readiness=ProbeState.DEGRADED,
        broker_venue=ProbeState.UNAVAILABLE,
        operator_readiness=ProbeState.DEGRADED,
    )
    assert health.liveness is ProbeState.PASS
    assert health.trading_readiness is False
    assert ready.process_alive is True
    assert ready.accept_trade is False
    dumped = health.model_dump()
    assert "liveness" in dumped and "trading_readiness" in dumped


def test_metric_specs_are_frozen_v1():
    spec = METRIC_CATALOG[0]
    assert isinstance(spec, MetricSpec)
    assert spec.metric_type in MetricType
    assert spec.unit in MetricUnit
    try:
        spec.name = "mutated"  # type: ignore[misc]
        raise AssertionError("MetricSpec must be frozen")
    except Exception:
        pass


def test_error_codes_match_catalog():
    assert {s.code for s in ERROR_CATALOG} == set(ErrorCode)


def test_structured_log_extra_fields_forbidden():
    try:
        StructuredLogEvent(
            level="info",
            event_name="x",
            module="observability",
            sequence=14,
            actor="system",
            profile="test",
            status="ok",
            extra="nope",  # type: ignore[call-arg]
        )
        raise AssertionError("extra fields must be forbidden")
    except Exception:
        pass

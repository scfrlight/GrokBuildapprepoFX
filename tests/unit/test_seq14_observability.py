"""Sequence 14 observability: logs, health, metrics, errors, safety."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.app.bootstrap import bootstrap
from botmoduleproject1.app.exceptions import LiveTradingDisabledError
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.sequence_gate import CANONICAL_SEQUENCES
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.cli.entrypoint import main
from botmoduleproject1.contracts.v1.observability import (
    ALLOWED_LOG_SYMBOLS,
    ErrorCode,
    LogLevel,
    ProbeState,
    REQUIRED_LOG_FIELDS,
)
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.observability.errors import ERROR_CATALOG, ERROR_BY_CODE, public_message
from botmoduleproject1.modules.observability.health_model import TRANSITION_TABLE, evaluate
from botmoduleproject1.modules.observability.logging_events import LogSchemaError, emit_event, event_as_log_dict
from botmoduleproject1.modules.observability.metrics import (
    CATALOG_BY_NAME,
    METRIC_CATALOG,
    CardinalityError,
    MetricRegistry,
    UnknownMetricError,
)
from botmoduleproject1.modules.observability.module import ObservabilityModule
from botmoduleproject1.modules.observability.redaction import contains_forbidden_secret, redact_mapping, safe_json
from botmoduleproject1.modules.observability.runbooks import REQUIRED_RUNBOOK_COUNT, RUNBOOKS, RUNBOOK_BY_ID

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"
BASE_YAML = ROOT / "configs" / "base.example.yaml"


def _settings():
    return load_settings(config_path=TEST_YAML, environ={}, cli_mode="observe")


def test_canonical_sequence_14():
    assert CANONICAL_SEQUENCES[14] == "observability_operations_documentation"
    assert CANONICAL_SEQUENCES[11] == "mt5_execution_engine"
    assert not CANONICAL_SEQUENCES[11].startswith("pm6")


def test_structured_log_schema_and_utc():
    event = emit_event(
        event_name="health.evaluated",
        module="observability",
        sequence=14,
        profile="test",
        status="degraded",
        actor="doctor",
        symbol="EURUSD",
        error_code=ErrorCode.STALE_DATA_ERROR,
        correlation_id=uuid4(),
        causation_id=uuid4(),
        trace_id=uuid4(),
        metadata={"note": "ok"},
    )
    payload = event_as_log_dict(event)
    for field in REQUIRED_LOG_FIELDS:
        assert field in payload
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.utcoffset().total_seconds() == 0
    assert event.symbol in ALLOWED_LOG_SYMBOLS


def test_naive_timestamp_rejected():
    with pytest.raises((LogSchemaError, ValueError)):
        emit_event(
            event_name="x",
            module="observability",
            sequence=14,
            profile="test",
            status="ok",
            timestamp=datetime.now(),  # naive
        )


def test_unknown_symbol_rejected():
    with pytest.raises(LogSchemaError):
        emit_event(
            event_name="x",
            module="observability",
            sequence=14,
            profile="test",
            status="ok",
            symbol="DOGEUSD",
        )


def test_correlation_causation_propagation():
    corr = uuid4()
    cause = uuid4()
    trace = uuid4()
    first = emit_event(
        event_name="a",
        module="observability",
        sequence=14,
        profile="test",
        status="ok",
        correlation_id=corr,
        trace_id=trace,
    )
    second = emit_event(
        event_name="b",
        module="observability",
        sequence=14,
        profile="test",
        status="ok",
        correlation_id=first.correlation_id,
        causation_id=first.correlation_id,
        trace_id=first.trace_id,
    )
    assert second.correlation_id == corr
    assert second.causation_id == first.correlation_id
    assert second.trace_id == trace
    del cause


def test_secret_redaction_in_log_metadata():
    secret = "super-secret-token-value-12345"
    event = emit_event(
        event_name="leak-attempt",
        module="observability",
        sequence=14,
        profile="test",
        status="ok",
        metadata={
            "password": secret,
            "telegram_bot_token": secret,
            "note": "safe",
            "dsn": "postgres://user:hunter2@localhost/db",
        },
    )
    blob = json.dumps(event_as_log_dict(event))
    assert secret not in blob
    assert "hunter2" not in blob
    assert event.metadata["password"] == "present"
    assert event.metadata["note"] == "safe"
    assert contains_forbidden_secret(blob, secret) is False


def test_redact_mapping_nested():
    out = redact_mapping({"a": {"api_key": "abcd", "ok": 1}, "list": [{"token": "zzz"}]})
    assert out["a"]["api_key"] == "present"
    assert out["a"]["ok"] == 1
    assert out["list"][0]["token"] == "present"


def test_metric_catalog_covers_required_names():
    names = {s.name for s in METRIC_CATALOG}
    required = {
        "botmodule.persistence.latency_ms",
        "botmodule.persistence.errors",
        "botmodule.outbox.backlog",
        "botmodule.outbox.relay_lag_ms",
        "botmodule.inbox.dedupe_hits",
        "botmodule.dead_letter.count",
        "botmodule.projection.lag",
        "botmodule.projection.rebuild_duration_ms",
        "botmodule.replay.duration_ms",
        "botmodule.snapshot.age_seconds",
        "botmodule.checkpoint.age_seconds",
        "botmodule.reconciliation.mismatch_count",
        "botmodule.reconciliation.degraded_count",
        "botmodule.risk.denials",
        "botmodule.execution.simulation_attempts",
        "botmodule.execution.duplicate_attempts",
        "botmodule.retry.count",
        "botmodule.market.stale_events",
        "botmodule.incidents.active",
        "botmodule.incidents.unresolved",
        "botmodule.operator.actions",
        "botmodule.operator.denied_actions",
        "botmodule.health.transitions",
        "botmodule.shutdown.duration_ms",
        "botmodule.recovery.duration_ms",
    }
    assert required <= names
    for spec in METRIC_CATALOG:
        assert spec.safe_default == 0.0
        assert "bounded" in spec.cardinality


def test_metric_name_stability():
    assert list(CATALOG_BY_NAME) == [s.name for s in METRIC_CATALOG]


def test_metric_cardinality_limits():
    reg = MetricRegistry()
    with pytest.raises(CardinalityError):
        reg.inc("botmodule.risk.denials", order_text="BUY EURUSD 1.0")
    with pytest.raises(CardinalityError):
        reg.set("botmodule.persistence.errors", 1, error_code="x" * 80)
    with pytest.raises(CardinalityError):
        reg.set("botmodule.health.transitions", 1, password="secret")
    with pytest.raises(UnknownMetricError):
        reg.inc("botmodule.unknown.metric")
    sample = reg.inc("botmodule.risk.denials", module="pm4_risk_gate", outcome="denied")
    assert sample.value == 1.0


def test_liveness_readiness_separation():
    settings = _settings()
    health, ready = evaluate(settings, lifecycle=LifecycleState.DEGRADED)
    assert ready.process_alive is True
    assert ready.accept_observe is True
    assert ready.accept_trade is False
    assert health.trading_readiness is False
    assert ready.liveness is ProbeState.PASS
    assert ready.trading_readiness is ProbeState.FAIL
    assert ready.broker_venue is ProbeState.UNAVAILABLE


def test_venue_absent_is_not_pass():
    settings = _settings()
    _health, ready = evaluate(settings, lifecycle=LifecycleState.DEGRADED)
    assert ready.broker_venue is ProbeState.UNAVAILABLE
    assert ready.broker_venue is not ProbeState.PASS


def test_recovery_incomplete_not_trade_ready():
    settings = _settings()
    health, ready = evaluate(settings, lifecycle=LifecycleState.WIRED)
    assert health.recovery_complete is False
    assert health.trading_readiness is False
    assert ready.recovery_readiness is ProbeState.DEGRADED


def test_stale_data_safe_stop():
    settings = _settings()
    health, ready = evaluate(settings, lifecycle=LifecycleState.DEGRADED, stale_data=True)
    assert health.stale_data is True
    assert health.trading_readiness is False
    assert ready.accept_trade is False
    assert any("stale" in r for r in health.reasons)


def test_integrity_fail_persistence_not_ready():
    settings = _settings()
    health, ready = evaluate(
        settings, lifecycle=LifecycleState.DEGRADED, integrity_ok=False, persistence_enabled=True
    )
    assert ready.persistence_readiness is ProbeState.FAIL
    assert health.trading_readiness is False


def test_all_flags_off_trading_false():
    settings = load_settings(config_path=BASE_YAML, environ={}, cli_mode="doctor")
    assert all(v is False for v in settings.feature_flags.enabled_map().values())
    health, ready = evaluate(settings, lifecycle=LifecycleState.DEGRADED)
    assert health.flags_any_on is False
    assert health.trading_readiness is False
    assert ready.accept_trade is False


def test_transition_table_covers_critical_rows():
    keys = {(row[0], row[1]) for row in TRANSITION_TABLE}
    assert ("trading_readiness", "sequence_14_scope") in keys
    assert ("broker_venue", "mt5_absent") in keys
    assert ("liveness", "process_assembled") in keys
    for _dim, _cond, state, halt in TRANSITION_TABLE:
        if _dim == "trading_readiness":
            assert state is ProbeState.FAIL
            assert halt is True


def test_error_taxonomy_complete_and_public_safe():
    codes = {spec.code for spec in ERROR_CATALOG}
    assert set(ErrorCode) == codes
    for spec in ERROR_CATALOG:
        assert spec.public_safe_message
        assert "traceback" not in spec.public_safe_message.lower()
        assert "/" not in spec.public_safe_message or "3.11" in spec.public_safe_message
        assert "password" not in spec.public_safe_message.lower()
        assert "token" not in spec.public_safe_message.lower()
        assert ERROR_BY_CODE[spec.code] is spec
    assert "Internal error" in public_message(ErrorCode.UNEXPECTED_INTERNAL_ERROR)
    halt_codes = {s.code for s in ERROR_CATALOG if s.trading_must_halt}
    assert ErrorCode.UNSAFE_OPERATION in halt_codes
    assert ErrorCode.BROKER_UNAVAILABLE in halt_codes


def test_runbooks_have_twelve_fields_and_count():
    assert len(RUNBOOKS) == REQUIRED_RUNBOOK_COUNT
    required_ids = {
        "RB-STARTUP-CLEAN",
        "RB-SHUTDOWN-SAFE",
        "RB-STALE-MARKET-DATA",
        "RB-PERSISTENCE-UNAVAILABLE",
        "RB-LEDGER-INTEGRITY",
        "RB-OUTBOX-BACKLOG",
        "RB-DUPLICATE-CALLBACK",
        "RB-RECONCILIATION-DEGRADED",
        "RB-RECOVERY-AFTER-RESTART",
        "RB-BACKUP-VERIFICATION",
        "RB-RESTORE-VERIFICATION",
        "RB-FAILED-MIGRATION",
        "RB-FAILED-PROJECTION",
        "RB-MT5-UNAVAILABLE",
        "RB-SIM-EXEC-REJECTION",
        "RB-KILL-SWITCH",
        "RB-OPERATOR-PERMISSION-DENIAL",
        "RB-INCIDENT-ESCALATION",
        "RB-SECRET-EXPOSURE",
        "RB-CORRUPTED-EVIDENCE",
    }
    assert required_ids <= set(RUNBOOK_BY_ID)
    for rb in RUNBOOKS:
        assert rb.trigger and rb.symptoms and rb.safety_classification
        assert rb.automatic_system_behavior
        assert rb.operator_inspection_commands
        assert rb.prohibited_operator_actions
        assert rb.recovery_steps and rb.verification_steps and rb.rollback_steps
        assert rb.evidence_to_preserve and rb.closure_criteria and rb.escalation_criteria
        assert "Do not send live" in " ".join(rb.prohibited_operator_actions)
        for cmd in rb.operator_inspection_commands:
            tokens = cmd.split()
            for i, tok in enumerate(tokens):
                if tok.startswith("tests/") or tok.startswith("scripts/") or tok.startswith("configs/") or tok.startswith("docs/"):
                    path = tok.split("::", 1)[0]
                    assert (ROOT / path).exists(), f"{rb.runbook_id} inspection path missing: {path}"
                if tok in {"doctor", "observe", "health", "live"} and i > 0 and "botmoduleproject1" in tokens[i - 1]:
                    pass


def test_observability_module_bound_and_snapshot():
    settings, container, runtime = bootstrap(config_path=TEST_YAML, cli_mode="observe", environ={})
    obs = container.registry.get("observability").instance
    assert isinstance(obs, ObservabilityModule)
    snap = obs.snapshot(settings, lifecycle=runtime.container.lifecycle.state)
    assert snap.sequence == 14
    assert snap.health.trading_readiness is False
    assert snap.readiness.accept_trade is False
    assert snap.telegram_bound is False
    assert snap.live_trading_enabled is False
    assert all(v is False for v in snap.flags.values())
    assert snap.metric_catalog_count == len(METRIC_CATALOG)
    assert snap.runbook_count == 20
    blob = snap.model_dump_json()
    assert "NOT TRADE READY" in blob or snap.kernel_note.startswith("NOT TRADE READY")
    runtime.stop()


def test_observe_cli_json(capsys):
    code = main(
        [
            "observe",
            "--profile",
            "test",
            "--config",
            str(TEST_YAML),
            "--json",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    start = out.find("{")
    assert start >= 0, out[:500]
    payload = json.loads(out[start:])
    assert payload["health"]["trading_readiness"] is False
    assert payload["readiness"]["accept_trade"] is False
    assert payload["readiness"]["broker_venue"] == "unavailable"


def test_live_still_fail_closed():
    with pytest.raises(LiveTradingDisabledError):
        bootstrap(config_path=TEST_YAML, cli_mode="live", environ={})
    assert main(["live", "--profile", "live", "--config", str(TEST_YAML)]) == 2


def test_telegram_transport_still_refused():
    from botmoduleproject1.adapters.telegram.transport import RealTelegramTransport
    from botmoduleproject1.app.exceptions import FeatureFlagError

    with pytest.raises(FeatureFlagError, match="refused"):
        RealTelegramTransport()


def test_no_pm6_execution_package():
    import botmoduleproject1.modules as mods

    root = Path(mods.__file__).parent
    assert not (root / "pm6_execution").exists()
    from botmoduleproject1.modules.mt5_execution_engine import DemoRouter

    assert DemoRouter is not None

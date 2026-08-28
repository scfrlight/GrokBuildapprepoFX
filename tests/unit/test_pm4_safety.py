"""Critical safety: deny-by-default, no orders, no PM5, no bypass, no lookahead."""

from __future__ import annotations

import inspect
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution, NullRiskGate
from botmoduleproject1.contracts.v1.execution import OrderRequest
from botmoduleproject1.contracts.v1.risk import (
    HandoffEligibility,
    RiskPublicationBundle,
    RiskRejectionReason,
    RiskVerdictStatus,
)
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.modules.pm4_risk_gate.module import PM4RiskGateModule
from tests.unit.pm4_support import (
    AS_OF,
    admitted_bundle,
    make_candidate,
    make_exposure,
    make_forecast,
    make_intent,
    risk_module,
)

ROOT = Path(__file__).resolve().parents[2]


def test_deny_by_default_without_upstream_artifacts() -> None:
    gate = risk_module()
    verdict = gate.evaluate(make_intent(), make_exposure())
    assert verdict.status is RiskVerdictStatus.DENY
    assert RiskRejectionReason.MISSING_FORECAST in verdict.reasons
    assert RiskRejectionReason.MISSING_CANDIDATE in verdict.reasons
    assert verdict.allows_execution is False


def test_flag_off_denies() -> None:
    gate = risk_module(enabled=False)
    bundle = admitted_bundle(gate, key="flag-off")
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    assert RiskRejectionReason.FEATURE_DISABLED in bundle.verdict.reasons


def test_null_risk_gate_still_denies_when_flag_off() -> None:
    settings = load_settings(config_path=ROOT / "configs" / "test.example.yaml", environ={})
    container = build_container(settings)
    risk = container.registry.get("pm4_risk").instance
    assert isinstance(risk, NullRiskGate)
    verdict = risk.evaluate(make_intent(key="null"), make_exposure())
    assert verdict.status is RiskVerdictStatus.DENY
    assert verdict.allows_execution is False


def test_allow_still_does_not_create_order_or_call_pm5() -> None:
    bundle = admitted_bundle()
    assert bundle.verdict.status is RiskVerdictStatus.ALLOW
    assert bundle.execution_permitted is False
    assert bundle.handoff_eligibility is HandoffEligibility.ELIGIBLE_PENDING_PM5
    assert "OrderRequest" not in bundle.model_dump_json()
    src = inspect.getsource(PM4RiskGateModule)
    assert "OrderRequest" not in src
    assert "submit(" not in src
    exec_adapter = DisabledExecution()
    with pytest.raises(ExecutionDisabledError):
        exec_adapter.submit(
            OrderRequest(
                causation_id=bundle.verdict.event_id,
                idempotency_key="nope",
                occurred_at=AS_OF,
                intent_id=bundle.intent_id,
                risk_verdict_id=bundle.verdict.verdict_id,
                symbol="EURUSD",
                direction=Direction.BUY,
                entry_type=__import__(
                    "botmoduleproject1.contracts.v1.strategy", fromlist=["EntryType"]
                ).EntryType.MARKET,
                volume=Decimal("0.01"),
            )
        )


def test_publication_rejects_execution_permitted_true() -> None:
    bundle = admitted_bundle(key="exec-false")
    payload = bundle.model_dump()
    payload["execution_permitted"] = True
    with pytest.raises(Exception, match="execution_permitted"):
        RiskPublicationBundle(**payload)


def test_no_future_information() -> None:
    gate = risk_module()
    candidate = make_candidate(as_of=AS_OF + timedelta(hours=5))
    intent = make_intent(key="future", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    assert RiskRejectionReason.LOOKAHEAD in bundle.verdict.reasons


def test_stale_artifact_rejected() -> None:
    gate = risk_module()
    stale = AS_OF - timedelta(hours=20)
    candidate = make_candidate(as_of=stale)
    intent = make_intent(key="stale", occurred_at=stale, candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent, occurred_at=stale)
    bundle = gate.evaluate_intent(
        intent, make_exposure(as_of=stale), candidate=candidate, forecast=forecast
    )
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    assert RiskRejectionReason.STALE_DATA in bundle.verdict.reasons


def test_missing_forecast_validity_diagnostics_denied() -> None:
    gate = risk_module()
    candidate = make_candidate()
    intent = make_intent(key="nodiag", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent, diagnostics={})
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    assert RiskRejectionReason.FORECAST_INVALID in bundle.verdict.reasons


def test_pm3_cannot_bypass_via_evaluate_protocol() -> None:
    gate = risk_module()
    intent = make_intent(key="bypass")
    verdict = gate.evaluate(intent, make_exposure())
    assert verdict.status is not RiskVerdictStatus.ALLOW
    assert verdict.allows_execution is False


def test_risk_publication_bundle_is_not_an_order() -> None:
    bundle = admitted_bundle(key="not-order")
    assert isinstance(bundle, RiskPublicationBundle)
    assert bundle.producer == "pm4_risk_gate"
    assert bundle.verdict.producer == "pm4_risk_gate"

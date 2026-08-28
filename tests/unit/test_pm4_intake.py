"""Intake validation: schema, freshness, consistency, duplicates."""

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.pm2 import QualificationStateName
from botmoduleproject1.contracts.v1.risk import RiskRejectionReason, RiskVerdictStatus
from botmoduleproject1.contracts.v1.strategy import Direction
from tests.unit.pm4_support import (
    admitted_bundle,
    make_candidate,
    make_exposure,
    make_forecast,
    make_intent,
    risk_module,
)


def test_symbol_mismatch_denied() -> None:
    gate = risk_module()
    candidate = make_candidate(symbol="GBPUSD")
    intent = make_intent(key="mismatch", symbol="EURUSD", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert bundle.verdict.status is RiskVerdictStatus.DENY
    assert RiskRejectionReason.SYMBOL_MISMATCH in bundle.verdict.reasons


def test_handoff_ineligible_denied() -> None:
    gate = risk_module()
    candidate = make_candidate(handoff=False)
    intent = make_intent(key="nohand", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert RiskRejectionReason.HANDOFF_INELIGIBLE in bundle.verdict.reasons


def test_suppressed_qualification_denied() -> None:
    gate = risk_module()
    candidate = make_candidate(state=QualificationStateName.SUPPRESSED)
    intent = make_intent(key="supp", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert bundle.verdict.status is RiskVerdictStatus.DENY


def test_flat_intent_denied() -> None:
    gate = risk_module()
    candidate = make_candidate()
    intent = make_intent(key="flat", direction=Direction.FLAT, candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert RiskRejectionReason.INVALID_INTENT in bundle.verdict.reasons


def test_missing_stop_denied() -> None:
    gate = risk_module()
    candidate = make_candidate()
    intent = make_intent(key="nostop", candidate_id=candidate.candidate_id)
    intent = intent.model_copy(update={"exit_plan": None})
    forecast = make_forecast(intent)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert RiskRejectionReason.STOP_MISSING in bundle.verdict.reasons


def test_forecast_intent_id_mismatch_denied() -> None:
    gate = risk_module()
    candidate = make_candidate()
    intent = make_intent(key="fxid", candidate_id=candidate.candidate_id)
    other = make_intent(key="other")
    forecast = make_forecast(other)
    bundle = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert RiskRejectionReason.MALFORMED in bundle.verdict.reasons


def test_duplicate_idempotency_returns_same_verdict() -> None:
    gate = risk_module()
    first = admitted_bundle(gate, key="dup-1")
    candidate = make_candidate()
    intent = make_intent(key="dup-1", candidate_id=candidate.candidate_id)
    intent = intent.model_copy(update={"intent_id": first.intent_id})
    forecast = make_forecast(intent)
    second = gate.evaluate_intent(
        intent, make_exposure(), candidate=candidate, forecast=forecast, mid_price=Decimal("1.10000")
    )
    assert second.verdict.verdict_id == first.verdict.verdict_id
    assert second.bundle_id == first.bundle_id

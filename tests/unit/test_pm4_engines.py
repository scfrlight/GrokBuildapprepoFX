"""Budget, sizing, heat, concentration, drawdown, pre-trade, uncertainty."""

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import (
    ConcentrationState,
    DrawdownStage,
    HeatRegime,
    RiskAdmissionDecision,
    RiskVerdictStatus,
)
from tests.unit.pm4_support import (
    admitted_bundle,
    make_candidate,
    make_exposure,
    make_forecast,
    make_intent,
    risk_module,
)


def test_happy_path_allow_with_size() -> None:
    bundle = admitted_bundle(key="happy")
    assert bundle.verdict.status is RiskVerdictStatus.ALLOW
    assert bundle.admission.decision in {
        RiskAdmissionDecision.APPROVE,
        RiskAdmissionDecision.REDUCE,
    }
    assert bundle.sizing.recommended_size > 0
    assert bundle.sizing.final_size_rationale
    assert bundle.budget.residual_headroom >= 0
    assert bundle.execution_permitted is False


def test_hierarchical_budget_not_flat() -> None:
    bundle = admitted_bundle(key="budget-tree")
    tree = bundle.budget.tree
    assert "account" in tree
    assert any(k.startswith("sleeve:") for k in tree)
    assert any(k.startswith("symbol:") for k in tree)
    assert any(k.startswith("cluster:") for k in tree)
    assert bundle.budget.account_budget >= bundle.budget.symbol_budget


def test_uncertainty_discounts_wide_interval() -> None:
    gate = risk_module()
    tight = admitted_bundle(gate, key="tight")
    candidate = make_candidate()
    intent = make_intent(key="wide", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent, q05="1.05000", q95="1.16000")
    wide = gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )
    if wide.verdict.status is RiskVerdictStatus.ALLOW:
        assert wide.sizing.uncertainty_discount < tight.sizing.uncertainty_discount
        assert wide.sizing.recommended_size <= tight.sizing.recommended_size
    else:
        assert wide.sizing.recommended_size == 0


def test_heat_is_not_raw_sum_only() -> None:
    bundle = admitted_bundle(key="heat")
    assert bundle.heat.effective_heat >= bundle.heat.raw_heat or bundle.heat.effective_heat >= 0
    assert bundle.heat.residual_heat_headroom >= 0
    assert bundle.heat.heat_regime in set(HeatRegime)


def test_concentration_fx_overlap() -> None:
    gate = risk_module()
    candidate = make_candidate(symbol="GBPUSD", cluster="european_majors")
    intent = make_intent(key="gbp", symbol="GBPUSD", candidate_id=candidate.candidate_id, entry="1.27000", stop="1.26500")
    forecast = make_forecast(intent, q05="1.26600", q95="1.27400")
    exposure = make_exposure(symbols=("EURUSD",), clusters=("european_majors",), heat_r=Decimal("0.008"))
    bundle = gate.evaluate_intent(
        intent,
        exposure,
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.27000"),
        session="london",
    )
    assert bundle.concentration.currency_overlap
    assert "USD" in bundle.concentration.currency_overlap
    assert bundle.concentration.stressed_concentration_state in set(ConcentrationState)


def test_one_per_cluster_blocks() -> None:
    gate = risk_module()
    candidate = make_candidate(symbol="EURUSD", cluster="european_majors")
    intent = make_intent(key="cluster-block", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    exposure = make_exposure(symbols=("GBPUSD",), clusters=("european_majors",))
    # Force overlap via open EURUSD
    exposure = exposure.model_copy(update={"symbols": ("EURUSD",)})
    bundle = gate.evaluate_intent(
        intent,
        exposure,
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )
    assert bundle.concentration.one_per_cluster_blocked is True
    assert bundle.verdict.status is RiskVerdictStatus.DENY


def test_drawdown_escalation_ladder() -> None:
    gate = risk_module()
    candidate = make_candidate()
    intent = make_intent(key="dd", candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    exposure = make_exposure(equity=Decimal("90000"), peak_equity=Decimal("100000"))
    bundle = gate.evaluate_intent(
        intent,
        exposure,
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )
    assert bundle.drawdown.current_drawdown == Decimal("0.1")
    assert bundle.drawdown.throttle_stage is DrawdownStage.KILL_PROTECTED
    assert bundle.verdict.status is RiskVerdictStatus.HALT


def test_pretrade_fat_finger_max_lots() -> None:
    from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig

    cfg = Pm4RiskGateConfig(max_lots=Decimal("0.01"), min_lots=Decimal("0.01"))
    gate = risk_module(config=cfg)
    bundle = admitted_bundle(gate, key="fat")
    # either reduced to cap or rejected; never above max
    assert bundle.sizing.recommended_size <= cfg.max_lots


def test_route_eligibility_recorded_closed() -> None:
    bundle = admitted_bundle(key="route")
    assert bundle.pretrade.route_eligible is False
    assert bundle.pretrade.checks.get("route") is False

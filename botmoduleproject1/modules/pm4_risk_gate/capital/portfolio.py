"""Conservative portfolio heat and exposure projection."""

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.pm4_capital import RiskEvaluationRequest
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig

_ZERO = Decimal("0")


def heat_before(request: RiskEvaluationRequest) -> Decimal:
    equity = request.account_equity
    if equity <= 0:
        raise ValueError("cannot compute heat without equity")
    return (request.open_position_risk + request.pending_order_risk) / equity


def heat_after(request: RiskEvaluationRequest, projected_risk: Decimal) -> Decimal:
    equity = request.account_equity
    if equity <= 0:
        raise ValueError("cannot compute heat without equity")
    total = request.open_position_risk + request.pending_order_risk + projected_risk
    return total / equity


def heat_headroom(request: RiskEvaluationRequest, config: Pm4RiskGateConfig) -> Decimal:
    before = heat_before(request)
    leftover = config.max_effective_heat - before
    return leftover if leftover > 0 else _ZERO


def currency_after(request: RiskEvaluationRequest, projected_risk: Decimal) -> Decimal:
    return request.currency_exposure + projected_risk


def concentration_after(request: RiskEvaluationRequest, projected_risk: Decimal) -> Decimal:
    return request.correlated_exposure + projected_risk

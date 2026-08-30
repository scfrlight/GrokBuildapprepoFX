"""Deterministic Decimal position sizing. Never round up through a risk limit."""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

from botmoduleproject1.contracts.v1.pm4_capital import RiskEvaluationRequest, SizingTrace
from botmoduleproject1.modules.pm4_risk_gate.capital.hashing import canonical_hash
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm8_persistence.money import canonical, decimal_from

CALC_VERSION = "capital-sizer-v1"
_ZERO = Decimal("0")


class SizingError(ValueError):
    pass


def stop_distance(request: RiskEvaluationRequest) -> Decimal:
    if request.side == "buy":
        distance = request.entry_price - request.stop_loss_price
    else:
        distance = request.stop_loss_price - request.entry_price
    return decimal_from(distance, field="stop_distance")


def size_position(
    request: RiskEvaluationRequest,
    config: Pm4RiskGateConfig,
    *,
    heat_headroom: Decimal,
    remaining_trade_budget: Decimal,
) -> SizingTrace:
    stop = stop_distance(request)
    if stop <= 0:
        raise SizingError("stop distance must be positive for the side")
    spread = request.spread if config.include_transaction_costs else _ZERO
    slip = request.estimated_slippage if config.include_transaction_costs else _ZERO
    effective_stop = stop + spread + slip
    if effective_stop <= 0:
        raise SizingError("effective stop is not positive")
    contract = request.contract_size or config.contract_size
    raw_step = request.volume_step or config.lot_step
    step = raw_step.normalize()
    if step <= 0:
        raise SizingError("lot step must be positive")
    rate = request.conversion_rate
    if rate is None:
        raise SizingError("conversion_rate missing")
    if rate <= 0:
        raise SizingError("conversion_rate must be positive")
    if request.account_equity <= 0:
        raise SizingError("account equity unknown or non-positive")
    budget = min(
        request.account_equity * config.max_per_trade_risk_pct,
        remaining_trade_budget if remaining_trade_budget > 0 else request.account_equity * config.max_per_trade_risk_pct,
    )
    if heat_headroom > 0:
        heat_budget = heat_headroom * request.account_equity
        budget = min(budget, heat_budget)
    if config.include_transaction_costs:
        budget = budget - request.estimated_commission
    if budget <= 0:
        raise SizingError("no remaining risk budget")
    risk_per_lot = effective_stop * contract * rate
    if risk_per_lot <= 0:
        raise SizingError("risk per lot is not positive")
    theoretical = budget / risk_per_lot
    constrained = min(theoretical, config.max_lots, request.requested_quantity)
    if constrained < config.min_lots:
        rounded = _ZERO
        constraints = ("below_min_lots",)
        final_risk = _ZERO
    else:
        rounded = constrained.quantize(step, rounding=ROUND_DOWN)
        if rounded < config.min_lots:
            rounded = _ZERO
            constraints = ("quantize_below_min",)
            final_risk = _ZERO
        else:
            position_risk = rounded * risk_per_lot
            # Budget already has commission subtracted. Never compare
            # commission-inclusive risk against a commission-exclusive budget.
            if position_risk > budget:
                raise SizingError("rounded quantity would breach the risk budget")
            commission = request.estimated_commission if config.include_transaction_costs else _ZERO
            final_risk = position_risk + commission
            constraints = []
            if rounded < request.requested_quantity:
                constraints.append("requested_quantity")
            if rounded < theoretical:
                constraints.append("risk_budget")
            if rounded == config.max_lots:
                constraints.append("max_lots")
    inputs = {
        "equity": canonical(request.account_equity),
        "stop": canonical(stop),
        "effective_stop": canonical(effective_stop),
        "budget": canonical(budget),
        "contract": canonical(contract),
        "rate": canonical(rate),
        "requested": canonical(request.requested_quantity),
    }
    outputs = {
        "theoretical": canonical(theoretical),
        "constrained": canonical(constrained),
        "rounded": canonical(rounded),
        "final_risk": canonical(final_risk),
    }
    return SizingTrace(
        theoretical_size=theoretical,
        constrained_size=constrained,
        rounded_size=rounded,
        final_risk=final_risk,
        stop_distance=stop,
        effective_stop=effective_stop,
        limiting_constraints=tuple(constraints),
        calculation_version=CALC_VERSION,
        input_hash=canonical_hash(inputs),
        output_hash=canonical_hash(outputs),
        include_costs=config.include_transaction_costs,
    )

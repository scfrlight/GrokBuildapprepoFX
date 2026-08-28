from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import ControlBreachType, PositionSizingDecision, PreTradeControlDecision
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.controls.collars import price_inside_collar
from botmoduleproject1.modules.pm4_risk_gate.controls.reasonability_checks import market_data_reasonable
from botmoduleproject1.modules.pm4_risk_gate.controls.throttles import BurstTracker
from botmoduleproject1.modules.pm4_risk_gate.intake.validators import reference_price
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


class PreTradeControlEngine:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config
        self.bursts = BurstTracker(config.burst_limit, config.burst_window_seconds)

    def evaluate(
        self,
        request: RiskIntakeRequest,
        sizing: PositionSizingDecision,
        now: datetime,
        *,
        duplicate: bool,
        route_open: bool,
    ) -> PreTradeControlDecision:
        breaches: list[ControlBreachType] = []
        checks: dict[str, bool] = {}
        size_ok = self.config.min_lots <= sizing.recommended_size <= self.config.max_lots
        if sizing.recommended_size == 0:
            size_ok = False
            breaches.append(ControlBreachType.MAX_ORDER_SIZE)
        checks["order_size"] = size_ok
        if sizing.recommended_size > self.config.max_lots:
            breaches.append(ControlBreachType.FAT_FINGER)

        px = reference_price(request) or Decimal("0")
        notional = sizing.recommended_size * self.config.contract_size * px
        notional_ok = notional <= self.config.max_notional
        checks["notional"] = notional_ok
        if not notional_ok:
            breaches.append(ControlBreachType.MAX_NOTIONAL)

        collar = price_inside_collar(request, self.config)
        checks["price_collar"] = collar
        if not collar:
            breaches.append(ControlBreachType.PRICE_COLLAR)

        md = market_data_reasonable(request)
        checks["market_data"] = md
        if not md:
            breaches.append(ControlBreachType.UNREASONABLE_MARKET_DATA)

        burst_ok = self.bursts.allow(now)
        checks["burst"] = burst_ok
        if not burst_ok:
            breaches.append(ControlBreachType.BURST)

        checks["duplicate"] = not duplicate
        if duplicate:
            breaches.append(ControlBreachType.DUPLICATE)

        checks["route"] = route_open
        # Sequence 06: PM5 is closed. Route eligibility is a control that
        # *records* the closed path; it does not by itself mint an order.
        # Admission still cannot treat the route as live.
        if not route_open:
            breaches.append(ControlBreachType.ROUTE)

        checks["cancel_on_disconnect_policy"] = self.config.cancel_on_disconnect
        price_legal = collar and md
        # Route closed is expected; it is recorded but admission uses a
        # dedicated handoff flag rather than treating ROUTE as a fat-finger.
        fatal = [
            b
            for b in breaches
            if b
            not in {
                ControlBreachType.ROUTE,
                ControlBreachType.CANCEL_ON_DISCONNECT,
            }
        ]
        passed = not fatal
        return PreTradeControlDecision(
            passed=passed,
            breach_reasons=tuple(breaches),
            order_size_legal=size_ok,
            price_legal=price_legal,
            message_legal=burst_ok and not duplicate,
            route_eligible=route_open,
            checks=checks,
            detail="pre-trade controls; route remains PM5-closed",
        )

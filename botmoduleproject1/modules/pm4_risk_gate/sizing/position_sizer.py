from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

from botmoduleproject1.contracts.v1.risk import (
    ConcentrationExposureCard,
    DrawdownStateCard,
    PortfolioHeatCard,
    PositionSizingDecision,
)
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.intake.validators import _stop_distance, reference_price
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest
from botmoduleproject1.modules.pm4_risk_gate.sizing.uncertainty_adjustment import (
    liquidity_factor,
    predictive_quality,
    uncertainty_discount,
)
from botmoduleproject1.modules.pm4_risk_gate.sizing.volatility_normalizer import clip


class PositionSizer:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config

    def size(
        self,
        request: RiskIntakeRequest,
        *,
        equity: Decimal,
        drawdown: DrawdownStateCard,
        concentration: ConcentrationExposureCard,
        heat: PortfolioHeatCard,
        budget_headroom: Decimal,
    ) -> PositionSizingDecision:
        stop = _stop_distance(request) or Decimal("0")
        base_pct = self.config.max_per_trade_risk_pct
        quality = predictive_quality(request, self.config)
        uncertain = uncertainty_discount(request, self.config)
        liq = liquidity_factor(request, self.config)
        corr = Decimal("1") - concentration.crowding_penalty
        if corr < 0:
            corr = Decimal("0")
        dd = drawdown.throttle_factor
        heat_cap = Decimal("1")
        if heat.residual_heat_headroom <= 0:
            heat_cap = Decimal("0")
        elif heat.effective_heat > 0 and self.config.max_effective_heat > 0:
            heat_cap = clip(
                heat.residual_heat_headroom / self.config.max_effective_heat,
                Decimal("0"),
                Decimal("1"),
            )
        adjusted = base_pct * quality * uncertain * dd * liq * corr * heat_cap
        if budget_headroom > 0 and equity > 0:
            budget_pct = budget_headroom / equity
            if adjusted > budget_pct:
                adjusted = budget_pct
        if adjusted > self.config.max_per_trade_risk_pct:
            adjusted = self.config.max_per_trade_risk_pct
        risk_amount = equity * adjusted
        lots = Decimal("0")
        hard_cap = False
        basis = "stop_distance"
        if stop > 0 and self.config.contract_size > 0:
            lots = risk_amount / (stop * self.config.contract_size)
        else:
            basis = "unavailable"
        if lots > self.config.max_lots:
            lots = self.config.max_lots
            hard_cap = True
        if lots > 0 and lots < self.config.min_lots:
            lots = Decimal("0")
        lots = lots.quantize(self.config.lot_step, rounding=ROUND_DOWN)
        px = reference_price(request)
        rationale = (
            f"base={base_pct} quality={quality} uncertainty={uncertain} "
            f"dd={dd} liq={liq} corr={corr} heat={heat_cap} stop={stop} px={px}"
        )
        return PositionSizingDecision(
            recommended_size=lots,
            base_risk_percentage=base_pct,
            adjusted_risk_percentage=adjusted if lots > 0 else Decimal("0"),
            stop_distance=stop,
            stop_distance_basis=basis,
            uncertainty_discount=uncertain,
            predictive_quality_factor=quality,
            drawdown_throttle=dd,
            liquidity_factor=liq,
            correlation_penalty=concentration.crowding_penalty,
            heat_cap_factor=heat_cap,
            hard_cap_applied=hard_cap,
            final_size_rationale=rationale,
            account_equity=equity,
            risk_amount=risk_amount if lots > 0 else Decimal("0"),
        )

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.intake.validators import interval_width, reference_price
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest
from botmoduleproject1.modules.pm4_risk_gate.sizing.volatility_normalizer import clip


def predictive_quality(request: RiskIntakeRequest, config: Pm4RiskGateConfig) -> Decimal:
    forecast = request.forecast
    intent = request.intent
    quality = Decimal("0.55")
    if forecast is not None and forecast.sample_size:
        ratio = Decimal(forecast.sample_size) / Decimal(max(config.min_forecast_samples, 1))
        quality = clip(ratio, Decimal("0.40"), Decimal("1.00"))
    if forecast is not None and forecast.coverage is not None:
        coverage = Decimal(str(forecast.coverage))
        quality *= clip(coverage / Decimal("0.90"), Decimal("0.70"), Decimal("1.00"))
    setup = Decimal(str(intent.setup_quality or 0))
    conf = Decimal(str(intent.confidence_score or 0))
    blend = (setup + conf) / Decimal("2")
    if blend > 0:
        quality *= clip(blend, Decimal("0.50"), Decimal("1.00"))
    return clip(quality, Decimal("0.20"), Decimal("1.00"))


def uncertainty_discount(request: RiskIntakeRequest, config: Pm4RiskGateConfig) -> Decimal:
    width = interval_width(request)
    px = reference_price(request)
    if width is None or px is None or px <= 0:
        return Decimal("0.50")
    relative = width / px
    if relative <= config.wide_interval_pct:
        return Decimal("1.00")
    extra = (relative - config.wide_interval_pct) / config.wide_interval_pct
    factor = Decimal("1.00") - clip(extra, Decimal("0"), Decimal("0.80"))
    return clip(factor, Decimal("0.20"), Decimal("1.00"))


def liquidity_factor(request: RiskIntakeRequest, config: Pm4RiskGateConfig) -> Decimal:
    if request.candidate is None:
        return Decimal("0.50")
    score = Decimal(str(request.candidate.scorecard.liquidity_score))
    floor = Decimal(str(config.min_liquidity_score))
    if score < floor:
        return Decimal("0")
    return clip(score / Decimal("100"), Decimal("0.40"), Decimal("1.00"))

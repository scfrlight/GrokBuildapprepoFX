from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.intake.validators import reference_price
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


def price_inside_collar(request: RiskIntakeRequest, config: Pm4RiskGateConfig) -> bool:
    px = reference_price(request)
    if px is None:
        return False
    if request.mid_price is None:
        return True
    if request.mid_price <= 0:
        return False
    bps = abs(px - request.mid_price) / request.mid_price * Decimal("10000")
    return bps <= config.price_collar_bps

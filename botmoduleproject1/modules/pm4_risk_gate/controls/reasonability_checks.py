from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.modules.pm4_risk_gate.intake.validators import interval_width, reference_price
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


def market_data_reasonable(request: RiskIntakeRequest) -> bool:
    px = reference_price(request)
    if px is None or px <= 0:
        return False
    width = interval_width(request)
    if width is not None and width < 0:
        return False
    if request.spread is not None and request.spread < 0:
        return False
    if request.spread is not None and px > 0 and request.spread / px > Decimal("0.01"):
        return False
    return True

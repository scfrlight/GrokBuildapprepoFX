from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import ExposureSnapshot


def effective_from_raw(raw: Decimal, crowding: Decimal) -> Decimal:
    overlap = Decimal("1") + crowding
    return raw * overlap


def directional_heat(exposure: ExposureSnapshot, equity: Decimal) -> Decimal:
    if equity <= 0:
        return Decimal("0")
    return abs(exposure.directional_net) / equity

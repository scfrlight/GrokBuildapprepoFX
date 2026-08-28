from decimal import Decimal


def residual(max_heat: Decimal, effective: Decimal) -> Decimal:
    left = max_heat - effective
    return left if left > 0 else Decimal("0")

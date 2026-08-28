from decimal import Decimal


def residual(limit: Decimal, used: Decimal) -> Decimal:
    left = limit - used
    return left if left > 0 else Decimal("0")

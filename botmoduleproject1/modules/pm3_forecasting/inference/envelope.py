"""Residual quantile envelope.

Deterministic nonparametric estimator. A fitted sklearn Quantile Regression
Forest is OUT OF SCOPE for Sequence 05; this module is the research-to-inference
plumbing a later sequence can swap for a fitted QRF behind the same port.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal

from pydantic import ValidationError

from botmoduleproject1.contracts.v1.forecasting import QuantileSet
from botmoduleproject1.modules.pm3_forecasting.domain.policies import (
    FX_QUANTUM,
    PERCENTILE_LEVELS,
    quantiles_non_decreasing,
)

# Hyndman-Fan type 7 (linear interpolation). Matches numpy.percentile
# method='linear' and R quantile type=7.
# For n sorted samples x[0] <= ... x[n-1] and probability p in [0, 1]:
#     h = p * (n - 1)           # 0-based real index
#     lo = floor(h), hi = ceil(h)
#     if lo == hi: return x[lo]
#     return x[lo] + (x[hi] - x[lo]) * (h - lo)


def empirical_percentile(sorted_samples: tuple[Decimal, ...], p: Decimal) -> Decimal:
    n = len(sorted_samples)
    if n == 0:
        raise ValueError("empty sample")
    if n == 1:
        return sorted_samples[0]
    if p <= 0:
        return sorted_samples[0]
    if p >= 1:
        return sorted_samples[-1]
    h = p * Decimal(n - 1)
    lo = int(h.to_integral_value(rounding=ROUND_FLOOR))
    hi = int(h.to_integral_value(rounding=ROUND_CEILING))
    lo = max(0, min(n - 1, lo))
    hi = max(0, min(n - 1, hi))
    if lo == hi:
        return sorted_samples[lo]
    weight = h - Decimal(lo)
    return sorted_samples[lo] + (sorted_samples[hi] - sorted_samples[lo]) * weight


def return_quantiles(forward_returns: tuple[Decimal, ...]) -> tuple[Decimal, ...] | None:
    if not forward_returns:
        return None
    ordered = tuple(sorted(forward_returns))
    values = tuple(empirical_percentile(ordered, p) for p in PERCENTILE_LEVELS)
    if not quantiles_non_decreasing(values):
        return None
    return values


def map_to_price(
    last_close: Decimal,
    q_returns: tuple[Decimal, ...],
    *,
    quantum: Decimal = FX_QUANTUM,
) -> tuple[Decimal, ...] | None:
    if last_close <= 0:
        return None
    one = Decimal("1")
    prices = tuple(
        (last_close * (one + q)).quantize(quantum, rounding=ROUND_HALF_EVEN) for q in q_returns
    )
    if not quantiles_non_decreasing(prices):
        return None
    return prices


def envelope(
    forward_returns: tuple[Decimal, ...],
    last_close: Decimal,
    *,
    quantum: Decimal = FX_QUANTUM,
) -> QuantileSet | None:
    """Empirical return quantiles mapped into FX price space. None if unusable."""
    q_ret = return_quantiles(forward_returns)
    if q_ret is None:
        return None
    prices = map_to_price(last_close, q_ret, quantum=quantum)
    if prices is None:
        return None
    try:
        return QuantileSet(
            q05=prices[0],
            q25=prices[1],
            q50=prices[2],
            q75=prices[3],
            q95=prices[4],
        )
    except ValidationError:
        return None

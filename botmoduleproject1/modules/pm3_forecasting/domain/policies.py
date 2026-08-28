"""Domain policies: fail-closed enrichment. Not risk. Not execution."""

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.modules.pm3_forecasting.domain.enums import EstimatorKind

MODEL_ID = EstimatorKind.RESIDUAL_QUANTILE_ENVELOPE.value
MODEL_VERSION = "0.1.0"
PERCENTILE_LEVELS: tuple[Decimal, ...] = (
    Decimal("0.05"),
    Decimal("0.25"),
    Decimal("0.50"),
    Decimal("0.75"),
    Decimal("0.95"),
)
FX_QUANTUM = Decimal("0.00001")


def is_blank_symbol(symbol: str | None) -> bool:
    return symbol is None or not str(symbol).strip()


def quantiles_non_decreasing(values: tuple[Decimal, ...]) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def sufficient_samples(n: int, minimum: int) -> bool:
    return n >= minimum


def coverage_healthy(realized: int, minimum: int) -> bool:
    """Insufficient conformal observations are not healthy."""
    return realized >= minimum

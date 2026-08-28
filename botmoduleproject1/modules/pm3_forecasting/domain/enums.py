"""PM3 forecasting / QRF domain enumerations. Pair-agnostic."""

from __future__ import annotations

from enum import Enum

from botmoduleproject1.contracts.v1.market import Timeframe


class EstimatorKind(str, Enum):
    """Research kernel. Fitted QRF is reserved and unused in Sequence 05."""

    RESIDUAL_QUANTILE_ENVELOPE = "residual_quantile_envelope"
    FITTED_QRF = "fitted_qrf"


class OperatingMode(str, Enum):
    SHADOW = "shadow"
    OBSERVE_ONLY = "observe-only"
    PAPER = "paper"


class CoverageBand(str, Enum):
    P90 = "p90"
    P50 = "p50"


__all__ = [
    "CoverageBand",
    "EstimatorKind",
    "OperatingMode",
    "Timeframe",
]

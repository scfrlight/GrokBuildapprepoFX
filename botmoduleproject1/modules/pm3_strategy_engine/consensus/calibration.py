"""Calibration policies. Raw and calibrated stay distinct. Not QRF."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy_engine import StrategyVote

RELIABILITY_TABLE: tuple[tuple[float, float], ...] = (
    (0.0, 0.12),
    (0.25, 0.28),
    (0.50, 0.48),
    (0.75, 0.68),
    (1.00, 0.82),
)


def _interp(raw: float, table: tuple[tuple[float, float], ...] = RELIABILITY_TABLE) -> float:
    x = min(1.0, max(0.0, raw))
    for i in range(len(table) - 1):
        x0, y0 = table[i]
        x1, y1 = table[i + 1]
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return table[-1][1]


class ReliabilityTablePolicy:
    version = "reliability_table.v1"

    def calibrate(self, vote: StrategyVote) -> StrategyVote:
        cal = _interp(vote.raw_probability)
        return vote.model_copy(
            update={
                "calibrated_probability": cal,
                "calibration_version": self.version,
                "calibration_fallback": False,
            }
        )


class ConservativeFallbackPolicy:
    version = "fallback.identity.v1"

    def calibrate(self, vote: StrategyVote) -> StrategyVote:
        shrink = 0.5 + (vote.raw_probability - 0.5) * 0.5
        return vote.model_copy(
            update={
                "calibrated_probability": min(1.0, max(0.0, shrink)),
                "calibration_version": self.version,
                "calibration_fallback": True,
                "diagnostics": {**vote.diagnostics, "calibration": "fallback"},
            }
        )


class PlattScalingPolicy:
    """Interface only in Sequence 04. Delegates to conservative fallback."""

    version = "platt.unfitted.v1"

    def __init__(self) -> None:
        self._inner = ConservativeFallbackPolicy()

    def calibrate(self, vote: StrategyVote) -> StrategyVote:
        out = self._inner.calibrate(vote)
        return out.model_copy(
            update={
                "calibration_version": self.version,
                "calibration_fallback": True,
                "diagnostics": {**out.diagnostics, "platt": "unfitted"},
            }
        )


class IsotonicCalibrationPolicy:
    """Interface only in Sequence 04. Delegates to conservative fallback."""

    version = "isotonic.unfitted.v1"

    def __init__(self) -> None:
        self._inner = ConservativeFallbackPolicy()

    def calibrate(self, vote: StrategyVote) -> StrategyVote:
        out = self._inner.calibrate(vote)
        return out.model_copy(
            update={
                "calibration_version": self.version,
                "calibration_fallback": True,
                "diagnostics": {**out.diagnostics, "isotonic": "unfitted"},
            }
        )


def policy_for(name: str):
    mapping = {
        "reliability_table": ReliabilityTablePolicy,
        "fallback": ConservativeFallbackPolicy,
        "platt": PlattScalingPolicy,
        "isotonic": IsotonicCalibrationPolicy,
    }
    return mapping.get(name, ReliabilityTablePolicy)()

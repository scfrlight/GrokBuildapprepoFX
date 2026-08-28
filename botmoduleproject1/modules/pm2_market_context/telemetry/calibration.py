"""Calibration-ready snapshot. Does not mutate production weights."""

from __future__ import annotations

from collections import Counter

from botmoduleproject1.contracts.v1.pm2 import RankedCandidate


def calibration_snapshot(candidates: tuple[RankedCandidate, ...]) -> dict[str, object]:
    bands = Counter(c.scorecard.quality_tier.value for c in candidates)
    states = Counter(c.state.state.value for c in candidates)
    scores = [c.scorecard.final_confluence_score for c in candidates]
    mean = sum(scores) / len(scores) if scores else 0.0
    return {
        "n": len(candidates),
        "band_counts": dict(bands),
        "state_counts": dict(states),
        "mean_score": round(mean, 4),
        "min_score": min(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
        "auto_weight_update": False,
        "note": "diagnostics only; production weights are not mutated",
    }

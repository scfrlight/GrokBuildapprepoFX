"""Deterministic score-component attribution. No auto-tuning."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import RankedCandidate


def attribute(candidate: RankedCandidate) -> dict[str, object]:
    components = candidate.scorecard.components
    dominant = ""
    best = -1.0
    for key, value in components.items():
        if key.endswith("penalty"):
            continue
        if float(value) > best:
            best = float(value)
            dominant = key
    return {
        "candidate_id": str(candidate.candidate_id),
        "symbol": candidate.symbol,
        "as_of": candidate.as_of.isoformat(),
        "final_rank": candidate.final_rank,
        "final_confluence_score": candidate.scorecard.final_confluence_score,
        "quality_tier": candidate.scorecard.quality_tier.value,
        "state": candidate.state.state.value,
        "regime": candidate.context.regime.value,
        "regime_confidence": candidate.context.regime_confidence,
        "components": dict(components),
        "dominant_family": dominant,
        "vetoes": list(candidate.scorecard.vetoes),
        "suppression": None
        if candidate.suppression is None
        else list(candidate.suppression.suppression_reasons),
        "side_bias": candidate.side_bias,
        "handoff_eligibility": candidate.handoff_eligibility,
    }


def attribute_all(candidates: tuple[RankedCandidate, ...]) -> tuple[dict[str, object], ...]:
    return tuple(attribute(c) for c in candidates)

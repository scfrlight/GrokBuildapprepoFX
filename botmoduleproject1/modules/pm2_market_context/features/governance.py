"""Family caps and anti-redundancy. One family, one capped contribution."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import FeatureFamily
from botmoduleproject1.modules.pm2_market_context.domain.policies import FAMILY_CAPS, cap_contribution


def apply_family_caps(contributions: dict[FeatureFamily, float]) -> dict[FeatureFamily, float]:
    return {family: cap_contribution(family, value) for family, value in contributions.items()}


def redundancy_penalty(contributions: dict[FeatureFamily, float]) -> float:
    """Penalty when bias, structure, and momentum all point the same way too hard."""
    trio = (
        contributions.get(FeatureFamily.DIRECTIONAL_BIAS, 0.0),
        contributions.get(FeatureFamily.STRUCTURE, 0.0),
        contributions.get(FeatureFamily.MOMENTUM, 0.0),
    )
    if min(trio) > 12.0:
        return 8.0
    if min(trio) > 8.0:
        return 4.0
    return 0.0


def family_cap(family: FeatureFamily) -> float:
    return FAMILY_CAPS[family]

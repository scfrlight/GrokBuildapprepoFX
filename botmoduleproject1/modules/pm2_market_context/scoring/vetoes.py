"""Hard vetoes. Vetoed candidates cannot qualify."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.modules.pm2_market_context.domain.enums import VolatilityPhase


def vetoes(
    *,
    quality: DataQualityStatus,
    regime: RegimeType,
    phase: VolatilityPhase,
    rollover: bool,
    weekend: bool,
) -> tuple[str, ...]:
    found: list[str] = []
    if quality is not DataQualityStatus.OK:
        found.append(f"data_quality:{quality.value}")
    if regime is RegimeType.UNTRADEABLE:
        found.append("regime:untradeable")
    if phase is VolatilityPhase.SHOCK:
        found.append("volatility:shock")
    if phase is VolatilityPhase.DEAD:
        found.append("volatility:dead")
    if rollover:
        found.append("session:rollover")
    if weekend:
        found.append("session:weekend")
    return tuple(found)

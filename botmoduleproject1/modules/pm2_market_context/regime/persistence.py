"""Regime persistence / hysteresis. Avoids one-bar flips."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType


def persist(
    previous: RegimeType | None,
    incoming: RegimeType,
    confidence: float,
    *,
    hold: int,
    seen: int,
) -> tuple[RegimeType, int]:
    if previous is None or previous is incoming:
        return incoming, seen + 1
    if incoming is RegimeType.UNTRADEABLE:
        return incoming, 1
    if hold > 0 and seen < hold and confidence < 0.75:
        return previous, seen + 1
    return incoming, 1

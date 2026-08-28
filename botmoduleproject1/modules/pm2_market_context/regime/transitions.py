"""Regime transition tracking."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.session import RegimeType


def transition_label(previous: RegimeType | None, current: RegimeType) -> str:
    if previous is None:
        return f"init:{current.value}"
    if previous is current:
        return f"hold:{current.value}"
    return f"{previous.value}->{current.value}"

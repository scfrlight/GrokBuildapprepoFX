"""Swing structure. Confirmed pivots only — no repaint."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from botmoduleproject1.contracts.v1.market import OhlcvBar
from botmoduleproject1.modules.pm2_market_context.domain.enums import StructureState
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


class StructureResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    state: StructureState
    quality: float
    hh: bool
    hl: bool
    lh: bool
    ll: bool


def _pivots(bars: tuple[OhlcvBar, ...], left: int = 2) -> tuple[list[float], list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    for i in range(left, len(bars) - left):
        h = float(bars[i].high)
        l = float(bars[i].low)
        if all(h >= float(bars[i - j].high) and h >= float(bars[i + j].high) for j in range(1, left + 1)):
            highs.append(h)
        if all(l <= float(bars[i - j].low) and l <= float(bars[i + j].low) for j in range(1, left + 1)):
            lows.append(l)
    return highs, lows


def evaluate_structure(bars: tuple[OhlcvBar, ...]) -> StructureResult:
    highs, lows = _pivots(bars)
    hh = len(highs) >= 2 and highs[-1] > highs[-2]
    lh = len(highs) >= 2 and highs[-1] < highs[-2]
    hl = len(lows) >= 2 and lows[-1] > lows[-2]
    ll = len(lows) >= 2 and lows[-1] < lows[-2]
    if hh and hl:
        state = StructureState.CONTINUATION
        quality = 72.0
    elif ll and lh:
        state = StructureState.CONTINUATION
        quality = 70.0
    elif hh and ll:
        state = StructureState.TRANSITION
        quality = 45.0
    elif lh and hl:
        state = StructureState.BREAK
        quality = 40.0
    else:
        state = StructureState.UNDEFINED
        quality = 30.0
    return StructureResult(
        state=state,
        quality=clamp(quality),
        hh=hh,
        hl=hl,
        lh=lh,
        ll=ll,
    )

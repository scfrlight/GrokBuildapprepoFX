"""Session and liquidity quality. Independent of directional bias."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from botmoduleproject1.contracts.v1.session import SessionContext, SessionName
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp


class SessionLiquidityResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    context: SessionContext
    session_score: float
    liquidity_score: float
    rollover_risk: bool


def evaluate_session(as_of: datetime, is_weekend: bool = False) -> SessionLiquidityResult:
    hour = as_of.hour
    sessions: list[SessionName] = []
    if 22 <= hour or hour < 7:
        sessions.append(SessionName.SYDNEY)
    if 0 <= hour < 9:
        sessions.append(SessionName.TOKYO)
    if 7 <= hour < 16:
        sessions.append(SessionName.LONDON)
    if 12 <= hour < 21:
        sessions.append(SessionName.NEW_YORK)
    if SessionName.LONDON in sessions and SessionName.NEW_YORK in sessions:
        sessions.append(SessionName.OVERLAP_LONDON_NY)
    rollover = hour == 21 or hour == 22
    if rollover:
        sessions.append(SessionName.ROLLOVER)
    if not sessions:
        sessions.append(SessionName.OFF_SESSION)
    quality = 0.85 if SessionName.OVERLAP_LONDON_NY in sessions else 0.55
    if SessionName.OFF_SESSION in sessions:
        quality = 0.25
    if rollover:
        quality = min(quality, 0.3)
    if is_weekend:
        quality = 0.1
        sessions = [SessionName.OFF_SESSION]
    ctx = SessionContext(as_of=as_of, sessions=tuple(sessions), is_weekend=is_weekend, quality=quality)
    session_score = clamp(quality * 100)
    liquidity = session_score if not rollover else 20.0
    return SessionLiquidityResult(
        context=ctx,
        session_score=session_score,
        liquidity_score=clamp(liquidity),
        rollover_risk=rollover,
    )

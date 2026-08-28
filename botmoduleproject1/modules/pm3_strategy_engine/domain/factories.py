"""Vote / no-trade helpers."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from botmoduleproject1.contracts.v1.strategy import Direction, EntryType, NoTradeDecision
from botmoduleproject1.contracts.v1.strategy_engine import (
    StrategyTemplateType,
    StrategyVote,
    VoteAbstentionReason,
)


def abstain_vote(
    *,
    template: StrategyTemplateType,
    profile_id: str,
    version_id: str,
    symbol: str,
    as_of: datetime,
    reason: VoteAbstentionReason,
    correlation_id: UUID,
    diagnostics: dict | None = None,
) -> StrategyVote:
    return StrategyVote(
        correlation_id=correlation_id,
        occurred_at=as_of,
        strategy_template_type=template,
        profile_id=profile_id,
        version_id=version_id,
        symbol=symbol,
        direction=Direction.FLAT,
        raw_probability=0.5,
        calibrated_probability=0.5,
        setup_quality=0.0,
        regime_fit=0.0,
        friction_fit=0.0,
        historical_reliability=0.5,
        recent_live_health=0.5,
        abstained=True,
        abstention_reason=reason,
        diagnostics=diagnostics or {"reason": reason.value},
    )


def directional_vote(
    *,
    template: StrategyTemplateType,
    profile_id: str,
    version_id: str,
    symbol: str,
    as_of: datetime,
    direction: Direction,
    raw: float,
    setup_quality: float,
    regime_fit: float,
    friction_fit: float,
    historical_reliability: float,
    recent_live_health: float,
    correlation_id: UUID,
    entry_type: EntryType = EntryType.LIMIT,
    hints: dict | None = None,
    diagnostics: dict | None = None,
) -> StrategyVote:
    raw_c = min(1.0, max(0.0, raw))
    return StrategyVote(
        correlation_id=correlation_id,
        occurred_at=as_of,
        strategy_template_type=template,
        profile_id=profile_id,
        version_id=version_id,
        symbol=symbol,
        direction=direction,
        raw_probability=raw_c,
        calibrated_probability=raw_c,
        setup_quality=min(1.0, max(0.0, setup_quality)),
        regime_fit=min(1.0, max(0.0, regime_fit)),
        friction_fit=min(1.0, max(0.0, friction_fit)),
        historical_reliability=min(1.0, max(0.0, historical_reliability)),
        recent_live_health=min(1.0, max(0.0, recent_live_health)),
        entry_type=entry_type,
        entry_hints=hints or {},
        diagnostics=diagnostics or {},
        abstained=False,
    )


def no_trade(
    symbol: str,
    as_of: datetime,
    reason: str,
    *,
    correlation_id: UUID | None = None,
    diagnostics: dict | None = None,
) -> NoTradeDecision:
    kwargs: dict = {
        "symbol": symbol,
        "reason": reason,
        "as_of": as_of,
        "observe_only": True,
        "diagnostics": diagnostics or {},
    }
    if correlation_id is not None:
        kwargs["correlation_id"] = correlation_id
    return NoTradeDecision(**kwargs)

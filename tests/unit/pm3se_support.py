"""Shared fixtures for PM3-Strategy Engine tests. Not a package."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from botmoduleproject1.contracts.v1.pm2 import (
    CandidateContextSnapshot,
    CandidateQualificationState,
    CandidateScoreCard,
    DataQualityStatus,
    QualificationStateName,
    QualityTier,
    RankedCandidate,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm3_strategy_engine.config.schema import Pm3StrategyEngineConfig
from botmoduleproject1.modules.pm3_strategy_engine.module import PM3StrategyEngineModule

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


class _Clock:
    def __init__(self, instant: datetime = AS_OF) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


def _card(score: float = 72.0, **kwargs) -> CandidateScoreCard:
    data = dict(
        long_score=80.0,
        short_score=30.0,
        final_confluence_score=score,
        directional_edge_gap=50.0,
        regime_score=80.0,
        structure_score=70.0,
        momentum_score=68.0,
        volatility_score=55.0,
        session_score=80.0,
        liquidity_score=80.0,
        correlation_penalty=0.0,
        feature_redundancy_penalty=0.0,
        confidence_score=70.0,
        quality_tier=quality_tier_for(score),
    )
    data.update(kwargs)
    return CandidateScoreCard(**data)


def ranked_candidate(
    *,
    symbol: str = "EURUSD",
    regime: RegimeType = RegimeType.TRENDING,
    quality: DataQualityStatus = DataQualityStatus.OK,
    state: QualificationStateName = QualificationStateName.QUALIFIED,
    handoff: bool = True,
    as_of: datetime = AS_OF,
    side_bias: str = "long",
    score: float = 72.0,
    context_as_of: datetime | None = None,
    **score_kwargs,
) -> RankedCandidate:
    cid = uuid4()
    ctx_time = context_as_of if context_as_of is not None else as_of
    context = CandidateContextSnapshot(
        candidate_id=cid,
        event_id=cid,
        correlation_id=cid,
        symbol=symbol,
        as_of=ctx_time,
        timeframes=("M15", "H1", "H4"),
        regime=regime,
        regime_confidence=0.8,
        session_quality=0.85,
        data_quality=quality,
        feature_family_summary={"regime": 18.0},
    )
    return RankedCandidate(
        candidate_id=cid,
        event_id=cid,
        correlation_id=cid,
        symbol=symbol,
        as_of=as_of,
        final_rank=1,
        scorecard=_card(score, **score_kwargs),
        state=CandidateQualificationState(
            state=state,
            entered_at=as_of,
            persistence_count=2,
        ),
        context=context,
        correlation_cluster="EUR|USD",
        handoff_eligibility=handoff,
        side_bias=side_bias,
    )


def engine(config: Pm3StrategyEngineConfig | None = None, enabled: bool = True) -> PM3StrategyEngineModule:
    cfg = config or Pm3StrategyEngineConfig()
    return PM3StrategyEngineModule(cfg, _Clock(), feature_enabled=enabled)

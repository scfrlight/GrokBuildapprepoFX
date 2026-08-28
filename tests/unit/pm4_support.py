"""Shared fixtures for PM4 Risk Gate tests. Not a package."""

from __future__ import annotations

from datetime import datetime, timedelta, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput, ModelVersionInfo, QuantileSet
from botmoduleproject1.contracts.v1.pm2 import (
    CandidateContextSnapshot,
    CandidateQualificationState,
    CandidateScoreCard,
    DataQualityStatus,
    QualificationStateName,
    RankedCandidate,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.risk import ExposureSnapshot
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType, ExitPlan, TradeIntent
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.module import PM4RiskGateModule

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


class _Clock:
    def __init__(self, instant: datetime = AS_OF) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant

    def set(self, instant: datetime) -> None:
        self._instant = instant


def make_intent(
    *,
    direction: Direction = Direction.BUY,
    symbol: str = "EURUSD",
    key: str = "pm4-1",
    occurred_at: datetime = AS_OF,
    candidate_id: UUID | None = None,
    entry: str = "1.10000",
    stop: str = "1.09500",
    setup_quality: float = 0.8,
    confidence: float = 0.8,
) -> TradeIntent:
    cid = candidate_id
    return TradeIntent(
        idempotency_key=key,
        occurred_at=occurred_at,
        symbol=symbol,
        direction=direction,
        entry_type=EntryType.MARKET,
        requested_volume=None,
        entry_price=Decimal(entry),
        entry_zone_low=Decimal(entry) - Decimal("0.00040"),
        entry_zone_high=Decimal(entry) + Decimal("0.00040"),
        exit_plan=ExitPlan(stop_price=Decimal(stop), stop_loss=Decimal(stop)),
        setup_quality=setup_quality,
        confidence_score=confidence,
        consensus_score=0.7,
        source_candidate_id=cid,
        profile_id="trend_pullback",
        version_id="v1",
        regime_state="trending",
    )


def make_candidate(
    *,
    symbol: str = "EURUSD",
    as_of: datetime = AS_OF,
    candidate_id: UUID | None = None,
    handoff: bool = True,
    state: QualificationStateName = QualificationStateName.QUALIFIED,
    score: float = 80.0,
    liquidity: float = 80.0,
    cluster: str = "EUR|USD",
) -> RankedCandidate:
    cid = candidate_id or uuid4()
    context = CandidateContextSnapshot(
        candidate_id=cid,
        event_id=cid,
        correlation_id=cid,
        symbol=symbol,
        as_of=as_of,
        timeframes=("M15", "H1", "H4"),
        regime=RegimeType.TRENDING,
        regime_confidence=0.8,
        session_quality=0.85,
        data_quality=DataQualityStatus.OK,
        feature_family_summary={"regime": 18.0},
    )
    return RankedCandidate(
        candidate_id=cid,
        event_id=cid,
        correlation_id=cid,
        symbol=symbol,
        as_of=as_of,
        final_rank=1,
        scorecard=CandidateScoreCard(
            long_score=80.0,
            short_score=30.0,
            final_confluence_score=score,
            directional_edge_gap=50.0,
            regime_score=80.0,
            structure_score=70.0,
            momentum_score=68.0,
            volatility_score=55.0,
            session_score=80.0,
            liquidity_score=liquidity,
            correlation_penalty=0.0,
            feature_redundancy_penalty=0.0,
            confidence_score=70.0,
            quality_tier=quality_tier_for(score),
        ),
        state=CandidateQualificationState(state=state, entered_at=as_of, persistence_count=2),
        context=context,
        correlation_cluster=cluster,
        handoff_eligibility=handoff,
        side_bias="long",
    )


def make_forecast(
    intent: TradeIntent,
    *,
    samples: int = 40,
    diagnostics: dict | None = None,
    occurred_at: datetime | None = None,
    q05: str = "1.09600",
    q95: str = "1.10400",
) -> ForecastOutput:
    lo = Decimal(q05)
    hi = Decimal(q95)
    span = hi - lo
    return ForecastOutput(
        forecast_id=uuid4(),
        intent_id=intent.intent_id,
        event_id=uuid4(),
        correlation_id=intent.correlation_id,
        causation_id=intent.event_id,
        occurred_at=occurred_at or intent.occurred_at,
        symbol=intent.symbol,
        horizon_bars=4,
        quantiles=QuantileSet(
            q05=lo,
            q25=lo + span * Decimal("0.25"),
            q50=lo + span * Decimal("0.50"),
            q75=lo + span * Decimal("0.75"),
            q95=hi,
        ),
        model=ModelVersionInfo(model_id="residual_quantile_envelope", version="0.1.0"),
        sample_size=samples,
        coverage=0.9,
        diagnostics=diagnostics
        if diagnostics is not None
        else {
            "estimator": "residual_quantile_envelope",
            "not_fitted_qrf": True,
            "sample_size": samples,
            "side_invariant": True,
            "observe_only": True,
            "lookahead": False,
        },
    )


def make_exposure(*, as_of: datetime = AS_OF, **kwargs) -> ExposureSnapshot:
    data = dict(
        as_of=as_of,
        equity=Decimal("100000"),
        peak_equity=Decimal("100000"),
        heat_r=Decimal("0"),
        gross_notional=Decimal("0"),
        net_notional=Decimal("0"),
        open_position_count=0,
        symbols=(),
        clusters=(),
    )
    data.update(kwargs)
    return ExposureSnapshot(**data)


def risk_module(enabled: bool = True, config: Pm4RiskGateConfig | None = None) -> PM4RiskGateModule:
    return PM4RiskGateModule(config or Pm4RiskGateConfig(), _Clock(), feature_enabled=enabled)


def admitted_bundle(module: PM4RiskGateModule | None = None, key: str = "pm4-ok"):
    gate = module or risk_module()
    candidate = make_candidate()
    intent = make_intent(key=key, candidate_id=candidate.candidate_id)
    forecast = make_forecast(intent)
    return gate.evaluate_intent(
        intent,
        make_exposure(),
        candidate=candidate,
        forecast=forecast,
        mid_price=Decimal("1.10000"),
        session="london",
    )

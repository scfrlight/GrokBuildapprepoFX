"""PM2 public contracts: UTC, identity, bands, no order fields."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.pm2 import (
    CandidateContextSnapshot,
    CandidateScoreCard,
    DataQualityStatus,
    PublicationBundle,
    QualificationStateName,
    QualityTier,
    RankedCandidate,
    CandidateQualificationState,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.time import UTC


AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


def test_context_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        CandidateContextSnapshot(
            symbol="EURUSD",
            as_of=datetime(2026, 1, 15, 14, 0),
            regime=RegimeType.RANGING,
            regime_confidence=0.5,
            data_quality=DataQualityStatus.OK,
        )


def test_scorecard_bounds() -> None:
    with pytest.raises(ValidationError):
        CandidateScoreCard(
            long_score=101,
            short_score=0,
            final_confluence_score=50,
            directional_edge_gap=0,
            regime_score=0,
            structure_score=0,
            momentum_score=0,
            volatility_score=0,
            session_score=0,
            liquidity_score=0,
            correlation_penalty=0,
            feature_redundancy_penalty=0,
            confidence_score=0,
            quality_tier=QualityTier.WATCH,
        )


def test_publication_bundle_has_identity_and_no_order_fields() -> None:
    bundle = PublicationBundle(as_of=AS_OF, idempotency_key="pm2:scan:x")
    assert bundle.event_id
    assert bundle.correlation_id
    assert bundle.schema_version == "v1"
    fields = set(type(bundle).model_fields)
    assert "idempotency_key" in fields
    assert "order" not in fields
    assert "volume" not in fields
    assert "trade_intent" not in fields


def test_ranked_candidate_requires_scorecard_and_state() -> None:
    cid = uuid4()
    context = CandidateContextSnapshot(
        candidate_id=cid,
        symbol="EURUSD",
        as_of=AS_OF,
        regime=RegimeType.TRENDING,
        regime_confidence=0.6,
        data_quality=DataQualityStatus.OK,
        session_quality=0.5,
    )
    state = CandidateQualificationState(
        state=QualificationStateName.NEUTRAL,
        entered_at=AS_OF,
    )
    card = CandidateScoreCard(
        long_score=50,
        short_score=50,
        final_confluence_score=50,
        directional_edge_gap=0,
        regime_score=50,
        structure_score=50,
        momentum_score=50,
        volatility_score=50,
        session_score=50,
        liquidity_score=50,
        correlation_penalty=0,
        feature_redundancy_penalty=0,
        confidence_score=50,
        quality_tier=QualityTier.WATCH,
    )
    ranked = RankedCandidate(
        candidate_id=cid,
        symbol="EURUSD",
        as_of=AS_OF,
        final_rank=1,
        scorecard=card,
        state=state,
        context=context,
    )
    assert ranked.handoff_eligibility is False
    assert ranked.producer == "pm2_market_context"


def test_quality_tier_helper_is_the_band_contract() -> None:
    mapping = [
        (0, QualityTier.SUPPRESS),
        (39, QualityTier.SUPPRESS),
        (40, QualityTier.WATCH),
        (60, QualityTier.ELIGIBLE),
        (75, QualityTier.HIGH),
        (90, QualityTier.TOP),
    ]
    for score, tier in mapping:
        assert quality_tier_for(score) is tier

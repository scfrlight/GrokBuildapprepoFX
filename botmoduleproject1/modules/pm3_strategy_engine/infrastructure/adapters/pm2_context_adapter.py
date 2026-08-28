"""Adapt public PM2 contracts only. No PM2 private imports."""

from __future__ import annotations

from typing import Any

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, QualificationStateName, RankedCandidate
from botmoduleproject1.modules.pm3_strategy_engine.domain.value_objects import (
    EvaluationContext,
    FeatureView,
    SystemFlags,
)


class PM2ContextAdapter:
    def from_candidate(
        self,
        candidate: RankedCandidate,
        *,
        profile_id: str,
        version_id: str,
        params: dict[str, Any],
        stale_ttl_hours: int,
        flags: SystemFlags | None = None,
    ) -> EvaluationContext:
        ctx = candidate.context
        score = candidate.scorecard
        lookahead = ctx.as_of > candidate.as_of
        stale = (
            candidate.state.state is QualificationStateName.STALE
            or ctx.data_quality is DataQualityStatus.STALE
            or (
                candidate.timing_valid_until is not None
                and candidate.as_of >= candidate.timing_valid_until
            )
        )
        malformed = ctx.data_quality in {DataQualityStatus.MALFORMED, DataQualityStatus.INCOMPLETE}
        features = FeatureView(
            family_summary=dict(ctx.feature_family_summary),
            confluence=score.final_confluence_score,
            long_score=score.long_score,
            short_score=score.short_score,
            structure=score.structure_score,
            momentum=score.momentum_score,
            volatility=score.volatility_score,
            session=score.session_score,
        )
        return EvaluationContext(
            symbol=candidate.symbol,
            as_of=candidate.as_of,
            candidate_id=candidate.candidate_id,
            candidate=candidate,
            regime=ctx.regime,
            data_quality=ctx.data_quality,
            stale=stale,
            malformed=malformed,
            lookahead=lookahead,
            handoff_eligible=bool(candidate.handoff_eligibility),
            session_quality=ctx.session_quality,
            side_bias=candidate.side_bias,
            features=features,
            params=params,
            profile_id=profile_id,
            version_id=version_id,
            flags=flags or SystemFlags(),
        )

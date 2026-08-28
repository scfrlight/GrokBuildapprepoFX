"""Candidate qualification state machine."""

from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.pm2 import (
    CandidateQualificationState,
    CandidateScoreCard,
    QualificationStateName,
    QualityTier,
)
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Thresholds


_ALLOWED = {
    QualificationStateName.NEUTRAL: {
        QualificationStateName.FORMING,
        QualificationStateName.SUPPRESSED,
        QualificationStateName.STALE,
    },
    QualificationStateName.FORMING: {
        QualificationStateName.QUALIFIED,
        QualificationStateName.SUPPRESSED,
        QualificationStateName.STALE,
        QualificationStateName.NEUTRAL,
    },
    QualificationStateName.QUALIFIED: {
        QualificationStateName.CONFIRMED,
        QualificationStateName.SUPPRESSED,
        QualificationStateName.STALE,
        QualificationStateName.INVALIDATED,
    },
    QualificationStateName.CONFIRMED: {
        QualificationStateName.COOLDOWN,
        QualificationStateName.INVALIDATED,
        QualificationStateName.STALE,
        QualificationStateName.SUPPRESSED,
    },
    QualificationStateName.COOLDOWN: {
        QualificationStateName.FORMING,
        QualificationStateName.STALE,
        QualificationStateName.NEUTRAL,
    },
    QualificationStateName.SUPPRESSED: {
        QualificationStateName.FORMING,
        QualificationStateName.STALE,
        QualificationStateName.NEUTRAL,
    },
    QualificationStateName.INVALIDATED: {
        QualificationStateName.NEUTRAL,
        QualificationStateName.STALE,
    },
    QualificationStateName.STALE: {
        QualificationStateName.NEUTRAL,
        QualificationStateName.FORMING,
    },
}


def transition(
    current: CandidateQualificationState,
    scorecard: CandidateScoreCard,
    as_of: datetime,
    thresholds: Pm2Thresholds,
    *,
    stale: bool = False,
) -> CandidateQualificationState:
    nxt = current.state
    reason = "hold"
    persist = current.persistence_count
    if stale:
        nxt, reason, persist = QualificationStateName.STALE, "context_expired", 0
    elif scorecard.vetoes or scorecard.quality_tier is QualityTier.SUPPRESS:
        nxt, reason, persist = QualificationStateName.SUPPRESSED, "score_or_veto", 0
    elif current.state is QualificationStateName.NEUTRAL:
        if scorecard.quality_tier is QualityTier.WATCH:
            nxt, reason, persist = QualificationStateName.FORMING, "watch_band", 1
        elif scorecard.final_confluence_score >= thresholds.watch_below:
            nxt, reason, persist = QualificationStateName.FORMING, "score_rising", 1
    elif current.state is QualificationStateName.FORMING:
        if scorecard.final_confluence_score >= thresholds.watch_below:
            persist = current.persistence_count + 1
            if persist >= thresholds.persistence_bars:
                nxt, reason = QualificationStateName.QUALIFIED, "persistence"
            else:
                nxt, reason = QualificationStateName.FORMING, "forming"
        else:
            nxt, reason, persist = QualificationStateName.NEUTRAL, "fade", 0
    elif current.state is QualificationStateName.QUALIFIED:
        persist = current.persistence_count + 1
        if scorecard.quality_tier in {QualityTier.HIGH, QualityTier.TOP} and persist >= thresholds.persistence_bars:
            nxt, reason = QualificationStateName.CONFIRMED, "confirmed_bar"
        else:
            nxt, reason = QualificationStateName.QUALIFIED, "hold_qualified"
    elif current.state is QualificationStateName.CONFIRMED:
        nxt, reason, persist = QualificationStateName.COOLDOWN, "post_confirm_cooldown", 0
    elif current.state is QualificationStateName.SUPPRESSED:
        if scorecard.quality_tier is QualityTier.WATCH and not scorecard.vetoes:
            nxt, reason, persist = QualificationStateName.FORMING, "reset_after_suppress", 1
    if nxt is current.state and reason == "hold":
        persist = current.persistence_count + 1
    if nxt not in _ALLOWED[current.state] and nxt is not current.state:
        nxt, reason = current.state, "illegal_blocked"
    cooldown = None
    if nxt is QualificationStateName.COOLDOWN:
        cooldown = as_of + timedelta(hours=max(1, thresholds.cooldown_bars))
    stale_after = as_of + timedelta(hours=max(1, thresholds.stale_bars))
    return CandidateQualificationState(
        state=nxt,
        entered_at=as_of if nxt is not current.state else current.entered_at,
        persistence_count=persist,
        cooldown_until=cooldown,
        stale_after=stale_after,
        last_transition_reason=reason,
    )


def initial(as_of: datetime) -> CandidateQualificationState:
    return CandidateQualificationState(
        state=QualificationStateName.NEUTRAL,
        entered_at=as_of,
        persistence_count=0,
        last_transition_reason="init",
    )

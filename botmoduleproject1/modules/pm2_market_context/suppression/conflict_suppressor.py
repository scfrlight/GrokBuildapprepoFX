"""Correlation / exposure suppressor. Pair-agnostic, no execution."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import (
    QualificationStateName,
    RankedCandidate,
    SuppressionRecord,
    quality_tier_for,
)
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config
from botmoduleproject1.modules.pm2_market_context.engines.correlation_engine import shared_currency
from botmoduleproject1.modules.pm2_market_context.features.normalization import clamp
from botmoduleproject1.modules.pm2_market_context.qualification.state_machine import transition
from botmoduleproject1.modules.pm2_market_context.suppression.policies import must_suppress
from botmoduleproject1.modules.pm2_market_context.suppression.redundancy_penalties import overlap_penalty


def _apply_penalty(candidate: RankedCandidate, penalty: float) -> RankedCandidate:
    if penalty <= 0:
        return candidate
    card = candidate.scorecard
    final = clamp(card.final_confluence_score - penalty)
    updated = card.model_copy(
        update={
            "correlation_penalty": clamp(card.correlation_penalty + penalty),
            "final_confluence_score": final,
            "quality_tier": quality_tier_for(final),
            "components": {**card.components, "correlation_penalty": penalty},
        }
    )
    return candidate.model_copy(update={"scorecard": updated})


def suppress(
    ranked: tuple[RankedCandidate, ...],
    config: Pm2Config,
) -> tuple[tuple[RankedCandidate, ...], tuple[SuppressionRecord, ...]]:
    """Walk rank order. Keep stronger names; suppress redundant / vetoed."""
    kept: list[RankedCandidate] = []
    records: list[SuppressionRecord] = []
    seen_clusters: set[str] = set()
    kept_symbols: list[str] = []

    for item in ranked:
        reasons = list(must_suppress(item, config))
        cluster = item.correlation_cluster
        if config.one_per_cluster and cluster and cluster in seen_clusters:
            reasons.append("one_per_cluster")
        penalty = overlap_penalty(item.symbol, tuple(kept_symbols))
        adjusted = _apply_penalty(item, penalty)
        if penalty and adjusted.scorecard.quality_tier.value == "suppress":
            reasons.append("redundant_exposure")
        for other in kept:
            if shared_currency(item.symbol, other.symbol) and item.side_bias != "flat":
                if other.side_bias not in {"flat", item.side_bias}:
                    reasons.append(f"conflict:{other.symbol}")
        if reasons:
            state = transition(
                adjusted.state,
                adjusted.scorecard,
                adjusted.as_of,
                config.thresholds,
            )
            if state.state is not QualificationStateName.SUPPRESSED:
                state = adjusted.state.model_copy(
                    update={
                        "state": QualificationStateName.SUPPRESSED,
                        "last_transition_reason": "suppression:" + ",".join(reasons[:3]),
                        "entered_at": adjusted.as_of,
                        "persistence_count": 0,
                    }
                )
            record = SuppressionRecord(
                symbol=item.symbol,
                as_of=item.as_of,
                suppression_reasons=tuple(reasons),
                veto_triggers=item.scorecard.vetoes,
                conflict_group=cluster,
                ghost_tracking_eligibility=config.ghost_tracking,
            )
            records.append(record)
            kept.append(
                adjusted.model_copy(
                    update={
                        "state": state,
                        "suppression": record,
                        "handoff_eligibility": False,
                    }
                )
            )
            continue
        if cluster:
            seen_clusters.add(cluster)
        kept_symbols.append(item.symbol)
        kept.append(adjusted)

    return tuple(kept), tuple(records)

"""Degradation hooks. Alerts only — never auto-adjust weights."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, RankedCandidate


def degradation_alerts(
    ranked: tuple[RankedCandidate, ...],
    *,
    qualities: tuple[DataQualityStatus, ...] = (),
) -> tuple[str, ...]:
    alerts: list[str] = []
    if any(q is not DataQualityStatus.OK for q in qualities):
        alerts.append("data_freshness")
    if ranked:
        mean = sum(c.scorecard.final_confluence_score for c in ranked) / len(ranked)
        if mean < 40:
            alerts.append("weak_shortlist_quality")
        regimes = {c.context.regime.value for c in ranked}
        if "transitional" in regimes and len(regimes) == 1:
            alerts.append("regime_instability")
        ranks_stable = len({c.final_rank for c in ranked}) == len(ranked)
        if not ranks_stable:
            alerts.append("ranking_instability")
    return tuple(alerts)

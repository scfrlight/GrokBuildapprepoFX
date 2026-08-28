"""Publish an immutable PublicationBundle. Identity is deterministic per scan."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid5, NAMESPACE_URL

from botmoduleproject1.contracts.v1.pm2 import (
    PublicationBundle,
    RankedCandidate,
    SuppressionRecord,
)
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config
from botmoduleproject1.modules.pm2_market_context.ranking.shortlist_builder import (
    build_shortlist,
    build_watchlist,
)


def scan_correlation_id(as_of: datetime) -> UUID:
    return uuid5(NAMESPACE_URL, f"pm2:scan:{as_of.isoformat()}")


def scan_event_id(as_of: datetime) -> UUID:
    return uuid5(NAMESPACE_URL, f"pm2:bundle:{as_of.isoformat()}")


def scan_idempotency_key(as_of: datetime) -> str:
    return f"pm2:scan:{as_of.isoformat()}"


def publish(
    ranked: tuple[RankedCandidate, ...],
    suppressed: tuple[SuppressionRecord, ...],
    *,
    as_of: datetime,
    config: Pm2Config,
    diagnostics: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
) -> PublicationBundle:
    shortlist = build_shortlist(ranked, config)
    watchlist = build_watchlist(ranked, shortlist, config)
    correlation = scan_correlation_id(as_of)
    return PublicationBundle(
        event_id=scan_event_id(as_of),
        correlation_id=correlation,
        as_of=as_of,
        shortlist=shortlist,
        watchlist=watchlist,
        suppressed=suppressed,
        diagnostics_summary=diagnostics or {},
        health_summary=health or {},
        calibration_snapshot=calibration or {},
        feature_set_version=config.feature_set_version,
        producer="pm2_market_context",
        idempotency_key=scan_idempotency_key(as_of),
    )

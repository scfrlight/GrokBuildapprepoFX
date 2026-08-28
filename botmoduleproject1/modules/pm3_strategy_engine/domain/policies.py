"""Domain policies: immutability, activation, health. Not risk."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy_engine import HealthStatus, ProfileStatus
from botmoduleproject1.modules.pm3_strategy_engine.domain.enums import ACTIVATABLE, NON_VOTING


def may_edit(status: ProfileStatus, immutable: bool) -> bool:
    if immutable or status is ProfileStatus.ACTIVE:
        return False
    return status is ProfileStatus.DRAFT


def may_activate(status: ProfileStatus) -> bool:
    return status in ACTIVATABLE


def may_vote(status: ProfileStatus) -> bool:
    return status is ProfileStatus.ACTIVE


def dropped_for_status(status: ProfileStatus) -> bool:
    return status in NON_VOTING


def default_health(*, samples: int, invalid: bool, stale_feedback: bool) -> HealthStatus:
    if invalid:
        return HealthStatus.DISABLED
    if stale_feedback:
        return HealthStatus.DEGRADED
    if samples < 20:
        return HealthStatus.UNKNOWN
    return HealthStatus.WATCHLIST

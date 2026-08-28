"""Readiness helpers for degraded publication modes."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus


def publication_allowed(qualities: tuple[DataQualityStatus, ...]) -> bool:
    if not qualities:
        return False
    return all(q is DataQualityStatus.OK for q in qualities)


def watchlist_only(calibration_poor: bool) -> bool:
    return calibration_poor

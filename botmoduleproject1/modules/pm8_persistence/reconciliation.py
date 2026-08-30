"""Reconciliation run aggregate. Unavailable venue cannot PASS. RECONSTRUCTED-SOURCE."""

from __future__ import annotations

from enum import Enum


class ReconciliationRunState(str, Enum):
    STARTED = "started"
    COLLECTING = "collecting"
    MISMATCH_FOUND = "mismatch_found"
    ACKNOWLEDGED = "acknowledged"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    CLOSED = "closed"
    FAILED = "failed"


ALLOWED_TRANSITIONS: dict[ReconciliationRunState, frozenset[ReconciliationRunState]] = {
    ReconciliationRunState.STARTED: frozenset(
        {
            ReconciliationRunState.COLLECTING,
            ReconciliationRunState.MISMATCH_FOUND,
            ReconciliationRunState.FAILED,
            ReconciliationRunState.REJECTED,
        }
    ),
    ReconciliationRunState.COLLECTING: frozenset(
        {
            ReconciliationRunState.MISMATCH_FOUND,
            ReconciliationRunState.RESOLVED,
            ReconciliationRunState.FAILED,
            ReconciliationRunState.CLOSED,
        }
    ),
    ReconciliationRunState.MISMATCH_FOUND: frozenset(
        {
            ReconciliationRunState.ACKNOWLEDGED,
            ReconciliationRunState.REJECTED,
            ReconciliationRunState.FAILED,
        }
    ),
    ReconciliationRunState.ACKNOWLEDGED: frozenset(
        {ReconciliationRunState.REMEDIATION_IN_PROGRESS, ReconciliationRunState.REJECTED}
    ),
    ReconciliationRunState.REMEDIATION_IN_PROGRESS: frozenset(
        {ReconciliationRunState.RESOLVED, ReconciliationRunState.FAILED, ReconciliationRunState.REJECTED}
    ),
    ReconciliationRunState.RESOLVED: frozenset({ReconciliationRunState.CLOSED}),
    ReconciliationRunState.REJECTED: frozenset({ReconciliationRunState.CLOSED}),
    ReconciliationRunState.FAILED: frozenset({ReconciliationRunState.CLOSED}),
    ReconciliationRunState.CLOSED: frozenset(),
}

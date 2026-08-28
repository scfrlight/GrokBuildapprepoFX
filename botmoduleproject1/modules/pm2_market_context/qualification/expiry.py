"""Context expiry / staleness TTL."""

from datetime import datetime

from botmoduleproject1.contracts.v1.pm2 import CandidateQualificationState


def is_stale(state: CandidateQualificationState, as_of: datetime) -> bool:
    if state.stale_after is None:
        return False
    return as_of >= state.stale_after

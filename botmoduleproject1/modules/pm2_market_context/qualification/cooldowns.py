"""Cooldown windows after confirmation."""

from datetime import datetime

from botmoduleproject1.contracts.v1.pm2 import CandidateQualificationState, QualificationStateName


def in_cooldown(state: CandidateQualificationState, as_of: datetime) -> bool:
    if state.state is not QualificationStateName.COOLDOWN:
        return False
    if state.cooldown_until is None:
        return False
    return as_of < state.cooldown_until

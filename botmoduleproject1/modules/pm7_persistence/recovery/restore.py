from botmoduleproject1.contracts.v1.persistence import RecoveryStatus


def restore_request(*, current: RecoveryStatus) -> RecoveryStatus:
    if current is RecoveryStatus.UNAVAILABLE:
        return RecoveryStatus.REQUIRES_REVIEW
    if current is RecoveryStatus.STALE:
        return RecoveryStatus.REQUIRES_REVIEW
    if current is RecoveryStatus.VERIFICATION_FAILED:
        return RecoveryStatus.REQUIRES_REVIEW
    return RecoveryStatus.RESTORE_PENDING

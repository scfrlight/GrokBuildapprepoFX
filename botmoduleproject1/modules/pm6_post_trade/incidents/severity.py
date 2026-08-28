from botmoduleproject1.contracts.v1.post_trade import SeverityLevel

RANK = {
    SeverityLevel.INFO: 0,
    SeverityLevel.LOW: 1,
    SeverityLevel.MEDIUM: 2,
    SeverityLevel.HIGH: 3,
    SeverityLevel.CRITICAL: 4,
}


def worse(a: SeverityLevel, b: SeverityLevel) -> SeverityLevel:
    return a if RANK[a] >= RANK[b] else b

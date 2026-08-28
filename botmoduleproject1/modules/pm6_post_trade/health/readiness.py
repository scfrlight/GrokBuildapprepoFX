from botmoduleproject1.app.health import CheckKind, CheckResult


def readiness_checks(kind: CheckKind, *, enabled: bool, ready: bool) -> list[CheckResult]:
    if kind is not CheckKind.READINESS:
        return []
    return [
        CheckResult(
            name="post_trade.ready",
            kind=kind,
            passed=True,
            critical=False,
            message="ready" if (enabled and ready) else "flag off; NullMonitoring bound in composition root",
        )
    ]

from botmoduleproject1.app.health import CheckKind, CheckResult


def liveness_checks(kind: CheckKind) -> list[CheckResult]:
    if kind is not CheckKind.LIVENESS:
        return []
    return [
        CheckResult(
            name="post_trade.liveness",
            kind=kind,
            passed=True,
            critical=False,
            message="pm6 process alive",
        )
    ]

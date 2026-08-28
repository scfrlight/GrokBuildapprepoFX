from botmoduleproject1.app.health import CheckKind, CheckResult


def liveness_checks(kind: CheckKind) -> list[CheckResult]:
    if kind is not CheckKind.LIVENESS:
        return []
    return [
        CheckResult(
            name="risk_gate.liveness",
            kind=kind,
            passed=True,
            critical=True,
            message="PM4 process heartbeat",
        )
    ]

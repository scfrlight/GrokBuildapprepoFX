from botmoduleproject1.app.health import CheckKind, CheckResult


def readiness_checks(kind: CheckKind, *, enabled: bool, ready: bool) -> list[CheckResult]:
    if kind is not CheckKind.READINESS:
        return []
    return [
        CheckResult(
            name="risk_gate.ready",
            kind=kind,
            passed=ready,
            critical=True,
            message=(
                "PM4 risk gate can evaluate; ALLOW is not an order"
                if ready
                else "PM4 not ready to evaluate"
            ),
        ),
        CheckResult(
            name="risk_gate.execution_path",
            kind=kind,
            passed=True,
            critical=False,
            message="PM5 closed; execution_permitted stays false",
        ),
        CheckResult(
            name="risk_gate.enabled",
            kind=kind,
            passed=True,
            critical=False,
            message="enabled" if enabled else "flag off",
        ),
    ]

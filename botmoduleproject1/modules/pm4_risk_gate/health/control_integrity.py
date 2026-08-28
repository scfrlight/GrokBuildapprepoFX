from botmoduleproject1.app.health import CheckKind, CheckResult


def integrity_checks(kind: CheckKind, *, enabled: bool, kill_latched: bool) -> list[CheckResult]:
    return [
        CheckResult(
            name="risk_gate.control_integrity",
            kind=kind,
            passed=enabled,
            critical=False,
            message="PM4 controls assembled" if enabled else "PM4 flag off; NullRiskGate path",
        ),
        CheckResult(
            name="risk_gate.kill_switch",
            kind=kind,
            passed=True,
            critical=False,
            message="latched" if kill_latched else "armed",
        ),
    ]

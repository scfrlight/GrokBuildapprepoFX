from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.modules.pm4_risk_gate.health.control_integrity import integrity_checks
from botmoduleproject1.modules.pm4_risk_gate.health.liveness import liveness_checks
from botmoduleproject1.modules.pm4_risk_gate.health.readiness import readiness_checks


def health_checks(
    kind: CheckKind,
    *,
    feature_enabled: bool,
    ready: bool,
    kill_latched: bool,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(readiness_checks(kind, enabled=feature_enabled, ready=ready))
    checks.extend(liveness_checks(kind))
    checks.extend(integrity_checks(kind, enabled=feature_enabled, kill_latched=kill_latched))
    if kind is CheckKind.STARTUP:
        checks.append(
            CheckResult(
                name="risk_gate.startup",
                kind=kind,
                passed=True,
                critical=True,
                message="PM4 risk gate imported",
            )
        )
    return checks

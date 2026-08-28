from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.modules.pm6_post_trade.health.control_integrity import integrity_checks
from botmoduleproject1.modules.pm6_post_trade.health.data_quality import quality_checks
from botmoduleproject1.modules.pm6_post_trade.health.liveness import liveness_checks
from botmoduleproject1.modules.pm6_post_trade.health.readiness import readiness_checks


def health_checks(kind: CheckKind, *, enabled: bool, ready: bool, truth: str) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(readiness_checks(kind, enabled=enabled, ready=ready))
    checks.extend(liveness_checks(kind))
    checks.extend(integrity_checks(kind, mt5=False, durable=False))
    checks.extend(quality_checks(kind, truth=truth))
    if kind is CheckKind.STARTUP:
        checks.append(
            CheckResult(
                name="post_trade.startup",
                kind=kind,
                passed=True,
                critical=False,
                message="PM6 post-trade imported; no orders; no MT5",
            )
        )
    return checks

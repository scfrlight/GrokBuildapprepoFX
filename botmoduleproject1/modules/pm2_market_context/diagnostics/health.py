"""PM2 health contributor. Non-critical so the kernel can still boot."""

from __future__ import annotations

from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus, PublicationBundle


def health_checks(
    kind: CheckKind,
    *,
    enabled: bool,
    last_bundle: PublicationBundle | None,
    last_qualities: tuple[DataQualityStatus, ...] = (),
    calibration_ok: bool = True,
) -> list[CheckResult]:
    checks: list[CheckResult] = [
        CheckResult(
            name="pm2.assembled",
            kind=kind,
            passed=True,
            critical=False,
            message="PM2 module assembled; ranking/context only",
        )
    ]
    if kind is CheckKind.STARTUP:
        checks.append(
            CheckResult(
                name="pm2.startup",
                kind=kind,
                passed=True,
                critical=False,
                message="enabled" if enabled else "flag off; NullMarketData would apply if unwired",
            )
        )
        return checks
    if kind is CheckKind.READINESS:
        freshness_ok = (not last_qualities) or all(q is DataQualityStatus.OK for q in last_qualities)
        checks.append(
            CheckResult(
                name="pm2.data_freshness",
                kind=kind,
                passed=freshness_ok,
                critical=False,
                message="fresh" if freshness_ok else "stale or incomplete bars; publication suppressed",
            )
        )
        checks.append(
            CheckResult(
                name="pm2.publication",
                kind=kind,
                passed=last_bundle is not None or not enabled,
                critical=False,
                message="bundle present" if last_bundle is not None else "no scan yet",
            )
        )
        checks.append(
            CheckResult(
                name="pm2.calibration",
                kind=kind,
                passed=calibration_ok,
                critical=False,
                message="telemetry only; weights frozen",
            )
        )
        return checks
    checks.append(
        CheckResult(
            name="pm2.liveness",
            kind=kind,
            passed=True,
            critical=False,
            message="process object alive",
        )
    )
    return checks

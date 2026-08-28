from __future__ import annotations

from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.execution import ExecutionMode, Pm5OperatingState


def health_checks(
    kind: CheckKind,
    *,
    mode: ExecutionMode,
    operating: Pm5OperatingState,
    simulation_enabled: bool,
    kill_latched: bool,
) -> list[CheckResult]:
    checks = [
        CheckResult(
            name="execution.mode",
            kind=kind,
            passed=mode is not ExecutionMode.LIVE,
            critical=True,
            message=f"mode={mode.value}; simulation={simulation_enabled}",
        ),
        CheckResult(
            name="execution.mt5",
            kind=kind,
            passed=True,
            critical=False,
            message="MT5 adapter placeholder_blocked; no MetaTrader5 import",
        ),
        CheckResult(
            name="execution.broker_truth",
            kind=kind,
            passed=True,
            critical=False,
            message="broker truth unavailable; recon default degraded",
        ),
        CheckResult(
            name="execution.control",
            kind=kind,
            passed=True,
            critical=False,
            message=f"operating={operating.value}; kill_latched={kill_latched}",
        ),
    ]
    if kind is CheckKind.STARTUP:
        checks.append(
            CheckResult(
                name="execution.startup",
                kind=kind,
                passed=True,
                critical=False,
                message="PM5 OMS/EMS imported; submit path disabled",
            )
        )
    if kind is CheckKind.LIVENESS:
        checks.append(
            CheckResult(
                name="execution.liveness",
                kind=kind,
                passed=True,
                critical=False,
                message="control plane reachable",
            )
        )
    return checks

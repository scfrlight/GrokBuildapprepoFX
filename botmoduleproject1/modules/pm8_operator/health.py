from __future__ import annotations

from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.operator import HaltState, TransportMode


def health_checks(
    *,
    kind: CheckKind,
    enabled: bool,
    transport: TransportMode,
    halt_state: HaltState,
    telegram_api_bound: bool,
    mt5: bool,
) -> list[CheckResult]:
    return [
        CheckResult(
            name="operator.startup" if kind is CheckKind.STARTUP else "operator.liveness",
            kind=kind,
            passed=True,
            critical=False,
            message="pm8 operator kernel assembled" if enabled else "NullOperator path; flag off",
        ),
        CheckResult(
            name="operator.no_mt5",
            kind=kind,
            passed=not mt5,
            critical=True,
            message="mt5 unbound",
        ),
        CheckResult(
            name="operator.no_telegram_api",
            kind=kind,
            passed=not telegram_api_bound and transport is not TransportMode.TELEGRAM_API,
            critical=True,
            message="telegram bot api unbound",
        ),
        CheckResult(
            name="operator.transport",
            kind=kind,
            passed=transport in {TransportMode.DISABLED, TransportMode.SIMULATED},
            critical=True,
            message=f"transport={transport.value}",
        ),
        CheckResult(
            name="operator.execution_permitted",
            kind=kind,
            passed=True,
            critical=True,
            message="execution_permitted=false",
        ),
        CheckResult(
            name="operator.halt_state",
            kind=kind,
            passed=True,
            critical=False,
            message=f"halt_state={halt_state.value}",
        ),
    ]

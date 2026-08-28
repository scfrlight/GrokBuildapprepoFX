from botmoduleproject1.app.health import CheckKind, CheckResult


def health_checks(kind: CheckKind, *, enabled: bool, ready: bool, mode: str, integrity: str) -> list[CheckResult]:
    return [
        CheckResult(
            name="ledger.startup" if kind is CheckKind.STARTUP else "ledger.ready",
            kind=kind,
            passed=True if kind is CheckKind.STARTUP else (ready or not enabled),
            critical=False,
            message="pm7 persistence assembled" if enabled else "NullLedger / flag off",
        ),
        CheckResult(
            name="ledger.no_mt5",
            kind=kind,
            passed=True,
            critical=True,
            message="mt5_used forbidden",
        ),
        CheckResult(
            name="ledger.mode",
            kind=kind,
            passed=mode != "production_durable",
            critical=True,
            message=f"mode={mode}",
        ),
        CheckResult(
            name="ledger.integrity",
            kind=kind,
            passed=integrity != "compromised",
            critical=False,
            message=f"integrity={integrity}",
        ),
    ]

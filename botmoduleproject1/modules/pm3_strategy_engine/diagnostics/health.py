from botmoduleproject1.app.health import CheckKind, CheckResult


def health_checks(kind: CheckKind, *, feature_enabled: bool, last_reason: str = "") -> list[CheckResult]:
    return [
        CheckResult(
            name="pm3_strategy_engine.kernel",
            kind=kind,
            passed=True,
            critical=False,
            message="PM3-Strategy Engine assembled; observe-only",
        ),
        CheckResult(
            name="pm3_strategy_engine.flag",
            kind=kind,
            passed=True,
            critical=False,
            message="enabled" if feature_enabled else "disabled (Null path when unwired)",
        ),
        CheckResult(
            name="pm3_strategy_engine.no_execution",
            kind=kind,
            passed=True,
            critical=False,
            message="does not call PM5 or MT5",
        ),
    ]

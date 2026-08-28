from botmoduleproject1.app.health import CheckKind, CheckResult


def integrity_checks(kind: CheckKind, *, mt5: bool, durable: bool) -> list[CheckResult]:
    return [
        CheckResult(
            name="post_trade.no_mt5",
            kind=kind,
            passed=not mt5,
            critical=True,
            message="mt5 disabled",
        ),
        CheckResult(
            name="post_trade.non_durable",
            kind=kind,
            passed=not durable,
            critical=False,
            message="in-memory before PM7",
        ),
    ]

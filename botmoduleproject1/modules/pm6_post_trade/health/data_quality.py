from botmoduleproject1.app.health import CheckKind, CheckResult


def quality_checks(kind: CheckKind, *, truth: str) -> list[CheckResult]:
    return [
        CheckResult(
            name="post_trade.truth",
            kind=kind,
            passed=truth != "broker_truth",
            critical=True,
            message=f"truth={truth}",
        )
    ]

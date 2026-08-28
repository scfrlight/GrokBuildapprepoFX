"""PM3 forecasting / QRF health contributor. Non-critical so the kernel can boot."""

from __future__ import annotations

from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.modules.pm3_forecasting.inference.conformal import ConformalTracker


def health_checks(
    kind: CheckKind,
    *,
    feature_enabled: bool,
    tracker: ConformalTracker | None = None,
) -> list[CheckResult]:
    snap = tracker.snapshot() if tracker is not None else {
        "sample_size": 0,
        "coverage_90": None,
        "healthy": False,
    }
    coverage_ok = bool(snap.get("healthy"))
    sample_size = snap.get("sample_size", 0)
    coverage_90 = snap.get("coverage_90")
    coverage_msg = (
        f"empirical 90% coverage={coverage_90!r} n={sample_size}"
        if coverage_ok
        else f"insufficient conformal data (n={sample_size}); not healthy"
    )
    checks = [
        CheckResult(
            name="pm3_forecasting.kernel",
            kind=kind,
            passed=True,
            critical=False,
            message="PM3 forecasting / QRF assembled; residual quantile envelope; observe-only",
        ),
        CheckResult(
            name="pm3_forecasting.flag",
            kind=kind,
            passed=True,
            critical=False,
            message="enabled" if feature_enabled else "disabled (NullModel when unwired)",
        ),
        CheckResult(
            name="pm3_forecasting.coverage",
            kind=kind,
            passed=coverage_ok,
            critical=False,
            message=coverage_msg,
        ),
        CheckResult(
            name="pm3_forecasting.no_execution",
            kind=kind,
            passed=True,
            critical=False,
            message="does not call PM5, MT5, or Telegram; does not mutate side",
        ),
        CheckResult(
            name="pm3_forecasting.estimator",
            kind=kind,
            passed=True,
            critical=False,
            message="residual_quantile_envelope 0.1.0; fitted QRF out of scope",
        ),
    ]
    return checks

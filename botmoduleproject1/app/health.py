"""Startup, readiness, and liveness are distinct probes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.app.exceptions import HealthError


class CheckKind(str, Enum):
    STARTUP = "startup"
    READINESS = "readiness"
    LIVENESS = "liveness"


class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    kind: CheckKind
    passed: bool
    critical: bool = True
    message: str = ""


class HealthReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: CheckKind
    passed: bool
    critical_failed: tuple[str, ...] = ()
    results: tuple[CheckResult, ...] = ()

    @property
    def summary(self) -> str:
        if self.passed:
            return f"{self.kind.value}: ok ({len(self.results)} checks)"
        failed = ", ".join(self.critical_failed) or "non-critical"
        return f"{self.kind.value}: failed ({failed})"


class HealthAggregator:
    def __init__(self) -> None:
        self._providers: list[object] = []

    def add(self, provider: object) -> None:
        self._providers.append(provider)

    def run(self, kind: CheckKind, *, fail_on_critical: bool = True) -> HealthReport:
        results: list[CheckResult] = []
        for provider in self._providers:
            checker = getattr(provider, "health_checks", None)
            if checker is None:
                continue
            results.extend(checker(kind))
        critical_failed = tuple(r.name for r in results if r.critical and not r.passed)
        passed = not critical_failed
        report = HealthReport(
            kind=kind,
            passed=passed,
            critical_failed=critical_failed,
            results=tuple(results),
        )
        if fail_on_critical and kind is CheckKind.STARTUP and not passed:
            raise HealthError(report.summary)
        return report

"""Startup preflight. Runs after config validation, before registry_ready."""

from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from botmoduleproject1.app import python_version as python_version_mod
from botmoduleproject1.app.exceptions import PreflightError
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.app.profiles import ProfileName
from botmoduleproject1.app.secrets import reveal_if_secret
from botmoduleproject1.app.settings import Settings

ROOT = Path(__file__).resolve().parents[2]


class PreflightReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    passed: bool
    profile: str
    checks: tuple[CheckResult, ...] = ()
    summary: str = ""

    def as_health_results(self) -> list[CheckResult]:
        return list(self.checks)


class PreflightService:
    """HealthCheckProvider adapter so preflight appears in STARTUP probes."""

    def __init__(self, report: PreflightReport) -> None:
        self.report = report

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        if kind is CheckKind.STARTUP:
            return list(self.report.checks)
        return [
            CheckResult(
                name="preflight.cached",
                kind=kind,
                passed=self.report.passed,
                critical=True,
                message=self.report.summary,
            )
        ]


def _ok(name: str, message: str, *, critical: bool = True) -> CheckResult:
    return CheckResult(
        name=name, kind=CheckKind.STARTUP, passed=True, critical=critical, message=message
    )


def _fail(name: str, message: str, *, critical: bool = True) -> CheckResult:
    return CheckResult(
        name=name, kind=CheckKind.STARTUP, passed=False, critical=critical, message=message
    )


def check_python_version(*, version: tuple[int, ...] | None = None) -> CheckResult:
    ver = tuple(version or python_version_mod.interpreter_version())
    display = ".".join(str(p) for p in ver[:3])
    if python_version_mod.is_supported(ver):
        return _ok(
            "python.version",
            f"Python {display} satisfies >={python_version_mod.MIN_PYTHON_DISPLAY}",
        )
    return _fail(
        "python.version",
        f"Python {display} is below required {python_version_mod.MIN_PYTHON_DISPLAY}+",
    )


def check_config_file(settings: Settings) -> CheckResult:
    if not settings.config_path:
        return _ok("config.file", "in-memory / default settings (no YAML path)")
    path = Path(settings.config_path)
    if not path.is_file():
        return _fail("config.file", f"config file missing: {path}")
    return _ok("config.file", f"config file readable: {path.name}")


def check_live_blocked(settings: Settings) -> CheckResult:
    if settings.profile is ProfileName.LIVE or settings.safety.trading_mode == "live":
        return _fail("profile.live_blocked", "live profile/mode is hard-blocked")
    if settings.safety.live_trading_enabled:
        return _fail("profile.live_blocked", "LIVE_TRADING_ENABLED is true")
    if not settings.profile_policy.may_enter_running:
        return _fail(
            "profile.live_blocked",
            f"profile {settings.profile.value} may not enter running",
        )
    return _ok(
        "profile.live_blocked",
        f"profile={settings.profile.value} is not live; running is not a trade authorization",
    )


def check_required_secrets(settings: Settings) -> CheckResult:
    missing: list[str] = []
    if settings.mt5.enabled and not reveal_if_secret(settings.mt5.password):
        missing.append(settings.mt5.password_env)
    if settings.telegram.enabled and not reveal_if_secret(settings.telegram.token):
        missing.append(settings.telegram.token_env)
    if settings.persistence.enabled and not reveal_if_secret(settings.persistence.dsn):
        missing.append("BOTMODULEPROJECT1_DATABASE_URL")
    if missing:
        names = ", ".join(missing)
        return _fail(
            "secrets.required",
            f"enabled adapter missing required secret name(s): {names}",
        )
    return _ok("secrets.required", "no enabled adapter is missing a required secret")


def _parse_requirement_names(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*([><=~!].+)?$", stripped)
        if not match:
            continue
        name = match.group(1)
        spec = (match.group(2) or "").strip()
        found.append((name, spec))
    return found


def check_dependencies(*, requirements_path: Path | None = None) -> CheckResult:
    path = requirements_path or (ROOT / "requirements.txt")
    if not path.is_file():
        return _fail("dependencies.pinned", f"requirements file missing: {path}")
    required = _parse_requirement_names(path.read_text(encoding="utf-8"))
    missing: list[str] = []
    present: list[str] = []
    for name, spec in required:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
            continue
        present.append(f"{name}=={version}")
    if missing:
        return _fail(
            "dependencies.pinned",
            "missing distributions: " + ", ".join(missing),
        )
    return _ok(
        "dependencies.pinned",
        f"core distributions importable ({len(present)} checked)",
    )


def check_filesystem(settings: Settings) -> CheckResult:
    problems: list[str] = []
    for label in ("log_dir", "data_dir"):
        raw = getattr(settings.paths, label)
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".preflight_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            problems.append(f"{label}={path}: {exc}")
    if problems:
        return _fail("filesystem.permissions", "; ".join(problems))
    return _ok(
        "filesystem.permissions",
        f"log_dir={settings.paths.log_dir} data_dir={settings.paths.data_dir} writable",
    )


def check_profile_capabilities(settings: Settings) -> CheckResult:
    policy = settings.profile_policy
    names = ", ".join(c.value for c in policy.allowed_capabilities) or "(none)"
    return _ok(
        "profile.capabilities",
        f"profile={policy.name.value} allowed_capabilities={names}",
        critical=False,
    )


def run_preflight(
    settings: Settings,
    *,
    python_version: tuple[int, ...] | None = None,
    requirements_path: Path | None = None,
    fail_fast: bool = True,
) -> PreflightReport:
    checks = [
        check_python_version(version=python_version),
        check_config_file(settings),
        check_live_blocked(settings),
        check_required_secrets(settings),
        check_dependencies(requirements_path=requirements_path),
        check_filesystem(settings),
        check_profile_capabilities(settings),
    ]
    critical_failed = tuple(c.name for c in checks if c.critical and not c.passed)
    passed = not critical_failed
    if passed:
        summary = f"preflight ok ({len(checks)} checks) profile={settings.profile.value}"
    else:
        summary = "preflight failed: " + ", ".join(critical_failed)
    report = PreflightReport(
        passed=passed,
        profile=settings.profile.value,
        checks=tuple(checks),
        summary=summary,
    )
    if fail_fast and not passed:
        raise PreflightError(summary)
    return report


def report_payload(report: PreflightReport) -> dict[str, Any]:
    return {
        "passed": report.passed,
        "profile": report.profile,
        "summary": report.summary,
        "checks": [c.model_dump(mode="json") for c in report.checks],
    }

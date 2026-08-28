"""Public bootstrap API used by the CLI. No business logic here."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from botmoduleproject1.app.container import Container, build_container
from botmoduleproject1.app.exceptions import LiveTradingDisabledError
from botmoduleproject1.app.feature_flags import CATALOG_BY_FIELD, SafetyClassification
from botmoduleproject1.app.profiles import ProfileName
from botmoduleproject1.app.runtime import Runtime, boot
from botmoduleproject1.app.settings import CliMode, Settings, load_settings
from botmoduleproject1.contracts.v1.journal import EventType, JournalEntry
from botmoduleproject1.contracts.v1.time import utc_now


def _audit_dangerous_flags(container: Container) -> None:
    settings = container.settings
    try:
        storage = container.registry.get("pm8_persistence").instance
    except Exception:
        return
    append = getattr(storage, "append", None)
    if append is None:
        return
    opted = set(settings.feature_flags.env_opt_in)
    for field, spec in CATALOG_BY_FIELD.items():
        if spec.safety is not SafetyClassification.DANGEROUS:
            continue
        if not bool(getattr(settings.feature_flags, field)):
            continue
        entry = JournalEntry(
            occurred_at=utc_now(),
            event_type=EventType.CONFIG,
            producer="pm1_platform",
            summary=f"dangerous feature flag enabled: {spec.name}",
            attributes={
                "flag": spec.name,
                "field": field,
                "profile": settings.profile.value,
                "source": "env" if field in opted else "unknown",
                "safety": spec.safety.value,
            },
        )
        append(entry)


def bootstrap(
    *,
    config_path: str | Path | None = None,
    cli_mode: CliMode = "doctor",
    environ: dict[str, str] | None = None,
    overrides: dict[str, Any] | None = None,
    heartbeat_ticks: int = 0,
    profile: str | ProfileName | None = None,
    env_file: str | Path | None = None,
) -> tuple[Settings, Container, Runtime]:
    settings = load_settings(
        config_path=config_path,
        environ=environ,
        cli_mode=cli_mode,
        profile=profile,
        env_file=env_file,
    )
    container = build_container(settings, overrides=overrides)
    _audit_dangerous_flags(container)
    runtime, _snapshot = boot(container, heartbeat_ticks=heartbeat_ticks)
    return settings, container, runtime


def doctor(
    *,
    config_path: str | Path | None = None,
    environ: dict[str, str] | None = None,
    overrides: dict[str, Any] | None = None,
    profile: str | ProfileName | None = None,
) -> dict[str, Any]:
    settings, _container, runtime = bootstrap(
        config_path=config_path,
        cli_mode="doctor",
        environ=environ,
        overrides=overrides,
        heartbeat_ticks=0,
        profile=profile,
    )
    assert runtime.last_snapshot is not None
    payload = runtime.last_snapshot.model_dump(mode="json")
    payload["fingerprint"] = settings.fingerprint()
    runtime.stop()
    return payload


__all__ = ["LiveTradingDisabledError", "bootstrap", "doctor"]

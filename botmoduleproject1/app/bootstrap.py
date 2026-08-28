"""Public bootstrap API used by the CLI. No business logic here."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from botmoduleproject1.app.container import Container, build_container
from botmoduleproject1.app.exceptions import LiveTradingDisabledError
from botmoduleproject1.app.runtime import Runtime, boot
from botmoduleproject1.app.settings import CliMode, Settings, load_settings


def bootstrap(
    *,
    config_path: str | Path | None = None,
    cli_mode: CliMode = "doctor",
    environ: dict[str, str] | None = None,
    overrides: dict[str, Any] | None = None,
    heartbeat_ticks: int = 0,
) -> tuple[Settings, Container, Runtime]:
    settings = load_settings(
        config_path=config_path, environ=environ, cli_mode=cli_mode
    )
    container = build_container(settings, overrides=overrides)
    runtime, _snapshot = boot(container, heartbeat_ticks=heartbeat_ticks)
    return settings, container, runtime


def doctor(
    *,
    config_path: str | Path | None = None,
    environ: dict[str, str] | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings, _container, runtime = bootstrap(
        config_path=config_path,
        cli_mode="doctor",
        environ=environ,
        overrides=overrides,
        heartbeat_ticks=0,
    )
    assert runtime.last_snapshot is not None
    payload = runtime.last_snapshot.model_dump(mode="json")
    payload["fingerprint"] = settings.fingerprint()
    runtime.stop()
    return payload


__all__ = ["LiveTradingDisabledError", "bootstrap", "doctor"]

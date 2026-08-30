"""PM1 composition root package.

Lazy exports keep `python -m botmoduleproject1` from importing pydantic
before the ADR-008 version guard runs.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "LifecycleState",
    "LiveTradingDisabledError",
    "Settings",
    "bootstrap",
    "doctor",
    "load_settings",
]


def __getattr__(name: str) -> Any:
    if name in {"bootstrap", "doctor"}:
        from botmoduleproject1.app.bootstrap import bootstrap, doctor

        return bootstrap if name == "bootstrap" else doctor
    if name in {"Settings", "load_settings"}:
        from botmoduleproject1.app.settings import Settings, load_settings

        return Settings if name == "Settings" else load_settings
    if name == "LiveTradingDisabledError":
        from botmoduleproject1.app.exceptions import LiveTradingDisabledError

        return LiveTradingDisabledError
    if name == "LifecycleState":
        from botmoduleproject1.app.lifecycle import LifecycleState

        return LifecycleState
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

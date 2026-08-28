"""Diagnostic payload helpers."""

from __future__ import annotations

from typing import Any


def empty_diagnostics() -> dict[str, Any]:
    return {"enabled": True, "producer": "pm2_market_context"}

"""Forecast identity helpers. New UUIDs; cache enforces idempotency."""

from __future__ import annotations

from uuid import UUID, uuid4, uuid5, NAMESPACE_URL


def new_forecast_id() -> UUID:
    return uuid4()


def new_event_id() -> UUID:
    return uuid4()


def memory_registry_uri(model_id: str, version: str) -> str:
    return f"memory://pm3_forecasting/{model_id}/{version}"


def registry_key(model_id: str, version: str) -> str:
    return f"{model_id}:{version}"


def deterministic_locator(model_id: str, version: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"pm3_forecasting:{model_id}:{version}")

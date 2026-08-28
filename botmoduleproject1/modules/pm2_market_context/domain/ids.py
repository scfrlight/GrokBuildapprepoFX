"""Deterministic candidate identifiers."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid5, NAMESPACE_URL


def candidate_id(symbol: str, as_of: datetime) -> UUID:
    stamp = as_of.astimezone().isoformat()
    return uuid5(NAMESPACE_URL, f"pm2:{symbol}:{stamp}")


def cluster_id(base: str, quote: str) -> str:
    return f"{base}|{quote}"

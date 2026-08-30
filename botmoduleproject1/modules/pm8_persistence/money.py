"""Decimal-safe money / quantity types for PM8 persistence.

RECONSTRUCTED-SOURCE relative to PM8a accounting fields. Not a venue.

SQLite stores canonical decimal strings. PostgreSQL maps money columns to NUMERIC(28, 8).
`production_durable` remains refused even when PostgreSQL is configured.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Any, Mapping

MONEY_FIELDS: frozenset[str] = frozenset(
    {
        "price",
        "qty",
        "quantity",
        "volume",
        "notional",
        "commission",
        "swap",
        "spread",
        "slippage",
        "realized_pnl",
        "unrealized_pnl",
        "fees",
        "execution_cost",
        "execution_costs",
        "risk_amount",
        "avg_px",
        "fill_qty",
        "fill_price",
    }
)

DEFAULT_SCALE = 8
QUANTIZE = Decimal("1e-8")
ROUNDING = ROUND_HALF_EVEN


class MoneyError(ValueError):
    pass


def decimal_from(value: Any, *, field: str = "amount") -> Decimal:
    if value is None:
        raise MoneyError(f"{field} is required")
    if isinstance(value, bool):
        raise MoneyError(f"{field} must not be bool")
    if isinstance(value, float):
        raise MoneyError(f"{field} must not be float; pass str or Decimal")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise MoneyError(f"{field} is not a finite decimal") from exc
    if not amount.is_finite():
        raise MoneyError(f"{field} NaN/Infinity forbidden")
    return amount.quantize(QUANTIZE, rounding=ROUNDING)


def canonical(value: Any, *, field: str = "amount") -> str:
    return format(decimal_from(value, field=field), "f")


def sanitize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Convert known money keys to canonical decimal strings. Reject float."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if key in MONEY_FIELDS or key.endswith("_pnl") or key.endswith("_px"):
            if value is None:
                out[key] = value
                continue
            if isinstance(value, float):
                raise MoneyError(f"{key} must not be float")
            out[key] = canonical(value, field=key)
        else:
            out[key] = value
    return out

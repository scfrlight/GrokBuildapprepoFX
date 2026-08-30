"""Named read-model projections. Not canonical truth. RECONSTRUCTED-SOURCE."""

from __future__ import annotations

NAMED_PROJECTIONS: tuple[str, ...] = (
    "open_orders",
    "open_positions",
    "closed_trades",
    "symbol_performance",
    "profile_performance",
    "daily_summary",
    "operator_dashboard",
    "reconciliation_alerts",
    "strategy_memory",
    "anomaly_summary",
)

CLOSED_ORDER_STATES = frozenset({"filled", "cancelled", "canceled", "closed", "rejected", "expired"})

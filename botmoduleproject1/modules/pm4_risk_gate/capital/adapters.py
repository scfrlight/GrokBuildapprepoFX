"""PM3 / forecast / PM8 adapters into the capital request. No execution adapter."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput
from botmoduleproject1.contracts.v1.pm4_capital import QuantileBand, RiskEvaluationRequest
from botmoduleproject1.contracts.v1.strategy import Direction, TradeIntent


def request_from_intent(
    intent: TradeIntent,
    *,
    equity: Decimal,
    peak_equity: Decimal,
    spread: Decimal,
    as_of: datetime,
    forecast: ForecastOutput | None = None,
    **extra: Any,
) -> RiskEvaluationRequest:
    side = "buy" if intent.direction is Direction.BUY else "sell"
    stop = None
    take_profit = None
    if intent.exit_plan is not None:
        stop = intent.exit_plan.stop_loss or intent.exit_plan.stop_price
        take_profit = intent.exit_plan.take_profit
    entry = intent.entry_price or Decimal("0")
    band = None
    model_id = None
    model_version = None
    quality = extra.get("model_quality_status", "unknown")
    if forecast is not None:
        q = forecast.quantiles
        band = QuantileBand(q05=q.q05, q25=q.q25, q50=q.q50, q75=q.q75, q95=q.q95)
        model_id = str(forecast.forecast_id)
        model_version = forecast.model.version
        quality = extra.get("model_quality_status", "ok")
    payload = dict(
        request_id=str(uuid4()),
        idempotency_key=intent.idempotency_key or str(intent.intent_id),
        correlation_id=str(intent.correlation_id),
        causation_id=str(intent.event_id),
        trade_intent_id=str(intent.intent_id),
        strategy_id=intent.profile_id or "strategy",
        strategy_version=intent.version_id or "v1",
        profile_id=intent.profile_id or "profile",
        profile_version=intent.version_id or "v1",
        symbol=intent.symbol,
        timeframe="H1",
        side=side,
        requested_quantity=intent.requested_volume or Decimal("1.00"),
        entry_price=entry,
        stop_loss_price=stop or Decimal("0"),
        take_profit_price=take_profit,
        signal_timestamp=intent.occurred_at,
        intent_created_at=intent.occurred_at,
        market_snapshot_id=extra.get("market_snapshot_id", "mkt"),
        regime_snapshot_id=extra.get("regime_snapshot_id", "reg"),
        model_snapshot_id=model_id,
        model_version=model_version,
        model_quality_status=quality,
        predicted_quantiles=band,
        spread=spread,
        estimated_slippage=extra.get("estimated_slippage", Decimal("0.00010")),
        estimated_commission=extra.get("estimated_commission", Decimal("2")),
        account_snapshot_id=extra.get("account_snapshot_id", "acct"),
        portfolio_snapshot_id=extra.get("portfolio_snapshot_id", "port"),
        current_positions_snapshot_id=extra.get("current_positions_snapshot_id", "pos"),
        current_orders_snapshot_id=extra.get("current_orders_snapshot_id", "ord"),
        risk_policy_version=extra.get("risk_policy_version", "1.0.0"),
        execution_policy_version=extra.get("execution_policy_version", "sim-1"),
        account_equity=equity,
        peak_equity=peak_equity,
        free_margin=extra.get("free_margin", equity),
        session=extra.get("session", "london"),
        regime=intent.regime_state or "trending",
        conversion_rate=extra.get("conversion_rate", Decimal("1")),
    )
    for key in (
        "realized_pnl_day",
        "open_position_risk",
        "pending_order_risk",
        "open_position_count",
        "pending_order_count",
        "symbol_exposure",
        "currency_exposure",
        "directional_exposure",
        "strategy_exposure",
        "profile_exposure",
        "correlated_exposure",
        "market_age_seconds",
        "account_age_seconds",
        "portfolio_age_seconds",
        "model_age_seconds",
        "account_unknown",
        "exposure_unknown",
        "open_orders_unknown",
        "reconciliation_status",
        "reconciliation_critical",
        "safe_halt",
        "control_state",
        "losing_streak",
        "existing_symbol_side",
        "expected_return",
        "expected_adverse_excursion",
        "contract_size",
        "volume_step",
        "persistence_available",
        "cooldown_until",
        "take_profit_price",
    ):
        if key in extra:
            payload[key] = extra[key]
    return RiskEvaluationRequest(**payload)

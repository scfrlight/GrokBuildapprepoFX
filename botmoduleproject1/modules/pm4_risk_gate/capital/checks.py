"""Independent capital checks. Missing data fails closed."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.pm4_capital import (
    CheckOutcome,
    CheckStatus,
    RiskEvaluationRequest,
)
from botmoduleproject1.modules.pm4_risk_gate.capital.catalog import CHECK_CATALOG
from botmoduleproject1.modules.pm4_risk_gate.capital.portfolio import heat_after
from botmoduleproject1.modules.pm4_risk_gate.capital.sizing import stop_distance
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm8_persistence.money import canonical

_ZERO = Decimal("0")


def _out(
    name: str,
    *,
    status: CheckStatus,
    reason: str,
    config: Pm4RiskGateConfig,
    measured: str | None = None,
    limit: str | None = None,
    blocking: bool = True,
    severity: str = "high",
) -> CheckOutcome:
    return CheckOutcome(
        name=name,
        status=status,
        measured=measured,
        limit=limit,
        severity=severity,
        reason=reason,
        policy_version=config.policy_version,
        blocking=blocking and status in {CheckStatus.FAIL, CheckStatus.BLOCK},
    )


def run_checks(
    request: RiskEvaluationRequest,
    config: Pm4RiskGateConfig,
    *,
    now: datetime,
    halt: bool,
    persistence_ok: bool,
    projected_risk: Decimal | None,
    sizing_error: str | None,
) -> list[CheckOutcome]:
    results: dict[str, CheckOutcome] = {}

    def put(item: CheckOutcome) -> None:
        results[item.name] = item

    put(_out("input_schema", status=CheckStatus.PASS, reason="schema accepted", config=config, blocking=False, severity="info"))
    put(_out("idempotency", status=CheckStatus.PASS, reason="key present", config=config, measured=request.idempotency_key, blocking=False, severity="info"))

    if request.market_age_seconds > config.market_stale_seconds:
        put(_out("market_freshness", status=CheckStatus.FAIL, reason="market snapshot stale", config=config, measured=str(request.market_age_seconds), limit=str(config.market_stale_seconds)))
    else:
        put(_out("market_freshness", status=CheckStatus.PASS, reason="market fresh", config=config, measured=str(request.market_age_seconds), limit=str(config.market_stale_seconds), blocking=False, severity="info"))

    if request.account_unknown or request.account_equity <= 0:
        put(_out("account_freshness", status=CheckStatus.BLOCK, reason="account equity unknown", config=config, severity="critical"))
    elif request.account_age_seconds > config.account_stale_seconds:
        put(_out("account_freshness", status=CheckStatus.FAIL, reason="account snapshot stale", config=config, measured=str(request.account_age_seconds), limit=str(config.account_stale_seconds)))
    elif request.free_margin < config.free_margin_floor:
        put(_out("account_freshness", status=CheckStatus.FAIL, reason="free margin below floor", config=config, measured=canonical(request.free_margin), limit=canonical(config.free_margin_floor)))
    else:
        put(_out("account_freshness", status=CheckStatus.PASS, reason="account fresh", config=config, blocking=False, severity="info"))

    if request.exposure_unknown:
        put(_out("portfolio_freshness", status=CheckStatus.BLOCK, reason="exposure unknown", config=config, severity="critical"))
    elif request.portfolio_age_seconds > config.account_stale_seconds:
        put(_out("portfolio_freshness", status=CheckStatus.FAIL, reason="portfolio snapshot stale", config=config, measured=str(request.portfolio_age_seconds)))
    else:
        put(_out("portfolio_freshness", status=CheckStatus.PASS, reason="portfolio fresh", config=config, blocking=False, severity="info"))

    if request.session not in config.session_allow:
        put(_out("session_eligibility", status=CheckStatus.FAIL, reason="session not permitted", config=config, measured=request.session, limit=",".join(config.session_allow)))
    else:
        put(_out("session_eligibility", status=CheckStatus.PASS, reason="session allowed", config=config, measured=request.session, blocking=False, severity="info"))

    if request.regime.lower() in {"unknown", "invalid", ""}:
        put(_out("regime_eligibility", status=CheckStatus.FAIL, reason="regime ineligible", config=config, measured=request.regime))
    else:
        put(_out("regime_eligibility", status=CheckStatus.PASS, reason="regime eligible", config=config, measured=request.regime, blocking=False, severity="info"))

    if request.symbol not in config.allowed_symbols:
        put(_out("symbol_eligibility", status=CheckStatus.FAIL, reason="symbol not on allowlist", config=config, measured=request.symbol))
    else:
        put(_out("symbol_eligibility", status=CheckStatus.PASS, reason="symbol allowed", config=config, measured=request.symbol, blocking=False, severity="info"))

    if not request.strategy_id or not request.profile_id or not request.strategy_version or not request.profile_version:
        put(_out("strategy_profile_eligibility", status=CheckStatus.FAIL, reason="strategy/profile version missing", config=config))
    else:
        put(_out("strategy_profile_eligibility", status=CheckStatus.PASS, reason="strategy/profile present", config=config, blocking=False, severity="info"))

    if config.require_model and not request.model_snapshot_id:
        put(_out("model_availability", status=CheckStatus.FAIL, reason="model snapshot required", config=config))
    else:
        put(_out("model_availability", status=CheckStatus.PASS, reason="model present or not required", config=config, blocking=False, severity="info"))

    if config.require_model and request.model_age_seconds > config.model_stale_seconds:
        put(_out("model_freshness", status=CheckStatus.FAIL, reason="model stale", config=config, measured=str(request.model_age_seconds), limit=str(config.model_stale_seconds)))
    else:
        put(_out("model_freshness", status=CheckStatus.PASS, reason="model fresh", config=config, blocking=False, severity="info"))

    quality_ok = request.model_quality_status in {"ok", "pass", "valid", "good"}
    if config.require_model and not quality_ok:
        put(_out("model_quality", status=CheckStatus.FAIL, reason="model quality unknown or failed", config=config, measured=request.model_quality_status))
    else:
        put(_out("model_quality", status=CheckStatus.PASS, reason="model quality acceptable", config=config, measured=request.model_quality_status, blocking=False, severity="info"))

    if config.require_model:
        band = request.predicted_quantiles
        if band is None:
            put(_out("model_uncertainty", status=CheckStatus.FAIL, reason="quantiles missing", config=config))
        else:
            span = band.q95 - band.q05
            if span > config.max_uncertainty_span:
                put(_out("model_uncertainty", status=CheckStatus.FAIL, reason="uncertainty exceeds maximum", config=config, measured=canonical(span), limit=canonical(config.max_uncertainty_span)))
            else:
                put(_out("model_uncertainty", status=CheckStatus.PASS, reason="uncertainty within cap", config=config, measured=canonical(span), blocking=False, severity="info"))
    else:
        put(_out("model_uncertainty", status=CheckStatus.SKIP, reason="model not required", config=config, blocking=False, severity="info"))

    if request.spread > config.max_spread:
        put(_out("spread_limit", status=CheckStatus.FAIL, reason="spread exceeds limit", config=config, measured=canonical(request.spread), limit=canonical(config.max_spread)))
    else:
        put(_out("spread_limit", status=CheckStatus.PASS, reason="spread ok", config=config, measured=canonical(request.spread), blocking=False, severity="info"))

    if request.estimated_slippage > config.max_slippage:
        put(_out("slippage_limit", status=CheckStatus.FAIL, reason="slippage exceeds limit", config=config, measured=canonical(request.estimated_slippage), limit=canonical(config.max_slippage)))
    else:
        put(_out("slippage_limit", status=CheckStatus.PASS, reason="slippage ok", config=config, measured=canonical(request.estimated_slippage), blocking=False, severity="info"))

    if request.estimated_commission > config.max_commission:
        put(_out("commission_cost_limit", status=CheckStatus.FAIL, reason="commission exceeds limit", config=config, measured=canonical(request.estimated_commission), limit=canonical(config.max_commission)))
    else:
        edge = request.expected_return
        cost = request.estimated_commission + request.estimated_swap
        if edge is not None and edge > 0 and cost / edge > config.max_cost_to_edge:
            put(_out("commission_cost_limit", status=CheckStatus.FAIL, reason="cost-to-edge exceeds policy", config=config, measured=canonical(cost / edge), limit=canonical(config.max_cost_to_edge)))
        else:
            put(_out("commission_cost_limit", status=CheckStatus.PASS, reason="cost ok", config=config, blocking=False, severity="info"))

    try:
        stop = stop_distance(request)
        put(_out("stop_loss_existence", status=CheckStatus.PASS, reason="stop present", config=config, measured=canonical(stop), blocking=False, severity="info"))
        if stop < config.min_stop_distance or stop > config.max_stop_distance:
            put(_out("stop_loss_distance", status=CheckStatus.FAIL, reason="stop distance outside bounds", config=config, measured=canonical(stop), limit=f"{config.min_stop_distance}-{config.max_stop_distance}"))
        else:
            put(_out("stop_loss_distance", status=CheckStatus.PASS, reason="stop distance ok", config=config, measured=canonical(stop), blocking=False, severity="info"))
        if request.take_profit_price is not None and stop > 0:
            if request.side == "buy":
                reward = request.take_profit_price - request.entry_price
            else:
                reward = request.entry_price - request.take_profit_price
            rr = reward / stop if stop else _ZERO
            if rr < config.min_reward_risk:
                put(_out("min_reward_risk", status=CheckStatus.FAIL, reason="reward/risk below minimum", config=config, measured=canonical(rr), limit=canonical(config.min_reward_risk)))
            else:
                put(_out("min_reward_risk", status=CheckStatus.PASS, reason="reward/risk ok", config=config, measured=canonical(rr), blocking=False, severity="info"))
        else:
            put(_out("min_reward_risk", status=CheckStatus.SKIP, reason="take-profit not provided", config=config, blocking=False, severity="low"))
    except Exception as exc:
        put(_out("stop_loss_existence", status=CheckStatus.FAIL, reason=str(exc), config=config))
        put(_out("stop_loss_distance", status=CheckStatus.FAIL, reason="stop unusable", config=config))
        put(_out("min_reward_risk", status=CheckStatus.FAIL, reason="stop unusable", config=config))

    if request.requested_quantity <= 0:
        put(_out("position_size_validity", status=CheckStatus.FAIL, reason="non-positive quantity", config=config, measured=canonical(request.requested_quantity)))
    elif sizing_error:
        put(_out("position_size_validity", status=CheckStatus.FAIL, reason=sizing_error, config=config))
    else:
        put(_out("position_size_validity", status=CheckStatus.PASS, reason="quantity usable", config=config, blocking=False, severity="info"))

    cap = request.account_equity * config.max_per_trade_risk_pct if request.account_equity > 0 else _ZERO
    risk = projected_risk if projected_risk is not None else _ZERO
    if projected_risk is not None and request.account_equity > 0 and risk > cap:
        put(_out("max_single_trade_risk", status=CheckStatus.FAIL, reason="single-trade risk exceeds cap", config=config, measured=canonical(risk), limit=canonical(cap)))
    else:
        put(_out("max_single_trade_risk", status=CheckStatus.PASS, reason="single-trade risk ok", config=config, measured=canonical(risk), blocking=False, severity="info"))

    daily_cap = request.account_equity * config.max_daily_loss_pct if request.account_equity > 0 else _ZERO
    day_loss = abs(min(request.realized_pnl_day, _ZERO))
    if request.account_equity > 0 and day_loss >= daily_cap:
        put(_out("daily_loss_limit", status=CheckStatus.FAIL, reason="daily loss limit reached", config=config, measured=canonical(day_loss), limit=canonical(daily_cap)))
    else:
        put(_out("daily_loss_limit", status=CheckStatus.PASS, reason="daily loss inside cap", config=config, measured=canonical(day_loss), blocking=False, severity="info"))

    if request.account_equity > 0 and request.peak_equity > 0:
        dd = (request.peak_equity - request.account_equity) / request.peak_equity
        if request.account_equity < config.equity_floor:
            put(_out("equity_drawdown_limit", status=CheckStatus.FAIL, reason="equity floor breached", config=config, measured=canonical(request.account_equity), limit=canonical(config.equity_floor)))
        elif dd >= config.dd_freeze:
            put(_out("equity_drawdown_limit", status=CheckStatus.FAIL, reason="drawdown freeze", config=config, measured=canonical(dd), limit=canonical(config.dd_freeze)))
        else:
            put(_out("equity_drawdown_limit", status=CheckStatus.PASS, reason="drawdown inside freeze", config=config, measured=canonical(dd), blocking=False, severity="info"))
    else:
        put(_out("equity_drawdown_limit", status=CheckStatus.BLOCK, reason="cannot compute drawdown", config=config, severity="critical"))

    if request.losing_streak >= config.consecutive_loss_limit:
        put(_out("consecutive_loss", status=CheckStatus.FAIL, reason="losing streak lock", config=config, measured=str(request.losing_streak), limit=str(config.consecutive_loss_limit)))
    else:
        put(_out("consecutive_loss", status=CheckStatus.PASS, reason="streak inside cap", config=config, measured=str(request.losing_streak), blocking=False, severity="info"))

    try:
        after = heat_after(request, risk)
        if after > config.max_effective_heat:
            put(_out("portfolio_heat", status=CheckStatus.FAIL, reason="portfolio heat would exceed cap", config=config, measured=canonical(after), limit=canonical(config.max_effective_heat)))
        else:
            put(_out("portfolio_heat", status=CheckStatus.PASS, reason="heat inside cap", config=config, measured=canonical(after), blocking=False, severity="info"))
    except Exception as exc:
        put(_out("portfolio_heat", status=CheckStatus.BLOCK, reason=str(exc), config=config, severity="critical"))

    if request.account_equity > 0:
        sym = (request.symbol_exposure + risk) / request.account_equity
        ccy = (request.currency_exposure + risk) / request.account_equity
        direc = (abs(request.directional_exposure) + risk) / request.account_equity
        strat = (request.strategy_exposure + risk) / request.account_equity
        prof = (request.profile_exposure + risk) / request.account_equity
        corr = (request.correlated_exposure + risk) / request.account_equity
        put(_out("symbol_exposure", status=CheckStatus.FAIL if sym > config.max_symbol_exposure_pct else CheckStatus.PASS, reason="symbol exposure", config=config, measured=canonical(sym), limit=canonical(config.max_symbol_exposure_pct), blocking=sym > config.max_symbol_exposure_pct, severity="high" if sym > config.max_symbol_exposure_pct else "info"))
        put(_out("currency_exposure", status=CheckStatus.FAIL if ccy > config.max_currency_exposure_pct else CheckStatus.PASS, reason="currency exposure", config=config, measured=canonical(ccy), limit=canonical(config.max_currency_exposure_pct), blocking=ccy > config.max_currency_exposure_pct, severity="high" if ccy > config.max_currency_exposure_pct else "info"))
        put(_out("directional_exposure", status=CheckStatus.FAIL if direc > config.max_currency_exposure_pct else CheckStatus.PASS, reason="directional exposure", config=config, measured=canonical(direc), limit=canonical(config.max_currency_exposure_pct), blocking=direc > config.max_currency_exposure_pct, severity="high" if direc > config.max_currency_exposure_pct else "info"))
        put(_out("correlation_concentration", status=CheckStatus.FAIL if corr > config.max_correlation_pct else CheckStatus.PASS, reason="correlated exposure", config=config, measured=canonical(corr), limit=canonical(config.max_correlation_pct), blocking=corr > config.max_correlation_pct, severity="high" if corr > config.max_correlation_pct else "info"))
        put(_out("strategy_concentration", status=CheckStatus.FAIL if strat > config.max_strategy_pct else CheckStatus.PASS, reason="strategy concentration", config=config, measured=canonical(strat), limit=canonical(config.max_strategy_pct), blocking=strat > config.max_strategy_pct, severity="medium" if strat > config.max_strategy_pct else "info"))
        put(_out("profile_allocation", status=CheckStatus.FAIL if prof > config.max_profile_pct else CheckStatus.PASS, reason="profile allocation", config=config, measured=canonical(prof), limit=canonical(config.max_profile_pct), blocking=prof > config.max_profile_pct, severity="medium" if prof > config.max_profile_pct else "info"))
    else:
        for name in ("symbol_exposure", "currency_exposure", "directional_exposure", "correlation_concentration", "strategy_concentration", "profile_allocation"):
            put(_out(name, status=CheckStatus.BLOCK, reason="equity unknown", config=config, severity="critical"))

    if request.open_orders_unknown:
        put(_out("open_order_exposure", status=CheckStatus.BLOCK, reason="open orders unknown", config=config, severity="critical"))
        put(_out("pending_order_exposure", status=CheckStatus.BLOCK, reason="pending orders unknown", config=config, severity="critical"))
    else:
        put(_out("open_order_exposure", status=CheckStatus.PASS, reason="open orders known", config=config, measured=str(request.open_position_count), blocking=False, severity="info"))
        put(_out("pending_order_exposure", status=CheckStatus.PASS, reason="pending orders known", config=config, measured=str(request.pending_order_count), blocking=False, severity="info"))

    if request.existing_symbol_side and request.existing_symbol_side.lower() == request.side:
        put(_out("duplicate_position", status=CheckStatus.FAIL, reason="duplicate same-side position", config=config, measured=request.existing_symbol_side))
    else:
        put(_out("duplicate_position", status=CheckStatus.PASS, reason="no duplicate same-side position", config=config, blocking=False, severity="info"))

    if request.cooldown_until is not None and request.cooldown_until > now:
        put(_out("cooldown", status=CheckStatus.FAIL, reason="cooldown active", config=config, measured=request.cooldown_until.isoformat()))
    else:
        put(_out("cooldown", status=CheckStatus.PASS, reason="no cooldown", config=config, blocking=False, severity="info"))

    if request.open_position_count >= config.max_simultaneous_positions:
        put(_out("max_simultaneous_positions", status=CheckStatus.FAIL, reason="simultaneous position cap", config=config, measured=str(request.open_position_count), limit=str(config.max_simultaneous_positions)))
    else:
        put(_out("max_simultaneous_positions", status=CheckStatus.PASS, reason="position count inside cap", config=config, measured=str(request.open_position_count), blocking=False, severity="info"))

    if request.reconciliation_critical or request.reconciliation_status.lower() in {"unknown", "mismatch", "critical"}:
        put(_out("reconciliation_status", status=CheckStatus.BLOCK, reason="reconciliation unresolved", config=config, measured=request.reconciliation_status, severity="critical"))
    else:
        put(_out("reconciliation_status", status=CheckStatus.PASS, reason="reconciliation not blocking", config=config, measured=request.reconciliation_status, blocking=False, severity="info"))

    if not persistence_ok:
        put(_out("persistence_availability", status=CheckStatus.BLOCK, reason="persistence unavailable", config=config, severity="critical"))
    else:
        put(_out("persistence_availability", status=CheckStatus.PASS, reason="persistence available", config=config, blocking=False, severity="info"))

    if request.control_state not in {"active", "armed", "normal"}:
        put(_out("system_control_state", status=CheckStatus.BLOCK, reason="control state does not permit evaluation", config=config, measured=request.control_state, severity="critical"))
    else:
        put(_out("system_control_state", status=CheckStatus.PASS, reason="control state active", config=config, measured=request.control_state, blocking=False, severity="info"))

    if halt or request.safe_halt:
        put(_out("global_safe_halt", status=CheckStatus.BLOCK, reason="safe-halt latched", config=config, severity="critical"))
    else:
        put(_out("global_safe_halt", status=CheckStatus.PASS, reason="safe-halt clear", config=config, blocking=False, severity="info"))

    ordered = [results[name] for name in CHECK_CATALOG if name in results]
    missing = [name for name in CHECK_CATALOG if name not in results]
    for name in missing:
        ordered.append(_out(name, status=CheckStatus.BLOCK, reason="check not executed", config=config, severity="critical"))
    return ordered

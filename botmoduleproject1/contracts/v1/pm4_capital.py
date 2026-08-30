"""Capital-management contracts for the PM4 risk gate.

Historical master-orchestration title: “PM5 Risk & Capital Management Gate”
(Sequence 07). Canonical home is Sequence 06 / ``pm4_risk_gate``.

A risk-approved executable intent is not a broker order. ``execution_allowed``
is always false in this stage.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc
from botmoduleproject1.modules.pm8_persistence.money import MoneyError, decimal_from


def _dec(value: Any, *, field: str) -> Decimal:
    return decimal_from(value, field=field)


class CapitalDecisionState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    APPROVED_REDUCED_SIZE = "APPROVED_REDUCED_SIZE"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    EXPIRED = "EXPIRED"
    BLOCKED_SYSTEM = "BLOCKED_SYSTEM"
    BLOCKED_DATA = "BLOCKED_DATA"
    BLOCKED_MODEL = "BLOCKED_MODEL"
    BLOCKED_ACCOUNT = "BLOCKED_ACCOUNT"
    BLOCKED_DRAWDOWN = "BLOCKED_DRAWDOWN"
    BLOCKED_PORTFOLIO_HEAT = "BLOCKED_PORTFOLIO_HEAT"
    BLOCKED_EXPOSURE = "BLOCKED_EXPOSURE"
    BLOCKED_CONCENTRATION = "BLOCKED_CONCENTRATION"
    BLOCKED_SPREAD = "BLOCKED_SPREAD"
    BLOCKED_SLIPPAGE = "BLOCKED_SLIPPAGE"
    BLOCKED_RECONCILIATION = "BLOCKED_RECONCILIATION"
    BLOCKED_POLICY = "BLOCKED_POLICY"
    ERROR_FAIL_CLOSED = "ERROR_FAIL_CLOSED"
    REPLAY_DIVERGENCE = "REPLAY_DIVERGENCE"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCK = "block"
    SKIP = "skip"


class CheckOutcome(ContractModel):
    name: str
    status: CheckStatus
    measured: str | None = None
    limit: str | None = None
    severity: str = "medium"
    reason: str
    policy_version: str
    evidence: tuple[str, ...] = ()
    blocking: bool = True


class QuantileBand(ContractModel):
    q05: Decimal
    q25: Decimal
    q50: Decimal
    q75: Decimal
    q95: Decimal

    @field_validator("q05", "q25", "q50", "q75", "q95", mode="before")
    @classmethod
    def _q(cls, value: Any) -> Decimal:
        return _dec(value, field="quantile")

    @model_validator(mode="after")
    def _ordered(self) -> QuantileBand:
        seq = (self.q05, self.q25, self.q50, self.q75, self.q95)
        if any(later < earlier for earlier, later in zip(seq, seq[1:])):
            raise ValueError("quantiles must be non-decreasing")
        return self


class RiskEvaluationRequest(ContractModel):
    """Typed intake for the capital gate. Not an order."""

    request_id: str
    idempotency_key: str
    correlation_id: str
    causation_id: str
    trade_intent_id: str
    strategy_id: str
    strategy_version: str
    profile_id: str
    profile_version: str
    symbol: str
    timeframe: str = "H1"
    side: str
    requested_quantity: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal | None = None
    signal_timestamp: datetime
    intent_created_at: datetime
    market_snapshot_id: str
    regime_snapshot_id: str
    model_snapshot_id: str | None = None
    model_version: str | None = None
    model_quality_status: str = "unknown"
    predicted_quantiles: QuantileBand | None = None
    expected_return: Decimal | None = None
    expected_adverse_excursion: Decimal | None = None
    spread: Decimal
    estimated_slippage: Decimal
    estimated_commission: Decimal
    estimated_swap: Decimal = Decimal("0")
    account_snapshot_id: str
    portfolio_snapshot_id: str
    current_positions_snapshot_id: str
    current_orders_snapshot_id: str
    risk_policy_version: str
    execution_policy_version: str
    account_equity: Decimal
    peak_equity: Decimal
    free_margin: Decimal
    realized_pnl_day: Decimal = Decimal("0")
    open_position_risk: Decimal = Decimal("0")
    pending_order_risk: Decimal = Decimal("0")
    open_position_count: int = 0
    pending_order_count: int = 0
    symbol_exposure: Decimal = Decimal("0")
    currency_exposure: Decimal = Decimal("0")
    directional_exposure: Decimal = Decimal("0")
    strategy_exposure: Decimal = Decimal("0")
    profile_exposure: Decimal = Decimal("0")
    correlated_exposure: Decimal = Decimal("0")
    conversion_rate: Decimal | None = Decimal("1")
    pip_value: Decimal | None = None
    contract_size: Decimal | None = None
    volume_step: Decimal | None = None
    losing_streak: int = 0
    session: str = "london"
    regime: str = "trending"
    market_age_seconds: int = 0
    account_age_seconds: int = 0
    portfolio_age_seconds: int = 0
    model_age_seconds: int = 0
    account_unknown: bool = False
    exposure_unknown: bool = False
    open_orders_unknown: bool = False
    reconciliation_status: str = "ok"
    reconciliation_critical: bool = False
    safe_halt: bool = False
    control_state: str = "active"
    cooldown_until: datetime | None = None
    existing_symbol_side: str | None = None
    persistence_available: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "requested_quantity",
        "entry_price",
        "stop_loss_price",
        "spread",
        "estimated_slippage",
        "estimated_commission",
        "estimated_swap",
        "account_equity",
        "peak_equity",
        "free_margin",
        "realized_pnl_day",
        "open_position_risk",
        "pending_order_risk",
        "symbol_exposure",
        "currency_exposure",
        "directional_exposure",
        "strategy_exposure",
        "profile_exposure",
        "correlated_exposure",
        mode="before",
    )
    @classmethod
    def _money(cls, value: Any) -> Decimal:
        return _dec(value, field="money")

    @field_validator("take_profit_price", "expected_return", "expected_adverse_excursion", "conversion_rate", "pip_value", "contract_size", "volume_step", mode="before")
    @classmethod
    def _opt_money(cls, value: Any) -> Decimal | None:
        if value is None:
            return None
        return _dec(value, field="money")

    @field_validator("signal_timestamp", "intent_created_at", "cooldown_until")
    @classmethod
    def _ts(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value, "timestamp")

    @field_validator("side")
    @classmethod
    def _side(cls, value: str) -> str:
        lowered = str(value).strip().lower()
        if lowered not in {"buy", "sell"}:
            raise ValueError("side must be buy|sell")
        return lowered

    @field_validator("symbol")
    @classmethod
    def _symbol(cls, value: str) -> str:
        text = str(value).strip().upper()
        if not text:
            raise ValueError("symbol is required")
        return text


class SizingTrace(ContractModel):
    theoretical_size: Decimal
    constrained_size: Decimal
    rounded_size: Decimal
    final_risk: Decimal
    stop_distance: Decimal
    effective_stop: Decimal
    limiting_constraints: tuple[str, ...]
    calculation_version: str = "v1"
    input_hash: str
    output_hash: str
    include_costs: bool = True


class RiskDecision(ContractModel):
    decision_id: str
    decision_status: CapitalDecisionState
    decision_timestamp: datetime
    expires_at: datetime
    correlation_id: str
    causation_id: str
    trade_intent_id: str
    strategy_id: str
    strategy_version: str
    profile_id: str
    profile_version: str
    symbol: str
    side: str
    requested_quantity: Decimal
    approved_quantity: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal | None = None
    stop_distance: Decimal
    monetary_risk: Decimal
    risk_percent_of_equity: Decimal
    portfolio_heat_before: Decimal
    portfolio_heat_after: Decimal
    currency_exposure_before: Decimal
    currency_exposure_after: Decimal
    concentration_before: Decimal
    concentration_after: Decimal
    spread: Decimal
    slippage_estimate: Decimal
    expected_cost: Decimal
    model_quality_status: str
    regime_status: str
    session_status: str
    account_status: str
    final_decision: CapitalDecisionState
    decision_reasons: tuple[str, ...] = ()
    failed_checks: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    policy_version: str
    policy_id: str
    configuration_hash: str
    input_hash: str
    output_hash: str
    audit_reference: str
    persistence_reference: str | None = None
    checks: tuple[CheckOutcome, ...] = ()
    sizing: SizingTrace | None = None
    execution_permitted: bool = False
    trading_readiness: bool = False

    @field_validator("decision_timestamp", "expires_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "ts")

    @model_validator(mode="after")
    def _no_exec(self) -> RiskDecision:
        if self.execution_permitted or self.trading_readiness:
            raise ValueError("capital decision cannot set execution_permitted or trading_readiness")
        if self.final_decision is CapitalDecisionState.ERROR_FAIL_CLOSED and self.approved_quantity != Decimal("0"):
            raise ValueError("fail-closed decisions must size to zero")
        return self


class RiskApprovedExecutableIntent(ContractModel):
    executable_intent_id: str
    risk_decision_id: str
    trade_intent_id: str
    symbol: str
    side: str
    approved_quantity: Decimal
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal | None = None
    maximum_slippage: Decimal
    maximum_latency_ms: int = 500
    expires_at: datetime
    strategy_id: str
    profile_id: str
    correlation_id: str
    risk_policy_version: str
    execution_policy_version: str
    execution_allowed: bool = False
    audit_reference: str
    persistence_reference: str
    creates_order: bool = False

    @model_validator(mode="after")
    def _never_order(self) -> RiskApprovedExecutableIntent:
        if self.execution_allowed or self.creates_order:
            raise ValueError("executable intent cannot authorize execution in this stage")
        return self


class RiskRejection(ContractModel):
    rejection_id: str
    trade_intent_id: str
    rejection_code: str
    rejection_category: str
    severity: str
    explanation: str
    failed_measurements: tuple[str, ...] = ()
    applicable_limits: tuple[str, ...] = ()
    policy_version: str
    timestamp: datetime
    correlation_id: str
    persistence_reference: str | None = None


class CapitalEvaluationResult(ContractModel):
    decision: RiskDecision
    executable_intent: RiskApprovedExecutableIntent | None = None
    rejection: RiskRejection | None = None
    replay_match: bool | None = None

    @model_validator(mode="after")
    def _shape(self) -> CapitalEvaluationResult:
        approved = self.decision.final_decision in {
            CapitalDecisionState.APPROVED,
            CapitalDecisionState.APPROVED_REDUCED_SIZE,
        }
        if approved and self.executable_intent is None:
            raise ValueError("approved decisions must emit an executable intent")
        if approved and self.executable_intent is not None and self.executable_intent.execution_allowed:
            raise ValueError("execution_allowed must stay false")
        if not approved and self.executable_intent is not None:
            raise ValueError("non-approved decisions cannot emit executable intents")
        return self

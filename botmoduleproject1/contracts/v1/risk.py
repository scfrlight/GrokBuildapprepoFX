"""PM4 risk-gate contracts. Exclusive execution permission (ADR-007 / ADR-011).

PM4 output is a risk-governed handoff artifact. It is not a broker order.
ALLOW still does not execute: PM5 remains closed in Sequence 06.
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


class RiskVerdictStatus(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    HALT = "halt"


class RiskRejectionReason(str, Enum):
    ENGINE_UNAVAILABLE = "engine_unavailable"
    NOT_READY = "not_ready"
    LIVE_DISABLED = "live_disabled"
    EXPOSURE_LIMIT = "exposure_limit"
    DRAWDOWN_LIMIT = "drawdown_limit"
    STALE_DATA = "stale_data"
    LEDGER_INCONSISTENT = "ledger_inconsistent"
    KILL_SWITCH = "kill_switch"
    INVALID_INTENT = "invalid_intent"
    POLICY = "policy"
    UNKNOWN_STATE = "unknown_state"
    MISSING_FORECAST = "missing_forecast"
    MISSING_CANDIDATE = "missing_candidate"
    FORECAST_INVALID = "forecast_invalid"
    HANDOFF_INELIGIBLE = "handoff_ineligible"
    CONCENTRATION_LIMIT = "concentration_limit"
    HEAT_LIMIT = "heat_limit"
    DUPLICATE_INTENT = "duplicate_intent"
    SESSION_RESTRICTED = "session_restricted"
    LIQUIDITY = "liquidity"
    SIZE_ZERO = "size_zero"
    FAT_FINGER = "fat_finger"
    PRICE_COLLAR = "price_collar"
    BURST_THROTTLE = "burst_throttle"
    DEGRADED_MODE = "degraded_mode"
    RECOVERY_GATE = "recovery_gate"
    LOOKAHEAD = "lookahead"
    BUDGET_EXHAUSTED = "budget_exhausted"
    FEATURE_DISABLED = "feature_disabled"
    CLOSE_ONLY = "close_only"
    NO_NEW_RISK = "no_new_risk"
    SYMBOL_MISMATCH = "symbol_mismatch"
    STOP_MISSING = "stop_missing"
    ROUTE_INELIGIBLE = "route_ineligible"
    MALFORMED = "malformed"


class RiskDecisionTier(str, Enum):
    HARD_VETO = "hard_veto"
    POLICY_REJECT = "policy_reject"
    REDUCED = "reduced"
    CONDITIONAL = "conditional"
    ADMITTED = "admitted"


class RiskAdmissionDecision(str, Enum):
    APPROVE = "approve"
    REDUCE = "reduce"
    REJECT = "reject"
    FREEZE = "freeze"
    KILL_PROTECTED = "kill_protected"


class RiskControlState(str, Enum):
    ACTIVE = "active"
    THROTTLED = "throttled"
    BREACHED = "breached"
    LATCHED = "latched"
    DISABLED = "disabled"


class DrawdownStage(str, Enum):
    NORMAL = "normal"
    MILD_THROTTLE = "mild_throttle"
    REDUCED_RISK = "reduced_risk"
    RESTRICTED_RISK = "restricted_risk"
    FREEZE = "freeze"
    KILL_PROTECTED = "kill_protected"
    RECOVERY = "recovery"


class HeatRegime(str, Enum):
    COOL = "cool"
    WARM = "warm"
    HOT = "hot"
    CRITICAL = "critical"
    STRESSED = "stressed"


class ConcentrationState(str, Enum):
    DIVERSIFIED = "diversified"
    ELEVATED = "elevated"
    CROWDED = "crowded"
    STRESSED = "stressed"
    BLOCKED = "blocked"


class KillSwitchScope(str, Enum):
    SYMBOL = "symbol"
    STRATEGY = "strategy"
    CLUSTER = "cluster"
    ACCOUNT = "account"


class KillSwitchStatus(str, Enum):
    DISARMED = "disarmed"
    ARMED = "armed"
    TRIPPED = "tripped"
    LATCHED = "latched"


class RecoveryStage(str, Enum):
    NONE = "none"
    INELIGIBLE = "ineligible"
    COOLDOWN = "cooldown"
    MANUAL_REVIEW = "manual_review"
    STAGED = "staged"
    CLEARED = "cleared"


class ControlBreachType(str, Enum):
    FAT_FINGER = "fat_finger"
    MAX_ORDER_SIZE = "max_order_size"
    MAX_INTRADAY_POSITION = "max_intraday_position"
    MAX_NOTIONAL = "max_notional"
    PRICE_COLLAR = "price_collar"
    SLIPPAGE = "slippage"
    DUPLICATE = "duplicate"
    BURST = "burst"
    STALE_QUOTE = "stale_quote"
    UNREASONABLE_MARKET_DATA = "unreasonable_market_data"
    ROUTE = "route"
    CANCEL_ON_DISCONNECT = "cancel_on_disconnect"


class PreTradeControlType(str, Enum):
    FAT_FINGER = "fat_finger"
    ORDER_SIZE = "order_size"
    INTRADAY_POSITION = "intraday_position"
    NOTIONAL = "notional"
    PRICE_COLLAR = "price_collar"
    SLIPPAGE = "slippage"
    DUPLICATE = "duplicate"
    BURST = "burst"
    MARKET_DATA = "market_data"
    STALE_CONTEXT = "stale_context"
    ROUTE_ELIGIBILITY = "route_eligibility"
    CANCEL_ON_DISCONNECT = "cancel_on_disconnect"


class RiskMode(str, Enum):
    NORMAL = "normal"
    THROTTLE = "throttle"
    PROTECTION = "protection"
    FREEZE = "freeze"
    CLOSE_ONLY = "close_only"
    NO_NEW_RISK = "no_new_risk"
    KILL_PROTECTED = "kill_protected"
    MANUAL_REVIEW = "manual_review"
    RECOVERY = "recovery"


class RiskSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HandoffEligibility(str, Enum):
    INELIGIBLE = "ineligible"
    ELIGIBLE_PENDING_PM5 = "eligible_pending_pm5"
    BLOCKED_KILL = "blocked_kill"
    BLOCKED_CONTROLS = "blocked_controls"
    BLOCKED_DEGRADED = "blocked_degraded"


class RiskEventType(str, Enum):
    ADMISSION = "admission"
    SIZING = "sizing"
    HEAT = "heat"
    CONCENTRATION = "concentration"
    DRAWDOWN = "drawdown"
    PRETRADE = "pretrade"
    KILL_SWITCH = "kill_switch"
    RECOVERY = "recovery"
    INCIDENT = "incident"
    GOVERNANCE = "governance"
    PUBLICATION = "publication"


class ExposureSnapshot(ContractModel):
    as_of: datetime
    gross_notional: Decimal = Decimal("0")
    net_notional: Decimal = Decimal("0")
    open_position_count: int = Field(default=0, ge=0)
    heat_r: Decimal = Decimal("0")
    equity: Decimal = Decimal("100000")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    peak_equity: Decimal = Decimal("100000")
    intraday_pnl: Decimal = Decimal("0")
    losing_streak: int = Field(default=0, ge=0)
    pending_order_count: int = Field(default=0, ge=0)
    symbols: tuple[str, ...] = ()
    clusters: tuple[str, ...] = ()
    directional_net: Decimal = Decimal("0")

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class RiskVerdict(ContractModel):
    """Sole final permission object consumed by PM5."""

    verdict_id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    occurred_at: datetime
    status: RiskVerdictStatus
    reasons: tuple[RiskRejectionReason, ...] = ()
    detail: str | None = None
    expires_at: datetime | None = None
    producer: str = "pm4_risk"
    recommended_volume: Decimal | None = None
    handoff_eligibility: HandoffEligibility = HandoffEligibility.INELIGIBLE

    @field_validator("occurred_at", "expires_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value)

    @property
    def allows_execution(self) -> bool:
        return self.status is RiskVerdictStatus.ALLOW

    @model_validator(mode="after")
    def _allow_is_explicit(self) -> RiskVerdict:
        if self.status is RiskVerdictStatus.ALLOW and not self.reasons:
            return self
        return self


class RiskAdmissionCard(ContractModel):
    decision: RiskAdmissionDecision
    tier: RiskDecisionTier
    reasons: tuple[str, ...] = ()
    active_controls: tuple[str, ...] = ()
    trace_id: UUID = Field(default_factory=uuid4)
    vetoes: tuple[str, ...] = ()
    detail: str = ""


class RiskBudgetCard(ContractModel):
    account_budget: Decimal
    sleeve_budget: Decimal
    regime_budget: Decimal
    cluster_budget: Decimal
    symbol_budget: Decimal
    candidate_budget: Decimal
    residual_headroom: Decimal
    consumed_headroom: Decimal
    proposed_risk: Decimal = Decimal("0")
    throttle_factor: Decimal = Decimal("1")
    tree: dict[str, Any] = Field(default_factory=dict)


class PositionSizingDecision(ContractModel):
    recommended_size: Decimal
    size_unit: str = "lots"
    base_risk_percentage: Decimal
    adjusted_risk_percentage: Decimal
    stop_distance: Decimal
    stop_distance_basis: str
    uncertainty_discount: Decimal
    predictive_quality_factor: Decimal
    drawdown_throttle: Decimal
    liquidity_factor: Decimal
    correlation_penalty: Decimal
    heat_cap_factor: Decimal = Decimal("1")
    hard_cap_applied: bool = False
    final_size_rationale: str
    account_equity: Decimal = Decimal("0")
    risk_amount: Decimal = Decimal("0")


class PortfolioHeatCard(ContractModel):
    raw_heat: Decimal
    effective_heat: Decimal
    cluster_heat: Decimal
    directional_heat: Decimal
    session_heat: Decimal
    residual_heat_headroom: Decimal
    heat_regime: HeatRegime
    stressed_heat: Decimal = Decimal("0")
    proposed_incremental_heat: Decimal = Decimal("0")


class ConcentrationExposureCard(ContractModel):
    symbol_overlap: tuple[str, ...] = ()
    currency_overlap: tuple[str, ...] = ()
    cluster_exposure: dict[str, Decimal] = Field(default_factory=dict)
    crowding_penalty: Decimal = Decimal("0")
    stressed_concentration_state: ConcentrationState = ConcentrationState.DIVERSIFIED
    usd_concentration: Decimal = Decimal("0")
    european_basket: Decimal = Decimal("0")
    one_per_cluster_blocked: bool = False
    cluster_id: str | None = None


class DrawdownStateCard(ContractModel):
    current_drawdown: Decimal
    peak_to_trough_drawdown: Decimal
    intraday_loss: Decimal
    losing_streak: int = Field(ge=0)
    throttle_stage: DrawdownStage
    protection_stage: DrawdownStage
    freeze_state: bool = False
    throttle_factor: Decimal = Decimal("1")


class PreTradeControlDecision(ContractModel):
    passed: bool
    breach_reasons: tuple[ControlBreachType, ...] = ()
    order_size_legal: bool = True
    price_legal: bool = True
    message_legal: bool = True
    route_eligible: bool = False
    checks: dict[str, bool] = Field(default_factory=dict)
    detail: str = ""


class KillSwitchState(ContractModel):
    status: KillSwitchStatus = KillSwitchStatus.DISARMED
    scope: KillSwitchScope = KillSwitchScope.ACCOUNT
    scope_id: str | None = None
    trigger_reason: str | None = None
    cancel_orders_status: str = "placeholder_pending_pm5"
    new_order_block_status: bool = False
    risk_reducing_order_policy: bool = False
    recovery_eligibility: RecoveryStage = RecoveryStage.NONE
    tripped_at: datetime | None = None
    actor: str | None = None

    @field_validator("tripped_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_aware_utc(value, "tripped_at")


class RiskPublicationBundle(ContractModel):
    """Immutable risk-governed handoff. Not an order. Not executable in Sequence 06."""

    bundle_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str | None = None
    occurred_at: datetime
    intent_id: UUID
    candidate_id: UUID | None = None
    forecast_id: UUID | None = None
    symbol: str
    verdict: RiskVerdict
    admission: RiskAdmissionCard
    budget: RiskBudgetCard
    sizing: PositionSizingDecision
    heat: PortfolioHeatCard
    concentration: ConcentrationExposureCard
    drawdown: DrawdownStateCard
    pretrade: PreTradeControlDecision
    kill_switch: KillSwitchState
    diagnostics_summary: dict[str, Any] = Field(default_factory=dict)
    audit_summary: dict[str, Any] = Field(default_factory=dict)
    handoff_eligibility: HandoffEligibility = HandoffEligibility.INELIGIBLE
    execution_permitted: bool = False
    producer: str = "pm4_risk_gate"
    risk_mode: RiskMode = RiskMode.NORMAL

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @model_validator(mode="after")
    def _never_an_order(self) -> RiskPublicationBundle:
        if self.execution_permitted:
            raise ValueError(
                "RiskPublicationBundle.execution_permitted must stay false; "
                "PM4 does not authorize broker execution in Sequence 06"
            )
        return self

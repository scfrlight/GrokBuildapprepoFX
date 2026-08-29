"""Operator control-plane contracts (Sequence 10 / PM8)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.roles import OperatorRole, PermissionScope
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class OperatorVerb(str, Enum):
    HELP = "help"
    STATUS = "status"
    HEALTH = "health"
    DOCTOR = "doctor"
    PENDING = "pending"
    LIST_ALERTS = "list_alerts"
    QUERY_JOURNAL = "query_journal"
    ACK = "ack"
    HALT = "halt"
    APPROVE = "approve"
    REJECT = "reject"
    PROPOSE_TUNING = "propose_tuning"
    PLACE_ORDER = "place_order"
    BUY = "buy"
    SELL = "sell"
    RESUME = "resume"
    REARM = "rearm"
    ENABLE_LIVE = "enable_live"
    CONNECT_MT5 = "connect_mt5"


class CommandDisposition(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNAUTHORIZED = "unauthorized"
    REFUSED = "refused"
    DUPLICATE = "duplicate"
    EXPIRED = "expired"
    PENDING_HITL = "pending_hitl"
    PENDING_DUAL_CONTROL = "pending_dual_control"


class TransportMode(str, Enum):
    DISABLED = "disabled"
    SIMULATED = "simulated"
    TELEGRAM_API = "telegram_api"


class HaltState(str, Enum):
    RUNNING = "running"
    HALT_REQUESTED = "halt_requested"
    HALTED = "halted"


REFUSED_VERBS: frozenset[OperatorVerb] = frozenset(
    {
        OperatorVerb.PLACE_ORDER,
        OperatorVerb.BUY,
        OperatorVerb.SELL,
        OperatorVerb.RESUME,
        OperatorVerb.REARM,
        OperatorVerb.ENABLE_LIVE,
        OperatorVerb.CONNECT_MT5,
    }
)

READ_VERBS: frozenset[OperatorVerb] = frozenset(
    {
        OperatorVerb.HELP,
        OperatorVerb.STATUS,
        OperatorVerb.HEALTH,
        OperatorVerb.DOCTOR,
        OperatorVerb.PENDING,
        OperatorVerb.LIST_ALERTS,
        OperatorVerb.QUERY_JOURNAL,
    }
)


class OperatorIdentity(ContractModel):
    actor_id: str
    display_name: str
    role: OperatorRole
    transport: TransportMode = TransportMode.SIMULATED
    telegram_user_id: str | None = None

    @field_validator("actor_id", "display_name")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped


class OperatorCommand(ContractModel):
    """Inbound operator command. Never an order."""

    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str
    occurred_at: datetime
    verb: OperatorVerb
    actor: OperatorIdentity
    text: str = ""
    target_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    channel: Literal["console", "simulated", "telegram"] = "simulated"

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

    @field_validator("idempotency_key")
    @classmethod
    def _key(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("idempotency_key is required")
        return stripped

    @model_validator(mode="after")
    def _no_secret_payload(self) -> "OperatorCommand":
        forbidden = ("token", "password", "secret", "api_key", "authorization")
        for key in self.payload:
            if any(part in key.lower() for part in forbidden):
                raise ValueError("secret-shaped keys are forbidden on OperatorCommand")
        return self


class CommandReceipt(ContractModel):
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    causation_id: UUID | None = None
    idempotency_key: str
    occurred_at: datetime
    verb: OperatorVerb
    disposition: CommandDisposition
    actor_id: str
    role: OperatorRole
    message: str
    reason_code: str
    creates_order: Literal[False] = False
    skips_pm4: Literal[False] = False
    broker_side_effect: Literal[False] = False
    mt5_used: Literal[False] = False
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class OperatorAlert(ContractModel):
    alert_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime
    code: str
    message: str
    severity: str = "info"
    acked: bool = False
    acked_by: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class OperatorPublicationBundle(ContractModel):
    as_of: datetime
    producer: str = "pm8_operator"
    transport_mode: TransportMode
    halt_state: HaltState
    hitl_pending: int = 0
    studio_open: int = 0
    last_disposition: CommandDisposition | None = None
    execution_permitted: Literal[False] = False
    telegram_api_bound: Literal[False] = False
    live_trading: Literal[False] = False
    diagnostics: dict[str, Any] = Field(default_factory=dict)

    @field_validator("as_of")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "as_of")


class TelegramInbound(ContractModel):
    """Decoded Telegram update. Adapter-only shape; no business fields."""

    update_id: int
    user_id: str
    username: str | None = None
    chat_id: str
    text: str
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")


class TelegramOutbound(ContractModel):
    chat_id: str
    text: str
    parse_mode: Literal["plain"] = "plain"


__all__ = [
    "CommandDisposition",
    "CommandReceipt",
    "HaltState",
    "OperatorAlert",
    "OperatorCommand",
    "OperatorIdentity",
    "OperatorPublicationBundle",
    "OperatorVerb",
    "READ_VERBS",
    "REFUSED_VERBS",
    "TelegramInbound",
    "TelegramOutbound",
    "TransportMode",
    "OperatorRole",
    "PermissionScope",
]

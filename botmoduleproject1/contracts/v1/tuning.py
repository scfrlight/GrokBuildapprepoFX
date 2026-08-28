"""Tuning-change contracts (PM9a). Research proposals, never auto-live."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from botmoduleproject1.contracts.v1.identity import ContractModel
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


class TuningChangeStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    VALIDATING = "validating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ParameterSchema(ContractModel):
    name: str
    display_name: str
    group: str
    type: Literal["int", "float", "bool", "string", "enum"]
    default: Any = None
    min: float | None = None
    max: float | None = None
    step: float | None = None
    allowed_values: tuple[Any, ...] | None = None
    ui_mode: Literal["input", "slider", "select", "toggle"] = "input"
    description: str = ""
    warning_text: str | None = None
    requires_revalidation: bool = True


class TuningChangeRequest(ContractModel):
    request_id: UUID = Field(default_factory=uuid4)
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    idempotency_key: str
    occurred_at: datetime
    parameter: ParameterSchema
    new_value: Any
    status: TuningChangeStatus = TuningChangeStatus.DRAFT
    requested_by: str
    auto_promote_to_live: Literal[False] = False

    @field_validator("occurred_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_aware_utc(value, "occurred_at")

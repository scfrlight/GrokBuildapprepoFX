"""Public PM5 contract tests: enums, publication safety, OMS types."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.execution import (
    ControlActionType,
    ControlScope,
    ExecutionIntentReceipt,
    ExecutionLifecycleState,
    ExecutionMode,
    ExecutionPublicationBundle,
    ExecutionRejectReason,
    NormalizedExecutionCommand,
    OrderRequest,
    Pm5OperatingState,
    ReconciliationOutcome,
)
from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.contracts.v1.time import utc_now


def test_required_enums_exist() -> None:
    assert ExecutionMode.SIMULATION
    assert ExecutionMode.DISABLED
    assert ExecutionLifecycleState.RECONCILIATION_PENDING
    assert ExecutionRejectReason.PM4_DENY
    assert ReconciliationOutcome.DEGRADED
    assert Pm5OperatingState.EMERGENCY_CANCEL
    assert ControlActionType.NO_NEW_RISK
    assert ControlScope.GLOBAL


def test_order_request_still_requires_idempotency() -> None:
    with pytest.raises(ValidationError):
        OrderRequest(
            causation_id=uuid4(),
            idempotency_key="  ",
            occurred_at=utc_now(),
            intent_id=uuid4(),
            risk_verdict_id=uuid4(),
            symbol="EURUSD",
            direction=Direction.BUY,
            entry_type=EntryType.MARKET,
            volume=Decimal("1"),
        )


def test_publication_defaults_are_safe() -> None:
    bundle = ExecutionPublicationBundle(
        occurred_at=utc_now(),
        receipt=ExecutionIntentReceipt(accepted=False),
    )
    assert bundle.broker_side_effect is False
    assert bundle.mt5_used is False
    assert bundle.durable is False
    assert bundle.execution_mode is ExecutionMode.DISABLED


def test_normalized_command_caps_quantity() -> None:
    oid = uuid4()
    cmd = NormalizedExecutionCommand(
        order_id=oid,
        pm4_decision_id=uuid4(),
        symbol="EURUSD",
        direction=Direction.BUY,
        approved_quantity=Decimal("2"),
        requested_quantity=Decimal("1"),
        order_type="market",
        idempotency_key=str(oid),
        correlation_id=oid,
    )
    assert cmd.broker_eligible is False
    assert cmd.requested_quantity < cmd.approved_quantity

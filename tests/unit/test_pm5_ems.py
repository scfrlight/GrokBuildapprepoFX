"""EMS adapters: disabled, simulation, MT5 placeholder. No real broker."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.contracts.v1.execution import (
    BrokerEventType,
    NormalizedExecutionCommand,
)
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm5_execution.ems.disabled_adapter import DisabledBrokerAdapter
from botmoduleproject1.modules.pm5_execution.ems.mt5_adapter import Mt5BrokerAdapter
from botmoduleproject1.modules.pm5_execution.ems.simulation_adapter import SimulationBrokerAdapter

NOW = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


def _cmd() -> NormalizedExecutionCommand:
    oid = uuid4()
    return NormalizedExecutionCommand(
        order_id=oid,
        pm4_decision_id=uuid4(),
        symbol="EURUSD",
        direction=Direction.BUY,
        approved_quantity=Decimal("1"),
        requested_quantity=Decimal("1"),
        order_type="market",
        idempotency_key=str(oid),
        correlation_id=oid,
        broker_eligible=False,
    )


def test_disabled_adapter_no_side_effects() -> None:
    adapter = DisabledBrokerAdapter()
    events = adapter.submit(_cmd(), now=NOW)
    assert adapter.available() is False
    assert events[0].kind is BrokerEventType.DISABLED
    assert events[0].ticket is None
    assert adapter.fetch_open_orders() == ()
    assert adapter.health()["mt5"] is False


def test_simulation_adapter_deterministic_ticket() -> None:
    cmd = _cmd()
    adapter = SimulationBrokerAdapter()
    first = adapter.submit(cmd, now=NOW)
    second = adapter.submit(cmd, now=NOW)
    assert first[0].ticket.startswith("SIM-")
    assert first[0].ticket == second[0].ticket
    assert first[0].kind is BrokerEventType.SIMULATED_ACK
    assert first[1].source == "simulation"
    assert adapter.health()["truth"] == "simulated"


def test_mt5_adapter_unavailable() -> None:
    adapter = Mt5BrokerAdapter()
    assert adapter.available() is False
    with pytest.raises(ExecutionDisabledError, match="MT5"):
        adapter.submit(_cmd(), now=NOW)
    with pytest.raises(ExecutionDisabledError):
        adapter.fetch_positions()
    health = adapter.health()
    assert health["status"] == "placeholder_blocked"
    assert health["methods"]["submit"] == "blocked"


def test_no_metatrader5_import() -> None:
    import sys

    assert "MetaTrader5" not in sys.modules
    from botmoduleproject1.modules.pm5_execution import ems as ems_pkg

    assert "MetaTrader5" not in sys.modules
    assert ems_pkg.Mt5BrokerAdapter().available() is False


def test_command_cannot_exceed_pm4_qty() -> None:
    from pydantic import ValidationError

    oid = uuid4()
    with pytest.raises(ValidationError):
        NormalizedExecutionCommand(
            order_id=oid,
            pm4_decision_id=uuid4(),
            symbol="EURUSD",
            direction=Direction.BUY,
            approved_quantity=Decimal("1"),
            requested_quantity=Decimal("2"),
            order_type="market",
            idempotency_key=str(oid),
            correlation_id=oid,
        )


def test_retries_are_capped() -> None:
    from pydantic import ValidationError

    from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig

    with pytest.raises(ValidationError):
        Pm5ExecutionConfig(max_retries=9)
    with pytest.raises(ValidationError):
        Pm5ExecutionConfig(broker_adapter_enabled=True)
    with pytest.raises(ValidationError):
        Pm5ExecutionConfig(mt5_enabled=True)
    with pytest.raises(ValidationError):
        Pm5ExecutionConfig(auto_rearm=True)
    with pytest.raises(ValidationError):
        Pm5ExecutionConfig(operating_mode="live")

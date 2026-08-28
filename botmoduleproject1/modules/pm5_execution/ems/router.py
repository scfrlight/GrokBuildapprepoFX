from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import ExecutionMode
from botmoduleproject1.modules.pm5_execution.ems.disabled_adapter import DisabledBrokerAdapter
from botmoduleproject1.modules.pm5_execution.ems.mt5_adapter import Mt5BrokerAdapter
from botmoduleproject1.modules.pm5_execution.ems.simulation_adapter import SimulationBrokerAdapter


def select_adapter(mode: ExecutionMode):
    if mode is ExecutionMode.SIMULATION:
        return SimulationBrokerAdapter()
    return DisabledBrokerAdapter()


def mt5_placeholder() -> Mt5BrokerAdapter:
    return Mt5BrokerAdapter()

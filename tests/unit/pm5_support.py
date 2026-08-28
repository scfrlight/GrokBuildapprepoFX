"""Shared fixtures for PM5 Execution tests. Not a package."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.strategy import Direction, EntryType
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig
from botmoduleproject1.modules.pm5_execution.module import PM5ExecutionModule
from tests.unit.pm4_support import AS_OF, admitted_bundle


class Clock:
    def __init__(self, instant: datetime = AS_OF) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant

    def set(self, instant: datetime) -> None:
        self._instant = instant


def pm5_module(
    *,
    simulation_enabled: bool = True,
    config: Pm5ExecutionConfig | None = None,
    clock: Clock | None = None,
) -> PM5ExecutionModule:
    cfg = config or Pm5ExecutionConfig(operating_mode="simulation")
    return PM5ExecutionModule(
        cfg,
        clock or Clock(),
        simulation_enabled=simulation_enabled,
        execution_flag=False,
    )


def ingest_allow(module: PM5ExecutionModule | None = None, key: str = "pm5-ok", **kwargs):
    gate = module or pm5_module()
    bundle = admitted_bundle(key=key)
    pub = gate.ingest(
        bundle,
        direction=kwargs.get("direction", Direction.BUY),
        entry_type=kwargs.get("entry_type", EntryType.MARKET),
        quantity=kwargs.get("quantity"),
        order_type=kwargs.get("order_type", "market"),
        entry_price=kwargs.get("entry_price", Decimal("1.10000")),
        stop_price=kwargs.get("stop_price", Decimal("1.09500")),
    )
    return gate, bundle, pub

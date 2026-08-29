"""Shared fixtures for PM8 operator tests."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.operator import OperatorIdentity, TransportMode
from botmoduleproject1.contracts.v1.roles import OperatorRole
from botmoduleproject1.modules.pm8_operator.config.schema import Pm8OperatorConfig
from botmoduleproject1.modules.pm8_operator.module import PM8OperatorModule
from tests.unit.pm5_support import Clock
from tests.unit.pm4_support import AS_OF


def actor(role: OperatorRole = OperatorRole.ADMIN, actor_id: str = "op-1") -> OperatorIdentity:
    return OperatorIdentity(
        actor_id=actor_id,
        display_name=actor_id,
        role=role,
        transport=TransportMode.SIMULATED,
    )


def pm8_module(*, clock: Clock | None = None, config: Pm8OperatorConfig | None = None, **kwargs) -> PM8OperatorModule:
    cfg = config or Pm8OperatorConfig(studio_enabled=kwargs.get("studio_enabled", True), hitl_enabled=kwargs.get("hitl_enabled", True))
    return PM8OperatorModule(
        cfg,
        clock or Clock(),
        feature_enabled=kwargs.get("feature_enabled", True),
        ledger=kwargs.get("ledger"),
    )

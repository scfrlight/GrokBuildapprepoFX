from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.risk import (
    KillSwitchScope,
    KillSwitchState,
    KillSwitchStatus,
    RecoveryStage,
)
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.kill.kill_scope import matches
from botmoduleproject1.modules.pm4_risk_gate.kill.recovery import may_recover


class KillSwitchEngine:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config
        self._state = KillSwitchState(
            status=KillSwitchStatus.ARMED,
            scope=KillSwitchScope.ACCOUNT,
            risk_reducing_order_policy=config.risk_reducing_only_on_kill,
            recovery_eligibility=RecoveryStage.NONE,
        )

    @property
    def state(self) -> KillSwitchState:
        return self._state

    def trip(
        self,
        *,
        reason: str,
        now: datetime,
        scope: KillSwitchScope = KillSwitchScope.ACCOUNT,
        scope_id: str | None = None,
        actor: str = "automatic",
    ) -> KillSwitchState:
        self._state = KillSwitchState(
            status=KillSwitchStatus.LATCHED,
            scope=scope,
            scope_id=scope_id,
            trigger_reason=reason,
            cancel_orders_status="placeholder_pending_pm5",
            new_order_block_status=True,
            risk_reducing_order_policy=self.config.risk_reducing_only_on_kill,
            recovery_eligibility=RecoveryStage.INELIGIBLE,
            tripped_at=now,
            actor=actor,
        )
        return self._state

    def blocks(self, symbol: str, sleeve: str | None, cluster: str | None) -> bool:
        if self._state.status not in {KillSwitchStatus.TRIPPED, KillSwitchStatus.LATCHED}:
            return False
        return matches(self._state.scope, self._state.scope_id, symbol, sleeve, cluster)

    def recover(self, *, reason: str, actor: str, now: datetime) -> KillSwitchState:
        ok, stage = may_recover(
            status=self._state.status,
            config=self.config,
            reason=reason,
            actor=actor,
            tripped_at=self._state.tripped_at,
            now=now,
        )
        if not ok:
            self._state = self._state.model_copy(update={"recovery_eligibility": stage})
            return self._state
        self._state = KillSwitchState(
            status=KillSwitchStatus.ARMED,
            scope=KillSwitchScope.ACCOUNT,
            trigger_reason=None,
            cancel_orders_status="placeholder_pending_pm5",
            new_order_block_status=False,
            risk_reducing_order_policy=self.config.risk_reducing_only_on_kill,
            recovery_eligibility=RecoveryStage.CLEARED,
            actor=actor,
        )
        return self._state

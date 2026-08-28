from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.execution import (
    ControlActionRecord,
    ControlActionType,
    ControlScope,
    ExecutionRejectReason,
    Pm5OperatingState,
)
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class ControlPlane:
    def __init__(self, config: Pm5ExecutionConfig) -> None:
        self.config = config
        self.actions: list[ControlActionRecord] = []
        self.block_new = False
        self.close_only = False
        self.frozen_scopes: set[tuple[str, str | None]] = set()
        self.kill_latched = False
        self.kill_reason: str | None = None
        self.tripped_at: datetime | None = None
        self.operating = Pm5OperatingState.NORMAL

    def _record(self, now, action, scope, reason, actor, trigger, scope_id=None, affected=()) -> ControlActionRecord:
        rec = ControlActionRecord(
            action_id=new_id(),
            occurred_at=now,
            action=action,
            scope=scope,
            scope_id=scope_id,
            actor=actor,
            reason=reason,
            trigger_source=trigger,
            affected_order_ids=tuple(affected),
        )
        self.actions.append(rec)
        return rec

    def blocks(self, symbol: str, strategy: str | None = None, cluster: str | None = None) -> bool:
        if self.kill_latched or self.block_new:
            return True
        if self.close_only:
            return True
        checks = {
            (ControlScope.GLOBAL.value, None),
            (ControlScope.SYMBOL.value, symbol),
            (ControlScope.STRATEGY.value, strategy),
            (ControlScope.CLUSTER.value, cluster),
            (ControlScope.ACCOUNT.value, "account"),
        }
        return bool(self.frozen_scopes & checks)

    def freeze(self, *, now, scope: ControlScope, reason: str, actor="operator", scope_id=None):
        self.frozen_scopes.add((scope.value, scope_id))
        self.block_new = True
        self.operating = Pm5OperatingState.FREEZE_NEW_ORDERS
        return self._record(now, ControlActionType.FREEZE, scope, reason, actor, "control_plane", scope_id)

    def enter_close_only(self, *, now, reason: str, actor="operator"):
        self.close_only = True
        self.block_new = True
        self.operating = Pm5OperatingState.CLOSE_ONLY
        return self._record(now, ControlActionType.CLOSE_ONLY, ControlScope.GLOBAL, reason, actor, "control_plane")

    def no_new_risk(self, *, now, reason: str, actor="operator"):
        self.block_new = True
        self.operating = Pm5OperatingState.FREEZE_NEW_ORDERS
        return self._record(now, ControlActionType.NO_NEW_RISK, ControlScope.GLOBAL, reason, actor, "control_plane")

    def emergency_cancel(self, *, now, reason: str, actor="operator", affected=()):
        self.kill_latched = True
        self.block_new = True
        self.tripped_at = now
        self.kill_reason = reason
        self.operating = Pm5OperatingState.EMERGENCY_CANCEL
        return self._record(
            now, ControlActionType.EMERGENCY_CANCEL, ControlScope.GLOBAL, reason, actor, "kill", affected=affected
        )

    def recover(self, *, now, reason: str, actor="operator"):
        if not reason.strip():
            return self._record(
                now, ControlActionType.RECOVERY_REQUEST, ControlScope.GLOBAL, "empty_reason", actor, "recovery"
            )
        if self.tripped_at and (now - self.tripped_at) < timedelta(seconds=self.config.recovery_cooldown_seconds):
            self.operating = Pm5OperatingState.MANUAL_REVIEW_REQUIRED
            rec = self._record(
                now, ControlActionType.RECOVERY_REQUEST, ControlScope.GLOBAL, "cooldown", actor, "recovery"
            )
            return rec.model_copy(update={"result": "cooldown"})
        self.kill_latched = False
        self.block_new = False
        self.close_only = False
        self.frozen_scopes.clear()
        self.operating = Pm5OperatingState.RECOVERED
        return self._record(now, ControlActionType.REENABLE, ControlScope.GLOBAL, reason, actor, "recovery")

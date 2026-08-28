from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.risk import KillSwitchStatus, RecoveryStage
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig


def may_recover(
    *,
    status: KillSwitchStatus,
    config: Pm4RiskGateConfig,
    reason: str,
    actor: str,
    tripped_at: datetime | None,
    now: datetime,
) -> tuple[bool, RecoveryStage]:
    if status not in {KillSwitchStatus.TRIPPED, KillSwitchStatus.LATCHED}:
        return False, RecoveryStage.NONE
    if config.auto_rearm:
        return False, RecoveryStage.INELIGIBLE
    if not reason.strip() or not actor.strip():
        return False, RecoveryStage.INELIGIBLE
    if config.require_manual_recovery_after_kill and tripped_at is not None:
        if now < tripped_at + timedelta(seconds=config.recovery_cooldown_seconds):
            return False, RecoveryStage.COOLDOWN
        return True, RecoveryStage.MANUAL_REVIEW
    return True, RecoveryStage.STAGED

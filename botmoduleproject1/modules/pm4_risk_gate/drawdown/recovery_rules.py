from __future__ import annotations

from botmoduleproject1.contracts.v1.risk import DrawdownStage, RecoveryStage
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig


def recovery_stage(
    current: DrawdownStage,
    *,
    config: Pm4RiskGateConfig,
    explicit: bool,
    reason: str,
) -> RecoveryStage:
    if current is DrawdownStage.KILL_PROTECTED:
        if not config.require_manual_recovery_after_kill:
            return RecoveryStage.INELIGIBLE
        if not explicit or not reason.strip():
            return RecoveryStage.INELIGIBLE
        return RecoveryStage.MANUAL_REVIEW
    if current is DrawdownStage.FREEZE:
        return RecoveryStage.COOLDOWN if explicit else RecoveryStage.INELIGIBLE
    if current in {DrawdownStage.RESTRICTED_RISK, DrawdownStage.REDUCED_RISK}:
        return RecoveryStage.STAGED
    return RecoveryStage.CLEARED

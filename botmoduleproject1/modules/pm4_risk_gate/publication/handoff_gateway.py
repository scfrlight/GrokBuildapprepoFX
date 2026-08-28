from __future__ import annotations

from botmoduleproject1.contracts.v1.risk import (
    HandoffEligibility,
    KillSwitchStatus,
    PreTradeControlDecision,
    RiskAdmissionDecision,
    RiskMode,
    RiskVerdictStatus,
)
from botmoduleproject1.modules.pm4_risk_gate.domain.policies import MODE_BLOCKS_NEW_RISK


def handoff_eligibility(
    *,
    admission: RiskAdmissionDecision,
    verdict: RiskVerdictStatus,
    kill: KillSwitchStatus,
    mode: RiskMode,
    pretrade: PreTradeControlDecision,
) -> HandoffEligibility:
    if kill in {KillSwitchStatus.TRIPPED, KillSwitchStatus.LATCHED}:
        return HandoffEligibility.BLOCKED_KILL
    if mode in MODE_BLOCKS_NEW_RISK:
        return HandoffEligibility.BLOCKED_DEGRADED
    if not pretrade.passed:
        return HandoffEligibility.BLOCKED_CONTROLS
    if verdict is RiskVerdictStatus.ALLOW and admission in {
        RiskAdmissionDecision.APPROVE,
        RiskAdmissionDecision.REDUCE,
    }:
        return HandoffEligibility.ELIGIBLE_PENDING_PM5
    return HandoffEligibility.INELIGIBLE

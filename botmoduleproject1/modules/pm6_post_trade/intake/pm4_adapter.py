from __future__ import annotations

from botmoduleproject1.contracts.v1.risk import KillSwitchStatus, RiskPublicationBundle


def kill_latched(bundle: RiskPublicationBundle | None) -> bool:
    if bundle is None:
        return False
    return bundle.kill_switch.status in {KillSwitchStatus.TRIPPED, KillSwitchStatus.LATCHED}


def freeze_or_halt(bundle: RiskPublicationBundle | None) -> bool:
    if bundle is None:
        return False
    from botmoduleproject1.contracts.v1.risk import RiskAdmissionDecision, RiskVerdictStatus

    if bundle.verdict.status is RiskVerdictStatus.HALT:
        return True
    return bundle.admission.decision in {
        RiskAdmissionDecision.FREEZE,
        RiskAdmissionDecision.KILL_PROTECTED,
    }

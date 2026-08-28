from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import DrawdownStage, ExposureSnapshot
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.domain.policies import THROTTLE_FACTOR


def peak_to_trough(exposure: ExposureSnapshot) -> Decimal:
    peak = exposure.peak_equity if exposure.peak_equity > 0 else exposure.equity
    if peak <= 0:
        return Decimal("0")
    trough = exposure.equity + exposure.unrealized_pnl
    dd = (peak - trough) / peak
    return dd if dd > 0 else Decimal("0")


def stage_for(drawdown: Decimal, config: Pm4RiskGateConfig, losing_streak: int) -> DrawdownStage:
    if drawdown >= config.dd_kill:
        return DrawdownStage.KILL_PROTECTED
    if drawdown >= config.dd_freeze:
        return DrawdownStage.FREEZE
    if drawdown >= config.dd_restricted:
        return DrawdownStage.RESTRICTED_RISK
    if drawdown >= config.dd_reduced:
        return DrawdownStage.REDUCED_RISK
    if drawdown >= config.dd_mild or losing_streak >= config.losing_streak_throttle:
        return DrawdownStage.MILD_THROTTLE
    return DrawdownStage.NORMAL


def throttle_factor(stage: DrawdownStage) -> Decimal:
    return THROTTLE_FACTOR[stage]

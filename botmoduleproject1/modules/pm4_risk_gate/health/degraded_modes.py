from __future__ import annotations

from botmoduleproject1.contracts.v1.risk import DrawdownStage, RiskMode


def mode_from(
    *,
    drawdown: DrawdownStage,
    kill_blocks: bool,
    forced: RiskMode | None = None,
) -> RiskMode:
    if forced is not None:
        return forced
    if kill_blocks:
        return RiskMode.KILL_PROTECTED
    if drawdown is DrawdownStage.KILL_PROTECTED:
        return RiskMode.KILL_PROTECTED
    if drawdown is DrawdownStage.FREEZE:
        return RiskMode.FREEZE
    if drawdown is DrawdownStage.RESTRICTED_RISK:
        return RiskMode.PROTECTION
    if drawdown is DrawdownStage.REDUCED_RISK:
        return RiskMode.THROTTLE
    if drawdown is DrawdownStage.MILD_THROTTLE:
        return RiskMode.THROTTLE
    if drawdown is DrawdownStage.RECOVERY:
        return RiskMode.RECOVERY
    return RiskMode.NORMAL

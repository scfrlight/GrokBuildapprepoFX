from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import DrawdownStage, DrawdownStateCard, ExposureSnapshot
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.drawdown.throttle_ladder import (
    peak_to_trough,
    stage_for,
    throttle_factor,
)


class DrawdownGovernor:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config
        self._forced: DrawdownStage | None = None

    def force(self, stage: DrawdownStage | None) -> None:
        self._forced = stage

    def evaluate(self, exposure: ExposureSnapshot) -> DrawdownStateCard:
        dd = peak_to_trough(exposure)
        if exposure.equity > 0:
            realized = abs(min(exposure.realized_pnl, Decimal("0"))) / exposure.equity
            current = max(dd, realized)
        else:
            current = dd
        intraday = Decimal("0")
        if exposure.equity > 0 and exposure.intraday_pnl < 0:
            intraday = abs(exposure.intraday_pnl) / exposure.equity
        stage = self._forced or stage_for(max(current, intraday), self.config, exposure.losing_streak)
        factor = throttle_factor(stage)
        return DrawdownStateCard(
            current_drawdown=current,
            peak_to_trough_drawdown=dd,
            intraday_loss=intraday,
            losing_streak=exposure.losing_streak,
            throttle_stage=stage,
            protection_stage=stage,
            freeze_state=stage in {DrawdownStage.FREEZE, DrawdownStage.KILL_PROTECTED},
            throttle_factor=factor,
        )

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import (
    ConcentrationExposureCard,
    ExposureSnapshot,
    HeatRegime,
    PortfolioHeatCard,
)
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.heat.effective_heat import directional_heat, effective_from_raw
from botmoduleproject1.modules.pm4_risk_gate.heat.residual_heat import residual


class PortfolioHeatEngine:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config

    def evaluate(
        self,
        exposure: ExposureSnapshot,
        concentration: ConcentrationExposureCard,
        proposed_risk: Decimal,
        equity: Decimal,
        stressed: bool,
    ) -> PortfolioHeatCard:
        raw_open = exposure.heat_r if exposure.heat_r > 0 else (
            exposure.gross_notional / equity if equity > 0 else Decimal("0")
        )
        incremental = proposed_risk / equity if equity > 0 else Decimal("0")
        raw = raw_open + incremental
        effective = effective_from_raw(raw, concentration.crowding_penalty)
        cluster = Decimal("0")
        if concentration.cluster_exposure:
            cluster = max(concentration.cluster_exposure.values())
        directional = directional_heat(exposure, equity) + incremental
        session = raw
        stressed_heat = effective * Decimal("1.25") if stressed else effective
        regime = HeatRegime.COOL
        if stressed_heat >= self.config.heat_critical or effective >= self.config.max_effective_heat:
            regime = HeatRegime.CRITICAL
        elif stressed:
            regime = HeatRegime.STRESSED
        elif effective >= self.config.heat_hot:
            regime = HeatRegime.HOT
        elif effective >= self.config.heat_warm:
            regime = HeatRegime.WARM
        headroom = residual(self.config.max_effective_heat, effective)
        return PortfolioHeatCard(
            raw_heat=raw,
            effective_heat=effective,
            cluster_heat=cluster,
            directional_heat=directional,
            session_heat=session,
            residual_heat_headroom=headroom,
            heat_regime=regime,
            stressed_heat=stressed_heat,
            proposed_incremental_heat=incremental,
        )

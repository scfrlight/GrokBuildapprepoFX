from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import (
    ConcentrationExposureCard,
    ConcentrationState,
    ExposureSnapshot,
)
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.concentration.overlap_engine import (
    cluster_id,
    currencies,
    european_weight,
    usd_weight,
)
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


class CorrelationEngine:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config

    def evaluate(
        self,
        request: RiskIntakeRequest,
        exposure: ExposureSnapshot,
        proposed_risk: Decimal,
        equity: Decimal,
    ) -> ConcentrationExposureCard:
        symbol = request.intent.symbol
        cid = (
            request.candidate.correlation_cluster
            if request.candidate and request.candidate.correlation_cluster
            else cluster_id(symbol)
        )
        open_symbols = tuple(exposure.symbols) if exposure.symbols else ()
        overlap_symbols = tuple(s for s in open_symbols if currencies(s) & currencies(symbol))
        currency_hits = tuple(sorted(currencies(symbol)))
        usd = Decimal(str(usd_weight(symbol)))
        euro = Decimal(str(european_weight(symbol)))
        if equity > 0:
            incremental = proposed_risk / equity
        else:
            incremental = Decimal("0")
        existing_cluster = Decimal("0")
        if cid in exposure.clusters and equity > 0:
            existing_cluster = exposure.heat_r
        cluster_exposure = existing_cluster + incremental
        usd_conc = usd * cluster_exposure
        euro_conc = euro * cluster_exposure
        crowded = False
        if self.config.one_per_cluster and any(
            cluster_id(s) == cid or s == symbol for s in open_symbols
        ):
            crowded = True
        penalty = Decimal("0")
        if overlap_symbols:
            penalty = min(Decimal("0.60"), Decimal("0.15") * Decimal(len(overlap_symbols)))
        if request.candidate is not None:
            corr = Decimal(str(request.candidate.scorecard.correlation_penalty)) / Decimal("100")
            penalty = max(penalty, corr)
        state = ConcentrationState.DIVERSIFIED
        blocked = False
        if crowded and self.config.one_per_cluster:
            state = ConcentrationState.BLOCKED
            blocked = True
            penalty = max(penalty, Decimal("1"))
        elif cluster_exposure >= self.config.cluster_cap or usd_conc >= self.config.usd_concentration_cap:
            state = ConcentrationState.STRESSED
            penalty = max(penalty, Decimal("0.85"))
        elif penalty >= self.config.crowding_block:
            state = ConcentrationState.CROWDED
        elif penalty > Decimal("0.20") or overlap_symbols:
            state = ConcentrationState.ELEVATED
        return ConcentrationExposureCard(
            symbol_overlap=overlap_symbols,
            currency_overlap=currency_hits,
            cluster_exposure={cid: cluster_exposure},
            crowding_penalty=penalty,
            stressed_concentration_state=state,
            usd_concentration=usd_conc,
            european_basket=euro_conc,
            one_per_cluster_blocked=blocked,
            cluster_id=cid,
        )

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import DrawdownStateCard, RiskBudgetCard
from botmoduleproject1.modules.pm4_risk_gate.budgeting.headroom import residual
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


class HierarchicalRiskAllocator:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config
        self._consumed: dict[str, Decimal] = {}

    def consume(self, key: str, amount: Decimal) -> None:
        self._consumed[key] = self._consumed.get(key, Decimal("0")) + amount

    def used(self, key: str) -> Decimal:
        return self._consumed.get(key, Decimal("0"))

    def allocate(
        self,
        request: RiskIntakeRequest,
        *,
        equity: Decimal,
        proposed_risk: Decimal,
        drawdown: DrawdownStateCard,
    ) -> RiskBudgetCard:
        throttle = drawdown.throttle_factor
        account = equity * self.config.account_risk_pct * throttle
        sleeve_key = request.intent.profile_id or "default_sleeve"
        regime_key = request.intent.regime_state or (
            request.candidate.context.regime.value if request.candidate else "unknown"
        )
        symbol_key = request.intent.symbol
        cluster_key = (
            request.candidate.correlation_cluster
            if request.candidate and request.candidate.correlation_cluster
            else symbol_key
        )
        sleeve = equity * self.config.sleeve_risk_pct * throttle
        regime = equity * self.config.regime_risk_pct * throttle
        cluster = equity * self.config.cluster_risk_pct * throttle
        symbol = equity * self.config.symbol_risk_pct * throttle
        candidate = equity * self.config.candidate_risk_pct * throttle
        levels = [
            ("account", account, self.used("account")),
            (f"sleeve:{sleeve_key}", sleeve, self.used(f"sleeve:{sleeve_key}")),
            (f"regime:{regime_key}", regime, self.used(f"regime:{regime_key}")),
            (f"cluster:{cluster_key}", cluster, self.used(f"cluster:{cluster_key}")),
            (f"symbol:{symbol_key}", symbol, self.used(f"symbol:{symbol_key}")),
            (f"candidate:{request.intent.intent_id}", candidate, Decimal("0")),
        ]
        headrooms = [residual(limit, used) for _, limit, used in levels]
        residual_headroom = min(headrooms) if headrooms else Decimal("0")
        tree = {name: str(limit) for name, limit, _ in levels}
        return RiskBudgetCard(
            account_budget=account,
            sleeve_budget=sleeve,
            regime_budget=regime,
            cluster_budget=cluster,
            symbol_budget=symbol,
            candidate_budget=candidate,
            residual_headroom=residual_headroom,
            consumed_headroom=max(Decimal("0"), proposed_risk if proposed_risk <= residual_headroom else residual_headroom),
            proposed_risk=proposed_risk,
            throttle_factor=throttle,
            tree=tree,
        )

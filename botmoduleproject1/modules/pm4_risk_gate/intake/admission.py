"""Hard vetoes before any sizing result is trusted."""

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.pm2 import QualityTier
from botmoduleproject1.contracts.v1.risk import (
    ConcentrationExposureCard,
    DrawdownStage,
    DrawdownStateCard,
    KillSwitchState,
    PortfolioHeatCard,
    RiskAdmissionCard,
    RiskAdmissionDecision,
    RiskDecisionTier,
    RiskMode,
    RiskRejectionReason,
)
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm4_risk_gate.domain.policies import MODE_BLOCKS_NEW_RISK
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


class RiskAdmissionController:
    def __init__(self, config: Pm4RiskGateConfig) -> None:
        self.config = config

    def decide(
        self,
        request: RiskIntakeRequest,
        *,
        intake_reasons: list[RiskRejectionReason],
        drawdown: DrawdownStateCard,
        heat: PortfolioHeatCard,
        concentration: ConcentrationExposureCard,
        kill: KillSwitchState,
        mode: RiskMode,
        budget_headroom: Decimal,
        feature_enabled: bool,
        session: str | None,
    ) -> RiskAdmissionCard:
        vetoes: list[str] = []
        reasons: list[str] = []
        if not feature_enabled:
            vetoes.append(RiskRejectionReason.FEATURE_DISABLED.value)
        for item in intake_reasons:
            vetoes.append(item.value)
        if mode in MODE_BLOCKS_NEW_RISK:
            if mode is RiskMode.CLOSE_ONLY:
                vetoes.append(RiskRejectionReason.CLOSE_ONLY.value)
            elif mode is RiskMode.NO_NEW_RISK:
                vetoes.append(RiskRejectionReason.NO_NEW_RISK.value)
            elif mode is RiskMode.KILL_PROTECTED:
                vetoes.append(RiskRejectionReason.KILL_SWITCH.value)
            else:
                vetoes.append(RiskRejectionReason.DEGRADED_MODE.value)
        if drawdown.throttle_stage in {DrawdownStage.FREEZE, DrawdownStage.KILL_PROTECTED}:
            vetoes.append(RiskRejectionReason.DRAWDOWN_LIMIT.value)
        if drawdown.intraday_loss >= self.config.max_intraday_loss_pct:
            vetoes.append(RiskRejectionReason.DRAWDOWN_LIMIT.value)
        if heat.residual_heat_headroom <= 0 or heat.heat_regime.value in {"critical"}:
            vetoes.append(RiskRejectionReason.HEAT_LIMIT.value)
        if concentration.one_per_cluster_blocked or concentration.stressed_concentration_state.value in {
            "blocked",
            "stressed",
        }:
            if concentration.one_per_cluster_blocked or concentration.stressed_concentration_state.value == "blocked":
                vetoes.append(RiskRejectionReason.CONCENTRATION_LIMIT.value)
        if budget_headroom <= 0:
            vetoes.append(RiskRejectionReason.BUDGET_EXHAUSTED.value)
        if session and session.lower() not in {s.lower() for s in self.config.session_allow}:
            vetoes.append(RiskRejectionReason.SESSION_RESTRICTED.value)
        if request.candidate and request.candidate.scorecard.quality_tier is QualityTier.SUPPRESS:
            vetoes.append(RiskRejectionReason.HANDOFF_INELIGIBLE.value)
        if request.candidate and request.candidate.scorecard.liquidity_score < self.config.min_liquidity_score:
            vetoes.append(RiskRejectionReason.LIQUIDITY.value)

        unique = tuple(dict.fromkeys(vetoes))
        if unique:
            if RiskRejectionReason.KILL_SWITCH.value in unique:
                decision = RiskAdmissionDecision.KILL_PROTECTED
                tier = RiskDecisionTier.HARD_VETO
            elif RiskRejectionReason.DRAWDOWN_LIMIT.value in unique and drawdown.freeze_state:
                decision = RiskAdmissionDecision.FREEZE
                tier = RiskDecisionTier.HARD_VETO
            else:
                decision = RiskAdmissionDecision.REJECT
                tier = RiskDecisionTier.HARD_VETO if len(unique) > 1 else RiskDecisionTier.POLICY_REJECT
            return RiskAdmissionCard(
                decision=decision,
                tier=tier,
                reasons=unique,
                active_controls=("admission", "deny_by_default"),
                vetoes=unique,
                detail="deny-by-default; hard veto before sizing is trusted",
            )

        reduce = (
            drawdown.throttle_factor < Decimal("1")
            or concentration.crowding_penalty > Decimal("0.15")
            or heat.heat_regime.value in {"warm", "hot", "stressed"}
        )
        if reduce:
            return RiskAdmissionCard(
                decision=RiskAdmissionDecision.REDUCE,
                tier=RiskDecisionTier.REDUCED,
                reasons=("throttled_or_crowded",),
                active_controls=("admission", "throttle"),
                vetoes=(),
                detail="admitted with reduction",
            )
        reasons.append("all_hard_vetoes_clear")
        return RiskAdmissionCard(
            decision=RiskAdmissionDecision.APPROVE,
            tier=RiskDecisionTier.ADMITTED,
            reasons=tuple(reasons),
            active_controls=("admission",),
            vetoes=(),
            detail="admitted",
        )

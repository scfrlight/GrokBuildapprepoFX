"""Capital-preservation policies. No alpha. No side mutation."""

from __future__ import annotations

from decimal import Decimal

from botmoduleproject1.contracts.v1.risk import DrawdownStage, RiskMode

PRODUCER = "pm4_risk_gate"
POLICY_OWNER = "risk-function"
CONTROL_VERSION = "0.6.0"

THROTTLE_FACTOR: dict[DrawdownStage, Decimal] = {
    DrawdownStage.NORMAL: Decimal("1.00"),
    DrawdownStage.MILD_THROTTLE: Decimal("0.75"),
    DrawdownStage.REDUCED_RISK: Decimal("0.50"),
    DrawdownStage.RESTRICTED_RISK: Decimal("0.25"),
    DrawdownStage.FREEZE: Decimal("0"),
    DrawdownStage.KILL_PROTECTED: Decimal("0"),
    DrawdownStage.RECOVERY: Decimal("0.35"),
}

MODE_BLOCKS_NEW_RISK = frozenset(
    {
        RiskMode.FREEZE,
        RiskMode.CLOSE_ONLY,
        RiskMode.NO_NEW_RISK,
        RiskMode.KILL_PROTECTED,
        RiskMode.MANUAL_REVIEW,
    }
)

BLOCKED_QUALIFICATION = frozenset({"stale", "suppressed", "invalidated", "cooldown"})
BLOCKED_QUALITY = frozenset({"suppress"})
EUROPEAN_MAJORS = frozenset({"EURUSD", "GBPUSD", "EURGBP", "EURJPY", "GBPJPY"})
USD_QUOTES = frozenset({"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD"})

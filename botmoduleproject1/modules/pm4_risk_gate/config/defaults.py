"""Default PM4 knobs. Enabling is a feature flag, not these values."""

from decimal import Decimal

from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig

DEFAULT_CONFIG = Pm4RiskGateConfig()
DEFAULT_EQUITY = Decimal("100000")
POLICY_VERSION = "pm4.risk.v1"

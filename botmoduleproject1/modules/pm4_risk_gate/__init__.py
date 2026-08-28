"""PM4 Risk Gate.

Authoritative pre-trade capital protection. Deny-by-default.
Produces RiskVerdict / RiskPublicationBundle. Never an order. Never PM5.
"""

from botmoduleproject1.modules.pm4_risk_gate.module import PM4RiskGateModule

__all__ = ["PM4RiskGateModule"]

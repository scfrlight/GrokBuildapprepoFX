"""PM4 capability declaration. Critical capital-protection gate."""

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM4_RISK_GATE_METADATA = ModuleMetadata(
    name="pm4_risk",
    version="0.6.0",
    capabilities=(Capability.RISK_GATING, Capability.DIAGNOSTICS),
    critical=True,
    dependencies=("pm1_platform",),
    health_support=True,
    readiness_required=True,
    liveness_required=True,
    description=(
        "PM4 Risk Gate. Authoritative pre-trade capital protection. "
        "Deny-by-default. ALLOW is not an order. PM5 remains closed."
    ),
)

__all__ = ["PM4_RISK_GATE_METADATA"]

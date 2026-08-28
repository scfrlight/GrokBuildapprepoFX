"""PM2 capability declaration."""

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM2_METADATA = ModuleMetadata(
    name="pm2_market_context",
    version="0.3.0",
    capabilities=(
        Capability.MARKET_DATA,
        Capability.REGIME_DETECTION,
        Capability.DIAGNOSTICS,
    ),
    critical=False,
    dependencies=("pm1_platform",),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description="Market context, regime, confluence, ranking. No orders.",
)

__all__ = ["PM2_METADATA"]

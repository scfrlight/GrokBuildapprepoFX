from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM6_POST_TRADE_METADATA = ModuleMetadata(
    name="pm6_monitoring",
    version="0.8.0",
    capabilities=(Capability.TELEMETRY, Capability.DIAGNOSTICS),
    critical=False,
    dependencies=("pm1_platform", "pm4_risk", "pm5_execution"),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description=(
        "PM6 post-trade controls, surveillance, incidents, and governance. "
        "Observes PM4/PM5. Never sends orders. Never fabricates broker truth. "
        "NullMonitoring remains the default bind."
    ),
)

__all__ = ["PM6_POST_TRADE_METADATA"]

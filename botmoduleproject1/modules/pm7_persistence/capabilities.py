from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM7_PERSISTENCE_METADATA = ModuleMetadata(
    name="pm7_ledger",
    version="0.9.0",
    capabilities=(Capability.LEDGER, Capability.DIAGNOSTICS),
    critical=False,
    dependencies=("pm1_platform", "pm4_risk", "pm5_execution", "pm6_monitoring"),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description=(
        "PM7 append-only journal, evidence, replay, and integrity. "
        "Stores PM4/PM5/PM6 publications. Never sends orders. "
        "Never fabricates broker truth. NullLedger remains the default bind."
    ),
)

__all__ = ["PM7_PERSISTENCE_METADATA"]

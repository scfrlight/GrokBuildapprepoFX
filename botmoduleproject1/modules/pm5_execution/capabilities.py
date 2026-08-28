from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM5_EXECUTION_METADATA = ModuleMetadata(
    name="pm5_execution",
    version="0.7.0",
    capabilities=(Capability.EXECUTION, Capability.DIAGNOSTICS),
    critical=False,
    dependencies=("pm1_platform", "pm4_risk"),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description=(
        "PM5 Execution fabric. OMS/EMS, simulation adapter, independent control "
        "plane, reconciliation. PM4-only authorization. No MT5 send. "
        "DisabledExecution remains the default bind."
    ),
)

__all__ = ["PM5_EXECUTION_METADATA"]

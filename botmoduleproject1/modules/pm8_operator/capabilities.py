from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM8_OPERATOR_METADATA = ModuleMetadata(
    name="pm8_operator",
    version="0.10.0",
    capabilities=(Capability.OPERATOR_CONTROL, Capability.DIAGNOSTICS),
    critical=False,
    dependencies=("pm1_platform",),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description=(
        "PM8 operator control plane, HITL queue, and simulated transport. "
        "Commands are not orders. Telegram Bot API is not bound. "
        "NullOperator remains the default bind."
    ),
)

__all__ = ["PM8_OPERATOR_METADATA"]

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM3_STRATEGY_ENGINE_METADATA = ModuleMetadata(
    name="pm3_strategy_engine",
    version="0.4.0",
    capabilities=(
        Capability.SIGNALS,
        Capability.STRATEGY_EVALUATION,
        Capability.STRATEGY_CONSENSUS,
        Capability.TRADE_INTENT_GENERATION,
        Capability.PROFILE_GOVERNANCE,
        Capability.STRATEGY_HEALTH,
        Capability.STRATEGY_DIAGNOSTICS,
    ),
    critical=False,
    dependencies=("pm1_platform",),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description="PM3-Strategy Engine. TradeIntent only. Never orders, never QRF.",
)

__all__ = ["PM3_STRATEGY_ENGINE_METADATA"]

"""PM3 forecasting / QRF capability declaration. Non-critical enrichment."""

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata

PM3_FORECASTING_METADATA = ModuleMetadata(
    name="pm3_forecasting",
    version="0.5.0",
    capabilities=(Capability.FORECASTING, Capability.DIAGNOSTICS),
    critical=False,
    dependencies=("pm1_platform",),
    health_support=True,
    readiness_required=False,
    liveness_required=True,
    description=(
        "PM3 forecasting / QRF. Residual quantile envelope research kernel. "
        "Enrichment only. Never orders, never mutates side."
    ),
)

__all__ = ["PM3_FORECASTING_METADATA"]

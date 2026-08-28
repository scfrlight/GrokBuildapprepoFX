"""Typed PM3 forecasting / QRF configuration. No secrets. No order-send knobs."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from botmoduleproject1.modules.pm3_forecasting.domain.enums import EstimatorKind, OperatingMode


class Pm3ForecastingConfig(BaseModel):
    """Public knobs. Enabling the kernel is a feature flag, not this block."""

    horizon_bars: int = Field(default=4, ge=1, le=48)
    lookback_bars: int = Field(default=64, ge=16, le=512)
    min_samples: int = Field(default=20, ge=1, le=512)
    embargo_bars: int = Field(default=1, ge=1, le=16)
    timeframe: str = "H1"
    operating_mode: str = OperatingMode.SHADOW.value
    observe_only: bool = True
    estimator: str = EstimatorKind.RESIDUAL_QUANTILE_ENVELOPE.value
    fx_decimal_places: int = Field(default=5, ge=1, le=8)
    min_coverage_samples: int = Field(default=20, ge=1, le=512)

    @field_validator("timeframe")
    @classmethod
    def _tf(cls, value: str) -> str:
        allowed = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}
        cleaned = value.strip().upper()
        if cleaned not in allowed:
            raise ValueError(f"unsupported timeframe {value!r}")
        return cleaned

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        allowed = {m.value for m in OperatingMode}
        if value not in allowed:
            raise ValueError("operating_mode must be shadow|observe-only|paper")
        return value

    @field_validator("estimator")
    @classmethod
    def _estimator(cls, value: str) -> str:
        if value != EstimatorKind.RESIDUAL_QUANTILE_ENVELOPE.value:
            raise ValueError(
                "fitted QRF is out of scope for Sequence 05; "
                "estimator must be residual_quantile_envelope"
            )
        return value

    @model_validator(mode="after")
    def _observe_only(self) -> Pm3ForecastingConfig:
        if not self.observe_only:
            raise ValueError("pm3_forecasting.observe_only must stay true")
        return self


def config_from_settings(settings: object) -> Pm3ForecastingConfig:
    section = getattr(settings, "pm3_forecasting")
    return Pm3ForecastingConfig(
        horizon_bars=section.horizon_bars,
        lookback_bars=section.lookback_bars,
        min_samples=section.min_samples,
        embargo_bars=section.embargo_bars,
        timeframe=section.timeframe,
        operating_mode=section.operating_mode,
        observe_only=bool(section.observe_only),
    )

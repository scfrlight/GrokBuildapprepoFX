"""In-memory ForecastOutput publication. Not Telegram. Not an order path."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.forecasting import ForecastOutput


class ForecastPublisher:
    def __init__(self) -> None:
        self.published: list[ForecastOutput] = []

    def publish(self, forecast: ForecastOutput) -> ForecastOutput:
        self.published.append(forecast)
        return forecast

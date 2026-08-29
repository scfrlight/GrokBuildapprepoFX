"""Real Telegram Bot API. Refused in Sequence 10."""

from __future__ import annotations

from botmoduleproject1.app.exceptions import FeatureFlagError


class RealTelegramTransport:
    def __init__(self, *args, **kwargs) -> None:
        raise FeatureFlagError(
            "Telegram Bot API is refused in Sequence 10; "
            "use enable_pm8_operator with SimulatedTransport"
        )

    def poll(self) -> None:
        raise FeatureFlagError("Telegram Bot API is refused in Sequence 10")

    def send(self, *args, **kwargs) -> None:
        raise FeatureFlagError("Telegram Bot API is refused in Sequence 10")

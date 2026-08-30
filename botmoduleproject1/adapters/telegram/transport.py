"""Real Telegram Bot API. Refused. Canonical Sequence 13 never binds it."""

from __future__ import annotations

from botmoduleproject1.app.exceptions import FeatureFlagError


class RealTelegramTransport:
    def __init__(self, *args, **kwargs) -> None:
        raise FeatureFlagError(
            "Telegram Bot API is refused; "
            "canonical Sequence 13 uses SimulatedTransport only"
        )

    def poll(self) -> None:
        raise FeatureFlagError("Telegram Bot API is refused")

    def send(self, *args, **kwargs) -> None:
        raise FeatureFlagError("Telegram Bot API is refused")

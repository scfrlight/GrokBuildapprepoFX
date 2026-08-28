"""System and fake clocks. Adapters only — no trading logic."""

from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.time import UTC, utc_now


class SystemClock:
    def now(self) -> datetime:
        return utc_now()


class FakeClock:
    def __init__(self, instant: datetime | None = None) -> None:
        self._instant = instant or utc_now()

    def now(self) -> datetime:
        return self._instant

    def advance(self, seconds: float) -> datetime:
        self._instant = self._instant + timedelta(seconds=seconds)
        if self._instant.tzinfo is None:
            self._instant = self._instant.replace(tzinfo=UTC)
        return self._instant

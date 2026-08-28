from __future__ import annotations

from datetime import datetime, timedelta


class BurstTracker:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self._hits: list[datetime] = []

    def allow(self, now: datetime) -> bool:
        cutoff = now - self.window
        self._hits = [t for t in self._hits if t >= cutoff]
        if len(self._hits) >= self.limit:
            return False
        self._hits.append(now)
        return True

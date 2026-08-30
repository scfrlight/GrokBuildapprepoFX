"""Restart-safe drawdown / daily-loss ledger. No silent reset."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily
from botmoduleproject1.modules.pm8_persistence.money import canonical, decimal_from


class DrawdownLedger:
    def __init__(self, persistence: Any | None = None) -> None:
        self.persistence = persistence
        self.peak_equity: Decimal | None = None
        self.daily_loss: Decimal = Decimal("0")
        self.daily_key: str | None = None
        self.losing_streak: int = 0
        self.loaded = False
        if persistence is not None:
            self.reload()

    def _day_key(self, now: datetime) -> str:
        stamp = now.astimezone(timezone.utc)
        return stamp.date().isoformat()

    def reload(self) -> None:
        if self.persistence is None:
            return
        events = self.persistence.store.list_events(limit=10_000)
        latest = None
        for ev in events:
            if ev.get("event_type") == "risk.drawdown.snapshot":
                latest = ev
        if latest is None:
            self.loaded = True
            return
        raw = latest.get("payload_json") or "{}"
        payload = json.loads(raw) if isinstance(raw, str) else raw
        peak = payload.get("peak_equity")
        if peak is not None:
            self.peak_equity = decimal_from(peak, field="peak_equity")
        self.daily_loss = decimal_from(payload.get("daily_loss") or "0", field="daily_loss")
        self.daily_key = payload.get("daily_key")
        self.losing_streak = int(payload.get("losing_streak") or 0)
        self.loaded = True

    def observe(
        self,
        *,
        equity: Decimal,
        peak: Decimal,
        realized_day: Decimal,
        streak: int,
        now: datetime,
        persist: bool = True,
    ) -> dict[str, Any]:
        day = self._day_key(now)
        if self.daily_key is None:
            self.daily_key = day
        elif self.daily_key != day:
            # UTC date rolled; do not carry the previous day's loss. Peak still stands.
            self.daily_loss = Decimal("0")
            self.daily_key = day
        if self.peak_equity is None:
            self.peak_equity = peak if peak > 0 else equity
        if peak > self.peak_equity:
            self.peak_equity = peak
        if equity > self.peak_equity:
            self.peak_equity = equity
        loss = abs(min(realized_day, Decimal("0")))
        if loss > self.daily_loss:
            self.daily_loss = loss
        if streak > self.losing_streak:
            self.losing_streak = streak
        snap = {
            "peak_equity": canonical(self.peak_equity),
            "daily_loss": canonical(self.daily_loss),
            "daily_key": self.daily_key,
            "losing_streak": self.losing_streak,
            "equity": canonical(equity),
        }
        if persist and self.persistence is not None:
            self.persistence.ingest_event(
                event_type="risk.drawdown.snapshot",
                producer="pm4_risk_gate",
                family=TableFamily.AUDIT,
                payload=snap,
            )
        return snap

    def drawdown_pct(self, equity: Decimal) -> Decimal:
        if self.peak_equity is None or self.peak_equity <= 0:
            return Decimal("0")
        if equity >= self.peak_equity:
            return Decimal("0")
        return (self.peak_equity - equity) / self.peak_equity

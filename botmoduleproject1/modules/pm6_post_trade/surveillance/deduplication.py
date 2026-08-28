from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.post_trade import PostTradeAlert
from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig


class AlertDeduper:
    def __init__(self, config: Pm6PostTradeConfig) -> None:
        self.config = config
        self._seen: dict[str, PostTradeAlert] = {}

    def apply(self, alert: PostTradeAlert, now: datetime) -> PostTradeAlert:
        prev = self._seen.get(alert.fingerprint)
        if prev is None:
            self._seen[alert.fingerprint] = alert
            return alert
        window = timedelta(seconds=self.config.alert_dedup_seconds)
        if now - prev.occurred_at <= window:
            updated = prev.model_copy(
                update={
                    "suppressed": True,
                    "suppress_count": prev.suppress_count + 1,
                    "updated_evidence": True,
                }
                if "updated_evidence" in PostTradeAlert.model_fields
                else {
                    "suppressed": True,
                    "suppress_count": prev.suppress_count + 1,
                    "observed": {**prev.observed, "duplicate": True},
                }
            )
            self._seen[alert.fingerprint] = updated
            return updated
        self._seen[alert.fingerprint] = alert
        return alert

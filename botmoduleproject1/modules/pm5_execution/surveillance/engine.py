from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

from botmoduleproject1.contracts.v1.execution import SurveillanceAlert
from botmoduleproject1.modules.pm5_execution.config.schema import Pm5ExecutionConfig
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class SurveillanceEngine:
    def __init__(self, config: Pm5ExecutionConfig) -> None:
        self.config = config
        self._submits: deque[datetime] = deque()
        self._rejects: deque[datetime] = deque()
        self._cancels: deque[datetime] = deque()
        self._modifies: deque[datetime] = deque()
        self.alerts: list[SurveillanceAlert] = []

    def _prune(self, q: deque, now: datetime) -> None:
        window = timedelta(seconds=self.config.burst_window_seconds)
        while q and now - q[0] > window:
            q.popleft()

    def note_submit(self, now: datetime) -> SurveillanceAlert | None:
        self._prune(self._submits, now)
        self._submits.append(now)
        if len(self._submits) > self.config.submit_burst:
            return self._alert(now, "submit_burst", "throttle", True)
        return None

    def note_reject(self, now: datetime) -> SurveillanceAlert | None:
        self._prune(self._rejects, now)
        self._rejects.append(now)
        if len(self._rejects) > self.config.reject_burst:
            return self._alert(now, "reject_burst", "kill", True)
        return None

    def note_cancel(self, now: datetime) -> SurveillanceAlert | None:
        self._prune(self._cancels, now)
        self._cancels.append(now)
        if len(self._cancels) > self.config.cancel_burst:
            return self._alert(now, "cancel_storm", "throttle", True)
        return None

    def note_modify(self, now: datetime) -> SurveillanceAlert | None:
        self._prune(self._modifies, now)
        self._modifies.append(now)
        if len(self._modifies) > self.config.modify_burst:
            return self._alert(now, "modify_storm", "throttle", True)
        return None

    def _alert(self, now, detector, action, auto) -> SurveillanceAlert:
        alert = SurveillanceAlert(
            alert_id=new_id(),
            occurred_at=now,
            severity="high",
            category="repeated_execution",
            detector=detector,
            observed={"window_s": self.config.burst_window_seconds},
            thresholds={"submit": self.config.submit_burst, "reject": self.config.reject_burst},
            scope="account",
            recommended_action=action,
            automatic_protection=auto,
        )
        self.alerts.append(alert)
        return alert

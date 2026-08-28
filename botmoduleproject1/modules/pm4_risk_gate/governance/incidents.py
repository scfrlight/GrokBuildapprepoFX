from __future__ import annotations

from datetime import datetime
from typing import Any

from botmoduleproject1.contracts.v1.risk import RiskSeverity


class IncidentLog:
    def __init__(self) -> None:
        self.incidents: list[dict[str, Any]] = []

    def raise_incident(
        self,
        *,
        now: datetime,
        title: str,
        severity: RiskSeverity,
        detail: str,
    ) -> dict[str, Any]:
        item = {
            "at": now.isoformat(),
            "title": title,
            "severity": severity.value,
            "detail": detail,
        }
        self.incidents.append(item)
        return item

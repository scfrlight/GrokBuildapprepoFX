from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from botmoduleproject1.contracts.v1.post_trade import IncidentType, SeverityLevel


@dataclass
class Finding:
    detector: str
    category: str
    severity: SeverityLevel
    description: str
    recommended_action: str
    incident_type: IncidentType | None = None
    observed: dict[str, Any] = field(default_factory=dict)
    threshold: dict[str, Any] = field(default_factory=dict)
    scope: str = "account"
    auto_action: str = "none"
    fingerprint: str = ""

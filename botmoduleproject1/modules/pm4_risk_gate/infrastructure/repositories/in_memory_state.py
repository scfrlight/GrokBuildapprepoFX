"""In-memory control state. Not durable. Replaceable by PM7/PM8."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.modules.pm4_risk_gate.models.inputs import RiskIntakeRequest


class InMemoryRiskState:
    def __init__(self) -> None:
        self.by_key: dict[str, RiskPublicationBundle] = {}
        self.intents: list[str] = []
        self.last_request: RiskIntakeRequest | None = None
        self.uri = "memory://pm4-risk-state"

    def get(self, key: str) -> RiskPublicationBundle | None:
        return self.by_key.get(key)

    def put(self, key: str, bundle: RiskPublicationBundle) -> None:
        self.by_key[key] = bundle
        self.intents.append(key)

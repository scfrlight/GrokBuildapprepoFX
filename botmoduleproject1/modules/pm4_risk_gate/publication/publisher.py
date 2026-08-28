from __future__ import annotations

from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle


class RiskPublisher:
    def __init__(self) -> None:
        self.published: list[RiskPublicationBundle] = []

    def publish(self, bundle: RiskPublicationBundle) -> RiskPublicationBundle:
        self.published.append(bundle)
        return bundle

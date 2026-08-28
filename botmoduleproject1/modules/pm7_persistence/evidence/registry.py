from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import EvidenceBundle


class EvidenceRegistry:
    def __init__(self) -> None:
        self.notes: list[str] = []
        self.bundles: list[EvidenceBundle] = []

    def note(self, text: str) -> None:
        self.notes.append(text)

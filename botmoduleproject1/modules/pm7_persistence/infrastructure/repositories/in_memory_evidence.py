class InMemoryEvidenceRepository:
    def __init__(self) -> None:
        self.items = []

    def add(self, bundle) -> None:
        self.items.append(bundle)

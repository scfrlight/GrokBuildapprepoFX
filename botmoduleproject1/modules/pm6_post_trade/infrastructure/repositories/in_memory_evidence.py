class InMemoryEvidenceRepository:
    def __init__(self) -> None:
        self.items = []

    def add(self, item) -> None:
        self.items.append(item)

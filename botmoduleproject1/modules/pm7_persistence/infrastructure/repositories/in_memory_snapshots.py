class InMemorySnapshotRepository:
    def __init__(self) -> None:
        self.items = []

    def add(self, snap) -> None:
        self.items.append(snap)

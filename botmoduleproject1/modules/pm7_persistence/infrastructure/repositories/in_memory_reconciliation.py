class InMemoryReconRepository:
    def __init__(self) -> None:
        self.items = []

    def add(self, record) -> None:
        self.items.append(record)

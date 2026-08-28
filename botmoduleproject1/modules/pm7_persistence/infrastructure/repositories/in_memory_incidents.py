class InMemoryIncidentIndex:
    def __init__(self) -> None:
        self.ids = []

    def add(self, incident_id: str) -> None:
        self.ids.append(incident_id)

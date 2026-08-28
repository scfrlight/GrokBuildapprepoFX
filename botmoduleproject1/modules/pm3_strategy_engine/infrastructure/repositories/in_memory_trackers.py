from __future__ import annotations

from botmoduleproject1.contracts.v1.strategy_engine import TrackerSnapshot


class InMemoryTrackerRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], TrackerSnapshot] = {}

    def get(self, profile_id: str, version_id: str) -> TrackerSnapshot | None:
        return self._items.get((profile_id, version_id))

    def save(self, snapshot: TrackerSnapshot) -> None:
        self._items[(snapshot.profile_id, snapshot.version_id)] = snapshot

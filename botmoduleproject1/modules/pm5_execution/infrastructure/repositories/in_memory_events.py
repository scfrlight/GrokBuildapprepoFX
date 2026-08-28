from __future__ import annotations


class InMemoryEventRepository:
    def __init__(self) -> None:
        self._items: list[dict] = []

    def append(self, event: dict) -> None:
        self._items.append(event)

    def all(self) -> tuple[dict, ...]:
        return tuple(self._items)

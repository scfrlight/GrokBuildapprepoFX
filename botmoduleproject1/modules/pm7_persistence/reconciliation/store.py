from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import ReconciliationPersistRecord, ReconciliationPersistState


class InMemoryReconciliationStore:
    def __init__(self) -> None:
        self._items: list[ReconciliationPersistRecord] = []

    def store(self, record: ReconciliationPersistRecord) -> ReconciliationPersistRecord:
        self._items.append(record)
        return record

    def all(self) -> list[ReconciliationPersistRecord]:
        return list(self._items)

    def history(self, *, order_id: str | None = None, session_id: str | None = None, symbol: str | None = None):
        items = self._items
        if order_id:
            items = [r for r in items if r.order_id == order_id]
        if session_id:
            items = [r for r in items if r.session_id == session_id]
        if symbol:
            items = [r for r in items if r.symbol == symbol]
        return list(items)

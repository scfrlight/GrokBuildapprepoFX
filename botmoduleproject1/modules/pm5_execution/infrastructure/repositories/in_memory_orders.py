from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import OrderRecord


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._items: dict[str, OrderRecord] = {}

    def put(self, record: OrderRecord) -> None:
        self._items[str(record.order_id)] = record

    def get(self, order_id) -> OrderRecord | None:
        return self._items.get(str(order_id))

    def all(self) -> tuple[OrderRecord, ...]:
        return tuple(self._items.values())

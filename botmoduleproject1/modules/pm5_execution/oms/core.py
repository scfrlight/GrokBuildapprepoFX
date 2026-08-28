from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from botmoduleproject1.contracts.v1.execution import (
    ExecutionLifecycleState,
    FillEvent,
    OrderLifecycleEvent,
    OrderRecord,
)
from botmoduleproject1.modules.pm5_execution.oms.state_machine import IllegalTransition, apply_transition


class OrderLifecycleManager:
    def __init__(self) -> None:
        self._orders: dict = {}
        self._events: dict[str, list[OrderLifecycleEvent]] = {}
        self._by_key: dict[str, str] = {}
        self._payload: dict[str, tuple] = {}

    def get(self, order_id) -> OrderRecord | None:
        rec = self._orders.get(str(order_id))
        return rec

    def by_key(self, key: str) -> OrderRecord | None:
        oid = self._by_key.get(key)
        return self.get(oid) if oid else None

    def events(self, order_id) -> tuple[OrderLifecycleEvent, ...]:
        return tuple(self._events.get(str(order_id), ()))

    def all_orders(self) -> tuple[OrderRecord, ...]:
        return tuple(self._orders.values())

    def put_new(self, record: OrderRecord, event: OrderLifecycleEvent) -> None:
        key = str(record.order_id)
        self._orders[key] = record
        self._events.setdefault(key, []).append(event)
        self._by_key[record.idempotency_key] = key
        self._payload[record.idempotency_key] = (
            record.symbol,
            record.direction,
            record.original_quantity,
        )

    def payload_for(self, key: str) -> tuple | None:
        return self._payload.get(key)

    def transit(self, record: OrderRecord, target: ExecutionLifecycleState, **kwargs) -> OrderRecord:
        nxt, event = apply_transition(record, target, **kwargs)
        key = str(record.order_id)
        self._orders[key] = nxt
        self._events.setdefault(key, []).append(event)
        return nxt

    def apply_fill(self, record: OrderRecord, fill: FillEvent, *, now: datetime) -> OrderRecord:
        filled = record.filled_quantity + fill.quantity
        remaining = record.original_quantity - filled
        if remaining < 0:
            remaining = Decimal("0")
        avg = fill.price
        if record.average_fill_price is not None and record.filled_quantity > 0:
            avg = (
                record.average_fill_price * record.filled_quantity + fill.price * fill.quantity
            ) / filled
        target = (
            ExecutionLifecycleState.FILLED
            if remaining == 0
            else ExecutionLifecycleState.PARTIALLY_FILLED
        )
        return self.transit(
            record,
            target,
            now=now,
            reason="fill",
            actor="simulation_adapter",
            source="ems",
            filled_quantity=filled,
            remaining_quantity=remaining,
            average_fill_price=avg,
            broker_ticket=fill.ticket or record.broker_ticket,
        )

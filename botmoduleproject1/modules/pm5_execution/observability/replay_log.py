from __future__ import annotations

from botmoduleproject1.contracts.v1.execution import OrderLifecycleEvent, ReplayBundle
from botmoduleproject1.modules.pm5_execution.domain.ids import new_id


class ReplayService:
    def __init__(self) -> None:
        self._events: dict[str, list[dict]] = {}

    def append(self, order_id, payload: dict) -> None:
        self._events.setdefault(str(order_id), []).append(dict(payload))

    def note_lifecycle(self, event: OrderLifecycleEvent) -> None:
        self.append(
            event.order_id,
            {
                "kind": "lifecycle",
                "from": None if event.from_state is None else event.from_state.value,
                "to": event.to_state.value,
                "reason": event.reason,
                "actor": event.actor,
                "source": event.source,
                "occurred_at": event.occurred_at.isoformat(),
            },
        )

    def bundle(self, order_id) -> ReplayBundle:
        events = tuple(self._events.get(str(order_id), ()))
        return ReplayBundle(bundle_id=new_id(), order_id=order_id, events=events, deterministic=True)

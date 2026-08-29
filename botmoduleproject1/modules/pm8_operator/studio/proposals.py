"""Research tuning proposals. Never auto-promote to live."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from botmoduleproject1.contracts.v1.tuning import (
    ParameterSchema,
    TuningChangeRequest,
    TuningChangeStatus,
)


class Studio:
    def __init__(self) -> None:
        self._items: dict[str, TuningChangeRequest] = {}

    def propose(
        self,
        *,
        actor: str,
        now: datetime,
        name: str,
        new_value: Any,
        key: str | None = None,
    ) -> TuningChangeRequest:
        schema = ParameterSchema(
            name=name,
            display_name=name,
            group="research",
            type="string",
            description="Sequence 10 research proposal",
            requires_revalidation=True,
            warning_text="Never auto-promotes to live.",
        )
        req = TuningChangeRequest(
            occurred_at=now,
            idempotency_key=key or f"studio:{uuid4()}",
            parameter=schema,
            new_value=new_value,
            status=TuningChangeStatus.PROPOSED,
            requested_by=actor,
            auto_promote_to_live=False,
        )
        existing = self._items.get(req.idempotency_key)
        if existing is not None:
            return existing
        self._items[req.idempotency_key] = req
        self._items[str(req.request_id)] = req
        return req

    def accept(self, request_id: str, *, actor: str) -> TuningChangeRequest | None:
        item = self._items.get(request_id)
        if item is None:
            return None
        if item.status is not TuningChangeStatus.PROPOSED:
            return item
        updated = item.model_copy(update={"status": TuningChangeStatus.ACCEPTED})
        self._items[request_id] = updated
        self._items[updated.idempotency_key] = updated
        return updated

    def reject(self, request_id: str) -> TuningChangeRequest | None:
        item = self._items.get(request_id)
        if item is None:
            return None
        updated = item.model_copy(update={"status": TuningChangeStatus.REJECTED})
        self._items[request_id] = updated
        return updated

    def open(self) -> tuple[TuningChangeRequest, ...]:
        return tuple(
            i
            for i in dict.fromkeys(self._items.values())
            if i.status in {TuningChangeStatus.DRAFT, TuningChangeStatus.PROPOSED, TuningChangeStatus.VALIDATING}
        )

    def snapshot(self) -> tuple[TuningChangeRequest, ...]:
        return tuple(dict.fromkeys(self._items.values()))

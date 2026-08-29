"""HITL approval queue. Approvals are not orders and cannot skip PM4."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from botmoduleproject1.contracts.v1.alerts import ApprovalRequest, ApprovalStatus
from botmoduleproject1.contracts.v1.time import UTC, ensure_aware_utc


class HitlQueue:
    def __init__(self, *, ttl_seconds: int = 900) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, ApprovalRequest] = {}

    def enqueue(self, request: ApprovalRequest) -> ApprovalRequest:
        key = str(request.request_id)
        existing = self._items.get(key)
        if existing is not None:
            return existing
        self._items[key] = request
        return request

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._items.get(request_id)

    def expire_due(self, now: datetime) -> list[ApprovalRequest]:
        now = ensure_aware_utc(now, "now")
        expired: list[ApprovalRequest] = []
        for key, item in list(self._items.items()):
            if item.status is not ApprovalStatus.PENDING:
                continue
            age = now - item.occurred_at
            if age >= timedelta(seconds=self.ttl_seconds):
                updated = item.model_copy(update={"status": ApprovalStatus.EXPIRED})
                self._items[key] = updated
                expired.append(updated)
        return expired

    def decide(
        self,
        request_id: str,
        *,
        approved: bool,
        actor: str,
        now: datetime,
    ) -> ApprovalRequest | None:
        item = self._items.get(request_id)
        if item is None:
            return None
        if item.status is ApprovalStatus.EXPIRED:
            return item
        if item.status is not ApprovalStatus.PENDING:
            return item
        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        updated = item.model_copy(
            update={
                "status": status,
                "note": f"{'approved' if approved else 'rejected'} by {actor}",
            }
        )
        self._items[request_id] = updated
        return updated

    def pending(self) -> tuple[ApprovalRequest, ...]:
        return tuple(i for i in self._items.values() if i.status is ApprovalStatus.PENDING)

    def snapshot(self) -> tuple[ApprovalRequest, ...]:
        return tuple(self._items.values())

    def open_intent_request(
        self,
        *,
        actor: str,
        now: datetime,
        intent_id: UUID | None = None,
        key: str | None = None,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            occurred_at=now,
            idempotency_key=key or f"hitl:{uuid4()}",
            intent_id=intent_id,
            requested_by=actor,
            note="operator_hitl",
        )
        return self.enqueue(request)

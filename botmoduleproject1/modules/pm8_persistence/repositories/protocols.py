"""Sequence 09 — 19 repository protocols. Implementations live in store.py."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EventRepository(Protocol):
    def append_event(self, row: dict[str, Any]) -> int: ...
    def get_event(self, event_id: str) -> dict[str, Any] | None: ...
    def list_events(self, limit: int = 100) -> list[dict[str, Any]]: ...
    def last_hash(self) -> str: ...
    def last_sequence(self) -> int: ...


@runtime_checkable
class SignalRepository(Protocol):
    def insert_signal(self, row: dict[str, Any]) -> None: ...
    def get_signal(self, signal_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class OrderRepository(Protocol):
    def insert_order(self, row: dict[str, Any]) -> None: ...
    def get_by_client_order_id(self, client_order_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class ExecutionRepository(Protocol):
    def insert_execution(self, row: dict[str, Any]) -> None: ...
    def get_by_callback(self, venue_callback_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class IdempotencyRepository(Protocol):
    def put_if_absent(self, edge: str, scope: str, key: str, result_ref: str, created_at: str) -> bool: ...
    def get(self, edge: str, scope: str, key: str) -> str | None: ...


@runtime_checkable
class OutboxRepository(Protocol):
    def enqueue(self, row: dict[str, Any]) -> None: ...
    def pending(self, limit: int = 50) -> list[dict[str, Any]]: ...
    def mark(self, outbox_id: str, state: str, published_at: str | None = None) -> None: ...


@runtime_checkable
class InboxRepository(Protocol):
    def accept(self, event_id: str, source: str, state: str, processed_at: str) -> bool: ...
    def seen(self, event_id: str) -> bool: ...


@runtime_checkable
class RecoveryRepository(Protocol):
    def save_checkpoint(self, row: dict[str, Any]) -> None: ...
    def latest_checkpoint(self) -> dict[str, Any] | None: ...


@runtime_checkable
class ProjectionRepository(Protocol):
    def upsert(self, name: str, last_event_seq: int, payload_json: str, rebuilt_at: str) -> None: ...
    def get(self, name: str) -> dict[str, Any] | None: ...


@runtime_checkable
class ReconciliationRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...
    def list_open(self) -> list[dict[str, Any]]: ...


@runtime_checkable
class AuditRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...


@runtime_checkable
class SnapshotRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...
    def latest(self) -> dict[str, Any] | None: ...


@runtime_checkable
class IntegrityLogRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...
    def latest(self) -> dict[str, Any] | None: ...


@runtime_checkable
class BackupManifestRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...
    def get(self, backup_id: str) -> dict[str, Any] | None: ...
    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]: ...


@runtime_checkable
class SchemaVersionRepository(Protocol):
    def current_version(self) -> int: ...
    def record(self, version: int, name: str, checksum: str, applied_at: str, direction: str) -> None: ...


@runtime_checkable
class UnitOfWork(Protocol):
    def begin(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@runtime_checkable
class RepairJournalRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...


@runtime_checkable
class ExportPackageRepository(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...
    def get(self, export_id: str) -> dict[str, Any] | None: ...


@runtime_checkable
class PositionProjectionRepository(Protocol):
    def upsert(self, symbol: str, qty: str, avg_px: str, as_of: str, source_seq: int) -> None: ...
    def get(self, symbol: str) -> dict[str, Any] | None: ...


PROTOCOL_CATALOG: tuple[str, ...] = (
    "EventRepository",
    "SignalRepository",
    "OrderRepository",
    "ExecutionRepository",
    "IdempotencyRepository",
    "OutboxRepository",
    "InboxRepository",
    "RecoveryRepository",
    "ProjectionRepository",
    "ReconciliationRepository",
    "AuditRepository",
    "SnapshotRepository",
    "IntegrityLogRepository",
    "BackupManifestRepository",
    "SchemaVersionRepository",
    "UnitOfWork",
    "RepairJournalRepository",
    "ExportPackageRepository",
    "PositionProjectionRepository",
)

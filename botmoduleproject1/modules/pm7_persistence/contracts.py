"""Typed Protocols for PM7 replaceable ports."""

from __future__ import annotations

from typing import Any, Protocol

from botmoduleproject1.contracts.v1.persistence import (
    BackupMetadata,
    CommittedJournalRecord,
    EvidenceBundle,
    ExportPackage,
    IngestResult,
    IntegrityReport,
    LedgerEvent,
    QueryResult,
    QuerySpec,
    ReconciliationPersistRecord,
    ReplayResult,
    RetentionStatus,
    SnapshotRecord,
)


class EventIngestionGateway(Protocol):
    def ingest(self, source: Any, **kwargs: Any) -> IngestResult: ...


class JournalWriter(Protocol):
    def append(self, event: LedgerEvent, *, now) -> IngestResult: ...
    def get(self, event_id) -> CommittedJournalRecord | None: ...


class ReconciliationStore(Protocol):
    def store(self, record: ReconciliationPersistRecord) -> ReconciliationPersistRecord: ...


class EvidenceStore(Protocol):
    def build(self, **kwargs: Any) -> EvidenceBundle: ...


class ReplayEngine(Protocol):
    def replay(self, **kwargs: Any) -> ReplayResult: ...


class SnapshotManager(Protocol):
    def capture(self, **kwargs: Any) -> SnapshotRecord: ...


class AnalyticsWarehouse(Protocol):
    def dataset(self, **kwargs: Any): ...


class IntegrityEngine(Protocol):
    def verify(self) -> IntegrityReport: ...


class RetentionManager(Protocol):
    def status(self, *, now) -> RetentionStatus: ...


class QueryEngine(Protocol):
    def execute(self, spec: QuerySpec) -> QueryResult: ...


class ExportPackager(Protocol):
    def pack(self, **kwargs: Any) -> ExportPackage: ...


class ReportingEngine(Protocol):
    def generate(self, **kwargs: Any): ...


class RecoveryMetadataStore(Protocol):
    def current(self, *, now) -> BackupMetadata: ...


class PublicationGateway(Protocol):
    def publish(self, **kwargs: Any): ...


class PersistenceHealthContributor(Protocol):
    def health_checks(self, kind): ...

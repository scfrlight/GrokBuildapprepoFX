"""PM7 persistence orchestrator. Append-only. Never an order. Never broker truth."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.execution import ExecutionPublicationBundle
from botmoduleproject1.contracts.v1.persistence import (
    ArchiveTier,
    BackupMetadata,
    EvidenceBundle,
    ExportPackage,
    IngestDisposition,
    IngestResult,
    IntegrityReport,
    IntegrityState,
    LedgerEvent,
    PersistenceMode,
    PersistencePublicationBundle,
    PersistenceTruthSource,
    QueryResult,
    QuerySpec,
    ReconciliationPersistRecord,
    ReconciliationPersistState,
    ReplayResult,
    ReplayScope,
    ReportKind,
    RetentionStatus,
    SnapshotRecord,
    SnapshotScope,
)
from botmoduleproject1.modules.pm7_persistence.capabilities import PM7_PERSISTENCE_METADATA
from botmoduleproject1.modules.pm7_persistence.config.schema import Pm7PersistenceConfig, config_from_settings
from botmoduleproject1.modules.pm7_persistence.evidence.builder import build_bundle
from botmoduleproject1.modules.pm7_persistence.evidence.registry import EvidenceRegistry
from botmoduleproject1.modules.pm7_persistence.export.packager import ExportService
from botmoduleproject1.modules.pm7_persistence.health import health_checks as pm7_health
from botmoduleproject1.modules.pm7_persistence.infrastructure.repositories.file_journal import FileJournal
from botmoduleproject1.modules.pm7_persistence.infrastructure.repositories.in_memory_journal import InMemoryJournal
from botmoduleproject1.modules.pm7_persistence.infrastructure.repositories.sqlite_journal import SqliteJournal
from botmoduleproject1.modules.pm7_persistence.intake.gateway import IntakeError, IntakeGateway
from botmoduleproject1.modules.pm7_persistence.intake.pm5_adapter import recon_from_execution
from botmoduleproject1.modules.pm7_persistence.integrity.verification import verify_chain
from botmoduleproject1.modules.pm7_persistence.journal.corrections import correction_event
from botmoduleproject1.modules.pm7_persistence.journal.writer import JournalService
from botmoduleproject1.modules.pm7_persistence.manifest import module_manifest
from botmoduleproject1.modules.pm7_persistence.publication.publisher import PublicationService
from botmoduleproject1.modules.pm7_persistence.query.engine import QueryService
from botmoduleproject1.modules.pm7_persistence.reconciliation.store import InMemoryReconciliationStore
from botmoduleproject1.modules.pm7_persistence.recovery.backup_metadata import RecoveryMetadataService
from botmoduleproject1.modules.pm7_persistence.reporting.generator import ReportingService
from botmoduleproject1.modules.pm7_persistence.replay.engine import ReplayEngine
from botmoduleproject1.modules.pm7_persistence.retention.manager import RetentionService
from botmoduleproject1.modules.pm7_persistence.snapshot.manager import SnapshotService


def _backend_for(config: Pm7PersistenceConfig):
    mode = config.mode
    path = Path(config.storage_path)
    if mode is PersistenceMode.FILE_BACKED:
        return FileJournal(path / "journal.jsonl")
    if mode in {PersistenceMode.SQLITE_LOCAL, PersistenceMode.DURABLE_CANDIDATE}:
        return SqliteJournal(path / "journal.sqlite")
    return InMemoryJournal()


class PM7PersistenceModule:
    """Registered as pm7_ledger when enable_pm7_persistence is on."""

    def __init__(
        self,
        config: Pm7PersistenceConfig,
        clock: Any,
        *,
        feature_enabled: bool = True,
        journal_enabled: bool = True,
        replay_enabled: bool = True,
        integrity_enabled: bool = True,
        retention_enabled: bool = True,
        reporting_enabled: bool = True,
    ) -> None:
        self.config = config
        self.clock = clock
        self.feature_enabled = feature_enabled
        self.journal_enabled = journal_enabled and feature_enabled
        self.replay_enabled = replay_enabled and feature_enabled
        self.integrity_enabled = integrity_enabled and feature_enabled
        self.retention_enabled = retention_enabled and feature_enabled
        self.reporting_enabled = reporting_enabled and feature_enabled
        self.gateway = IntakeGateway()
        self.backend = _backend_for(config)
        self.journal = JournalService(self.backend)
        self.recon = InMemoryReconciliationStore()
        self.evidence = EvidenceRegistry()
        self.snapshots = SnapshotService()
        self.replay_engine = ReplayEngine()
        self.queries = QueryService()
        self.exports = ExportService()
        self.reports = ReportingService()
        self.retention = RetentionService(
            simulate_archive=config.simulate_archive,
            allow_purge=config.allow_purge,
        )
        self.recovery = RecoveryMetadataService()
        self.publisher = PublicationService()
        self.quarantine: list[IngestResult] = []
        self.last_integrity = IntegrityState.UNKNOWN
        self._last_bundle: PersistencePublicationBundle | None = None
        self._reload_durable_sidecars()

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM7PersistenceModule:
        flags = getattr(settings, "feature_flags")
        cfg = config_from_settings(settings)
        return cls(
            cfg,
            clock,
            feature_enabled=bool(getattr(flags, "pm7_persistence", False)),
            journal_enabled=bool(getattr(flags, "pm7_journal", True)),
            replay_enabled=bool(getattr(flags, "pm7_replay", True)),
            integrity_enabled=bool(getattr(flags, "pm7_integrity", True)),
            retention_enabled=bool(getattr(flags, "pm7_retention", True)),
            reporting_enabled=bool(getattr(flags, "pm7_reporting", True)),
        )

    def metadata(self) -> ModuleMetadata:
        return PM7_PERSISTENCE_METADATA

    def _reload_durable_sidecars(self) -> None:
        loader = getattr(self.backend, "load_snapshots", None)
        if callable(loader):
            self.snapshots.items = list(loader())
        ev_loader = getattr(self.backend, "load_evidence", None)
        if callable(ev_loader):
            self.evidence.bundles = list(ev_loader())

    def _persist_snapshot(self, snap: SnapshotRecord) -> None:
        fn = getattr(self.backend, "persist_snapshot", None)
        if callable(fn):
            fn(snap)

    def _persist_evidence(self, bundle: EvidenceBundle) -> None:
        fn = getattr(self.backend, "persist_evidence", None)
        if callable(fn):
            fn(bundle)

    def manifest(self) -> dict:
        return module_manifest()

    def is_ready(self) -> bool:
        return bool(self.feature_enabled)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return pm7_health(
            kind,
            enabled=self.feature_enabled,
            ready=self.is_ready(),
            mode=self.config.operating_mode,
            integrity=self.last_integrity.value,
        )

    def ingest(self, source: Any) -> IngestResult:
        now = self.clock.now()
        if not self.feature_enabled:
            return IngestResult(disposition=IngestDisposition.FEATURE_DISABLED, reasons=("feature_disabled",))
        try:
            event = self.gateway.normalize(source, now=now)
        except IntakeError as exc:
            result = IngestResult(
                disposition=IngestDisposition.REJECTED,
                reasons=exc.reasons,
            )
            self.quarantine.append(result)
            self.evidence.note(f"{now.isoformat()} ingest rejected schema")
            return result
        blocked = self.gateway.validate(event, now=now, feature_enabled=self.feature_enabled)
        if blocked is not None:
            self.quarantine.append(blocked)
            self.evidence.note(f"{now.isoformat()} ingest {blocked.disposition.value}")
            return blocked
        if not self.journal_enabled:
            result = IngestResult(disposition=IngestDisposition.REJECTED, reasons=("journal_disabled",))
            self.quarantine.append(result)
            return result
        durable = self.config.claims_durable
        result = self.journal.append(event, now=now, durable=durable)
        self.evidence.note(f"{now.isoformat()} ingest {result.disposition.value} seq={result.sequence}")
        if result.disposition is IngestDisposition.CONTRADICTION_RECORDED:
            self.quarantine.append(result)
            self.last_integrity = IntegrityState.WARNING
        if result.disposition is IngestDisposition.COMMITTED and isinstance(source, ExecutionPublicationBundle):
            rec = recon_from_execution(source, now=now, source_event_id=event.event_id)
            if rec is not None:
                self.recon.store(rec)
        if event.incident_id:
            pass
        self._last_bundle = self._publish(now, result, event.truth_source)
        return result

    def correct(self, original_event_id: UUID, *, payload: dict, actor: str, reason: str) -> IngestResult:
        now = self.clock.now()
        original = self.journal.get(original_event_id)
        if original is None:
            return IngestResult(disposition=IngestDisposition.REJECTED, reasons=("original_missing",))
        event = correction_event(original.event, payload=payload, actor=actor, reason=reason, now=now)
        return self.journal.append(event, now=now, durable=self.config.claims_durable)

    def mutate(self, event_id: UUID, **kwargs) -> None:
        self.backend.mutate(event_id, **kwargs)

    def record_reconciliation(self, record: ReconciliationPersistRecord) -> ReconciliationPersistRecord:
        return self.recon.store(record)

    def build_evidence(self, *, entity_id: str | None = None, actor: str | None = None) -> EvidenceBundle:
        now = self.clock.now()
        report = self.verify_integrity()
        bundle = build_bundle(
            now=now,
            records=self.journal.records(),
            integrity=report.state,
            entity_id=entity_id,
            actor=actor,
        )
        self.evidence.bundles.append(bundle)
        self._persist_evidence(bundle)
        return bundle

    def replay(self, *, scope: ReplayScope = ReplayScope.SESSION, entity_id: str | None = None) -> ReplayResult:
        now = self.clock.now()
        records = self.journal.records()
        if entity_id:
            records = [
                r
                for r in records
                if entity_id in {r.event.order_id, r.event.incident_id, r.event.session_id, r.event.symbol}
            ]
        snap = self.snapshots.items[-1] if self.snapshots.items else None
        result = self.replay_engine.replay(
            records,
            now=now,
            scope=scope,
            snapshot=snap,
            enabled=self.replay_enabled,
        )
        persist = getattr(self.backend, "persist_snapshot", None)
        if callable(persist) and result is not None:
            # Replay sessions reuse snapshot sidecar as durable watermark only when a snapshot exists.
            pass
        return result

    def capture_snapshot(self, *, scope: SnapshotScope = SnapshotScope.SYSTEM) -> SnapshotRecord:
        now = self.clock.now()
        snap = self.snapshots.capture(now=now, records=self.journal.records(), scope=scope)
        self._persist_snapshot(snap)
        return snap

    def verify_integrity(self) -> IntegrityReport:
        now = self.clock.now()
        report = verify_chain(self.journal.records(), now=now)
        if not self.integrity_enabled:
            report = report.model_copy(update={"state": IntegrityState.UNKNOWN, "claim": "integrity_flag_off"})
        self.last_integrity = report.state
        return report

    def freeze(self, *, reason: str, actor: str = "operator") -> RetentionStatus:
        now = self.clock.now()
        if not self.retention_enabled:
            return self.retention.status(now=now)
        self.evidence.note(f"{now.isoformat()} freeze by {actor}: {reason}")
        return self.retention.freeze(reason=reason, now=now)

    def archive(self, *, tier: ArchiveTier) -> RetentionStatus:
        now = self.clock.now()
        return self.retention.transition(tier, now=now)

    def purge(self):
        now = self.clock.now()
        return self.retention.purge(now=now)

    def query(self, spec: QuerySpec) -> QueryResult:
        return self.queries.execute(spec, self.journal.records(), limit_cap=self.config.query_limit)

    def export_package(self, *, kind: str = "audit_request") -> ExportPackage:
        now = self.clock.now()
        integrity = self.verify_integrity()
        records = self.journal.records()
        truth = records[-1].event.truth_source if records else PersistenceTruthSource.UNKNOWN
        return self.exports.pack(now=now, kind=kind, records=records, integrity=integrity.state, truth=truth)

    def generate_report(self, kind: ReportKind = ReportKind.DAILY_OPERATIONS):
        now = self.clock.now()
        return self.reports.generate(
            now=now,
            kind=kind,
            records=self.journal.records(),
            recon=self.recon.all(),
            enabled=self.reporting_enabled,
        )

    def backup_metadata(self) -> BackupMetadata:
        now = self.clock.now()
        return self.recovery.current(now=now, records=self.journal.records())

    def request_restore(self):
        return self.recovery.request_restore()

    def get_journal_entry(self, event_id: UUID):
        return self.journal.get(event_id)

    def search_events(self, spec: QuerySpec) -> QueryResult:
        return self.query(spec)

    def get_order_history(self, order_id: str):
        return [r for r in self.journal.records() if r.event.order_id == order_id]

    def get_incident_evidence(self, incident_id: str) -> EvidenceBundle:
        now = self.clock.now()
        records = [r for r in self.journal.records() if r.event.incident_id == incident_id]
        return build_bundle(now=now, records=records, integrity=self.verify_integrity().state, entity_id=incident_id)

    def get_reconciliation_history(self, *, order_id: str | None = None):
        return self.recon.history(order_id=order_id)

    def publish(self) -> PersistencePublicationBundle:
        now = self.clock.now()
        last = self._last_bundle
        if last is not None:
            return self.publisher.publish(last)
        empty = IngestResult(disposition=IngestDisposition.DEGRADED, reasons=("no_ingest",))
        bundle = self._publish(now, empty, PersistenceTruthSource.UNKNOWN)
        return self.publisher.publish(bundle)

    def _publish(self, now, result: IngestResult, truth: PersistenceTruthSource) -> PersistencePublicationBundle:
        recon_state = self.recon.all()[-1].state if self.recon.all() else None
        bundle = PersistencePublicationBundle(
            occurred_at=now,
            mode=self.config.mode,
            journal_sequence=len(self.journal.records()),
            ingest=result,
            integrity=self.last_integrity,
            retention=self.retention.tier,
            reconciliation_state=recon_state,
            truth_source=truth,
            durable=False if self.config.mode is PersistenceMode.MEMORY else self.config.claims_durable,
        )
        self.publisher.publish(bundle)
        return bundle

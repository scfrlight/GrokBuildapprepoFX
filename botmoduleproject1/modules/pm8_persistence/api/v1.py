"""Versioned Persistence API v1 — the only downstream access path (Sequence 09)."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from botmoduleproject1.contracts.v1.journal import EventType, JournalEntry
from botmoduleproject1.contracts.v1.pm8_persistence import (
    ApiDisposition,
    ApiResult,
    BackupReport,
    IdempotencyEdge,
    IntegrityFinding,
    PersistenceApiVersion,
    RepairAction,
    TableFamily,
)
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore, new_id


SERVICE_CATALOG: tuple[str, ...] = (
    "EventIngestService",
    "SignalPersistService",
    "OrderPersistService",
    "ExecutionPersistService",
    "IdempotencyGuardService",
    "OutboxEnqueueService",
    "OutboxDispatchService",
    "InboxConsumeService",
    "ProjectionRebuildService",
    "ReconciliationPersistService",
    "AuditTrailService",
    "IntegrityCheckService",
    "RepairPolicyService",
    "BackupExportService",
    "SnapshotCaptureService",
    "RecoveryCheckpointService",
    "VersionedQueryService",
    "TransactionCoordinatorService",
    "DedupService",
    "PersistenceHealthService",
)


def _iso() -> str:
    return utc_now().isoformat()


class PersistenceApiV1:
    """CQRS-style facade. Repositories are private."""

    version = PersistenceApiVersion.V1

    def __init__(self, store: SqliteStore, *, enabled: bool = True, max_outbox_attempts: int = 3) -> None:
        self.store = store
        self.enabled = enabled
        self.max_outbox_attempts = max_outbox_attempts
        self._dispatched: list[dict[str, Any]] = []
        self.entries: list[JournalEntry] = []  # bootstrap compatibility

    # --- 18. TransactionCoordinatorService ---
    def in_transaction(self, fn):
        self.store.begin()
        try:
            result = fn()
            self.store.commit()
            return result
        except Exception:
            self.store.rollback()
            raise

    # --- 5. IdempotencyGuardService / 19. DedupService ---
    def _guard(self, edge: IdempotencyEdge, scope: str, key: str | None) -> str | None:
        if not key:
            return None
        existing = self.store.get(edge.value, scope, key)
        return existing

    def _remember(self, edge: IdempotencyEdge, scope: str, key: str | None, result_ref: str) -> bool:
        if not key:
            return True
        return self.store.put_if_absent(edge.value, scope, key, result_ref, _iso())

    # --- 1. EventIngestService + 6. OutboxEnqueueService (same UoW) ---
    def ingest_event(
        self,
        *,
        event_type: str,
        producer: str,
        family: TableFamily,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
        event_id: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        topic: str = "domain.events",
    ) -> ApiResult:
        if not self.enabled:
            return ApiResult(disposition=ApiDisposition.FEATURE_DISABLED, message="pm8_persistence off")
        eid = event_id or new_id()
        dup = self._guard(IdempotencyEdge.EVENT_CONSUMER, "event", eid)
        if dup:
            return ApiResult(
                disposition=ApiDisposition.DUPLICATE_IGNORED,
                duplicate_of=UUID(dup) if _is_uuid(dup) else None,
                message="duplicate event_id",
            )
        if idempotency_key:
            hit = self._guard(IdempotencyEdge.REQUEST, family.value, idempotency_key)
            if hit:
                return ApiResult(
                    disposition=ApiDisposition.DUPLICATE_IGNORED,
                    duplicate_of=UUID(hit) if _is_uuid(hit) else None,
                    message="duplicate request idempotency_key",
                )

        def _write() -> ApiResult:
            seq = self.store.append_event(
                {
                    "event_id": eid,
                    "correlation_id": correlation_id or new_id(),
                    "causation_id": causation_id,
                    "idempotency_key": idempotency_key,
                    "occurred_at": _iso(),
                    "event_type": event_type,
                    "producer": producer,
                    "family": family.value,
                    "payload_json": json.dumps(payload, sort_keys=True),
                }
            )
            self.store.enqueue(
                {
                    "outbox_id": new_id(),
                    "event_id": eid,
                    "topic": topic,
                    "payload_json": json.dumps(payload, sort_keys=True),
                    "state": "pending",
                    "created_at": _iso(),
                }
            )
            self._remember(IdempotencyEdge.EVENT_CONSUMER, "event", eid, eid)
            if idempotency_key:
                self._remember(IdempotencyEdge.REQUEST, family.value, idempotency_key, eid)
            return ApiResult(
                disposition=ApiDisposition.COMMITTED,
                record_id=UUID(eid),
                sequence_no=seq,
                message="committed with outbox",
            )

        return self.in_transaction(_write)

    # --- 2. SignalPersistService ---
    def persist_signal(self, symbol: str, payload: dict[str, Any], *, idempotency_key: str | None = None) -> ApiResult:
        result = self.ingest_event(
            event_type="signal.recorded",
            producer="pm8_persistence",
            family=TableFamily.SIGNAL,
            payload={"symbol": symbol, **payload},
            idempotency_key=idempotency_key,
        )
        if result.disposition is ApiDisposition.COMMITTED and result.record_id:
            self.store.insert_signal(
                {
                    "signal_id": new_id(),
                    "event_id": str(result.record_id),
                    "symbol": symbol,
                    "payload_json": json.dumps(payload, sort_keys=True),
                    "committed_at": _iso(),
                }
            )
        return result

    # --- 3. OrderPersistService ---
    def persist_order(
        self,
        client_order_id: str,
        payload: dict[str, Any],
        *,
        intent_id: str | None = None,
        verdict_id: str | None = None,
    ) -> ApiResult:
        existing = self.store.get_by_client_order_id(client_order_id)
        if existing:
            return ApiResult(
                disposition=ApiDisposition.DUPLICATE_IGNORED,
                message="duplicate client_order_id",
                details={"order_id": existing["order_id"]},
            )
        result = self.ingest_event(
            event_type="order.recorded",
            producer="pm8_persistence",
            family=TableFamily.ORDER,
            payload={"client_order_id": client_order_id, **payload},
            idempotency_key=client_order_id,
        )
        if result.disposition is ApiDisposition.COMMITTED:
            self.store.insert_order(
                {
                    "order_id": new_id(),
                    "client_order_id": client_order_id,
                    "intent_id": intent_id,
                    "verdict_id": verdict_id,
                    "state": payload.get("state", "accepted"),
                    "payload_json": json.dumps(payload, sort_keys=True),
                    "committed_at": _iso(),
                }
            )
        return result

    # --- 4. ExecutionPersistService ---
    def persist_execution(
        self,
        order_id: str,
        venue_kind: str,
        payload: dict[str, Any],
        *,
        venue_ticket: str | None = None,
        venue_callback_id: str | None = None,
    ) -> ApiResult:
        if venue_kind == "pm5_broker":
            return ApiResult(disposition=ApiDisposition.REJECTED, message="broker truth refused")
        if venue_callback_id:
            hit = self.store.get_by_callback(venue_callback_id)
            if hit:
                return ApiResult(
                    disposition=ApiDisposition.DUPLICATE_IGNORED,
                    message="duplicate broker callback",
                    details={"execution_id": hit["execution_id"]},
                )
            inserted = self._remember(
                IdempotencyEdge.BROKER_CALLBACK, "callback", venue_callback_id, venue_callback_id
            )
            if not inserted:
                return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="duplicate broker callback")
        result = self.ingest_event(
            event_type="execution.recorded",
            producer="pm8_persistence",
            family=TableFamily.EXECUTION,
            payload={"order_id": order_id, "venue_kind": venue_kind, "venue_ticket": venue_ticket, **payload},
            idempotency_key=venue_callback_id,
        )
        if result.disposition is ApiDisposition.COMMITTED:
            self.store.insert_execution(
                {
                    "execution_id": new_id(),
                    "order_id": order_id,
                    "venue_kind": venue_kind,
                    "venue_ticket": venue_ticket,
                    "venue_callback_id": venue_callback_id,
                    "payload_json": json.dumps(payload, sort_keys=True),
                    "committed_at": _iso(),
                }
            )
        return result

    # --- 7. OutboxDispatchService ---
    def dispatch_outbox(self, limit: int = 50) -> list[dict[str, Any]]:
        published: list[dict[str, Any]] = []
        for row in self.store.pending(limit):
            attempts = int(row["attempts"]) + 1
            if attempts > self.max_outbox_attempts:
                self.store.mark(row["outbox_id"], "quarantined")
                continue
            self.store.mark(row["outbox_id"], "published", _iso())
            item = dict(row)
            item["state"] = "published"
            published.append(item)
            self._dispatched.append(item)
        return published

    # --- 8. InboxConsumeService ---
    def consume_inbox(self, event_id: str, source: str, handler) -> ApiResult:
        if self.store.seen(event_id):
            return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="inbox already processed")
        accepted = self.store.accept(event_id, source, "processed", _iso())
        if not accepted:
            return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="inbox race duplicate")
        handler(event_id)
        return ApiResult(disposition=ApiDisposition.COMMITTED, message="inbox processed")

    # --- 9. ProjectionRebuildService ---
    def rebuild_projections(self) -> dict[str, Any]:
        events = self.store.list_events(limit=1_000_000)
        counts: dict[str, int] = {}
        last_seq = 0
        for ev in events:
            fam = ev["family"]
            counts[fam] = counts.get(fam, 0) + 1
            last_seq = int(ev["sequence_no"])
            key = f"proj:{fam}:{ev['sequence_no']}"
            self._remember(IdempotencyEdge.PROJECTION, fam, key, ev["event_id"])
        payload = json.dumps({"counts": counts, "last_seq": last_seq}, sort_keys=True)
        self.store.upsert("family_counts", last_seq, payload, _iso())
        return {"last_seq": last_seq, "counts": counts}

    def apply_projection_event(self, projection_name: str, source_seq: int, payload: dict[str, Any]) -> ApiResult:
        key = f"{projection_name}:{source_seq}"
        if self._guard(IdempotencyEdge.PROJECTION, projection_name, key):
            return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="projection already applied")
        self._remember(IdempotencyEdge.PROJECTION, projection_name, key, str(source_seq))
        current = self.store.get_projection(projection_name)
        merged = {}
        if current:
            merged = json.loads(current["payload_json"])
        merged.update(payload)
        self.store.upsert(projection_name, source_seq, json.dumps(merged, sort_keys=True), _iso())
        return ApiResult(disposition=ApiDisposition.COMMITTED, sequence_no=source_seq)

    # --- 10. ReconciliationPersistService ---
    def persist_reconciliation(
        self, local_ref: str, venue_ref: str | None, state: str, detail: dict[str, Any]
    ) -> ApiResult:
        if venue_ref is None and state == "pass":
            return ApiResult(disposition=ApiDisposition.REJECTED, message="silent pass without venue refused")
        if venue_ref is None and state not in {"degraded", "unavailable"}:
            state = "degraded"
            detail = {**detail, "reason": "no_venue_never_silent_pass"}
        self.store.insert(
            {
                "_table": "recon_records",
                "recon_id": new_id(),
                "local_ref": local_ref,
                "venue_ref": venue_ref,
                "state": state,
                "detail_json": json.dumps(detail, sort_keys=True),
                "committed_at": _iso(),
            }
        )
        return self.ingest_event(
            event_type="reconciliation.recorded",
            producer="pm8_persistence",
            family=TableFamily.RECONCILIATION,
            payload={"local_ref": local_ref, "venue_ref": venue_ref, "state": state},
        )

    # --- 11. AuditTrailService ---
    def audit(self, actor: str, action: str, target: str, payload: dict[str, Any] | None = None) -> None:
        redacted = _redact(payload or {})
        self.store.insert(
            {
                "_table": "audit_log",
                "audit_id": new_id(),
                "actor": actor,
                "action": action,
                "target": target,
                "payload_json": json.dumps(redacted, sort_keys=True),
                "occurred_at": _iso(),
            }
        )

    # --- 12. IntegrityCheckService ---
    def check_integrity(self) -> IntegrityFinding:
        events = self.store.list_events(limit=1_000_000)
        prev = "genesis"
        for ev in events:
            expected_prev = prev
            if ev["prev_hash"] != expected_prev:
                finding = IntegrityFinding(
                    state="compromised",
                    sequence_from=1,
                    sequence_to=int(ev["sequence_no"]),
                    mismatch_at=int(ev["sequence_no"]),
                    message="hash chain mismatch",
                )
                self._log_integrity(finding)
                return finding
            prev = ev["row_hash"]
        finding = IntegrityFinding(
            state="valid",
            sequence_from=1,
            sequence_to=self.store.last_sequence(),
            message="chain ok",
        )
        self._log_integrity(finding)
        return finding

    def _log_integrity(self, finding: IntegrityFinding) -> None:
        self.store.insert(
            {
                "_table": "integrity_log",
                "check_id": new_id(),
                "state": finding.state,
                "detail_json": finding.model_dump_json(),
                "occurred_at": _iso(),
            }
        )

    # --- 13. RepairPolicyService ---
    def repair(self, finding: IntegrityFinding) -> ApiResult:
        if finding.state != "compromised":
            return ApiResult(disposition=ApiDisposition.REJECTED, message="nothing to repair")
        # Never rewrite committed rows.
        correction = self.ingest_event(
            event_type="integrity.correction",
            producer="pm8_persistence",
            family=TableFamily.AUDIT,
            payload={"action": RepairAction.CORRECTION_EVENT.value, "mismatch_at": finding.mismatch_at},
        )
        self.store.insert(
            {
                "_table": "repair_log",
                "repair_id": new_id(),
                "check_id": None,
                "action": RepairAction.CORRECTION_EVENT.value,
                "new_event_id": str(correction.record_id) if correction.record_id else None,
                "detail_json": finding.model_dump_json(),
                "occurred_at": _iso(),
            }
        )
        return ApiResult(
            disposition=ApiDisposition.COMPROMISED,
            record_id=correction.record_id,
            message="correction recorded; chain not rewritten",
            details={"repair": RepairAction.CORRECTION_EVENT.value},
        )

    # --- 14. BackupExportService ---
    def backup(self, directory: Path) -> BackupReport:
        directory.mkdir(parents=True, exist_ok=True)
        blob = self.store.dump_events_json()
        checksum = sha256(blob.encode("utf-8")).hexdigest()
        backup_id = uuid4()
        path = directory / f"{backup_id}.json"
        path.write_text(blob, encoding="utf-8")
        verified = sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == checksum
        events = json.loads(blob)
        self.store.insert(
            {
                "_table": "backup_manifest",
                "backup_id": str(backup_id),
                "path": str(path),
                "checksum": checksum,
                "event_count": len(events),
                "verified": verified,
                "created_at": _iso(),
            }
        )
        return BackupReport(
            backup_id=backup_id,
            checksum=checksum,
            path=str(path),
            verified=verified,
            event_count=len(events),
            created_at=utc_now(),
        )

    def export_package(self) -> dict[str, Any]:
        blob = self.store.dump_events_json()
        checksum = sha256(blob.encode("utf-8")).hexdigest()
        export_id = new_id()
        self.store.insert(
            {
                "_table": "export_packages",
                "export_id": export_id,
                "checksum": checksum,
                "payload_json": blob,
                "created_at": _iso(),
            }
        )
        return {"export_id": export_id, "checksum": checksum}

    # --- 15. SnapshotCaptureService ---
    def snapshot(self, scope: str = "system") -> dict[str, Any]:
        blob = self.store.dump_events_json()
        checksum = sha256(blob.encode("utf-8")).hexdigest()
        snap_id = new_id()
        self.store.insert(
            {
                "_table": "snapshots",
                "snapshot_id": snap_id,
                "scope": scope,
                "checksum": checksum,
                "payload_json": blob,
                "created_at": _iso(),
            }
        )
        return {"snapshot_id": snap_id, "checksum": checksum}

    # --- 16. RecoveryCheckpointService ---
    def checkpoint(self) -> dict[str, Any]:
        row = {
            "checkpoint_id": new_id(),
            "cursor_seq": self.store.last_sequence(),
            "payload_json": json.dumps({"last_hash": self.store.last_hash()}),
            "created_at": _iso(),
        }
        self.store.save_checkpoint(row)
        return row

    def latest_checkpoint(self) -> dict[str, Any] | None:
        return self.store.latest_checkpoint()

    # --- 17. VersionedQueryService ---
    def query_events(self, *, limit: int = 50, actor: str, authorized: bool) -> list[dict[str, Any]]:
        if not authorized:
            raise PermissionError("query requires authorized=true")
        self.audit(actor, "query.events", "events", {"limit": limit})
        return self.store.list_events(limit=limit)

    # --- 20. PersistenceHealthService ---
    def health(self) -> dict[str, Any]:
        integrity = self.check_integrity()
        return {
            "api_version": self.version.value,
            "enabled": self.enabled,
            "mode": "sqlite",
            "schema_version": self.store.current_version(),
            "event_count": self.store.last_sequence(),
            "integrity": integrity.state,
            "outbox_pending": len(self.store.pending()),
            "mt5": False,
            "production_durable": False,
        }

    def append(self, entry: JournalEntry) -> None:
        """Bootstrap compatibility for dangerous-flag audit."""
        self.entries.append(entry)
        if self.enabled:
            self.ingest_event(
                event_type=str(entry.event_type),
                producer=entry.producer,
                family=TableFamily.AUDIT,
                payload={"summary": entry.summary, **(entry.attributes or {})},
            )

    def upsert_position(self, symbol: str, qty: str, avg_px: str, as_of: str, source_seq: int) -> None:
        self.store.upsert_position(symbol, qty, avg_px, as_of, source_seq)

    def get_position(self, symbol: str) -> dict[str, Any] | None:
        return self.store.get_position(symbol)


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except Exception:
        return False


_SECRET_KEYS = {"password", "token", "secret", "api_key", "apikey"}


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in _SECRET_KEYS or "token" in key.lower() or "password" in key.lower():
            out[key] = "[redacted]"
        else:
            out[key] = value
    return out

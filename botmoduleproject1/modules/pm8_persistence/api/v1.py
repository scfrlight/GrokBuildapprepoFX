"""Versioned Persistence API v1 — the only downstream access path (Sequence 09).

Remediation 2026-08-30: nested unit of work, Decimal money, outbox relay,
named projections, reconciliation runs, isolated restore-apply.
"""

from __future__ import annotations

import json
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from botmoduleproject1.contracts.v1.journal import JournalEntry
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
from botmoduleproject1.modules.pm8_persistence.money import (
    DEFAULT_SCALE,
    MONEY_FIELDS,
    MoneyError,
    canonical,
    sanitize_payload,
)
from botmoduleproject1.modules.pm8_persistence.outbox import InProcessPublisher, OutboxPublisher
from botmoduleproject1.modules.pm8_persistence.projections import CLOSED_ORDER_STATES, NAMED_PROJECTIONS
from botmoduleproject1.modules.pm8_persistence.reconciliation import (
    ALLOWED_TRANSITIONS,
    ReconciliationRunState,
)
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
    "OutboxRelayService",
    "NamedProjectionService",
    "ReconciliationRunService",
    "RestoreApplyService",
    "DecimalMoneyService",
)


class PersistenceApiError(ValueError):
    """Typed public error from PersistenceApiV1."""


class UnsupportedApiVersion(PersistenceApiError):
    pass


class SchemaMismatch(PersistenceApiError):
    pass


class IdempotencyConflict(PersistenceApiError):
    pass


def _iso() -> str:
    return utc_now().isoformat()


def _request_hash(payload: dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


class PersistenceApiV1:
    """CQRS-style facade. Repositories are private."""

    version = PersistenceApiVersion.V1
    SUPPORTED_VERSIONS = frozenset({PersistenceApiVersion.V1})

    def __init__(
        self,
        store: SqliteStore,
        *,
        enabled: bool = True,
        max_outbox_attempts: int = 3,
        publisher: OutboxPublisher | None = None,
    ) -> None:
        self.store = store
        self.enabled = enabled
        self.max_outbox_attempts = max_outbox_attempts
        self.publisher = publisher or InProcessPublisher()
        self._dispatched: list[dict[str, Any]] = []
        self.entries: list[JournalEntry] = []
        self.inject_fault: str | None = None

    def require_version(self, version: str) -> None:
        if version != PersistenceApiVersion.V1.value:
            raise UnsupportedApiVersion(f"unsupported API version {version}; supported=v1")

    def _fault(self, point: str) -> None:
        if self.inject_fault == point:
            raise RuntimeError(f"injected fault:{point}")

    def in_transaction(self, fn):
        nested = self.store._in_tx
        if not nested:
            self.store.begin()
        try:
            self._fault("before_mutation")
            result = fn()
            self._fault("before_commit")
            if not nested:
                self.store.commit()
            self._fault("after_commit")
            return result
        except Exception:
            if not nested:
                self.store.rollback()
            raise

    def _guard(self, edge: IdempotencyEdge, scope: str, key: str | None) -> str | None:
        if not key:
            return None
        existing = self.store.get(edge.value, scope, key)
        return existing

    def _remember(
        self,
        edge: IdempotencyEdge,
        scope: str,
        key: str | None,
        result_ref: str,
        request_hash: str = "",
    ) -> bool:
        if not key:
            return True
        existing = self.store.get_idempotency(edge.value, scope, key)
        if existing is not None:
            stored_hash = existing.get("request_hash") or ""
            if request_hash and stored_hash and stored_hash != request_hash:
                raise IdempotencyConflict("same idempotency key with different request hash")
            return False
        return self.store.put_if_absent(edge.value, scope, key, result_ref, _iso(), request_hash)

    def _append_event_and_outbox(
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
        request_hash: str = "",
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
            hit = self.store.get_idempotency(IdempotencyEdge.REQUEST.value, family.value, idempotency_key)
            if hit is not None:
                stored_hash = hit.get("request_hash") or ""
                if request_hash and stored_hash and stored_hash != request_hash:
                    raise IdempotencyConflict("same idempotency key with different request hash")
                return ApiResult(
                    disposition=ApiDisposition.DUPLICATE_IGNORED,
                    duplicate_of=UUID(hit["result_ref"]) if _is_uuid(str(hit["result_ref"])) else None,
                    message="duplicate request idempotency_key",
                )
        cid = correlation_id or new_id()
        self._fault("before_outbox")
        seq = self.store.append_event(
            {
                "event_id": eid,
                "correlation_id": cid,
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
                "aggregate_id": eid,
                "correlation_id": cid,
                "causation_id": causation_id,
                "payload_version": "v1",
            }
        )
        self._remember(IdempotencyEdge.EVENT_CONSUMER, "event", eid, eid)
        if idempotency_key:
            self._remember(IdempotencyEdge.REQUEST, family.value, idempotency_key, eid, request_hash)
        return ApiResult(
            disposition=ApiDisposition.COMMITTED,
            record_id=UUID(eid),
            sequence_no=seq,
            message="committed with outbox",
        )

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
        req_hash = _request_hash({"event_type": event_type, "payload": payload})
        return self.in_transaction(
            lambda: self._append_event_and_outbox(
                event_type=event_type,
                producer=producer,
                family=family,
                payload=payload,
                idempotency_key=idempotency_key,
                event_id=event_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                topic=topic,
                request_hash=req_hash,
            )
        )

    def persist_signal(self, symbol: str, payload: dict[str, Any], *, idempotency_key: str | None = None) -> ApiResult:
        clean = sanitize_payload(payload)

        def _write() -> ApiResult:
            result = self._append_event_and_outbox(
                event_type="signal.recorded",
                producer="pm8_persistence",
                family=TableFamily.SIGNAL,
                payload={"symbol": symbol, **clean},
                idempotency_key=idempotency_key,
                request_hash=_request_hash({"symbol": symbol, **clean}),
            )
            if result.disposition is ApiDisposition.COMMITTED and result.record_id:
                self._fault("before_audit")
                self.store.insert_signal(
                    {
                        "signal_id": new_id(),
                        "event_id": str(result.record_id),
                        "symbol": symbol,
                        "payload_json": json.dumps(clean, sort_keys=True),
                        "committed_at": _iso(),
                    }
                )
                self._record_money(TableFamily.SIGNAL.value, clean, str(result.record_id))
                self.audit("pm8", "signal.persist", symbol, {"event_id": str(result.record_id)})
            return result

        return self.in_transaction(_write)

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
        clean = sanitize_payload(payload)

        def _write() -> ApiResult:
            result = self._append_event_and_outbox(
                event_type="order.recorded",
                producer="pm8_persistence",
                family=TableFamily.ORDER,
                payload={"client_order_id": client_order_id, **clean},
                idempotency_key=client_order_id,
                request_hash=_request_hash({"client_order_id": client_order_id, **clean}),
            )
            if result.disposition is ApiDisposition.COMMITTED:
                self._fault("after_mutation")
                self.store.insert_order(
                    {
                        "order_id": new_id(),
                        "client_order_id": client_order_id,
                        "intent_id": intent_id,
                        "verdict_id": verdict_id,
                        "state": clean.get("state", "accepted"),
                        "payload_json": json.dumps(clean, sort_keys=True),
                        "committed_at": _iso(),
                    }
                )
                self._record_money(TableFamily.ORDER.value, clean, str(result.record_id) if result.record_id else None)
                self._fault("before_audit")
                self.audit("pm8", "order.persist", client_order_id, {"state": clean.get("state", "accepted")})
            return result

        return self.in_transaction(_write)

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
        clean = sanitize_payload(payload)

        def _write() -> ApiResult:
            if venue_callback_id:
                inserted = self._remember(
                    IdempotencyEdge.BROKER_CALLBACK, "callback", venue_callback_id, venue_callback_id
                )
                if not inserted:
                    return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="duplicate broker callback")
            result = self._append_event_and_outbox(
                event_type="execution.recorded",
                producer="pm8_persistence",
                family=TableFamily.EXECUTION,
                payload={"order_id": order_id, "venue_kind": venue_kind, "venue_ticket": venue_ticket, **clean},
                idempotency_key=venue_callback_id,
                request_hash=_request_hash({"order_id": order_id, "callback": venue_callback_id, **clean}),
            )
            if result.disposition is ApiDisposition.COMMITTED:
                self.store.insert_execution(
                    {
                        "execution_id": new_id(),
                        "order_id": order_id,
                        "venue_kind": venue_kind,
                        "venue_ticket": venue_ticket,
                        "venue_callback_id": venue_callback_id,
                        "payload_json": json.dumps(clean, sort_keys=True),
                        "committed_at": _iso(),
                    }
                )
                self._record_money(
                    TableFamily.EXECUTION.value, clean, str(result.record_id) if result.record_id else None
                )
                if "qty" in clean and "avg_px" in clean:
                    self.store.upsert_position(
                        order_id, clean["qty"], clean["avg_px"], _iso(), int(result.sequence_no or 0)
                    )
            return result

        return self.in_transaction(_write)

    def _record_money(self, family: str, payload: dict[str, Any], event_id: str | None) -> None:
        for field, value in payload.items():
            if field not in MONEY_FIELDS and not field.endswith("_pnl") and not field.endswith("_px"):
                continue
            if value is None:
                continue
            self.store.insert_money(
                {
                    "record_id": new_id(),
                    "family": family,
                    "field": field,
                    "amount_canonical": canonical(value, field=field),
                    "scale": DEFAULT_SCALE,
                    "currency": "QUOTE",
                    "source_event_id": event_id,
                    "committed_at": _iso(),
                }
            )

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

    def relay_outbox(
        self,
        *,
        limit: int = 50,
        worker: str = "local-worker",
        lease_seconds: int = 30,
        publisher: OutboxPublisher | None = None,
    ) -> list[dict[str, Any]]:
        """Claim → publish → published | retry | dead-letter. SQLite local/test-only."""
        pub = publisher or self.publisher
        now = utc_now()
        now_iso = now.isoformat()
        until = (now + timedelta(seconds=lease_seconds)).isoformat()
        handled: list[dict[str, Any]] = []
        for row in self.store.claimable_outbox(now_iso, limit):
            if not self.store.claim_outbox(row["outbox_id"], worker, until, now_iso):
                continue
            claimed = dict(row)
            claimed["state"] = "claimed"
            try:
                pub.publish(claimed)
                self.store.mark(row["outbox_id"], "published", now_iso)
                claimed["state"] = "published"
            except Exception as exc:
                attempts = int(row.get("attempts") or 0) + 1
                dead = attempts >= self.max_outbox_attempts
                nxt = (now + timedelta(seconds=min(60, 2 ** attempts))).isoformat()
                self.store.mark_outbox_failed(row["outbox_id"], str(exc), nxt, dead)
                claimed["state"] = "dead-letter" if dead else "failed"
                claimed["failure_reason"] = str(exc)
            handled.append(claimed)
            self._dispatched.append(claimed)
        return handled

    def consume_inbox(self, event_id: str, source: str, handler) -> ApiResult:
        existing = self.store.get_inbox(event_id)
        if existing and existing["state"] in {"processed", "duplicate"}:
            return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="inbox already processed")
        if existing is None:
            accepted = self.store.accept(event_id, source, "received", _iso())
            if not accepted:
                return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="inbox race duplicate")
        try:
            handler(event_id)
        except Exception as exc:
            self.store.mark_inbox(event_id, "failed", _iso(), str(exc))
            row = self.store.get_inbox(event_id) or {}
            attempts = int(row.get("attempts") or 1)
            if attempts >= self.max_outbox_attempts:
                self.store.insert_inbox_dead_letter(
                    {
                        "event_id": event_id,
                        "source": source,
                        "attempts": attempts,
                        "last_error": str(exc),
                        "payload_json": "{}",
                        "created_at": _iso(),
                    }
                )
                self.store.mark_inbox(event_id, "dead-letter", _iso(), str(exc))
                return ApiResult(disposition=ApiDisposition.QUARANTINED, message="inbox dead-letter")
            return ApiResult(disposition=ApiDisposition.REJECTED, message="inbox handler failed; retryable")
        self.store.mark_inbox(event_id, "processed", _iso(), None)
        return ApiResult(disposition=ApiDisposition.COMMITTED, message="inbox processed")

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
        named = self.rebuild_named_projections()
        return {"last_seq": last_seq, "counts": counts, "named": named}

    def apply_projection_event(self, projection_name: str, source_seq: int, payload: dict[str, Any]) -> ApiResult:
        key = f"{projection_name}:{source_seq}"
        if self._guard(IdempotencyEdge.PROJECTION, projection_name, key):
            return ApiResult(disposition=ApiDisposition.DUPLICATE_IGNORED, message="projection already applied")
        self._remember(IdempotencyEdge.PROJECTION, projection_name, key, str(source_seq))
        current = self.store.get_projection(projection_name)
        merged: dict[str, Any] = {}
        if current:
            merged = json.loads(current["payload_json"])
        merged.update(payload)
        self.store.upsert(projection_name, source_seq, json.dumps(merged, sort_keys=True), _iso())
        return ApiResult(disposition=ApiDisposition.COMMITTED, sequence_no=source_seq)

    def rebuild_named_projections(self) -> dict[str, Any]:
        for name in NAMED_PROJECTIONS:
            self.store.clear_named_projection(name)
        events = self.store.list_events(limit=1_000_000)
        last_seq = 0
        for ev in events:
            last_seq = int(ev["sequence_no"])
            self._apply_named_from_event(ev, rebuild=True)
        now = _iso()
        lag = 0
        status: dict[str, Any] = {}
        for name in NAMED_PROJECTIONS:
            rows = self.store.list_named_rows(name)
            self.store.set_named_meta(name, 1, last_seq, now, "ready", lag)
            status[name] = {"rows": len(rows), "last_event_seq": last_seq, "status": "ready", "lag_seq": lag}
        return status

    def named_projection_status(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        tip = self.store.last_sequence()
        for name in NAMED_PROJECTIONS:
            meta = self.store.get_named_meta(name)
            rows = self.store.list_named_rows(name)
            last = int(meta["last_event_seq"]) if meta else 0
            out[name] = {
                "rows": len(rows),
                "last_event_seq": last,
                "lag_seq": max(tip - last, 0),
                "status": (meta or {}).get("status", "absent"),
                "version": (meta or {}).get("version", 0),
            }
        return out

    def get_named_projection(self, name: str) -> list[dict[str, Any]]:
        if name not in NAMED_PROJECTIONS:
            raise PersistenceApiError(f"unknown named projection {name}")
        return self.store.list_named_rows(name)

    def _apply_named_from_event(self, ev: dict[str, Any], *, rebuild: bool) -> None:
        eid = ev["event_id"]
        seq = int(ev["sequence_no"])
        family = ev["family"]
        payload = json.loads(ev["payload_json"]) if isinstance(ev["payload_json"], str) else ev["payload_json"]
        occurred = ev.get("occurred_at") or _iso()
        day = str(occurred)[:10]
        now = _iso()

        def mark(name: str) -> bool:
            if rebuild:
                return True
            return self.store.mark_processed_event(name, eid, seq, now)

        if family == TableFamily.ORDER.value:
            key = str(payload.get("client_order_id") or eid)
            state = str(payload.get("state") or "accepted")
            blob = json.dumps({**payload, "event_id": eid, "state": state}, sort_keys=True)
            if state.lower() in CLOSED_ORDER_STATES:
                if mark("closed_trades"):
                    self.store.upsert_named_row("closed_trades", key, blob, seq, now)
                if mark("open_orders"):
                    self.store.delete_named_row("open_orders", key)
            else:
                if mark("open_orders"):
                    self.store.upsert_named_row("open_orders", key, blob, seq, now)
        if family == TableFamily.EXECUTION.value:
            symbol = str(payload.get("symbol") or payload.get("order_id") or "UNKNOWN")
            qty = payload.get("qty") or payload.get("quantity") or payload.get("fill_qty")
            px = payload.get("avg_px") or payload.get("price") or payload.get("fill_price")
            if qty is not None and px is not None:
                try:
                    q = canonical(qty, field="qty")
                    p = canonical(px, field="avg_px")
                    if mark("open_positions"):
                        self.store.upsert_named_row(
                            "open_positions",
                            symbol,
                            json.dumps({"symbol": symbol, "qty": q, "avg_px": p}, sort_keys=True),
                            seq,
                            now,
                        )
                    self.store.upsert_position(symbol, q, p, now, seq)
                except MoneyError:
                    pass
            if mark("symbol_performance"):
                self.store.upsert_named_row(
                    "symbol_performance",
                    symbol,
                    json.dumps({"symbol": symbol, "last_event": eid, "seq": seq}, sort_keys=True),
                    seq,
                    now,
                )
        if family == TableFamily.SIGNAL.value:
            symbol = str(payload.get("symbol") or "UNKNOWN")
            if mark("strategy_memory"):
                self.store.upsert_named_row(
                    "strategy_memory",
                    symbol,
                    json.dumps({"symbol": symbol, "payload": payload, "event_id": eid}, sort_keys=True),
                    seq,
                    now,
                )
        if family == TableFamily.RECONCILIATION.value:
            state = str(payload.get("state") or "")
            if state not in {"pass", "matched"}:
                if mark("reconciliation_alerts"):
                    self.store.upsert_named_row(
                        "reconciliation_alerts",
                        eid,
                        json.dumps(payload, sort_keys=True),
                        seq,
                        now,
                    )
        if family == TableFamily.AUDIT.value:
            if mark("operator_dashboard"):
                self.store.upsert_named_row(
                    "operator_dashboard",
                    "latest",
                    json.dumps({"last_audit_event": eid, "seq": seq}, sort_keys=True),
                    seq,
                    now,
                )
        if ev.get("event_type") == "integrity.correction":
            if mark("anomaly_summary"):
                self.store.upsert_named_row(
                    "anomaly_summary",
                    eid,
                    json.dumps({"event_id": eid, "type": ev.get("event_type")}, sort_keys=True),
                    seq,
                    now,
                )
        producer = ev.get("producer") or "unknown"
        if mark("profile_performance"):
            self.store.upsert_named_row(
                "profile_performance",
                producer,
                json.dumps({"producer": producer, "last_seq": seq}, sort_keys=True),
                seq,
                now,
            )
        if mark("daily_summary"):
            self.store.upsert_named_row(
                "daily_summary",
                day,
                json.dumps({"day": day, "last_seq": seq}, sort_keys=True),
                seq,
                now,
            )

    def persist_reconciliation(
        self, local_ref: str, venue_ref: str | None, state: str, detail: dict[str, Any]
    ) -> ApiResult:
        if venue_ref is None and state == "pass":
            return ApiResult(disposition=ApiDisposition.REJECTED, message="silent pass without venue refused")
        if venue_ref is None and state not in {"degraded", "unavailable"}:
            state = "degraded"
            detail = {**detail, "reason": "no_venue_never_silent_pass"}

        def _write() -> ApiResult:
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
            return self._append_event_and_outbox(
                event_type="reconciliation.recorded",
                producer="pm8_persistence",
                family=TableFamily.RECONCILIATION,
                payload={"local_ref": local_ref, "venue_ref": venue_ref, "state": state},
            )

        return self.in_transaction(_write)

    def start_reconciliation_run(self, *, venue_available: bool, actor: str = "system") -> dict[str, Any]:
        run_id = new_id()
        now = _iso()

        def _write() -> dict[str, Any]:
            self.store.insert_recon_run(
                {
                    "run_id": run_id,
                    "state": ReconciliationRunState.STARTED.value,
                    "venue_available": venue_available,
                    "started_at": now,
                    "updated_at": now,
                    "payload_json": json.dumps({"actor": actor}, sort_keys=True),
                }
            )
            self._append_event_and_outbox(
                event_type="reconciliation.run.started",
                producer="pm8_persistence",
                family=TableFamily.RECONCILIATION,
                payload={"run_id": run_id, "venue_available": venue_available},
            )
            self.audit(actor, "recon.run.start", run_id, {"venue_available": venue_available})
            return {"run_id": run_id, "state": ReconciliationRunState.STARTED.value, "venue_available": venue_available}

        return self.in_transaction(_write)

    def add_reconciliation_item(
        self,
        run_id: str,
        *,
        local_ref: str,
        venue_ref: str | None,
        classification: str,
        severity: str = "medium",
    ) -> dict[str, Any]:
        run = self.store.get_recon_run(run_id)
        if run is None:
            raise PersistenceApiError("item cannot exist without parent run")
        if classification.lower() == "pass" and not run["venue_available"] and venue_ref is None:
            raise PersistenceApiError("unavailable venue cannot produce PASS")
        for item in self.store.list_recon_items(run_id):
            if item["local_ref"] == local_ref and item.get("venue_ref") == venue_ref:
                return {"item_id": item["item_id"], "duplicate": True, "state": item["state"]}
        item_id = new_id()
        now = _iso()
        mismatch = classification.lower() in {"mismatch", "critical"}

        def _write() -> dict[str, Any]:
            self.store.insert_recon_item(
                {
                    "item_id": item_id,
                    "run_id": run_id,
                    "local_ref": local_ref,
                    "venue_ref": venue_ref,
                    "classification": classification,
                    "severity": severity,
                    "state": "open",
                    "payload_json": "{}",
                    "created_at": now,
                }
            )
            nxt = ReconciliationRunState.COLLECTING
            if mismatch:
                nxt = ReconciliationRunState.MISMATCH_FOUND
            self._transition_run(run_id, nxt, now)
            self._append_event_and_outbox(
                event_type="reconciliation.item.added",
                producer="pm8_persistence",
                family=TableFamily.RECONCILIATION,
                payload={"run_id": run_id, "item_id": item_id, "classification": classification},
            )
            return {"item_id": item_id, "run_id": run_id, "classification": classification, "duplicate": False}

        return self.in_transaction(_write)

    def acknowledge_reconciliation(self, run_id: str, *, actor: str, item_id: str) -> dict[str, Any]:
        now = _iso()

        def _write() -> dict[str, Any]:
            self._transition_run(run_id, ReconciliationRunState.ACKNOWLEDGED, now)
            self.store.insert_mismatch_action(
                {
                    "action_id": new_id(),
                    "item_id": item_id,
                    "run_id": run_id,
                    "action": "acknowledge",
                    "actor": actor,
                    "occurred_at": now,
                    "payload_json": "{}",
                }
            )
            self.audit(actor, "recon.acknowledge", run_id, {"item_id": item_id})
            return {"run_id": run_id, "state": ReconciliationRunState.ACKNOWLEDGED.value}

        return self.in_transaction(_write)

    def remediate_reconciliation(self, run_id: str, *, actor: str, item_id: str, correction: dict[str, Any]) -> dict[str, Any]:
        now = _iso()

        def _write() -> dict[str, Any]:
            self._transition_run(run_id, ReconciliationRunState.REMEDIATION_IN_PROGRESS, now)
            self.store.insert_mismatch_action(
                {
                    "action_id": new_id(),
                    "item_id": item_id,
                    "run_id": run_id,
                    "action": "remediate",
                    "actor": actor,
                    "occurred_at": now,
                    "payload_json": json.dumps(correction, sort_keys=True),
                }
            )
            self._append_event_and_outbox(
                event_type="reconciliation.correction",
                producer="pm8_persistence",
                family=TableFamily.RECONCILIATION,
                payload={"run_id": run_id, "item_id": item_id, "correction": correction},
            )
            return {"run_id": run_id, "state": ReconciliationRunState.REMEDIATION_IN_PROGRESS.value}

        return self.in_transaction(_write)

    def resolve_reconciliation(self, run_id: str, *, actor: str) -> dict[str, Any]:
        run = self.store.get_recon_run(run_id)
        if run is None:
            raise PersistenceApiError("run missing")
        now = _iso()
        self._transition_run(run_id, ReconciliationRunState.RESOLVED, now)
        self.audit(actor, "recon.resolve", run_id, {})
        return {"run_id": run_id, "state": ReconciliationRunState.RESOLVED.value}

    def close_reconciliation(self, run_id: str, *, actor: str, failed: bool = False) -> dict[str, Any]:
        now = _iso()
        if failed:
            self._transition_run(run_id, ReconciliationRunState.FAILED, now)
        self._transition_run(run_id, ReconciliationRunState.CLOSED, now, closed_at=now)
        self.audit(actor, "recon.close", run_id, {"failed": failed})
        return {"run_id": run_id, "state": ReconciliationRunState.CLOSED.value}

    def reject_reconciliation(self, run_id: str, *, actor: str) -> dict[str, Any]:
        now = _iso()
        self._transition_run(run_id, ReconciliationRunState.REJECTED, now)
        self.audit(actor, "recon.reject", run_id, {})
        return {"run_id": run_id, "state": ReconciliationRunState.REJECTED.value}

    def _transition_run(
        self, run_id: str, target: ReconciliationRunState, now: str, closed_at: str | None = None
    ) -> None:
        run = self.store.get_recon_run(run_id)
        if run is None:
            raise PersistenceApiError("run missing")
        current = ReconciliationRunState(run["state"])
        if current is target:
            return
        allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            raise PersistenceApiError(f"illegal recon transition {current.value} -> {target.value}")
        self.store.update_recon_run(run_id, target.value, now, closed_at)

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

    def repair(self, finding: IntegrityFinding) -> ApiResult:
        if finding.state != "compromised":
            return ApiResult(disposition=ApiDisposition.REJECTED, message="nothing to repair")
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

    def query_events(self, *, limit: int = 50, actor: str, authorized: bool) -> list[dict[str, Any]]:
        if not authorized:
            raise PermissionError("query requires authorized=true")
        self.audit(actor, "query.events", "events", {"limit": limit})
        return self.store.list_events(limit=limit)

    def health(self) -> dict[str, Any]:
        integrity = self.check_integrity()
        diag = self.store.diagnostics()
        return {
            "api_version": self.version.value,
            "enabled": self.enabled,
            "mode": diag["backend"],
            "path": diag["path"],
            "schema_version": self.store.current_version(),
            "event_count": self.store.last_sequence(),
            "integrity": integrity.state,
            "outbox_pending": len(self.store.pending()),
            "mt5": False,
            "production_durable": False,
            "trading_readiness": False,
        }

    def append(self, entry: JournalEntry) -> None:
        self.entries.append(entry)
        if self.enabled:
            self.ingest_event(
                event_type=str(entry.event_type),
                producer=entry.producer,
                family=TableFamily.AUDIT,
                payload={"summary": entry.summary, **(entry.attributes or {})},
            )

    def upsert_position(self, symbol: str, qty: str, avg_px: str, as_of: str, source_seq: int) -> None:
        q = canonical(qty, field="qty")
        p = canonical(avg_px, field="avg_px")
        self.store.upsert_position(symbol, q, p, as_of, source_seq)

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

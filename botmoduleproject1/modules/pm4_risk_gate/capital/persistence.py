"""PM8 PersistenceApiV1 adapter. No second database."""

from __future__ import annotations

import json
from typing import Any

from botmoduleproject1.contracts.v1.pm4_capital import CapitalEvaluationResult
from botmoduleproject1.contracts.v1.pm8_persistence import ApiDisposition, TableFamily
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.pm4_risk_gate.capital.hashing import canonical_hash
from botmoduleproject1.modules.pm8_persistence.api.v1 import IdempotencyConflict


class CapitalPersistence:
    def __init__(self, api: Any | None) -> None:
        self.api = api

    def lookup(self, idempotency_key: str, input_hash: str) -> CapitalEvaluationResult | None:
        if self.api is None:
            return None
        existing = self.api.store.get_idempotency("request", "pm4_capital", idempotency_key)
        if existing is None:
            return None
        stored_hash = existing.get("request_hash") or ""
        if stored_hash and stored_hash != input_hash:
            raise ValueError("idempotency conflict: same key with different payload")
        events = self.api.store.list_events(limit=10_000)
        for ev in reversed(events):
            if ev.get("event_type") != "risk.decision.committed":
                continue
            raw = ev.get("payload_json") or "{}"
            payload = json.loads(raw) if isinstance(raw, str) else raw
            if payload.get("idempotency_key") != idempotency_key:
                continue
            dumped = payload.get("result")
            if dumped:
                return CapitalEvaluationResult.model_validate(dumped)
        return None

    def commit(
        self,
        *,
        request: Any,
        decision_id: str,
        input_hash: str,
        output_hash: str,
        payload: dict[str, Any],
        result: CapitalEvaluationResult | None = None,
    ) -> str:
        if self.api is None:
            return f"memory:{decision_id}"
        stored = None
        if result is not None:
            stored = result.model_dump(mode="json")
        try:
            ingest = self.api.ingest_event(
                event_type="risk.decision.committed",
                producer="pm4_risk_gate",
                family=TableFamily.AUDIT,
                payload={
                    "decision_id": decision_id,
                    "input_hash": input_hash,
                    "output_hash": output_hash,
                    "idempotency_key": request.idempotency_key,
                    "symbol": request.symbol,
                    "qty": str(payload.get("approved_quantity")),
                    "price": str(request.entry_price),
                    "risk_amount": str(payload.get("projected_risk")),
                    "state": payload.get("state"),
                    "result": stored,
                },
                idempotency_key=request.idempotency_key,
            )
        except IdempotencyConflict as exc:
            raise ValueError("idempotency conflict: same key with different payload") from exc
        if ingest.disposition not in {ApiDisposition.COMMITTED, ApiDisposition.DUPLICATE_IGNORED}:
            raise RuntimeError(f"persistence did not commit: {ingest.disposition}")
        self.api.store.put_if_absent(
            "request",
            "pm4_capital",
            request.idempotency_key,
            decision_id,
            utc_now().isoformat(),
            request_hash=input_hash,
        )
        if ingest.disposition is ApiDisposition.COMMITTED and ingest.record_id and hasattr(self.api, "_record_money"):
            money = {
                "qty": str(payload.get("approved_quantity") or "0"),
                "price": str(request.entry_price),
                "risk_amount": str(payload.get("projected_risk") or "0"),
            }

            def _write_money() -> bool:
                self.api._record_money(TableFamily.AUDIT.value, money, str(ingest.record_id))
                return True

            self.api.in_transaction(_write_money)
        return str(ingest.record_id or decision_id)

    def divergence(self, decision_id: str, original: str, replayed: str) -> None:
        if self.api is None:
            return
        self.api.ingest_event(
            event_type="risk.replay.divergence",
            producer="pm4_risk_gate",
            family=TableFamily.AUDIT,
            payload={
                "decision_id": decision_id,
                "original_hash": original,
                "replay_hash": replayed,
                "action": "do_not_overwrite",
            },
            idempotency_key=f"divergence:{decision_id}:{canonical_hash(replayed)}",
        )

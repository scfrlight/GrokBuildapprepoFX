from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from botmoduleproject1.contracts.v1.persistence import JournalCategory, LedgerEvent, PersistenceTruthSource


def classify_truth(event: LedgerEvent) -> LedgerEvent:
    ticket = event.ticket or str(event.event_payload.get("ticket") or event.event_payload.get("broker_ticket") or "")
    if ticket.startswith("SIM-"):
        return event.model_copy(update={"truth_source": PersistenceTruthSource.PM5_SIMULATION, "ticket": ticket})
    return event


def from_mapping(payload: dict, *, now: datetime) -> LedgerEvent:
    data = dict(payload)
    data.setdefault("event_timestamp", now)
    data.setdefault("ingested_at", now)
    data.setdefault("source_timestamp", data.get("event_timestamp"))
    data.setdefault("source_module", "operator")
    data.setdefault("event_type", "operator_action")
    if "category" in data and isinstance(data["category"], str):
        data["category"] = JournalCategory(data["category"])
    if "truth_source" in data and isinstance(data["truth_source"], str):
        data["truth_source"] = PersistenceTruthSource(data["truth_source"])
    return classify_truth(LedgerEvent.model_validate(data))

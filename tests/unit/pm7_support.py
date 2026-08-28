"""Shared fixtures for PM7 persistence tests."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import (
    JournalCategory,
    LedgerEvent,
    PersistenceTruthSource,
)
from botmoduleproject1.modules.pm7_persistence.config.schema import Pm7PersistenceConfig
from botmoduleproject1.modules.pm7_persistence.module import PM7PersistenceModule
from tests.unit.pm4_support import AS_OF
from tests.unit.pm5_support import Clock, ingest_allow


def pm7_module(*, clock: Clock | None = None, config: Pm7PersistenceConfig | None = None, **kwargs) -> PM7PersistenceModule:
    return PM7PersistenceModule(
        config or Pm7PersistenceConfig(),
        clock or Clock(),
        feature_enabled=kwargs.get("feature_enabled", True),
        journal_enabled=kwargs.get("journal_enabled", True),
        replay_enabled=kwargs.get("replay_enabled", True),
        integrity_enabled=kwargs.get("integrity_enabled", True),
        retention_enabled=kwargs.get("retention_enabled", True),
        reporting_enabled=kwargs.get("reporting_enabled", True),
    )


def make_event(**kwargs) -> LedgerEvent:
    now = kwargs.pop("now", AS_OF)
    payload = {
        "source_module": kwargs.pop("source_module", "pm5_execution"),
        "event_type": kwargs.pop("event_type", "order_lifecycle"),
        "event_timestamp": now,
        "ingested_at": now,
        "source_timestamp": now,
        "event_payload": kwargs.pop("event_payload", {"ok": True}),
        "truth_source": kwargs.pop("truth_source", PersistenceTruthSource.PM5_SIMULATION),
        "category": kwargs.pop("category", JournalCategory.ORDER_LIFECYCLE),
        "ticket": kwargs.pop("ticket", "SIM-000001"),
        "symbol": kwargs.pop("symbol", "EURUSD"),
        "order_id": kwargs.pop("order_id", "ord-1"),
    }
    payload.update(kwargs)
    return LedgerEvent.model_validate(payload)


def ingest_sim(module: PM7PersistenceModule | None = None, key: str = "pm7-ok"):
    pm7 = module or pm7_module()
    _exe, bundle, pub = ingest_allow(key=key)
    result = pm7.ingest(pub)
    return pm7, bundle, pub, result

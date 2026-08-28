import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.persistence import (
    LedgerEvent,
    PersistencePublicationBundle,
    PersistenceTruthSource,
    ReconciliationPersistRecord,
    ReconciliationPersistState,
)
from tests.unit.pm4_support import AS_OF


def test_sim_cannot_be_broker():
    with pytest.raises(ValidationError):
        LedgerEvent.model_validate(
            {
                "source_module": "pm5_execution",
                "event_type": "fill",
                "event_timestamp": AS_OF,
                "ticket": "SIM-1",
                "truth_source": PersistenceTruthSource.PM5_BROKER,
            }
        )


def test_recon_without_venue_cannot_pass():
    with pytest.raises(ValidationError):
        ReconciliationPersistRecord.model_validate(
            {
                "occurred_at": AS_OF,
                "state": ReconciliationPersistState.PASS,
                "broker_truth_available": False,
            }
        )


def test_publication_refuses_production_durable():
    with pytest.raises(ValidationError):
        PersistencePublicationBundle.model_validate(
            {"occurred_at": AS_OF, "mode": "production_durable"}
        )


def test_memory_cannot_claim_durable():
    with pytest.raises(ValidationError):
        PersistencePublicationBundle.model_validate(
            {"occurred_at": AS_OF, "mode": "memory", "durable": True}
        )

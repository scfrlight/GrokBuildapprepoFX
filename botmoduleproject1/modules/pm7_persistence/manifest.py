from botmoduleproject1.modules.pm7_persistence.capabilities import PM7_PERSISTENCE_METADATA


def module_manifest() -> dict:
    meta = PM7_PERSISTENCE_METADATA
    return {
        "name": meta.name,
        "version": meta.version,
        "role": "persistence_journal_evidence",
        "depends_on": list(meta.dependencies),
        "accepts": [
            "RiskPublicationBundle",
            "ExecutionPublicationBundle",
            "OperationalTruthBundle",
            "LedgerEvent",
        ],
        "does_not": [
            "orders",
            "mt5",
            "bypass_pm4",
            "bypass_pm5",
            "bypass_pm6",
            "fabricate_broker_truth",
            "mutate_committed_records",
            "production_durable",
            "telegram",
        ],
        "capabilities": [
            "durable_journal",
            "evidence_store",
            "reconciliation_store",
            "replay",
            "snapshots",
            "integrity_verification",
            "retention_archival",
            "audit_queries",
            "report_generation",
            "export_packaging",
        ],
        "truth": "simulation_or_degraded",
        "durable": False,
        "persistence_handoff": "pending_pm8",
    }

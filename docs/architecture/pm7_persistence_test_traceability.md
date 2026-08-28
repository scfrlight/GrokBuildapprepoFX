# PM7 Persistence — Test Traceability (Sequence 09)

| Invariant / Requirement | Test file | Test name | Result |
|---|---|---|---|
| append valid event | `tests/unit/test_pm7_journal.py` | `test_append_valid_event` | PASS |
| immutable committed event | `tests/unit/test_pm7_journal.py` | `test_immutable_committed_event` | PASS |
| ordering / hash chain | `tests/unit/test_pm7_journal.py` | `test_ordering` | PASS |
| duplicate idempotency | `tests/unit/test_pm7_journal.py` | `test_duplicate_idempotency` | PASS |
| duplicate payload conflict | `tests/unit/test_pm7_journal.py` | `test_duplicate_payload_conflict` | PASS |
| correction instead of mutation | `tests/unit/test_pm7_journal.py` | `test_correction_instead_of_mutation` | PASS |
| causal lineage | `tests/unit/test_pm7_journal.py` | `test_causal_lineage` | PASS |
| schema validation | `tests/unit/test_pm7_journal.py` | `test_schema_version_validation` | PASS |
| quarantine malformed | `tests/unit/test_pm7_journal.py` | `test_quarantine_malformed_source` | PASS |
| source module validation | `tests/unit/test_pm7_journal.py` | `test_source_module_validation` | PASS |
| SIM-* is simulation | `tests/unit/test_pm7_truth.py` | `test_sim_ticket_stored_as_simulation` | PASS |
| SIM labelled broker rejected | `tests/unit/test_pm7_truth.py` | `test_sim_labelled_broker_truth_rejected` | PASS |
| no venue recon degraded | `tests/unit/test_pm7_truth.py` | `test_no_venue_stays_degraded` | PASS |
| derived retains provenance | `tests/unit/test_pm7_truth.py` | `test_derived_data_retains_provenance` | PASS |
| provenance contradiction | `tests/unit/test_pm7_truth.py` | `test_provenance_contradiction_recorded` | PASS |
| recon pass/mismatch/degraded/unavailable/critical | `tests/unit/test_pm7_recon.py` | `test_store_*` | PASS |
| resolution keeps history | `tests/unit/test_pm7_recon.py` | `test_resolution_event_keeps_history` | PASS |
| query by order/session/symbol | `tests/unit/test_pm7_recon.py` | `test_query_by_order_session_symbol` | PASS |
| no silent pass on PM5 ingest | `tests/unit/test_pm7_recon.py` | `test_ingest_pm5_never_silent_pass` | PASS |
| evidence bundle | `tests/unit/test_pm7_evidence.py` | `test_build_bundle_from_source_events` | PASS |
| missing refs flagged | `tests/unit/test_pm7_evidence.py` | `test_missing_event_references_flagged` | PASS |
| operator action included | `tests/unit/test_pm7_evidence.py` | `test_incident_evidence_and_operator_action` | PASS |
| export reproducibility | `tests/unit/test_pm7_evidence.py` | `test_export_reproducibility` | PASS |
| deterministic replay | `tests/unit/test_pm7_replay.py` | `test_deterministic_session_replay` | PASS |
| order/incident replay | `tests/unit/test_pm7_replay.py` | `test_order_and_incident_replay` | PASS |
| snapshot / divergence | `tests/unit/test_pm7_replay.py` | `test_snapshot_assisted_replay_and_divergence` | PASS |
| invalid order fails | `tests/unit/test_pm7_replay.py` | `test_invalid_event_order_fails` | PASS |
| replay no mutation | `tests/unit/test_pm7_replay.py` | `test_replay_does_not_mutate_source` | PASS |
| snapshot checksum | `tests/unit/test_pm7_snapshots.py` | `test_capture_and_validate_checksum` | PASS |
| superseded | `tests/unit/test_pm7_snapshots.py` | `test_superseded_snapshot` | PASS |
| corrupt detection | `tests/unit/test_pm7_snapshots.py` | `test_corrupt_detection` | PASS |
| sequence linkage | `tests/unit/test_pm7_snapshots.py` | `test_journal_sequence_linkage` | PASS |
| valid hash chain | `tests/unit/test_pm7_integrity.py` | `test_canonical_hashing_and_valid_chain` | PASS |
| mismatch compromised | `tests/unit/test_pm7_integrity.py` | `test_mismatch_compromised` | PASS |
| repair is correction | `tests/unit/test_pm7_integrity.py` | `test_repair_is_correction_not_rewrite` | PASS |
| export checksum | `tests/unit/test_pm7_integrity.py` | `test_archive_checksum_on_export` | PASS |
| hot/warm/cold | `tests/unit/test_pm7_retention.py` | `test_hot_warm_cold_transition` | PASS |
| freeze | `tests/unit/test_pm7_retention.py` | `test_retention_lock_and_legal_freeze` | PASS |
| purge blocked frozen | `tests/unit/test_pm7_retention.py` | `test_purge_blocked_while_frozen` | PASS |
| no silent delete | `tests/unit/test_pm7_retention.py` | `test_purge_eligibility_without_delete` | PASS |
| archive manifest | `tests/unit/test_pm7_retention.py` | `test_archive_manifest` | PASS |
| authorized query | `tests/unit/test_pm7_query.py` | `test_authorized_query_with_limit` | PASS |
| unauthorized rejected | `tests/unit/test_pm7_query.py` | `test_unauthorized_query_rejected` | PASS |
| export no secrets | `tests/unit/test_pm7_query.py` | `test_export_manifest_checksum_no_secrets` | PASS |
| lineage report | `tests/unit/test_pm7_reports.py` | `test_lineage_aware_report` | PASS |
| insufficient_data | `tests/unit/test_pm7_reports.py` | `test_insufficient_data_handled` | PASS |
| sim ≠ broker in reports | `tests/unit/test_pm7_reports.py` | `test_simulation_not_shown_as_broker` | PASS |
| recon degraded visible | `tests/unit/test_pm7_reports.py` | `test_reconciliation_degraded_visible` | PASS |
| backup metadata | `tests/unit/test_pm7_recovery.py` | `test_backup_metadata_unavailable_by_default` | PASS |
| stale restore review | `tests/unit/test_pm7_recovery.py` | `test_stale_backup_requires_review_on_restore` | PASS |
| restore pending | `tests/unit/test_pm7_recovery.py` | `test_restore_pending_when_available` | PASS |
| continuity | `tests/unit/test_pm7_recovery.py` | `test_continuity_check` | PASS |
| PM1 bind | `tests/unit/test_pm7_integration.py` | `test_flag_on_binds_pm7` | PASS |
| NullLedger default | `tests/unit/test_pm7_integration.py` | `test_flag_off_null_ledger` | PASS |
| PM4/PM5/PM6 adapters | `tests/unit/test_pm7_integration.py` | `test_pm4_pm5_pm6_adapters` | PASS |
| downstream offline | `tests/unit/test_pm7_integration.py` | `test_downstream_offline_does_not_break` | PASS |
| file/sqlite backends | `tests/unit/test_pm7_integration.py` | `test_file_and_sqlite_backends` | PASS |
| flags default false | `tests/unit/test_pm7_safety.py` | `test_flags_default_false` | PASS |
| no MT5 via config | `tests/unit/test_pm7_safety.py` | `test_cannot_enable_mt5_via_config` | PASS |
| production_durable refused | `tests/unit/test_pm7_safety.py` | `test_production_durable_refused` | PASS |
| no order submit | `tests/unit/test_pm7_safety.py` | `test_pm7_does_not_submit_orders` | PASS |
| no telegram | `tests/unit/test_pm7_safety.py` | `test_no_telegram_import` | PASS |
| publication forbids broker | `tests/unit/test_pm7_safety.py` | `test_publication_forbids_broker_truth` | PASS |
| no hidden purge | `tests/unit/test_pm7_safety.py` | `test_no_hidden_purge` | PASS |
| contracts: SIM ≠ broker | `tests/contract/test_pm7_persistence_contracts.py` | `test_sim_cannot_be_broker` | PASS |
| contracts: recon no silent pass | `tests/contract/test_pm7_persistence_contracts.py` | `test_recon_without_venue_cannot_pass` | PASS |
| contracts: memory ≠ durable | `tests/contract/test_pm7_persistence_contracts.py` | `test_memory_cannot_claim_durable` | PASS |

# Traceability matrix — Sequence 14 + reconciliation 2026-08-30

Statuses: COMPLETE | PARTIAL | BLOCKED | NEEDS-HARDENING | NOT-IN-SCOPE | SOURCE-MISSING | ABSENT.

COMPLETE requires an implementation path and a test or evidence path.

Source: architect Sequence 14 authorization 2026-08-30; architect reconciliation authorization 2026-08-30.

This is **not** Sequence 15.

| ID | Requirement | Source | Implementation | Test / evidence | Status | Known limitation | Next |
|---|---|---|---|---|---|---|---|
| S14-01 | Structured log schema + UTC | §3 | `modules/observability/logging_events.py` | `tests/unit/test_seq14_observability.py::test_structured_log_schema_and_utc` | COMPLETE | Console renderer still used when json_output=false | keep JSON in observe --json |
| S14-02 | Correlation / causation / trace | §3 | `logging_events.py` | `test_correlation_causation_propagation` | COMPLETE | — | — |
| S14-03 | Secret redaction | §3 | `modules/observability/redaction.py` | `test_secret_redaction_in_log_metadata` `test_seq14_ci_hygiene.py::test_evidence_has_no_secret_values` | COMPLETE | Heuristic URL scrubber | rotate on any leak |
| S14-04 | Typed metrics catalog | §4 | `modules/observability/metrics.py` | `test_metric_catalog_covers_required_names` | COMPLETE | In-process registry only; no Prometheus exporter | Seq 15+ if authorized |
| S14-05 | Cardinality limits | §4 | `MetricRegistry._check_labels` | `test_metric_cardinality_limits` | COMPLETE | — | — |
| S14-06 | Liveness ≠ readiness ≠ trading | §5 | `health_model.py` `HealthReport` `ReadinessReport` | `test_liveness_readiness_separation` | COMPLETE | — | — |
| S14-07 | Venue absent ≠ pass | §5 | `health_model.py` broker_venue=UNAVAILABLE | `test_venue_absent_is_not_pass` | COMPLETE | — | — |
| S14-08 | Recovery incomplete ⇒ not trade-ready | §5 | `health_model.py` | `test_recovery_incomplete_not_trade_ready` | COMPLETE | — | — |
| S14-09 | Stale data safe-stop | §5 | `health_model.py` stale_data | `test_stale_data_safe_stop` | COMPLETE | Threshold wiring to PM2 is PARTIAL (flag off) | PM2 flag remains off |
| S14-10 | Error taxonomy | §6 | `modules/observability/errors.py` | `test_error_taxonomy_complete_and_public_safe` | COMPLETE | — | — |
| S14-11 | Public-safe messages | §6 | `ErrorSpec.public_safe_message` | same | COMPLETE | — | — |
| S14-12 | Runbooks (20) | §7 | `runbooks.py` `docs/runbooks/` | `test_runbooks_have_twelve_fields_and_count` `test_runbook_markdown_matches_catalog` | COMPLETE | Tabletop via executable_check ids | — |
| S14-13 | Documentation set | §8 | `docs/observability/*` `docs/guides/*` README | `test_seq14_docs.py` | COMPLETE | Master Orchestration file still missing | — |
| S14-14 | Numbering map 00–14 | §8 §12 | `docs/MODULE_NUMBERING_MAP.md` | `test_numbering_map_covers_seq_00_to_14` | COMPLETE | — | — |
| S14-15 | No bare pm6 execution | §8 §10 | `mt5_execution_engine` | `test_no_pm6_execution_package` | COMPLETE | — | — |
| S14-16 | Flags default false | §1 §10 | `feature_flags.py` YAML | `test_all_flags_off_trading_false` `test_feature_flags.py` | COMPLETE | — | — |
| S14-17 | Live fail-closed | §1 §10 | CLI / settings | `test_live_still_fail_closed` `test_live_command_fail_closed_in_hygiene` | COMPLETE | — | — |
| S14-18 | Telegram refused | §1 §10 | `adapters/telegram/transport.py` | `test_telegram_transport_still_refused` | COMPLETE | — | — |
| S14-19 | No PM4 bypass | §1 §10 | PM4 exclusive | `tests/unit/test_pm4_safety.py` | COMPLETE | — | — |
| S14-20 | SIM/DEMO ≠ broker truth | §1 §10 | pm5 + mt5_execution_engine | `tests/unit/test_seq11_mt5_exit.py` `test_pm5_safety.py` | COMPLETE | — | — |
| S14-21 | CI pipefail / no false green | §12 | `.github/workflows/tests.yml` | `test_workflows_pipefail_on_pipelines` `test_set_plus_e_restores_errexit` | COMPLETE | Artifact ZIP still login-gated | committed `docs/evidence/` |
| S14-22 | Evidence bundle | §11 | `scripts/bot/emit_seq14_evidence.py` | `docs/evidence/seq14/` | COMPLETE | Dump checksums are run-specific | payload_canonical comparable |
| S14-23 | Health transitions table | §5 | `TRANSITION_TABLE` | `test_transition_table_covers_critical_rows` | COMPLETE | — | — |
| S14-24 | Observe CLI | §2 | `cli/entrypoint.py` observe/health | `test_observe_cli_json` | COMPLETE | — | — |
| S14-25 | Fitted QRF / real MT5 / Seq 15 | §13 | — | — | NOT-IN-SCOPE | Forbidden in Seq 14 | architect permission |
| S14-26 | Trading readiness=true | §13 | forced false | `test_liveness_readiness_separation` | COMPLETE (refused) | Never true here | — |
| S14-27 | Persistence inconsistency not-ready | §5 | integrity_ok=False → FAIL | `test_integrity_fail_persistence_not_ready` | COMPLETE | — | — |
| S14-28 | Python 3.10 fail-fast | ADR-008 | `python_version.py` | `tests/unit/test_python_version.py` CI doctor-py310 | COMPLETE | — | — |
| R-01 | Inventory of sources vs modules | recon §3 | `docs/ARCHITECTURE_INVENTORY.md` | `test_traceability_and_inventory_exist` | COMPLETE | Master Orchestration SOURCE-MISSING | keep inventory current |
| R-02 | PM6 ≠ Seq 14 observability | recon §4A | `pm6_post_trade` vs `modules/observability` | `test_observability_is_not_pm6` `test_pm6_module_cannot_submit_orders_or_size_risk` | COMPLETE | PM6 is in-memory Seq 08 | — |
| R-03 | PM6 cannot submit / size | recon §5.12 | AST + hasattr | `test_pm6_module_cannot_submit_orders_or_size_risk` | COMPLETE | — | — |
| R-04 | PM7 classified PARTIAL evidence-journal | recon §4B | `pm7_persistence` README + inventory | `test_pm7_status_is_partial_evidence_journal` | COMPLETE | not production durable; not canonical API | do not relabel COMPLETE |
| R-05 | PM7 append-only + correction + lineage | recon §4B | journal + `correct()` | `test_pm7_append_only_correction_lineage` `test_pm7_journal.py` | COMPLETE (in-process) | file/sqlite no reload | — |
| R-06 | PM7 replay + integrity | recon §4B | replay/integrity | `test_pm7_replay_and_integrity_status` | COMPLETE (in-process) | detection not proof | — |
| R-07 | PM8a identity = hardening of PM8 | recon §4C | same package `pm8_persistence` | inventory + gap matrix | COMPLETE (identity) | original Drive spec SOURCE-MISSING | — |
| R-08 | PM8 versioned API | recon G | `PersistenceApiV1` | `test_pm8_versioned_api` | COMPLETE | v1 only | — |
| R-09 | PM8 four idempotency edges | recon C | REQUEST/EVENT_CONSUMER/BROKER_CALLBACK/PROJECTION | `test_pm8_idempotency_and_dedupe_edges` `test_four_idempotency_edges` | COMPLETE | simulated ids | — |
| R-10 | PM8 outbox same UoW as event | recon C | `ingest_event` | `test_pm8_outbox_atomicity` | COMPLETE | relay/bus ABSENT | — |
| R-11 | PM8 inbox duplicate | recon C | `consume_inbox` | `test_inbox_effectively_once` | PARTIAL | handler after accept | — |
| R-12 | Checkpoint monotonic | recon D | `SqliteStore.save_checkpoint` | `test_pm8_checkpoint_monotonic` | COMPLETE | this recon | — |
| R-13 | Named projections not COMPLETE | recon F | gap matrix ABSENT rows | `test_pm8_named_projections_are_not_claimed_complete` | ABSENT (honest) | do not invent | architect if authorized |
| R-14 | Restore-apply ABSENT | recon H | verify only | `test_pm8a_seq10.py` + gap matrix | ABSENT | verify COMPLETE | do not fake restore |
| R-15 | Recovery-before-trading | recon D | `UnifiedRuntime.tick` | `test_recovery_before_trading_still_halts` | COMPLETE | observe-only | — |
| R-16 | Recon no silent pass | recon E | `persist_reconciliation` | `test_recon_no_silent_pass` | COMPLETE | — | — |
| R-17 | Seq 14 cannot set trading_readiness true | recon §5.14 | `health_model.py` | `test_sequence_14_cannot_set_trading_readiness_true` | COMPLETE | — | — |
| R-18 | Observability cannot submit orders | recon §5.10 | AST | `test_observability_cannot_submit_orders` | COMPLETE | — | — |
| R-19 | Operator cannot bypass PM4 | recon §5.10 | `/buy` REFUSED | `test_operator_cannot_bypass_pm4` | COMPLETE | — | — |
| R-20 | Flags default false | recon §8 | catalog | `test_all_catalog_flags_default_false` | COMPLETE | — | — |
| R-21 | Live CLI fail-closed | recon §8 | CLI | `test_live_cli_fail_closed` | COMPLETE | — | — |
| R-22 | Telegram refused | recon §8 | transport | `test_telegram_transport_refused` | COMPLETE | — | — |
| R-23 | Numbering map 00–14 | recon §8 | map | `test_numbering_map_consistency_00_to_14` | COMPLETE | — | — |
| R-24 | No unsafe CI pipe gates | recon §8 | `tests.yml` | `test_ci_hygiene_still_bans_piped_gates` | COMPLETE | — | — |
| RMD-01 | Durable SQLite reload | rem §5 | `SqliteStore` / PM7 journals | `test_file_backed_sqlite_survives_process_restart` `test_pm7_journal_and_snapshot_survive_restart` | COMPLETE (local) | PG is a separate backend (PG-01+) | — |
| RMD-02 | Decimal money keys | rem §6 | `pm8_persistence/money.py` | `test_decimal_round_trip_and_reject_float` | COMPLETE persist_* | residual JSON bags PARTIAL | — |
| RMD-03 | Nested Unit of Work | rem §7 | `in_transaction` | `test_uow_failure_injection_rolls_back` | COMPLETE | — | — |
| RMD-04 | Outbox relay / DLQ | rem §8 | `relay_outbox` | `test_outbox_relay_retry_dead_letter_and_restart` | COMPLETE SQLite | PG SKIP LOCKED BLOCKED | — |
| RMD-05 | Inbox retry / hash conflict | rem §9 | `consume_inbox` | `test_inbox_retry_dead_letter_and_duplicate` `test_request_idempotency_hash_conflict` | COMPLETE | — | — |
| RMD-06 | Named projections | rem §10 | `rebuild_named_projections` | `test_named_projections_rebuild_and_duplicate` | COMPLETE read-models | not canonical | supersedes R-13 ABSENT |
| RMD-07 | Reconciliation run aggregate | rem §11 | `start_reconciliation_run` | `test_reconciliation_run_lifecycle_and_no_silent_pass` | COMPLETE | — | — |
| RMD-08 | Isolated restore-apply | rem §12 | `restore_apply.py` | `test_isolated_restore_apply` | COMPLETE SQLite isolated + PG isolated DSN | live target refused | supersedes R-14 ABSENT |
| RMD-09 | PM7 journal reload | rem §13 | sqlite/file journals | `test_pm7_file_journal_survives_restart` | COMPLETE sqlite/file | memory mode ephemeral | supersedes R-05 limitation |
| RMD-10 | API version / no broker | rem §14 | `require_version` | `test_api_version_and_no_broker_surface` | COMPLETE | v1 only | — |
| RMD-11 | Sequence 15 still blocked | rem stop | no artifacts | `test_no_sequence_15_artifacts` | COMPLETE (refused) | — | — |
| R-25 | No Sequence 15 artifacts | recon §11 | files + flags | `test_no_sequence_15_artifacts` | COMPLETE (blocked) | remains blocked | architect permission |
| R-26 | PM7/PM8 not broker adapters | recon §5.13 | AST | `test_pm7_pm8_not_broker_adapters` | COMPLETE | — | — |
| R-27 | Decimal accounting types | recon A | none | gap matrix | ABSENT | TEXT qty/avg_px | do not invent |
| R-28 | Outbox relay / bus | recon C | none | gap matrix | ABSENT | in-process mark published | — |
| PG-01 | PostgreSQL fail-closed / no SQLite fallback | PG durability | `open_pm8_store` `PostgresStore` | `test_pm8_postgresql_failclosed.py` | COMPLETE | production_durable still refused | — |
| PG-02 | Prefixed DSN only | PG §15 | `BOTMODULEPROJECT1_DATABASE_URL` | `test_unprefixed_database_url_is_ignored` | COMPLETE | — | — |
| PG-03 | NUMERIC money round-trip | PG §6 | `money_records` `positions_proj` | `test_numeric_round_trip` | COMPLETE on persist_* | residual JSON bags | — |
| PG-04 | Append-only triggers | PG §8 | `pm8_forbid_mutation` | `test_append_only_events_and_audit` | COMPLETE | TRUNCATE still allowed for tests | — |
| PG-05 | Unique idempotency | PG §10 | `idempotency_keys` PK | `test_unique_idempotency_index` | COMPLETE | — | — |
| PG-06 | SKIP LOCKED outbox claim | PG §11 | `CLAIM_BATCH_SQL` | `test_outbox_skip_locked_concurrent_claim` | COMPLETE | sqlite sequential claim remains | — |
| PG-07 | Schema migrations repeat-safe | PG §16 | `MigrationService` | `test_schema_migrations_repeat_safe` | COMPLETE | v1/v2 catalog | — |
| PG-08 | Projection rebuild | PG §13 | `rebuild_named_projections` | `test_projection_rebuild` | COMPLETE read-models | not canonical | — |
| PG-09 | Reconciliation lifecycle | PG §14 | recon run APIs | `test_reconciliation_lifecycle_no_silent_pass` | COMPLETE | — | — |
| PG-10 | Isolated PG restore-apply | PG §13 | `apply_restore_postgres` | `test_isolated_restore_apply` | COMPLETE isolated DSN | live DSN refused | — |
| PG-11 | Restart durability | PG §13 | reopen `PostgresStore` | `test_restart_durability` | COMPLETE | sandbox/CI cluster | — |
| PG-12 | UoW fault injection | PG §20 | `inject_fault` | `test_uow_fault_injection_no_partial_commit` | COMPLETE | — | — |
| PG-13 | Sequence 11+ still blocked | stop | flags / CLI | `test_reconciliation_boundaries.py` | COMPLETE (refused) | — | — |


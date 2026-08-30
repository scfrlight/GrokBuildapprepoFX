# Traceability matrix — Sequence 14

Statuses: COMPLETE | PARTIAL | BLOCKED | NEEDS-HARDENING | NOT-IN-SCOPE.

COMPLETE requires an implementation path and a test or evidence path.

Source: architect Sequence 14 authorization 2026-08-30.

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

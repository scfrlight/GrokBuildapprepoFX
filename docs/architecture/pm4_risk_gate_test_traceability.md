# PM4 Risk Gate — Test Traceability (Sequence 06)

Date (UTC): 2026-08-28  
Suite: 235 collected / 235 passed (46 added in Sequence 06)

| Invariant / Requirement | Test file | Test name | Result |
|---|---|---|---|
| deny-by-default | `tests/unit/test_pm4_safety.py` | `test_deny_by_default_without_upstream_artifacts` | PASS |
| flag off denies | `tests/unit/test_pm4_safety.py` | `test_flag_off_denies` | PASS |
| NullRiskGate when YAML flag false | `tests/unit/test_pm4_safety.py` | `test_null_risk_gate_still_denies_when_flag_off` | PASS |
| no future information | `tests/unit/test_pm4_safety.py` | `test_no_future_information` | PASS |
| stale artifact rejection | `tests/unit/test_pm4_safety.py` | `test_stale_artifact_rejected` | PASS |
| no direct execution / no order object | `tests/unit/test_pm4_safety.py` | `test_allow_still_does_not_create_order_or_call_pm5` | PASS |
| no risk bypass via evaluate() | `tests/unit/test_pm4_safety.py` | `test_pm3_cannot_bypass_via_evaluate_protocol` | PASS |
| missing PM3 forecast validity | `tests/unit/test_pm4_safety.py` | `test_missing_forecast_validity_diagnostics_denied` | PASS |
| ALLOW still not an order | `tests/unit/test_pm4_safety.py` | `test_risk_publication_bundle_is_not_an_order` | PASS |
| execution_permitted stays false | `tests/unit/test_pm4_safety.py` | `test_publication_rejects_execution_permitted_true` | PASS |
| duplicate prevention (idempotent) | `tests/unit/test_pm4_intake.py` | `test_duplicate_idempotency_returns_same_verdict` | PASS |
| heat headroom / effective heat | `tests/unit/test_pm4_engines.py` | `test_heat_is_not_raw_sum_only` | PASS |
| concentration cap / one-per-cluster | `tests/unit/test_pm4_engines.py` | `test_one_per_cluster_blocks` | PASS |
| drawdown stage escalation | `tests/unit/test_pm4_engines.py` | `test_drawdown_escalation_ladder` | PASS |
| kill-switch block | `tests/unit/test_pm4_kill_governance.py` | `test_kill_switch_blocks_new_risk` | PASS |
| no hidden auto-rearm | `tests/unit/test_pm4_kill_governance.py` | `test_kill_switch_no_auto_rearm` | PASS |
| recovery policy gate | `tests/unit/test_pm4_kill_governance.py` | `test_recovery_requires_reason_and_cooldown` | PASS |
| close-only / no-new-risk | `tests/unit/test_pm4_kill_governance.py` | `test_close_only_blocks_new_risk` | PASS |
| route eligibility recorded closed | `tests/unit/test_pm4_engines.py` | `test_route_eligibility_recorded_closed` | PASS |
| no PM5 execution call | `tests/unit/test_pm4_integration.py` | `test_allow_handoff_pending_pm5_and_execution_still_disabled` | PASS |
| YAML flag remains false | `tests/unit/test_pm4_integration.py` | `test_yaml_does_not_enable_pm4` | PASS |
| demo cannot opt-in | `tests/unit/test_pm4_integration.py` | `test_flag_on_in_demo_rejected` | PASS |
| public contracts | `tests/contract/test_pm4_risk_contracts.py` | `test_required_enums_exist` | PASS |
| capital 40-check catalog | `tests/unit/test_pm4_capital_gate.py` | `test_catalog_has_exactly_forty_named_checks` | PASS |
| capital no execution | `tests/unit/test_pm4_capital_gate.py` | `test_happy_path_emits_all_forty_checks_and_no_execution` | PASS |
| capital ROUND_DOWN sizing | `tests/unit/test_pm4_capital_gate.py` | `test_sizing_never_rounds_up_through_budget` | PASS |
| capital restart drawdown | `tests/unit/test_pm4_capital_gate.py` | `test_drawdown_survives_restart` | PASS |
| capital idempotency conflict | `tests/unit/test_pm4_capital_gate.py` | `test_idempotency_same_key_different_hash_conflicts` | PASS |
| capital replay | `tests/unit/test_pm4_capital_gate.py` | `test_replay_matches_and_does_not_overwrite` | PASS |
| capital fail-inject | `tests/unit/test_pm4_capital_gate.py` | `test_injected_faults_fail_closed` | PASS |
| capital PG NUMERIC | `tests/unit/test_pm4_capital_persistence.py` | `test_postgres_numeric_capital_decision` | PASS |
| existing evaluate() unbroken | `tests/unit/test_pm4_capital_gate.py` | `test_existing_evaluate_path_unchanged` | PASS |

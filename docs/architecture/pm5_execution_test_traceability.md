# PM5 Execution — Test Traceability (Sequence 07)

| Invariant / Requirement | Test file | Test name | Result |
|---|---|---|---|
| PM4-only authorization | `tests/unit/test_pm5_intake.py` | `test_missing_pm4_authorization_rejected` | PASS |
| PM4 DENY cannot reach adapter | `tests/unit/test_pm5_intake.py` | `test_pm4_deny_rejected` | PASS |
| Simulation accepts PM4 ALLOW | `tests/unit/test_pm5_intake.py` | `test_simulation_accepts_pm4_allow` | PASS |
| execution_permitted=false rejected on broker path | `tests/unit/test_pm5_intake.py` | `test_execution_permitted_false_rejected_on_broker_path` | PASS |
| Deny-by-default / feature off | `tests/unit/test_pm5_safety.py` | `test_feature_disabled_when_simulation_off` | PASS |
| Execution flag false / YAML | `tests/unit/test_pm5_safety.py` | `test_yaml_flags_false` | PASS |
| Default bind DisabledExecution | `tests/unit/test_pm5_safety.py` | `test_default_bind_is_disabled_execution` | PASS |
| No live profile | `tests/unit/test_pm5_safety.py` | `test_live_profile_refused` | PASS |
| Live execution flag refused | `tests/unit/test_pm5_safety.py` | `test_live_execution_flag_refused` | PASS |
| Idempotency replay | `tests/unit/test_pm5_intake.py` | `test_duplicate_idempotency_replays` | PASS |
| Duplicate conflict | `tests/unit/test_pm5_intake.py` | `test_duplicate_conflict_on_payload_mismatch` | PASS |
| No duplicate submit | `tests/unit/test_pm5_intake.py` | `test_duplicate_idempotency_replays` | PASS |
| OMS valid/invalid transitions | `tests/unit/test_pm5_oms.py` | `test_valid_transitions` / `test_invalid_transition_rejected` | PASS |
| Terminal protection | `tests/unit/test_pm5_oms.py` | `test_terminal_state_protected` | PASS |
| Partial fills | `tests/unit/test_pm5_oms.py` | `test_partial_and_full_fill` | PASS |
| Cancel lifecycle | `tests/unit/test_pm5_oms.py` | `test_cancel_lifecycle` | PASS |
| Modify lifecycle | `tests/unit/test_pm5_oms.py` | `test_modify_lifecycle` | PASS |
| Broker recon unavailable ≠ pass | `tests/unit/test_pm5_recon.py` | `test_unavailable_broker_is_degraded_not_pass` | PASS |
| Simulation recon degraded | `tests/unit/test_pm5_recon.py` | `test_simulation_ingest_recon_is_degraded` | PASS |
| Critical mismatch blocks | `tests/unit/test_pm5_recon.py` | `test_critical_mismatch_blocks_new_orders` | PASS |
| Kill-switch | `tests/unit/test_pm5_control.py` | `test_emergency_cancel_latches` / `test_kill_switch_from_pm4_bundle` | PASS |
| No-new-risk | `tests/unit/test_pm5_control.py` | `test_close_only_and_no_new_risk` | PASS |
| Close-only | `tests/unit/test_pm5_control.py` | `test_close_only_and_no_new_risk` | PASS |
| No auto-rearm | `tests/unit/test_pm5_control.py` | `test_no_hidden_auto_rearm_cooldown` | PASS |
| Reconnect recon before submit | `tests/unit/test_pm5_recon.py` | `test_unavailable_broker_is_degraded_not_pass` | PASS |
| No direct MT5 side effects | `tests/unit/test_pm5_ems.py` | `test_mt5_adapter_unavailable` / `test_no_metatrader5_import` | PASS |
| Replay determinism | `tests/unit/test_pm5_surveillance.py` | `test_replay_is_deterministic` | PASS |
| Stale / lookahead | `tests/unit/test_pm5_intake.py` | `test_stale_intent_rejected` / `test_future_timestamp_rejected` | PASS |
| Quantity cap | `tests/unit/test_pm5_intake.py` | `test_quantity_above_pm4_rejected` | PASS |
| No PM2/PM3 bypass | `tests/unit/test_pm5_safety.py` | `test_no_pm2_pm3_bypass` | PASS |
| submit() raises | `tests/unit/test_pm5_safety.py` | `test_module_submit_always_raises` | PASS |
| Publication forbids live/mt5 | `tests/unit/test_pm5_safety.py` | `test_publication_forbids_mt5_and_live` | PASS |

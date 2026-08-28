# PM6 Post-Trade — Test Traceability (Sequence 08)

| Invariant / Requirement | Test file | Test name | Result |
|---|---|---|---|
| valid PM5 simulation accepted | `tests/unit/test_pm6_intake.py` | `test_valid_simulation_event_accepted` | PASS |
| SIM-* not broker truth | `tests/unit/test_pm6_truth.py` | `test_sim_ticket_is_simulation_truth` | PASS |
| missing source quarantined | `tests/unit/test_pm6_intake.py` | `test_missing_source_quarantined` | PASS |
| stale quarantined | `tests/unit/test_pm6_intake.py` | `test_stale_quarantined` | PASS |
| future-dated rejected | `tests/unit/test_pm6_intake.py` | `test_future_dated_rejected` | PASS |
| missing trace rejected | `tests/unit/test_pm6_intake.py` | `test_missing_trace_rejected` | PASS |
| sim labelled broker truth rejected | `tests/unit/test_pm6_truth.py` | `test_sim_labelled_broker_truth_rejected` | PASS |
| no venue recon degraded | `tests/unit/test_pm6_truth.py` | `test_no_venue_stays_degraded` | PASS |
| quantity drift | `tests/unit/test_pm6_controls.py` | `test_quantity_drift_detected` | PASS |
| execution after kill | `tests/unit/test_pm6_controls.py` | `test_execution_after_kill_detected` | PASS |
| recon mismatch | `tests/unit/test_pm6_controls.py` | `test_unresolved_mismatch_incident` | PASS |
| two lanes independent | `tests/unit/test_pm6_lanes.py` | `test_two_lanes_are_independent` | PASS |
| control lane on kill | `tests/unit/test_pm6_lanes.py` | `test_control_lane_priority_on_kill` | PASS |
| alert dedup / evidence | `tests/unit/test_pm6_alerts.py` | `test_alert_dedup_retains_evidence` | PASS |
| distinct alerts not merged | `tests/unit/test_pm6_alerts.py` | `test_materially_different_alerts_not_merged` | PASS |
| submit burst | `tests/unit/test_pm6_surveillance.py` | `test_submit_burst_detector` | PASS |
| reject burst | `tests/unit/test_pm6_surveillance.py` | `test_reject_burst_detector` | PASS |
| incident lifecycle | `tests/unit/test_pm6_incidents.py` | `test_incident_lifecycle_and_no_silent_drop` | PASS |
| illegal transition | `tests/unit/test_pm6_incidents.py` | `test_illegal_transition_rejected` | PASS |
| suppress requires reason | `tests/unit/test_pm6_incidents.py` | `test_suppress_requires_reason` | PASS |
| transfer keeps record | `tests/unit/test_pm6_incidents.py` | `test_transfer_to_persistence_keeps_record` | PASS |
| withdrawal recommended | `tests/unit/test_pm6_withdrawal.py` | `test_kill_recommends_withdrawal` | PASS |
| confirmation required | `tests/unit/test_pm6_withdrawal.py` | `test_withdrawal_confirmation_required` | PASS |
| failed → manual review | `tests/unit/test_pm6_withdrawal.py` | `test_failed_withdrawal_to_manual_review` | PASS |
| governance packets | `tests/unit/test_pm6_governance.py` | `test_governance_and_validation_packets` | PASS |
| flags default false | `tests/unit/test_pm6_safety.py` | `test_flags_default_false` | PASS |
| live blocked | `tests/unit/test_pm6_safety.py` | `test_live_profile_blocked` | PASS |
| no MT5 via config | `tests/unit/test_pm6_safety.py` | `test_cannot_enable_mt5_via_config` | PASS |
| no order submit | `tests/unit/test_pm6_safety.py` | `test_pm6_does_not_submit_orders` | PASS |
| publication forbids broker truth | `tests/unit/test_pm6_safety.py` | `test_publication_forbids_broker_truth` | PASS |
| no telegram import | `tests/unit/test_pm6_safety.py` | `test_no_telegram_import` | PASS |
| PM1 bind on flag | `tests/unit/test_pm6_integration.py` | `test_flag_on_binds_pm6` | PASS |
| NullMonitoring default | `tests/unit/test_pm6_integration.py` | `test_flag_off_null_monitoring` | PASS |
| contracts / no broker command | `tests/contract/test_pm6_post_trade_contracts.py` | `test_control_request_cannot_be_broker_command` | PASS |

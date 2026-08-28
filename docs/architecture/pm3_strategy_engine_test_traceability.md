# PM3-Strategy Engine — Test Traceability

Date (UTC): 2026-08-28  
Suite: 159 collected / 159 passed (sandbox CPython 3.10.21 with ADR-008 patch)

| Invariant / Requirement | Test file | Test name | Result |
|---|---|---|---|
| No-lookahead | `tests/unit/test_pm3_se_safety.py` | `test_no_lookahead_future_context` | PASS |
| No-lookahead (pipe) | `tests/unit/test_pm3_se_symbol_pipe.py` | `test_lookahead_rejected` | PASS |
| Confirmed as-of only / no repaint | `tests/unit/test_pm3_se_safety.py` | `test_confirmed_as_of_only` | PASS |
| PM2 handoff safety | `tests/unit/test_pm3_se_symbol_pipe.py` | `test_handoff_false_is_no_trade` | PASS |
| No direct execution / no MT5 / no Telegram | `tests/unit/test_pm3_se_integration.py` | `test_no_pm5_or_telegram_imports` | PASS |
| Public PM2 adapter only | `tests/unit/test_pm3_se_integration.py` | `test_pm2_adapter_uses_public_contracts_only` | PASS |
| Consensus determinism | `tests/unit/test_pm3_se_consensus.py` | `test_deterministic` | PASS |
| Consensus formula | `tests/unit/test_pm3_se_consensus.py` | `test_base_weight_formula` | PASS |
| Profile immutability | `tests/unit/test_pm3_se_profiles.py` | `test_clone_active_to_draft_and_immutability` | PASS |
| Max 3 branches | `tests/unit/test_pm3_se_bindings.py` | `test_three_active_branches_per_symbol` | PASS |
| Duplicate binding / max 3 | `tests/unit/test_pm3_se_bindings.py` | `test_duplicate_and_max_three_rejected` | PASS |
| Duplicate intent prevention | `tests/unit/test_pm3_se_symbol_pipe.py` | `test_duplicate_idempotency` | PASS |
| Calibration separation | `tests/unit/test_pm3_se_consensus.py` | `test_calibration_changes_probability` | PASS |
| Risk-gate non-bypass | `tests/unit/test_pm3_se_integration.py` | `test_bootstrap_with_flag_still_not_trade_ready` | PASS |
| TradeIntent has no lot size | `tests/contract/test_pm3_se_contracts.py` | `test_trade_intent_rejects_lot_size` | PASS |
| Flag default off | `tests/unit/test_pm3_se_integration.py` | `test_flag_default_off_keeps_placeholder` | PASS |
| Insufficient tracker ≠ healthy | `tests/unit/test_pm3_se_feedback.py` | `test_synthetic_feedback_does_not_claim_health` | PASS |

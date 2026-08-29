# PM8 operator test traceability

| Requirement | Test |
|---|---|
| NullOperator default bind | `test_flag_off_null_operator` |
| Flag on binds PM8 | `test_flag_on_binds_pm8` |
| YAML flags stay false | `test_yaml_cannot_enable_operator_in_demo` |
| Observer cannot halt | `test_observer_cannot_halt` |
| Admin halt is not flatten | `test_admin_halt_is_not_broker_flatten` |
| Buy/sell/order/live/mt5/resume refused | `test_refused_order_verbs` |
| Idempotency | `test_idempotency` |
| HITL approve is not an order / not PM4 skip | `test_approve_does_not_emit_order` |
| HITL expiry | `test_hitl_expiry` |
| Operator cannot approve | `test_operator_cannot_approve` |
| Dual-control halt | `test_dual_control_halt` |
| Studio never auto-promotes | `test_studio_never_auto_promotes` |
| Studio flag off | `test_studio_disabled_refuses` |
| Telegram Bot API refused | `test_real_telegram_refused`, `test_telegram_flag_refused` |
| Decoder has no trading logic | `test_telegram_decode_encode_has_no_orders` |
| Secrets stripped from audit | `test_audit_strips_secret_shaped_text` |
| Contracts refuse secret payload | `test_secret_payload_rejected` |
| Receipt cannot claim order | `test_receipt_cannot_claim_order` |
| pm9 re-export | `test_pm9_reexport` |

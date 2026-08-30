# RB-OPERATOR-PERMISSION-DENIAL: Operator permission denial

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Command outside role/scope or HITL trying to skip PM4.
2. **Observable symptoms.**
- permission_denied
- denied_actions metric
3. **Safety classification.** deny
4. **Automatic system behavior.** Deny. Audit. HITL cannot skip PM4.
5. **Operator inspection commands.**
- python -m pytest tests/unit/test_pm4_safety.py tests/unit/test_pm8_hitl.py --tb=short
6. **Prohibited operator actions.**
- Do not grant a shadow role.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Re-issue a permitted observe command.
8. **Verification steps.**
- permission denied tests green
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- command receipt
11. **Closure criteria.** Denied command has an audit row.
12. **Escalation criteria.** A denied command still mutated risk.

Executable check id: `no_pm4_bypass`

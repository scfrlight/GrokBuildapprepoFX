# RB-KILL-SWITCH: Kill-switch activation

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Operator or risk kill-switch.
2. **Observable symptoms.**
- risk denials
- trading halted
3. **Safety classification.** halt
4. **Automatic system behavior.** No auto-rearm. No auto-promote.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not auto-rearm.
- Do not weaken the switch.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Leave halted.
- Architect permission required to change policy.
8. **Verification steps.**
- trading_readiness false
9. **Rollback steps.**
- N/A — halt stands.
10. **Evidence to preserve.**
- kill-switch audit
11. **Closure criteria.** Switch remains armed; no trading.
12. **Escalation criteria.** Any attempt to auto-rearm.

Executable check id: `trading_readiness_false`
